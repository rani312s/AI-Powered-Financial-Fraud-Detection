# NeuroFinance GPT: Explainable Deep Learning for Financial Fraud Prediction Using Multi-Modal Data

> **Academic College Project & Research Prototype**  
> *"Explainable Deep Learning for Smarter Financial Security"*

---

## 1. Project Overview & Architectural Specifications

**NeuroFinance GPT** is an academic research prototype demonstrating explainable deep learning for financial fraud prediction using multi-modal transaction data. The project is built upon a project subset of the benchmark **IEEE-CIS Fraud Detection Dataset** (Kaggle / Vesta Corporation).

### Official Model & System Specification
- **Primary Model**: **Artificial Neural Network (ANN)**
- **Model Type**: Deep Learning — Multi-Layer Perceptron (`MLPClassifier`: 72 input features &rarr; 128 &rarr; 64 &rarr; 32 &rarr; 2 output logits)
- **Dataset**: **IEEE-CIS Fraud Detection Dataset — project subset** (49,999 joined transaction & identity records, 72 selected multi-modal features across 6 analytical streams)
- **Explainable AI (XAI)**: **SHAP (SHapley Additive exPlanations)** — ANN KernelExplainer computing relative feature attributions ($\phi_i$)
- **Optional Baseline Model**: **Random Forest Classifier** (evaluated strictly as an academic baseline comparator)
- **Database**: **SQLite** (`database/neurofinance.db`) with full transactional persistence and customer isolation
- **Explanation Layer**: **NeuroFinance GPT** — Natural-language explanation layer translating technical ANN predictions into plain English
- **System Classification**: **Academic Prototype** (not connected to live banking production rails)

---

## 2. End-to-End Processing Flow & Single Source of Truth

```
User Transaction Submission
        ↓
Backend API Endpoint (/api/analyze)
        ↓
Customer History Isolation (WHERE customer_id = ?)
        ↓
Data-Driven Feature Engineering (Minutes-since-midnight circular temporal check, spending baseline)
        ↓
Fitted Preprocessing Pipeline (StandardScaler & Ordinal Encoders, 72 features)
        ↓
Primary Model: Artificial Neural Network (ANN)
        ↓
Raw Statistical Probability P(Fraud | X)
        ↓
Operational Risk Score (Single Source of Truth: 0–100 Scale)
        ↓
Operational Risk Level Policy:
  • 0–30%      → LOW RISK
  • >30–70%    → MEDIUM RISK
  • >70–100%   → HIGH RISK
        ↓
Model-Agnostic ANN SHAP Attributions (KernelExplainer)
        ↓
NeuroFinance GPT Natural-Language Explanation Layer
        ↓
SQLite Database History Record
        ↓
Frontend Dashboard & Analysis View
```

### Risk Score & Probability Policy
- The ANN posterior probability is the single source of truth for every transaction.
- `risk_score = min(100.0, max(0.0, fraud_probability_percentage))`
- Probabilities are displayed with high precision: `<0.01%` for small positive probabilities, avoiding misleading "0%" displays.
- High transaction amount alone does **NOT** trigger fraud: multi-modal features (device verification, geolocation, behavioral velocity) are evaluated simultaneously.

---

## 3. Real Holdout Test Set Evaluation Metrics (N = 10,000)

The model is evaluated on 10,000 unseen holdout samples (271 actual fraud cases, 9,729 legitimate transactions) from the IEEE-CIS project subset:

| Metric | Primary Model: Artificial Neural Network (ANN) | Baseline Model: Random Forest (Optional) |
| :--- | :---: | :---: |
| **Architecture** | **MLP (72 &rarr; 128 &rarr; 64 &rarr; 32 &rarr; 2)** | Random Forest (60 trees, max depth 10) |
| **Accuracy** | **97.29%** | 93.50% |
| **ROC-AUC** | **87.82%** | 92.13% |
| **Fraud Recall** | **53.51%** | 76.38% |
| **Precision** | **50.00%** | 26.10% |
| **F1 Score** | **51.69%** | 38.91% |
| **Test Set Size** | **10,000 samples** (271 fraud / 9,729 normal) | 10,000 samples |

*Confusion Matrix (Primary ANN):*
- **True Negatives (TN)**: 9,584 (98.5% Specificity)
- **False Positives (FP)**: 145 (Drastically minimized false alarms)
- **False Negatives (FN)**: 126
- **True Positives (TP)**: 145 (53.5% Sensitivity)

---

## 4. Multi-Modal Feature Space & IEEE-CIS Anonymized Features

