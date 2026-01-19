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
from modules.utils.helpers import human_delay


class BrowserController:
    """Controls browser automation for job applications"""

    def __init__(self, page: Page, user_info: Dict, screenshots_dir: str = "workspace/screenshots"):
        self.page = page
        self.user_info = user_info
        self.logger = logging.getLogger(__name__)

        # Initialize components - use hybrid analyzer for speed
        self.analyzer = get_hybrid_analyzer()
        self.filler = get_form_filler(user_info, page)
        self.uploader = get_file_uploader(page)

        # Screenshot directory
        self.screenshots_dir = Path(screenshots_dir)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

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
        """Handle external career page application"""

        self.logger.warning("External applications not fully implemented yet")
        result["status"] = "not_implemented"
        result["error"] = "External application handling coming in future update"
        return result

    def _detect_application_type(self) -> str:
        """Detect what type of application this is"""

        try:
            # Check for LinkedIn Easy Apply button
            easy_apply_selectors = [
                "button.jobs-apply-button",
                "button[aria-label*='Easy Apply']",
                "button:has-text('Easy Apply')",
            ]

            for selector in easy_apply_selectors:
                if self.page.locator(selector).first.is_visible():
                    return "linkedin_easy_apply"

        except:
            pass

        # Check if we're on an external site
        url = self.page.url
        if "linkedin.com" not in url:
            return "external"

        return "unknown"

    def _click_easy_apply_button(self) -> bool:
        """Click the Easy Apply button"""

        selectors = [
            "button.jobs-apply-button",
            "button[aria-label*='Easy Apply']",
            "button:has-text('Easy Apply')",
        ]

        for selector in selectors:
            try:
                button = self.page.locator(selector).first
                if button.is_visible():
                    button.click()
                    self.logger.info("✓ Clicked Easy Apply button")
                    return True
            except:
                continue

        return False

    def _click_next_button(self) -> bool:
        """Click Next/Continue button"""

        selectors = [
            "button[aria-label*='Continue']",
            "button[aria-label*='Next']",
            "button:has-text('Next')",
            "button:has-text('Continue')",
            "button:has-text('Proceed')",
        ]

        for selector in selectors:
            try:
                button = self.page.locator(selector).first
                if button.is_visible():
                    button.click()
                    self.logger.info("✓ Clicked Next button")
                    return True
            except:
                continue

        return False

    def _click_submit_button(self) -> bool:
        """Click final Submit button"""

        selectors = [
            "button[aria-label*='Submit application']",
            "button[aria-label*='Submit']",
            "button:has-text('Submit application')",
            "button:has-text('Submit')",
            "button:has-text('Send application')",
        ]

        for selector in selectors:
            try:
                button = self.page.locator(selector).first
                if button.is_visible():
                    button.click()
                    self.logger.info("✓ Clicked Submit button")
                    return True
            except:
                continue

        return False

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
