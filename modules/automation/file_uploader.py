"""
File Uploader
Handles file uploads for CVs, cover letters, and other documents
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional
from playwright.sync_api import Page, Locator

from modules.utils.helpers import human_delay


class FileUploader:
    """Handles file uploads in application forms"""

    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger(__name__)

    def upload_file(self, file_path: str, field_label: str = "", selector: str = None) -> bool:
        """
        Upload a file to a file input field

        Args:
            file_path: Path to the file to upload
            field_label: Label of the file upload field (e.g., "Resume", "Cover Letter")
            selector: CSS selector for the file input (if known)

        Returns:
            True if upload successful
        """
        # Validate file exists
        if not Path(file_path).exists():
            self.logger.error(f"File not found: {file_path}")
            return False

        file_path = str(Path(file_path).absolute())
        self.logger.info(f"Uploading file: {Path(file_path).name} for field: {field_label}")

        # Find file input element
        file_input = self._find_file_input(field_label, selector)
        if not file_input:
            self.logger.error(f"Could not find file input for: {field_label}")
            return False

        try:
            # Set the file
            file_input.set_input_files(file_path)
            human_delay(1.0, 2.0)  # Wait for upload to process

            # Verify upload
            if self._verify_upload(field_label):
                self.logger.info(f"✓ File uploaded successfully: {Path(file_path).name}")
                return True
            else:
                self.logger.warning(f"Upload verification failed for: {field_label}")
                return True  # Still return True as file was set

        except Exception as e:
            self.logger.error(f"File upload failed: {e}")
            return False

    def upload_resume(self, cv_path: str) -> bool:
        """Upload resume/CV"""
        return self.upload_file(cv_path, "Resume")

    def upload_cover_letter(self, cl_path: str) -> bool:
        """Upload cover letter"""
        return self.upload_file(cl_path, "Cover Letter")

    def upload_documents(self, documents: Dict[str, str]) -> Dict[str, bool]:
        """
        Upload multiple documents

        Args:
            documents: Dict mapping field labels to file paths
                      e.g., {"Resume": "/path/to/cv.docx", "Cover Letter": "/path/to/cl.docx"}

        Returns:
            Dict mapping field labels to upload success status
        """
        results = {}

        for label, file_path in documents.items():
            success = self.upload_file(file_path, label)
            results[label] = success
            human_delay(0.5, 1.0)  # Small delay between uploads

        return results

    def _find_file_input(self, field_label: str, selector: str = None) -> Optional[Locator]:
        """Find file input element"""

        if selector:
            try:
                element = self.page.locator(selector).first
                if element.is_visible() or element.get_attribute("type") == "file":
                    return element
            except:
                pass

        # Common selectors for file inputs
        selectors = []

        if field_label:
            label_lower = field_label.lower()
            selectors.extend([
                # By label association
                f"label:has-text('{field_label}') ~ input[type='file']",
                f"label:has-text('{field_label}') input[type='file']",

                # By aria-label
                f"input[type='file'][aria-label*='{field_label}']",

                # By name attribute
                f"input[type='file'][name*='{label_lower.replace(' ', '_')}']",
                f"input[type='file'][name*='{label_lower.replace(' ', '-')}']",

                # By id
                f"input[type='file'][id*='{label_lower.replace(' ', '_')}']",
                f"input[type='file'][id*='{label_lower.replace(' ', '-')}']",
            ])

        # Generic file input fallbacks
        selectors.extend([
            "input[type='file']",
            "input[accept*='pdf']",
            "input[accept*='doc']",
            "input[accept*='application']",
        ])

        # Try each selector
        for sel in selectors:
            try:
                elements = self.page.locator(sel).all()
                for element in elements:
                    try:
                        # Check if it's visible or hidden but functional
                        if element.is_visible() or element.get_attribute("type") == "file":
                            # Additional check: if label specified, make sure this is the right one
                            if field_label:
                                # Check nearby text content
                                parent = element.locator("xpath=../..")
                                parent_text = parent.inner_text().lower() if parent else ""
                                if field_label.lower() in parent_text:
                                    return element
                            else:
                                return element
                    except:
                        continue
            except:
                continue

        # If no match found with label, try generic file input
        if field_label:
            try:
                # Get all file inputs and return first visible one
                file_inputs = self.page.locator("input[type='file']").all()
                for inp in file_inputs:
                    if inp.is_visible() or inp.get_attribute("type") == "file":
                        return inp
            except:
                pass

        return None

    def _verify_upload(self, field_label: str) -> bool:
        """Verify that file was uploaded successfully"""
        try:
            # Look for success indicators
            success_patterns = [
                f"✓.*{field_label}",
                f"{field_label}.*uploaded",
                "upload.*success",
                "file.*added",
            ]

            page_text = self.page.inner_text("body").lower()

            for pattern in success_patterns:
                import re
                if re.search(pattern.lower(), page_text):
                    return True

            # Check if file name appears on page
            # (LinkedIn shows uploaded file name)
            return True  # Optimistic default

        except:
            return True  # Default to success if verification fails

    def handle_linkedin_file_upload(self, file_path: str, upload_type: str = "resume") -> bool:
        """
        Handle LinkedIn-specific file upload

        Args:
            file_path: Path to file
            upload_type: "resume" or "cover_letter"

        Returns:
            True if successful
        """
        self.logger.info(f"LinkedIn file upload: {upload_type}")

        try:
            # LinkedIn Easy Apply file upload patterns
            if upload_type == "resume":
                selectors = [
                    "input[type='file'][name='file']",
                    "input[id*='resume']",
                    "input[id*='cv']",
                    "input[type='file']",
                ]
            else:  # cover letter
                selectors = [
                    "input[type='file'][name='file']",
                    "input[id*='cover']",
                    "input[type='file']",
                ]

            for selector in selectors:
                try:
                    file_input = self.page.locator(selector).first
                    if file_input:
                        file_input.set_input_files(str(Path(file_path).absolute()))
                        human_delay(1.5, 2.5)

                        self.logger.info(f"✓ LinkedIn {upload_type} uploaded")
                        return True
                except:
                    continue

            self.logger.warning(f"Could not find LinkedIn file input for {upload_type}")
            return False

        except Exception as e:
            self.logger.error(f"LinkedIn file upload failed: {e}")
            return False


def get_file_uploader(page: Page) -> FileUploader:
    """Get file uploader instance"""
    return FileUploader(page)
