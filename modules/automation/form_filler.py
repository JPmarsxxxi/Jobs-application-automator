"""
Form Filler
Intelligently fills application form fields based on user information
"""

import logging
import re
import time
import random
from typing import Dict, List, Optional, Any
from playwright.sync_api import Page, Locator

from modules.utils.helpers import human_delay


class FormFiller:
    """Fills application forms with user data"""

    def __init__(self, user_info: Dict[str, Any], page: Page):
        self.user_info = user_info
        self.page = page
        self.logger = logging.getLogger(__name__)

        # Field mapping: common field labels -> user_info keys
        self.field_mapping = {
            # Name fields
            "first name": "first_name",
            "firstname": "first_name",
            "given name": "first_name",
            "last name": "last_name",
            "lastname": "last_name",
            "surname": "last_name",
            "family name": "last_name",
            "full name": "name",
            "name": "name",

            # Contact fields
            "email": "email",
            "email address": "email",
            "phone": "phone",
            "phone number": "phone",
            "mobile": "phone",
            "telephone": "phone",

            # Location fields
            "city": "city",
            "country": "country",
            "location": "location",
            "address": "location",

            # Professional fields
            "linkedin": "linkedin",
            "linkedin url": "linkedin",
            "linkedin profile": "linkedin",
            "github": "github",
            "github url": "github",
            "portfolio": "portfolio",
            "website": "portfolio",

            # Education
            "university": "university",
            "college": "university",
            "school": "university",
            "degree": "degree",
            "graduation year": "graduation_year",
            "graduation date": "graduation_year",

            # Work authorization
            "work authorization": "work_authorization",
            "authorized to work": "work_authorization",
            "visa status": "visa_status",
            "require sponsorship": "requires_sponsorship",
            "sponsorship": "requires_sponsorship",
        }

    def fill_field(self, field_data: Dict, selector: str = None) -> bool:
        """
        Fill a single form field

        Args:
            field_data: Field information from vision analyzer
            selector: CSS selector for the field (if known)

        Returns:
            True if field was filled successfully
        """
        field_label = field_data.get("label", "").lower()
        field_type = field_data.get("type", "text")
        required = field_data.get("required", False)

        self.logger.debug(f"Filling field: {field_label} (type: {field_type}, required: {required})")

        # Get value for this field
        value = self._get_field_value(field_label, field_type, field_data)

        if not value:
            if required:
                self.logger.warning(f"No value found for required field: {field_label}")
            return False

        # Find the field element
        element = self._find_field_element(field_label, field_type, selector)
        if not element:
            self.logger.warning(f"Could not find element for field: {field_label}")
            return False

        # Fill based on field type
        try:
            if field_type in ["text", "email", "phone", "textarea"]:
                return self._fill_text_field(element, value)

            elif field_type == "dropdown":
                return self._fill_dropdown(element, value, field_data.get("options", []))

            elif field_type == "checkbox":
                return self._fill_checkbox(element, value)

            elif field_type == "radio":
                return self._fill_radio(element, value)

            else:
                self.logger.warning(f"Unsupported field type: {field_type}")
                return False

        except Exception as e:
            self.logger.error(f"Error filling field {field_label}: {e}")
            return False

    def _get_field_value(self, field_label: str, field_type: str, field_data: Dict) -> Optional[str]:
        """Determine what value to enter for a field"""

        # Check direct mapping
        for pattern, key in self.field_mapping.items():
            if pattern in field_label:
                value = self.user_info.get(key)
                if value:
                    return str(value)

        # Handle special cases
        if "year" in field_label and "experience" in field_label:
            # Years of experience
            return self._calculate_years_of_experience()

        if "notice" in field_label or "availability" in field_label:
            # Notice period / availability
            return "Immediate" if self.user_info.get("currently_employed") == "No" else "2 weeks"

        if "salary" in field_label:
            # Salary expectation
            return self.user_info.get("salary_expectation", "Negotiable")

        if "relocation" in field_label or "relocate" in field_label:
            return "Yes" if self.user_info.get("willing_to_relocate", True) else "No"

        if "remote" in field_label:
            return "Yes"

        # Dropdown options matching
        if field_type == "dropdown":
            options = field_data.get("options", [])
            if options:
                return self._match_dropdown_option(field_label, options)

        return None

    def _fill_text_field(self, element: Locator, value: str) -> bool:
        """Fill a text input field with human-like typing"""
        try:
            # Click to focus
            element.click()
            human_delay(0.3, 0.6)

            # Clear existing value
            element.fill("")
            human_delay(0.2, 0.4)

            # Type with random delays (human-like)
            for char in value:
                element.type(char, delay=random.randint(50, 150))

            human_delay(0.2, 0.4)
            self.logger.debug(f"✓ Filled text field with: {value}")
            return True

        except Exception as e:
            self.logger.error(f"Text field filling failed: {e}")
            return False

    def _fill_dropdown(self, element: Locator, value: str, options: List[str]) -> bool:
        """Select option from dropdown"""
        try:
            # Click to open dropdown
            element.click()
            human_delay(0.5, 1.0)

            # Try to select by value
            try:
                element.select_option(value)
                self.logger.debug(f"✓ Selected dropdown option: {value}")
                return True
            except:
                pass

            # Try to find matching option
            best_match = self._find_best_option_match(value, options)
            if best_match:
                try:
                    element.select_option(label=best_match)
                    self.logger.debug(f"✓ Selected dropdown option: {best_match}")
                    return True
                except:
                    pass

            self.logger.warning(f"Could not select dropdown value: {value}")
            return False

        except Exception as e:
            self.logger.error(f"Dropdown filling failed: {e}")
            return False

    def _fill_checkbox(self, element: Locator, value: Any) -> bool:
        """Check or uncheck a checkbox"""
        try:
            should_check = self._parse_boolean(value)

            if should_check and not element.is_checked():
                element.check()
                self.logger.debug("✓ Checked checkbox")
            elif not should_check and element.is_checked():
                element.uncheck()
                self.logger.debug("✓ Unchecked checkbox")

            human_delay(0.3, 0.6)
            return True

        except Exception as e:
            self.logger.error(f"Checkbox filling failed: {e}")
            return False

    def _fill_radio(self, element: Locator, value: str) -> bool:
        """Select a radio button"""
        try:
            element.check()
            human_delay(0.3, 0.6)
            self.logger.debug(f"✓ Selected radio button: {value}")
            return True

        except Exception as e:
            self.logger.error(f"Radio button filling failed: {e}")
            return False

    def _find_field_element(self, field_label: str, field_type: str, selector: str = None) -> Optional[Locator]:
        """Find form field element by label or selector"""

        if selector:
            try:
                return self.page.locator(selector).first
            except:
                pass

        # Try to find by label text
        label_selectors = [
            f"label:has-text('{field_label}') ~ input",
            f"label:has-text('{field_label}') ~ select",
            f"label:has-text('{field_label}') ~ textarea",
            f"input[placeholder*='{field_label}']",
            f"input[aria-label*='{field_label}']",
            f"input[name*='{field_label.replace(' ', '_')}']",
            f"select[name*='{field_label.replace(' ', '_')}']",
        ]

        for selector in label_selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible():
                    return element
            except:
                continue

        return None

    def _match_dropdown_option(self, field_label: str, options: List[str]) -> Optional[str]:
        """Match user info to dropdown options"""

        # Education level
        if "education" in field_label or "degree" in field_label:
            degree = self.user_info.get("degree", "").lower()
            if "master" in degree or "msc" in degree:
                for opt in options:
                    if "master" in opt.lower():
                        return opt
            elif "bachelor" in degree or "bsc" in degree:
                for opt in options:
                    if "bachelor" in opt.lower():
                        return opt

        # Experience level
        if "experience" in field_label:
            years = self._calculate_years_of_experience()
            try:
                years_int = int(years.split()[0]) if years else 0

                for opt in options:
                    opt_lower = opt.lower()
                    if years_int < 2 and ("0-2" in opt_lower or "entry" in opt_lower or "junior" in opt_lower):
                        return opt
                    elif 2 <= years_int < 5 and ("2-5" in opt_lower or "mid" in opt_lower):
                        return opt
                    elif years_int >= 5 and ("5+" in opt_lower or "senior" in opt_lower):
                        return opt
            except:
                pass

        # Default: return first option
        return options[0] if options else None

    def _find_best_option_match(self, value: str, options: List[str]) -> Optional[str]:
        """Find best matching option from list"""
        value_lower = value.lower()

        # Exact match
        for opt in options:
            if opt.lower() == value_lower:
                return opt

        # Contains match
        for opt in options:
            if value_lower in opt.lower() or opt.lower() in value_lower:
                return opt

        return None

    def _calculate_years_of_experience(self) -> str:
        """Calculate years of experience from user info"""
        # This is a placeholder - implement based on user_info structure
        work_experience = self.user_info.get("years_of_experience")
        if work_experience:
            return str(work_experience)

        # Try to calculate from work history
        # For now, return a default
        return "2"

    def _parse_boolean(self, value: Any) -> bool:
        """Parse various representations of boolean"""
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.lower() in ["yes", "true", "1", "y"]

        return bool(value)


def get_form_filler(user_info: Dict[str, Any], page: Page) -> FormFiller:
    """Get form filler instance"""
    return FormFiller(user_info, page)
