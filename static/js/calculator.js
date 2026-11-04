/* Precision Fertilizer & Dosage Calculator Controller (Phase 2 Enhanced) */

const CalculatorController = {
    init() {
        const cropSelect = document.getElementById('calc-crop-select');
        const acreageInput = document.getElementById('calc-acreage-input');
        const acreageSlider = document.getElementById('calc-acreage-slider');
        const unitSelect = document.getElementById('calc-unit-select');
        const stageSelect = document.getElementById('calc-stage-select');
        const yieldInput = document.getElementById('calc-yield-input');
        const soilN = document.getElementById('calc-soil-n');
        const soilP = document.getElementById('calc-soil-p');
        const soilK = document.getElementById('calc-soil-k');
        const calculateBtn = document.getElementById('run-calc-btn');

        if (acreageSlider && acreageInput) {
            acreageSlider.addEventListener('input', (e) => {
                acreageInput.value = e.target.value;
                this.calculatePlan();
            });

            acreageInput.addEventListener('input', (e) => {
                acreageSlider.value = e.target.value;
                this.calculatePlan();
            });
        }

        [cropSelect, unitSelect, stageSelect, soilN, soilP, soilK].forEach(el => {
            if (el) el.addEventListener('change', () => this.calculatePlan());
        });

        if (yieldInput) yieldInput.addEventListener('input', () => this.calculatePlan());
        if (calculateBtn) calculateBtn.addEventListener('click', () => this.calculatePlan());

        // Initial default calculation
        this.calculatePlan();
    },

    async calculatePlan() {
        const cropSelect = document.getElementById('calc-crop-select');
        const acreageInput = document.getElementById('calc-acreage-input');
        const unitSelect = document.getElementById('calc-unit-select');
        const stageSelect = document.getElementById('calc-stage-select');
        const yieldInput = document.getElementById('calc-yield-input');
        const soilN = document.getElementById('calc-soil-n');
        const soilP = document.getElementById('calc-soil-p');
        const soilK = document.getElementById('calc-soil-k');

        const cropName = cropSelect ? cropSelect.value : 'Tomato';
        const area = acreageInput ? parseFloat(acreageInput.value) || 1.0 : 1.0;
        const unit = unitSelect ? unitSelect.value : 'Acres';
        const stage = stageSelect ? stageSelect.value : 'All Stages';
        const targetYield = yieldInput ? parseFloat(yieldInput.value) || 0 : 0;

        const payload = {
            crop_name: cropName,
            acreage: area,
            unit: unit,
            growth_stage: stage,
            target_yield: targetYield > 0 ? targetYield : null,
            soil_test: {
                nitrogen: soilN ? soilN.value : 'Medium',
                phosphorus: soilP ? soilP.value : 'Medium',
                potassium: soilK ? soilK.value : 'Medium'
            }
        };

        try {
            const res = await fetch('/api/fertilizer/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (res.ok && data.success) {
                this.renderPlan(data.plan);
            } else {
                Components.showToast(data.error || 'Failed to calculate fertilizer plan', 'warning');
            }
        } catch (err) {
            console.error('Fertilizer calculation error:', err);
        }
    },

    renderPlan(plan) {
        // Summary Cards
        const ureaKg = document.getElementById('plan-urea-kg');
        const ureaBags = document.getElementById('plan-urea-bags');
        const dapKg = document.getElementById('plan-dap-kg');
        const dapBags = document.getElementById('plan-dap-bags');
        const mopKg = document.getElementById('plan-mop-kg');
        const mopBags = document.getElementById('plan-mop-bags');
        const totalCost = document.getElementById('plan-total-cost');
        const normalizedArea = document.getElementById('plan-norm-area');

        if (ureaKg) ureaKg.textContent = `${plan.commercial_fertilizers.urea_kg} kg`;
        if (ureaBags) ureaBags.textContent = `(~${plan.commercial_fertilizers.urea_bags} bags of 45kg)`;

        if (dapKg) dapKg.textContent = `${plan.commercial_fertilizers.dap_kg} kg`;
        if (dapBags) dapBags.textContent = `(~${plan.commercial_fertilizers.dap_bags} bags of 50kg)`;

        if (mopKg) mopKg.textContent = `${plan.commercial_fertilizers.mop_kg} kg`;
        if (mopBags) mopBags.textContent = `(~${plan.commercial_fertilizers.mop_bags} bags of 50kg)`;

        if (totalCost) totalCost.textContent = `₹${plan.estimated_cost_inr.toLocaleString('en-IN')}`;
        if (normalizedArea) normalizedArea.textContent = `Computed for ${plan.input_area} ${plan.input_unit} (${plan.normalized_acres} standard acres)`;

        // Methodology & Explanation
        const explanationEl = document.getElementById('plan-explanation-text');
        if (explanationEl) explanationEl.textContent = plan.calculation_explanation;

        const disclaimerEl = document.getElementById('plan-cost-disclaimer');
        if (disclaimerEl) disclaimerEl.textContent = plan.cost_disclaimer;

        // Render Application Schedule Table
        const scheduleBody = document.getElementById('plan-schedule-body');
        if (scheduleBody) {
            scheduleBody.innerHTML = plan.schedule.map(s => `
                <tr style="border-bottom: 1px solid var(--border-color-subtle);">
                    <td style="padding: 12px 14px; font-weight: 600;">
                        <div>${s.stage}</div>
                        <small style="color: var(--text-muted);">${s.timing}</small>
                    </td>
                    <td style="padding: 12px 14px; color: var(--primary-700); font-weight: 700;">${s.urea_kg} kg</td>
                    <td style="padding: 12px 14px; color: var(--primary-700); font-weight: 700;">${s.dap_kg} kg</td>
                    <td style="padding: 12px 14px; color: var(--primary-700); font-weight: 700;">${s.mop_kg} kg</td>
                    <td style="padding: 12px 14px; font-size: 13px; color: var(--text-secondary);">
                        <div>${s.method}</div>
                        <div style="font-size: 12px; color: var(--text-muted); margin-top: 2px;"><em>${s.agronomic_rationale}</em></div>
                    </td>
                </tr>
            `).join('');
        }
    }
};

window.CalculatorController = CalculatorController;
