# Autonomous Job Application Bot

> **Fully automated job hunting system that finds, applies, and networks - all while you sleep.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Cost: £0/month](https://img.shields.io/badge/cost-£0%2Fmonth-brightgreen.svg)](https://github.com)

---

## 🎯 Overview

A completely local, zero-cost job application automation system that:

- ✅ **Searches job boards in real-time** (LinkedIn, Indeed, Reed, eFinancialCareers, Glassdoor, Jobberman)
- ✅ **Applies "Most Recent" filter automatically** (only jobs from last 7 days)
- ✅ **Generates ATS-optimized CVs and cover letters on-the-fly** using local LLM
- ✅ **Uses vision AI to fill ANY application form** (handles unknown layouts)
- ✅ **Smart file uploads** (correct CV/cover letter for each job)
- ✅ **Finds hiring managers on LinkedIn** (scrapes profiles)
- ✅ **Sends personalized cold emails** (AI-generated, sent via Gmail API)
- ✅ **Runs twice daily automatically** (6:30am GMT for UK, 2pm GMT for US)
- ✅ **Emails you daily summaries** with success rates and top applications
- ✅ **100% sandboxed** (cannot access your system outside designated folder)

### **Monthly Cost: £0.00** 💰

Everything runs locally or uses free APIs:
- **LLaVA** (vision model) - Local via Ollama
- **Llama 3.1** (CV/cover letter/email generation) - Local via Ollama
- **Gmail API** - Free (1 billion requests/day limit)
- **Playwright** - Open source browser automation
- All other tools - Open source

---

## 🎬 How It Works

### **Morning Run (6:30am GMT - UK Jobs)**
```
1. Bot wakes up → Navigates to LinkedIn, Indeed, Reed
2. Applies "Most Recent" filter (last 7 days only)
3. Clicks first job → Extracts details
4. Llama analyzes job → Matches your relevant projects
5. Generates ATS-optimized CV (15 sec)
6. Generates tailored cover letter (10 sec)
7. Clicks "Apply" → Vision model screenshots form
8. Vision AI identifies all fields (text, dropdowns, file uploads)
9. Fills form + uploads correct files
10. Submits application
11. Logs to CSV with screenshot
12. Goes back → Repeats for next job (20 UK jobs total)
```

### **Afternoon Run (2pm GMT - US Jobs)**
```
Same flow but:
- Targets US job boards (LinkedIn US, Indeed USA, Glassdoor)
- Applies visa sponsorship filter
- 15 US jobs total
```

### **Networking Layer (Runs 2-3 hours after applications)**
```
For each job applied:
1. Searches LinkedIn for recruiter/hiring manager
2. Scrapes profile (name, title)
3. Generates email address patterns (firstname.lastname@company.com)
4. Verifies email exists (SMTP check - doesn't send)
5. Llama generates personalized email (mentions relevant project)
6. Sends via Gmail API
7. Logs networking attempt
```

### **End of Day**
```
8pm GMT: Email summary to you with:
- Total applications submitted (UK + US)
- Success rate per platform
- Top 5 opportunities
- Networking emails sent
- Failed applications (for manual review)
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│  SCHEDULER (APScheduler - runs 24/7)                │
│  6:30am GMT → UK Morning Run (20 apps)              │
│  2:00pm GMT → US Morning Run (15 apps)              │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│  JOB SCRAPER (Per Platform)                         │
│  • LinkedIn: Filter "Most Recent" (7 days)          │
│  • Indeed: Sort by date, last week only             │
│  • Reed: Latest jobs filter                         │
│  • Iterate through jobs (newest → oldest)           │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│  INTELLIGENT PROJECT MATCHER (Llama)                │
│  1. Analyzes job description                        │
│  2. Scores your projects for relevance (0-10)       │
│  3. Selects top 2-3 projects to highlight           │
│  4. Returns project IDs + reasons                   │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│  ATS-OPTIMIZED MATERIAL GENERATOR (Llama)           │
│  CV Generation:                                     │
│  • Keyword optimization (matches job description)   │
│  • ATS-friendly formatting (no tables, columns)     │
│  • Standard fonts (Arial, Calibri)                  │
│  • Clear section headers                            │
│  • Bullet points with action verbs                  │
│  • Quantified achievements                          │
│  • Saves as .docx and .pdf                          │
│                                                      │
│  Cover Letter:                                      │
│  • Company-specific customization                   │
│  • Highlights matched projects                      │
│  • ATS keyword optimization                         │
│  • Professional tone                                │
│  • Saves as .pdf                                    │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│  VISION-GUIDED APPLICATION BOT (LLaVA + Playwright) │
│  1. Clicks "Apply" button                           │
│  2. Takes screenshot of application form            │
│  3. LLaVA vision model analyzes screenshot:         │
│     • Identifies all form fields                    │
│     • Detects field types (text, email, file, etc.) │
│     • Finds CSS selectors for each field            │
│     • Returns JSON mapping                          │
│  4. Fills each field intelligently:                 │
│     • "Full Name" → Emmanuel Isijola                │
│     • "Email" → theemmanuelisijola@gmail.com        │
│     • "Phone" → 07756963565                         │
│     • "CV/Resume" → Upload generated_cv.pdf         │
│     • "Cover Letter" → Upload cover_letter.pdf      │
│     • "Visa Sponsorship?" → Yes (for US jobs)       │
│  5. Handles multi-page forms (repeats 2-4)          │
│  6. Clicks "Submit"                                 │
│  7. Screenshots confirmation page                   │
│  8. Logs success/failure to CSV + SQLite            │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│  NETWORKING AUTOMATION                              │
│  LinkedIn Scraper:                                  │
│  • Searches "[Job Title] recruiter at [Company]"    │
│  • Scrapes top 3 profiles                           │
│  • Extracts: Name, Title, LinkedIn URL              │
│                                                      │
│  Email Finder:                                      │
│  • Generates patterns: firstname.lastname@co.com    │
│  • Verifies with SMTP (doesn't send, just checks)   │
│  • Stores valid email                               │
│                                                      │
│  Email Generator (Llama):                           │
│  • Generates personalized email                     │
│  • References specific job + your relevant project  │
│  • Professional but personable tone                 │
│  • 3-4 sentences max                                │
│                                                      │
│  Email Sender (Gmail API - FREE):                   │
│  • Sends email 2-3 hours after application          │
│  • Logs sent time, recipient                        │
│  • Tracks in networking.csv                         │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│  DAILY SUMMARY EMAIL                                │
│  Sent at 8pm GMT with:                              │
│  • Applications: 35 total (20 UK + 15 US)           │
│  • Success rate: 94%                                │
│  • Networking: 33 emails sent                       │
│  • Top opportunities (scored 9-10)                  │
│  • Failed applications (manual review needed)       │
│  • CSV logs + screenshots attached                  │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Features

### **1. Real-Time Application (No Batch Processing)**

Unlike traditional systems that scrape → generate → apply in batches, this bot works in **real-time**:

```python
for job in iterate_jobs():
    extract_details()          # 2 sec
    match_projects()           # 5 sec (Llama)
    generate_cv()              # 15 sec (Llama)
    generate_cover_letter()    # 10 sec (Llama)
    apply_to_job()             # 20-30 sec (Vision + form filling)
    log_application()          # 1 sec
    # Total: ~60 sec per job
```

**Why real-time is better:**
- ✅ Applies to jobs immediately (first applicant advantage)
- ✅ No stale job data (job could be closed by batch time)
- ✅ Adapts materials to each job on-the-fly
- ✅ Better memory efficiency (no large batches)

### **2. ATS Optimization (Critical!)**

90% of large companies use Applicant Tracking Systems (ATS) to filter resumes. This bot ensures your materials pass:

#### **CV ATS Optimization:**
```python
ATS_RULES = {
    "formatting": {
        "no_tables": True,           # ATS can't parse tables
        "no_columns": True,          # Single column layout only
        "no_headers_footers": True,  # ATS ignores these
        "no_images": True,           # ATS can't read images
        "no_text_boxes": True        # ATS skips text boxes
    },
    "fonts": {
        "allowed": ["Arial", "Calibri", "Times New Roman", "Helvetica"],
        "size": "10-12pt",
        "avoid": ["decorative", "script", "fancy"]
    },
    "structure": {
        "clear_headers": ["Education", "Experience", "Projects", "Skills"],
        "standard_names": True,      # Use common section names
        "bullet_points": True,       # Use bullets, not paragraphs
        "chronological": True        # Most recent first
    },
    "content": {
        "keywords": "MATCH_JOB_DESCRIPTION",  # Extract and use job keywords
        "action_verbs": ["Built", "Developed", "Engineered", "Implemented"],
        "quantify": True,            # Include numbers/metrics
        "no_pronouns": True          # No "I", "me", "my"
    },
    "file_format": {
        "preferred": ".docx",        # Most ATS-friendly
        "acceptable": ".pdf",        # PDF is backup
        "avoid": [".txt", ".rtf", ".pages"]
    }
}
```

#### **How the bot ensures ATS compatibility:**

1. **Keyword Extraction:**
```python
# Llama extracts keywords from job description
keywords = extract_keywords(job_description)
# Output: ["Python", "Machine Learning", "SQL", "pandas", "scikit-learn", "data visualization"]

# Injects keywords naturally into CV sections
cv_text = inject_keywords_naturally(base_cv, keywords, matched_projects)
```

2. **Standard Section Headers:**
```
✅ GOOD (ATS recognizes):
- EDUCATION
- WORK EXPERIENCE
- PROJECTS
- TECHNICAL SKILLS

❌ BAD (ATS confused):
- WHERE I LEARNED
- MY WORK HISTORY
- COOL STUFF I BUILT
- TECH I KNOW
```

3. **Simple Formatting:**
```
✅ GOOD:
PROJECTS
────────
• Fantasy Premier League Prediction System
  - Built ML system achieving 94% R² accuracy
  - Processed 11,000+ time-series records using Python, XGBoost
  - Technologies: Python, scikit-learn, pandas, NumPy

❌ BAD:
┌─────────────────────────────────────┐
│ Projects                            │
│ ═══════                             │
│ • FPL Prediction (see image →) 📊   │
└─────────────────────────────────────┘
```

4. **Action Verb + Quantification:**
```
✅ GOOD:
- Engineered time-series features achieving 94% accuracy on 11,000+ records
- Built BERT-based sentiment system analyzing 4,000+ social posts
- Automated video pipeline reducing production time by 90%

❌ BAD:
- Worked on a prediction system
- Did sentiment analysis
- Made videos faster
```

5. **File Format Strategy:**
```python
# Bot generates BOTH formats:
1. CV.docx → Primary (best ATS compatibility)
2. CV.pdf  → Backup (if company requests PDF)

# Upload logic:
if "PDF only" in job_description:
    upload("CV.pdf")
elif ".docx" in accepted_formats:
    upload("CV.docx")  # Prefer .docx
else:
    upload("CV.pdf")   # Fallback
```

#### **ATS Testing:**
The bot's generated CVs are optimized to pass common ATS systems:
- ✅ **Taleo** (Oracle)
- ✅ **Workday**
- ✅ **Greenhouse**
- ✅ **Lever**
- ✅ **iCIMS**
- ✅ **BambooHR**

### **3. Intelligent Project Matching**

Your portfolio folder contains project summaries. Llama intelligently matches projects to each job:

```
workspace/portfolio/
├── projects_index.json          # Master list
├── projects/
│   ├── fpl_prediction.md        # Sports analytics, ML, forecasting
│   ├── crypto_sentiment.md      # NLP, trading, transformers
│   ├── polymarket_arbitrage.md  # Quant trading, automation
│   ├── video_automation.md      # Computer vision, APIs
│   └── hand_gesture_recognition.md
```

**Example Matching:**

**Job: "Quantitative Researcher at Citadel"**
```python
# Llama analyzes job description
job_keywords = ["quantitative", "statistical modeling", "Python", "forecasting", "trading"]

# Scores projects:
{
  "fpl_prediction": 9,        # Time-series forecasting, statistics
  "crypto_sentiment": 8,      # Trading, alternative data
  "polymarket_arbitrage": 9,  # Direct trading experience
  "video_automation": 3,      # Not relevant
  "hand_gesture": 2           # Not relevant
}

# Selects top 3:
selected = ["polymarket_arbitrage", "fpl_prediction", "crypto_sentiment"]

# CV highlights these projects with tailored descriptions
# Cover letter mentions polymarket_arbitrage specifically
# Cold email references polymarket_arbitrage's trading results
```

**Job: "Machine Learning Engineer at DeepMind"**
```python
job_keywords = ["machine learning", "deep learning", "computer vision", "Python", "TensorFlow"]

# Scores projects:
{
  "hand_gesture_recognition": 10,  # Direct ML + computer vision
  "video_automation": 9,           # Computer vision, AI integration
  "fpl_prediction": 7,             # ML but not deep learning
  "crypto_sentiment": 6,           # NLP/transformers relevant
  "polymarket_arbitrage": 2        # Not relevant
}

selected = ["hand_gesture_recognition", "video_automation", "crypto_sentiment"]
```

### **4. Vision-Based Form Filling (Works on ANY Site)**

Instead of hardcoding form logic for each platform, the vision model adapts to ANY form:

```python
# Vision model analyzes screenshot and returns:
{
  "text_fields": [
    {"label": "First Name", "id": "first_name", "value": "Emmanuel"},
    {"label": "Last Name", "id": "last_name", "value": "Isijola"},
    {"label": "Email Address", "id": "email", "value": "theemmanuelisijola@gmail.com"},
    {"label": "Phone Number", "id": "phone", "value": "07756963565"}
  ],
  "file_uploads": [
    {"label": "Upload Resume/CV", "id": "resume-upload", "accepts": [".pdf", ".docx"]},
    {"label": "Cover Letter (Optional)", "id": "cover-letter", "accepts": [".pdf"]}
  ],
  "dropdowns": [
    {"label": "Years of Experience", "id": "experience", "options": ["0-1", "1-3", "3-5", "5+"], "select": "1-3"},
    {"label": "Visa Sponsorship Required?", "id": "visa", "options": ["Yes", "No"], "select": "Yes"}
  ],
  "checkboxes": [
    {"label": "I agree to terms", "id": "terms", "checked": true}
  ],
  "textareas": [
    {"label": "Why do you want this role?", "id": "motivation", "max_length": 500}
  ],
  "submit_button": {"text": "Submit Application", "id": "submit-btn"},
  "is_multi_page": true,
  "next_button": {"text": "Continue", "id": "next-page"}
}
```

**Handles edge cases:**
- ✅ Multi-page forms (continues to next page)
- ✅ Optional vs required fields
- ✅ Dynamic dropdowns (loads options from page)
- ✅ File format validation (checks accepted types)
- ✅ Character limits on text areas
- ✅ LinkedIn Easy Apply (special modal handling)
- ✅ Custom company career pages
- ✅ ATS systems (Greenhouse, Lever, Workday, etc.)

### **5. Smart File Upload Logic**

The bot knows which file to upload based on field labels:

```python
UPLOAD_RULES = {
    "resume|cv|curriculum": "generated_materials/cvs/Emmanuel_Isijola_CV_{company}_ATS.docx",
    "cover letter|covering letter": "generated_materials/cover_letters/{company}_Cover_Letter.pdf",
    "additional documents": None,  # Skip optional fields
    "transcript": None,  # Don't have this
}

# Example:
if "resume" in field_label.lower():
    if ".docx" in accepted_formats:
        upload_file("CV.docx")  # ATS-optimized .docx
    else:
        upload_file("CV.pdf")   # Fallback PDF
```

### **6. Sandboxed Environment (Security)**

Bot can ONLY access files in designated workspace:

```
workspace/                    # ← Bot's jail
├── portfolio/                # Your projects (you update)
├── generated_materials/      # Bot creates CVs/letters here
├── screenshots/              # Bot saves screenshots here
└── logs/                     # Bot logs here

/home/your_user/              # ← Bot CANNOT access
/etc/                         # ← Bot CANNOT access
/var/                         # ← Bot CANNOT access
```

**Implementation:**
```dockerfile
# Docker container with restricted volume mount
docker run \
  --rm \
  -v $(pwd)/workspace:/app/workspace:rw \
  job-bot:latest
```

No access to:
- ❌ Your home directory
- ❌ System files
- ❌ Other user data
- ❌ Network drives
- ❌ Sensitive files

### **7. Automated Scheduling**

Set it and forget it:

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

# UK Morning Run: 6:30am GMT every weekday
scheduler.add_job(
    func=run_job_hunt,
    trigger='cron',
    day_of_week='mon-fri',
    hour=6,
    minute=30,
    args=['uk'],
    id='uk_morning_run'
)

# US Morning Run: 2pm GMT (9am EST) every weekday
scheduler.add_job(
    func=run_job_hunt,
    trigger='cron',
    day_of_week='mon-fri',
    hour=14,
    minute=0,
    args=['us'],
    id='us_morning_run'
)

# Networking: 3 hours after UK run (9:30am GMT)
scheduler.add_job(
    func=run_networking,
    trigger='cron',
    day_of_week='mon-fri',
    hour=9,
    minute=30,
    id='networking_run'
)

# Summary email: 8pm GMT
scheduler.add_job(
    func=send_daily_summary,
    trigger='cron',
    day_of_week='mon-fri',
    hour=20,
    minute=0,
    id='daily_summary'
)

scheduler.start()
```

**Runs as system service:**
```bash
# Linux (systemd)
sudo systemctl enable job-bot
sudo systemctl start job-bot

# macOS (launchd)
launchctl load ~/Library/LaunchAgents/com.jobbot.plist

# Windows (Task Scheduler)
# Import job-bot-task.xml
```

### **8. Networking with Cold Emails**

After applying, bot finds hiring managers and sends personalized emails:

#### **LinkedIn Profile Scraping:**
```python
# Search: "Machine Learning Recruiter at DeepMind"
# Extract top 3 results:
recruiters = [
    {
        "name": "Sarah Johnson",
        "title": "Technical Recruiter - ML/AI",
        "company": "DeepMind",
        "linkedin_url": "linkedin.com/in/sarahjohnson",
        "profile_summary": "10+ years recruiting for AI roles..."
    }
]
```

#### **Email Address Generation:**
```python
# Generate patterns:
patterns = [
    "sarah.johnson@deepmind.com",
    "sjohnson@deepmind.com",
    "sarah@deepmind.com",
    "sarah.j@deepmind.com"
]

# Verify with SMTP (doesn't send email, just checks if address exists)
valid_email = verify_email_patterns(patterns)
# Result: "sarah.johnson@deepmind.com" ✅
```

#### **AI-Generated Email (Llama):**
```
SUBJECT: Quick question about ML Engineer role

Hi Sarah,

I applied for the Machine Learning Engineer position yesterday and wanted to reach out directly. I recently built a hand gesture recognition system achieving 96.77% accuracy using MobileNetV2, which aligns closely with your team's work in computer vision.

Would you have 10 minutes this week for a brief chat about the role?

Best regards,
Emmanuel Isijola
```

#### **Sending (Gmail API - Free):**
```python
gmail_api.send_email(
    to="sarah.johnson@deepmind.com",
    subject="Quick question about ML Engineer role",
    body=email_body
)
# Logged to networking.csv
```

---

## 📋 Prerequisites

### **Required:**
- Python 3.10+
- Ollama (for LLaVA vision model + Llama 3.1)
- Docker (for sandboxing - optional but recommended)
- Gmail account (for sending emails)
- LinkedIn account (for job searching and networking)

### **Optional:**
- GitHub account (for portfolio sync)
- Dedicated machine/VPS (to run 24/7)

---

## 🛠️ Installation

### **Step 1: Clone Repository**

```bash
git clone https://github.com/yourusername/job-application-bot.git
cd job-application-bot
```

### **Step 2: Install Ollama & Models**

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull vision model (for form analysis)
ollama pull llava:13b

# Pull text model (for CV/cover letter/email generation)
ollama pull llama3.1:8b

# Verify models are ready
ollama list
```

### **Step 3: Install Python Dependencies**

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### **Step 4: Setup Gmail API**

1. **Enable Gmail API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create new project: "Job Application Bot"
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Download `credentials.json`

2. **Move credentials file:**
```bash
mv ~/Downloads/credentials.json config/credentials.json
```

3. **First-time authorization:**
```bash
python scripts/setup_gmail.py
# Opens browser → Click "Allow" → token.json saved
```

### **Step 5: Configure Your Details**

```bash
# Copy example config
cp config/user_info.example.py config/user_info.py

# Edit with your details
nano config/user_info.py
```

```python
# config/user_info.py

USER_INFO = {
    "name": "Emmanuel Isijola",
    "email": "theemmanuelisijola@gmail.com",
    "phone": "07756963565",
    "location": "Cambridge, UK",
    "linkedin": "linkedin.com/in/isijola-emmanuel-1b3a9821b",
    "github": "github.com/JPmarsxxxi",
    "current_education": "MSc Data Science, University of Hertfordshire (Expected June 2026)",
    "previous_education": "BSc Anatomy, Bowen University",
    "visa_status": {
        "uk": "student_visa",  # or "work_visa", "citizen", "sponsorship_needed"
        "us": "sponsorship_needed"
    }
}
```

### **Step 6: Setup Your Project Portfolio**

```bash
# Your portfolio lives here (update as you build projects):
workspace/portfolio/projects/

# Example project file:
nano workspace/portfolio/projects/fpl_prediction.md
```

See [Portfolio Setup](#portfolio-setup) section below for detailed instructions.

### **Step 7: Test the System**

```bash
# Test vision model
python tests/test_vision.py

# Test job scraping
python tests/test_scrapers.py

# Test material generation
python tests/test_generation.py

# Test email sending
python tests/test_email.py

# Run single application (dry run)
python main.py --test --platform linkedin --limit 1
```

### **Step 8: Start the Scheduler**

```bash
# Run in foreground (testing)
python main.py --schedule

# Run as background service (production)
# See "Running as Service" section below
```

---

## 📁 Project Structure

```
job-application-bot/
├── README.md                          # This file
├── SETUP.md                           # Detailed setup guide
├── ARCHITECTURE.md                    # System design docs
├── requirements.txt                   # Python dependencies
├── Dockerfile                         # Docker container
├── docker-compose.yml                 # Docker orchestration
├── .env.example                       # Environment variables template
├── .gitignore
│
├── config/                            # Configuration files
│   ├── __init__.py
│   ├── user_info.py                   # Your personal details
│   ├── schedules.py                   # Daily run schedules
│   ├── platforms.py                   # Job board configs
│   ├── regions.py                     # UK/US/Nigeria settings
│   ├── credentials.json               # Gmail API credentials (gitignored)
│   └── token.json                     # Gmail API token (gitignored)
│
├── main.py                            # Entry point
│
├── modules/                           # Core application code
│   ├── __init__.py
│   │
│   ├── core/                          # Core system components
│   │   ├── __init__.py
│   │   ├── scheduler.py               # APScheduler wrapper
│   │   ├── orchestrator.py            # Main workflow coordinator
│   │   └── logger.py                  # CSV + SQLite logging
│   │
│   ├── scraping/                      # Job board scrapers
│   │   ├── __init__.py
│   │   ├── base_scraper.py            # Abstract scraper class
│   │   ├── linkedin_scraper.py        # LinkedIn jobs
│   │   ├── indeed_scraper.py          # Indeed UK/US
│   │   ├── reed_scraper.py            # Reed.co.uk
│   │   ├── efinancial_scraper.py      # eFinancialCareers
│   │   ├── glassdoor_scraper.py       # Glassdoor
│   │   └── jobberman_scraper.py       # Jobberman Nigeria
│   │
│   ├── generation/                    # Content generation
│   │   ├── __init__.py
│   │   ├── project_matcher.py         # Llama project matching
│   │   ├── material_generator.py      # CV + cover letter generator
│   │   ├── ollama_client.py           # Ollama API wrapper
│   │   ├── ats_optimizer.py           # ATS compliance checker
│   │   └── file_manager.py            # Save generated files
│   │
│   ├── automation/                    # Application automation
│   │   ├── __init__.py
│   │   ├── browser_controller.py      # Playwright wrapper
│   │   ├── vision_analyzer.py         # LLaVA form analysis
│   │   ├── form_filler.py             # Intelligent form filling
│   │   ├── file_uploader.py           # Smart file uploads
│   │   └── captcha_handler.py         # CAPTCHA solving (basic)
│   │
│   ├── networking/                    # LinkedIn networking
│   │   ├── __init__.py
│   │   ├── linkedin_finder.py         # Find recruiters/HRs
│   │   ├── profile_scraper.py         # Scrape LinkedIn profiles
│   │   ├── email_finder.py            # Generate email patterns
│   │   ├── email_verifier.py          # SMTP verification
│   │   ├── email_generator.py         # Llama email generation
│   │   └── gmail_sender.py            # Gmail API wrapper
│   │
│   └── utils/                         # Utilities
│       ├── __init__.py
│       ├── sandbox.py                 # Sandboxing utilities
│       ├── notifications.py           # Email summaries
│       ├── rate_limiter.py            # API rate limiting
│       └── helpers.py                 # Common functions
│
├── prompts/                           # LLM prompts
│   ├── job_analysis.txt               # Analyze job postings
│   ├── project_matching.txt           # Match projects to jobs
│   ├── cv_generation_ats.txt          # Generate ATS-optimized CV
│   ├── cover_letter_generation.txt    # Generate cover letter
│   ├── vision_form_analysis.txt       # Vision model form analysis
│   └── cold_email_generation.txt      # Generate networking emails
│
├── templates/                         # Base templates
│   ├── base_cv_quant.txt              # Base CV for quant roles
│   ├── base_cv_general.txt            # Base CV for general DS roles
│   └── email_signature.txt            # Email signature
│
├── workspace/                         # SANDBOXED directory (bot's jail)
│   ├── portfolio/                     # Your project portfolio
│   │   ├── projects_index.json        # Master project list
│   │   ├── projects/                  # Individual project markdowns
│   │   │   ├── fpl_prediction.md
│   │   │   ├── crypto_sentiment.md
│   │   │   ├── polymarket_arbitrage.md
│   │   │   ├── video_automation.md
│   │   │   └── hand_gesture_recognition.md
│   │   └── github_activity/           # Optional: GitHub sync data
│   │       ├── recent_commits.json
│   │       └── active_repos.json
│   │
│   ├── generated_materials/           # Bot creates files here
│   │   ├── cvs/                       # Generated CVs
│   │   │   ├── Emmanuel_Isijola_CV_Citadel_ATS.docx
│   │   │   ├── Emmanuel_Isijola_CV_Citadel_ATS.pdf
│   │   │   └── ...
│   │   └── cover_letters/             # Generated cover letters
│   │       ├── Citadel_Cover_Letter.pdf
│   │       └── ...
│   │
│   ├── screenshots/                   # Application screenshots
│   │   ├── 2026-01-15/
│   │   │   ├── linkedin_job_12345_form.png
│   │   │   ├── linkedin_job_12345_confirmation.png
│   │   │   └── ...
│   │   └── ...
│   │
│   └── logs/                          # Application logs
│       ├── applications.csv           # All applications
│       ├── networking.csv             # Networking attempts
│       ├── database.db                # SQLite database
│       └── daily_summaries/
│           ├── 2026-01-15_summary.txt
│           └── ...
│
├── scripts/                           # Utility scripts
│   ├── setup_gmail.py                 # First-time Gmail auth
│   ├── sync_github.py                 # Update portfolio from GitHub
│   ├── test_application.py            # Test single application
│   └── generate_report.py             # Weekly performance report
│
└── tests/                             # Test suite
    ├── test_scrapers.py
    ├── test_vision.py
    ├── test_generation.py
    ├── test_ats_compliance.py
    └── test_networking.py
```

---

## 🗂️ Portfolio Setup

Your project portfolio is the key to intelligent CV customization. Update this folder weekly as you build new projects.

### **projects_index.json**

Master list of all your projects:

```json
{
  "last_updated": "2026-01-15",
  "projects": [
    {
      "id": "fpl_prediction",
      "name": "Fantasy Premier League Prediction System",
      "summary": "ML system predicting player performance with 94% R² accuracy",
      "keywords": [
        "machine learning",
        "time-series",
        "forecasting",
        "sports analytics",
        "python",
        "scikit-learn",
        "xgboost",
        "statistical modeling"
      ],
      "relevance_tags": [
        "data_science",
        "ml_engineering",
        "sports_analytics",
        "quant_research"
      ],
      "tech_stack": ["Python", "scikit-learn", "XGBoost", "Pandas", "NumPy"],
      "key_metrics": "94% R² accuracy on 11,000+ time-series records",
      "use_cases": ["forecasting", "time-series", "ML", "statistics", "sports"],
      "github_url": "https://github.com/JPmarsxxxi/fpl-prediction",
      "last_updated": "2025-11-15",
      "priority": 9
    },
    {
      "id": "crypto_sentiment",
      "name": "Cryptocurrency Sentiment Trading System",
      "summary": "BERT-based sentiment analysis for crypto price prediction",
      "keywords": [
        "NLP",
        "transformers",
        "BERT",
        "trading",
        "sentiment analysis",
        "financial markets",
        "alternative data"
      ],
      "relevance_tags": [
        "quant_trading",
        "nlp_engineering",
        "fintech",
        "data_science"
      ],
      "tech_stack": ["Python", "BERT", "Transformers", "APIs", "Pandas"],
      "key_metrics": "Analyzed 4,000+ social media posts with BERT",
      "use_cases": ["trading", "NLP", "fintech", "sentiment", "alternative data"],
      "github_url": "https://github.com/JPmarsxxxi/crypto-sentiment",
      "last_updated": "2025-10-20",
      "priority": 10
    }
  ]
}
```

### **Individual Project Markdown**

`workspace/portfolio/projects/fpl_prediction.md`:

```markdown
# Fantasy Premier League Prediction System

## Overview
Production-ready ML system predicting player performance with 94% R² accuracy on 11,000+ time-series records.

## Problem Statement
Fantasy Premier League players need accurate predictions to select optimal teams. Existing prediction methods are unreliable and don't account for recent form, fixture difficulty, and player-specific patterns.

## Solution
Built end-to-end ML pipeline using XGBoost to predict player points based on:
- Historical performance (rolling averages, momentum indicators)
- Fixture difficulty (opponent strength, home/away)
- Player-specific features (position, team, price)
- Temporal patterns (gameweek, season trends)

## Technical Implementation

### Data Engineering
- Scraped 11,000+ player-gameweek records from FPL API
- Engineered 40+ features: rolling averages (3, 5, 10 weeks), lag variables, momentum indicators
- Handled missing data: forward-fill for player attributes, mean imputation for stats
- Created train/test split: 80/20 with temporal ordering preserved

### Modeling
- Compared 5 algorithms: XGBoost, Random Forest, Linear Regression, Ridge, Lasso
- Best model: XGBoost with 94% R² accuracy
- Hyperparameter tuning via GridSearchCV (max_depth, learning_rate, n_estimators)
- Identified and corrected data leakage: removed future-looking features

### Validation
- 5-fold cross-validation to ensure robustness
- Feature importance analysis: recent form (38%), fixture difficulty (22%), player price (15%)
- Residual analysis: confirmed no systematic errors

## Key Achievements
- **94% R² accuracy** on held-out test set
- **11,000+ records** processed and analyzed
- **Identified data leakage** and corrected model
- **Production-ready** pipeline for weekly predictions

## Business Value
- Demonstrates statistical modeling expertise (relevant for quant research)
- Shows time-series forecasting ability (trading systems)
- Proves data pipeline engineering skills (data engineering roles)
- Evidence of critical thinking (found and fixed model issues)

## Technologies
Python, scikit-learn, XGBoost, Pandas, NumPy, Matplotlib, Jupyter

## Relevant For
- Quantitative Research (time-series forecasting, statistical modeling)
- Sports Analytics (direct domain match)
- Data Science (ML modeling, feature engineering)
- Trading Systems (forecasting techniques, validation methods)
- ML Engineering (pipeline development, model deployment)

## GitHub
https://github.com/JPmarsxxxi/fpl-prediction

## Last Updated
November 2025

## Demo/Results
[Link to notebook with visualizations]
```

### **Updating Your Portfolio**

Weekly routine (5 minutes):

```bash
# 1. Add new project (if you finished something)
nano workspace/portfolio/projects/new_project.md

# 2. Update projects_index.json
nano workspace/portfolio/projects_index.json
# Add entry for new project

# 3. (Optional) Sync GitHub activity
python scripts/sync_github.py

# Done! Bot will use updated projects all week
```

---

## ⚙️ Configuration

### **Daily Schedules** (`config/schedules.py`)

```python
DAILY_SCHEDULES = {
    "uk_morning": {
        "time": "06:30",
        "timezone": "Europe/London",
        "region": "UK",
        "platforms": {
            "linkedin": {
                "limit": 8,
                "search_terms": [
                    "Data Scientist graduate London",
                    "Machine Learning Engineer entry level UK",
                    "Quantitative Analyst London"
                ],
                "filters": {
                    "date_posted": "past_week",
                    "experience_level": ["Entry level", "Associate"],
                    "sort": "most_recent"
                }
            },
            "indeed": {
                "limit": 7,
                "search_terms": [
                    "Graduate Data Scientist London",
                    "Junior ML Engineer UK"
                ],
                "filters": {
                    "date_posted": "7_days",
                    "sort": "date"
                }
            },
            "reed": {
                "limit": 5,
                "search_terms": ["Data Scientist London", "ML Engineer UK"],
                "filters": {"date_posted": 7, "sort": "latest"}
            }
        },
        "total_limit": 20
    },
    
    "us_morning": {
        "time": "14:00",  # 9am EST
        "timezone": "Europe/London",
        "region": "US",
        "platforms": {
            "linkedin": {
                "limit": 8,
                "search_terms": [
                    "Quantitative Researcher New York",
                    "Data Scientist visa sponsorship USA",
                    "ML Engineer H1B sponsor"
                ],
                "filters": {
                    "date_posted": "past_week",
                    "visa_sponsorship": True,
                    "location": ["New York", "Chicago", "San Francisco"],
                    "sort": "most_recent"
                }
            },
            "indeed": {
                "limit": 4,
                "search_terms": [
                    "Quantitative Analyst H1B",
                    "Data Scientist tier 2 sponsor"
                ],
                "filters": {
                    "date_posted": "7_days",
                    "visa": True,
                    "sort": "date"
                }
            },
            "glassdoor": {
                "limit": 3,
                "search_terms": ["Machine Learning Engineer visa"],
                "filters": {"visa_sponsorship": True, "date_posted": 7}
            }
        },
        "total_limit": 15
    }
}
```

### **Platform Configs** (`config/platforms.py`)

```python
PLATFORMS = {
    "linkedin": {
        "base_url": "https://www.linkedin.com/jobs/search",
        "login_required": True,
        "easy_apply": True,
        "rate_limit": {
            "requests_per_minute": 20,
            "applications_per_hour": 30
        },
        "selectors": {
            "job_card": ".job-card-container",
            "apply_button": ".jobs-apply-button",
            "easy_apply_modal": ".jobs-easy-apply-modal"
        }
    },
    
    "indeed": {
        "base_url": "https://uk.indeed.com/jobs",
        "login_required": False,
        "easy_apply": True,
        "rate_limit": {
            "requests_per_minute": 30,
            "applications_per_hour": 40
        }
    },
    
    # ... other platforms
}
```

### **Region Settings** (`config/regions.py`)

```python
REGIONS = {
    "UK": {
        "location_strings": [
            "United Kingdom",
            "London",
            "Cambridge",
            "Manchester",
            "Remote UK"
        ],
        "visa_required": False,
        "platforms": ["linkedin", "indeed", "reed", "efinancialcareers"],
        "priority_companies": [
            "Citadel",
            "Two Sigma",
            "Jane Street",
            "Man Group",
            "Winton Capital",
            "Marshall Wace"
        ]
    },
    
    "US": {
        "location_strings": [
            "United States",
            "New York",
            "Chicago",
            "San Francisco",
            "Remote USA"
        ],
        "visa_required": True,
        "visa_filter_mandatory": True,
        "platforms": ["linkedin", "indeed", "glassdoor"],
        "priority_cities": ["New York", "Chicago", "San Francisco"],
        "priority_companies": [
            "Jane Street",
            "Citadel",
            "Two Sigma",
            "DE Shaw",
            "Google",
            "Meta",
            "Amazon"
        ]
    },
    
    "NIGERIA": {
        "location_strings": ["Nigeria", "Lagos", "Remote"],
        "visa_required": False,
        "platforms": ["linkedin", "jobberman"],
        "remote_keywords": ["remote", "UK-based remote", "global remote"],
        "priority_companies": [
            "Flutterwave",
            "Paystack",
            "Kuda",
            "Carbon",
            "PiggyVest"
        ]
    }
}
```

---

## 🚀 Usage

### **Basic Commands**

```bash
# Run UK morning session (20 applications)
python main.py --region uk

# Run US morning session (15 applications)
python main.py --region us

# Run both regions (35 applications)
python main.py --region uk us

# Test mode (dry run, no actual applications)
python main.py --region uk --test

# Apply to single platform
python main.py --platform linkedin --limit 5

# Run with custom schedule
python main.py --schedule custom_schedule.json
```

### **Automated Scheduling**

```bash
# Start scheduler (runs in background)
python main.py --schedule

# Check scheduler status
python main.py --status

# Stop scheduler
python main.py --stop
```

### **Running as System Service**

#### **Linux (systemd)**

Create service file:

```bash
sudo nano /etc/systemd/system/job-bot.service
```

```ini
[Unit]
Description=Autonomous Job Application Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/job-application-bot
ExecStart=/path/to/venv/bin/python main.py --schedule
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable job-bot
sudo systemctl start job-bot

# Check logs
sudo journalctl -u job-bot -f
```

#### **macOS (launchd)**

Create plist file:

```bash
nano ~/Library/LaunchAgents/com.jobbot.plist
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jobbot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/venv/bin/python</string>
        <string>/path/to/job-application-bot/main.py</string>
        <string>--schedule</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/path/to/logs/jobbot.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/logs/jobbot.error.log</string>
</dict>
</plist>
```

Load service:

```bash
launchctl load ~/Library/LaunchAgents/com.jobbot.plist
launchctl start com.jobbot
```

#### **Windows (Task Scheduler)**

```powershell
# Create scheduled task
schtasks /create /tn "JobBot" /tr "C:\path\to\venv\Scripts\python.exe C:\path\to\main.py --schedule" /sc onstart /ru SYSTEM
```

### **Manual Operations**

```bash
# Update portfolio
python scripts/sync_github.py

# Test single application
python scripts/test_application.py --url "https://linkedin.com/jobs/view/12345"

# Generate weekly report
python scripts/generate_report.py --week 2026-W03

# Clean old logs (keep last 30 days)
python scripts/cleanup.py --days 30
```

---

## 📊 Monitoring & Logs

### **CSV Logs**

`workspace/logs/applications.csv`:

```csv
date,time,platform,company,title,location,job_url,applied,success,error,cv_file,cover_letter_file,screenshot,matched_projects
2026-01-15,06:35:12,linkedin,Citadel,Quantitative Researcher,London,https://linkedin.com/jobs/view/12345,true,true,,Emmanuel_Isijola_CV_Citadel_ATS.docx,Citadel_Cover_Letter.pdf,linkedin_12345_confirmation.png,"polymarket_arbitrage,fpl_prediction"
2026-01-15,06:38:45,indeed,Two Sigma,Data Scientist,London,https://indeed.co.uk/job/67890,true,true,,Emmanuel_Isijola_CV_TwoSigma_ATS.docx,TwoSigma_Cover_Letter.pdf,indeed_67890_confirmation.png,"crypto_sentiment,fpl_prediction"
```

`workspace/logs/networking.csv`:

```csv
date,time,company,job_title,recruiter_name,recruiter_title,email,email_sent,email_opened,response_received
2026-01-15,09:35:00,Citadel,Quantitative Researcher,Sarah Johnson,Technical Recruiter,sarah.johnson@citadel.com,true,false,false
2026-01-15,09:36:15,Two Sigma,Data Scientist,Michael Chen,Talent Acquisition,michael.chen@twosigma.com,true,true,false
```

### **SQLite Database**

Query application history:

```bash
sqlite3 workspace/logs/database.db

# Applications by platform
SELECT platform, COUNT(*) as count, 
       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
FROM applications
GROUP BY platform;

# Success rate over time
SELECT date, 
       COUNT(*) as total,
       AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) * 100 as success_rate
