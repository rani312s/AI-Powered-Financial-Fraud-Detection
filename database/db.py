import sqlite3
import json
import os
from datetime import datetime, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(__file__), 'neurofinance.db')

CUSTOMER_PERSONAS = [
    {
        "customer_id": "LIVE-USER",
        "name": "Live Transaction Account",
        "account_number": "ACC-LIVE-900128",
        "account_type": "Standard Digital Account",
        "is_demo": 0,
        "balance": 250000.0,
        "home_location": "Local Region, India",
        "registered_devices": ["Web Browser (Chrome)", "Mobile App (Android)", "Mobile App (iOS)"],
        "typical_start_hour": 8,
        "typical_end_hour": 22,
        "prior_fraud_record": 0,
        "baseline_avg_amount": 0.0,
        "profile_summary": "Live Test Account • Dynamic history computed from live test transactions"
    },
    {
        "customer_id": "CUST-001",
        "name": "Priya Sharma (Demo Profile)",
        "account_number": "ACC-9041285512",
        "account_type": "Premium Savings",
        "is_demo": 1,
        "balance": 145200.0,
        "home_location": "Mumbai, MH",
        "registered_devices": ["Mobile App (iOS)", "MacBook Pro (Chrome)", "iPad Air (Safari)"],
        "typical_start_hour": 7,
        "typical_end_hour": 23,
        "prior_fraud_record": 0,
        "baseline_avg_amount": 3200.0,
        "profile_summary": "[DEMO DATA] Salaried Senior Engineer • Regular grocery, rides & utility spending"
    },
    {
        "customer_id": "CUST-002",
        "name": "Aarav Patel (Demo Profile)",
        "account_number": "ACC-7819204431",
        "account_type": "Business Elite Current",
        "is_demo": 1,
        "balance": 1890000.0,
        "home_location": "Bengaluru, KA",
        "registered_devices": ["MacBook Air (Chrome)", "iPad Pro (Safari)", "Mobile App (Android)"],
        "typical_start_hour": 8,
        "typical_end_hour": 22,
        "prior_fraud_record": 0,
        "baseline_avg_amount": 22000.0,
        "profile_summary": "[DEMO DATA] Director / Enterprise Founder • High volume vendor & tuition transfers"
    },
    {
        "customer_id": "CUST-003",
        "name": "Rohan Verma (Demo Profile)",
        "account_number": "ACC-3190482105",
        "account_type": "Student Advantage",
        "is_demo": 1,
        "balance": 24800.0,
        "home_location": "Delhi, DL",
        "registered_devices": ["Android Phone (OnePlus)", "Windows PC (Firefox)"],
        "typical_start_hour": 9,
        "typical_end_hour": 1,
        "prior_fraud_record": 1,
        "baseline_avg_amount": 1400.0,
        "profile_summary": "[DEMO DATA] Graduate Student • Micro payments, food deliveries (Prior phishing flag)"
    }
]

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('PRAGMA journal_mode=WAL;')
    cursor = conn.cursor()
    
    # 1. Customers Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            account_number TEXT NOT NULL,
            account_type TEXT NOT NULL,
            balance REAL DEFAULT 50000.0,
            home_location TEXT NOT NULL,
            registered_devices TEXT NOT NULL,
            typical_start_hour INTEGER DEFAULT 7,
            typical_end_hour INTEGER DEFAULT 23,
            prior_fraud_record INTEGER DEFAULT 0,
            baseline_avg_amount REAL DEFAULT 3000.0,
            profile_summary TEXT,
            is_demo INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Transactions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE NOT NULL,
            customer_id TEXT DEFAULT 'CUST-001',
            recipient TEXT DEFAULT 'General Merchant',
            description TEXT DEFAULT '',
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'INR',
            transaction_type TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            location TEXT NOT NULL,
            device_type TEXT NOT NULL,
            new_device INTEGER NOT NULL,
            unusual_location INTEGER NOT NULL,
            customer_average_amount REAL NOT NULL,
            previous_transaction_count INTEGER NOT NULL,
            similar_transaction_count INTEGER NOT NULL,
            previous_fraud_history INTEGER DEFAULT 0,
            typical_time INTEGER DEFAULT 1,
            temporal_status TEXT DEFAULT '',
            fraud_probability REAL NOT NULL,
            raw_ann_probability REAL DEFAULT 0.0,
            risk_score REAL DEFAULT 0.0,
            risk_level TEXT NOT NULL,
            prediction TEXT NOT NULL,
            explanation TEXT,
            feature_importance_json TEXT,
            derived_factors_json TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Safe column migrations if tables existed previously
    cust_cols = [r[1] for r in cursor.execute('PRAGMA table_info(customers)').fetchall()]
    if 'is_demo' not in cust_cols:
        try:
            cursor.execute('ALTER TABLE customers ADD COLUMN is_demo INTEGER DEFAULT 1')
        except Exception as e:
            print(f"[DB Migration] Notice adding is_demo to customers: {e}")

    existing_cols = [r[1] for r in cursor.execute('PRAGMA table_info(transactions)').fetchall()]
    migration_cols = [
        ('customer_id', 'TEXT DEFAULT "CUST-001"'),
        ('recipient', 'TEXT DEFAULT "General Merchant"'),
        ('description', 'TEXT DEFAULT ""'),
        ('derived_factors_json', 'TEXT DEFAULT "{}"'),
        ('is_demo', 'INTEGER DEFAULT 0'),
        ('transaction_timestamp', 'TEXT DEFAULT ""'),
        ('risk_score', 'REAL DEFAULT 0.0'),
        ('raw_ann_probability', 'REAL DEFAULT 0.0'),
        ('temporal_status', 'TEXT DEFAULT ""')
    ]
    for col_name, col_def in migration_cols:
        if col_name not in existing_cols:
            try:
                cursor.execute(f'ALTER TABLE transactions ADD COLUMN {col_name} {col_def}')
            except Exception as e:
                print(f"[DB Migration] Notice adding {col_name}: {e}")

    # Seed/Update customer personas (ensures LIVE-USER and demo profiles are present)
    seed_customers(cursor)

    # Seed demo records if empty or fewer than 5 records
    cursor.execute('SELECT COUNT(*) as count FROM transactions')
    tx_count = cursor.fetchone()['count']
    if tx_count == 0:
        seed_demo_data(cursor)
    else:
        # Re-align legacy transactions with customer personas
        cursor.execute("UPDATE transactions SET customer_id = 'CUST-002' WHERE transaction_id IN ('TXN-2026-90810', 'TXN-2026-90805') OR (amount >= 50000 AND risk_level = 'LOW RISK')")
        cursor.execute("UPDATE transactions SET customer_id = 'CUST-003' WHERE transaction_id IN ('TXN-2026-90809', 'TXN-2026-90808')")
        # Ensure demo seed records are marked with is_demo = 1
        cursor.execute("UPDATE transactions SET is_demo = 1 WHERE transaction_id LIKE 'TXN-HIST-%' OR transaction_id LIKE 'TXN-2026-908%'")
        # Ensure transaction_timestamp is populated
        cursor.execute("UPDATE transactions SET transaction_timestamp = date || ' ' || time WHERE transaction_timestamp IS NULL OR transaction_timestamp = ''")
        # Ensure risk_score is aligned with fraud_probability for all legacy records
        cursor.execute("UPDATE transactions SET risk_score = fraud_probability WHERE risk_score IS NULL OR risk_score = 0.0")
        # Ensure risk_level strictly matches academic prototype policy for legacy records
        cursor.execute("UPDATE transactions SET risk_level = 'HIGH RISK' WHERE fraud_probability > 70.0 AND risk_level != 'HIGH RISK'")
        cursor.execute("UPDATE transactions SET risk_level = 'MEDIUM RISK' WHERE fraud_probability > 30.0 AND fraud_probability <= 70.0 AND risk_level != 'MEDIUM RISK'")
        
    # Ensure realistic customer background histories are up to date with realistic diurnal distributions
    seed_realistic_customer_histories(cursor, datetime.now())
    # Clean up test rows for LIVE-USER so new account baseline starts cleanly
    cursor.execute("DELETE FROM transactions WHERE customer_id = 'LIVE-USER'")
    # Clean up non-seed test rows for demo personas to preserve authentic historical diurnal distribution
    cursor.execute("DELETE FROM transactions WHERE customer_id IN ('CUST-001', 'CUST-002', 'CUST-003') AND transaction_id NOT LIKE 'TXN-HIST-%' AND transaction_id NOT LIKE 'TXN-2026-908%'")

    conn.commit()
    conn.close()

