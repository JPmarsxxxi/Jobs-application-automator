"""
Vision-based Form Analyzer
Uses LLaVA vision model to analyze application forms and identify fields
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from modules.generation.ollama_client import OllamaClient, get_ollama_client


class VisionFormAnalyzer:
    """Analyzes application forms using vision model"""

    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        self.ollama = ollama_client or get_ollama_client()
        self.logger = logging.getLogger(__name__)

    def analyze_form(self, screenshot_path: str) -> Dict:
        """
        Analyze an application form screenshot and identify all fields

        Args:
            screenshot_path: Path to screenshot of the form

        Returns:
            Dict with form structure:
            {
                "fields": [
                    {
                        "label": "First Name",
                        "type": "text",
                        "required": true,
                        "placeholder": "",
                        "options": []  # For dropdowns
                    },
                    ...
                ],
                "buttons": ["Next", "Submit"],
                "file_uploads": ["Resume", "Cover Letter"],
                "page_number": 1,
                "total_pages": 3
            }
        """
        self.logger.info(f"Analyzing form screenshot: {screenshot_path}")

        prompt = """You are analyzing a job application form. Look at this screenshot and identify ALL visible form fields.

For EACH field you see, provide:
1. The field label/name (e.g., "First Name", "Email Address", "Years of Experience")
2. The field type (text, email, phone, dropdown, checkbox, radio, textarea, file_upload)
3. Whether it's required (look for red asterisks * or "required" text)
4. Any placeholder text visible
5. For dropdowns, list the visible options

Also identify:
- Any buttons (Next, Submit, Cancel, etc.)
- File upload fields (Resume, Cover Letter, etc.)
- Page indicators (e.g., "Page 1 of 3")

Return ONLY valid JSON in this exact format:
{
    "fields": [
        {
            "label": "First Name",
            "type": "text",
            "required": true,
            "placeholder": "Enter your first name",
            "options": []
        }
    ],
    "buttons": ["Next"],
    "file_uploads": ["Resume"],
    "page_number": 1,
    "total_pages": 1
}

Do NOT include any explanation, only the JSON."""

        try:
            response = self.ollama.analyze_image(
                image_path=screenshot_path,
                prompt=prompt
            )

            # Parse JSON response
            form_data = self._parse_form_response(response)

            self.logger.info(f"✓ Identified {len(form_data.get('fields', []))} fields")
            return form_data

        except Exception as e:
            self.logger.error(f"Form analysis failed: {e}")
            return self._empty_form()

    def analyze_field_value(self, screenshot_path: str, field_label: str) -> str:
        """
        Analyze a specific field to determine what value should be entered

        Args:
            screenshot_path: Path to screenshot
            field_label: Label of the field to analyze

        Returns:
            Suggested value or empty string
        """
        prompt = f"""Look at this form field labeled "{field_label}".

What type of information is this field asking for?
If it's a dropdown, what are the available options?
If it has placeholder text or hints, what are they?

Return a brief description of what should be entered in this field."""

        try:
            response = self.ollama.analyze_image(
                image_path=screenshot_path,
                prompt=prompt
            )
            return response.strip()

        except Exception as e:
            self.logger.error(f"Field analysis failed: {e}")
            return ""

    def detect_captcha(self, screenshot_path: str) -> bool:
        """
        Detect if there's a CAPTCHA on the page

        Args:
            screenshot_path: Path to screenshot

        Returns:
            True if CAPTCHA detected
        """
        prompt = """Look at this screenshot. Is there a CAPTCHA challenge visible?
This could be:
- reCAPTCHA ("I'm not a robot" checkbox)
- Image selection (select all traffic lights, etc.)
- Text CAPTCHA
- hCaptcha

Answer with ONLY "yes" or "no"."""

        try:
            response = self.ollama.analyze_image(
                image_path=screenshot_path,
                prompt=prompt
            )
            return "yes" in response.lower()

        except Exception as e:
            self.logger.debug(f"CAPTCHA detection failed: {e}")
            return False

    def verify_submission(self, screenshot_path: str) -> Dict[str, any]:
        """
        Verify if application was successfully submitted

        Args:
            screenshot_path: Path to confirmation page screenshot

        Returns:
            Dict with verification result:
            {
                "success": bool,
                "confirmation_message": str,
                "confirmation_number": str or None
            }
        """
        prompt = """Look at this screenshot. Does it show a successful job application submission?

Look for:
- Success messages ("Application submitted", "Thank you", etc.)
- Confirmation numbers or reference IDs
- "Next steps" information
- Error messages (if submission failed)

Return ONLY valid JSON:
{
    "success": true,
    "confirmation_message": "Your application has been submitted",
    "confirmation_number": "APP-12345"
}

If submission failed:
{
    "success": false,
    "confirmation_message": "Error: Please fill all required fields",
    "confirmation_number": null
}"""

        try:
            response = self.ollama.analyze_image(
                image_path=screenshot_path,
                prompt=prompt
            )

            verification = self._parse_verification_response(response)

            if verification["success"]:
                self.logger.info("✓ Application submission confirmed")
            else:
                self.logger.warning(f"⚠ Submission verification: {verification['confirmation_message']}")

            return verification

        except Exception as e:
            self.logger.error(f"Submission verification failed: {e}")
            return {
                "success": False,
                "confirmation_message": f"Verification error: {e}",
                "confirmation_number": None
            }

    def _parse_form_response(self, response: str) -> Dict:
        """Parse JSON response from vision model"""
        try:
            # Try to extract JSON from response
            # Sometimes the model includes extra text
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                form_data = json.loads(json_str)

                # Validate structure
                if "fields" not in form_data:
                    form_data["fields"] = []
                if "buttons" not in form_data:
                    form_data["buttons"] = []
                if "file_uploads" not in form_data:
                    form_data["file_uploads"] = []
                if "page_number" not in form_data:
                    form_data["page_number"] = 1
                if "total_pages" not in form_data:
                    form_data["total_pages"] = 1

                return form_data
            else:
                self.logger.warning("No JSON found in response, returning empty form")
                return self._empty_form()

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing failed: {e}")
            self.logger.debug(f"Response was: {response}")
            return self._empty_form()

    def _parse_verification_response(self, response: str) -> Dict:
        """Parse verification response from vision model"""
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                verification = json.loads(json_str)

                # Ensure required fields
                if "success" not in verification:
                    verification["success"] = False
                if "confirmation_message" not in verification:
                    verification["confirmation_message"] = ""
                if "confirmation_number" not in verification:
                    verification["confirmation_number"] = None

                return verification
            else:
                return {
                    "success": False,
                    "confirmation_message": "Could not parse verification",
                    "confirmation_number": None
                }

        except json.JSONDecodeError as e:
            self.logger.error(f"Verification parsing failed: {e}")
            return {
                "success": False,
                "confirmation_message": f"Parse error: {e}",
                "confirmation_number": None
            }

    def _empty_form(self) -> Dict:
        """Return empty form structure"""
        return {
            "fields": [],
            "buttons": [],
            "file_uploads": [],
            "page_number": 1,
            "total_pages": 1
        }


def get_vision_analyzer() -> VisionFormAnalyzer:
    """Get singleton vision analyzer instance"""
    return VisionFormAnalyzer()