Features are curated into 6 multi-modal analytical groups:
1. **Transaction Core Attributes**: `TransactionAmt` (USD), `ProductCD`, `TransactionDT` (relative seconds delta).
2. **Digital Identity Attributes**: `id_01` to `id_38` (device hardware signatures, IP hop distance, verification indicators).
3. **Device & Network Attributes**: `DeviceType`, `DeviceInfo`, `P_emaildomain`, `R_emaildomain`.
4. **Behavioral Velocity & Counters**: `C1`–`C14` frequency counters and `D1`–`D15` timedelta features.
5. **Numerical & Spatial Attributes**: `card1`–`card6`, `addr1`, `addr2`, `dist1`, `V12`–`V310` engineered relation indicators.
6. **Categorical Attributes**: Card payment schemes (`card4`), funding types (`card6`), address match flags (`M1`–`M9`).

*Academic Integrity Note on IEEE-CIS Features:*  
Anonymized features (`C1`–`C14`, `D1`–`D15`, `V12`–`V310`, `id_01`–`id_38`) are labeled honestly as `(Anonymized IEEE-CIS feature)` without fabricating unverified real-world semantics.

---

## 5. Circular Minutes-Since-Midnight Temporal Engine

The customer temporal analysis compares transaction execution time strictly against the customer's actual historical distribution using circular 1440-minute mathematics ($\text{minutes} = \text{hour} \times 60 + \text{minute}$):
- `03:10` &rarr; 190 minutes
- `04:12` &rarr; 252 minutes
- Accounts with $< 2$ past transactions return `temporal_status = "INSUFFICIENT_HISTORY"` (neutral status, neither risk driver nor risk-reducing feature).
- Accounts with $\ge 2$ past transactions identify the inactive sleep interval via maximum circular gap on the 24-hour ring and set the active span as its complement ($\pm 60$ min tolerance).

---

## 6. Directory Structure

```
c:/Chitti/Neuro Finance GPT/
├── app.py                      # Main Flask Server & REST API
├── requirements.txt            # Pinned Compatible Python Dependencies
├── .env.example                # Environment Variable Template
├── README.md                   # Complete Academic Project Documentation
├── scenarios.py                # Academic Evaluation Demonstration Scenarios
├── database/
│   ├── db.py                   # SQLite Schema, Customer Isolation & Temporal Engine
│   └── neurofinance.db         # SQLite Application Database
├── model/
│   ├── fraud_model.py          # Primary ANN Model (MLPClassifier) & SHAP Engine
│   ├── explainability.py       # Model-Agnostic Explainable AI Interface
│   ├── data_loader.py          # IEEE-CIS Subset Loader & Preprocessing Pipeline
│   └── model_metrics.json      # Programmatically Computed Holdout Test Metrics
├── data/
│   ├── raw/                    # Kaggle IEEE-CIS Raw Dataset Files (train_transaction, train_identity)
│   └── processed/              # Preprocessed Joblib Artifacts & Metadata JSON
├── services/
│   └── gpt_service.py          # Natural Language Explanation & AI Assistant Service
├── static/
│   ├── css/style.css           # Modern Academic Fintech UI Stylesheet
│   └── js/
│       ├── main.js             # View Routing & Core Navigation
│       ├── dashboard.js        # Analytics Charts & Summary KPIs
│       ├── analyze.js          # Transaction Form & Factor Attribution Display
│       ├── dataset.js          # Dataset Statistics & Confusion Matrix Explorer
│       └── chat.js             # NeuroFinance GPT Explanatory Assistant
└── templates/
    └── index.html              # Single Page Application HTML Shell
```

---

## 7. Installation & Setup Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.14 on Windows)
- Pinned runtime libraries: `scikit-learn==1.9.0`, `numpy==2.5.2`, `pandas==3.0.5`, `shap==0.52.0`, `flask==3.1.3`

### Step 1: Open Project Directory
```powershell
cd "c:\Chitti\Neuro Finance GPT"
```

### Step 2: Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### Step 3: Run the Server
```powershell
python app.py
```

Open your browser at:  
[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 8. Academic Evaluation Scenarios

The prototype provides 3 key academic scenarios:
1. **Normal Transaction**: ₹2,500 grocery purchase, verified mobile device, familiar region, regular afternoon time &rarr; **LOW RISK**.
2. **Suspicious Transaction**: ₹80,000 crypto desk transfer, unrecognized device, foreign proxy location, overnight &rarr; **HIGH RISK**.
3. **High-Value Legitimate Transaction**: ₹1,20,000 university semester tuition fee, verified MacBook, home location, regular morning time &rarr; **LOW RISK** (proves that large monetary values do not cause false positives when contextual and behavioral features verify legitimacy).

---

## 9. Academic Disclaimer

NeuroFinance GPT is an academic research and demonstration prototype developed for coursework evaluation. All predictions are continuous probability risk assessments output by deep learning models and do not constitute legal proof or a real commercial banking system.
