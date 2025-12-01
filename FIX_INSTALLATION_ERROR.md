# Fixing "No such file or directory" Installation Error

You're encountering a Windows path length limitation error during package installation. This is a common issue with Microsoft Store Python installations.

## The Error

```
ERROR: Could not install packages due to an OSError: [Errno 2] No such file or directory: 
'C:\\Users\\jun.cheng\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python311\\site-packages\\jedi\\third_party\\typeshed\\third_party\\2and3\\requests\\packages\\urllib3\\packages\\ssl_match_hostname\\_implementation.pyi'
```

**Causes:**
- Windows 260 character path length limit
- Microsoft Store Python uses very long paths
- Nested directory structure in packages

## Solution 1: Use Virtual Environment (Recommended) ⭐⭐⭐

**This is the best solution** - virtual environments have shorter paths:

```powershell
# Make sure you're in your project directory
cd C:\Users\jun.cheng\Desktop\Project\0001_Simulate_Usage_Data

# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Now install packages in venv (shorter paths)
pip install -r requirements.txt
```

The virtual environment will use much shorter paths, avoiding the Windows limit.

## Solution 2: Enable Long Path Support in Windows

Enable Windows long path support (requires Administrator):

### Step 1: Enable via Group Policy (Windows Pro/Enterprise)

1. Press `Windows Key + R`
2. Type `gpedit.msc` and press Enter
3. Navigate to: `Computer Configuration` → `Administrative Templates` → `System` → `Filesystem`
4. Find "Enable Win32 long paths"
5. Double-click and set to **Enabled**
6. Click **OK**
7. **Restart your computer**

### Step 2: Enable via Registry (All Windows Versions)

⚠️ **Backup your registry first!**

1. Press `Windows Key + R`
2. Type `regedit` and press Enter
3. Navigate to: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem`
4. Find `LongPathsEnabled` (or create a DWORD if it doesn't exist)
5. Set value to `1`
6. **Restart your computer**

### Step 3: Enable via PowerShell (Run as Administrator)

```powershell
# Run PowerShell as Administrator
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

Then restart your computer.

## Solution 3: Install Packages Individually (Skip Jupyter)

If you don't need Jupyter notebooks, skip the problematic packages:

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Install core packages only (skip jupyter)
pip install pandas numpy python-dateutil
pip install snowflake-connector-python python-dotenv

# Optional: Install visualization (if needed)
pip install matplotlib seaborn

# Skip jupyter and streamlit if you don't need them
# pip install jupyter  # This causes the error
# pip install streamlit plotly  # Skip if not needed
```

## Solution 4: Clear Pip Cache

Corrupted cache can cause issues:

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Clear pip cache
pip cache purge

# Upgrade pip first
python -m pip install --upgrade pip

# Try installing again
pip install -r requirements.txt
```

## Solution 5: Install in Batches

Install packages in smaller groups:

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Batch 1: Core dependencies
pip install pandas numpy python-dateutil

# Batch 2: Snowflake
pip install snowflake-connector-python python-dotenv

# Batch 3: Visualization (optional)
pip install matplotlib seaborn

# Batch 4: Jupyter (if needed - this might fail)
pip install jupyter ipykernel

# Batch 5: Streamlit (optional)
pip install streamlit plotly
```

If jedi/jupyter installation fails, you can skip it if you don't need notebooks.

## Solution 6: Use Different Python Installation

If you continue having issues with Microsoft Store Python, consider:

### Option A: Install Python from python.org

1. Download Python from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Use this Python instead of Microsoft Store version

### Option B: Use Anaconda/Miniconda

1. Download from https://www.anaconda.com/download
2. Install Anaconda
3. Use conda environment instead

## Solution 7: Install Without Jedi (Workaround)

If you need Jupyter but jedi fails, try installing without it:

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Install jupyter without jedi (less IDE features but works)
pip install jupyter ipykernel --no-deps
pip install notebook jupyterlab --no-deps
# Then manually install other dependencies
pip install tornado pyzmq traitlets
```

## Recommended Approach for This Project

**For Snowflake connection and data generation only:**

```powershell
# 1. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 2. Install only what you need (skip jupyter)
pip install pandas numpy python-dateutil
pip install snowflake-connector-python python-dotenv

# 3. Test connection
python snowflake_loader.py --test
```

**If you need notebooks:**
1. Enable long path support (Solution 2)
2. Or use venv and install jupyter separately later

## Quick Fix: Minimal Installation

If you just need to test Snowflake connection:

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Install minimum required packages
pip install pandas numpy python-dateutil snowflake-connector-python python-dotenv

# Test connection
python snowflake_loader.py --test
```

This avoids the problematic jedi/jupyter installation entirely.

## Verify Installation

After installing (even without jupyter), verify:

```powershell
# Test core packages
python -c "import pandas; print('pandas OK')"
python -c "import numpy; print('numpy OK')"
python -c "import snowflake.connector; print('snowflake OK')"

# Test Snowflake connection
python snowflake_loader.py --test
```

## What You Can Skip

If you're not using:
- **Jupyter notebooks** → Skip `jupyter`, `ipykernel`
- **Streamlit dashboard** → Skip `streamlit`, `plotly`
- **Visualization in notebooks** → Skip `matplotlib`, `seaborn`

You only need:
- ✅ `pandas`, `numpy`, `python-dateutil` (core data)
- ✅ `snowflake-connector-python`, `python-dotenv` (Snowflake connection)

## Summary

**Quick fix (recommended):**
```powershell
.\venv\Scripts\Activate.ps1
pip install pandas numpy python-dateutil snowflake-connector-python python-dotenv
```

**If you need notebooks:**
1. Enable Windows long path support (Solution 2)
2. Or install packages in venv in smaller batches

**For this project, you probably don't need jupyter** - just install the core packages!

