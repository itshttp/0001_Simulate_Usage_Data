"""
Reproducibility Setup for PyTorch Models

Add this code to the beginning of your training notebooks to ensure
reproducible results across multiple runs.
"""

import torch
import numpy as np
import random
import os

def set_seed(seed=42):
    """
    Set random seeds for reproducibility.

    This ensures that:
    - Data splits are identical
    - Model initialization is identical
    - Training order is identical

    Args:
        seed: Random seed value (default: 42)
    """
    # Python random
    random.seed(seed)

    # Numpy
    np.random.seed(seed)

    # PyTorch
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)  # for multi-GPU

    # PyTorch backend
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    # Python hash seed
    os.environ['PYTHONHASHSEED'] = str(seed)

    print(f"✓ Random seed set to {seed} for reproducibility")


# ============================================================================
# HOW TO USE IN YOUR NOTEBOOK
# ============================================================================
"""
Add this to the FIRST code cell of your training notebook (after imports):

```python
# Ensure reproducibility
set_seed(42)
```

This guarantees that:
1. split_data() will create the same train/test split every time
2. Model weights will initialize the same way
3. Training will be deterministic
4. Results will be identical across runs

IMPORTANT:
- Call set_seed() BEFORE any random operations
- Use the same seed value (42) in both notebooks
- Don't regenerate your data between training runs
"""

if __name__ == "__main__":
    print("="*70)
    print("REPRODUCIBILITY SETUP")
    print("="*70)
    print("\nTo ensure identical results across training runs:")
    print("\n1. Add this to your training notebook (first code cell):")
    print("\n   from ensure_reproducibility import set_seed")
    print("   set_seed(42)")
    print("\n2. Use the same seed value in both notebooks")
    print("\n3. Don't regenerate data between runs")
    print("\n" + "="*70)

    # Test it
    set_seed(42)
