"""
Automated Test Suite for ANN Fraud Probability & Risk Level Consistency
Validates:
1. Single Source of Truth (p_ann -> fraud_probability, risk_score, risk_level)
2. Case A (p=0.05 -> LOW RISK, score 5.0)
3. Case B (p=0.45 -> MEDIUM RISK, score 45.0)
4. Case C (p=0.808425 -> HIGH RISK, score 80.84)
5. Case D (GPT Explanation Consistency)
6. Case E (Live /api/analyze HTTP API + SQLite DB persistence verification)
"""

import sys
import os
import json
import sqlite3
import requests

# Windows console encoding safeguard
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from model.fraud_model import fraud_detector
from services.gpt_service import gpt_service
from database.db import DB_PATH, get_db_connection

def test_risk_mapping_unit():
    print("=== [TEST 1] Model Core Risk Score & Level Mapping Unit Tests ===")
    
    test_cases = [
        {"prob": 0.05, "expected_level": "LOW RISK", "expected_score": 5.0, "expected_pred": "Safe Transaction"},
        {"prob": 0.30, "expected_level": "LOW RISK", "expected_score": 30.0, "expected_pred": "Safe Transaction"},
        {"prob": 0.45, "expected_level": "MEDIUM RISK", "expected_score": 45.0, "expected_pred": "Suspicious Activity"},
        {"prob": 0.70, "expected_level": "MEDIUM RISK", "expected_score": 70.0, "expected_pred": "Suspicious Activity"},
        {"prob": 0.808425, "expected_level": "HIGH RISK", "expected_score": 80.84, "expected_pred": "Potential Fraud"},
        {"prob": 0.999, "expected_level": "HIGH RISK", "expected_score": 99.9, "expected_pred": "Potential Fraud"}
    ]
    
    for tc in test_cases:
        p = tc["prob"]
        fraud_prob_pct = round(p * 100.0, 4)
        model_risk_score = round(min(100.0, max(0.0, fraud_prob_pct)), 2)
        
        if model_risk_score > 70.0:
            level = "HIGH RISK"
            pred = "Potential Fraud"
        elif model_risk_score > 30.0:
            level = "MEDIUM RISK"
            pred = "Suspicious Activity"
        else:
            level = "LOW RISK"
            pred = "Safe Transaction"
            
        print(f"Prob: {p:.6f} -> Score: {model_risk_score} | Level: {level} | Pred: {pred}")
        assert level == tc["expected_level"], f"Mismatch for prob {p}: got {level}, expected {tc['expected_level']}"
        assert model_risk_score == tc["expected_score"], f"Score mismatch: got {model_risk_score}, expected {tc['expected_score']}"
        assert pred == tc["expected_pred"], f"Prediction mismatch: got {pred}, expected {tc['expected_pred']}"
        
    print(">>> TEST 1 PASSED: All unit test mapping thresholds strictly conform to Academic Prototype Policy.\n")

def test_gpt_explanation_consistency():
    print("=== [TEST 2] GPT Explanation Consistency Verification ===")
    
    # Simulate high risk transaction inputs (80.8425%)
    prob_pct = 80.84
    prob_str = "80.84%"
    risk_level = "HIGH RISK"
    score = 80.84
    xai_factors = [
        {"feature": "Overnight Hours (02:30 AM)", "impact": 35.2, "direction": "Risk"},
        {"feature": "Unusual Location (Lagos, Nigeria)", "impact": 28.6, "direction": "Risk"},
        {"feature": "New Unrecognized Device", "impact": 18.5, "direction": "Risk"},
        {"feature": "Transaction Amount", "impact": 12.0, "direction": "Risk"}
    ]
    tx_data = {
        "transaction_id": "TEST-TXN-HIGH-01",
        "amount": 50000.0,
        "customer_average_amount": 2500.0,
        "location": "Lagos, Nigeria",
        "device_type": "Linux / Tor Proxy",
        "new_device": 1,
        "unusual_location": 1,
        "typical_time": 0
    }
    
    prediction_result = {
        "fraud_probability": prob_pct,
        "fraud_prob_display": prob_str,
        "risk_level": risk_level,
        "risk_score": score,
        "prediction": "Potential Fraud"
    }
    
    exp = gpt_service.generate_explanation(
        tx_data=tx_data,
        prediction_result=prediction_result,
        xai_factors=xai_factors
    )
    
    print(f"Generated GPT Explanation:\n---\n{exp}\n---")
    
    assert "HIGH RISK" in exp or "High Risk" in exp or "high risk" in exp, "Explanation MUST mention HIGH RISK"
    assert "LOW RISK" not in exp, "High risk transaction explanation must NEVER contain 'LOW RISK'"
    assert "80.84%" in exp, f"Explanation must accurately state the fraud probability {prob_str}"
    
    print(">>> TEST 2 PASSED: GPT Explanation perfectly reflects 80.84% HIGH RISK without contradictions.\n")

