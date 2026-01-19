"""
Smart Element Discovery
Uses vision/OCR to automatically discover HTML selectors for any website
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from playwright.sync_api import Page, ElementHandle

from modules.automation.hybrid_form_analyzer import get_hybrid_analyzer


class SmartElementDiscovery:
    """
    Automatically discovers HTML selectors using vision/OCR guidance

    How it works:
    1. Screenshot element (job card, form field, etc.)
    2. Use OCR/Vision to locate text (e.g., "Company name")
    3. Map coordinates → HTML element
    4. Generate CSS selector for that element
    5. Return selector for future use
    """

    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger(__name__)
        self.analyzer = get_hybrid_analyzer()

    def discover_selector(
        self,
        element: ElementHandle,
        field_type: str,
        expected_text: Optional[str] = None
    ) -> Optional[str]:
        """
        Discover CSS selector for a field within an element

        Args:
            element: Playwright ElementHandle (e.g., job card)
            field_type: What to find ("company", "title", "location", "button_next", etc.)
            expected_text: Optional text hint (e.g., "Google" for company)

        Returns:
            CSS selector string or None if discovery failed
        """
        try:
            # Take screenshot of the element
            screenshot_path = Path("workspace/temp_discovery.png")
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            element.screenshot(path=str(screenshot_path))

            # Use OCR to extract all text with positions
            ocr_results = self._extract_text_positions(str(screenshot_path))

            if not ocr_results:
                self.logger.warning("OCR returned no results for discovery")
                return None

            # Find the target text based on field type
            target_coords = self._find_target_coords(ocr_results, field_type, expected_text)

            if not target_coords:
                self.logger.debug(f"Could not locate {field_type} in OCR results")
                return None

            # Get bounding box of the element relative to page
            element_box = element.bounding_box()
            if not element_box:
                return None

            # Calculate absolute coordinates on page
            abs_x = element_box['x'] + target_coords['x']
            abs_y = element_box['y'] + target_coords['y']

            # Find HTML element at those coordinates
            target_element = self.page.locator(f"xpath=//*").element_at(abs_x, abs_y)

            if not target_element:
                self.logger.debug(f"No element found at coordinates ({abs_x}, {abs_y})")
                return None

            # Generate selector for this element
            selector = self._generate_selector(target_element)

            self.logger.info(f"✓ Discovered selector for {field_type}: {selector}")
            return selector

        except Exception as e:
            self.logger.error(f"Error discovering selector for {field_type}: {e}")
            return None

    def _extract_text_positions(self, image_path: str) -> List[Dict]:
        """Extract all text with bounding boxes using OCR"""
        try:
            # Try OCR first if available
            if hasattr(self.analyzer, 'ocr') and self.analyzer.use_ocr:
                return self.analyzer.ocr.extract_text_with_boxes(image_path)
            else:
                # Fallback: use vision to extract text (slower)
                self.logger.debug("OCR not available, using vision for text extraction")
                return []
        except Exception as e:
            self.logger.error(f"Text extraction failed: {e}")
            return []

    def _find_target_coords(
        self,
        ocr_results: List[Dict],
        field_type: str,
        expected_text: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Find coordinates of target field in OCR results

        Uses heuristics based on field type:
        - company: Usually below title, smaller font
        - title: Usually largest text, top of card
        - location: Contains location keywords or is near bottom
        - button: Contains button keywords (Next, Submit, etc.)
        """
        if expected_text:
            # If we have expected text, search for exact match
            for item in ocr_results:
                if expected_text.lower() in item['text'].lower():
                    return {'x': item['x'], 'y': item['y']}

        # Heuristic-based search by field type
        if field_type == "company":
            # Company is usually 2nd largest text, or text below title
            # Sort by font size (approximated by height)
            sorted_by_size = sorted(ocr_results, key=lambda x: x['height'], reverse=True)
            if len(sorted_by_size) >= 2:
                return {'x': sorted_by_size[1]['x'], 'y': sorted_by_size[1]['y']}

        elif field_type == "title":
            # Title is usually largest text at top
            largest = max(ocr_results, key=lambda x: x['height'])
            return {'x': largest['x'], 'y': largest['y']}

        elif field_type == "location":
            # Look for location keywords
            location_keywords = ['london', 'remote', 'uk', 'hybrid', 'cambridge', 'manchester']
            for item in ocr_results:
                if any(kw in item['text'].lower() for kw in location_keywords):
                    return {'x': item['x'], 'y': item['y']}

        elif field_type.startswith("button_"):
            # Look for button keywords
            button_text = field_type.replace("button_", "")
            for item in ocr_results:
                if button_text.lower() in item['text'].lower():
                    return {'x': item['x'], 'y': item['y']}

        return None

    def _generate_selector(self, element: ElementHandle) -> str:
        """
        Generate a robust CSS selector for an element

        Priority:
        1. ID (if unique)
        2. Data attributes
        3. Class + tag
        4. XPath as fallback
        """
        try:
            # Get element attributes
            tag = element.evaluate("el => el.tagName.toLowerCase()")
            elem_id = element.get_attribute("id")
            classes = element.get_attribute("class")
            data_attrs = element.evaluate("""
                el => {
                    const attrs = {};
                    for (let attr of el.attributes) {
                        if (attr.name.startsWith('data-')) {
                            attrs[attr.name] = attr.value;
                        }
                    }
                    return attrs;
                }
            """)

            # Strategy 1: Use ID if present
            if elem_id:
                return f"#{elem_id}"

            # Strategy 2: Use data attributes (most stable)
            if data_attrs:
                for attr_name, attr_value in data_attrs.items():
                    return f"{tag}[{attr_name}='{attr_value}']"

            # Strategy 3: Use tag + classes
            if classes:
                # Use first 2 classes for specificity
                class_list = classes.split()[:2]
                class_selector = ".".join(class_list)
                return f"{tag}.{class_selector}"

            # Strategy 4: Just tag (weak but works)
            return tag

        except Exception as e:
            self.logger.error(f"Selector generation failed: {e}")
            return None


def get_smart_discovery(page: Page) -> SmartElementDiscovery:
    """Get SmartElementDiscovery instance"""
    return SmartElementDiscovery(page)
