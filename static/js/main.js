// NeuroFinance GPT - Main UI Router & Global Utilities

let activeTransactionContext = null;

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    loadDashboardData();
    loadModelMetrics();
    initCustomerProfiles();
});

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetView = item.getAttribute('data-view');
            navigateTo(targetView);
            closeSidebar();
        });
    });

    // Close mobile drawer on Escape key or resize
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeSidebar();
            closeModal();
        }
    });

    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            closeSidebar();
        }
    });
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (sidebar) sidebar.classList.toggle('open');
    if (backdrop) backdrop.classList.toggle('active');
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (sidebar) sidebar.classList.remove('open');
    if (backdrop) backdrop.classList.remove('active');
}

function navigateTo(viewId) {
    // Automatically close mobile navigation drawer
    closeSidebar();

    // Update navigation sidebar active state
    document.querySelectorAll('.nav-item').forEach(el => {
        if (el.getAttribute('data-view') === viewId) {
            el.classList.add('active');
        } else {
            el.classList.remove('active');
        }
    });

    // Update section visibility
    document.querySelectorAll('.view-section').forEach(sec => {
        sec.classList.remove('active');
    });

    const targetSec = document.getElementById(`view-${viewId}`);
    if (targetSec) {
        targetSec.classList.add('active');
    }

    // Update topbar titles
    const titles = {
        'dashboard': { title: 'Dashboard', sub: 'Monitor financial transactions and identify suspicious activity using explainable AI.' },
        'analyze': { title: 'Initiate Financial Transaction', sub: 'Academic fraud detection prototype with automatic behavioral profiling & ML fraud security.' },
        'result': { title: 'Transaction Analysis Result', sub: 'Fraud risk assessment, automatically derived factors, XAI feature attributions, and GPT security summary.' },
        'transactions': { title: 'Transaction History', sub: 'Search, filter, and review stored transaction risk reports.' },
        'xai': { title: 'Explainable AI (XAI)', sub: 'Multi-modal feature fusion breakdown and model evaluation performance.' },
        'dataset': { title: 'Dataset & Model Evaluation', sub: 'Authentic Kaggle IEEE-CIS Fraud Detection dataset statistics, 6 multi-modal feature groups, and academic model benchmarks.' },
        'chat': { title: 'AI Assistant', sub: 'Interactive GPT explanation assistant for financial security queries.' },
        'about': { title: 'About NeuroFinance GPT', sub: 'Academic system architecture and anti-false-positive design principles.' }
    };

    if (titles[viewId]) {
        document.getElementById('topbar-title').textContent = titles[viewId].title;
        document.getElementById('topbar-subtitle').textContent = titles[viewId].sub;
    }

    // Refresh specific view data if needed
    if (viewId === 'dashboard') {
        loadDashboardData();
    } else if (viewId === 'transactions') {
        fetchTransactions();
    } else if (viewId === 'dataset') {
        loadDatasetPage();
    } else if (viewId === 'analyze' && !window._loadingScenario) {
        if (typeof resetBankingForm === 'function') {
            resetBankingForm();
        }
    }
}

// Indian Currency Formatter (₹)
function formatINR(amount) {
    const num = parseFloat(amount) || 0;
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 2
    }).format(num);
}

// Badge Helper
function getRiskBadgeHTML(level) {
    if (level === 'LOW RISK') {
        return `<span class="badge badge-safe">🟢 LOW RISK</span>`;
    } else if (level === 'MEDIUM RISK') {
        return `<span class="badge badge-medium">🟡 MEDIUM RISK</span>`;
    } else {
        return `<span class="badge badge-high">🔴 HIGH RISK</span>`;
    }
}

// Load Model Evaluation Metrics
async function loadModelMetrics() {
    try {
        const res = await fetch('/api/metrics');
        const json = await res.json();
        if (json.status === 'success') {
            const m = json.data;
            document.getElementById('metric-accuracy').textContent = m.accuracy + '%';
            document.getElementById('metric-precision').textContent = m.precision + '%';
            document.getElementById('metric-recall').textContent = m.recall + '%';
            document.getElementById('metric-f1').textContent = m.f1_score + '%';
        }
    } catch (e) {
        console.error('Failed to load metrics', e);
    }
}