def seed_customers(cursor):
    for c in CUSTOMER_PERSONAS:
        cursor.execute('''
            INSERT OR REPLACE INTO customers (
                customer_id, name, account_number, account_type, balance,
                home_location, registered_devices, typical_start_hour,
                typical_end_hour, prior_fraud_record, baseline_avg_amount, profile_summary, is_demo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            c["customer_id"], c["name"], c["account_number"], c["account_type"],
            c["balance"], c["home_location"], json.dumps(c["registered_devices"]),
            c["typical_start_hour"], c["typical_end_hour"], c["prior_fraud_record"],
            c["baseline_avg_amount"], c["profile_summary"], c.get("is_demo", 1)
        ))

def seed_demo_data(cursor):
    """Seed realistic initial transaction history with customer associations."""
    now = datetime.now()
    
    # Primary Showcase Transactions
    primary_records = [
        {
            "transaction_id": "TXN-2026-90812",
            "customer_id": "CUST-001",
            "recipient": "Nature's Basket",
            "description": "Weekly organic groceries & dairy",
            "amount": 2500.0,
            "currency": "INR",
            "transaction_type": "Purchase",
            "date": (now - timedelta(days=0, hours=1)).strftime("%Y-%m-%d"),
            "time": "14:25",
            "location": "Mumbai, MH",
            "device_type": "Mobile App (iOS)",
            "new_device": 0,
            "unusual_location": 0,
            "customer_average_amount": 2850.0,
            "previous_transaction_count": 142,
            "similar_transaction_count": 38,
            "previous_fraud_history": 0,
            "typical_time": 1,
            "fraud_probability": 8.5,
            "risk_level": "LOW RISK",
            "prediction": "Safe Transaction",
            "explanation": "Transaction details closely match customer Priya Sharma's historical patterns. The transaction amount of ₹2,500 aligns with her typical average of ₹2,850, performed from a verified daily mobile device at a normal time and familiar Mumbai location.",
            "feature_importance_json": json.dumps([
                {"feature": "Known Device Verification", "impact": 22.4, "direction": "Safe"},
                {"feature": "Familiar Geographic Location", "impact": 18.1, "direction": "Safe"},
                {"feature": "Consistent Transaction Time", "impact": 14.3, "direction": "Safe"},
                {"feature": "Amount relative to average", "impact": 5.2, "direction": "Safe"},
                {"feature": "High Historical Count", "impact": 11.5, "direction": "Safe"}
            ]),
            "derived_factors_json": json.dumps({
                "customer_name": "Priya Sharma",
                "derived_device": "Mobile App (iOS)",
                "new_device": 0,
                "device_status_label": "Verified Registered Device",
                "derived_location": "Mumbai, MH",
                "unusual_location": 0,
                "location_status_label": "Verified Primary Region (Mumbai, MH)",
                "derived_time": "14:25",
                "typical_time": 1,
                "time_status_label": "Normal Active Hours (07:00 - 23:00)",
                "customer_average_amount": 2850.0,
                "amount_ratio": 0.88,
                "amount_comparison_label": "0.88x of historical customer baseline (₹2,850.00)",
                "previous_transaction_count": 142,
                "similar_transaction_count": 38,
                "previous_fraud_history": 0,
                "fraud_history_label": "Clean Account History (No Prior Fraud)"
            })
        },
        {
            "transaction_id": "TXN-2026-90811",
            "customer_id": "CUST-001",
            "recipient": "CryptoGlobal Liquidity Desk",
            "description": "Urgent offshore wallet transfer",
            "amount": 80000.0,
            "currency": "INR",
            "transaction_type": "Online Transfer",
            "date": (now - timedelta(days=0, hours=3)).strftime("%Y-%m-%d"),
            "time": "03:14",
            "location": "Lagos, NG (Proxy IP)",
            "device_type": "Unknown Browser (Linux)",
            "new_device": 1,
            "unusual_location": 1,
            "customer_average_amount": 2850.0,
            "previous_transaction_count": 141,
            "similar_transaction_count": 0,
            "previous_fraud_history": 0,
            "typical_time": 0,
            "fraud_probability": 88.4,
            "risk_level": "HIGH RISK",
            "prediction": "Potential Fraud",
            "explanation": "Critical fraud probability flagged (88.4%). The transfer occurred at an abnormal overnight hour (03:14 AM) from a brand new unrecognized Linux device in an anomalous overseas IP (Lagos, Nigeria). The transfer amount of ₹80,000 is 28x higher than the customer's historical average of ₹2,850.",
            "feature_importance_json": json.dumps([
                {"feature": "New Device Detection", "impact": 32.5, "direction": "Risk"},
                {"feature": "Unusual Location Anomalies", "impact": 28.1, "direction": "Risk"},
                {"feature": "Unusual Time of Day (03:14 AM)", "impact": 18.6, "direction": "Risk"},
                {"feature": "High Amount vs Average (28x)", "impact": 14.2, "direction": "Risk"},
                {"feature": "Zero Similar Historical Transfers", "impact": 6.6, "direction": "Risk"}
            ]),
            "derived_factors_json": json.dumps({
                "customer_name": "Priya Sharma",
                "derived_device": "Unknown Browser (Linux)",
                "new_device": 1,
                "device_status_label": "Unrecognized / New Device (⚠️ Flagged)",
                "derived_location": "Lagos, NG (Proxy IP)",
                "unusual_location": 1,
                "location_status_label": "Anomalous / Foreign Location (Lagos, NG) (⚠️ Flagged)",
                "derived_time": "03:14",
                "typical_time": 0,
                "time_status_label": "Unusual Overnight Hours (03:14) (⚠️ Flagged)",
                "customer_average_amount": 2850.0,
                "amount_ratio": 28.07,
                "amount_comparison_label": "28.1x of historical customer baseline (₹2,850.00)",
                "previous_transaction_count": 141,
                "similar_transaction_count": 0,
                "previous_fraud_history": 0,
                "fraud_history_label": "Clean Account History (No Prior Fraud)"
            })
        },
        {
            "transaction_id": "TXN-2026-90810",
            "customer_id": "CUST-002",
            "recipient": "Manipal University Fee Portal",
            "description": "Executive Education Semester Fee",
            "amount": 100000.0,
            "currency": "INR",
            "transaction_type": "Payment",
            "date": (now - timedelta(days=0, hours=6)).strftime("%Y-%m-%d"),
            "time": "11:45",
            "location": "Bengaluru, KA",
            "device_type": "MacBook Air (Chrome)",
            "new_device": 0,
            "unusual_location": 0,
            "customer_average_amount": 22500.0,
            "previous_transaction_count": 89,
            "similar_transaction_count": 14,
            "previous_fraud_history": 0,
            "typical_time": 1,
            "fraud_probability": 24.2,
            "risk_level": "LOW RISK",
            "prediction": "Legitimate High-Value Transaction",
            "explanation": "While this transaction has a high value of ₹1,00,000, multi-modal contextual factors confirm low risk. Aarav Patel performed the transfer on his registered MacBook, at a normal business hour (11:45 AM), from his primary Bengaluru location, and has a history of prior tuition and vendor payments.",
            "feature_importance_json": json.dumps([
                {"feature": "Registered Trusted Device", "impact": -25.0, "direction": "Safe"},
                {"feature": "Primary Location Verified", "impact": -20.4, "direction": "Safe"},
                {"feature": "Prior Similar High Payments", "impact": -15.2, "direction": "Safe"},
                {"feature": "High Transaction Amount", "impact": 18.5, "direction": "Risk"},
                {"feature": "Normal Business Hours", "impact": -12.1, "direction": "Safe"}
            ]),
            "derived_factors_json": json.dumps({
                "customer_name": "Aarav Patel",
                "derived_device": "MacBook Air (Chrome)",
                "new_device": 0,
                "device_status_label": "Verified Registered Device",
                "derived_location": "Bengaluru, KA",
                "unusual_location": 0,
                "location_status_label": "Verified Primary Region (Bengaluru, KA)",
                "derived_time": "11:45",
                "typical_time": 1,
                "time_status_label": "Normal Active Hours (08:00 - 22:00)",
                "customer_average_amount": 22500.0,
                "amount_ratio": 4.44,
                "amount_comparison_label": "4.44x of historical customer baseline (₹22,500.00)",
                "previous_transaction_count": 89,
                "similar_transaction_count": 14,
                "previous_fraud_history": 0,
                "fraud_history_label": "Clean Account History (No Prior Fraud)"
            })
        },
        {
            "transaction_id": "TXN-2026-90809",
            "customer_id": "CUST-003",
            "recipient": "TechMart Electronics",
            "description": "Gaming monitor & accessories",
            "amount": 35000.0,
            "currency": "INR",
            "transaction_type": "Transfer",
            "date": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
            "time": "19:50",
            "location": "Delhi, DL",
            "device_type": "Windows PC (Edge)",
            "new_device": 1,
            "unusual_location": 0,
            "customer_average_amount": 1450.0,
            "previous_transaction_count": 45,
            "similar_transaction_count": 2,
            "previous_fraud_history": 1,
            "typical_time": 1,
            "fraud_probability": 52.8,
            "risk_level": "MEDIUM RISK",
            "prediction": "Suspicious Activity",
            "explanation": "Medium risk score (52.8%). Initiated from a new browser session for ₹35,000, which is significantly higher than customer Rohan's normal ₹1,450 spending level. Conducted within Delhi during normal evening hours, but account has prior security warnings.",
            "feature_importance_json": json.dumps([
                {"feature": "New Unrecognized Device", "impact": 28.0, "direction": "Risk"},
                {"feature": "Elevated Transfer Amount", "impact": 22.5, "direction": "Risk"},
                {"feature": "Home Location Match", "impact": -18.2, "direction": "Safe"},
                {"feature": "Normal Evening Hour", "impact": -12.4, "direction": "Safe"},
                {"feature": "Prior Account Alert Record", "impact": 15.0, "direction": "Risk"}
            ]),
            "derived_factors_json": json.dumps({
                "customer_name": "Rohan Verma",
                "derived_device": "Windows PC (Edge)",
                "new_device": 1,
                "device_status_label": "Unrecognized / New Device (⚠️ Flagged)",
                "derived_location": "Delhi, DL",
                "unusual_location": 0,
                "location_status_label": "Verified Primary Region (Delhi, DL)",
                "derived_time": "19:50",
                "typical_time": 1,
                "time_status_label": "Normal Active Hours (09:00 - 01:00)",
                "customer_average_amount": 1450.0,
                "amount_ratio": 24.1,
                "amount_comparison_label": "24.1x of historical customer baseline (₹1,450.00)",
                "previous_transaction_count": 45,
                "similar_transaction_count": 2,
                "previous_fraud_history": 1,
                "fraud_history_label": "Prior Fraud Alerts on Record (⚠️ Flagged)"
            })
        },
        {
            "transaction_id": "TXN-2026-90808",
            "customer_id": "CUST-003",
            "recipient": "ATM Cash Terminal #402",
            "description": "Late night ATM cash withdrawal",
            "amount": 125000.0,
            "currency": "INR",
            "transaction_type": "Withdrawal",
            "date": (now - timedelta(days=1, hours=4)).strftime("%Y-%m-%d"),
            "time": "02:40",
            "location": "Kolkata, WB",
            "device_type": "ATM Terminal #402",
            "new_device": 1,
            "unusual_location": 1,
            "customer_average_amount": 1450.0,
            "previous_transaction_count": 44,
            "similar_transaction_count": 0,
            "previous_fraud_history": 1,
            "typical_time": 0,
            "fraud_probability": 94.1,
            "risk_level": "HIGH RISK",
            "prediction": "Potential Fraud",
            "explanation": "Critical fraud risk flagged (94.1%). Midnight ATM cash withdrawal of ₹1,25,000 from an unverified terminal in Kolkata, far from Delhi home region. Customer account has prior fraud record.",
            "feature_importance_json": json.dumps([
                {"feature": "Prior Account Fraud History", "impact": 35.0, "direction": "Risk"},
                {"feature": "Unusual Location (Kolkata)", "impact": 25.4, "direction": "Risk"},
                {"feature": "Unusual Overnight Hours (02:40 AM)", "impact": 19.8, "direction": "Risk"},
                {"feature": "Extreme Amount vs Average (86x)", "impact": 15.0, "direction": "Risk"}
            ]),
            "derived_factors_json": json.dumps({
                "customer_name": "Rohan Verma",
                "derived_device": "ATM Terminal #402",
                "new_device": 1,
                "device_status_label": "Unrecognized Terminal (⚠️ Flagged)",
                "derived_location": "Kolkata, WB",
                "unusual_location": 1,
                "location_status_label": "Anomalous Out-of-State Location (⚠️ Flagged)",
                "derived_time": "02:40",
                "typical_time": 0,
                "time_status_label": "Unusual Overnight Hours (⚠️ Flagged)",
                "customer_average_amount": 1450.0,
                "amount_ratio": 86.2,
                "amount_comparison_label": "86.2x of historical customer baseline (₹1,450.00)",
                "previous_transaction_count": 44,
                "similar_transaction_count": 0,
                "previous_fraud_history": 1,
                "fraud_history_label": "Prior Fraud Alerts on Record (⚠️ Flagged)"
            })
        }
    ]

    for item in primary_records:
        cursor.execute('''
            INSERT OR REPLACE INTO transactions (
                transaction_id, customer_id, recipient, description, amount, currency, transaction_type,
                date, time, location, device_type, new_device, unusual_location, customer_average_amount,
                previous_transaction_count, similar_transaction_count, previous_fraud_history,
                typical_time, fraud_probability, risk_level, prediction, explanation,
                feature_importance_json, derived_factors_json, is_demo, transaction_timestamp, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item["transaction_id"], item["customer_id"], item["recipient"], item["description"],
            item["amount"], item["currency"], item["transaction_type"], item["date"], item["time"],
            item["location"], item["device_type"], item["new_device"], item["unusual_location"],
            item["customer_average_amount"], item["previous_transaction_count"],
            item["similar_transaction_count"], item["previous_fraud_history"], item["typical_time"],
            item["fraud_probability"], item["risk_level"], item["prediction"], item["explanation"],
            item["feature_importance_json"], item["derived_factors_json"],
            1, item["date"] + " " + item["time"] + ":00",
            item["date"] + " " + item["time"] + ":00"
        ))

    # Seed background realistic transaction history for dynamic SQL calculations
    seed_realistic_customer_histories(cursor, now)

