# Churn Prediction Model - README

## Overview

This notebook trains a churn prediction model using **real Snowflake data from MY_DATABASE.PUBLIC** with a **12-month lookback window** and **LSTM with Attention** architecture.

⚠️ **IMPORTANT:** This notebook does NOT generate synthetic data. It uses your actual data from `MY_DATABASE.PUBLIC`.

## Notebook: `churn_prediction_snowflake.ipynb`

### What This Notebook Does

1. **Loads Real Data from MY_DATABASE.PUBLIC**
   - `MY_DATABASE.PUBLIC.PHONE_USAGE_DATA` - Monthly usage metrics
   - `MY_DATABASE.PUBLIC.ACCOUNT_ATTRIBUTES_MONTHLY` - Account information
   - `MY_DATABASE.PUBLIC.CHURN_RECORDS` - Churn labels

2. **Creates Time-Series Features**
   - Extracts up to 12 months of usage history per account
   - 10 normalized features per month:
     - Total calls (normalized)
     - Total minutes (normalized)
     - Voice calls, Fax calls
     - Inbound/Outbound calls
     - Device usage (Hardphone, Softphone, Mobile)
     - Monthly active users (MAU)

3. **Trains LSTM + Attention Model**
   - PyTorch-based deep learning model
   - Attention mechanism to focus on important months
   - Binary classification (will churn vs won't churn)

4. **Evaluates Performance**
   - Metrics: F1 Score, Precision, Recall, AUC-ROC
   - Visualizations: ROC curve, confusion matrix, training history
   - Detailed classification report

5. **Saves Results to MY_DATABASE.PUBLIC**
   - `MY_DATABASE.PUBLIC.CHURN_PREDICTIONS` - Account-level predictions
   - `MY_DATABASE.PUBLIC.CHURN_MODEL_METRICS` - Model performance metrics

## Key Differences from Example Notebook

| Aspect | Example Notebook | **This Notebook** |
|--------|------------------|-------------------|
| **Data Source** | Generated pseudo data | **MY_DATABASE.PUBLIC (real data)** |
| **Database** | N/A | **MY_DATABASE** |
| **Schema** | N/A | **PUBLIC** |
| **Features** | 5 synthetic features | **10 real usage metrics** |
| **Data Loading** | `generate_pseudo_churn_data()` | **Loads from Snowflake tables** |
| **Sequences** | Random patterns | **Actual 12-month history** |
| **Labels** | Simulated churn | **Real churn records** |
| **Results** | In-memory only | **Saved to MY_DATABASE.PUBLIC** |

## How to Use

### 1. Run in Snowflake Notebook

```python
# The notebook is designed to run in Snowflake Notebooks
# It automatically connects using get_active_session()
```

### 2. Prerequisites

- Snowflake account with Notebooks enabled
- **Database:** `MY_DATABASE` must exist
- **Schema:** `PUBLIC` must exist
- **Tables must exist in MY_DATABASE.PUBLIC:**
  - `MY_DATABASE.PUBLIC.PHONE_USAGE_DATA`
  - `MY_DATABASE.PUBLIC.ACCOUNT_ATTRIBUTES_MONTHLY`
  - `MY_DATABASE.PUBLIC.CHURN_RECORDS`
- PyTorch and required packages installed
- Warehouse with sufficient compute for training

### 3. Run All Cells

The notebook is structured in order:
1. Import libraries
2. Connect to Snowflake
3. Load data
4. Feature engineering (12-month sequences)
5. Train/val/test split
6. Define PyTorch model
7. Train model
8. Evaluate on test set
9. Visualize results
10. Save predictions to Snowflake

## Model Architecture

```
LSTMWithAttention(
  (lstm): LSTM(10, 64, num_layers=2, batch_first=True, dropout=0.3)
  (attention): Linear(in_features=64, out_features=1, bias=True)
  (fc1): Linear(in_features=64, out_features=32, bias=True)
  (fc2): Linear(in_features=32, out_features=1, bias=True)
  (relu): ReLU()
  (dropout): Dropout(p=0.3, inplace=False)
  (sigmoid): Sigmoid()
)
```

**Parameters:** ~12,000 trainable parameters

## Features Used (10 per month)

1. **Total Calls (normalized)** - Overall call volume
2. **Total Minutes (normalized)** - Total talk time
3. **Voice Calls (normalized)** - Voice communication
4. **Fax Calls (normalized)** - Fax usage
5. **Inbound Calls (normalized)** - Incoming calls
6. **Outbound Calls (normalized)** - Outgoing calls
7. **Hardphone Calls (normalized)** - Desk phone usage
8. **Softphone Calls (normalized)** - Software phone usage
9. **Mobile Calls (normalized)** - Mobile device usage
10. **MAU (normalized)** - Monthly active users

All features are normalized to [0, 1] range for better training.

## Training Configuration

```python
LEARNING_RATE = 0.001
NUM_EPOCHS = 50
PATIENCE = 7  # Early stopping
BATCH_SIZE = 32
MAX_LOOKBACK_WINDOW = 12  # months
HIDDEN_SIZE = 64
NUM_LAYERS = 2
DROPOUT = 0.3
THRESHOLD = 0.5  # Classification threshold
```

## Output Tables in Snowflake (MY_DATABASE.PUBLIC)

### 1. `MY_DATABASE.PUBLIC.CHURN_PREDICTIONS`

Contains predictions for all test accounts:

| Column | Type | Description |
|--------|------|-------------|
| `ACCOUNT_ID` | String | Account identifier |
| `ACTUAL_CHURN` | Integer | True label (0 or 1) |
| `CHURN_PROBABILITY` | Float | Predicted probability (0-1) |
| `PREDICTED_CHURN` | Integer | Predicted label (0 or 1) |
| `SEQUENCE_LENGTH` | Integer | Months of history used |

**Use Cases:**
- Identify high-risk accounts for intervention
- Prioritize customer success efforts
- Track prediction accuracy over time

### 2. `MY_DATABASE.PUBLIC.CHURN_MODEL_METRICS`

Contains model performance metrics:

| Column | Type | Description |
|--------|------|-------------|
| `MODEL_NAME` | String | Model identifier |
| `TRAIN_DATE` | Timestamp | When model was trained |
| `TEST_LOSS` | Float | Test set loss |
| `TEST_PRECISION` | Float | Precision score |
| `TEST_RECALL` | Float | Recall score |
| `TEST_F1_SCORE` | Float | F1 score |
| `TEST_AUC_ROC` | Float | AUC-ROC score |
| `NUM_FEATURES` | Integer | Number of features |
| `LOOKBACK_WINDOW` | Integer | Months of history |
| ... | ... | Other config params |

**Use Cases:**
- Track model performance over time
- Compare different model versions
- Monitor for model drift

## Expected Performance

Based on your data characteristics, you should expect:

- **F1 Score:** 0.60 - 0.85 (depends on data quality)
- **Precision:** 0.55 - 0.90
- **Recall:** 0.50 - 0.85
- **AUC-ROC:** 0.70 - 0.95

Lower scores may indicate:
- Insufficient training data
- Class imbalance (too few churned accounts)
- Features need improvement
- Need more data preprocessing

## Next Steps After Training

1. **Review High-Risk Accounts**
   ```sql
   SELECT *
   FROM MY_DATABASE.PUBLIC.CHURN_PREDICTIONS
   WHERE CHURN_PROBABILITY > 0.7
   ORDER BY CHURN_PROBABILITY DESC;
   ```

2. **Analyze Feature Importance**
   - Look at attention weights to see which months matter most
   - Identify patterns in churned vs active accounts

3. **Integrate with Business Workflows**
   - Set up alerts for high-risk accounts
   - Create dashboards in Streamlit
   - Automate intervention workflows

4. **Monitor Model Performance**
   - Track predictions vs actual churn monthly
   - Retrain model quarterly with new data
   - Watch for model drift

5. **Improve Model**
   - Add more features (account attributes, support tickets, etc.)
   - Experiment with different architectures
   - Try ensemble methods
   - Handle class imbalance better

## Troubleshooting

### Error: "No module named 'torch'"

Install PyTorch in your Snowflake environment:
```python
!pip install torch torchvision torchaudio
```

### Error: "Table not found"

Ensure tables exist in MY_DATABASE.PUBLIC:
```sql
USE DATABASE MY_DATABASE;
USE SCHEMA PUBLIC;

SHOW TABLES LIKE 'PHONE_USAGE_DATA';
SHOW TABLES LIKE 'ACCOUNT_ATTRIBUTES_MONTHLY';
SHOW TABLES LIKE 'CHURN_RECORDS';

-- Or use fully qualified names:
SELECT COUNT(*) FROM MY_DATABASE.PUBLIC.PHONE_USAGE_DATA;
SELECT COUNT(*) FROM MY_DATABASE.PUBLIC.ACCOUNT_ATTRIBUTES_MONTHLY;
SELECT COUNT(*) FROM MY_DATABASE.PUBLIC.CHURN_RECORDS;
```

### Low Model Performance

Try these improvements:
1. Increase training data (more months)
2. Add more features (account attributes, support metrics)
3. Handle class imbalance (use weighted loss)
4. Tune hyperparameters (learning rate, hidden size)
5. Try different architectures (GRU, Transformer)

### Out of Memory

Reduce batch size:
```python
BATCH_SIZE = 16  # or 8
```

## Model Interpretability

The attention mechanism shows which months are most important for predictions:

```python
# Get attention weights for a specific account
with torch.no_grad():
    sequence = test_dataset[0][0].unsqueeze(0).to(device)
    prob, attention = model(sequence, return_attention=True)

# attention shape: [1, 12, 1]
# Higher values = more important months
```

Use this to understand:
- Which months predict churn best
- How usage patterns change before churn
- When to intervene for at-risk accounts

## Questions?

For issues or questions:
1. Check Snowflake Notebooks documentation
2. Review PyTorch tutorials for LSTM models
3. Analyze your data quality and distribution
4. Experiment with different hyperparameters

---

**Created:** 2025-11-02
**Model:** LSTM with Attention
**Framework:** PyTorch
**Data Source:** Snowflake Tables