// Transaction Detail Modal Handlers
async function openTransactionModal(txId) {
    try {
        const res = await fetch(`/api/transactions/${txId}`);
        const json = await res.json();
        if (json.status === 'success') {
            const tx = json.data;
            document.getElementById('modal-tx-id').textContent = `Transaction ${tx.transaction_id}`;
            
            const xaiFactors = tx.feature_importance_json ? JSON.parse(tx.feature_importance_json) : [];
            let xaiHTML = '';
            xaiFactors.forEach(f => {
                const color = f.direction === 'Risk' ? '#DC2626' : '#16A34A';
                xaiHTML += `
                    <div style="margin-bottom: 8px; font-size: 13px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom: 2px;">
                            <span>${f.feature}</span>
                            <span style="font-weight: 700; color: ${color};">${f.impact}% (${f.direction})</span>
                        </div>
                    </div>
                `;
            });

                const isDemoRecord = (tx.is_demo === 1 || (tx.transaction_id && (tx.transaction_id.includes('HIST') || tx.transaction_id.startsWith('TXN-2026-908'))));
                const recordTypeBadge = isDemoRecord
                    ? '<span class="badge" style="background:#FEF3C7; color:#92400E; font-weight:700;">DEMO DATA RECORD</span>'
                    : '<span class="badge" style="background:#DCFCE7; color:#16A34A; font-weight:700;">LIVE NEW TRANSACTION</span>';
                const tsDisplay = tx.transaction_timestamp || `${tx.date} ${tx.time}`;

                document.getElementById('modal-body-content').innerHTML = `
                <div class="modal-amount-header">
                    <div>
                        <div style="font-size: 12px; color: var(--color-text-muted);">Amount</div>
                        <div style="font-size: 24px; font-weight: 800; color: var(--color-primary);">${formatINR(tx.amount)}</div>
                    </div>
                    <div class="modal-amount-right">
                        ${getRiskBadgeHTML(tx.risk_level)}
                        <div style="font-size: 14px; font-weight: 700; margin-top: 4px;">${tx.risk_score !== undefined && tx.risk_score !== null ? tx.risk_score : tx.fraud_probability}/100 Risk Score</div>
                        <div style="font-size: 12px; color: var(--color-text-muted);">(${tx.fraud_probability}% Fraud Probability)</div>
                    </div>
                </div>

                <div class="modal-grid-2">
                    <div><strong>Record Classification:</strong> ${recordTypeBadge}</div>
                    <div><strong>Application Timestamp:</strong> <code>${tsDisplay}</code></div>
                    <div><strong>Customer Account:</strong> ${tx.customer_id || 'CUST-001'}</div>
                    <div><strong>Recipient:</strong> ${tx.recipient || 'General Merchant'}</div>
                    <div><strong>Transaction Type:</strong> ${tx.transaction_type}</div>
                    <div><strong>Location:</strong> ${tx.location} ${tx.unusual_location ? '<span style="color:#DC2626;">(Anomalous ⚠️)</span>' : '(Verified Home)'}</div>
                    <div><strong>Device:</strong> ${tx.device_type} ${tx.new_device ? '<span style="color:#DC2626;">(New Device ⚠️)</span>' : '(Known Device)'}</div>
                    <div><strong>Customer Historical Avg:</strong> ${formatINR(tx.customer_average_amount)}</div>
                    <div class="modal-grid-full"><strong>Payment Remarks:</strong> ${tx.description || 'Standard payment'}</div>
                </div>

                <div style="margin-bottom: 20px;">
                    <strong style="font-size: 14px; display: block; margin-bottom: 8px;">Explainable AI Impact Factors:</strong>
                    ${xaiHTML || 'No XAI data'}
                </div>

                <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: var(--radius-md); padding: 16px; font-size: 13px; color: #1E40AF;">
                    <strong>GPT Explanation:</strong><br>
                    ${tx.explanation || 'No summary available.'}
                </div>
            `;
            
            document.getElementById('detail-modal').classList.add('active');
        }
    } catch (e) {
        alert('Could not fetch transaction details.');
    }
}

function closeModal() {
    document.getElementById('detail-modal').classList.remove('active');
}

function closeModalOnOverlay(e) {
    if (e.target.id === 'detail-modal') {
        closeModal();
    }
}
