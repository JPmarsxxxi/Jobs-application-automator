# Environment Variables Setup

## Create .env File

Create a `.env` file in the root directory of the project with the following content:

```env
# LinkedIn Credentials (Required for job scraping)
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your_password_here

# Browser Settings
HEADLESS_MODE=false

# Run Modes
DRY_RUN=false
MANUAL_APPROVAL=true

# Logging
LOG_LEVEL=INFO

# Ollama Configuration (if not using default)
OLLAMA_BASE_URL=http://localhost:11434
```

## Quick Setup

On Windows (PowerShell):
```powershell
# Create .env file
@"
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your_password_here
HEADLESS_MODE=false
DRY_RUN=false
MANUAL_APPROVAL=true
LOG_LEVEL=INFO
"@ | Out-File -FilePath .env -Encoding utf8
```

On Linux/Mac:
```bash
# Create .env file
cat > .env << 'EOF'
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your_password_here
HEADLESS_MODE=false
DRY_RUN=false
MANUAL_APPROVAL=true
LOG_LEVEL=INFO
EOF
```

## Important Notes

- **Never commit `.env` to git** - it's already in `.gitignore`
- Replace `your.email@example.com` with your actual LinkedIn email
- Replace `your_password_here` with your actual LinkedIn password
- The `.env` file is loaded automatically by `python-dotenv` in `main.py`

## Security

- Store your credentials securely
- Consider using a dedicated LinkedIn account for automation (optional)
- Keep your `.env` file private and never share it