def seed_realistic_customer_histories(cursor, now):
    """Adds realistic past transactions so SQL AVG, COUNT, and Temporal Pattern queries reflect true customer behaviors."""
    # CUST-001: Priya Sharma (Routine daytime and evening purchases, groceries, utilities in Mumbai)
    priya_merchants = [
        ("Uber Rides", "Office commute taxi", "Payment", 480.0, "08:45"),
        ("Reliance Fresh", "Supermarket items", "Purchase", 3200.0, "10:15"),
        ("Apollo Pharmacy", "Prescription medicines", "Purchase", 850.0, "12:30"),
        ("Zomato Online", "Weekend lunch", "Purchase", 950.0, "13:30"),
        ("Nature's Basket", "Weekly organic groceries", "Purchase", 2500.0, "14:25"),
        ("Decathlon Mumbai", "Sporting goods", "Purchase", 2800.0, "15:45"),
        ("Flipkart", "Kitchen appliances", "Purchase", 4100.0, "17:20"),
        ("Swiggy Food", "Dinner delivery", "Purchase", 650.0, "19:30"),
        ("Amazon India", "Electronics & Books", "Purchase", 1850.0, "20:50"),
        ("Tata Power", "Residential electricity", "Payment", 2400.0, "21:40"),
        ("Airtel Broadband", "Monthly fiber connection", "Payment", 1199.0, "22:15")
    ]
    for idx, (merchant, desc, t_type, amt, h_time) in enumerate(priya_merchants):
        t_date = (now - timedelta(days=idx * 2 + 3)).strftime("%Y-%m-%d")
        tx_id = f"TXN-HIST-P{idx+101}"
        cursor.execute('''
            INSERT OR REPLACE INTO transactions (
                transaction_id, customer_id, recipient, description, amount, currency, transaction_type,
                date, time, location, device_type, new_device, unusual_location, customer_average_amount,
                previous_transaction_count, similar_transaction_count, previous_fraud_history,
                typical_time, fraud_probability, risk_level, prediction, explanation,
                feature_importance_json, derived_factors_json, is_demo, transaction_timestamp, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tx_id, "CUST-001", merchant, desc, amt, "INR", t_type, t_date, h_time, "Mumbai, MH",
            "Mobile App (iOS)", 0, 0, 2850.0, 100 + idx, 20 + idx, 0, 1, 5.0, "LOW RISK",
            "Safe Transaction", "Normal recurring spending pattern.", "[]", "{}", 1, f"{t_date} {h_time}:00", f"{t_date} {h_time}:00"
        ))

    # CUST-002: Aarav Patel (High-value business payments, tuition, cloud servers in Bengaluru: Workday hours)
    aarav_merchants = [
        ("Lufthansa Airlines", "Business conference flights", "Payment", 55000.0, "09:15"),
        ("Dell India Enterprise", "Workstation upgrades", "Payment", 85000.0, "10:30"),
        ("OfficeSupplies Co", "Printer paper and ink", "Purchase", 8200.0, "11:15"),
        ("Starbucks Indiranagar", "Client meeting coffee", "Purchase", 1850.0, "11:45"),
        ("Manipal University Fee Portal", "Application & term deposit", "Payment", 65000.0, "13:15"),
        ("WeWork Bengaluru", "Coworking membership", "Payment", 18000.0, "14:30"),
        ("Amazon Web Services", "Cloud hosting invoice", "Payment", 32000.0, "16:00"),
        ("Prestige Office Lease", "Commercial rent transfer", "Online Transfer", 45000.0, "17:30")
    ]
    for idx, (merchant, desc, t_type, amt, h_time) in enumerate(aarav_merchants):
        t_date = (now - timedelta(days=idx * 3 + 4)).strftime("%Y-%m-%d")
        tx_id = f"TXN-HIST-A{idx+201}"
        cursor.execute('''
            INSERT OR REPLACE INTO transactions (
                transaction_id, customer_id, recipient, description, amount, currency, transaction_type,
                date, time, location, device_type, new_device, unusual_location, customer_average_amount,
                previous_transaction_count, similar_transaction_count, previous_fraud_history,
                typical_time, fraud_probability, risk_level, prediction, explanation,
                feature_importance_json, derived_factors_json, is_demo, transaction_timestamp, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tx_id, "CUST-002", merchant, desc, amt, "INR", t_type, t_date, h_time, "Bengaluru, KA",
            "MacBook Air (Chrome)", 0, 0, 22500.0, 70 + idx, 10 + idx, 0, 1, 12.0, "LOW RISK",
            "Safe Transaction", "Verified recurring business expense.", "[]", "{}", 1, f"{t_date} {h_time}:00", f"{t_date} {h_time}:00"
        ))

    # CUST-003: Rohan Verma (Student evening & late night micro-transfers in Delhi)
    rohan_merchants = [
        ("Campus Canteen", "Lunch & refreshments", "Purchase", 180.0, "16:15"),
        ("Delhi Metro Rail", "Metro smart card recharge", "Payment", 500.0, "18:30"),
        ("Oxford Book Store", "Semester textbooks", "Purchase", 1450.0, "19:45"),
        ("TechMart Electronics", "Gaming monitor & accessories", "Transfer", 35000.0, "20:30"),
        ("Blinkit Quick Delivery", "Snacks and stationery", "Purchase", 420.0, "22:00"),
        ("Netflix India", "Student streaming plan", "Payment", 499.0, "23:15"),
        ("Zomato Delivery", "Late night study snacks", "Purchase", 380.0, "00:45")
    ]
    for idx, (merchant, desc, t_type, amt, h_time) in enumerate(rohan_merchants):
        t_date = (now - timedelta(days=idx * 2 + 2)).strftime("%Y-%m-%d")
        tx_id = f"TXN-HIST-R{idx+301}"
        cursor.execute('''
            INSERT OR REPLACE INTO transactions (
                transaction_id, customer_id, recipient, description, amount, currency, transaction_type,
                date, time, location, device_type, new_device, unusual_location, customer_average_amount,
                previous_transaction_count, similar_transaction_count, previous_fraud_history,
                typical_time, fraud_probability, risk_level, prediction, explanation,
                feature_importance_json, derived_factors_json, is_demo, transaction_timestamp, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tx_id, "CUST-003", merchant, desc, amt, "INR", t_type, t_date, h_time, "Delhi, DL",
            "Android Phone (OnePlus)", 0, 0, 1450.0, 35 + idx, 5 + idx, 1, 1, 15.0, "LOW RISK",
            "Safe Transaction", "Routine student micro-expense.", "[]", "{}", 1, f"{t_date} {h_time}:00", f"{t_date} {h_time}:00"
        ))

def get_all_customers():
    """Retrieve all customer profiles with parsed registered devices."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers ORDER BY customer_id ASC")
    rows = cursor.fetchall()
    conn.close()
    
    customers = []
    for r in rows:
        c = dict(r)
        try:
            c["registered_devices"] = json.loads(c.get("registered_devices", "[]"))
        except Exception:
            c["registered_devices"] = []
        customers.append(c)
    return customers

def get_customer_profile(customer_id):
    """Retrieve detailed customer profile by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    c = dict(row)
    try:
        c["registered_devices"] = json.loads(c.get("registered_devices", "[]"))
    except Exception:
        c["registered_devices"] = []
    return c

def calculate_customer_temporal_pattern(customer_id, new_time_str, new_date_str=None, cursor=None):
    """
    Data-driven temporal pattern analyzer based on actual customer historical transactions.
    Compares the new transaction time (in minutes since midnight, 0–1439) against the customer's
    actual historical transaction-time distribution rather than using any generic hardcoded bank operating window.
    
    Returns a dictionary containing:
    - typical_time: 1 (Within normal pattern), 0 (Outside normal pattern), or -1 (Insufficient history)
    - temporal_status: "WITHIN_PATTERN", "OUTSIDE_PATTERN", or "INSUFFICIENT_HISTORY"
    - is_anomaly: bool
    - time_status_label: user-facing descriptive label
    - profile_label: 'Demo historical pattern' or 'Live customer historical pattern'
    - window_description: human-readable active window string
    - debug_info: detailed audit payload
    """
    need_close = False
    if cursor is None:
        conn = get_db_connection()
        cursor = conn.cursor()
        need_close = True

    try:
        # 1. Parse new transaction time into minutes since midnight
        time_parts = str(new_time_str).strip().split(":")
        new_hour = int(time_parts[0]) if len(time_parts) > 0 else 12
        new_minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        new_second = int(time_parts[2]) if len(time_parts) > 2 else 0
    except Exception:
        new_hour = 12
        new_minute = 0
        new_second = 0

    new_minutes_since_midnight = (new_hour * 60 + new_minute) % 1440

    # 2. Check profile type to label source transparently
    cursor.execute("SELECT customer_id, name, is_demo FROM customers WHERE customer_id = ?", (customer_id,))
    cust_row = cursor.fetchone()
    is_demo_profile = bool(cust_row["is_demo"]) if cust_row else (customer_id != "LIVE-USER")
    profile_label = "Demo historical pattern" if is_demo_profile else "Live customer historical pattern"

    # 3. Fetch legitimate historical transaction records for this specific customer only
    # Prior completed historical transactions (excluding atypical attacks)
    cursor.execute("""
        SELECT time, date
        FROM transactions
        WHERE customer_id = ? AND (typical_time != 0 OR typical_time IS NULL)
        ORDER BY id ASC
    """, (customer_id,))
    rows = cursor.fetchall()

    if need_close:
        conn.close()

    hist_minutes = []
    hist_hours = []
    for r in rows:
        t_str = str(r["time"]).strip()
        try:
            parts = [int(p) for p in t_str.split(":")[:2]]
            h = parts[0]
            m = parts[1] if len(parts) > 1 else 0
            hist_hours.append(h)
            hist_minutes.append((h * 60 + m) % 1440)
        except Exception:
            pass

    hist_count = len(hist_minutes)

    # 4. Statistical analysis in minutes since midnight
    if hist_count < 2:
        # Brand new account or unestablished baseline
        # Scientifically neutral: neither a risk driver nor a risk-reducing feature
        typical_time = -1
        temporal_status = "INSUFFICIENT_HISTORY"
        is_anomaly = False
        tolerance_mins = 60
        spans_midnight = False
        window_start_min = new_minutes_since_midnight
        window_end_min = new_minutes_since_midnight
        hour_counts = {hist_hours[0]: 1} if hist_hours else {}
        hour_freqs = {hist_hours[0]: 100.0} if hist_hours else {}
        window_desc = "Temporal pattern not established — insufficient historical transactions"
        time_status_label = f"{new_time_str} — Temporal pattern not established — insufficient historical transactions"
    else:
        hour_counts = {}
        for h in hist_hours:
            hour_counts[h] = hour_counts.get(h, 0) + 1
        hour_freqs = {h: round((count / hist_count) * 100.0, 1) for h, count in hour_counts.items()}

        unique_mins = sorted(list(set(hist_minutes)))
        k = len(unique_mins)

        # 5. Circular 1440-minute gap analysis to identify customer's normal active window vs inactive sleep period
        if k == 1:
            # Single distinct historical time point
            active_start = unique_mins[0]
            active_end = unique_mins[0]
        else:
            gaps = []
            for i in range(k):
                m_curr = unique_mins[i]
                m_next = unique_mins[(i + 1) % k]
                gap_len = (m_next - m_curr) % 1440
                gaps.append((gap_len, m_curr, m_next))

            # Maximum gap on the circular 1440-min ring represents customer's typical sleep/inactive interval
            max_gap, inactive_start, inactive_end = max(gaps, key=lambda x: x[0])
            active_start = inactive_end
            active_end = inactive_start

        # Apply configurable tolerance buffer (60 minutes on each boundary)
        tolerance_mins = 60
        window_start_min = (active_start - tolerance_mins) % 1440
        window_end_min = (active_end + tolerance_mins) % 1440

        spans_midnight = (window_start_min > window_end_min)

        # 6. Check if new transaction minute falls within customer's normal pattern window
        if not spans_midnight:
            is_typical_time = (window_start_min <= new_minutes_since_midnight <= window_end_min)
        else:
            is_typical_time = (new_minutes_since_midnight >= window_start_min or new_minutes_since_midnight <= window_end_min)

        typical_time = 1 if is_typical_time else 0
        is_anomaly = (typical_time == 0)
        temporal_status = "WITHIN_PATTERN" if is_typical_time else "OUTSIDE_PATTERN"

        start_str = f"{window_start_min // 60:02d}:{window_start_min % 60:02d}"
        end_str = f"{window_end_min // 60:02d}:{window_end_min % 60:02d}"
        active_s_str = f"{active_start // 60:02d}:{active_start % 60:02d}"
        active_e_str = f"{active_end // 60:02d}:{active_end % 60:02d}"

        window_desc = f"{start_str} – {end_str} (Active span: {active_s_str} – {active_e_str} with ±{tolerance_mins}m tolerance)"

        time_status_label = (
            f"{new_time_str} — Within customer's usual transaction-time pattern"
            if typical_time == 1
            else f"{new_time_str} — Outside customer's usual transaction-time pattern (Flagged Risk)"
        )

    # 7. Comprehensive debug instrumentation for verification
    tx_timestamp = f"{new_date_str or ''} {new_time_str}".strip()
    debug_info = {
        "new_transaction_timestamp": tx_timestamp,
        "extracted_hour": new_hour,
        "extracted_minute": new_minute,
        "extracted_second": new_second,
        "new_minutes_since_midnight": new_minutes_since_midnight,
        "temporal_status": temporal_status,
        "historical_transaction_count": hist_count,
        "historical_time_distribution": hour_counts,
        "historical_hour_frequencies": hour_freqs,
        "calculated_normal_window": {
            "window_start_minute": window_start_min,
            "window_end_minute": window_end_min,
            "window_description": window_desc,
            "tolerance_minutes": tolerance_mins,
            "spans_midnight": spans_midnight
        },
        "final_temporal_anomaly_result": is_anomaly,
        "typical_time": typical_time,
        "profile_label": profile_label,
        "rule_type": "Rule-based contextual signal (Not an ANN model input feature)"
    }

    return {
        "typical_time": typical_time,
        "temporal_status": temporal_status,
        "is_anomaly": is_anomaly,
        "time_status_label": time_status_label,
        "profile_label": profile_label,
        "window_description": window_desc,
        "debug_info": debug_info
    }

def derive_customer_features(customer_id, amount, txn_type, recipient="",
                             simulated_device=None, simulated_location=None, simulated_time=None,
                             custom_date=None, custom_time=None):
    """
    Automatically derives behavioral and contextual ML features from:
    1. Customer profile & registered device / home region registry.
    2. Real-time SQL aggregation of historical transactions (AVG amount, total count, similar frequency).
       History strictly scoped to this customer (WHERE customer_id = ?). Current txn analyzed BEFORE saving.
    3. Environmental context (device fingerprinting, geolocation check, data-driven temporal check).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Fetch customer profile
    cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
    cust_row = cursor.fetchone()
    if not cust_row:
        cursor.execute("SELECT * FROM customers WHERE customer_id = 'CUST-001'")
        cust_row = cursor.fetchone()
        
    cust = dict(cust_row)
    try:
        registered_devices = json.loads(cust.get("registered_devices", "[]"))
    except Exception:
        registered_devices = ["Mobile App (iOS)"]
        
    home_location = cust.get("home_location", "Mumbai, MH")
    home_city = home_location.split(",")[0].strip().lower()
    baseline_avg = float(cust.get("baseline_avg_amount", 3000.0))
    
    is_demo_profile = (cust.get("customer_id") != "LIVE-USER" and bool(cust.get("is_demo", 1)))
    
    # 2. Query dynamic historical stats strictly from prior records for THIS customer only
    cursor.execute("""
        SELECT COUNT(*) as total_count, AVG(amount) as avg_amount
        FROM transactions
        WHERE customer_id = ? AND (typical_time != 0 OR typical_time IS NULL)
    """, (cust["customer_id"],))
    hist_stats = cursor.fetchone()
    
    db_count = hist_stats["total_count"] if hist_stats and hist_stats["total_count"] else 0
    db_avg = hist_stats["avg_amount"] if hist_stats and hist_stats["avg_amount"] else None
    
    if db_avg is not None and db_count >= 1:
        customer_avg_amount = round(float(db_avg), 2)
        previous_transaction_count = int(db_count)
        amount_ratio = round(float(amount) / max(1.0, customer_avg_amount), 2)
        amount_comparison_label = f"{amount_ratio}x of customer baseline (₹{customer_avg_amount:,.2f})"
    else:
        if is_demo_profile:
            customer_avg_amount = baseline_avg
            previous_transaction_count = int(db_count)
            amount_ratio = round(float(amount) / max(1.0, customer_avg_amount), 2)
            amount_comparison_label = f"{amount_ratio}x of customer baseline (₹{customer_avg_amount:,.2f}) [DEMO DATA]"
        else:
            # Brand new live account with no genuine prior history
            customer_avg_amount = 0.0
            previous_transaction_count = 0
            amount_ratio = None
            amount_comparison_label = "New account — historical baseline not established"

    # 3. Query similarity frequency (same type or matching recipient) strictly for THIS customer
    cursor.execute("""
        SELECT COUNT(*) as sim_count
        FROM transactions
        WHERE customer_id = ? AND (transaction_type = ? OR recipient LIKE ?)
    """, (cust["customer_id"], txn_type, f"%{recipient}%" if recipient else "___"))
    sim_stats = cursor.fetchone()
    similar_transaction_count = int(sim_stats["sim_count"]) if sim_stats else 0
    
    # 4. Device Identification & Context (Prototype simulation)
    if simulated_device and simulated_device.strip():
        device_type = simulated_device.strip()
        is_known_device = any(
            (reg.lower() in device_type.lower() or device_type.lower() in reg.lower())
            for reg in registered_devices
        )
        new_device = 0 if is_known_device else 1
    elif not is_demo_profile:
        device_type = "Web Browser (Chrome)"
        new_device = 0
    else:
        device_type = registered_devices[0] if registered_devices else "Mobile App (iOS)"
        new_device = 0

    if not is_demo_profile:
        device_status_label = "Prototype device context: Authenticated client session" if new_device == 0 else "Prototype device context: Unrecognized / New Device (Flagged Risk)"
    else:
        device_status_label = "Verified Registered Device" if new_device == 0 else "Unrecognized / New Device (Flagged Risk)"
        
    # 5. Geolocation Identification & Context (Prototype simulation)
    if simulated_location and simulated_location.strip():
        location = simulated_location.strip()
    elif not is_demo_profile:
        location = "Local Region, India"
    else:
        location = home_location
        
    loc_lower = location.lower()
    is_foreign_or_proxy = any(kw in loc_lower for kw in ["lagos", "proxy", "vpn", "nigeria", "tor", "russia", "unknown ip"])

    if not is_demo_profile:
        unusual_location = 1 if is_foreign_or_proxy else 0
        location_status_label = f"Simulated location context: Anomalous Location ({location}) (Flagged Risk)" if unusual_location == 1 else f"Simulated location context: Verified Local Region ({location})"
    else:
        is_home_match = (home_city in loc_lower)
        if is_foreign_or_proxy:
            unusual_location = 1
        elif not is_home_match and ("," in location and home_city not in loc_lower):
            unusual_location = 1
        else:
            unusual_location = 0
        location_status_label = f"Verified Home Location ({home_location})" if unusual_location == 0 else f"Anomalous Location ({location}) (Flagged Risk)"

    # 6. Temporal Identification & Data-Driven Pattern Analyzer (Actual Application Time)
    now = datetime.now()
    if custom_time and str(custom_time).strip():
        time_str = str(custom_time).strip()
    elif simulated_time and str(simulated_time).strip() and is_demo_profile:
        time_str = str(simulated_time).strip()
    else:
        time_str = now.strftime("%H:%M:%S")

    if custom_date and str(custom_date).strip():
        date_str = str(custom_date).strip()
    else:
        date_str = now.strftime("%Y-%m-%d")

    # Format time with seconds if needed
    if len(time_str.split(":")) == 2:
        time_str = f"{time_str}:00"

    tx_timestamp = f"{date_str} {time_str}"
        
    # Run Customer-Specific Temporal Pattern Analysis from real historical records
    temporal_result = calculate_customer_temporal_pattern(
        customer_id=cust["customer_id"],
        new_time_str=time_str,
        new_date_str=date_str,
        cursor=cursor
    )
    
    typical_time = temporal_result["typical_time"]
    temporal_status = temporal_result["temporal_status"]
    time_status_label = temporal_result["time_status_label"]
    temporal_debug = temporal_result["debug_info"]
    temporal_source = temporal_result["profile_label"]

    # 7. Customer Fraud History
    previous_fraud_history = int(cust.get("prior_fraud_record", 0))

    # Close DB connection cleanly
    conn.close()
    
    # Assemble comprehensive derived factors payload for the UI
    derived_factors = {
        "customer_id": cust["customer_id"],
        "customer_name": cust["name"],
        "account_number": cust["account_number"],
        "account_type": cust["account_type"],
        "is_demo_data": is_demo_profile,
        "data_source_label": "DEMO DATA (Simulated Customer Persona)" if is_demo_profile else "DATABASE LIVE TEST RECORD",
        "temporal_pattern_source": temporal_source,
        "temporal_status": temporal_status,
        "temporal_debug": temporal_debug,
        "recipient": recipient or "General Beneficiary",
        "home_location": home_location if is_demo_profile else location,
        "derived_device": device_type,
        "new_device": new_device,
        "device_status_label": device_status_label,
        "derived_location": location,
        "unusual_location": unusual_location,
        "location_status_label": location_status_label,
        "derived_time": time_str,
        "transaction_timestamp": tx_timestamp,
        "typical_time": typical_time,
        "time_status_label": time_status_label,
        "customer_average_amount": customer_avg_amount,
        "amount_ratio": amount_ratio,
        "amount_comparison_label": amount_comparison_label,
        "previous_transaction_count": previous_transaction_count,
        "similar_transaction_count": similar_transaction_count,
        "previous_fraud_history": previous_fraud_history,
        "fraud_history_label": "Prior Fraud Alerts on Record (Flagged Risk)" if previous_fraud_history == 1 else "Clean Account History (No Prior Fraud)"
    }
    
    return {
        "amount": float(amount),
        "customer_average_amount": customer_avg_amount,
        "new_device": new_device,
        "unusual_location": unusual_location,
        "typical_time": typical_time,
        "previous_fraud_history": previous_fraud_history,
        "previous_transaction_count": previous_transaction_count,
        "similar_transaction_count": similar_transaction_count,
        "transaction_type": txn_type,
        "device_type": device_type,
        "location": location,
        "time": time_str,
        "date": date_str,
        "transaction_timestamp": tx_timestamp,
        "customer_id": cust["customer_id"],
        "recipient": recipient,
        "derived_factors": derived_factors
    }

def get_all_transactions(search="", risk="", txn_type="", record_type="", sort_by="date_desc"):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    
    if search:
        query += " AND (transaction_id LIKE ? OR location LIKE ? OR device_type LIKE ? OR transaction_type LIKE ? OR recipient LIKE ? OR description LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s, s, s])
        
    if risk:
        query += " AND risk_level = ?"
        params.append(risk)
        
    if txn_type:
        query += " AND transaction_type = ?"
        params.append(txn_type)

    if record_type == "live":
        query += " AND is_demo = 0"
    elif record_type == "demo":
        query += " AND is_demo = 1"
        
    if sort_by == "date_desc":
        query += " ORDER BY transaction_timestamp DESC, id DESC"
    elif sort_by == "date_asc":
        query += " ORDER BY transaction_timestamp ASC, id ASC"
    elif sort_by == "risk_desc":
        query += " ORDER BY fraud_probability DESC"
    elif sort_by == "amount_desc":
        query += " ORDER BY amount DESC"
    else:
        query += " ORDER BY transaction_timestamp DESC, id DESC"
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_transaction_by_id(tx_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE transaction_id = ?", (tx_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_transaction(tx_data):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Ensure clean transaction_timestamp
    tx_timestamp = tx_data.get("transaction_timestamp")
    if not tx_timestamp:
        d = tx_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        t = tx_data.get("time", datetime.now().strftime("%H:%M:%S"))
        tx_timestamp = f"{d} {t}"

    is_demo = int(tx_data.get("is_demo", 0))

    risk_score = float(tx_data.get("risk_score", tx_data.get("fraud_probability", 0.0)))
    raw_ann_probability = float(tx_data.get("raw_ann_probability", tx_data.get("fraud_probability", 0.0) / 100.0))
    temporal_status = str(tx_data.get("temporal_status", tx_data.get("derived_factors", {}).get("temporal_status", "")))

    cursor.execute('''
        INSERT INTO transactions (
            transaction_id, customer_id, recipient, description, amount, currency, transaction_type,
            date, time, location, device_type, new_device, unusual_location, customer_average_amount,
            previous_transaction_count, similar_transaction_count, previous_fraud_history,
            typical_time, temporal_status, fraud_probability, raw_ann_probability, risk_score, risk_level, prediction, explanation,
            feature_importance_json, derived_factors_json, is_demo, transaction_timestamp, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        tx_data["transaction_id"],
        tx_data.get("customer_id", "CUST-001"),
        tx_data.get("recipient", "General Merchant"),
        tx_data.get("description", ""),
        tx_data["amount"],
        tx_data.get("currency", "INR"),
        tx_data["transaction_type"],
        tx_data["date"],
        tx_data["time"],
        tx_data["location"],
        tx_data["device_type"],
        tx_data["new_device"],
        tx_data["unusual_location"],
        tx_data["customer_average_amount"],
        tx_data["previous_transaction_count"],
        tx_data["similar_transaction_count"],
        tx_data.get("previous_fraud_history", 0),
        tx_data.get("typical_time", 1),
        temporal_status,
        tx_data["fraud_probability"],
        raw_ann_probability,
        risk_score,
        tx_data["risk_level"],
        tx_data["prediction"],
        tx_data["explanation"],
        json.dumps(tx_data.get("feature_importance", [])),
        json.dumps(tx_data.get("derived_factors", {})),
        is_demo,
        tx_timestamp,
        tx_timestamp
    ))
    conn.commit()
    conn.close()
    return tx_data["transaction_id"]

