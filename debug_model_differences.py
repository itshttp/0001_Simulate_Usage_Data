"""
Debug Model Differences

This script helps identify why two "identical" models produce different results.
"""

import pickle
import torch
import numpy as np

def compare_models(model1_path, model2_path):
    """Compare two model checkpoint files in detail."""

    print("="*80)
    print("MODEL COMPARISON DIAGNOSTICS")
    print("="*80)

    # Load both models
    print("\n📥 Loading models...")
    with open(model1_path, 'rb') as f:
        model1 = pickle.load(f)
    print(f"  ✓ Loaded: {model1_path}")

    with open(model2_path, 'rb') as f:
        model2 = pickle.load(f)
    print(f"  ✓ Loaded: {model2_path}")

    # ========================================================================
    # 1. Compare Metadata
    # ========================================================================
    print("\n" + "="*80)
    print("1️⃣ METADATA COMPARISON")
    print("="*80)

    if 'metadata' in model1 and 'metadata' in model2:
        m1_meta = model1['metadata']
        m2_meta = model2['metadata']

        print(f"\n📅 Training Dates:")
        print(f"  Model 1: {m1_meta.get('train_date', 'N/A')}")
        print(f"  Model 2: {m2_meta.get('train_date', 'N/A')}")
        print(f"  Same: {'✓' if m1_meta.get('train_date') == m2_meta.get('train_date') else '✗'}")

        print(f"\n📊 Dataset Sizes:")
        print(f"  Model 1 - Train: {m1_meta.get('train_samples', 'N/A'):,}, Test: {m1_meta.get('test_samples', 'N/A'):,}")
        print(f"  Model 2 - Train: {m2_meta.get('train_samples', 'N/A'):,}, Test: {m2_meta.get('test_samples', 'N/A'):,}")
        print(f"  Same: {'✓' if m1_meta.get('train_samples') == m2_meta.get('train_samples') else '✗'}")

        print(f"\n🔧 Hyperparameters:")
        for key in ['learning_rate', 'batch_size', 'num_epochs_trained', 'hidden_size', 'dropout']:
            val1 = m1_meta.get(key, 'N/A')
            val2 = m2_meta.get(key, 'N/A')
            match = '✓' if val1 == val2 else '✗'
            print(f"  {key}: {val1} vs {val2} {match}")

    # ========================================================================
    # 2. Compare Model Weights
    # ========================================================================
    print("\n" + "="*80)
    print("2️⃣ MODEL WEIGHTS COMPARISON")
    print("="*80)

    if 'model_state_dict' in model1 and 'model_state_dict' in model2:
        state1 = model1['model_state_dict']
        state2 = model2['model_state_dict']

        # Check if they have the same layers
        keys1 = set(state1.keys())
        keys2 = set(state2.keys())

        if keys1 != keys2:
            print("  ✗ Models have different layers!")
            print(f"    Only in model1: {keys1 - keys2}")
            print(f"    Only in model2: {keys2 - keys1}")
        else:
            print("  ✓ Models have the same layers")

            # Compare weights layer by layer
            all_identical = True
            differences = []

            for key in sorted(keys1):
                tensor1 = state1[key]
                tensor2 = state2[key]

                if tensor1.shape != tensor2.shape:
                    differences.append(f"{key}: different shapes {tensor1.shape} vs {tensor2.shape}")
                    all_identical = False
                else:
                    # Check if weights are identical
                    are_equal = torch.equal(tensor1, tensor2)
                    if not are_equal:
                        # Calculate difference
                        diff = torch.abs(tensor1 - tensor2).max().item()
                        mean_diff = torch.abs(tensor1 - tensor2).mean().item()
                        differences.append(f"{key}: max_diff={diff:.6f}, mean_diff={mean_diff:.6f}")
                        all_identical = False

            if all_identical:
                print("  ✓ All weights are IDENTICAL")
            else:
                print(f"  ✗ Weights are DIFFERENT in {len(differences)} layers:")
                for diff in differences[:10]:  # Show first 10
                    print(f"    • {diff}")
                if len(differences) > 10:
                    print(f"    ... and {len(differences) - 10} more layers")

    # ========================================================================
    # 3. Compare Test Metrics
    # ========================================================================
    print("\n" + "="*80)
    print("3️⃣ TEST METRICS COMPARISON")
    print("="*80)

    if 'test_metrics' in model1 and 'test_metrics' in model2:
        m1_metrics = model1['test_metrics']
        m2_metrics = model2['test_metrics']

        print(f"\n{'Metric':<12} {'Model 1':<12} {'Model 2':<12} {'Difference':<12} {'Match'}")
        print("-" * 65)

        for metric in ['f1', 'precision', 'recall', 'auc', 'loss']:
            if metric in m1_metrics and metric in m2_metrics:
                val1 = m1_metrics[metric]
                val2 = m2_metrics[metric]
                diff = abs(val1 - val2)
                match = '✓' if diff < 0.0001 else '✗'
                print(f"{metric:<12} {val1:<12.6f} {val2:<12.6f} {diff:<12.6f} {match}")

    # ========================================================================
    # 4. Compare Thresholds
    # ========================================================================
    print("\n" + "="*80)
    print("4️⃣ THRESHOLD COMPARISON")
    print("="*80)

    if 'threshold' in model1 and 'threshold' in model2:
        thresh1 = model1['threshold']
        thresh2 = model2['threshold']
        print(f"\n  Model 1 threshold: {thresh1}")
        print(f"  Model 2 threshold: {thresh2}")
        print(f"  Same: {'✓' if thresh1 == thresh2 else '✗'}")

    # ========================================================================
    # 5. Summary and Diagnosis
    # ========================================================================
    print("\n" + "="*80)
    print("📋 DIAGNOSIS SUMMARY")
    print("="*80)

    # Check if weights are identical
    weights_identical = False
    if 'model_state_dict' in model1 and 'model_state_dict' in model2:
        weights_identical = all(
            torch.equal(model1['model_state_dict'][k], model2['model_state_dict'][k])
            for k in model1['model_state_dict'].keys()
        )

    # Check if metrics are different
    metrics_different = False
    if 'test_metrics' in model1 and 'test_metrics' in model2:
        metrics_different = any(
            abs(model1['test_metrics'].get(m, 0) - model2['test_metrics'].get(m, 0)) > 0.0001
            for m in ['f1', 'precision', 'recall', 'auc']
        )

    print("\n🔍 Findings:")

    if weights_identical and metrics_different:
        print("\n  🎯 DIAGNOSIS: Same model weights, but DIFFERENT test metrics")
        print("\n  📌 Most likely causes:")
        print("     1. Models evaluated on DIFFERENT test data")
        print("     2. Different random seeds caused different train/test splits")
        print("     3. Data changed between training runs")
        print("\n  💡 Solution:")
        print("     • Check if both models used the same random_state in split_data()")
        print("     • Verify both models used the same source data")
        print("     • Check timestamps to see if data was regenerated")

    elif not weights_identical and metrics_different:
        print("\n  🎯 DIAGNOSIS: DIFFERENT model weights AND different metrics")
        print("\n  📌 Most likely causes:")
        print("     1. Models trained separately (not copies)")
        print("     2. Different random initialization")
        print("     3. Trained on different data")
        print("\n  💡 Solution:")
        print("     • These are genuinely different models, not copies")
        print("     • If you copied files, check that you copied the right ones")

    elif weights_identical and not metrics_different:
        print("\n  ✅ DIAGNOSIS: Models are IDENTICAL")
        print("\n  These are true copies - same weights, same metrics")

    else:
        print("\n  ⚠️ Unable to determine - insufficient information")

    print("\n" + "="*80)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python debug_model_differences.py model1.pkl model2.pkl")
        print("\nExample:")
        print("  python debug_model_differences.py churn_model_v1.pkl churn_model_v2.pkl")
        sys.exit(1)

    model1_path = sys.argv[1]
    model2_path = sys.argv[2]

    compare_models(model1_path, model2_path)