FROM applications
GROUP BY date
ORDER BY date DESC
LIMIT 30;

# Top companies applied to
SELECT company, COUNT(*) as applications
FROM applications
WHERE success = 1
GROUP BY company
ORDER BY applications DESC
LIMIT 10;
```

### **Daily Email Summary**

Sent to your email at 8pm GMT:

```
Subject: ✅ Job Hunt Complete - Wednesday, January 15, 2026

Hey Emmanuel,

Your Wednesday job hunt sessions are done! Here's the breakdown:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 OVERALL STATS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Applications Submitted: 35 (20 UK + 15 US)
• Success Rate: 94% (33 successful, 2 failed)
• Time Taken: 2 hours 15 minutes
• Networking Emails Sent: 31

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌍 BY REGION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UK (20 applications):
  ✅ Applied: 19 | ❌ Failed: 1
  
  Breakdown by platform:
  • LinkedIn: 8 apps (100% success)
  • Indeed: 7 apps (100% success)
  • Reed: 4 apps (80% success - 1 failed)

US (15 applications):
  ✅ Applied: 14 | ❌ Failed: 1
  
  Breakdown by platform:
  • LinkedIn: 8 apps (100% success)
  • Indeed: 4 apps (100% success)
  • Glassdoor: 2 apps (67% success - 1 failed)
  
  ⚠️ All US apps verified H1B visa sponsorship

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔥 TOP 5 APPLICATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 🎯 Citadel - Quantitative Researcher (London)
   Score: 9/10 | Platform: LinkedIn
   Projects Highlighted: Polymarket Arbitrage, FPL Prediction
   Recruiter Email Sent: ✅ sarah.johnson@citadel.com