def get_dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM transactions")
    total = cursor.fetchone()["total"]
    
    cursor.execute("SELECT COUNT(*) as safe FROM transactions WHERE risk_level = 'LOW RISK'")
    safe = cursor.fetchone()["safe"]
    
    cursor.execute("SELECT COUNT(*) as suspicious FROM transactions WHERE risk_level IN ('MEDIUM RISK', 'HIGH RISK')")
    suspicious = cursor.fetchone()["suspicious"]
    
    cursor.execute("SELECT AVG(risk_score) as avg_risk FROM transactions")
    avg_risk_row = cursor.fetchone()
    avg_risk = round(avg_risk_row["avg_risk"] or 0, 1)
    
    # Recent 6 transactions
    cursor.execute("SELECT * FROM transactions ORDER BY created_at DESC LIMIT 6")
    recent_rows = cursor.fetchall()
    
    # Risk Distribution for charts
    cursor.execute("SELECT risk_level, COUNT(*) as cnt FROM transactions GROUP BY risk_level")
    dist_rows = cursor.fetchall()
    distribution = {r["risk_level"]: r["cnt"] for r in dist_rows}
    
    conn.close()
    
    return {
        "total_transactions": total,
        "safe_transactions": safe,
        "suspicious_transactions": suspicious,
        "average_risk_score": avg_risk,
        "recent_transactions": [dict(r) for r in recent_rows],
        "distribution": distribution
    }
