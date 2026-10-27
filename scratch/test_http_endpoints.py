import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

# Allow server 2 seconds to initialize
time.sleep(2)

def test_api():
    print("Testing GET /api/customers...")
    r = requests.get(f"{BASE_URL}/api/customers")
    assert r.status_code == 200, f"Failed GET /api/customers: {r.text}"
    custs = r.json()['data']
    live_cust = next((c for c in custs if c['customer_id'] == 'LIVE-USER'), None)
    assert live_cust is not None, "LIVE-USER must be in customer list"
    assert live_cust['is_demo'] == 0, "LIVE-USER is_demo must be 0"
    print(f"  [PASS] Found LIVE-USER in /api/customers: {live_cust['name']}")

    print("\nTesting POST /api/analyze with Live Transaction of INR 40,000...")
    tx_payload = {
        "amount": 40000.0,
        "transaction_type": "Purchase",
        "recipient": "Reliance Digital Electronics",
        "description": "Smart TV Purchase"
    }
    r = requests.post(f"{BASE_URL}/api/analyze", json=tx_payload)
    assert r.status_code == 200, f"Failed POST /api/analyze: {r.text}"
    data = r.json()['data']
    print(f"  Transaction ID: {data['transaction_id']}")
    print(f"  Customer ID: {data['customer_id']}")
    print(f"  Is Demo: {data['is_demo']}")
    print(f"  Raw ANN Prob: {data['raw_ann_probability']}")
    print(f"  Display Prob: {data['fraud_prob_display']}")
    print(f"  Risk Score: {data['risk_score']} ({data['risk_level']})")
    print(f"  Drivers ({data['driver_count']}): {[f['feature'] for f in data['risk_drivers'][:2]]}")
    print(f"  Reducers ({data['reducer_count']}): {[f['feature'] for f in data['risk_reducers'][:2]]}")
    base_lbl = data['derived_factors']['amount_comparison_label'].replace('\u20b9', 'INR ')
    print(f"  Baseline Label: {base_lbl}")
    print(f"  Source Label: {data['derived_factors']['data_source_label']}")

    assert data['customer_id'] == 'LIVE-USER', "Live transaction should default to LIVE-USER"
    assert data['is_demo'] == 0, "Live transaction must have is_demo = 0"
    assert data['derived_factors']['is_demo_data'] is False, "Derived factors must have is_demo_data = False"
    assert "DEMO DATA" not in data['derived_factors']['data_source_label']
    assert data['fraud_prob_display'] != "0%", "Fraud probability display must never be static '0%'"
    assert data['risk_score'] > 0, "Risk score must be positive"
    print("  [PASS] Live INR 40,000 transaction analysis verified successfully!")

    print("\nTesting POST /api/analyze with INR 500...")
    r500 = requests.post(f"{BASE_URL}/api/analyze", json={
        "amount": 500.0,
        "transaction_type": "Purchase",
        "recipient": "Coffee Shop"
    })
    assert r500.status_code == 200
    d500 = r500.json()['data']
    print(f"  Display Prob: {d500['fraud_prob_display']} | Risk: {d500['risk_score']}")

    print("\nTesting POST /api/analyze with INR 500,000...")
    r500k = requests.post(f"{BASE_URL}/api/analyze", json={
        "amount": 500000.0,
        "transaction_type": "Purchase",
        "recipient": "Automobile Dealer"
    })
    assert r500k.status_code == 200
    d500k = r500k.json()['data']
    print(f"  Display Prob: {d500k['fraud_prob_display']} | Risk: {d500k['risk_score']}")

    print("\n================================================================")
    print("ALL HTTP API LIVE TESTS PASSED!")
    print("================================================================")

if __name__ == '__main__':
    test_api()
