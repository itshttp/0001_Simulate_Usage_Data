# Fix Model Reproducibility Issues

## 🎯 Problem
Two "identical" models show different metrics because they were evaluated on different test data.

## ✅ Solution

### Step 1: Add Seed Setting to Training Notebooks

Add this code to **Cell 2** (right after imports) in BOTH notebooks:

#### For churn_prediction_snowflake.ipynb (v1):
```python
# ADD THIS AFTER THE IMPORTS CELL (Cell 2)

import random

def set_seed(seed=42):
    """Set random seeds for reproducibility"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

set_seed(42)
print("✓ Random seed set to 42 for reproducibility")
```

#### For PICKLE.ipynb (v2):
```python
# ADD THIS AFTER THE IMPORTS CELL (Cell 2)
# Use the SAME code as above
set_seed(42)
```

### Step 2: Verify the Issue First

Before retraining, let's see what's actually different:

```bash
# Run the diagnostic script
python debug_model_differences.py churn_model_v1.pkl churn_model_v2.pkl
```

This will tell you:
- ✅ Are weights identical? (if yes, it's a data split issue)
- ✅ Are metrics different? (if yes, confirms the problem)
- ✅ What exactly differs between the models

### Step 3: Retrain with Reproducibility

1. **Delete old model files** (to avoid confusion):
   ```bash
   rm churn_model_v1.pkl churn_model_v2.pkl
   rm churn_model_v1.pth churn_model_v2.pth
   ```

2. **Add seed setting** to both notebooks (see Step 1)

3. **Train v1**:
   - Run `churn_prediction_snowflake.ipynb` completely
   - Save as v1

4. **Copy v1 to v2** (for testing):
   ```bash
   cp churn_model_v1.pkl churn_model_v2.pkl
   ```

5. **Compare again**:
   ```bash
   python debug_model_differences.py churn_model_v1.pkl churn_model_v2.pkl
   ```

Now they should be **100% identical** - same weights, same metrics.

## 🔍 Understanding the Root Cause

### What Happened

```python
# First training run (v1)
df.sample(frac=1, random_state=42)  # Shuffles data
# → Test accounts: [A, B, C, D, E]
# → Model evaluated on these → Metrics: F1=0.85

# Second training run (v2) - NO SEED SET
df.sample(frac=1, random_state=42)  # Same random_state
# BUT if numpy random state is different:
# → Test accounts: [F, G, H, I, J]  ← Different accounts!
# → Model evaluated on these → Metrics: F1=0.78  ← Different!
```

### Why `random_state=42` Alone Isn't Enough

The `split_data()` function uses pandas `.sample()` with `random_state=42`, but:
- Pandas relies on NumPy's random state
- If NumPy random state differs between runs, you get different splits
- Other randomness: PyTorch initialization, dropout, batch shuffling

## 📊 Expected Results After Fix

### Before Fix (Current):
```
Model 1: F1=0.8234, Precision=0.7891, Recall=0.8567
Model 2: F1=0.7845, Precision=0.8123, Recall=0.7590  ← Different!
```

### After Fix (with set_seed):
```
Model 1: F1=0.8234, Precision=0.7891, Recall=0.8567
Model 2: F1=0.8234, Precision=0.7891, Recall=0.8567  ← Identical!
```

## 🎓 When Results SHOULD Differ

Results should differ when:
- ✅ Different model architecture (v1 vs v2 with actual changes)
- ✅ Different hyperparameters
- ✅ Different training data
- ✅ Intentional improvements

Results should NOT differ when:
- ❌ Just copying model files
- ❌ Running same notebook twice
- ❌ Testing "identical" models

## 💡 Quick Check

To verify if two models are truly identical:

```python
import pickle

with open('churn_model_v1.pkl', 'rb') as f:
    m1 = pickle.load(f)
with open('churn_model_v2.pkl', 'rb') as f:
    m2 = pickle.load(f)

# Check if weights are identical
import torch
weights_same = all(
    torch.equal(m1['model_state_dict'][k], m2['model_state_dict'][k])
    for k in m1['model_state_dict'].keys()
)

print(f"Weights identical: {weights_same}")
print(f"F1 scores: {m1['test_metrics']['f1']:.4f} vs {m2['test_metrics']['f1']:.4f}")

if weights_same and m1['test_metrics']['f1'] != m2['test_metrics']['f1']:
    print("⚠️ Same model, different test data!")
```

## 📝 Summary

1. **Run diagnostic**: `python debug_model_differences.py model1.pkl model2.pkl`
2. **Add seed setting** to both notebooks
3. **Retrain** with reproducibility enabled
4. **Verify** results are now identical

This ensures your comparisons are fair and reproducible!
