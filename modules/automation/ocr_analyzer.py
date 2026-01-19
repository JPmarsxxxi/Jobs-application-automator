"""
OCR-based Form Analyzer
Fast text extraction from form screenshots using Tesseract OCR
Falls back to vision model for complex cases
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logging.warning("pytesseract not installed - OCR will not be available")


class OCRFormAnalyzer:
    """Fast form analysis using OCR"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        if not OCR_AVAILABLE:
            raise ImportError("pytesseract required for OCR. Install with: pip install pytesseract pillow")

    def extract_text_with_boxes(self, image_path: str) -> List[Dict]:
        """
        Extract text with bounding box coordinates

        Args:
            image_path: Path to screenshot

        Returns:
            List of dicts: [{"text": "First Name", "x": 100, "y": 200, "width": 80, "height": 20}, ...]
        """
        try:
            img = Image.open(image_path)

            # Get detailed OCR data with bounding boxes
            ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

            results = []
            n_boxes = len(ocr_data['text'])

            for i in range(n_boxes):
                text = ocr_data['text'][i].strip()
                if text:  # Only include non-empty text
                    results.append({
                        'text': text,
                        'x': ocr_data['left'][i],
                        'y': ocr_data['top'][i],
                        'width': ocr_data['width'][i],
                        'height': ocr_data['height'][i],
                        'conf': ocr_data['conf'][i]  # confidence
                    })

            self.logger.debug(f"OCR extracted {len(results)} text elements")
            return results

        except Exception as e:
            self.logger.error(f"OCR extraction failed: {e}")
            return []

    def identify_fields(self, ocr_results: List[Dict]) -> List[Dict]:
        """
        Identify form fields from OCR text

        Args:
            ocr_results: OCR data with text and positions

        Returns:
            List of identified fields with metadata
        """
        fields = []

        # Common field patterns
        field_patterns = {
            'first_name': r'(?i)first\s*name',
            'last_name': r'(?i)last\s*name|surname',
            'email': r'(?i)e[-\s]?mail',
            'phone': r'(?i)phone|mobile|telephone',
            'city': r'(?i)city',
            'country': r'(?i)country',
            'linkedin': r'(?i)linkedin',
            'github': r'(?i)github',
            'resume': r'(?i)resume|cv',
            'cover_letter': r'(?i)cover\s*letter',
            'experience': r'(?i)years?\s*of\s*experience',
            'education': r'(?i)education|degree',
            'graduation': r'(?i)graduat(ion|ed)',
            'sponsorship': r'(?i)sponsor(ship)?|visa',
            'salary': r'(?i)salary|compensation',
            'availability': r'(?i)availab(le|ility)|notice',
        }

        # Combine nearby text elements into phrases
        phrases = self._combine_nearby_text(ocr_results)

        for phrase in phrases:
            text = phrase['text']

            # Check if this text matches a field pattern
            for field_type, pattern in field_patterns.items():
                if re.search(pattern, text):
                    # Check if it's a required field (look for *)
                    required = '*' in text or 'required' in text.lower()

                    fields.append({
                        'label': text,
                        'type': self._guess_field_type(field_type, text),
                        'required': required,
                        'position': {
                            'x': phrase['x'],
                            'y': phrase['y'],
                        },
                        'field_name': field_type
                    })
                    break

        self.logger.info(f"Identified {len(fields)} form fields via OCR")
        return fields

    def find_buttons(self, ocr_results: List[Dict]) -> List[str]:
        """
        Find button text (Next, Submit, Continue, etc.)

        Args:
            ocr_results: OCR data

        Returns:
            List of button texts found
        """
        button_keywords = ['next', 'submit', 'continue', 'send', 'apply', 'review', 'back', 'cancel', 'skip']

        buttons = []
        for item in ocr_results:
            text_lower = item['text'].lower()
            if any(keyword in text_lower for keyword in button_keywords):
                buttons.append(item['text'])

        self.logger.debug(f"Found buttons: {buttons}")
        return buttons

    def _combine_nearby_text(self, ocr_results: List[Dict], max_distance: int = 50) -> List[Dict]:
        """
        Combine text elements that are close together into phrases
        E.g., "First" and "Name" -> "First Name"
        """
        if not ocr_results:
            return []

        # Sort by y-coordinate (top to bottom), then x (left to right)
        sorted_results = sorted(ocr_results, key=lambda x: (x['y'], x['x']))

        phrases = []
        current_phrase = sorted_results[0].copy()
        current_phrase['text'] = [current_phrase['text']]

        for item in sorted_results[1:]:
            # Check if this item is on the same line (similar y-coordinate)
            y_diff = abs(item['y'] - current_phrase['y'])
            x_diff = item['x'] - (current_phrase['x'] + current_phrase['width'])

            if y_diff < 20 and x_diff < max_distance:
                # Same line and close together - combine
                current_phrase['text'].append(item['text'])
                current_phrase['width'] = item['x'] + item['width'] - current_phrase['x']
            else:
                # New phrase
                current_phrase['text'] = ' '.join(current_phrase['text'])
                phrases.append(current_phrase)

                current_phrase = item.copy()
                current_phrase['text'] = [current_phrase['text']]

        # Add last phrase
        current_phrase['text'] = ' '.join(current_phrase['text'])
        phrases.append(current_phrase)

        return phrases

    def _guess_field_type(self, field_name: str, label_text: str) -> str:
        """Guess HTML input type from field name"""

        type_map = {
            'email': 'email',
            'phone': 'phone',
            'linkedin': 'url',
            'github': 'url',
            'resume': 'file',
            'cover_letter': 'file',
        }

        # Check for dropdown indicators
        if any(word in label_text.lower() for word in ['select', 'choose', 'dropdown']):
            return 'dropdown'

        # Check for checkbox/radio indicators
        if any(word in label_text.lower() for word in ['agree', 'accept', 'terms', 'consent']):
            return 'checkbox'

        return type_map.get(field_name, 'text')

    def analyze_form_fast(self, screenshot_path: str) -> Dict:
        """
        Fast form analysis using OCR

        Args:
            screenshot_path: Path to screenshot

        Returns:
            Dict with form structure (same format as VisionFormAnalyzer for compatibility)
        """
        # Extract text with OCR
        ocr_results = self.extract_text_with_boxes(screenshot_path)

        if not ocr_results:
            self.logger.warning("OCR returned no results")
            return self._empty_form()

        # Identify fields
        fields = self.identify_fields(ocr_results)

        # Find buttons
        buttons = self.find_buttons(ocr_results)

        # Separate file uploads
        file_uploads = [f['label'] for f in fields if f['type'] == 'file']
        text_fields = [f for f in fields if f['type'] != 'file']

        return {
            'fields': text_fields,
            'buttons': buttons,
            'file_uploads': file_uploads,
            'page_number': 1,  # Would need more logic to determine
            'total_pages': 1,  # Would need more logic to determine
            'ocr_confidence': 'high' if len(fields) > 0 else 'low'
        }

    def _empty_form(self) -> Dict:
        """Empty form structure"""
        return {
            'fields': [],
            'buttons': [],
            'file_uploads': [],
            'page_number': 1,
            'total_pages': 1,
            'ocr_confidence': 'none'
        }


def get_ocr_analyzer() -> OCRFormAnalyzer:
    """Get OCR analyzer instance"""
    return OCRFormAnalyzer()