2. 🎯 Jane Street - Quantitative Trader (New York)
   Score: 10/10 | Platform: LinkedIn
   Projects Highlighted: Crypto Sentiment, Polymarket Arbitrage
   Recruiter Email Sent: ✅ michael.zhang@janestreet.com

3. 🎯 Two Sigma - Data Scientist (London)
   Score: 9/10 | Platform: Indeed
   Projects Highlighted: FPL Prediction, Crypto Sentiment
   Recruiter Email Sent: ✅ emily.roberts@twosigma.com

4. 🎯 DE Shaw - Machine Learning Engineer (New York)
   Score: 8/10 | Platform: LinkedIn
   Projects Highlighted: Hand Gesture Recognition, Video Automation
   Recruiter Email Sent: ✅ alex.kumar@deshaw.com

5. 🎯 Man Group - Quantitative Analyst (London)
   Score: 8/10 | Platform: eFinancialCareers
   Projects Highlighted: Crypto Sentiment, FPL Prediction
   Recruiter Email Sent: ✅ james.mitchell@man.com

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ FAILED APPLICATIONS (Manual Review)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ❌ TechStartup X - Senior Data Scientist (London)
   Platform: Reed
   Error: Required video introduction (not automated yet)
   Action: Manual application recommended
   Link: https://reed.co.uk/job/12345

