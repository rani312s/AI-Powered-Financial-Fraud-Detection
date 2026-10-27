// NeuroFinance GPT - Dashboard Analytics & Chart.js Integration

let pieChartInstance = null;
let barChartInstance = null;

async function loadDashboardData() {
    try {
        const res = await fetch('/api/stats');
        const json = await res.json();
        if (json.status === 'success') {
            const data = json.data;

            // 1. Update Stats KPI Cards
            document.getElementById('stat-total').textContent = data.total_transactions.toLocaleString();
            document.getElementById('stat-safe').textContent = data.safe_transactions.toLocaleString();
            document.getElementById('stat-suspicious').textContent = data.suspicious_transactions.toLocaleString();
            document.getElementById('stat-avg-risk').textContent = data.average_risk_score + ' / 100';

            // 2. Render Recent Transactions Table
            renderRecentTable(data.recent_transactions);

            // 3. Render Charts
            renderCharts(data);
        }
    } catch (e) {
        console.error('Failed to load dashboard data:', e);
    }
}

function renderRecentTable(transactions) {
    const tbody = document.getElementById('recent-tx-table-body');
    if (!transactions || transactions.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding: 24px;">No transactions recorded yet.</td></tr>`;
        return;
    }

    let html = '';
    transactions.forEach(tx => {
        const isDemo = (tx.is_demo === 1 || (tx.transaction_id && (tx.transaction_id.includes('HIST') || tx.transaction_id.startsWith('TXN-2026-908'))));
        const badge = isDemo 
            ? '<span class="badge" style="background:#FEF3C7; color:#92400E; font-size:10px; font-weight:700;">DEMO</span>' 
            : '<span class="badge" style="background:#DCFCE7; color:#16A34A; font-size:10px; font-weight:700;">LIVE</span>';
        const ts = tx.transaction_timestamp || `${tx.date} ${tx.time}`;

        html += `
            <tr>
                <td><strong style="font-family: monospace;">${tx.transaction_id}</strong></td>
                <td><strong>${ts}</strong></td>
                <td><strong>${formatINR(tx.amount)}</strong></td>
                <td>${tx.transaction_type}</td>
                <td><strong>${tx.risk_score !== undefined && tx.risk_score !== null ? tx.risk_score : tx.fraud_probability} / 100</strong> <span style="font-size:11px; color:#64748B;">(${tx.fraud_probability}%)</span></td>
                <td>${badge}</td>
                <td>${getRiskBadgeHTML(tx.risk_level)}</td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="openTransactionModal('${tx.transaction_id}')">
                        Details
                    </button>
                </td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

function renderCharts(data) {
    const safeCount = data.safe_transactions;
    const suspCount = data.suspicious_transactions;
    const dist = data.distribution || {};

    // Donut Chart: Safe vs Suspicious
    const ctxPie = document.getElementById('chart-pie-ratio').getContext('2d');
    if (pieChartInstance) pieChartInstance.destroy();
    
    pieChartInstance = new Chart(ctxPie, {
        type: 'doughnut',
        data: {
            labels: ['Safe Transactions', 'Suspicious / Fraud'],
            datasets: [{
                data: [safeCount, suspCount],
                backgroundColor: ['#16A34A', '#DC2626'],
                borderWidth: 2,
                borderColor: '#FFFFFF'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }
            },
            cutout: '68%'
        }
    });

    // Bar Chart: Risk Distribution
    const ctxBar = document.getElementById('chart-bar-risk').getContext('2d');
    if (barChartInstance) barChartInstance.destroy();

    barChartInstance = new Chart(ctxBar, {
        type: 'bar',
        data: {
            labels: ['Low Risk (0-30%)', 'Medium Risk (31-70%)', 'High Risk (71-100%)'],
            datasets: [{
                label: 'Transaction Count',
                data: [
                    dist['LOW RISK'] || 0,
                    dist['MEDIUM RISK'] || 0,
                    dist['HIGH RISK'] || 0
                ],
                backgroundColor: ['#16A34A', '#F59E0B', '#DC2626'],
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true, ticks: { stepSize: 1 } }
            }
        }
    });
}

// Faculty Demo Scenario Loader
async function loadScenario(scenarioKey) {
    try {
        const res = await fetch('/api/scenarios');
        const json = await res.json();
        if (json.status === 'success' && json.data[scenarioKey]) {
            const sc = json.data[scenarioKey].data;
            const scenarioInfo = json.data[scenarioKey];

            // Prevent navigateTo('analyze') from auto-wiping the scenario data
            window._loadingScenario = true;
            navigateTo('analyze');
            window._loadingScenario = false;

            // Mark as Demo Data
            const isDemoEl = document.getElementById('input-is-demo');
            if (isDemoEl) isDemoEl.value = "1";

            // Show Demo Scenario Notice Banner
            const banner = document.getElementById('demo-scenario-banner');
            if (banner) {
                banner.style.display = 'flex';
                const bannerTitle = document.getElementById('demo-banner-title');
                const bannerDesc = document.getElementById('demo-banner-desc');
                if (bannerTitle) bannerTitle.textContent = `DEMO SCENARIO: ${scenarioInfo.title}`;
                if (bannerDesc) bannerDesc.textContent = `${scenarioInfo.description} (Demo Mode Active). Click 'Clear / Fresh Live Transaction' to analyze a new real transaction.`;
            }

            // Set Customer Dropdown
            const custSelect = document.getElementById('input-customer');
            if (custSelect && sc.customer_id) {
                custSelect.value = sc.customer_id;
                if (typeof onCustomerSelectChange === 'function') {
                    onCustomerSelectChange();
                }
            }

            // Fill standard banking inputs
            if (document.getElementById('input-amount')) {
                document.getElementById('input-amount').value = sc.amount;
            }
            if (document.getElementById('input-type')) {
                document.getElementById('input-type').value = sc.transaction_type;
            }
            if (document.getElementById('input-recipient')) {
                document.getElementById('input-recipient').value = sc.recipient || '';
            }
            if (document.getElementById('input-description')) {
                document.getElementById('input-description').value = sc.description || '';
            }

            // Optional custom date/time from scenario
            if (document.getElementById('input-date')) {
                document.getElementById('input-date').value = '';
            }
            if (document.getElementById('input-time')) {
                document.getElementById('input-time').value = sc.simulated_time || '';
            }

            // Fill optional faculty simulation overrides
            const drawer = document.getElementById('simulation-details-drawer');
            const simDevice = document.getElementById('input-sim-device');
            const simLocation = document.getElementById('input-sim-location');
            const simTime = document.getElementById('input-sim-time');

            if (simDevice) simDevice.value = sc.simulated_device || '';
            if (simLocation) simLocation.value = sc.simulated_location || '';
            if (simTime) simTime.value = sc.simulated_time || '';

            // Open the drawer if simulation overrides are active (e.g. Scenario 2) so faculty can inspect
            if (drawer) {
                if (sc.simulated_device || sc.simulated_location || sc.simulated_time) {
                    drawer.open = true;
                } else {
                    drawer.open = false;
                }
            }

            // Smoothly scroll to the form
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    } catch (e) {
        console.error('Failed to load scenario:', e);
    }
}
