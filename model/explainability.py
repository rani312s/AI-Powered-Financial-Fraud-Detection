import os
import json
import numpy as np
import pandas as pd

class ExplainableAIEngine:
    """
    Explainable AI (XAI) Attribution Engine.
    Computes local feature attributions across the 6 multi-modal feature groups
    derived from the IEEE-CIS Fraud Detection dataset.
    """
    def __init__(self, fraud_detector):
        self.detector = fraud_detector
        self.shap_explainer = None
        self._init_shap()

    def _init_shap(self):
        # Ensure single consistent SHAP pipeline for the Primary ANN Model (model-agnostic KernelExplainer)
        if hasattr(self.detector, '_get_shap_explainer'):
            self.shap_explainer = self.detector._get_shap_explainer()
        else:
            self.shap_explainer = None

    def explain_transaction(self, tx_features, raw_tx_input, prediction_result):
        """
        Calculates local feature attributions for the transaction across:
        1. Transaction Attributes (Amount, Product Code)
        2. Identity & Authentication Attributes
        3. Device & Network Footprint
        4. Behavioral Velocity & Historical Spikes (C-columns, D-columns)
        5. Numerical Attributes (V-features, Card values)
        6. Categorical Attributes (Card networks, Email domains)
        """
        # If the fraud_detector already computed feature_importance during prediction, use it
        if prediction_result and 'feature_importance' in prediction_result and prediction_result['feature_importance']:
            return prediction_result['feature_importance']

        # Otherwise delegate to detector's attribution method
        if hasattr(self.detector, '_compute_feature_attributions'):
            fraud_prob = prediction_result.get('fraud_probability', 10.0) if prediction_result else 10.0
            res = self.detector._compute_feature_attributions(None, tx_features, fraud_prob, raw_tx_input)
            if isinstance(res, dict):
                return res.get('all_factors', [])
            return res

        return []

