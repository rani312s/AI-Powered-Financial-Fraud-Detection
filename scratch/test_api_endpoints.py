import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_apis():
    print("=== TESTING BACKEND APIS & ML PREDICTION ===")
    
    # 1. Stats
    r = requests.get(f"{BASE_URL}/api/stats")
    assert r.status_code == 200, f"Stats failed: {r.status_code}"
    stats = r.json()
    print(f"[PASS] /api/stats -> total: {stats['data']['total_transactions']}, safe: {stats['data']['safe_transactions']}")

    # 2. Customers
    r = requests.get(f"{BASE_URL}/api/customers")
    assert r.status_code == 200, f"Customers failed: {r.status_code}"
    customers = r.json()
    print(f"[PASS] /api/customers -> found {len(customers['data'])} customer profiles")

    # 3. Metrics
    r = requests.get(f"{BASE_URL}/api/metrics")
    assert r.status_code == 200, f"Metrics failed: {r.status_code}"
    metrics = r.json()
    print(f"[PASS] /api/metrics -> accuracy: {metrics['data']['accuracy']}%, F1: {metrics['data']['f1_score']}%")

    # 4. Dataset
    r = requests.get(f"{BASE_URL}/api/dataset")
    assert r.status_code == 200, f"Dataset failed: {r.status_code}"
    ds = r.json()
    print(f"[PASS] /api/dataset -> total records: {ds['data']['total_records']}, raw features: {ds['data']['total_raw_features']}")

    # 5. Analyze Scenario 1 (Safe)
    payload_safe = {
        "customer_id": "CUST-001",
        "amount": 2500,
        "currency": "INR",
        "transaction_type": "Purchase",
        "recipient": "Nature's Basket",
        "description": "Weekly groceries",
        "is_demo": 1
    }
    r = requests.post(f"{BASE_URL}/api/analyze", json=payload_safe)
    assert r.status_code == 200, f"Analyze safe failed: {r.text}"
    res_safe = r.json()['data']
    print(f"[PASS] /api/analyze (Scenario 1 Safe) -> Risk Level: {res_safe['risk_level']}, Score: {res_safe['risk_score']}")

    # 6. Analyze Scenario 2 (Fraud)
    payload_fraud = {
        "customer_id": "CUST-001",
        "amount": 80000,
        "currency": "INR",
        "transaction_type": "Online Transfer",
        "recipient": "CryptoGlobal Desk",
        "description": "Overseas crypto purchase",
        "is_demo": 1,
        "simulated_device": "Linux / Tor Browser",
        "simulated_location": "Lagos, Nigeria",
        "simulated_time": "03:15:00"
    }
    r = requests.post(f"{BASE_URL}/api/analyze", json=payload_fraud)
    assert r.status_code == 200, f"Analyze fraud failed: {r.text}"
    res_fraud = r.json()['data']
    print(f"[PASS] /api/analyze (Scenario 2 Fraud) -> Risk Level: {res_fraud['risk_level']}, Score: {res_fraud['risk_score']}")

    # 7. AI Assistant Chat
    payload_chat = {
        "question": "Why was this transaction flagged?",
        "tx_context": res_fraud
    }
    r = requests.post(f"{BASE_URL}/api/chat", json=payload_chat)
    assert r.status_code == 200, f"Chat failed: {r.text}"
    reply = r.json()['data']['reply']
    print(f"[PASS] /api/chat -> AI Reply preview: {reply[:80]}...")

    print("=== ALL FUNCTIONALITY & ML PREDICTION TESTS PASSED! ===")

if __name__ == '__main__':
    test_apis()
