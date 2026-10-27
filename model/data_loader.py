import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

RAW_TXN_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'train_transaction.csv')
RAW_ID_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'train_identity.csv')
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
METADATA_PATH = os.path.join(PROCESSED_DIR, 'dataset_metadata.json')
PROCESSED_DATA_PATH = os.path.join(PROCESSED_DIR, 'ieee_fraud_processed.parquet')

# Define the 6 Multi-Modal Information Categories for IEEE-CIS Dataset
FEATURE_GROUPS = {
    "transaction_features": {
        "title": "Transaction Core Information",
        "description": "Monetary values, product category codes, and transactional time offsets.",
        "columns": ["TransactionAmt", "ProductCD", "TransactionDT"]
    },
    "identity_features": {
        "title": "Identity & Verification Features",
        "description": "Digital identity signatures, verification flags, and security protocol ratings (id_01 to id_38).",
        "columns": ["id_01", "id_12", "id_15", "id_16", "id_28", "id_29", "id_31", "id_35", "id_36", "id_37", "id_38"]
    },
    "device_network_features": {
        "title": "Device & Network Information",
        "description": "Operating system, browser hardware fingerprints, and purchaser/recipient email domains.",
        "columns": ["DeviceType", "DeviceInfo", "P_emaildomain", "R_emaildomain"]
    },
    "behavioral_features": {
        "title": "Behavioral Counters & Velocity Deltas",
        "description": "Transaction velocity counts (C1-C14) and time differences from prior user actions (D1-D15).",
        "columns": ["C1", "C2", "C5", "C6", "C9", "C11", "C13", "C14", "D1", "D2", "D4", "D10", "D15"]
    },
    "numerical_features": {
        "title": "Numerical & Spatial Attributes",
        "description": "Billing/card numerical identifiers, geographic distance estimates, and Vesta multi-factor scores.",
        "columns": ["card1", "card2", "card3", "card5", "addr1", "addr2", "dist1", "V12", "V13", "V29", "V30", "V44", "V45", "V75", "V76", "V86", "V87", "V90", "V91", "V107", "V126", "V127", "V128", "V130", "V282", "V283", "V306", "V307", "V308", "V310"]
    },
    "categorical_features": {
        "title": "Categorical Attributes",
        "description": "Payment card networks, card funding types (credit/debit), and address matching criteria (M1-M9).",
        "columns": ["card4", "card6", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9"]
    }
}

def load_and_preprocess_dataset():
    """
    Executes the complete, leakage-free data processing pipeline:
    1. Loads raw authentic IEEE-CIS transaction and identity tables.
    2. Joins tables on TransactionID.
    3. Selects representative features across all 6 multi-modal categories.
    4. Handles missing values and encodings on train split first to avoid data leakage.
    5. Saves metadata, sample rows, and train/test splits.
    """
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    print("[Data Pipeline] Loading raw IEEE-CIS dataset files...")
    if not os.path.exists(RAW_TXN_PATH) or not os.path.exists(RAW_ID_PATH):
        raise FileNotFoundError("Raw IEEE-CIS files not found in data/raw/")

    df_txn = pd.read_csv(RAW_TXN_PATH)
    df_id = pd.read_csv(RAW_ID_PATH)

    print(f"[Data Pipeline] Raw Transactions: {df_txn.shape}, Raw Identity: {df_id.shape}")

    # 1. Join on TransactionID
    df = pd.merge(df_txn, df_id, on='TransactionID', how='left')
    print(f"[Data Pipeline] Merged Dataset Shape: {df.shape}")

    total_records = len(df)
    total_raw_cols = df.shape[1]
    fraud_counts = df['isFraud'].value_counts().to_dict()
    fraud_records = int(fraud_counts.get(1, 0))
    non_fraud_records = int(fraud_counts.get(0, 0))
    fraud_percentage = round((fraud_records / total_records) * 100, 2)

    print(f"[Data Pipeline] Class Distribution: Non-Fraud={non_fraud_records}, Fraud={fraud_records} ({fraud_percentage}%)")

    # 2. Extract columns present in feature groups
    selected_cols = ['TransactionID', 'isFraud']
    feature_cols = []
    
    for group_name, group_info in FEATURE_GROUPS.items():
        for col in group_info["columns"]:
            if col in df.columns and col not in selected_cols:
                selected_cols.append(col)
                feature_cols.append(col)

    df_subset = df[selected_cols].copy()
    print(f"[Data Pipeline] Selected {len(feature_cols)} features across 6 multi-modal groups.")

    # 3. Separate Features (X) and Target (y)
    X = df_subset.drop(columns=['TransactionID', 'isFraud'])
    y = df_subset['isFraud'].astype(int)
    tx_ids = df_subset['TransactionID']

    # 4. Identify Numerical and Categorical feature columns cleanly
    cat_cols = []
    num_cols = []
    for col in X.columns:
        if X[col].dtype == 'object' or str(X[col].dtype).startswith('string'):
            cat_cols.append(col)
        elif col in ['ProductCD', 'card4', 'card6', 'DeviceType', 'P_emaildomain', 'R_emaildomain'] or col.startswith('M') or col.startswith('id_'):
            # Some id_ columns or M columns have text or mixed values
            try:
                # Test if purely numeric
                sample_s = pd.to_numeric(X[col].dropna().head(50))
                num_cols.append(col)
            except Exception:
                cat_cols.append(col)
        else:
            try:
                pd.to_numeric(X[col].dropna().head(50))
                num_cols.append(col)
            except Exception:
                cat_cols.append(col)

    # 5. Stratified Train/Test Split (Avoid Data Leakage)
    X_train, X_test, y_train, y_test, id_train, id_test = train_test_split(
        X, y, tx_ids, test_size=0.20, random_state=42, stratify=y
    )

    print(f"[Data Pipeline] Train Split: {len(X_train)} ({int(y_train.sum())} frauds), Test Split: {len(X_test)} ({int(y_test.sum())} frauds)")

    # 6. Preprocessing: Fit transformations ONLY on training set
    encoders = {}
    fill_values = {}

    # Categorical handling
    for col in cat_cols:
        fill_val = 'missing'
        fill_values[col] = fill_val
        X_train_col = X_train[col].astype(str).fillna(fill_val)
        X_test_col = X_test[col].astype(str).fillna(fill_val)
        
        # Frequency / Label mapping based on train frequencies
        top_cats = X_train_col.value_counts().nlargest(20).index.tolist()
        mapping = {cat: idx + 1 for idx, cat in enumerate(top_cats)}
        mapping['missing'] = 0
        encoders[col] = mapping

        X_train[col] = X_train_col.map(lambda v: mapping.get(v, len(top_cats) + 1))
        X_test[col] = X_test_col.map(lambda v: mapping.get(v, len(top_cats) + 1))

    # Numerical handling (Median imputation)
    for col in num_cols:
        med = float(X_train[col].median() if not pd.isna(X_train[col].median()) else 0.0)
        fill_values[col] = med
        X_train[col] = X_train[col].fillna(med)
        X_test[col] = X_test[col].fillna(med)

    # Standard scaling numerical features
    scaler = StandardScaler()
    X_train[num_cols] = scaler.fit_transform(X_train[num_cols])
    X_test[num_cols] = scaler.transform(X_test[num_cols])

    # 7. Generate a real 10-row raw sample for Dataset & Model frontend table
    sample_df = df.head(10)[[
        'TransactionID', 'isFraud', 'TransactionDT', 'TransactionAmt', 'ProductCD',
        'card4', 'card6', 'P_emaildomain', 'DeviceType', 'DeviceInfo'
    ]].copy()
    
    sample_rows = []
    for _, row in sample_df.iterrows():
        sample_rows.append({
            "TransactionID": int(row['TransactionID']),
            "isFraud": int(row['isFraud']),
            "TransactionAmt": float(row['TransactionAmt']),
            "ProductCD": str(row['ProductCD']) if not pd.isna(row['ProductCD']) else "W",
            "card4": str(row['card4']) if not pd.isna(row['card4']) else "visa",
            "card6": str(row['card6']) if not pd.isna(row['card6']) else "debit",
            "P_emaildomain": str(row['P_emaildomain']) if not pd.isna(row['P_emaildomain']) else "gmail.com",
            "DeviceType": str(row['DeviceType']) if not pd.isna(row['DeviceType']) else "mobile",
            "DeviceInfo": str(row['DeviceInfo']) if not pd.isna(row['DeviceInfo']) else "iOS Device"
        })

    # 8. Compile and persist dataset metadata
    metadata = {
        "dataset_name": "IEEE-CIS Fraud Detection Dataset",
        "dataset_source": "Kaggle / Vesta Corporation (IEEE Computational Intelligence Society)",
        "source_url": "https://www.kaggle.com/c/ieee-fraud-detection",
        "total_records": total_records,
        "total_raw_features": total_raw_cols,
        "selected_features_count": len(feature_cols),
        "fraud_records": fraud_records,
        "non_fraud_records": non_fraud_records,
        "fraud_percentage": fraud_percentage,
        "train_records": len(X_train),
        "test_records": len(X_test),
        "feature_groups": FEATURE_GROUPS,
        "sample_rows": sample_rows,
        "feature_columns": feature_cols,
        "cat_columns": cat_cols,
        "num_columns": num_cols
    }

    with open(METADATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    # 9. Save preprocessed data as pickle / npz for instant model loading
    preprocessed_data = {
        'X_train': X_train,
        'X_test': X_test,
        'y_train': y_train,
        'y_test': y_test,
        'id_train': id_train,
        'id_test': id_test,
        'feature_cols': feature_cols,
        'cat_cols': cat_cols,
        'num_cols': num_cols,
        'encoders': encoders,
        'fill_values': fill_values,
        'scaler': scaler
    }
    
    import joblib
    joblib.dump(preprocessed_data, os.path.join(PROCESSED_DIR, 'preprocessed_data.joblib'))
    
    print(f"[Data Pipeline] Preprocessing completed successfully! Saved to {PROCESSED_DIR}")
    return metadata

if __name__ == '__main__':
    load_and_preprocess_dataset()