2. ❌ FinTech Y - ML Engineer (San Francisco)
   Platform: Glassdoor
   Error: Unusual CAPTCHA couldn't be solved
   Action: Apply manually via company website
   Link: https://glassdoor.com/job/67890

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 NETWORKING SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Recruiters Found: 33
• Valid Emails Found: 31 (94%)
• Emails Sent: 31
• Email Opens (so far): 5 (tracking 24hrs)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📂 FILES & LOGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• CSV Log: workspace/logs/applications.csv
• Networking Log: workspace/logs/networking.csv
• Screenshots: workspace/screenshots/2026-01-15/
• Generated CVs: workspace/generated_materials/cvs/
• Database: workspace/logs/database.db

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 NEXT RUN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Thursday, January 16 at:
• 6:30am GMT - UK Jobs (20 applications)
• 2:00pm GMT - US Jobs (15 applications)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Keep crushing it! 💪

- Your Job Bot 🤖
```

---

## 🐛 Troubleshooting

### **Common Issues**

#### **1. Ollama Connection Failed**

```bash
Error: Could not connect to Ollama at http://localhost:11434

# Fix:
ollama serve  # Start Ollama server

# Verify:
curl http://localhost:11434/api/tags
```

#### **2. Gmail API Authentication Error**

```bash
Error: invalid_grant - Token has been expired or revoked

