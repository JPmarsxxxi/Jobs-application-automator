# Phase 2: Application Automation - Quick Start Guide

Phase 2 enables automatic job application submission via LinkedIn Easy Apply.

## ⚠️ Important: Start with Dry Run!

**ALWAYS test with dry run first** before doing real submissions.

## Quick Start

### 1. Test Phase 2 (Dry Run - Recommended)

```bash
python main.py --region uk --limit 1 --submit --dry-run
```

What this does:
- Scrapes 1 job from LinkedIn
- Generates CV and cover letter
- **Goes through entire Easy Apply flow**
- **Fills in all form fields**
- **Does NOT click final Submit button**
- Takes screenshots at each step
- Shows you what would be submitted

### 2. Review the Results

After dry run, check:
- **Screenshots:** `workspace/screenshots/` - see what was filled
- **Application Log:** `workspace/applications_log.csv` - see the result
- **Generated Materials:** `workspace/generated_materials/` - CV and cover letter

### 3. Real Submission (When Ready)

```bash
python main.py --region uk --limit 1 --submit
```

⚠️ **This will actually submit applications!** Remove `--dry-run` only when you've verified the dry run worked correctly.

## How It Works

```
1. Scrape LinkedIn Easy Apply jobs
2. Generate CV + Cover Letter (Phase 1)
3. Click "Easy Apply" button
4. For each page of the form:
   - Take screenshot
   - Analyze form with vision model
   - Fill fields from your user_info
   - Upload CV/cover letter if requested
   - Click Next
5. Click Submit (only if not dry run)
6. Verify submission
7. Log everything to CSV
```

## Configuration Needed

Make sure `config/user_info.py` has these fields:

```python
USER_INFO = {
    # Basic
    "name": "Your Full Name",
    "first_name": "First",
    "last_name": "Last",
    "email": "your.email@example.com",
    "phone": "+44 7XXX XXXXXX",

    # Location
    "location": "Cambridge, United Kingdom",
    "city": "Cambridge",
    "country": "United Kingdom",

    # Professional
    "linkedin": "https://linkedin.com/in/yourprofile",
    "github": "https://github.com/yourusername",
    "portfolio": "https://yourportfolio.com",

    # Education
    "university": "Your University",
    "degree": "Master of Science in Data Science",
    "graduation_year": "2026",

    # Work
    "years_of_experience": "2",
    "currently_employed": "No",

    # Authorization (UK/US specific)
    "work_authorization": "Authorized to work",  # or "Requires sponsorship"
    "visa_status": "Student Visa",
    "requires_sponsorship": "No",  # "Yes" or "No"
    "willing_to_relocate": True,

    # Preferences
    "salary_expectation": "Negotiable",
}
```

## Command Options

```bash
# Dry run (recommended for testing)
python main.py --region uk --limit 1 --submit --dry-run

# Real submission with manual approval for each job
python main.py --region uk --limit 3 --submit

# Real submission, automatic (no approval prompts)
python main.py --region uk --limit 5 --submit --no-manual-approval

# Phase 1 only (no submission)
python main.py --region uk --limit 5
```

## What Gets Tracked

Every application attempt is logged to `workspace/applications_log.csv`:

```csv
timestamp,company,title,location,job_url,status,confirmation,error,cv_path,cover_letter_path,screenshots
2026-01-19T12:34:56,Google,Data Scientist,London,https://...,submitted,Application submitted successfully,,/path/to/cv.docx,/path/to/cl.docx,screenshot1.png|screenshot2.png
```

Status codes:
- `dry_run_complete` - Dry run successful
- `submitted` - Actually submitted
- `failed` - Submission failed
- `skipped` - Skipped (no Easy Apply, or user declined)
- `captcha_required` - CAPTCHA detected (manual intervention needed)

## Screenshots

Every step is screenshotted:
- `01_initial_page.png` - Job posting page
- `02_easy_apply_modal.png` - Easy Apply modal opened
- `03_page_1.png` - First page of form
- `03_page_2.png` - Second page of form
- `04_confirmation.png` - Confirmation page (if submitted)

## Troubleshooting

### "No Easy Apply option"
Not all jobs have Easy Apply. The bot will skip these and log as "skipped".

### "CAPTCHA detected"
Bot pauses for 30 seconds. Solve the CAPTCHA manually in the browser window.

### "Could not find field"
Some fields might not be recognized. Check screenshots to see what was missed.

### "Upload failed"
Make sure CV and cover letter files exist and are valid .docx files.

### Vision model fails
Make sure `llava:13b` model is downloaded:
```bash
ollama pull llava:13b
```

## Safety Features

1. **Dry Run Mode** - Test without submitting
2. **Manual Approval** - Approve each application before submission
3. **Screenshot Capture** - Visual record of every step
4. **Detailed Logging** - CSV log of all attempts
5. **Browser Visibility** - Browser runs in non-headless mode so you can watch

## Next Steps

Once Phase 2 works well:
- **Phase 3:** Networking automation (find recruiters, send messages)
- **Phase 4:** Scheduling and email summaries

## Support

If something goes wrong:
1. Check `workspace/logs/` for error logs
2. Review screenshots in `workspace/screenshots/`
3. Check `workspace/applications_log.csv` for status
4. Open an issue on GitHub

---

**Remember: Always start with `--dry-run`!**
