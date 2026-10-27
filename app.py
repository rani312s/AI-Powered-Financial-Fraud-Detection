from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from database.db import (
    init_db, get_dashboard_stats, get_all_transactions, get_transaction_by_id,
    save_transaction, get_all_customers, get_customer_profile, derive_customer_features
)
from model.fraud_model import fraud_detector
from model.explainability import ExplainableAIEngine
from services.gpt_service import gpt_service
from scenarios import DEMO_SCENARIOS

# Initialize Flask App
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Initialize Explainable AI Engine
xai_engine = ExplainableAIEngine(fraud_detector)

# Initialize Database schema & demo data
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats', methods=['GET'])
def api_stats():
    try:
        stats = get_dashboard_stats()
        return jsonify({"status": "success", "data": stats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/customers', methods=['GET'])
def api_customers():
    try:
        customers = get_all_customers()
        return jsonify({"status": "success", "data": customers})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/transactions', methods=['GET'])
def api_transactions():
    try:
        search = request.args.get('search', '')
        risk = request.args.get('risk', '')
        txn_type = request.args.get('type', '')
        record_type = request.args.get('record_type', '') # 'all', 'live', 'demo'
        sort_by = request.args.get('sort', 'date_desc')
        
        txs = get_all_transactions(search, risk, txn_type, record_type, sort_by)
        return jsonify({"status": "success", "data": txs})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/transactions/<tx_id>', methods=['GET'])
def api_transaction_detail(tx_id):
    try:
        tx = get_transaction_by_id(tx_id)
        if not tx:
            return jsonify({"status": "error", "message": "Transaction not found"}), 404
        if tx.get('derived_factors_json'):
            try:
                tx['derived_factors'] = json.loads(tx['derived_factors_json'])
            except Exception:
                tx['derived_factors'] = {}
        return jsonify({"status": "success", "data": tx})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "Missing input data"}), 400
            
        # Form input validation (clean banking fields)
        amount = data.get('amount')
        if amount is None or float(amount) <= 0:
            return jsonify({"status": "error", "message": "Transaction amount must be a positive number"}), 400
            
        if not data.get('transaction_type'):
            return jsonify({"status": "error", "message": "Transaction type is required"}), 400

        # Customer ID and Demo/Live separation
        customer_id = (data.get('customer_id') or '').strip()
        if not customer_id:
            customer_id = 'LIVE-USER'

        if 'is_demo' in data and data['is_demo'] is not None:
            is_demo = int(data['is_demo'])
        else:
            is_demo = 0 if customer_id == 'LIVE-USER' else 1

        recipient = (data.get('recipient') or '').strip() or 'General Beneficiary'
        description = (data.get('description') or '').strip()

        # Capture actual current application date & time
        now = datetime.now()
        user_date = (data.get('date') or '').strip()
        user_time = (data.get('time') or '').strip()

        actual_date = user_date if user_date else now.strftime("%Y-%m-%d")
        if user_time:
            actual_time = user_time if len(user_time.split(":")) == 3 else f"{user_time}:00"
        else:
            actual_time = now.strftime("%H:%M:%S")

        actual_timestamp = f"{actual_date} {actual_time}"

        # Automatic Behavioral & Contextual Feature Derivation Engine
        # Calculates historical avg, transaction counts, similarity frequencies,
        # device registry check, location check, and operating hours.
        derived = derive_customer_features(
            customer_id=customer_id,
            amount=float(amount),
            txn_type=data.get('transaction_type'),
            recipient=recipient,
            simulated_device=data.get('simulated_device'),
            simulated_location=data.get('simulated_location'),
            simulated_time=data.get('simulated_time'),
            custom_date=actual_date,
            custom_time=actual_time
        )

        merged_tx = {**derived}
        if data.get('currency'):
            merged_tx['currency'] = data.get('currency')
        merged_tx['description'] = description
        merged_tx['is_demo'] = is_demo
        merged_tx['date'] = actual_date
        merged_tx['time'] = actual_time
        merged_tx['transaction_timestamp'] = actual_timestamp

        # Simulation / Faculty overrides if explicitly toggled in demonstration mode
        if 'new_device' in data and data['new_device'] is not None:
            merged_tx['new_device'] = int(data['new_device'])
            merged_tx['derived_factors']['new_device'] = merged_tx['new_device']
            merged_tx['derived_factors']['device_status_label'] = "Unrecognized / New Device (Flagged Risk)" if merged_tx['new_device'] == 1 else "Verified Registered Device"
            
        if 'unusual_location' in data and data['unusual_location'] is not None:
            merged_tx['unusual_location'] = int(data['unusual_location'])
            merged_tx['derived_factors']['unusual_location'] = merged_tx['unusual_location']
            merged_tx['derived_factors']['location_status_label'] = f"Anomalous Location ({merged_tx['location']}) (Flagged Risk)" if merged_tx['unusual_location'] == 1 else f"Verified Home Location ({merged_tx['derived_factors']['home_location']})"

        if 'typical_time' in data and data['typical_time'] is not None:
            merged_tx['typical_time'] = int(data['typical_time'])
            merged_tx['derived_factors']['typical_time'] = merged_tx['typical_time']
            merged_tx['derived_factors']['time_status_label'] = f"{merged_tx['time']} — Within customer's usual transaction-time pattern" if merged_tx['typical_time'] == 1 else f"{merged_tx['time']} — Outside customer's usual transaction-time pattern (Flagged Risk)"

        # Always generate a cryptographically unique transaction ID for every newly analyzed transaction
        unique_suffix = f"{now.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        merged_tx['transaction_id'] = f"TXN-{unique_suffix}"

        # 1. Primary Artificial Neural Network (ANN) Fraud Prediction
        result = fraud_detector.predict_transaction(merged_tx)
        
        # 2. Explainable AI Feature Importance calculation (ANN KernelSHAP)
        xai_factors = xai_engine.explain_transaction(
            result['features_dict'], merged_tx, result
        )
        
        # 3. GPT / NLG Natural Language Explanation
        explanation = gpt_service.generate_explanation(merged_tx, result, xai_factors)
        
        # Expose temporal debug metrics inside debug_info for auditing
        debug_info = result.get('debug_info', {})
        if 'temporal_debug' in merged_tx['derived_factors']:
            debug_info['temporal_analysis'] = merged_tx['derived_factors']['temporal_debug']

        # Log temporal pattern analysis details to terminal
        temporal_dbg = merged_tx['derived_factors'].get('temporal_debug', {})
        print(f"[Temporal Pattern Engine] Customer: {merged_tx['customer_id']} ({merged_tx['derived_factors'].get('temporal_pattern_source', 'History')})")
        print(f"   --> Txn Time: {merged_tx['time']} (Hour {temporal_dbg.get('extracted_hour', 'N/A')}) | Past Records: {temporal_dbg.get('historical_transaction_count', 0)}")
        print(f"   --> Normal Window: {temporal_dbg.get('calculated_normal_window', {}).get('window_description', 'N/A')}")
        print(f"   --> Check Result: {'Within normal pattern' if merged_tx['typical_time'] == 1 else 'OUTSIDE normal pattern (Flagged)'} (typical_time={merged_tx['typical_time']})")
        print(f"   --> Attribution: Rule-based contextual signal (Not an ANN model input feature)")

        # Assemble full output record
        record = {
            "transaction_id": merged_tx['transaction_id'],
            "customer_id": merged_tx['customer_id'],
            "recipient": merged_tx['recipient'],
            "description": merged_tx['description'],
            "amount": float(merged_tx['amount']),
            "currency": merged_tx.get('currency', 'INR'),
            "transaction_type": merged_tx['transaction_type'],
            "date": actual_date,
            "time": actual_time,
            "transaction_timestamp": actual_timestamp,
            "is_demo": is_demo,
            "location": merged_tx['location'],
            "device_type": merged_tx['device_type'],
            "new_device": int(merged_tx['new_device']),
            "unusual_location": int(merged_tx['unusual_location']),
            "customer_average_amount": float(merged_tx['customer_average_amount']),
            "previous_transaction_count": int(merged_tx['previous_transaction_count']),
            "similar_transaction_count": int(merged_tx['similar_transaction_count']),
            "previous_fraud_history": int(merged_tx['previous_fraud_history']),
            "typical_time": int(merged_tx['typical_time']),
            "temporal_status": merged_tx['derived_factors'].get('temporal_status', ''),
            "fraud_probability": result['fraud_probability'],
            "raw_ann_probability": result.get('raw_ann_probability', result['fraud_probability']),
            "fraud_prob_display": result.get('fraud_prob_display', f"{result['fraud_probability']:.2f}%"),
            "risk_score": result.get('risk_score', result['fraud_probability']),
            "risk_level": result['risk_level'],
            "prediction": result['prediction'],
            "explanation": explanation,
            "feature_importance": xai_factors,
            "risk_drivers": result.get('risk_drivers', []),
            "risk_reducers": result.get('risk_reducers', []),
            "driver_count": result.get('driver_count', len(result.get('risk_drivers', []))),
            "reducer_count": result.get('reducer_count', len(result.get('risk_reducers', []))),
            "debug_info": debug_info,
            "derived_factors": merged_tx['derived_factors']
        }
        
        # Save to database
        save_transaction(record)
        
        return jsonify({"status": "success", "data": record})
        
    except ValueError as ve:
        return jsonify({"status": "error", "message": f"Validation Error: {str(ve)}"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Server Error during analysis: {str(e)}"}), 500

@app.route('/api/scenarios', methods=['GET'])
def api_scenarios():
    return jsonify({"status": "success", "data": DEMO_SCENARIOS})

@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        data = request.json or {}
        user_question = data.get('question', '').strip()
        tx_context = data.get('tx_context', None)
        
        if not user_question:
            return jsonify({"status": "error", "message": "Question cannot be empty"}), 400
            
        reply = gpt_service.answer_user_question(user_question, tx_context)
        return jsonify({"status": "success", "data": {"reply": reply}})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/metrics', methods=['GET'])
def api_metrics():
    return jsonify({"status": "success", "data": fraud_detector.metrics})

@app.route('/api/dataset', methods=['GET'])
def api_dataset():
    try:
        meta_path = os.path.join(os.path.dirname(__file__), 'data', 'processed', 'dataset_metadata.json')
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify({"status": "success", "data": data})
        return jsonify({"status": "error", "message": "Dataset metadata not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/model/performance', methods=['GET'])
def api_model_performance():
    try:
        metrics_path = os.path.join(os.path.dirname(__file__), 'model', 'model_metrics.json')
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify({"status": "success", "data": data})
        return jsonify({"status": "success", "data": fraud_detector.metrics})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"==================================================")
    print(f" NeuroFinance GPT Server Running on http://127.0.0.1:{port}")
    print(f" Academic Explainable AI Financial Security Prototype")
    print(f"==================================================")
    app.run(host='0.0.0.0', port=port, debug=True)
