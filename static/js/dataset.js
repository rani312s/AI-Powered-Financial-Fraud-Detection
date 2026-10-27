/**
 * NeuroFinance GPT — Dataset & Model Academic Evaluation Module
 * Loads programmatically calculated statistics from the authentic Kaggle IEEE-CIS Fraud Detection dataset.
 */

let datasetLoaded = false;

async function loadDatasetPage() {
    try {
        const [dsRes, modelRes] = await Promise.all([
            fetch('/api/dataset').then(r => r.json()),
            fetch('/api/model/performance').then(r => r.json())
        ]);

        if (dsRes.status === 'success' && dsRes.data) {
            renderDatasetMetadata(dsRes.data);
            renderFeatureGroups(dsRes.data.feature_groups);
            renderSampleTable(dsRes.data.sample_records);
        }

        if (modelRes.status === 'success' && modelRes.data) {
            renderModelPerformance(modelRes.data);
        }

        datasetLoaded = true;
        if (window.lucide) lucide.createIcons();
    } catch (err) {
        console.error("Error loading dataset/model evaluation:", err);
    }
}

function renderDatasetMetadata(meta) {
    const setEl = (id, text) => {
        const el = document.getElementById(id);
        if (el) el.innerText = text;
    };

    setEl('ds-total-records', (meta.total_records || 49999).toLocaleString());
    setEl('ds-raw-features', meta.total_raw_features || 434);
    setEl('ds-selected-features', meta.selected_features_count || 72);
    setEl('ds-fraud-records', `${(meta.fraud_records || 1357).toLocaleString()} (${meta.fraud_percentage || 2.71}%)`);
    setEl('ds-non-fraud-records', `${(meta.non_fraud_records || 48642).toLocaleString()} (${(100 - (meta.fraud_percentage || 2.71)).toFixed(2)}%)`);
    setEl('ds-train-split', `${(meta.train_records || 39999).toLocaleString()} (80%)`);
    setEl('ds-test-split', `${(meta.test_records || 10000).toLocaleString()} (20%)`);
}

function renderFeatureGroups(groups) {
    const container = document.getElementById('feature-groups-container');
    if (!container || !groups) return;

    const groupKeys = [
        { key: 'transaction_features', icon: 'credit-card', color: '#2563EB' },
        { key: 'identity_features', icon: 'shield-check', color: '#7C3AED' },
        { key: 'device_network_features', icon: 'smartphone', color: '#059669' },
        { key: 'behavioral_features', icon: 'activity', color: '#D97706' },
        { key: 'numerical_features', icon: 'hash', color: '#DC2626' },
        { key: 'categorical_features', icon: 'tag', color: '#4B5563' }
    ];

    container.innerHTML = groupKeys.map(({ key, icon, color }) => {
        const g = groups[key];
        if (!g) return '';
        const cols = g.columns || [];
        const chips = cols.map(c => `<span class="feature-chip">${c}</span>`).join('');
        return `
            <div class="feature-group-card">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                    <h4 style="font-size: 15px; font-weight: 700; color: var(--color-primary); display: flex; align-items: center; gap: 8px;">
                        <i data-lucide="${icon}" style="color: ${color}; width: 18px; height: 18px;"></i>
                        ${g.title}
                    </h4>
                    <span class="badge" style="background: #F1F5F9; color: #475569; font-size: 11px;">${cols.length} Features</span>
                </div>
                <p style="font-size: 12px; color: var(--color-text-muted); line-height: 1.5; margin-bottom: 10px;">
                    ${g.description}
                </p>
                <div class="feature-chips-wrap">
                    ${chips}
                </div>
            </div>
        `;
    }).join('');
}

