# Tab Closing Issue - Analysis & Fix

## Problem
After clicking "Easy Apply", tabs close or navigation breaks.

## Root Cause
Browser controller is navigating to job URL when we're already on the job page from scraping.

Current flow:
```
1. Scrape jobs → Navigate through LinkedIn, click panels → Extract data
2. Keep browser open
3. Phase 2: navigate AGAIN to job.job_url
4. Click Easy Apply
```

The double navigation is causing issues.

## Solution Options

### Option A: Don't Re-Navigate (Recommended)
If browser is kept open from scraping, we're already on the last job page.

```python
def apply_to_job(...):
    # Check if we're already on the job page
    if self.page.url != job_url:
        self.page.goto(job_url)
    else:
        self.logger.debug("Already on job page, skipping navigation")
```

### Option B: Always Navigate Fresh
Close all tabs except first, then navigate fresh.

```python
# Close extra tabs
for context in self.page.context.pages[1:]:
    context.close()

# Navigate to job
self.page.goto(job_url)
```

### Option C: Separate Scrape and Apply Sessions
- Phase 1: Scrape → Close browser
- Phase 2: Open fresh browser → Navigate → Apply

Less efficient but cleanest separation.

## Recommended Fix

Update `browser_controller.py`:

```python
def apply_to_job(self, job_url, cv_path, cover_letter_path=None, dry_run=True):
    try:
        # Navigate to job page only if not already there
        current_url = self.page.url
        if job_url not in current_url:
            self.logger.info(f"Navigating to job: {job_url}")
            self.page.goto(job_url, wait_until="domcontentloaded")
            human_delay(2.0, 4.0)
        else:
            self.logger.info("Already on job page from scraping")
            human_delay(1.0, 2.0)

        # Rest of the flow...
```

This prevents double navigation and keeps the tab intact.

## Testing

After fix:
1. Browser should stay on same tab throughout
2. No unexpected tab closes
3. Easy Apply modal opens correctly
4. Form fills without navigation issues
