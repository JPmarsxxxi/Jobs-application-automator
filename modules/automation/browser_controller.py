"""
Browser Controller
Orchestrates the application submission process
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from playwright.sync_api import Page

from modules.automation.hybrid_form_analyzer import get_hybrid_analyzer
from modules.automation.form_filler import get_form_filler
from modules.automation.file_uploader import get_file_uploader
from modules.automation.adaptive_scraper import get_adaptive_scraper
from modules.automation.vision_coordinator import get_vision_coordinator
from modules.utils.helpers import human_delay


class BrowserController:
    """Controls browser automation for job applications"""

    def __init__(self, page: Page, user_info: Dict, screenshots_dir: str = "workspace/screenshots"):
        self.page = page
        self.user_info = user_info
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.analyzer = get_hybrid_analyzer()  # OCR/vision form analyzer (fallback)
        self.filler = get_form_filler(user_info, page)
        self.uploader = get_file_uploader(page)
        self.adaptive = get_adaptive_scraper(page, "application")
        self.vision = get_vision_coordinator()  # Llava + Llama coordinator

        # Screenshot directory
        self.screenshots_dir = Path(screenshots_dir)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

        # Action tracking for vision-based recovery
        self.history = []
        self.failed_patterns = []
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3

    def apply_to_job(
        self,
        job_url: str,
        cv_path: str,
        cover_letter_path: str = None,
        dry_run: bool = True
    ) -> Dict:
        """
        Apply to a job posting

        Args:
            job_url: URL of the job posting
            cv_path: Path to CV file
            cover_letter_path: Path to cover letter file (optional)
            dry_run: If True, don't actually submit

        Returns:
            Dict with application result:
            {
                "success": bool,
                "status": str,
                "confirmation": str,
                "error": str,
                "screenshots": [paths]
            }
        """
        self.logger.info(f"{'[DRY RUN] ' if dry_run else ''}Starting application for: {job_url}")

        result = {
            "success": False,
            "status": "not_started",
            "confirmation": None,
            "error": None,
            "screenshots": []
        }

        try:
            # Navigate to job page only if not already there
            # (Browser might already be on this page from scraping phase)
            current_url = self.page.url
            if job_url not in current_url:
                self.logger.info(f"Navigating to job page: {job_url}")
                self.page.goto(job_url, wait_until="domcontentloaded")
                human_delay(2.0, 4.0)
            else:
                self.logger.info("Already on job page from scraping - no navigation needed")
                human_delay(1.0, 2.0)

            # Take initial screenshot
            screenshot_path = self._take_screenshot("01_initial_page")
            result["screenshots"].append(screenshot_path)

            # Detect application type
            app_type = self._detect_application_type()
            self.logger.info(f"Application type detected: {app_type}")

            if app_type == "linkedin_easy_apply":
                return self._handle_linkedin_easy_apply(cv_path, cover_letter_path, dry_run, result)

            elif app_type == "external":
                return self._handle_external_application(cv_path, cover_letter_path, dry_run, result)

            else:
                result["error"] = "Could not detect application type"
                result["status"] = "failed"
                return result

        except Exception as e:
            self.logger.error(f"Application failed: {e}")
            result["error"] = str(e)
            result["status"] = "error"
            return result

    def _handle_linkedin_easy_apply(
        self,
        cv_path: str,
        cover_letter_path: str,
        dry_run: bool,
        result: Dict
    ) -> Dict:
        """Handle LinkedIn Easy Apply flow"""

        try:
            # Click Easy Apply button
            if not self._click_easy_apply_button():
                result["error"] = "Could not find Easy Apply button"
                result["status"] = "failed"
                return result

            human_delay(2.0, 3.0)

            # Take screenshot of first page
            screenshot_path = self._take_screenshot("02_easy_apply_modal")
            result["screenshots"].append(screenshot_path)

            # Multi-page form handling
            page_num = 1
            max_pages = 10  # Safety limit

            while page_num <= max_pages:
                self.logger.info(f"Processing page {page_num}")

                # Analyze current page
                screenshot_path = self._take_screenshot(f"03_page_{page_num}")
                result["screenshots"].append(screenshot_path)

                form_data = self.analyzer.analyze_form(screenshot_path)

                # Check for CAPTCHA
                if self.analyzer.detect_captcha(screenshot_path):
                    self.logger.warning("⚠ CAPTCHA detected - manual intervention required")
                    result["status"] = "captcha_required"
                    human_delay(30.0, 30.0)  # Wait for manual solving
                    continue

                # Fill form fields
                for field in form_data.get("fields", []):
                    self.filler.fill_field(field)
                    human_delay(0.3, 0.6)

                # Handle file uploads
                for upload_label in form_data.get("file_uploads", []):
                    if "resume" in upload_label.lower() or "cv" in upload_label.lower():
                        self.uploader.upload_file(cv_path, upload_label)
                    elif "cover" in upload_label.lower() and cover_letter_path:
                        self.uploader.upload_file(cover_letter_path, upload_label)

                human_delay(1.0, 2.0)

                # Check what buttons are available
                buttons = form_data.get("buttons", [])
                self.logger.debug(f"Buttons found: {buttons}")

                # Check if we're on the last page (Submit/Review button)
                if any(b.lower() in ["submit", "review", "submit application"] for b in buttons):
                    if dry_run:
                        self.logger.info("[DRY RUN] Would submit application here")
                        result["success"] = True
                        result["status"] = "dry_run_complete"
                        result["confirmation"] = "DRY RUN - Application not actually submitted"
                        return result
                    else:
                        # Actually submit
                        if self._click_submit_button():
                            human_delay(3.0, 5.0)

                            # Verify submission
                            screenshot_path = self._take_screenshot("04_confirmation")
                            result["screenshots"].append(screenshot_path)

                            verification = self.analyzer.verify_submission(screenshot_path)

                            result["success"] = verification["success"]
                            result["status"] = "submitted" if verification["success"] else "verification_failed"
                            result["confirmation"] = verification.get("confirmation_message")

                            return result
                        else:
                            result["error"] = "Could not click submit button"
                            result["status"] = "failed"
                            return result

                # Click Next button to continue
                elif any(b.lower() in ["next", "continue"] for b in buttons):
                    if self._click_next_button():
                        human_delay(2.0, 3.0)
                        page_num += 1
                    else:
                        result["error"] = f"Could not click Next button on page {page_num}"
                        result["status"] = "failed"
                        return result

                else:
                    result["error"] = f"Unexpected buttons on page {page_num}: {buttons}"
                    result["status"] = "failed"
                    return result

            # Exceeded max pages
            result["error"] = f"Exceeded maximum pages ({max_pages})"
            result["status"] = "failed"
            return result

        except Exception as e:
            self.logger.error(f"LinkedIn Easy Apply failed: {e}")
            result["error"] = str(e)
            result["status"] = "error"
            return result

    def _handle_external_application(
        self,
        cv_path: str,
        cover_letter_path: str,
        dry_run: bool,
        result: Dict
    ) -> Dict:
        """
        Handle external career page application using OCR/vision.
        Works on ANY career site - Workday, Greenhouse, Lever, etc.
        """
        self.logger.info("Handling external application using OCR/vision")

        try:
            # Take screenshot of current page
            screenshot_path = self._take_screenshot("02_external_page")
            result["screenshots"].append(screenshot_path)

            # Analyze form using OCR/vision
            self.logger.info("Analyzing external application form...")
            form_analysis = self.analyzer.analyze_form(screenshot_path)

            fields = form_analysis.get("fields", [])
            self.logger.info(f"Found {len(fields)} form fields via OCR/vision")

            if dry_run:
                self.logger.info("[DRY RUN] Would fill external application form")
                result["status"] = "dry_run_success"
                result["success"] = True
                return result

            # Fill each field intelligently
            filled_count = 0
            for field in fields:
                field_type = field.get("type", "unknown")
                field_label = field.get("label", "")

                self.logger.debug(f"Processing field: {field_label} ({field_type})")

                # Use form filler to fill the field
                if self.filler.fill_field_intelligent(field):
                    filled_count += 1

            self.logger.info(f"✓ Filled {filled_count}/{len(fields)} fields")

            # Upload files (CV/cover letter)
            if cv_path:
                cv_uploaded = self.uploader.upload_cv(cv_path)
                if not cv_uploaded:
                    self.logger.warning("CV upload failed")

            if cover_letter_path:
                cl_uploaded = self.uploader.upload_cover_letter(cover_letter_path)
                if not cl_uploaded:
                    self.logger.warning("Cover letter upload failed")

            # Click Submit button
            screenshot_path = self._take_screenshot("03_before_submit")
            result["screenshots"].append(screenshot_path)

            if self._click_submit_button():
                human_delay(2.0, 4.0)
                screenshot_path = self._take_screenshot("04_after_submit")
                result["screenshots"].append(screenshot_path)

                result["status"] = "submitted"
                result["success"] = True
                self.logger.info("✓ External application submitted successfully")
            else:
                result["error"] = "Could not find submit button"
                result["status"] = "failed"

            return result

        except Exception as e:
            self.logger.error(f"External application failed: {e}")
            result["error"] = str(e)
            result["status"] = "error"
            return result

    def _detect_application_type(self) -> str:
        """
        Detect application type using Llava (vision) + Llama (decision).
        Works on ANY site - no hardcoded selectors!
        """
        try:
            # Take screenshot
            screenshot_path = self._take_screenshot("detect_app_type")
            current_url = self.page.url

            # Get brief visual description from Llava
            self.logger.info("Using Llava to detect application type...")
            visual_desc = self.vision.get_brief_visual_description(
                screenshot_path,
                goal="Detect application type",
                current_url=current_url
            )

            if not visual_desc:
                # Fallback to URL-based detection
                self.logger.warning("Llava unavailable, using URL-based detection")
                if "linkedin.com" in current_url:
                    return "linkedin_easy_apply"
                else:
                    return "external"

            # Check description for application type indicators
            desc_lower = visual_desc.lower()

            if "easy apply" in desc_lower or "apply now" in desc_lower:
                self.logger.info("✓ Detected Easy Apply via vision")
                return "linkedin_easy_apply"

            if "external" in desc_lower or "company site" in desc_lower or "career page" in desc_lower:
                self.logger.info("✓ Detected external application via vision")
                return "external"

            # Final fallback: check URL
            if "linkedin.com" in current_url:
                return "linkedin_easy_apply"
            else:
                return "external"

        except Exception as e:
            self.logger.error(f"Error detecting application type: {e}")
            return "unknown"

    def _click_button_by_text(self, button_keywords: List[str], button_name: str = "button") -> bool:
        """
        Universal button clicker using Llava (vision) + Llama (decision).
        Works on ANY site!

        Args:
            button_keywords: List of possible button text (e.g., ["Easy Apply", "Apply Now"])
            button_name: Name for logging

        Returns:
            True if clicked successfully
        """
        try:
            # Take screenshot
            screenshot_path = self._take_screenshot(f"find_{button_name}")
            current_url = self.page.url

            # Get visual description from Llava
            self.logger.info(f"Using Llava to find {button_name}...")
            visual_desc = self.vision.get_brief_visual_description(
                screenshot_path,
                goal=f"Find and click {button_name} button",
                current_url=current_url
            )

            # Get DOM elements (buttons/links)
            dom_elements = []
            for elem in self.page.query_selector_all('button, a, [role="button"]'):
                try:
                    text = elem.inner_text()
                    if text and len(text) < 100:  # Filter out long text
                        selector = None
                        # Try to generate selector
                        elem_id = elem.get_attribute('id')
                        if elem_id:
                            selector = f"#{elem_id}"
                        else:
                            elem_class = elem.get_attribute('class')
                            if elem_class:
                                first_class = elem_class.split()[0]
                                selector = f".{first_class}"

                        if selector:
                            dom_elements.append({
                                'type': 'button',
                                'text': text,
                                'selector': selector
                            })
                except:
                    continue

            # Ask Llama to decide which button to click
            goal = f"Click the '{button_keywords[0]}' button to proceed"
            action = self.vision.decide_action(
                visual_description=visual_desc or "Page with interactive elements",
                dom_elements=dom_elements,
                goal=goal,
                current_url=current_url,
                history=self.history,
                failed_patterns=self.failed_patterns
            )

            # Execute the action
            if action.get('action') == 'click':
                selector = action.get('selector')
                if selector:
                    try:
                        elem = self.page.locator(selector).first
                        if elem.is_visible():
                            elem.click()
                            self.logger.info(f"✓ Clicked {button_name} via {selector}")
                            human_delay(1.0, 2.0)
                            self.consecutive_failures = 0
                            return True
                    except Exception as e:
                        self.logger.warning(f"Failed to click {selector}: {e}")

            # Fallback: try keyword matching in DOM
            for elem_data in dom_elements:
                elem_text = elem_data['text'].lower()
                if any(kw.lower() in elem_text for kw in button_keywords):
                    try:
                        selector = elem_data['selector']
                        elem = self.page.locator(selector).first
                        if elem.is_visible():
                            elem.click()
                            self.logger.info(f"✓ Clicked {button_name} via fallback: {selector}")
                            human_delay(1.0, 2.0)
                            self.consecutive_failures = 0
                            return True
                    except:
                        continue

            self.logger.warning(f"Could not find {button_name}")
            self.consecutive_failures += 1
            return False

        except Exception as e:
            self.logger.error(f"Error clicking {button_name}: {e}")
            self.consecutive_failures += 1
            return False

    def _click_easy_apply_button(self) -> bool:
        """Click the Easy Apply button using OCR/vision"""
        return self._click_button_by_text(["Easy Apply", "Apply Now", "Apply"], "Easy Apply")

    def _click_next_button(self) -> bool:
        """Click Next/Continue button using OCR/vision"""
        return self._click_button_by_text(["Next", "Continue", "Proceed", "Review"], "Next")

    def _click_submit_button(self) -> bool:
        """Click final Submit button using OCR/vision"""
        return self._click_button_by_text(["Submit application", "Submit", "Send application", "Apply"], "Submit")

    def _take_screenshot(self, name: str) -> str:
        """Take a screenshot and save it"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.png"
        path = self.screenshots_dir / filename

        try:
            self.page.screenshot(path=str(path), full_page=True)
            self.logger.debug(f"Screenshot saved: {path}")
            return str(path)
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return ""


def get_browser_controller(page: Page, user_info: Dict) -> BrowserController:
    """Get browser controller instance"""
    return BrowserController(page, user_info)
