"""
Hybrid Form Analyzer
Uses OCR for speed, falls back to vision model when needed
"""

import logging
from typing import Dict
from pathlib import Path

from modules.automation.ocr_analyzer import get_ocr_analyzer, OCR_AVAILABLE
from modules.automation.vision_analyzer import get_vision_analyzer


class HybridFormAnalyzer:
    """Hybrid form analyzer: OCR first, vision fallback"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.vision = get_vision_analyzer()

        # Try to use OCR if available
        self.use_ocr = OCR_AVAILABLE
        if self.use_ocr:
            try:
                self.ocr = get_ocr_analyzer()
                self.logger.info("✓ OCR available - using hybrid analysis (10x faster)")
            except Exception as e:
                self.logger.warning(f"OCR not available: {e}")
                self.use_ocr = False

        if not self.use_ocr:
            self.logger.info("OCR not available - using vision-only analysis")

    def analyze_form(self, screenshot_path: str) -> Dict:
        """
        Analyze form using hybrid approach

        Strategy:
        1. Try OCR first (fast - ~200ms)
        2. If OCR confidence is high, use OCR results
        3. If OCR confidence is low, fall back to vision model (~2-5s)

        Args:
            screenshot_path: Path to screenshot

        Returns:
            Form structure dict
        """
        if self.use_ocr:
            # Try OCR first
            self.logger.debug("Attempting OCR analysis...")
            ocr_result = self.ocr.analyze_form_fast(screenshot_path)

            # Check if OCR was successful
            confidence = ocr_result.get('ocr_confidence', 'none')
            num_fields = len(ocr_result.get('fields', []))

            if confidence == 'high' and num_fields > 0:
                self.logger.info(f"✓ OCR analysis successful ({num_fields} fields)")
                return ocr_result

            # OCR failed or low confidence
            self.logger.debug(f"OCR confidence low ({confidence}), falling back to vision model")

        # Fall back to vision model
        self.logger.debug("Using vision model analysis...")
        return self.vision.analyze_form(screenshot_path)

    def detect_buttons(self, screenshot_path: str) -> list:
        """
        Detect buttons - OCR is usually good enough for this

        Args:
            screenshot_path: Path to screenshot

        Returns:
            List of button texts
        """
        if self.use_ocr:
            ocr_results = self.ocr.extract_text_with_boxes(screenshot_path)
            buttons = self.ocr.find_buttons(ocr_results)
            if buttons:
                return buttons

        # Fallback: parse from full form analysis
        form_data = self.vision.analyze_form(screenshot_path)
        return form_data.get('buttons', [])

    def detect_captcha(self, screenshot_path: str) -> bool:
        """
        Detect CAPTCHA - vision model is better for this

        Args:
            screenshot_path: Path to screenshot

        Returns:
            True if CAPTCHA detected
        """
        return self.vision.detect_captcha(screenshot_path)

    def verify_submission(self, screenshot_path: str) -> Dict:
        """
        Verify submission - use vision for accuracy

        Args:
            screenshot_path: Path to screenshot

        Returns:
            Verification result dict
        """
        return self.vision.verify_submission(screenshot_path)


def get_hybrid_analyzer() -> HybridFormAnalyzer:
    """Get hybrid analyzer instance"""
    return HybridFormAnalyzer()
