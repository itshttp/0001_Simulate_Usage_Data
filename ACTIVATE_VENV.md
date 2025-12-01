# How to Activate Virtual Environment

This guide shows you how to activate your Python virtual environment on different operating systems.

## Windows (PowerShell) - Your System ⭐

Since you're on Windows, use these commands:

### Step 1: Open PowerShell

1. Press `Windows Key + X`
2. Select "Windows PowerShell" or "Terminal"
3. Navigate to your project directory:
   ```powershell
   cd C:\Users\jun.cheng\Desktop\Project\0001_Simulate_Usage_Data
   ```

### Step 2: Activate Virtual Environment

If you already have a virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

**If you get an execution policy error**, run this first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again:
```powershell
.\venv\Scripts\Activate.ps1
```

### Step 3: Verify Activation

You should see `(venv)` at the beginning of your prompt:

```powershell
(venv) PS C:\Users\jun.cheng\Desktop\Project\0001_Simulate_Usage_Data>
```

### Alternative: Windows Command Prompt (CMD)

If you prefer Command Prompt:

```cmd
cd C:\Users\jun.cheng\Desktop\Project\0001_Simulate_Usage_Data
venv\Scripts\activate.bat
```

You should see:
```cmd
(venv) C:\Users\jun.cheng\Desktop\Project\0001_Simulate_Usage_Data>
```

---

## If Virtual Environment Doesn't Exist Yet

### Create Virtual Environment (Windows)

```powershell
# Navigate to project directory
cd C:\Users\jun.cheng\Desktop\Project\0001_Simulate_Usage_Data

# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1
```

### Install Dependencies

After activation, install project dependencies:

```powershell
pip install -r requirements.txt
```

---

## Mac/Linux

If you're on Mac or Linux:

```bash
# Navigate to project directory
cd path/to/0001_Simulate_Usage_Data

# Activate virtual environment
source venv/bin/activate
```

You should see `(venv)` at the beginning of your prompt:
```bash
(venv) user@computer:~/Project/0001_Simulate_Usage_Data$
```

---

## Quick Reference

### Windows PowerShell
```powershell
.\venv\Scripts\Activate.ps1
```

### Windows CMD
```cmd
venv\Scripts\activate.bat
```

### Mac/Linux
```bash
source venv/bin/activate
```

---

## After Activation

Once your virtual environment is activated, you can:

1. **Test Snowflake connection:**
   ```powershell
   python snowflake_loader.py --test
   ```

2. **Install packages:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Run Python scripts:**
   ```powershell
   python your_script.py
   ```

---

## Deactivate Virtual Environment

When you're done, deactivate the virtual environment:

```powershell
deactivate
```

Or simply close the terminal window.

---

## Troubleshooting

### Error: "Execution Policy" on Windows

**Error:**
```
.venv\Scripts\Activate.ps1 : cannot be loaded because running scripts is disabled on this system
```

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again.

### Error: "venv folder not found"

**Solution:** Create the virtual environment first:
```powershell
python -m venv venv
```

### Error: "python command not found"

**Solution:** Try using `python3` instead:
```powershell
python3 -m venv venv
```

Or check if Python is installed and in your PATH.

---

## Visual Guide: How to Know It's Activated

**Before activation:**
```powershell
PS C:\Users\jun.cheng\Desktop\Project\0001_Simulate_Usage_Data>
```

**After activation:**
```powershell
(venv) PS C:\Users\jun.cheng\Desktop\Project\0001_Simulate_Usage_Data>
```

Notice the `(venv)` prefix - that means your virtual environment is active!

---

## Next Steps

After activating your virtual environment:

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Test Snowflake connection: `python snowflake_loader.py --test`
3. ✅ Start using the project!

---

**Need help?** Check [NEW_SNOWFLAKE_SETUP.md](NEW_SNOWFLAKE_SETUP.md) for complete setup instructions.

