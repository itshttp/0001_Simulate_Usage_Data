# How to Get Updated Code from Repository

This guide shows you how to pull the latest code updates from the git repository.

## Quick Update (Recommended)

### Step 1: Check Current Status

```powershell
git status
```

This shows:
- Current branch
- Any uncommitted changes
- Files that differ from the remote

### Step 2: Stash or Commit Local Changes (If Any)

**If you have uncommitted changes you want to keep:**

**Option A: Stash changes (temporary save)**
```powershell
git stash
```

**Option B: Commit changes**
```powershell
git add .
git commit -m "Your commit message"
```

**Option C: Discard local changes (⚠️ WARNING: This deletes your changes!)**
```powershell
git reset --hard
```

### Step 3: Pull Latest Updates

```powershell
git pull origin main
```

Or simply:
```powershell
git pull
```

This will:
- Fetch the latest changes from the remote repository
- Merge them into your local branch
- Update your files

## Complete Update Process

### Method 1: Simple Pull (If No Conflicts)

```powershell
# 1. Check status
git status

# 2. Pull latest changes
git pull origin main

# 3. Verify update
git log --oneline -5
```

### Method 2: Fetch and Merge (More Control)

```powershell
# 1. Fetch latest changes (doesn't modify your files yet)
git fetch origin

# 2. Check what changed
git log HEAD..origin/main --oneline

# 3. Merge the changes
git merge origin/main
```

### Method 3: Reset to Match Remote (⚠️ Discards Local Changes)

**Use this ONLY if you want to completely replace your local code with remote:**

```powershell
# 1. Fetch latest
git fetch origin

# 2. Reset to match remote (⚠️ WARNING: Deletes local changes!)
git reset --hard origin/main
```

## Handling Conflicts

If you get merge conflicts:

### Step 1: See Which Files Have Conflicts

```powershell
git status
```

### Step 2: Resolve Conflicts

Open the conflicted files and look for conflict markers:
```
<<<<<<< HEAD
Your local changes
=======
Remote changes
>>>>>>> origin/main
```

Edit the file to resolve the conflict, then:

### Step 3: Mark as Resolved

```powershell
git add <filename>
git commit -m "Resolved merge conflicts"
```

## Checking for Updates Without Pulling

To see if there are updates available without pulling:

```powershell
# Fetch latest info
git fetch origin

# Compare local vs remote
git log HEAD..origin/main --oneline

# Or see a summary
git status
```

## Common Scenarios

### Scenario 1: You Have No Local Changes

```powershell
git pull
```

### Scenario 2: You Have Uncommitted Changes You Want to Keep

```powershell
# Save your changes temporarily
git stash

# Pull updates
git pull

# Restore your changes
git stash pop
```

### Scenario 3: You Want to See What Changed First

```powershell
# Fetch without merging
git fetch origin

# See what's new
git log HEAD..origin/main --oneline

# See file changes
git diff HEAD origin/main

# Then pull when ready
git pull
```

### Scenario 4: You Want to Discard All Local Changes

```powershell
# ⚠️ WARNING: This deletes all uncommitted changes!
git reset --hard
git clean -fd
git pull
```

## Verify Update Was Successful

After pulling:

```powershell
# Check latest commits
git log --oneline -5

# Check current status
git status

# Verify you're up to date
git status  # Should say "Your branch is up to date with 'origin/main'"
```

## Troubleshooting

### Error: "Your local changes would be overwritten"

**Solution:** Stash or commit your changes first:
```powershell
git stash
git pull
git stash pop
```

### Error: "Merge conflict"

**Solution:** Resolve conflicts manually (see "Handling Conflicts" above)

### Error: "Repository not found" or "Permission denied"

**Solution:** Check your remote URL:
```powershell
git remote -v
```

If needed, update the remote:
```powershell
git remote set-url origin https://github.com/itshttp/0001_Simulate_Usage_Data.git
```

### Error: "Branch is behind"

**Solution:** This is normal - just pull:
```powershell
git pull
```

## Quick Reference Commands

```powershell
# Check status
git status

# Pull latest updates
git pull

# Fetch without merging
git fetch origin

# See what's new
git log HEAD..origin/main --oneline

# Stash local changes
git stash

# Restore stashed changes
git stash pop

# Discard local changes (⚠️ WARNING!)
git reset --hard origin/main
```

## Best Practices

1. ✅ **Always check status first** - `git status`
2. ✅ **Commit or stash local changes** before pulling
3. ✅ **Pull regularly** to stay up to date
4. ✅ **Review changes** with `git log` before pulling if unsure
5. ⚠️ **Never use `git reset --hard`** unless you're sure you want to lose changes

## Your Current Repository

- **Remote:** https://github.com/itshttp/0001_Simulate_Usage_Data.git
- **Branch:** main
- **Status:** Up to date with origin/main

## Next Steps After Updating

After pulling updates:

1. **Check for new dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Review changes:**
   ```powershell
   git log --oneline -10
   ```

3. **Test the updated code:**
   ```powershell
   python snowflake_loader.py --test
   ```

---

**Quick Update Command:**
```powershell
git pull origin main
```

