// NeuroFinance GPT - Banking Transaction Analyze & Result Logic

let loadedCustomers = [];

// Initialize Customer Profiles & Form Setup
async function initCustomerProfiles() {
    try {
        const res = await fetch('/api/customers');
        const json = await res.json();
        if (json.status === 'success' && json.data) {
            loadedCustomers = json.data;
            populateCustomerDropdown(loadedCustomers);
            updateCustomerCard(loadedCustomers[0]);
        }
    } catch (e) {
        console.error('Failed to load customer profiles:', e);
    }
}

function populateCustomerDropdown(customers) {
    const select = document.getElementById('input-customer');
    if (!select) return;
    
    select.innerHTML = '';

    const liveGroup = document.createElement('optgroup');
    liveGroup.label = "Live Test Account (Interactive)";

    const demoGroup = document.createElement('optgroup');
    demoGroup.label = "Faculty Demonstration Scenarios (Demo Data)";

    customers.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.customer_id;
        if (c.is_demo === 0 || c.customer_id === 'LIVE-USER') {
            opt.textContent = `[LIVE TEST ACCOUNT] ${c.name} (${c.account_number}) • Interactive Testing`;
            liveGroup.appendChild(opt);
        } else {
            opt.textContent = `[DEMO DATA] ${c.name} (${c.account_number} — ${c.account_type}) • ${c.home_location}`;
            demoGroup.appendChild(opt);
        }
    });

    if (liveGroup.children.length > 0) select.appendChild(liveGroup);
    if (demoGroup.children.length > 0) select.appendChild(demoGroup);

    // Default to LIVE-USER for live transaction submission
    const liveCust = customers.find(c => c.customer_id === 'LIVE-USER');
    if (liveCust) {
        select.value = liveCust.customer_id;
        updateCustomerCard(liveCust);
    } else if (customers.length > 0) {
        updateCustomerCard(customers[0]);
    }
}

function onCustomerSelectChange() {
    const select = document.getElementById('input-customer');
    const custId = select.value;
    const cust = loadedCustomers.find(c => c.customer_id === custId) || loadedCustomers[0];
    if (cust) {
        updateCustomerCard(cust);
    }
}

function updateCustomerCard(cust) {
    if (!cust) return;
    const title = document.getElementById('cust-card-title');
    const status = document.getElementById('cust-card-status');
    const bal = document.getElementById('cust-card-balance');
    const loc = document.getElementById('cust-card-location');
    const avg = document.getElementById('cust-card-avg');
    const dev = document.getElementById('cust-card-devices');

    const isLive = (cust.is_demo === 0 || cust.customer_id === 'LIVE-USER');

    if (title) {
        if (isLive) {
            title.innerHTML = `<span class="badge" style="background:#DCFCE7; color:#16A34A; margin-right:6px; font-weight:700;">LIVE PROFILE</span> ${cust.name} (${cust.account_number})`;
        } else {
            title.innerHTML = `<span class="badge" style="background:#FEF3C7; color:#92400E; margin-right:6px; font-weight:700;">DEMO DATA</span> ${cust.name} — ${cust.account_type}`;
        }
    }
    if (bal) bal.textContent = formatINR(cust.balance || 250000);
    if (loc) loc.textContent = isLive ? 'Local Region, India (User Location)' : (cust.home_location || 'Mumbai, MH');
    if (avg) avg.textContent = isLive ? 'Computed dynamically from live transaction history' : `${formatINR(cust.baseline_avg_amount || 3000)} (Typical Spend)`;
    
    if (dev) {
        const devices = Array.isArray(cust.registered_devices) ? cust.registered_devices.join(', ') : 'Web Browser (Chrome)';
        dev.textContent = devices;
    }

    if (status) {
        if (cust.prior_fraud_record === 1) {
            status.className = 'badge badge-medium';
            status.textContent = 'Prior Alert on File [DEMO]';
        } else {
            status.className = 'badge badge-safe';
            status.textContent = isLive ? 'Active Live Standing' : 'Clean Account History';
        }
    }
}

