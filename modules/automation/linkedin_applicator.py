"""
LinkedIn Applicator
Handles LinkedIn Easy Apply automation end-to-end
"""

import logging
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from playwright.sync_api import Page

from modules.automation.browser_controller import get_browser_controller
from modules.scraping.job_models import JobPosting


class LinkedInApplicator:
    """Automates LinkedIn Easy Apply applications"""

    def __init__(self, page: Page, user_info: Dict, tracking_file: str = "workspace/applications_log.csv"):
        self.page = page
        self.user_info = user_info
        self.logger = logging.getLogger(__name__)
        self.controller = get_browser_controller(page, user_info)

        # Tracking file
        self.tracking_file = Path(tracking_file)
        self.tracking_file.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_tracking_file()

    def apply(
        self,
        job: JobPosting,
        cv_path: str,
        cover_letter_path: str = None,
        dry_run: bool = True
    ) -> bool:
        """
        Apply to a job via LinkedIn Easy Apply

        Args:
            job: JobPosting object
            cv_path: Path to CV file
            cover_letter_path: Path to cover letter file
            dry_run: If True, don't actually submit

        Returns:
            True if application successful
        """
        self.logger.info(f"{'[DRY RUN] ' if dry_run else ''}Applying to: {job.company} - {job.title}")

        # Check if Easy Apply is available
        if not job.easy_apply:
            self.logger.warning("Job does not have Easy Apply - skipping")
            self._log_application(job, "skipped", "No Easy Apply option")
            return False

        # Apply using browser controller
        result = self.controller.apply_to_job(
            job_url=job.job_url,
            cv_path=cv_path,
            cover_letter_path=cover_letter_path,
            dry_run=dry_run
        )

        # Log the application
        status = result["status"]
        confirmation = result.get("confirmation", "")
        error = result.get("error", "")

        self._log_application(
            job,
            status,
            confirmation,
            error,
            result.get("screenshots", [])
        )

        # Log result
        if result["success"]:
            self.logger.info(f"✓ Application {'simulated' if dry_run else 'submitted'} successfully")
            self.logger.info(f"  Confirmation: {confirmation}")
        else:
            self.logger.error(f"✗ Application failed: {error}")

        return result["success"]

    def _initialize_tracking_file(self):
        """Initialize CSV tracking file if it doesn't exist"""

        if not self.tracking_file.exists():
            with open(self.tracking_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "company",
                    "title",
                    "location",
                    "job_url",
                    "status",
                    "confirmation",
                    "error",
                    "cv_path",
                    "cover_letter_path",
                    "screenshots"
                ])

    def _log_application(
        self,
        job: JobPosting,
        status: str,
        confirmation: str = "",
        error: str = "",
        screenshots: List[str] = None
    ):
        """Log application to tracking file"""

        try:
            with open(self.tracking_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    job.company,
                    job.title,
                    job.location,
                    job.job_url,
                    status,
                    confirmation,
                    error,
                    "",  # cv_path - filled in by calling code
                    "",  # cover_letter_path - filled in by calling code
                    "|".join(screenshots) if screenshots else ""
                ])

            self.logger.debug(f"Application logged to {self.tracking_file}")

        except Exception as e:
            self.logger.error(f"Failed to log application: {e}")

    def generate_application_report(self) -> Dict:
        """
        Generate summary report of all applications

        Returns:
            Dict with statistics
        """
        try:
            if not self.tracking_file.exists():
                return {"total": 0}

            with open(self.tracking_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            stats = {
                "total": len(rows),
                "submitted": sum(1 for r in rows if r["status"] == "submitted"),
                "dry_run": sum(1 for r in rows if r["status"] == "dry_run_complete"),
                "failed": sum(1 for r in rows if r["status"] in ["failed", "error"]),
                "skipped": sum(1 for r in rows if r["status"] == "skipped"),
                "by_company": {}
            }

            # Count by company
            for row in rows:
                company = row["company"]
                stats["by_company"][company] = stats["by_company"].get(company, 0) + 1

            return stats

        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
            return {"error": str(e)}

    def print_report(self):
        """Print application report to console"""

        report = self.generate_application_report()

        print("\n" + "="*60)
        print("APPLICATION REPORT")
        print("="*60)

        if "error" in report:
            print(f"Error generating report: {report['error']}")
            return

        print(f"\nTotal Applications: {report['total']}")
        print(f"  Submitted:        {report['submitted']}")
        print(f"  Dry Run:          {report['dry_run']}")
        print(f"  Failed:           {report['failed']}")
        print(f"  Skipped:          {report['skipped']}")

        if report.get("by_company"):
            print("\nBy Company:")
            for company, count in sorted(report["by_company"].items(), key=lambda x: x[1], reverse=True):
                print(f"  {company}: {count}")

        print("\n" + "="*60 + "\n")


def get_linkedin_applicator(page: Page, user_info: Dict) -> LinkedInApplicator:
    """Get LinkedIn applicator instance"""
    return LinkedInApplicator(page, user_info)
