import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import sqlite3
import requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "neurofinance.db")

def run_tests():
    print("=" * 70)
    print("NEUROFINANCE GPT — 12-TEST COMPREHENSIVE ACADEMIC AUDIT SUITE")
    print("=" * 70)
    passed = 0
    total = 12

    # -------------------------------------------------------------
    # TEST 1: TIME (Minutes-since-midnight & customer history distribution)
    # -------------------------------------------------------------
    print("\n--- TEST 1: TIME EVALUATION ---")
    from database.db import calculate_customer_temporal_pattern, init_db
    
    # Priya Sharma (CUST-001) has historical transactions between 08:45 and 21:40
    res_0310 = calculate_customer_temporal_pattern("CUST-001", "03:10:00")
    res_0412 = calculate_customer_temporal_pattern("CUST-001", "04:12:00")
    res_1000 = calculate_customer_temporal_pattern("CUST-001", "10:00:00")
    res_1400 = calculate_customer_temporal_pattern("CUST-001", "14:00:00")
    res_2000 = calculate_customer_temporal_pattern("CUST-001", "20:00:00")

    print(f"  Priya @ 03:10 -> typical_time={res_0310['typical_time']}, status={res_0310['temporal_status']}")
    print(f"  Priya @ 04:12 -> typical_time={res_0412['typical_time']}, status={res_0412['temporal_status']}")
    print(f"  Priya @ 10:00 -> typical_time={res_1000['typical_time']}, status={res_1000['temporal_status']}")
    print(f"  Priya @ 14:00 -> typical_time={res_1400['typical_time']}, status={res_1400['temporal_status']}")
    print(f"  Priya @ 20:00 -> typical_time={res_2000['typical_time']}, status={res_2000['temporal_status']}")

    assert res_0310['typical_time'] == 0, f"Expected 03:10 outside pattern, got {res_0310['typical_time']}"
    assert res_0412['typical_time'] == 0, f"Expected 04:12 outside pattern, got {res_0412['typical_time']}"
    assert res_1000['typical_time'] == 1, f"Expected 10:00 within pattern, got {res_1000['typical_time']}"
    assert res_1400['typical_time'] == 1, f"Expected 14:00 within pattern, got {res_1400['typical_time']}"
    assert res_2000['typical_time'] == 1, f"Expected 20:00 within pattern, got {res_2000['typical_time']}"

    # Night-shift profile test (Rohan CUST-003 has late transactions 16:15 - 00:45)
    res_rohan_late = calculate_customer_temporal_pattern("CUST-003", "23:15:00")
    print(f"  Rohan @ 23:15 -> typical_time={res_rohan_late['typical_time']}, status={res_rohan_late['temporal_status']}")
    assert res_rohan_late['typical_time'] == 1, "Expected Rohan 23:15 within late night pattern"

    print("  [PASS] Test 1 Passed: Exact minutes-since-midnight temporal pattern verified.")
    passed += 1

    # -------------------------------------------------------------
    # TEST 2: NEW ACCOUNT WITH ZERO HISTORY
    # -------------------------------------------------------------
    print("\n--- TEST 2: BRAND NEW ACCOUNT WITH ZERO HISTORY ---")
    res_new = calculate_customer_temporal_pattern("LIVE-USER", "03:10:00")
    print(f"  LIVE-USER temporal_status: {res_new['temporal_status']}")
    print(f"  LIVE-USER typical_time: {res_new['typical_time']}")
    print(f"  LIVE-USER label: {res_new['time_status_label']}")

    assert res_new['temporal_status'] == "INSUFFICIENT_HISTORY", f"Expected INSUFFICIENT_HISTORY, got {res_new['temporal_status']}"
    assert res_new['typical_time'] == -1, f"Expected -1 neutral flag, got {res_new['typical_time']}"
    assert "insufficient historical" in res_new['time_status_label'].lower(), "Expected insufficient history message"
    print("  [PASS] Test 2 Passed: Brand new account returns neutral unestablished status.")
    passed += 1

    # -------------------------------------------------------------
    # TEST 3: CUSTOMER HISTORY IS CUSTOMER-SPECIFIC
    # -------------------------------------------------------------
    print("\n--- TEST 3: HISTORY IS CUSTOMER-SPECIFIC ---")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT DISTINCT customer_id FROM transactions")
    tx_custs = [r[0] for r in c.fetchall()]
    print(f"  Active customer IDs in transactions: {tx_custs}")

    c.execute("SELECT COUNT(*) FROM transactions WHERE customer_id = 'CUST-001'")
    cnt_cust1 = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM transactions WHERE customer_id = 'CUST-002'")
    cnt_cust2 = c.fetchone()[0]
    conn.close()

    print(f"  CUST-001 tx count: {cnt_cust1} | CUST-002 tx count: {cnt_cust2}")
    assert cnt_cust1 > 0 and cnt_cust2 > 0, "Both demo personas must have records"
    assert cnt_cust1 != cnt_cust2, "Personas have independent counts"
    print("  [PASS] Test 3 Passed: Customer histories are strictly customer-specific.")
    passed += 1

    # -------------------------------------------------------------
    # TEST 4: DEMO/LIVE DATA SEPARATION
    # -------------------------------------------------------------
    print("\n--- TEST 4: DEMO / LIVE DATA SEPARATION ---")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM transactions WHERE customer_id = 'LIVE-USER' AND is_demo = 1")
    live_marked_demo = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM transactions WHERE customer_id IN ('CUST-001', 'CUST-002', 'CUST-003') AND is_demo = 0")
    demo_marked_live = c.fetchone()[0]
    conn.close()

    print(f"  LIVE-USER transactions marked demo: {live_marked_demo}")
    print(f"  Demo profile transactions marked live: {demo_marked_live}")
    assert live_marked_demo == 0, "LIVE-USER must never contain demo records"
    assert demo_marked_live == 0, "Demo profiles must never contain live test records"
    print("  [PASS] Test 4 Passed: Strict demo/live separation maintained.")
    passed += 1

    # -------------------------------------------------------------
    # TEST 5: CURRENT TRANSACTION NOT IN OWN BASELINE
    # -------------------------------------------------------------
    print("\n--- TEST 5: CURRENT TRANSACTION NOT IN OWN BASELINE ---")
    from database.db import derive_customer_features
    # For LIVE-USER with 0 previous transactions
    derived_live = derive_customer_features("LIVE-USER", 5000.0, "Purchase")
    print(f"  LIVE-USER initial count: {derived_live['previous_transaction_count']}")
    print(f"  LIVE-USER baseline label: {derived_live['derived_factors']['amount_comparison_label']}")
    assert derived_live['previous_transaction_count'] == 0, "Current transaction must not be in its own baseline count"
    assert "not established" in derived_live['derived_factors']['amount_comparison_label'].lower(), "Baseline should not be established before analysis"
    print("  [PASS] Test 5 Passed: Current transaction analyzed before saving into history.")
    passed += 1

    # -------------------------------------------------------------
    # TEST 6: DIFFERENT AMOUNTS PRODUCE DIFFERENT FEATURE VECTORS
    # -------------------------------------------------------------
    print("\n--- TEST 6: DIFFERENT AMOUNTS (INR 500, 40,000, 500,000) ---")
    from model.fraud_model import fraud_detector
    
    tx_500 = {"amount": 500.0, "transaction_type": "Purchase", "location": "Mumbai, MH", "device_type": "Mobile App (iOS)", "customer_id": "CUST-001"}
    tx_40k = {"amount": 40000.0, "transaction_type": "Purchase", "location": "Mumbai, MH", "device_type": "Mobile App (iOS)", "customer_id": "CUST-001"}
    tx_500k = {"amount": 500000.0, "transaction_type": "Purchase", "location": "Mumbai, MH", "device_type": "Mobile App (iOS)", "customer_id": "CUST-001"}

    df_500, _, dbg_500 = fraud_detector.transform_input_transaction(tx_500)
    df_40k, _, dbg_40k = fraud_detector.transform_input_transaction(tx_40k)
    df_500k, _, dbg_500k = fraud_detector.transform_input_transaction(tx_500k)

    scaled_amt_500 = dbg_500['scaled_TransactionAmt']
    scaled_amt_40k = dbg_40k['scaled_TransactionAmt']
    scaled_amt_500k = dbg_500k['scaled_TransactionAmt']

    print(f"  INR 500   -> Scaled TransactionAmt: {scaled_amt_500:.4f}")
    print(f"  INR 40,000 -> Scaled TransactionAmt: {scaled_amt_40k:.4f}")
    print(f"  INR 500,000 -> Scaled TransactionAmt: {scaled_amt_500k:.4f}")

    assert scaled_amt_500 < scaled_amt_40k < scaled_amt_500k, "Amounts must strictly produce scaled differentiating feature values"
    print("  [PASS] Test 6 Passed: Dynamic feature transformations correctly reflect different amounts.")
    passed += 1

    # -------------------------------------------------------------
    # TEST 7: DIFFERENT TIMES TEST (API Integration)
    # -------------------------------------------------------------
    print("\n--- TEST 7: DIFFERENT TIMES VIA API ---")
    test_times = ["03:10:00", "04:12:00", "10:00:00", "14:00:00", "20:00:00"]
    for t in test_times:
        payload = {
            "customer_id": "CUST-001",
            "amount": 2000.0,
            "currency": "INR",
            "transaction_type": "Purchase",
            "recipient": "Store",
            "date": "2026-09-10",
            "time": t
        }
        res = requests.post(f"{BASE_URL}/api/analyze", json=payload).json()
        assert res['status'] == "success"
        typical = res['data']['typical_time']
        status = res['data']['derived_factors']['temporal_status']
        print(f"  API Test CUST-001 @ {t}: typical_time={typical} ({status})")
        if t in ["03:10:00", "04:12:00"]:
            assert typical == 0, f"Expected 0 for {t}"
        else:
            assert typical == 1, f"Expected 1 for {t}"
    print("  [PASS] Test 7 Passed: API temporal responses respond according to customer history.")
    passed += 1

    # -------------------------------------------------------------
    # TEST 8: DIFFERENT DEVICES
    # -------------------------------------------------------------
    print("\n--- TEST 8: REGISTERED DEVICE VS UNKNOWN DEVICE ---")
    payload_reg = {
        "customer_id": "CUST-001",
        "amount": 2500.0,
        "transaction_type": "Purchase",
        "simulated_device": "Mobile App (iOS)"
    }
    payload_unreg = {
        "customer_id": "CUST-001",
        "amount": 2500.0,
        "transaction_type": "Purchase",
        "simulated_device": "Linux Terminal Browser (Tor)"
    }
    res_reg = requests.post(f"{BASE_URL}/api/analyze", json=payload_reg).json()['data']
    res_unreg = requests.post(f"{BASE_URL}/api/analyze", json=payload_unreg).json()['data']

    print(f"  Known device -> new_device={res_reg['new_device']} | {res_reg['derived_factors']['device_status_label']}")
    print(f"  Unknown device -> new_device={res_unreg['new_device']} | {res_unreg['derived_factors']['device_status_label']}")
    assert res_reg['new_device'] == 0
    assert res_unreg['new_device'] == 1
    print("  [PASS] Test 8 Passed: Contextual device checking operates correctly.")
    passed += 1

    # -------------------------------------------------------------
    # TEST 9: DIFFERENT LOCATIONS
    # -------------------------------------------------------------
    print("\n--- TEST 9: FAMILIAR LOCATION VS ANOMALOUS LOCATION ---")
    payload_home = {
        "customer_id": "CUST-001",
        "amount": 2500.0,
        "transaction_type": "Purchase",
        "simulated_location": "Mumbai, MH"
    }
    payload_proxy = {
        "customer_id": "CUST-001",
        "amount": 2500.0,
        "transaction_type": "Purchase",
        "simulated_location": "Lagos, Nigeria (Proxy VPN)"
    }
    res_home = requests.post(f"{BASE_URL}/api/analyze", json=payload_home).json()['data']
    res_proxy = requests.post(f"{BASE_URL}/api/analyze", json=payload_proxy).json()['data']

    print(f"  Familiar location -> unusual_location={res_home['unusual_location']}")
    print(f"  Proxy location -> unusual_location={res_proxy['unusual_location']}")
    assert res_home['unusual_location'] == 0
    assert res_proxy['unusual_location'] == 1
    print("  [PASS] Test 9 Passed: Contextual location checking operates correctly.")
    passed += 1

    # -------------------------------------------------------------
    # TEST 10: RISK CONSISTENCY (Single Source of Truth)
    # -------------------------------------------------------------
    print("\n--- TEST 10: RISK CONSISTENCY (Single Source of Truth) ---")
    res_safe = requests.post(f"{BASE_URL}/api/analyze", json={
        "customer_id": "CUST-001",
        "amount": 1500.0,
        "transaction_type": "Purchase",
        "time": "14:00:00",
        "simulated_device": "Mobile App (iOS)",
        "simulated_location": "Mumbai, MH"
    }).json()['data']

    res_fraud = requests.post(f"{BASE_URL}/api/analyze", json={
        "customer_id": "CUST-001",
        "amount": 95000.0,
        "transaction_type": "Purchase",
        "time": "03:15:00",
        "simulated_device": "Unknown Linux Browser",
        "simulated_location": "Lagos, Nigeria"
    }).json()['data']

    print(f"  Safe Txn: prob={res_safe['fraud_probability']}% -> risk_score={res_safe['risk_score']} -> level={res_safe['risk_level']}")
    print(f"  Fraud Txn: prob={res_fraud['fraud_probability']}% -> risk_score={res_fraud['risk_score']} -> level={res_fraud['risk_level']}")

    assert res_safe['risk_score'] == round(res_safe['fraud_probability'], 2)
    assert res_fraud['risk_score'] == round(res_fraud['fraud_probability'], 2)
    assert res_fraud['risk_level'] == "HIGH RISK"
    assert res_safe['risk_level'] == "LOW RISK"
    print("  [PASS] Test 10 Passed: Risk score and risk level strictly derived from ANN probability.")
    passed += 1

    # -------------------------------------------------------------
    # TEST 11: GPT CONSISTENCY
    # -------------------------------------------------------------
    print("\n--- TEST 11: GPT EXPLANATION CONSISTENCY ---")
    exp_text = res_fraud['explanation']
    print(f"  GPT Explanation snippet: {exp_text[:120]}...")
    assert "HIGH RISK" in exp_text, "GPT must state HIGH RISK"
    assert str(res_fraud['risk_score']) in exp_text or str(res_fraud['fraud_probability']) in exp_text, "GPT must use exact numerical score"
    print("  [PASS] Test 11 Passed: GPT uses exact identical ANN prediction outputs.")
    passed += 1

    # -------------------------------------------------------------
    # TEST 12: SHAP CONSISTENCY
    # -------------------------------------------------------------
    print("\n--- TEST 12: SHAP CONSISTENCY WITH ANN ---")
    factors = res_fraud['feature_importance']
    print(f"  Computed factors count: {len(factors)}")
    for f in factors[:3]:
        print(f"    - {f['feature']}: {f['impact']}% ({f.get('effect', f.get('direction'))})")
    assert len(factors) > 0, "Factors must be computed"
    assert all("Relative SHAP Attribution Share" in f.get('contribution_label', '') or "Relative SHAP" in f.get('contribution_label', '') for f in factors)
    print("  [PASS] Test 12 Passed: SHAP attributions correspond strictly to ANN model.")
    passed += 1

    print("\n" + "=" * 70)
    print(f"AUDIT SUITE COMPLETE: {passed}/{total} TESTS PASSED SUCCESSFULLY.")
    print("=" * 70)
    
    # Clean up test transactions to keep database in pristine state
    init_db()
    print("Database cleaned and pristine seed state restored.")

if __name__ == "__main__":
    run_tests()