// Handle Form Submission (Clean Banking Form)
async function handleAnalyzeSubmit(e) {
    if (e) e.preventDefault();

    const customerId = document.getElementById('input-customer').value || 'CUST-001';
    const amountVal = parseFloat(document.getElementById('input-amount').value);
    const txnType = document.getElementById('input-type').value;
    const recipient = document.getElementById('input-recipient').value.trim();
    const description = document.getElementById('input-description').value.trim();

    // Form date/time inputs (optional - if left blank backend uses current application time)
    const dateVal = document.getElementById('input-date') ? document.getElementById('input-date').value.trim() : '';
    const timeVal = document.getElementById('input-time') ? document.getElementById('input-time').value.trim() : '';
    const isDemoVal = document.getElementById('input-is-demo') ? parseInt(document.getElementById('input-is-demo').value || '0', 10) : 0;

    // Advanced Demonstration Simulation Overrides (optional)
    const simDevice = document.getElementById('input-sim-device') ? document.getElementById('input-sim-device').value.trim() : '';
    const simLocation = document.getElementById('input-sim-location') ? document.getElementById('input-sim-location').value.trim() : '';
    const simTime = document.getElementById('input-sim-time') ? document.getElementById('input-sim-time').value.trim() : '';

    // Validation
    if (isNaN(amountVal) || amountVal <= 0) {
        alert("Please enter a valid positive transaction amount.");
        return;
    }

    if (!recipient) {
        alert("Please enter the recipient or merchant name.");
        return;
    }

    const payload = {
        customer_id: customerId,
        amount: amountVal,
        currency: 'INR',
        transaction_type: txnType,
        recipient: recipient,
        description: description,
        is_demo: isDemoVal
    };

    if (dateVal) payload.date = dateVal;
    if (timeVal) payload.time = timeVal;
    if (simDevice) payload.simulated_device = simDevice;
    if (simLocation) payload.simulated_location = simLocation;
    if (simTime) payload.simulated_time = simTime;

    // Trigger Professional Multi-Step Progress Overlay Animation
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.classList.add('active');

    const steps = [
        document.getElementById('step-1'),
        document.getElementById('step-2'),
        document.getElementById('step-3'),
        document.getElementById('step-4')
    ];

    if (steps[0]) {
        steps.forEach((s, idx) => {
            if (s) {
                s.classList.remove('active');
                s.textContent = idx === 0 ? "✓ Validating banking payment details..." :
                                idx === 1 ? "⏳ Automatically deriving behavioral & contextual features..." :
                                idx === 2 ? "⏳ Running Machine Learning fraud classifier..." :
                                "⏳ Generating SHAP attributions & GPT security summary...";
            }
        });

        steps[0].classList.add('active');
        await new Promise(r => setTimeout(r, 300));
        steps[0].textContent = "✓ Validated banking payment inputs";
        
        if (steps[1]) {
            steps[1].classList.add('active');
            await new Promise(r => setTimeout(r, 350));
            steps[1].textContent = "✓ Extracted customer baselines & environmental signals";
        }

        if (steps[2]) steps[2].classList.add('active');
    }

    try {
        const res = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (steps[2]) steps[2].textContent = "✓ Evaluated fraud risk probability";
        if (steps[3]) {
            steps[3].classList.add('active');
            await new Promise(r => setTimeout(r, 400));
        }

        const json = await res.json();
        if (overlay) overlay.classList.remove('active');

        if (json.status === 'success') {
            displayAnalysisResult(json.data);
        } else {
            alert(`Analysis Error: ${json.message}`);
        }
    } catch (err) {
        if (overlay) overlay.classList.remove('active');
        alert(`Server Error: ${err.message}`);
    }
}

