import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import json
from database.db import init_db, calculate_customer_temporal_pattern, get_db_connection
from app import app

def run_tests():
    print("=" * 70)
    print("RUNNING COMPREHENSIVE TEMPORAL PATTERN VERIFICATION SUITE")
    print("=" * 70)

    # 1. Initialize DB and reset test data
    init_db()

    # 2. Test CUST-001 (Priya Sharma - Daytime/Evening Persona)
    print("\n--- TEST 1: CUST-001 (Priya Sharma - Demo Daytime/Evening Profile) ---")
    expected_priya = {
        '03:10': 0, # Outside
        '04:12': 0, # Outside
        '10:00': 1, # Within
        '15:00': 1, # Within
        '22:00': 1  # Within
    }

    priya_all_passed = True
    for time_str, expected_flag in expected_priya.items():
        res = calculate_customer_temporal_pattern('CUST-001', time_str)
        dbg = res['debug_info']
        passed = (res['typical_time'] == expected_flag)
        if not passed:
            priya_all_passed = False
        status_mark = "PASS" if passed else "FAIL"
        print(f"[{status_mark}] Time {time_str} -> typical_time: {res['typical_time']} (expected: {expected_flag})")
        print(f"       Label: {res['time_status_label']}")
        print(f"       Source: {res['profile_label']}")
        print(f"       Window: {dbg['calculated_normal_window']['window_description']}")
        print(f"       Hour: {dbg['extracted_hour']}, Count: {dbg['historical_transaction_count']}")

    assert priya_all_passed, "Priya Sharma temporal test cases failed!"

    # 3. Test Night-shift Persona (Proves data-driven behavior, Requirement 3)
    print("\n--- TEST 2: Night-Shift Persona (Transacts 01:00 - 04:30 AM) ---")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO customers (customer_id, name, account_number, account_type, balance, home_location, registered_devices, is_demo) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ('CUST-NIGHT', 'Vikram Night-Shift (Demo)', 'ACC-NIGHT-01', 'Salary', 50000.0, 'Pune, MH', '["Phone"]', 1))
    
    # Insert 4 historical transactions at 01:15, 02:30, 03:20, 04:10
    for idx, (t, d) in enumerate([("01:15", "2026-09-01"), ("02:30", "2026-09-02"), ("03:20", "2026-09-03"), ("04:10", "2026-09-04")]):
        cur.execute("""
            INSERT OR REPLACE INTO transactions (
                transaction_id, customer_id, recipient, description, amount, currency, transaction_type,
                date, time, location, device_type, new_device, unusual_location, customer_average_amount,
                previous_transaction_count, similar_transaction_count, previous_fraud_history,
                typical_time, fraud_probability, risk_level, prediction, explanation,
                feature_importance_json, derived_factors_json, is_demo, transaction_timestamp, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"TXN-NIGHT-{idx}", 'CUST-NIGHT', 'Cafe', 'Midnight coffee', 200.0, 'INR', 'Purchase',
            d, t, 'Pune, MH', 'Phone', 0, 0, 200.0, 10, 5, 0, 1, 5.0, 'LOW RISK', 'Safe', '', '[]', '{}', 1, f"{d} {t}:00", f"{d} {t}:00"
        ))
    conn.commit()
    conn.close()

    expected_night = {
        '03:10': 1, # Within night-shift pattern!
        '04:12': 1, # Within night-shift pattern!
        '10:00': 0, # Outside night-shift pattern!
        '15:00': 0, # Outside night-shift pattern!
        '22:00': 0  # Outside night-shift pattern!
    }

    night_all_passed = True
    for time_str, expected_flag in expected_night.items():
        res = calculate_customer_temporal_pattern('CUST-NIGHT', time_str)
        dbg = res['debug_info']
        passed = (res['typical_time'] == expected_flag)
        if not passed:
            night_all_passed = False
        status_mark = "PASS" if passed else "FAIL"
        print(f"[{status_mark}] Night Time {time_str} -> typical_time: {res['typical_time']} (expected: {expected_flag})")
        print(f"       Label: {res['time_status_label']}")
        print(f"       Window: {dbg['calculated_normal_window']['window_description']}")

    assert night_all_passed, "Night-shift temporal test cases failed!"

    # 4. Test Live Profile (LIVE-USER)
    print("\n--- TEST 3: LIVE-USER Profile Label & Logic ---")
    res_live = calculate_customer_temporal_pattern('LIVE-USER', '14:30')
    print(f"LIVE-USER profile label: {res_live['profile_label']}")
    assert res_live['profile_label'] == "Live customer historical pattern", "LIVE-USER must be labeled as Live customer historical pattern"

    # 5. Test Full Flask /api/analyze Endpoint
    print("\n--- TEST 4: Flask API /api/analyze Integration ---")
    client = app.test_client()

    # Test 4a: CUST-001 at 03:10:00
    res_0310 = client.post('/api/analyze', json={
        'customer_id': 'CUST-001',
        'amount': 2500,
        'transaction_type': 'Purchase',
        'recipient': "Nature's Basket",
        'time': '03:10:00',
        'is_demo': 1
    })
    assert res_0310.status_code == 200, f"API error: {res_0310.data}"
    d_0310 = json.loads(res_0310.data)['data']
    assert d_0310['typical_time'] == 0, f"Expected typical_time 0 for 03:10, got {d_0310['typical_time']}"
    assert "Outside customer's usual transaction-time pattern" in d_0310['derived_factors']['time_status_label']
    assert d_0310['derived_factors']['temporal_pattern_source'] == "Demo historical pattern"
    assert 'temporal_analysis' in d_0310['debug_info'], "debug_info must include temporal_analysis"
    assert d_0310['debug_info']['temporal_analysis']['extracted_hour'] == 3
    print("PASS: /api/analyze 03:10 correctly flagged Outside with full debug_info payload.")

    # Test 4b: CUST-001 at 15:00:00
    res_1500 = client.post('/api/analyze', json={
        'customer_id': 'CUST-001',
        'amount': 2500,
        'transaction_type': 'Purchase',
        'recipient': "Nature's Basket",
        'time': '15:00:00',
        'is_demo': 1
    })
    assert res_1500.status_code == 200, f"API error: {res_1500.data}"
    d_1500 = json.loads(res_1500.data)['data']
    assert d_1500['typical_time'] == 1, f"Expected typical_time 1 for 15:00, got {d_1500['typical_time']}"
    assert "Within customer's usual transaction-time pattern" in d_1500['derived_factors']['time_status_label']
    print("PASS: /api/analyze 15:00 correctly confirmed Within customer usual pattern.")

    print("\n" + "=" * 70)
    print("ALL VERIFICATION SUITE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == '__main__':
    run_tests()
