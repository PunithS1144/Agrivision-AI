# 🌱 AgriVision Plantix AI — Precision Agronomic Platform (Phase 2 Upgrade)

AgriVision Plantix AI is an enterprise-grade agricultural intelligence application. Phase 2 introduces comprehensive upgrades to the core agricultural intelligence pipeline, computer vision image quality validation, differential pathology classification, regulatory-compliant 4-pillar treatment guidance, multi-unit fertilizer calculation, 7-day agro-meteorological forecasting with hourly spray windows, multi-farm plot activity logging, searchable diagnosis history with CSV export, and alert notifications.

---

## 🚀 Phase 2 Core Feature Upgrades

### 1. 📷 Advanced AI Crop Diagnosis & Quality Gatekeeper
- **Multi-Source Capture:** Dedicated in-app **Camera** capture and **Gallery** upload with live client-side preview.
- **5-Point Image Quality Verification:**
  - **Blur Detection:** Laplacian gradient variance analysis ($\nabla^2 I$). Rejects out-of-focus imagery.
  - **Underexposure Check:** Detects night/deep canopy low-light shots (mean luminance $< 38$).
  - **Overexposure / Glare Check:** Detects washed-out direct midday sun reflections (mean luminance $> 230$).
  - **Non-Plant Spectral Filter:** Uses the Excess Green Index ($2G - R - B$) to verify presence of actual plant foliage, rejecting synthetic materials, indoor surfaces, or skin.
  - **Framing & Proximity Check:** Verifies that the diseased leaf occupies at least 30% of the viewfinder.
- **Actionable Retake Instructions:** If any check fails, returns specific guidance on distance, lighting, and focus locking.

### 2. 🔬 Diagnostic Differential Diagnosis & Severity Grading
- **Primary Pathology:** Pathogen type, symptoms, disease cause, and model confidence score.
- **Differential Alternatives:** Displays top alternative candidate diagnoses with confidence offsets and differentiating symptom indicators (e.g., distinguishing Early Blight concentric rings from Septoria pycnidia or Bacterial Spot angular water-soaking).
- **Follow-up Monitoring:** Prescribes specific inspection protocols (e.g., check at Day 5 for lesion margin drying).

### 3. 🛡️ Regulatory-Compliant 4-Pillar Treatment Advisory
- **🧪 Chemical Treatment:**
  - Active ingredient with CIBRC / University approved dosages (e.g. Mancozeb 75% WP @ 2.5 g/L).
  - Pre-Harvest Interval (PHI) in days.
  - Fungicide Resistance Action Committee (FRAC) codes (e.g. FRAC M03, FRAC 11, FRAC 27) with rotation rules.
  - Required Personal Protective Equipment (PPE) safety gear (N95 mask, nitrile gloves, eye goggles).
- **🌱 Biological Control:** Antagonistic bio-agents (*Trichoderma harzianum*, *Bacillus subtilis*, *Pseudomonas fluorescens*).
- **🍃 Organic Control:** Cold-pressed Neem Oil (10,000 ppm @ 2 ml/L), NSKE 5%, Panchagavya 3%.
- **🛡️ Cultural Practices:** Strict 3-year crop rotation, vine staking, sanitizing shears with 70% alcohol.

### 4. ⚖️ Multi-Unit Precision Fertilizer & Nutrient Calculator
- **Land Measurement Units:** Automatic conversions across **Acres (1.0 ac)**, **Hectares (2.47 ac)**, **Gunthas (0.025 ac)**, and **Bighas (0.625 ac)**.
- **Physiological Growth Stages:** Basal transplanting, vegetative tillering, flowering & fruit setting, and maturity.
- **Target Yield Scaling:** Optional target yield input (tons/unit) for high-density commercial production.
- **Commercial Bags Calculation:** Computes exact 45kg bags of **Urea (46% N)**, 50kg bags of **DAP (18-46-0)**, and 50kg bags of **MOP (60% K2O)**.
- **3-Stage Split Calendar:** Detailed soil placement vs. fertigation methods and agronomic rationale.
- **Cost Transparency:** Indicative central government subsidized retail price calculation with disclaimer.

### 5. 🌤️ 7-Day Agro-Meteorological Weather & Spraying Window
- Live Open-Meteo satellite/radar feed with rural fallback.
- **Hourly 24-Hour Spray Suitability Meter:** Evaluates hourly wind speed, rain probability, temperature, and relative humidity.
- **Fungal Epidemic Alert:** Alerts growers when relative humidity $> 75\%$ and temperature is between 18-27°C.
- **7-Day Forward Forecast Cards.**

### 6. 🏡 Multi-Farm & Crop Activity Log
- Switch between multiple farms (e.g., Green Valley Organic Plot vs. Shantinagar Block).
- Track field plots by variety, sowing date, and area.
- Log field operations: Spraying, Fertigation, Irrigation, Weeding, Harvesting, and Pruning.

### 7. 📜 Diagnosis History, Search & CSV Export
- Search past diagnoses by crop name, disease, or symptom keywords.
- Filter by crop type and toggle date sorting (newest/oldest).
- Delete obsolete diagnosis records.
- One-click **Export to CSV** for farm record-keeping and insurance claims (`/api/diagnoses/export?format=csv`).

### 8. 🔔 Farm Alerts & Notifications
- Outbreak warnings (e.g. Fall Armyworm in adjacent taluks).
- Weather alerts (humidity, wind drift, rain wash-out).
- Scheduled diagnosis follow-ups and fertigation reminders.

---

## 🧪 Automated Test Suite

Run the full test suite (15 unit & integration test cases):
```bash
python -m unittest discover -s tests -p "test_*.py"
```
```text
...............
----------------------------------------------------------------------
Ran 15 tests in 10.657s

OK
```

---

## 🏃 Running the Application

```bash
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in any browser.