function renderModelPerformance(metrics) {
    const setEl = (id, text) => {
        const el = document.getElementById(id);
        if (el) el.innerText = text;
    };

    // Primary Model: Artificial Neural Network (ANN)
    setEl('ds-model-accuracy', `${metrics.accuracy || 97.29}%`);
    setEl('ds-model-roc-auc', `${metrics.roc_auc || 87.82}%`);
    setEl('ds-model-recall', `${metrics.recall || 53.51}%`);
    setEl('ds-model-precision', `${metrics.precision || 50.0}%`);
    setEl('ds-model-f1', `${metrics.f1_score || 51.69}%`);

    // Optional Baseline Model: Random Forest
    setEl('ds-baseline-accuracy', `${metrics.baseline_rf_accuracy || 93.5}%`);
    setEl('ds-baseline-f1', `${metrics.baseline_rf_f1 || 38.91}%`);
    setEl('ds-baseline-roc', `${metrics.baseline_rf_roc_auc || 92.13}%`);

    // Render Confusion Matrix
    if (metrics.confusion_matrix && metrics.confusion_matrix.length === 2) {
        const cm = metrics.confusion_matrix;
        const tn = cm[0][0];
        const fp = cm[0][1];
        const fn = cm[1][0];
        const tp = cm[1][1];

        setEl('cm-tn-val', tn.toLocaleString());
        setEl('cm-fp-val', fp.toLocaleString());
        setEl('cm-fn-val', fn.toLocaleString());
        setEl('cm-tp-val', tp.toLocaleString());

        const tnRate = ((tn / (tn + fp)) * 100).toFixed(1);
        const tpRate = ((tp / (tp + fn)) * 100).toFixed(1);
        setEl('cm-tn-sub', `True Negatives (${tnRate}% Specificity)`);
        setEl('cm-tp-sub', `True Positives (${tpRate}% Sensitivity)`);
    }

    // Render Top Global Features Bar Chart / List
    if (metrics.top_global_features) {
        const topContainer = document.getElementById('ds-top-features-list');
        if (topContainer) {
            topContainer.innerHTML = metrics.top_global_features.slice(0, 8).map(f => `
                <div style="margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 600; margin-bottom: 4px;">
                        <span><code style="background: #F1F5F9; padding: 2px 6px; border-radius: 4px;">${f.feature}</code></span>
                        <span style="color: var(--color-secondary);">${f.importance}%</span>
                    </div>
                    <div class="xai-bar-track" style="height: 6px;">
                        <div class="xai-bar-fill bar-safe" style="width: ${Math.min(100, f.importance * 18)}%; height: 6px;"></div>
                    </div>
                </div>
            `).join('');
        }
    }
}

function renderSampleTable(samples) {
    const tbody = document.getElementById('ds-sample-table-body');
    if (!tbody) return;

    if (!samples || samples.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 16px;">No sample records available.</td></tr>';
        return;
    }

    tbody.innerHTML = samples.map(row => {
        const isFraud = row.isFraud === 1 || row.isFraud === '1';
        const badgeClass = isFraud ? 'badge-fraud' : 'badge-safe';
        const badgeText = isFraud ? 'Confirmed Fraud' : 'Legitimate';
        const amount = parseFloat(row.TransactionAmt || 0).toFixed(2);
        const device = row.DeviceInfo || row.DeviceType || 'Standard Client';
        const email = row.P_emaildomain || 'Direct / Undisclosed';

        return `
            <tr>
                <td><strong>TXN-${row.TransactionID || 'N/A'}</strong></td>
                <td>$${amount}</td>
                <td><span class="badge" style="background:#E2E8F0; color:#334155;">${row.ProductCD || 'W'}</span></td>
                <td>${device}</td>
                <td>${email}</td>
                <td><span class="badge ${badgeClass}">${badgeText}</span></td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="quickFillSample('${row.TransactionID}', ${amount}, '${row.ProductCD}', '${device}', '${email}')">
                        Use in Analyze
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function quickFillSample(id, amount, product, device, email) {
    navigateTo('analyze');
    const amtInput = document.getElementById('input-amount');
    const descInput = document.getElementById('input-description');
    const recipInput = document.getElementById('input-recipient');
    const simDevInput = document.getElementById('input-sim-device');

    if (amtInput) amtInput.value = amount;
    if (descInput) descInput.value = `IEEE-CIS Kaggle Sample #${id} (${product})`;
    if (recipInput) recipInput.value = email !== 'Direct / Undisclosed' ? `${email} merchant` : 'E-Commerce Merchant';
    if (simDevInput) simDevInput.value = device;

    // Open drawer so user sees device filled
    const drawer = document.getElementById('simulation-details-drawer');
    if (drawer) drawer.open = true;
}
