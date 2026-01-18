# GitHub Setup Guide

## Quick Commands

```powershell
# 1. Complete the merge (if you see merge message)
git commit -m "Complete merge"

# 2. Stage all changes
git add .

# 3. Commit changes
git commit -m "Add LinkedIn login, human-like navigation, and persistent sessions"

# 4. Push to GitHub
git push origin main
```

## Step-by-Step Guide

### Step 1: Complete the Merge
If you see "All conflicts fixed but you are still merging":

```powershell
git commit -m "Complete merge and add new features"
```

### Step 2: Check What Will Be Committed
```powershell
# See what files will be added
git status

# See detailed changes
git diff
```

### Step 3: Stage Changes
```powershell
# Add all changes
git add .

# Or add specific files
git add .gitignore
git add modules/
git add ENV_SETUP.md
```

### Step 4: Commit
```powershell
# Create a commit with a descriptive message
git commit -m "Add LinkedIn login, human-like navigation, persistent browser sessions, and improved job card extraction"
```

### Step 5: Push to GitHub
```powershell
# Push to main branch
git push origin main

# If you need to set upstream (first time)
git push -u origin main
```

## Important: Check Before Committing

**DO NOT commit these files** (they're in .gitignore, but double-check):
- ❌ `.env` (contains your LinkedIn password)
- ❌ `config/user_info.py` (contains personal info)
- ❌ `config/credentials.json` (Gmail API credentials)
- ❌ `workspace/.browser_sessions/` (browser cookies)
- ❌ `workspace/generated_materials/` (generated CVs)
- ❌ `venv/` (virtual environment)

**Safe to commit:**
- ✅ All Python code in `modules/`
- ✅ `main.py`
- ✅ `requirements.txt`
- ✅ `README.md`, `INSTALLATION.md`, etc.
- ✅ `.gitignore`
- ✅ `ENV_SETUP.md`
- ✅ `config/user_info.example.py` (example file only)
- ✅ `workspace/portfolio/projects_index.json` (if you want to share project structure)

## If You Haven't Created a GitHub Repo Yet

### Option 1: Create via GitHub Website
1. Go to https://github.com/new
2. Create a new repository (name it `Jobs-application-automator`)
3. **DO NOT** initialize with README (you already have one)
4. Copy the repository URL

### Option 2: Add Remote (if needed)
```powershell
# If you need to add a remote
git remote add origin https://github.com/YOUR_USERNAME/Jobs-application-automator.git

# Or if using SSH
git remote add origin git@github.com:YOUR_USERNAME/Jobs-application-automator.git

# Check remote
git remote -v
```

## Recommended Commit Messages

```powershell
# For the current changes
git commit -m "feat: Add LinkedIn authentication, human-like navigation, and persistent sessions

- Implement LinkedIn login with credential support from .env
- Add human-like behavior (random delays, scrolling, typing)
- Fix job card extraction with multiple fallback selectors
- Add persistent browser sessions to avoid repeated logins
- Improve error handling and debugging capabilities"

# Or shorter version
git commit -m "Add LinkedIn login, navigation improvements, and persistent sessions"
```

## Troubleshooting

### If push is rejected:
```powershell
# Pull latest changes first
git pull origin main

# Resolve any conflicts, then:
git add .
git commit -m "Resolve conflicts"
git push origin main
```

### If you need to remove a file from staging:
```powershell
git restore --staged <filename>
```

### To see what's in .gitignore:
```powershell
cat .gitignore
```
