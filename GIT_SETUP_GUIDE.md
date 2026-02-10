# Git Setup Guide for SecureFlow Analytics

## Step 1: Create .gitignore File

Copy the `.gitignore` file to your project root:
```bash
# Navigate to your project
cd C:\Users\Manu\secureflow_analytics

# The .gitignore file should be in the root directory
# Copy it there if not already present
```

## Step 2: Initialize Git Repository (if not already done)

```bash
# Initialize git repo
git init

# Verify .gitignore exists
dir .gitignore  # Windows
# or
ls -la .gitignore  # Git Bash
```

## Step 3: Create .gitkeep Files (to track empty directories)

```bash
# Create .gitkeep in directories you want to track (but keep empty)
echo. > data\.gitkeep
echo. > models\.gitkeep
echo. > logs\.gitkeep
```

## Step 4: Check What Will Be Committed

```bash
# See what files git will track
git status

# You should see:
# - Source code files (.py)
# - Notebooks (.ipynb)
# - Documentation (.md)
# - .gitignore

# You should NOT see:
# - data/ folder contents
# - .parquet files
# - __pycache__
# - .ipynb_checkpoints
```

## Step 5: Add and Commit Files

```bash
# Add all files (respecting .gitignore)
git add .

# Verify what's staged
git status

# Commit
git commit -m "Initial commit: SecureFlow Analytics project structure"
```

## Step 6: Connect to GitHub (Optional)

```bash
# Create a new repo on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/secureflow-analytics.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Important: If You Already Committed Data Files

If you accidentally committed large data files before adding .gitignore:

```bash
# Remove data files from git tracking (but keep them locally)
git rm --cached -r data/
git rm --cached *.parquet
git rm --cached *.csv
git rm --cached *.duckdb

# Commit the removal
git commit -m "Remove data files from git tracking"

# Push changes
git push
```

## Verify .gitignore is Working

```bash
# Try to add a data file (should be ignored)
git add data/raw/events.parquet

# Should see message: "The following paths are ignored by one of your .gitignore files:"
```

## What Gets Committed vs Ignored

### ✅ COMMITTED (Tracked by Git):
```
secureflow_analytics/
├── .gitignore              ✓
├── README.md               ✓
├── requirements.txt        ✓
├── src/
│   ├── __init__.py        ✓
│   ├── config.py          ✓
│   ├── utils/             ✓
│   └── analytics/         ✓
├── notebooks/
│   ├── 01_eda.ipynb       ✓
│   ├── 02_funnel.ipynb    ✓
│   └── 03_cohort.ipynb    ✓
└── docs/                   ✓
```

### ❌ IGNORED (Not tracked):
```
secureflow_analytics/
├── data/                   ✗ (all data files)
│   ├── raw/*.parquet      ✗
│   └── *.csv              ✗
├── __pycache__/           ✗
├── .ipynb_checkpoints/    ✗
├── *.duckdb               ✗
├── .env                   ✗
├── venv/                  ✗
└── logs/                  ✗
```

## Quick Reference Commands

```bash
# Check git status
git status

# See ignored files
git status --ignored

# Add all changes (respecting .gitignore)
git add .

# Commit changes
git commit -m "Your commit message"

# Push to remote
git push

# Pull latest changes
git pull
```

## Troubleshooting

### Problem: "Large file" error when pushing

```bash
# Check file sizes
git ls-files -s | awk '{print $4, $2}' | sort -k2 -n -r | head -20

# Remove large file from git history (WARNING: rewrites history)
git filter-branch --tree-filter 'rm -f data/raw/events.parquet' HEAD
```

### Problem: .gitignore not working for already tracked files

```bash
# Remove from git but keep locally
git rm --cached filename

# Or remove entire directory
git rm --cached -r data/
```

### Problem: Want to check if .gitignore is correct

```bash
# Test if a file would be ignored
git check-ignore -v data/raw/events.parquet

# Should show which line in .gitignore is ignoring it
```

## Best Practices

1. **Never commit:**
   - Large data files (use cloud storage instead)
   - Credentials or API keys
   - Personal environment configurations
   - Compiled Python files (`__pycache__`)

2. **Always commit:**
   - Source code (`.py` files)
   - Documentation (`.md` files)
   - Requirements (`requirements.txt`)
   - Project structure (directories with `.gitkeep`)

3. **Document data sources:**
   - Add `data/README.md` explaining where to get data
   - Include instructions in main README

4. **Use Git LFS for necessary large files:**
   ```bash
   git lfs install
   git lfs track "*.psd"
   ```

## Example Workflow

```bash
# Daily workflow
cd C:\Users\Manu\secureflow_analytics

# See what changed
git status

# Add changes
git add src/analytics/new_analysis.py
git add notebooks/04_new_analysis.ipynb

# Commit
git commit -m "Add new customer segmentation analysis"

# Push
git push
```

---

## Need Help?

- Check ignored files: `git status --ignored`
- Check .gitignore syntax: `git check-ignore -v <filename>`
- View commit history: `git log --oneline`
