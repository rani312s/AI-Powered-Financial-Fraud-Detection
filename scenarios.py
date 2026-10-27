DEMO_SCENARIOS = {
    "scenario_1": {
        "title": "Scenario 1 — Safe Transaction",
        "badge": "Safe",
        "description": "Routine INR 2,500 grocery purchase by Priya Sharma using her verified iPhone from her home city (Mumbai) within her usual transaction-time pattern (14:30).",
        "data": {
            "customer_id": "CUST-001",
            "amount": 2500.0,
            "currency": "INR",
            "transaction_type": "Purchase",
            "recipient": "Nature's Basket",
            "description": "Weekly organic groceries and supplies",
            "simulated_device": "Mobile App (iOS)",
            "simulated_location": "Mumbai, MH",
            "simulated_time": "14:30"
        },
        "faculty_note": "Expected Result: LOW RISK (Safe). Baseline match: normal average, trusted mobile device, verified Mumbai location, usual transaction-time pattern."
    },
    "scenario_2": {
        "title": "Scenario 2 — Suspicious High-Risk Fraud",
        "badge": "Fraud Alert",
        "description": "Large INR 80,000 online transfer attempt from an unrecognized Linux browser at 03:15 AM outside customer's usual transaction-time pattern routed through a foreign proxy IP (Lagos, Nigeria).",
        "data": {
            "customer_id": "CUST-001",
            "amount": 80000.0,
            "currency": "INR",
            "transaction_type": "Online Transfer",
            "recipient": "CryptoGlobal Liquidity Desk",
            "description": "Urgent offshore settlement",
            "simulated_device": "Unknown Browser (Linux)",
            "simulated_location": "Lagos, NG (Proxy IP)",
            "simulated_time": "03:15"
        },
        "faculty_note": "Expected Result: HIGH RISK (>85% Fraud Probability). Triggers multi-modal anomaly: abnormal amount multiplier (28x), new unverified device, foreign proxy geolocation, outside usual transaction-time pattern."
    },
    "scenario_3": {
        "title": "Scenario 3 — High Amount Legitimate",
        "badge": "High Value Safe",
        "description": "High-value INR 1,20,000 semester tuition payment by Aarav Patel using his registered MacBook from Bengaluru within customer's usual transaction-time pattern (11:30).",
        "data": {
            "customer_id": "CUST-002",
            "amount": 120000.0,
            "currency": "INR",
            "transaction_type": "Payment",
            "recipient": "Manipal University Fee Portal",
            "description": "Executive Education Semester Tuition Fee",
            "simulated_device": "MacBook Air (Chrome)",
            "simulated_location": "Bengaluru, KA",
            "simulated_time": "11:30"
        },
        "faculty_note": "Expected Result: LOW RISK (Legitimate High-Value). Critical Anti-False-Positive Demonstration: Proves the system does NOT flag transactions solely because of high monetary value when contextual and behavioral baselines (known device, home region, usual transaction-time pattern, prior category history) confirm legitimacy."
    }
}
