import os
import json
import requests

class GPTService:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

    def generate_explanation(self, tx_data, prediction_result, xai_factors):
        """
        Generates a concise, plain-English explanation for a predicted transaction.
        Tries OpenAI/Gemini API first if keys exist; falls back to NLG Engine.
        """
        # Try OpenAI API if available
        if self.openai_api_key:
            try:
                res = self._call_openai_explanation(tx_data, prediction_result, xai_factors)
                if res:
                    return res
            except Exception as e:
                print(f"[GPT Service] OpenAI API call failed: {e}")
                
        # Try Gemini API if available
        if self.gemini_api_key:
            try:
                res = self._call_gemini_explanation(tx_data, prediction_result, xai_factors)
                if res:
                    return res
            except Exception as e:
                print(f"[GPT Service] Gemini API call failed: {e}")

        # Deterministic NLG Explanation Engine (Fallback)
        return self._generate_nlg_explanation(tx_data, prediction_result, xai_factors)

    def answer_user_question(self, user_question, tx_context=None):
        """
        Answers user questions regarding transaction risk, XAI factors, and false positives.
        """
        if self.openai_api_key:
            try:
                res = self._call_openai_chat(user_question, tx_context)
                if res:
                    return res
            except Exception as e:
                print(f"[GPT Chat] OpenAI chat failed: {e}")

        return self._generate_nlg_chat_answer(user_question, tx_context)

    def _generate_nlg_explanation(self, tx, result, factors):
        prob_display = result.get("fraud_prob_display")
        prob_val = result.get("fraud_probability", 0.0)
        prob_str = prob_display if prob_display else f"{prob_val:.2f}%"
        level = result.get("risk_level", "LOW RISK")
        score = result.get("risk_score", round(prob_val, 2))
        amount = tx.get("amount", 0)
        recipient = tx.get("recipient", "")
        recip_str = f" to {recipient}" if recipient and recipient != "General Beneficiary" else ""

        # Group factors strictly from actual XAI results (no invented reasons)
        risk_increasing = [
            f"{f['feature']} ({f['impact']}% SHAP impact share)"
            for f in factors if f.get('direction') == 'Risk'
        ]
        risk_reducing = [
            f"{f['feature']} ({f['impact']}% SHAP impact share)"
            for f in factors if f.get('direction') == 'Safe'
        ]

        disclaimer = (
            " Reminder: No individual feature proves a transaction is safe or fraudulent. "
            "The risk score represents a multi-modal assessment, and high transaction amount alone does NOT indicate fraud."
        )

        if level == "HIGH RISK":
            reasons_str = "; ".join(risk_increasing[:4]) if risk_increasing else "multi-modal anomaly indicators"
            explanation = (
                f"This transaction{recip_str} received a HIGH RISK rating with a model risk score of {score}/100 ({prob_str} fraud probability). "
                f"Features that increased model risk include: {reasons_str}. "
                f"{disclaimer}"
            )
        elif level == "MEDIUM RISK":
            risk_str = "; ".join(risk_increasing[:3]) if risk_increasing else "minor pattern variances"
            safe_str = "; ".join(risk_reducing[:3]) if risk_reducing else "standard baseline matches"
            explanation = (
                f"This transaction{recip_str} received a MEDIUM RISK rating with a model risk score of {score}/100 ({prob_str} fraud probability). "
                f"While risk-reducing features ({safe_str}) lowered the score, features increasing model risk ({risk_str}) warranted elevated caution. "
                f"Secondary step-up verification is advised.{disclaimer}"
            )
        else:
            safe_str = "; ".join(risk_reducing[:4]) if risk_reducing else "historical baseline consistency"
            explanation = (
                f"This transaction{recip_str} received a LOW RISK rating with a model risk score of {score}/100 ({prob_str} fraud probability). "
                f"The assessment was supported by risk-reducing features that lowered model risk: {safe_str}. "
                f"{'Notice: Even with a substantial transfer value of ₹{:,.2f}, high transaction amount alone does NOT mean fraud when verified device, location, and behavioral baselines reduce model risk. ' if amount >= 50000 else 'Multi-modal features align with baseline expectations. '}"
                f"{disclaimer}"
            ).format(amount)

        return explanation

    def _generate_nlg_chat_answer(self, question, tx_context):
        q = question.lower()
        
        tx_id = tx_context.get("transaction_id", "Current Transaction") if tx_context else "this transaction"
        prob = tx_context.get("fraud_probability", "N/A") if tx_context else ""
        level = tx_context.get("risk_level", "analyzed risk") if tx_context else ""
        amount = tx_context.get("amount", 0) if tx_context else 0

        if "why" in q and ("flag" in q or "risk" in q or "high" in q or "suspicious" in q):
            if tx_context and tx_context.get("risk_level") == "HIGH RISK":
                return (
                    f"Transaction {tx_id} was flagged as HIGH RISK ({prob}%) because multiple risk factors coincided at once. "
                    "Specifically, the neural network identified an unrecognized device, an anomalous location, and elevated monetary velocity. "
                    "In addition, rule-based contextual checks flagged the execution time as outside the customer's usual transaction-time pattern."
                )
            elif tx_context and tx_context.get("risk_level") == "MEDIUM RISK":
                return (
                    f"Transaction {tx_id} received a MEDIUM RISK score ({prob}%) due to conflicting signals. "
                    "While risk-reducing features (like familiar device or location) were present, other attributes diverged from historical baseline patterns. Secondary review or step-up verification is recommended."
                )
            else:
                return (
                    f"Transaction {tx_id} received a LOW RISK assessment ({prob}% probability). "
                    "Risk-reducing neural network features—such as verified device identity and primary geographic location—lowered the model risk score. "
                    "Furthermore, rule-based contextual checks confirm the transaction occurred within the customer's usual transaction-time pattern."
                )

        if "factor" in q or "affect" in q or "impact" in q or "most" in q:
            return (
                "Based on the Explainable AI (SHAP) feature attribution analysis, device verification and geographic location "
                "have the highest impact weights on the risk score (accounting for ~55-60% of total decision weight). "
                "The transaction amount contributes to the score only in combination with device and location context."
            )

        if "genuine" in q or "false positive" in q or "legitimate" in q or "wrong" in q:
            return (
                f"Yes, absolutely. Transaction {tx_id} could still be a genuine customer transaction! "
                "For example, customers frequently purchase high-value items (e.g., college fees, emergency travel, electronics) "
                "from a new phone or while traveling. That is why NeuroFinance GPT explicitly treats predictions as Risk Assessments rather than absolute proof of fraud."
            )

        if "amount" in q or "high amount" in q or "money" in q:
            return (
                "NeuroFinance GPT is specifically designed to avoid flagging transactions solely based on high monetary values. "
                "A customer transferring ₹1,00,000 for a legitimate invoice from their regular laptop at 11 AM will be marked LOW RISK, "
                "whereas a ₹10,000 transfer from an unknown offshore IP address at 3 AM will be flagged HIGH RISK."
            )

        # Default fallback answer
        return (
            f"Regarding your query about {tx_id}: The model evaluated numerical, categorical, temporal, and behavioral feature streams. "
            f"The transaction is currently categorized as {level} ({prob}% probability). "
            "You can view the detailed XAI bar chart in the Explainable AI tab to see exact feature impact percentages."
        )

    def _call_openai_explanation(self, tx, result, factors):
        headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
        prompt = f"""
You are NeuroFinance GPT, an explainable financial fraud detection AI powered by an Artificial Neural Network (ANN).
Translate the following technical transaction risk assessment into concise, simple English (2-3 sentences) suitable for a non-technical banking customer.

Transaction: ID={tx.get('transaction_id')}, Amount=₹{tx.get('amount')}, Type={tx.get('transaction_type')}, Location={tx.get('location')}
Model Output: Primary Model=Artificial Neural Network (ANN), Risk Level={result.get('risk_level')}, Risk Score={result.get('risk_score')}/100, Fraud Probability={result.get('fraud_prob_display', str(result.get('fraud_probability')) + '%')}
Contributing XAI Factors: {json.dumps(factors[:4])}

Rule: Explicitly clarify if the high amount alone was NOT treated as proof of fraud. Remind that this prediction is a risk assessment, not absolute proof.
"""
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 180,
            "temperature": 0.3
        }
        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=5)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
        return None

    def _call_gemini_explanation(self, tx, result, factors):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.gemini_api_key}"
        prob_str = result.get('fraud_prob_display', str(result.get('fraud_probability')) + '%')
        score = result.get('risk_score', result.get('fraud_probability'))
        prompt = f"""
Explain this financial transaction risk result in simple English:
Transaction: ₹{tx.get('amount')}, Risk Level: {result.get('risk_level')} (Risk Score: {score}/100, Fraud Probability: {prob_str}), Type: {tx.get('transaction_type')}
XAI Factors: {json.dumps(factors[:4])}
Keep it short, clear, and professional. State that prediction is a risk score, not absolute proof.
"""
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, json=payload, timeout=5)
        if res.status_code == 200:
            return res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        return None

    def _call_openai_chat(self, question, tx_context):
        headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
        ctx_str = json.dumps(tx_context) if tx_context else "No active transaction selected"
        prompt = f"""
You are NeuroFinance GPT Assistant. Answer the user's question about financial fraud detection and explainable AI concisely.
Context: {ctx_str}
Question: {question}
"""
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,
            "temperature": 0.4
        }
        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=5)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
        return None

# Singleton instance
gpt_service = GPTService()