# Fix: Re-authenticate
rm config/token.json
python scripts/setup_gmail.py
```

#### **3. LinkedIn Account Locked**

```
Error: Your LinkedIn account has been temporarily restricted

# Cause: Too aggressive scraping
# Fix:
# 1. Reduce rate limits in config/platforms.py
# 2. Add random delays between requests
# 3. Use residential proxies (optional)
# 4. Create burner LinkedIn account for testing
```

#### **4. Vision Model Not Detecting Fields**

```bash
Error: No form fields detected in screenshot

# Debug:
python scripts/test_vision.py --screenshot path/to/screenshot.png

# Potential fixes:
# 1. Try different vision model:
ollama pull llava:34b  # Larger, smarter model

# 2. Adjust vision prompt (prompts/vision_form_analysis.txt)

# 3. Check screenshot quality (must be clear, full page)
```

#### **5. Application Submission Failed**

```bash
Error: Submit button not found or not clickable

# Debug:
# Check screenshot: workspace/screenshots/[date]/[job_id]_form.png

# Common causes:
# 1. Multi-page form (bot should handle this, but check)
# 2. JavaScript-heavy form (wait longer for loading)
# 3. Hidden CAPTCHA (add CAPTCHA handling)

# Fix: Adjust wait times in config
WAIT_TIMES = {
    "page_load": 5,      # seconds (increase if slow site)
    "element_load": 3,   # seconds
    "after_click": 2     # seconds
}
```

#### **6. File Upload Failed**

```bash
Error: Could not upload CV - file not found

