# Installation Guide

## Prerequisites

Before starting, ensure you have:
- **Python 3.10+** installed
- **Git** installed
- A **Gmail account** (for sending emails)
- A **LinkedIn account** (for job searching)

## Step 1: Install Ollama (Local LLM)

Ollama provides local LLM inference for CV generation and form analysis.

### Linux/Mac:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows:
Download from: https://ollama.com/download

### Verify Installation:
```bash
ollama --version
```

## Step 2: Pull Required Models

```bash
# Vision model for form analysis (1.7GB download)
ollama pull llava:13b

# Text model for CV/cover letter generation (4.7GB download)
ollama pull llama3.1:8b

# Verify models are downloaded
ollama list
```

Expected output:
```
NAME                ID              SIZE      MODIFIED
llava:13b           xxx             1.7 GB    x minutes ago
llama3.1:8b         xxx             4.7 GB    x minutes ago
```

## Step 3: Setup Python Environment

```bash
# Clone the repository (if not already done)
cd Jobs-application-automator

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## Step 4: Configure User Information

```bash
# Copy example config
cp config/user_info.example.py config/user_info.py

# Edit with your details
nano config/user_info.py  # or use any text editor
```

Fill in your:
- Name, email, phone, location
- LinkedIn and GitHub profiles
- Education details
- Visa status
- Skills and experience

## Step 5: Setup Gmail API (Optional - for networking emails)

**Note:** Skip this step for now if you just want to test job scraping and CV generation.

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project: "Job Application Bot"
3. Enable the Gmail API
4. Create OAuth 2.0 credentials
5. Download `credentials.json`
6. Move to config folder:

```bash
mv ~/Downloads/credentials.json config/credentials.json
```

7. Run first-time authorization (will be implemented in Phase 3):
```bash
python scripts/setup_gmail.py
```

## Step 6: Setup Your Project Portfolio

Create your project portfolio files:

```bash
# Navigate to portfolio directory
cd workspace/portfolio

# Create your first project
nano projects/my_project.md
```

See README section "Portfolio Setup" for detailed instructions on project format.

## Step 7: Create Environment File

```bash
# Copy example environment file
cp .env.example .env

# Edit with your preferences
nano .env
```

Key settings:
- `DRY_RUN=true` - Start in dry-run mode
- `MANUAL_APPROVAL=true` - Require manual approval
- `HEADLESS_MODE=false` - See the browser during testing
- `LOG_LEVEL=INFO` - Logging verbosity

## Step 8: Test the Installation

```bash
# Test basic functionality
python main.py --test --region uk --limit 1

# This should:
# - Connect to Ollama
# - Validate your config
# - Create workspace directories
# - Show you're ready to start
```

## Step 9: Start Ollama Server (Important!)

Ollama must be running before starting the bot:

```bash
# In a separate terminal, start Ollama server
ollama serve

# Keep this terminal open while the bot runs
```

## Verification Checklist

Before running the bot, verify:

- [ ] Ollama is installed and running (`ollama serve`)
- [ ] Models are downloaded (`ollama list` shows llava:13b and llama3.1:8b)
- [ ] Python environment is activated (`which python` shows venv path)
- [ ] Dependencies are installed (`pip list` shows playwright, ollama, etc.)
- [ ] `config/user_info.py` exists and is filled out
- [ ] `.env` file exists
- [ ] Workspace directories exist (`ls workspace/`)

## Ready to Go!

You're now ready to run the bot:

```bash
# Test mode with 1 job (recommended first run)
python main.py --test --region uk --limit 1

# Test mode with 5 jobs
python main.py --test --region uk --limit 5

# See all options
python main.py --help
```

## Troubleshooting

### "Could not connect to Ollama"
- Make sure Ollama server is running: `ollama serve`
- Check Ollama is accessible: `curl http://localhost:11434/api/tags`

### "config/user_info.py not found"
- Copy the example file: `cp config/user_info.example.py config/user_info.py`
- Fill in your details

### "playwright not installed"
- Run: `playwright install chromium`
- Make sure you're in the virtual environment

### "Import errors"
- Activate virtual environment: `source venv/bin/activate`
- Reinstall requirements: `pip install -r requirements.txt`

## Next Steps

1. Review the [README](README.md) for detailed feature documentation
2. Set up your project portfolio in `workspace/portfolio/`
3. Run test jobs to verify everything works
4. Review the Quality Control Log after each test run
5. When satisfied, disable `MANUAL_APPROVAL` for automatic operation

## Need Help?

- Check the [README](README.md) for detailed documentation
- Review the Quality Control Log: `workspace/logs/QUALITY_CONTROL_LOG.md`
- Open an issue on GitHub
