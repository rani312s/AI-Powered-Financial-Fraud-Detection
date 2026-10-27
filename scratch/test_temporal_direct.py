import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
from database.db import calculate_customer_temporal_pattern, init_db

init_db()

test_times = ['03:10', '04:12', '10:00', '15:00', '22:00']
print("=" * 60)
print("TESTING CUST-001 (Priya Sharma - Demo Profile)")
print("=" * 60)
for t in test_times:
    res = calculate_customer_temporal_pattern('CUST-001', t)
    dbg = res['debug_info']
    print(f"Time: {t} -> typical_time: {res['typical_time']} (anomaly: {res['is_anomaly']})")
    print(f"   Label:  {res['time_status_label']}")
    print(f"   Source: {res['profile_label']}")
    print(f"   Window: {dbg['calculated_normal_window']['window_description']}")
    print(f"   Distribution: {dbg['historical_time_distribution']}")
    print("-" * 50)