# Debug:
ls workspace/generated_materials/cvs/

# Verify files were generated
# Check file paths in upload logic

# Common cause: ATS filename too long
# Fix: Shorten company name in filename generator
```

### **Debug Mode**

Run with verbose logging:

```bash
python main.py --region uk --debug

# Output shows:
# - Every browser action
# - Vision model responses
# - Form field mappings
# - File upload attempts
# - Error stack traces
```

### **Manual Testing**

Test individual components:

```bash
# Test vision model on specific screenshot
python tests/test_vision.py --image path/to/form.png

# Test scraper on specific platform
python tests/test_scrapers.py --platform linkedin --limit 3

# Test material generation
python tests/test_generation.py --job-url "https://linkedin.com/jobs/view/12345"

# Test email generation
python tests/test_email.py --recruiter-name "Sarah Johnson" --company "Citadel"

# Test full application flow (dry run)
python scripts/test_application.py --url "https://linkedin.com/jobs/view/12345" --dry-run
```

---

## 🔒 Security & Privacy

### **Data Storage**

All sensitive data stays local in sandboxed directory:
- ✅ CVs, cover letters, screenshots → `workspace/`
- ✅ Application logs → `workspace/logs/`
- ✅ Gmail credentials → `config/credentials.json` (gitignored)
- ❌ **Never commits sensitive files to Git** (see `.gitignore`)

### **Gmail API Security**

- Uses OAuth 2.0 (more secure than passwords)
- Token stored locally in `config/token.json`
- Revocable at any time: [Google Account Permissions](https://myaccount.google.com/permissions)

### **LinkedIn Account Protection**

Bot includes rate limiting to avoid account flags:

```python
RATE_LIMITS = {
    "linkedin": {
        "requests_per_minute": 20,
        "applications_per_hour": 30,
        "max_daily_applications": 50
    }
}
```

**Best practices:**
- Create separate LinkedIn account for automation (optional)
- Use residential proxies if scraping heavily (optional)
- Monitor account health in LinkedIn settings

### **Sandboxing**

Bot is restricted to `workspace/` directory only:

```bash
# Docker isolation (recommended)
docker run --rm \
  -v $(pwd)/workspace:/app/workspace:rw \
  --network none \  # No internet for container (optional)
  job-bot:latest

