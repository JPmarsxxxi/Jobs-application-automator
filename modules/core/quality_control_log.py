"""
Quality Control Log System

This module generates a detailed log of all materials created during a run.
The log is overwritten on each new run for easy review.

The user can review this log to ensure quality before moving to automatic mode.
"""

import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class QualityControlLog:
    """
    Generates a detailed, human-readable log of all bot activities
    for quality control and review purposes.
    """

    def __init__(self, log_path: str = "workspace/logs/QUALITY_CONTROL_LOG.md"):
        self.log_path = Path(log_path)
        self.log_entries: List[Dict[str, Any]] = []
        self.run_start_time = datetime.now()
        self.stats = {
            "jobs_scraped": 0,
            "cvs_generated": 0,
            "cover_letters_generated": 0,
            "applications_attempted": 0,
            "applications_successful": 0,
            "applications_failed": 0,
            "emails_sent": 0,
        }

    def start_run(self, mode: str, region: str, platforms: List[str]):
        """Initialize a new run and overwrite the log file"""
        self.run_start_time = datetime.now()
        self.log_entries = []
        self.stats = {
            "jobs_scraped": 0,
            "cvs_generated": 0,
            "cover_letters_generated": 0,
            "applications_attempted": 0,
            "applications_successful": 0,
            "applications_failed": 0,
            "emails_sent": 0,
        }

        # Create header
        header = f"""# QUALITY CONTROL LOG
# Job Application Bot - Detailed Activity Report

**Run Started:** {self.run_start_time.strftime("%Y-%m-%d %H:%M:%S")}
**Mode:** {mode.upper()}
**Region:** {region.upper()}
**Platforms:** {", ".join(platforms)}

---

## RUN SUMMARY
This log will be updated throughout the run with detailed information about:
- Jobs discovered and scraped
- CVs and cover letters generated (with full content preview)
- Application forms filled (field-by-field details)
- Networking emails sent
- Success/failure status for each action

**NOTE:** This log is overwritten on each new run. Review it before starting the next run.

---

"""
        # Write header immediately
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "w", encoding="utf-8") as f:
            f.write(header)

    def log_job_scraped(
        self,
        job_id: str,
        platform: str,
        company: str,
        title: str,
        location: str,
        job_url: str,
        description: str,
        keywords_extracted: List[str],
    ):
        """Log a job that was scraped"""
        self.stats["jobs_scraped"] += 1

        entry = f"""
## JOB #{self.stats["jobs_scraped"]}: {company} - {title}

**Platform:** {platform}
**Location:** {location}
**URL:** {job_url}
**Job ID:** {job_id}
**Timestamp:** {datetime.now().strftime("%H:%M:%S")}

### Job Description (First 500 chars):
```
{description[:500]}...
```

### Keywords Extracted:
{", ".join(keywords_extracted)}

---

"""
        self._append_to_log(entry)

    def log_cv_generated(
        self,
        job_id: str,
        company: str,
        cv_file_path: str,
        matched_projects: List[str],
        cv_content_preview: str,
        ats_score: Optional[float] = None,
    ):
        """Log a CV that was generated"""
        self.stats["cvs_generated"] += 1

        entry = f"""
### CV GENERATED for {company}

**File:** `{cv_file_path}`
**Matched Projects:** {", ".join(matched_projects)}
**ATS Optimization Score:** {ats_score if ats_score else "N/A"}/10

#### CV Content Preview (First 1000 chars):
```
{cv_content_preview[:1000]}...
```

#### Projects Highlighted:
"""
        for project in matched_projects:
            entry += f"- {project}\n"

        entry += "\n---\n\n"
        self._append_to_log(entry)

    def log_cover_letter_generated(
        self,
        job_id: str,
        company: str,
        cover_letter_file_path: str,
        cover_letter_content: str,
    ):
        """Log a cover letter that was generated"""
        self.stats["cover_letters_generated"] += 1

        entry = f"""
### COVER LETTER GENERATED for {company}

**File:** `{cover_letter_file_path}`

#### Full Cover Letter Content:
```
{cover_letter_content}
```

---

"""
        self._append_to_log(entry)

    def log_application_form_analysis(
        self, job_id: str, company: str, form_fields: Dict[str, Any], screenshot_path: str
    ):
        """Log the form analysis from vision model"""
        entry = f"""
### APPLICATION FORM ANALYSIS for {company}

**Screenshot:** `{screenshot_path}`

#### Fields Detected by Vision Model:
"""
        if "text_fields" in form_fields:
            entry += "\n**Text Fields:**\n"
            for field in form_fields["text_fields"]:
                entry += f"- {field.get('label', 'Unknown')}: {field.get('value', 'N/A')}\n"

        if "file_uploads" in form_fields:
            entry += "\n**File Upload Fields:**\n"
            for field in form_fields["file_uploads"]:
                entry += f"- {field.get('label', 'Unknown')}: {field.get('accepts', 'Any')}\n"

        if "dropdowns" in form_fields:
            entry += "\n**Dropdowns:**\n"
            for field in form_fields["dropdowns"]:
                entry += f"- {field.get('label', 'Unknown')}: Selected '{field.get('select', 'N/A')}'\n"

        if "checkboxes" in form_fields:
            entry += "\n**Checkboxes:**\n"
            for field in form_fields["checkboxes"]:
                checked = "✓" if field.get("checked") else "✗"
                entry += f"- {checked} {field.get('label', 'Unknown')}\n"

        entry += "\n---\n\n"
        self._append_to_log(entry)

    def log_application_submitted(
        self,
        job_id: str,
        company: str,
        title: str,
        success: bool,
        error_message: Optional[str] = None,
        confirmation_screenshot: Optional[str] = None,
    ):
        """Log application submission result"""
        if success:
            self.stats["applications_successful"] += 1
            status = "✅ SUCCESS"
        else:
            self.stats["applications_failed"] += 1
            status = "❌ FAILED"

        self.stats["applications_attempted"] += 1

        entry = f"""
### APPLICATION SUBMISSION: {status}

**Company:** {company}
**Title:** {title}
**Job ID:** {job_id}
**Timestamp:** {datetime.now().strftime("%H:%M:%S")}
"""

        if success:
            entry += f"**Confirmation Screenshot:** `{confirmation_screenshot}`\n"
            entry += "**Status:** Application submitted successfully!\n"
        else:
            entry += f"**Error:** {error_message}\n"
            entry += "**Action Required:** Manual review needed\n"

        entry += "\n---\n\n"
        self._append_to_log(entry)

    def log_networking_email(
        self,
        company: str,
        recruiter_name: str,
        recruiter_email: str,
        email_subject: str,
        email_body: str,
        sent: bool,
    ):
        """Log networking email sent"""
        if sent:
            self.stats["emails_sent"] += 1
            status = "✅ SENT"
        else:
            status = "❌ NOT SENT"

        entry = f"""
### NETWORKING EMAIL: {status}

**Company:** {company}
**Recipient:** {recruiter_name} ({recruiter_email})
**Subject:** {email_subject}

#### Email Content:
```
{email_body}
```

---

"""
        self._append_to_log(entry)

    def finalize_run(self):
        """Finalize the log with summary statistics"""
        run_end_time = datetime.now()
        duration = run_end_time - self.run_start_time

        summary = f"""

# RUN COMPLETED

**Run Ended:** {run_end_time.strftime("%Y-%m-%d %H:%M:%S")}
**Total Duration:** {duration}

## FINAL STATISTICS

| Metric | Count |
|--------|-------|
| Jobs Scraped | {self.stats["jobs_scraped"]} |
| CVs Generated | {self.stats["cvs_generated"]} |
| Cover Letters Generated | {self.stats["cover_letters_generated"]} |
| Applications Attempted | {self.stats["applications_attempted"]} |
| Applications Successful | {self.stats["applications_successful"]} |
| Applications Failed | {self.stats["applications_failed"]} |
| Networking Emails Sent | {self.stats["emails_sent"]} |

**Success Rate:** {
    (self.stats["applications_successful"] / self.stats["applications_attempted"] * 100)
    if self.stats["applications_attempted"] > 0
    else 0
:.1f}%

---

## QUALITY CONTROL CHECKLIST

Before enabling automatic mode, please review:

- [ ] Are the generated CVs high quality and ATS-optimized?
- [ ] Are the cover letters personalized and professional?
- [ ] Are the correct projects being matched to jobs?
- [ ] Are form fields being filled correctly?
- [ ] Are the networking emails appropriate and professional?
- [ ] Are there any patterns in failed applications?

**Next Steps:**
1. Review all generated materials in `workspace/generated_materials/`
2. Check screenshots in `workspace/screenshots/`
3. Review application logs in `workspace/logs/applications.csv`
4. If satisfied, set `MANUAL_APPROVAL=false` in `.env` for automatic operation

---

*This log will be overwritten on the next run*
"""
        self._append_to_log(summary)
        print(f"\n✅ Quality control log saved to: {self.log_path}")

    def _append_to_log(self, content: str):
        """Append content to the log file"""
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(content)

    def get_stats(self) -> Dict[str, int]:
        """Return current statistics"""
        return self.stats.copy()


# Singleton instance
_qc_log_instance = None


def get_qc_log() -> QualityControlLog:
    """Get or create the singleton quality control log instance"""
    global _qc_log_instance
    if _qc_log_instance is None:
        _qc_log_instance = QualityControlLog()
    return _qc_log_instance
