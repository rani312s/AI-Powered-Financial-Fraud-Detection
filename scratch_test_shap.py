from model.fraud_model import fraud_detector
import json

tx_normal = {
    'amount': 2500.0,
    'transaction_type': 'Purchase',
    'recipient': "Nature's Basket",
    'time': '14:30:00',
    'new_device': 0,
    'unusual_location': 0,
    'typical_time': 1
}

res_normal = fraud_detector.predict_transaction(tx_normal)
print("=== NORMAL TRANSACTION ===")
print(f"Fraud Probability: {res_normal['fraud_probability']}%")
print(f"Risk Score: {res_normal['risk_score']}")
print(f"Risk Level: {res_normal['risk_level']}")
print("Attributions:")
for f in res_normal['feature_importance']:
    print(f"  [{f['direction']}] {f['feature']} ({f['raw_feature']}): Raw SHAP = {f['raw_shap']}, Impact Share = {f['impact']}%")

tx_high = {
    'amount': 80000.0,
    'transaction_type': 'Online Transfer',
    'recipient': "CryptoGlobal Desk",
    'time': '03:15:00',
    'new_device': 1,
    'unusual_location': 1,
    'typical_time': 0
}

res_high = fraud_detector.predict_transaction(tx_high)
print("\n=== HIGH RISK TRANSACTION ===")
print(f"Fraud Probability: {res_high['fraud_probability']}%")
print(f"Risk Score: {res_high['risk_score']}")
print(f"Risk Level: {res_high['risk_level']}")
print("Attributions:")
for f in res_high['feature_importance']:
    print(f"  [{f['direction']}] {f['feature']} ({f['raw_feature']}): Raw SHAP = {f['raw_shap']}, Impact Share = {f['impact']}%")