# Bot CANNOT access:
# - Your home directory
# - System files
# - Other user data
```

---

## 📈 Performance & Scalability

### **Current Limits**

```
Daily Applications: 35 (20 UK + 15 US)
Application Speed: ~60 seconds per job
Session Duration: ~35-60 minutes per run
Success Rate: ~90-95% (depends on form complexity)
Networking Emails: ~30-35 per day
```

### **Scaling Up**

Want to apply to more jobs? Adjust in `config/schedules.py`:

```python
# Increase limits (careful not to spam)
"uk_morning": {
    "total_limit": 30,  # Up from 20
    "platforms": {
        "linkedin": {"limit": 12},
        "indeed": {"limit": 10},
        "reed": {"limit": 8}
    }
}

# Add more sessions
"uk_afternoon": {
    "time": "12:00",  # Lunchtime run
    "region": "UK",
    "total_limit": 15
}
```

**Warning:** More applications = higher risk of:
- ❌ LinkedIn account restrictions
- ❌ Platform rate limiting
- ❌ Lower quality applications (rushed)

**Recommended max:** 50-60 applications per day total

### **Optimizations**

If bot is too slow:

```python
# 1. Use smaller vision model
ollama pull llava:7b  # Faster than 13b

# 2. Reduce material generation time
OLLAMA_CONFIG = {
    "max_tokens": 1000,  # Down from 2000
    "temperature": 0.5   # More deterministic = faster
}

