# How to Install Packages Without Plotly

Plotly is only needed for the Streamlit dashboards. If you're not using the dashboard, you can skip it. Here are several ways to do this.

## Method 1: Install Packages Individually (Recommended) ⭐

Install only the packages you need, excluding plotly:

### For Snowflake Connection Only:
```powershell
# Activate virtual environment first
.\venv\Scripts\Activate.ps1

# Install core packages
pip install pandas numpy python-dateutil
pip install snowflake-connector-python python-dotenv
```

### For Data Generation Only:
```powershell
pip install pandas numpy python-dateutil
```

### For Snowflake + Data Generation:
```powershell
pip install pandas numpy python-dateutil
pip install snowflake-connector-python python-dotenv
```

### For Notebooks (without dashboard):
```powershell
pip install pandas numpy python-dateutil
pip install matplotlib seaborn
pip install jupyter ipykernel
```

---

## Method 2: Install from requirements.txt, Then Uninstall Plotly

If you want to install everything first, then remove plotly:

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install all packages
pip install -r requirements.txt

# Uninstall plotly
pip uninstall plotly -y
```

---

## Method 3: Modify requirements.txt Temporarily

### Option A: Comment Out Plotly

Edit `requirements.txt` and comment out the plotly line:

```txt
# Streamlit dashboard (optional, for interactive analytics)
streamlit>=1.28.0
# plotly>=5.17.0  # Commented out - not needed
```

Then install:
```powershell
pip install -r requirements.txt
```

**Remember to uncomment it later if you decide to use the dashboard.**

### Option B: Create a Custom Requirements File

Create a new file `requirements-core.txt`:

```txt
# Core dependencies
pandas>=1.5.0
numpy>=1.20.0

# Date utilities
python-dateutil>=2.8.0

# Visualization (optional, for notebooks)
matplotlib>=3.5.0
seaborn>=0.12.0

# Jupyter notebook (optional, for running notebooks)
jupyter>=1.0.0
ipykernel>=6.0.0

# Snowflake integration (optional, for database loading)
snowflake-connector-python>=3.0.0
python-dotenv>=1.0.0

# Streamlit dashboard (optional, for interactive analytics)
streamlit>=1.28.0
# plotly>=5.17.0  # Excluded - add if needed for dashboard
```

Then install:
```powershell
pip install -r requirements-core.txt
```

---

## Method 4: Use pip install with --ignore-installed

This is more complex, but you can install everything except plotly:

```powershell
# Install all packages
pip install -r requirements.txt

# Remove plotly
pip uninstall plotly -y
```

---

## Method 5: Install Everything Except Specific Packages

Use grep (on Mac/Linux) or findstr (on Windows) to exclude plotly:

**On Windows PowerShell:**
```powershell
# Get all lines from requirements.txt except plotly
Get-Content requirements.txt | Where-Object { $_ -notmatch "plotly" } | pip install -r /dev/stdin
```

Actually, a simpler approach on Windows:

```powershell
# Create temporary file without plotly
Get-Content requirements.txt | Where-Object { $_ -notmatch "plotly" } | Out-File -FilePath requirements-no-plotly.txt -Encoding utf8

# Install from modified file
pip install -r requirements-no-plotly.txt

# Clean up
Remove-Item requirements-no-plotly.txt
```

---

## Recommended: Minimal Installation

If you only need Snowflake connection and data generation:

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install essential packages only
pip install pandas>=1.5.0
pip install numpy>=1.20.0
pip install python-dateutil>=2.8.0
pip install snowflake-connector-python>=3.0.0
pip install python-dotenv>=1.0.0
```

This gives you:
- ✅ Data generation (`function.py`)
- ✅ Snowflake connection (`snowflake_loader.py`)
- ❌ No dashboard (no plotly, no streamlit)
- ❌ No notebooks visualization (no matplotlib, seaborn)

---

## What Plotly Is Used For

Plotly is only used in:
- `streamlit_app.py` - Local Streamlit dashboard
- `streamlit_app_snowflake.py` - Snowflake Streamlit dashboard

If you're not using these dashboards, you don't need plotly.

---

## Verify Installation

After installing without plotly, verify:

```powershell
# Check installed packages
pip list

# Verify plotly is NOT installed
pip show plotly
# Should show: "WARNING: Package(s) not found: plotly"

# Test that core functionality works
python snowflake_loader.py --test
```

---

## If You Need Plotly Later

If you decide you want the dashboard later, just install plotly:

```powershell
pip install plotly>=5.17.0
```

---

## Quick Reference

**Minimal installation (no plotly):**
```powershell
.\venv\Scripts\Activate.ps1
pip install pandas numpy python-dateutil snowflake-connector-python python-dotenv
```

**Install everything, then remove plotly:**
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip uninstall plotly -y
```

**Install from modified requirements.txt:**
1. Comment out plotly line in `requirements.txt`
2. `pip install -r requirements.txt`

---

## Summary

**Easiest method:** Install packages individually, excluding plotly:
```powershell
pip install pandas numpy python-dateutil snowflake-connector-python python-dotenv
```

**If you already installed everything:** Just uninstall plotly:
```powershell
pip uninstall plotly -y
```

Plotly is only needed for the Streamlit dashboards, so you can safely skip it if you don't need those features.

