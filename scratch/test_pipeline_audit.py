import sys
import os
import json

# Force UTF-8 if supported
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.fraud_model import IEEEFraudModel
from database.db import init_db, get_db_connection, derive_customer_features

def run_tests():
    print("================================================================")
    print("STEP 1: Testing Model Pipeline Directly")
    print("================================================================")
    detector = IEEEFraudModel()

    # Test A: INR 500
    tx_a = {
        'transaction_id': 'TEST-500',
        'amount': 500.0,
        'currency': 'INR',
        'transaction_type': 'Purchase',
        'time': '14:30:00',
        'location': 'Local Region, India',
        'device_type': 'Web Browser (Chrome)',
        'new_device': 0,
        'unusual_location': 0,
        'typical_time': 1,
        'amount_ratio': 1.0,
        'customer_average_amount': 500.0,
        'previous_transaction_count': 0,
        'similar_transaction_count': 0
    }
    res_a = detector.predict_transaction(tx_a)
    print("Test A (INR 500):")
    print(f"  Scaled Amt: {res_a['debug_info']['scaled_TransactionAmt']}")
    print(f"  Raw ANN Prob: {res_a['raw_ann_probability']:.8e}")
    print(f"  Display Prob: {res_a['fraud_prob_display']}")
    print(f"  Risk Score: {res_a['risk_score']} ({res_a['risk_level']})")
    print(f"  Drivers ({res_a['driver_count']}): {[f['feature'] for f in res_a['risk_drivers'][:2]]}")
    print(f"  Reducers ({res_a['reducer_count']}): {[f['feature'] for f in res_a['risk_reducers'][:2]]}")

    # Test B: INR 40,000
    tx_b = {
        'transaction_id': 'TEST-40000',
        'amount': 40000.0,
        'currency': 'INR',
        'transaction_type': 'Purchase',
        'time': '14:30:00',
        'location': 'Local Region, India',
        'device_type': 'Web Browser (Chrome)',
        'new_device': 0,
        'unusual_location': 0,
        'typical_time': 1,
        'amount_ratio': 1.0,
        'customer_average_amount': 40000.0,
        'previous_transaction_count': 0,
        'similar_transaction_count': 0
    }
    res_b = detector.predict_transaction(tx_b)
    print("\nTest B (INR 40,000):")
    print(f"  Scaled Amt: {res_b['debug_info']['scaled_TransactionAmt']}")
    print(f"  Raw ANN Prob: {res_b['raw_ann_probability']:.8e}")
    print(f"  Display Prob: {res_b['fraud_prob_display']}")
    print(f"  Risk Score: {res_b['risk_score']} ({res_b['risk_level']})")
    print(f"  Drivers ({res_b['driver_count']}): {[f['feature'] for f in res_b['risk_drivers'][:2]]}")
    print(f"  Reducers ({res_b['reducer_count']}): {[f['feature'] for f in res_b['risk_reducers'][:2]]}")

    # Test C: INR 500,000
    tx_c = {
        'transaction_id': 'TEST-500000',
        'amount': 500000.0,
        'currency': 'INR',
        'transaction_type': 'Purchase',
        'time': '14:30:00',
        'location': 'Local Region, India',
        'device_type': 'Web Browser (Chrome)',
        'new_device': 0,
        'unusual_location': 0,
        'typical_time': 1,
        'amount_ratio': 1.0,
        'customer_average_amount': 500000.0,
        'previous_transaction_count': 0,
        'similar_transaction_count': 0
    }
    res_c = detector.predict_transaction(tx_c)
    print("\nTest C (INR 500,000):")
    print(f"  Scaled Amt: {res_c['debug_info']['scaled_TransactionAmt']}")
    print(f"  Raw ANN Prob: {res_c['raw_ann_probability']:.8e}")
    print(f"  Display Prob: {res_c['fraud_prob_display']}")
    print(f"  Risk Score: {res_c['risk_score']} ({res_c['risk_level']})")
    print(f"  Drivers ({res_c['driver_count']}): {[f['feature'] for f in res_c['risk_drivers'][:2]]}")
    print(f"  Reducers ({res_c['reducer_count']}): {[f['feature'] for f in res_c['risk_reducers'][:2]]}")

    # Assertions on scaling and risk scores
    assert res_a['debug_info']['scaled_TransactionAmt'] < res_b['debug_info']['scaled_TransactionAmt'], "Scaled amount must scale with input"
    assert res_b['debug_info']['scaled_TransactionAmt'] < res_c['debug_info']['scaled_TransactionAmt'], "Scaled amount must scale with input"
    assert res_a['risk_score'] > 0, "Risk score must be positive"
    assert res_b['risk_score'] > 0, "Risk score must be positive"
    assert res_c['risk_score'] > 0, "Risk score must be positive"
    print("\n[PASS] Scaled amounts and risk scores are valid, distinct, and monotonic.")

    # Test D: Anomalous Transaction
    tx_d = {
        'transaction_id': 'TEST-FRAUD-ANOMALY',
        'amount': 80000.0,
        'currency': 'INR',
        'transaction_type': 'Online Transfer',
        'recipient': 'CryptoGlobal Liquidity Desk',
        'time': '03:14:00',
        'location': 'Lagos, NG (Proxy IP)',
        'device_type': 'Unknown Browser (Linux)',
        'new_device': 1,
        'unusual_location': 1,
        'typical_time': 0,
        'amount_ratio': 28.0,
        'customer_average_amount': 2850.0,
        'previous_transaction_count': 141,
        'similar_transaction_count': 0
    }
    res_d = detector.predict_transaction(tx_d)
    print("\nTest D (Anomalous Transfer INR 80,000, Lagos Proxy, Linux, 3:14 AM):")
    print(f"  Raw ANN Prob: {res_d['raw_ann_probability']:.6f} ({res_d['fraud_prob_display']})")
    print(f"  Risk Score: {res_d['risk_score']} ({res_d['risk_level']})")
    print(f"  Risk Drivers ({res_d['driver_count']}): {[f['feature'] for f in res_d['risk_drivers']]}")
    print(f"  Risk Reducers ({res_d['reducer_count']}): {[f['feature'] for f in res_d['risk_reducers']]}")
    assert res_d['risk_level'] == 'HIGH RISK', "Anomalous transaction must be flagged HIGH RISK"
    assert res_d['driver_count'] > 0, "Anomalous transaction must have risk drivers"
    
    # Audit SHAP values strictly for direction
    for drv in res_d['risk_drivers']:
        assert drv['direction'] == 'Risk', "Risk drivers must push risk higher"
        if 'raw_shap' in drv:
            assert drv['raw_shap'] >= 0, "Risk drivers must have positive raw SHAP"
            
    for red in res_d['risk_reducers']:
        assert red['direction'] == 'Safe', "Risk reducers must reduce model risk"
        if 'raw_shap' in red:
            assert red['raw_shap'] <= 0, "Risk reducers must have negative raw SHAP"
            
    print("[PASS] Dynamic SHAP partition strictly adheres to mathematical sign (phi > 0 vs phi < 0).")

    print("\n================================================================")
    print("STEP 2: Testing Live vs Demo Profile Derivation")
    print("================================================================")
    init_db()

    # Derived features for LIVE-USER with INR 40,000
    derived_live = derive_customer_features(
        customer_id='LIVE-USER',
        amount=40000.0,
        txn_type='Purchase',
        recipient='Local Electronics Store'
    )
    df_live = derived_live['derived_factors']
    print(f"LIVE-USER profile derived:")
    print(f"  Customer: {df_live['customer_name']} (is_demo: {df_live['is_demo_data']})")
    print(f"  Source Label: {df_live['data_source_label']}")
    print(f"  Amount Ratio Label: {df_live['amount_comparison_label']}")
    print(f"  Location: {df_live['derived_location']} (unusual: {df_live['unusual_location']})")
    print(f"  Device: {df_live['derived_device']} (new: {df_live['new_device']})")

    assert df_live['is_demo_data'] is False, "LIVE-USER must not be demo data"
    assert "DEMO DATA" not in df_live['data_source_label'], "Source label must be LIVE"
    assert "Priya" not in df_live['customer_name'], "Live profile must not be Priya Sharma"
    assert "2,850" not in df_live['amount_comparison_label'], "Live profile must not use Priya baseline"
    print("[PASS] LIVE-USER is completely isolated from demo personas.")

    # Derived features for Demo Persona CUST-001
    derived_demo = derive_customer_features(
        customer_id='CUST-001',
        amount=40000.0,
        txn_type='Purchase',
        recipient='Local Electronics Store'
    )
    df_demo = derived_demo['derived_factors']
    print(f"\nCUST-001 (Demo Persona) derived:")
    print(f"  Customer: {df_demo['customer_name']} (is_demo: {df_demo['is_demo_data']})")
    print(f"  Source Label: {df_demo['data_source_label']}")
    print(f"  Amount Ratio Label: {df_demo['amount_comparison_label']}")
    assert df_demo['is_demo_data'] is True, "CUST-001 must be demo data"
    assert "DEMO DATA" in df_demo['data_source_label'], "Source label must be DEMO DATA"
    print("[PASS] Demo profiles retain proper simulation tagging.")

    print("\n================================================================")
    print("ALL AUDIT AND PIPELINE VERIFICATIONS PASSED SUCCESSFULLY!")
    print("================================================================")

if __name__ == '__main__':
    run_tests()