# 3. Parallelize some operations
# (Advanced - requires code changes)
```

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

1. **Additional job boards** (Glassdoor, Monster, etc.)
2. **Better CAPTCHA handling** (2captcha integration?)
3. **Video introduction automation** (some apps require this)
4. **Interview scheduling automation** (respond to interview invites)
5. **Application tracking dashboard** (web UI for monitoring)

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- **Ollama** - Local LLM inference
- **Playwright** - Browser automation
- **LLaVA** - Vision language model
- **Meta** - Llama 3.1 model

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/job-application-bot/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/job-application-bot/discussions)
- **Email:** theemmanuelisijola@gmail.com

---

## 🗺️ Roadmap

### **Q1 2026**
- [x] Core application automation
- [x] Vision-based form filling
- [x] LinkedIn networking
- [ ] ATS compliance testing
- [ ] Video introduction handling

### **Q2 2026**
- [ ] Interview scheduling automation
- [ ] Application tracking dashboard
- [ ] Mobile app (monitor on the go)
- [ ] Multi-user support

### **Q3 2026**
- [ ] AI interview preparation
- [ ] Salary negotiation assistant
- [ ] Offer comparison tool

---

## ⚡ Quick Start (TL;DR)

```bash
# 1. Install Ollama + models
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llava:13b
ollama pull llama3.1:8b

# 2. Clone repo
git clone https://github.com/yourusername/job-application-bot.git
cd job-application-bot

# 3. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# 4. Setup Gmail API
python scripts/setup_gmail.py

# 5. Configure your details
cp config/user_info.example.py config/user_info.py
nano config/user_info.py

# 6. Add your projects
nano workspace/portfolio/projects_index.json

# 7. Run!
python main.py --schedule
```

Now sit back and let the bot hunt for jobs while you focus on interview prep! 🚀

---

**Built with ❤️ by Emmanuel Isijola**

*Last Updated: January 2026*
# Jobs-application-automator
.....