// Display Prediction Result with Automatically Derived Factors Breakdown
function displayAnalysisResult(data) {
    activeTransactionContext = data;

    // Log temporal pattern debug metrics for transparent auditing
    if (data.derived_factors && data.derived_factors.temporal_debug) {
        console.log('[Temporal Pattern Check Debug]', data.derived_factors.temporal_debug);
    }

    // Header info with record classification & actual application timestamp
    const ts = data.transaction_timestamp || `${data.date} ${data.time}`;
    const demoBadge = (data.is_demo === 1) 
        ? '<span class="badge" style="background:#FEF3C7; color:#92400E; margin-left:8px; font-weight:700;">DEMO DATA</span>'
        : '<span class="badge" style="background:#DCFCE7; color:#16A34A; margin-left:8px; font-weight:700;">LIVE NEW</span>';
    
    document.getElementById('res-tx-id').innerHTML = `${data.transaction_id} ${demoBadge}`;
    document.getElementById('res-amount').textContent = formatINR(data.amount);
    
    const payeeText = data.recipient ? `To: ${data.recipient}` : 'General Merchant';
    document.getElementById('res-meta').textContent = `${data.transaction_type} • ${payeeText} • ${data.location} • Timestamp: ${ts}`;
    
    // High-precision formatted probability string (never show plain 0% for low probabilities)
    const displayProb = data.fraud_prob_display || `${data.fraud_probability}%`;
    document.getElementById('res-risk-prob').textContent = displayProb;
    document.getElementById('res-prediction-text').textContent = data.prediction;

    // Risk Meter Styling with Model Risk Score (0–100)
    const box = document.getElementById('res-risk-box');
    const label = document.getElementById('res-risk-label');
    
    box.className = 'risk-meter-box';
    if (data.risk_level === 'HIGH RISK') {
        box.classList.add('high-risk');
        label.textContent = `🔴 ${data.risk_score}/100 • HIGH RISK`;
    } else if (data.risk_level === 'MEDIUM RISK') {
        box.classList.add('medium-risk');
        label.textContent = `🟡 ${data.risk_score}/100 • MEDIUM RISK`;
    } else {
        box.classList.add('low-risk');
        label.textContent = `🟢 ${data.risk_score}/100 • LOW RISK`;
    }

    // Anti-False-Positive Nuance Banner
    const nuanceNote = document.getElementById('res-nuance-note');
    const derived = data.derived_factors || {};
    const avgAmount = data.customer_average_amount || 1;
    const ratio = (data.amount / avgAmount).toFixed(1);

    if (data.amount > avgAmount * 2.5) {
        nuanceNote.innerHTML = `<strong>High-Value Legitimate Transaction Nuance (${ratio}x normal spend):</strong> High transaction amount alone does NOT mean fraud. Legitimate high-value payments (tuition, invoices, emergency medical) remain low risk when verified from trusted devices and familiar locations.`;
    } else {
        nuanceNote.textContent = "High transaction amount alone is not treated as proof of fraud. Multi-modal behavioral features and customer historical baselines are evaluated simultaneously.";
    }

    // Populate Key Metrics Distinction Cards
    const fraudProbEl = document.getElementById('dist-fraud-prob');
    if (fraudProbEl) {
        const rawNote = (data.raw_ann_probability !== undefined && data.raw_ann_probability !== null)
            ? `<span style="font-size: 11px; font-weight: 500; color: #64748B; margin-left: 6px; font-family: monospace;">(raw: ${Number(data.raw_ann_probability).toExponential(3)})</span>`
            : '';
        fraudProbEl.innerHTML = `${displayProb} ${rawNote}`;
    }

    const riskScoreEl = document.getElementById('dist-risk-score');
    if (riskScoreEl) riskScoreEl.textContent = `${data.risk_score} / 100 (${data.risk_level})`;

    const shapSumEl = document.getElementById('dist-shap-summary');
    if (shapSumEl) {
        if (data.feature_importance && data.feature_importance.length > 0) {
            const topF = data.feature_importance[0];
            const rawShapStr = topF.raw_shap !== undefined ? ` (&phi;: ${topF.raw_shap > 0 ? '+' : ''}${topF.raw_shap})` : '';
            shapSumEl.textContent = `${topF.impact}%${rawShapStr}`;
        } else {
            shapSumEl.textContent = 'Calculated';
        }
    }

    // Render Derived Factors Cards
    renderDerivedFactorsGrid(derived, data);

    // Render SHAP Feature Importance Bars
    renderXAIBarChart(data.feature_importance);

    // Render GPT Text
    document.getElementById('res-gpt-text').textContent = data.explanation;

    // Reinitialize lucide icons if available
    if (window.lucide) {
        lucide.createIcons();
    }

    // Switch view to result page
    navigateTo('result');
}