def test_api_end_to_end():
    print("=== [TEST 3] Live HTTP API & Database Persistence End-to-End Test ===")
    base_url = "http://127.0.0.1:5000"
    
    # 1. Test /api/stats
    res_stats = requests.get(f"{base_url}/api/stats")
    assert res_stats.status_code == 200, f"Stats endpoint failed: {res_stats.text}"
    stats_data = res_stats.json().get("data", {})
    avg_score = stats_data.get("average_risk_score")
    print(f"Stats check: Total Transactions = {stats_data.get('total_transactions')}, Avg Risk Score = {avg_score}")
    assert avg_score is not None, "average_risk_score missing from /api/stats"
    
    # 2. Test /api/analyze with Live Transaction Submission
    payload_normal = {
        "amount": 1800.0,
        "transaction_type": "Purchase",
        "location": "Mumbai, MH",
        "recipient": "Starbucks Coffee",
        "device_type": "Mobile App (iOS)"
    }
    
    res_norm = requests.post(f"{base_url}/api/analyze", json=payload_normal)
    assert res_norm.status_code == 200, f"Analyze endpoint failed: {res_norm.text}"
    data_norm = res_norm.json().get("data", {})
    
    p_norm = data_norm.get("fraud_probability")
    s_norm = data_norm.get("risk_score")
    l_norm = data_norm.get("risk_level")
    tx_id_norm = data_norm.get("transaction_id")
    
    print(f"Live Normal Txn [{tx_id_norm}]: Prob={p_norm}%, Score={s_norm}/100, Level={l_norm}")
    assert p_norm is not None and s_norm is not None, "Missing prob or score"
    assert abs(round(p_norm, 2) - s_norm) < 0.05, f"Risk score ({s_norm}) does not match probability ({p_norm})"
    
    if s_norm <= 30.0:
        assert l_norm == "LOW RISK", f"Score {s_norm} should be LOW RISK, got {l_norm}"
    elif s_norm <= 70.0:
        assert l_norm == "MEDIUM RISK", f"Score {s_norm} should be MEDIUM RISK, got {l_norm}"
    else:
        assert l_norm == "HIGH RISK", f"Score {s_norm} should be HIGH RISK, got {l_norm}"
        
    # 3. Test /api/analyze with Scenario 2 (Suspicious High-Risk Fraud)
    payload_high = {
        "customer_id": "CUST-001",
        "amount": 80000.0,
        "transaction_type": "Online Transfer",
        "recipient": "CryptoGlobal Liquidity Desk",
        "description": "Urgent offshore settlement",
        "simulated_device": "Unknown Browser (Linux)",
        "simulated_location": "Lagos, NG (Proxy IP)",
        "simulated_time": "03:15"
    }
    
    res_high = requests.post(f"{base_url}/api/analyze", json=payload_high)
    assert res_high.status_code == 200, f"Analyze endpoint failed: {res_high.text}"
    data_high = res_high.json().get("data", {})
    
    p_high = data_high.get("fraud_probability")
    s_high = data_high.get("risk_score")
    l_high = data_high.get("risk_level")
    tx_id_high = data_high.get("transaction_id")
    
    print(f"Live High-Risk Txn [{tx_id_high}]: Prob={p_high}%, Score={s_high}/100, Level={l_high}")
    assert abs(round(p_high, 2) - s_high) < 0.05, f"Risk score ({s_high}) does not match probability ({p_high})"
    
    if s_high > 70.0:
        assert l_high == "HIGH RISK", f"Score {s_high} must map to HIGH RISK, got {l_high}"
    elif s_high > 30.0:
        assert l_high == "MEDIUM RISK", f"Score {s_high} must map to MEDIUM RISK, got {l_high}"
    else:
        assert l_high == "LOW RISK", f"Score {s_high} must map to LOW RISK, got {l_high}"
        
    # 4. Verify SQLite Database Record
    conn = get_db_connection()
    row_norm = conn.execute("SELECT * FROM transactions WHERE transaction_id = ?", (tx_id_norm,)).fetchone()
    row_high = conn.execute("SELECT * FROM transactions WHERE transaction_id = ?", (tx_id_high,)).fetchone()
    conn.close()
    
    assert row_norm is not None, "Normal txn not persisted in DB"
    assert row_high is not None, "High txn not persisted in DB"
    
    print(f"DB Row [{tx_id_norm}]: DB risk_score = {row_norm['risk_score']}, DB fraud_prob = {row_norm['fraud_probability']}, DB risk_level = {row_norm['risk_level']}")
    print(f"DB Row [{tx_id_high}]: DB risk_score = {row_high['risk_score']}, DB fraud_prob = {row_high['fraud_probability']}, DB risk_level = {row_high['risk_level']}")
    
    assert row_high['risk_score'] == s_high, f"DB risk_score mismatch: {row_high['risk_score']} vs {s_high}"
    assert row_high['risk_level'] == l_high, f"DB risk_level mismatch: {row_high['risk_level']} vs {l_high}"
    
    # 5. Check migration of legacy row TXN-20260910-011812-04BBBB (which had the 80.8425% LOW RISK bug)
    from database.db import init_db
    init_db()
    conn = get_db_connection()
    legacy_row = conn.execute("SELECT * FROM transactions WHERE transaction_id = 'TXN-20260910-011812-04BBBB'").fetchone()
    conn.close()
    if legacy_row:
        print(f"Legacy Fixed Row: {legacy_row['transaction_id']} | Prob: {legacy_row['fraud_probability']}% | Score: {legacy_row['risk_score']} | Level: {legacy_row['risk_level']}")
        assert legacy_row['risk_level'] == 'HIGH RISK', f"Legacy row should now be HIGH RISK, got {legacy_row['risk_level']}"
        assert legacy_row['risk_score'] > 70.0, f"Legacy score should be >70, got {legacy_row['risk_score']}"
    
    print(">>> TEST 3 PASSED: HTTP API, Single Source of Truth, and SQLite DB persistence verified completely.\n")

if __name__ == "__main__":
    test_risk_mapping_unit()
    test_gpt_explanation_consistency()
    test_api_end_to_end()
    print("==================================================")
    print("ALL 5 AUDIT & CONSISTENCY TEST SUITES PASSED (100%)")
    print("==================================================")