// Render the Automatically Derived Behavioral & Contextual Factor Cards
function renderDerivedFactorsGrid(derived, tx) {
    const container = document.getElementById('derived-factors-container');
    const badge = document.getElementById('derived-account-badge');
    const isLive = Boolean(tx.is_demo === 0 && (!derived.is_demo_data));

    if (badge && derived.customer_name) {
        const tag = isLive
            ? `<span class="badge" style="background:#DCFCE7; color:#16A34A; margin-left:6px; font-size:10px; font-weight:700;">LIVE TEST RECORD</span>`
            : `<span class="badge" style="background:#FEF3C7; color:#92400E; margin-left:6px; font-size:10px; font-weight:700;">DEMO DATA</span>`;
        badge.innerHTML = `Account: ${derived.customer_name} (${derived.account_number || tx.customer_id}) ${tag}`;
    }

    if (!container) return;

    const temporalDbg = derived.temporal_debug || (tx.debug_info ? tx.debug_info.temporal_analysis : null) || {};
    const patternSource = derived.temporal_pattern_source || (isLive ? 'Live customer historical pattern' : 'Demo historical pattern');
    const windowDesc = (temporalDbg.calculated_normal_window && temporalDbg.calculated_normal_window.window_description)
        ? temporalDbg.calculated_normal_window.window_description
        : (tx.typical_time === 1 ? 'Matches calculated active window' : 'Diverges from calculated active window');
    const histCount = temporalDbg.historical_transaction_count != null ? temporalDbg.historical_transaction_count : (tx.previous_transaction_count || 0);

    // Check if temporal pattern has sufficient historical records (N >= 2)
    const isTemporalNeutral = (tx.typical_time === -1 || derived.temporal_status === 'INSUFFICIENT_HISTORY' || histCount < 2);
    const isSpendingNeutral = isLive && (tx.previous_transaction_count === 0 || !tx.customer_average_amount || tx.customer_average_amount === 0);

    const cards = [
        {
            title: "Historical Spending Baseline (Rule-Based Contextual Check)",
            icon: "trending-up",
            value: isSpendingNeutral
                ? `${formatINR(tx.amount)}`
                : (isLive
                    ? `${formatINR(tx.amount)} (${(tx.amount / (tx.customer_average_amount || 1)).toFixed(1)}x of avg)`
                    : `${formatINR(tx.amount)} (${derived.amount_ratio || (tx.amount / (tx.customer_average_amount || 1)).toFixed(1)}x of avg)`),
            sub: isSpendingNeutral
                ? "New account — historical baseline not established (0 prior completed records)"
                : (isLive
                    ? `Dynamic historical average: ${formatINR(tx.customer_average_amount)}`
                    : `Customer historical baseline: ${formatINR(tx.customer_average_amount)} [DEMO DATA]`),
            isRisk: !isSpendingNeutral && (tx.amount > (tx.customer_average_amount * 3.5)),
            isNeutral: isSpendingNeutral,
            statusText: isSpendingNeutral
                ? "ℹ️ Historical Baseline Not Established"
                : ((tx.amount > (tx.customer_average_amount * 3.5)) ? `⚠️ Flagged: ${(tx.amount / tx.customer_average_amount).toFixed(1)}x Above Normal Baseline` : "✓ Within Expected Spending Profile")
        },
        {
            title: "Device Identity Check (Rule-Based Contextual Check)",
            icon: "smartphone",
            value: tx.device_type,
            sub: tx.new_device ? "Hardware unverified in registry" : (isLive ? "Prototype device context: Authenticated client session" : "Matched with registered customer hardware"),
            isRisk: tx.new_device === 1,
            isNeutral: false,
            statusText: tx.new_device === 1 ? "⚠️ Unrecognized / Brand New Device" : "✓ Verified Registered Device"
        },
        {
            title: "Geolocation Verification (Rule-Based Contextual Check)",
            icon: "map-pin",
            value: tx.location,
            sub: tx.unusual_location ? `Diverges from primary region (${derived.home_location || 'Home Region'})` : (isLive ? `Simulated location context: ${tx.location}` : `Matches primary region (${derived.home_location || tx.location})`),
            isRisk: tx.unusual_location === 1,
            isNeutral: false,
            statusText: tx.unusual_location === 1 ? "⚠️ Anomalous / Foreign IP Geolocation" : "✓ Region Verified"
        },
        {
            title: "Temporal Pattern Analysis (Rule-Based Contextual Check)",
            icon: "clock",
            value: isTemporalNeutral
                ? `${tx.time} — Temporal pattern not established`
                : (tx.typical_time === 0
                    ? `${tx.time} — Outside customer's usual transaction-time pattern`
                    : `${tx.time} — Within customer's usual transaction-time pattern`),
            sub: isTemporalNeutral
                ? `${patternSource} • Insufficient historical transactions (N=${histCount} past records)`
                : `${patternSource} • Normal window: ${windowDesc} (N=${histCount} past records)`,
            isRisk: (!isTemporalNeutral) && tx.typical_time === 0,
            isNeutral: isTemporalNeutral,
            statusText: isTemporalNeutral
                ? "ℹ️ Temporal Pattern Not Established"
                : (tx.typical_time === 0 ? "⚠️ Outside Usual Time Pattern" : "✓ Within Usual Time Pattern")
        },
        {
            title: "Historical Transaction Volume (Rule-Based Contextual Check)",
            icon: "history",
            value: `${tx.previous_transaction_count || 0} Past Transactions`,
            sub: `${tx.similar_transaction_count || 0} matching historical transactions (${tx.transaction_type})`,
            isRisk: false,
            isNeutral: (tx.previous_transaction_count || 0) === 0,
            statusText: (tx.previous_transaction_count || 0) > 0 ? "✓ Derived from Customer Database Records" : "ℹ️ New Account — 0 Prior Transactions"
        },
        {
            title: "Account Security Standing (Rule-Based Contextual Check)",
            icon: "shield",
            value: derived.previous_fraud_history === 1 ? "Security Alert on Record" : "Clean Security Standing",
            sub: derived.previous_fraud_history === 1 ? "Account experienced prior security incidents [DEMO DATA]" : "No previous fraud or chargeback alerts recorded",
            isRisk: derived.previous_fraud_history === 1,
            isNeutral: false,
            statusText: derived.previous_fraud_history === 1 ? "⚠️ Prior Account Flag on File" : "✓ Clean Security Record"
        }
    ];

    let html = '';
    cards.forEach(c => {
        const cardClass = c.isRisk ? 'flagged' : (c.isNeutral ? 'neutral-card' : 'verified');
        const badgeClass = c.isRisk ? 'status-badge-risk' : (c.isNeutral ? 'status-badge-neutral' : 'status-badge-safe');
        const customBadgeStyle = c.isNeutral ? 'style="background:#F1F5F9; color:#475569; border:1px solid #CBD5E1; font-weight:600;"' : '';
        
        html += `
            <div class="derived-card ${cardClass}">
                <div>
                    <div class="derived-card-top">
                        <span class="derived-card-title">
                            <i data-lucide="${c.icon}" style="width:14px; height:14px;"></i>
                            ${c.title}
                        </span>
                    </div>
                    <div class="derived-card-value">${c.value}</div>
                    <div class="derived-card-sub">${c.sub}</div>
                </div>
                <div>
                    <span class="derived-status-badge ${badgeClass}" ${customBadgeStyle}>${c.statusText}</span>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// Render SHAP Feature Importance Bars with Audited Risk-Increasing vs Risk-Reducing Grouping
function renderXAIBarChart(factors) {
    const container = document.getElementById('xai-bars-container');
    if (!factors || factors.length === 0) {
        container.innerHTML = '<p style="color:#64748B;">No feature attributions calculated.</p>';
        return;
    }

    const riskFactors = factors.filter(f => f.direction === 'Risk');
    const safeFactors = factors.filter(f => f.direction === 'Safe');

    const renderItems = (list, isRisk) => {
        if (!list || list.length === 0) {
            return `
                <div style="padding: 12px; background: #F8FAFC; border-radius: var(--radius-sm); border: 1px dashed var(--color-border); font-size: 12px; color: var(--color-text-muted);">
                    ${isRisk ? '✓ No significant risk-increasing factors detected.' : '✓ No strong risk-reducing features identified for this transaction.'}
                </div>
            `;
        }

        return list.map(f => {
            const fillClass = isRisk ? 'fill-risk' : 'fill-safe';
            const color = isRisk ? '#DC2626' : '#16A34A';
            const actionTag = isRisk ? '▲ Pushed Model Risk Higher' : '▼ Reduced Model Risk';
            const rawCol = f.raw_feature ? `<code style="font-size:10px; background:#F1F5F9; padding:2px 5px; border-radius:3px; color:#475569; margin-left:6px;">${f.raw_feature}</code>` : '';
            const rawShapVal = (f.raw_shap !== undefined && f.raw_shap !== null) 
                ? (f.raw_shap > 0 ? `+${f.raw_shap}` : `${f.raw_shap}`)
                : null;
            const rawShapDisplay = rawShapVal ? ` &bull; Raw &phi;: <code>${rawShapVal}</code>` : '';

            return `
                <div class="xai-factor-item" style="margin-bottom: 12px; background: #FFFFFF; border: 1px solid var(--color-border); border-radius: var(--radius-sm); padding: 12px 14px;">
                    <div class="xai-factor-header" style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 6px;">
                        <div>
                            <span style="font-weight: 700; font-size: 13px; color: var(--color-primary);">${f.feature}</span>
                            ${rawCol}
                            <div style="font-size: 11px; color: var(--color-text-muted); margin-top: 2px;">
                                ${actionTag}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <span style="color:${color}; font-weight:800; font-size: 14px;">${f.impact}%</span>
                            <div style="font-size: 10px; color: var(--color-text-muted); text-transform: uppercase;">SHAP Impact Share${rawShapDisplay}</div>
                        </div>
                    </div>
                    <div class="xai-bar-track" style="height: 8px; background: #E2E8F0; border-radius: 4px; overflow: hidden;">
                        <div class="xai-bar-fill ${fillClass}" style="width: ${Math.min(100, Math.max(8, f.impact * 2))}%; height: 8px;"></div>
                    </div>
                </div>
            `;
        }).join('');
    };

    container.innerHTML = `
        <div style="background: #F8FAFC; border: 1px solid var(--color-border); border-radius: var(--radius-sm); padding: 14px 16px; margin-bottom: 18px;">
            <div style="font-size: 13px; font-weight: 700; color: var(--color-primary); display: flex; align-items: center; gap: 6px; margin-bottom: 6px;">
                <i data-lucide="info" style="width: 15px; height: 15px; color: var(--color-secondary);"></i>
                <span>Explainable AI (ANN SHAP) Attribution & Normalization Formula</span>
            </div>
            <p style="font-size: 12px; color: #334155; line-height: 1.5; margin: 0 0 10px 0;">
                These percentages represent the <strong>relative influence share</strong> (SHAP decision attribution) exerted by each feature on the Artificial Neural Network (ANN) prediction for this specific transaction.
                <br>
                <strong style="color: #DC2626;">Crucial Distinction:</strong> SHAP contribution is <strong>NOT a probability</strong>. It represents the relative weight by which a feature moved the prediction from the neural network's base expected risk ($E[f(x)]$).
            </p>
            <div style="font-size: 11px; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 4px; padding: 10px 14px; font-family: monospace; color: #1E293B; margin-bottom: 8px;">
                <strong>ANN SHAP Normalization Formula:</strong><br>
                Relative SHAP Impact Share (%) = [ |&phi;<sub>i</sub>| / &sum;<sub>k &isin; Top</sub> |&phi;<sub>k</sub>| ] &times; 100%<br>
                <span style="color: #64748B; font-family: sans-serif; font-size: 10.5px;">Where &phi;<sub>i</sub> is the local Shapley value computed on the Artificial Neural Network: &phi;<sub>i</sub> &gt; 0 indicates Increased Model Risk, &phi;<sub>i</sub> &lt; 0 indicates Reduced Model Risk.</span>
            </div>
            <div style="font-size: 11px; color: #64748B; line-height: 1.4;">
                <em>Audit Rule: No individual feature proves that a transaction is safe or fraudulent. Feature codes strictly reflect official IEEE-CIS / Vesta dataset specifications (e.g., C-features are frequency counters, V-features are engineered relation scores, card3 is billing country code).</em>
            </div>
        </div>

        <!-- Group 1: Features Increasing Risk -->
        <div style="margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h4 style="font-size: 13px; font-weight: 700; color: #DC2626; display: flex; align-items: center; gap: 6px;">
                    <i data-lucide="trending-up" style="width: 14px; height: 14px;"></i>
                    <span>Features Increasing Fraud Risk</span>
                </h4>
                <span class="badge" style="background:#FEE2E2; color:#DC2626; font-size:11px; font-weight:700;">${riskFactors.length} Risk Driver${riskFactors.length !== 1 ? 's' : ''}</span>
            </div>
            ${renderItems(riskFactors, true)}
        </div>

        <!-- Group 2: Features Reducing Risk -->
        <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h4 style="font-size: 13px; font-weight: 700; color: #16A34A; display: flex; align-items: center; gap: 6px;">
                    <i data-lucide="shield-check" style="width: 14px; height: 14px;"></i>
                    <span>Risk-Reducing Features</span>
                </h4>
                <span class="badge" style="background:#DCFCE7; color:#16A34A; font-size:11px; font-weight:700;">${safeFactors.length} Risk-Reducing Feature${safeFactors.length !== 1 ? 's' : ''}</span>
            </div>
            ${renderItems(safeFactors, false)}
        </div>
    `;

    if (window.lucide) {
        lucide.createIcons();
    }
}

function resetBankingForm() {
    const form = document.getElementById('analyze-form');
    if (form) form.reset();
    
    // Reset hidden is_demo flag to 0
    const isDemoEl = document.getElementById('input-is-demo');
    if (isDemoEl) isDemoEl.value = "0";

    // Hide demo scenario banner
    const banner = document.getElementById('demo-scenario-banner');
    if (banner) banner.style.display = 'none';

    // Clear simulation overrides and custom date/time inputs
    if (document.getElementById('input-sim-device')) document.getElementById('input-sim-device').value = '';
    if (document.getElementById('input-sim-location')) document.getElementById('input-sim-location').value = '';
    if (document.getElementById('input-sim-time')) document.getElementById('input-sim-time').value = '';
    if (document.getElementById('input-date')) document.getElementById('input-date').value = '';
    if (document.getElementById('input-time')) document.getElementById('input-time').value = '';

    if (loadedCustomers.length > 0) {
        const liveCust = loadedCustomers.find(c => c.customer_id === 'LIVE-USER') || loadedCustomers[0];
        const custSelect = document.getElementById('input-customer');
        if (custSelect) custSelect.value = liveCust.customer_id;
        updateCustomerCard(liveCust);
    }
    const drawer = document.getElementById('simulation-details-drawer');
    if (drawer) drawer.open = false;
}

// Fetch Transactions Table for History View
async function fetchTransactions() {
    const search = document.getElementById('tx-search') ? document.getElementById('tx-search').value.trim() : '';
    const risk = document.getElementById('filter-risk') ? document.getElementById('filter-risk').value : '';
    const type = document.getElementById('filter-type') ? document.getElementById('filter-type').value : '';
    const recordType = document.getElementById('filter-record-type') ? document.getElementById('filter-record-type').value : '';

    const url = `/api/transactions?search=${encodeURIComponent(search)}&risk=${encodeURIComponent(risk)}&type=${encodeURIComponent(type)}&record_type=${encodeURIComponent(recordType)}`;
    
    try {
        const res = await fetch(url);
        const json = await res.json();
        if (json.status === 'success') {
            const tbody = document.getElementById('history-table-body');
            if (!tbody) return;

            if (json.data.length === 0) {
                tbody.innerHTML = `<tr><td colspan="10" style="text-align:center; padding: 24px;">No matching transactions found.</td></tr>`;
                return;
            }

            let html = '';
            json.data.forEach(tx => {
                const recipientText = tx.recipient ? `<br><span style="font-size:11px; color:#64748B;">To: ${tx.recipient}</span>` : '';
                const isDemoRecord = (tx.is_demo === 1 || (tx.transaction_id && (tx.transaction_id.includes('HIST') || tx.transaction_id.startsWith('TXN-2026-908'))));
                const recordTypeBadge = isDemoRecord
                    ? '<span class="badge" style="background:#FEF3C7; color:#92400E; font-size:10px; font-weight:700;">DEMO DATA</span>'
                    : '<span class="badge" style="background:#DCFCE7; color:#16A34A; font-size:10px; font-weight:700;">LIVE NEW</span>';
                const tsDisplay = tx.transaction_timestamp || `${tx.date} ${tx.time}`;

                html += `
                    <tr>
                        <td><strong style="font-family: monospace;">${tx.transaction_id}</strong></td>
                        <td><strong>${tsDisplay}</strong></td>
                        <td><strong>${formatINR(tx.amount)}</strong></td>
                        <td>${tx.transaction_type} ${recipientText}</td>
                        <td>${tx.location}</td>
                        <td>${tx.device_type} ${tx.new_device ? '<span style="color:#DC2626;">(New)</span>' : ''}</td>
                        <td><strong>${tx.risk_score !== undefined && tx.risk_score !== null ? tx.risk_score : tx.fraud_probability} / 100</strong> <span style="font-size:11px; color:#64748B;">(${tx.fraud_probability}%)</span></td>
                        <td>${recordTypeBadge}</td>
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
    } catch (e) {
        console.error('Failed to fetch transactions history:', e);
    }
}
