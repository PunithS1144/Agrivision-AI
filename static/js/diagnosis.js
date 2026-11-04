/* Crop Diagnosis & AI Screening Controller (Phase 3 Enhanced) */

const DiagnosisController = {
    selectedFile: null,

    init() {
        const fileInput = document.getElementById('leaf-file-input');
        const cameraInput = document.getElementById('leaf-camera-input');
        const dropzone = document.getElementById('diagnosis-dropzone');
        const diagnoseBtn = document.getElementById('run-diagnosis-btn');
        const resetBtn = document.getElementById('reset-diagnosis-btn');

        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                if (e.target.files && e.target.files[0]) this.handleFileSelection(e.target.files[0]);
            });
        }

        if (cameraInput) {
            cameraInput.addEventListener('change', (e) => {
                if (e.target.files && e.target.files[0]) this.handleFileSelection(e.target.files[0]);
            });
        }

        if (dropzone) {
            dropzone.addEventListener('click', (e) => {
                if (e.target.id === 'open-camera-btn' || e.target.closest('#open-camera-btn')) {
                    e.preventDefault();
                    e.stopPropagation();
                    SmartCamera.open((capturedFile, dataUrl, metrics) => {
                        this.handleSmartCameraCapture(capturedFile, dataUrl, metrics);
                    });
                    return;
                }
                if (fileInput) fileInput.click();
            });

            ['dragenter', 'dragover'].forEach(event => {
                dropzone.addEventListener(event, (e) => {
                    e.preventDefault();
                    dropzone.style.borderColor = 'var(--primary-600)';
                });
            });

            ['dragleave', 'drop'].forEach(event => {
                dropzone.addEventListener(event, (e) => {
                    e.preventDefault();
                    dropzone.style.borderColor = 'var(--primary-300)';
                });
            });

            dropzone.addEventListener('drop', (e) => {
                if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                    this.handleFileSelection(e.dataTransfer.files[0]);
                }
            });
        }

        if (diagnoseBtn) diagnoseBtn.addEventListener('click', () => this.submitDiagnosis());
        if (resetBtn) resetBtn.addEventListener('click', () => this.resetForm());

        // Setup treatment sub-tabs
        Components.setupTabs('#treatment-tabs-container', (tabKey) => {
            document.querySelectorAll('.treatment-tab-pane').forEach(p => p.style.display = 'none');
            const activePane = document.getElementById(`treatment-pane-${tabKey}`);
            if (activePane) activePane.style.display = 'block';
        });
    },

    handleFileSelection(file) {
        if (!file.type.startsWith('image/')) {
            Components.showToast('Please select a valid leaf image file (JPG, PNG, WEBP)', 'warning');
            return;
        }

        this.selectedFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            const preview = document.getElementById('leaf-preview-img');
            const placeholder = document.getElementById('upload-placeholder');
            const previewContainer = document.getElementById('preview-container');
            const diagnoseBtn = document.getElementById('run-diagnosis-btn');
            const qualityAlert = document.getElementById('diagnosis-quality-alert');
            const bboxBox = document.getElementById('symptom-bbox-overlay');

            if (preview && placeholder && previewContainer) {
                preview.src = e.target.result;
                placeholder.style.display = 'none';
                previewContainer.style.display = 'block';
                if (qualityAlert) qualityAlert.style.display = 'none';
                if (bboxBox) bboxBox.style.display = 'none';
                if (diagnoseBtn) diagnoseBtn.disabled = false;
            }
        };
        reader.readAsDataURL(file);
    },

    handleSmartCameraCapture(file, dataUrl, metrics) {
        this.selectedFile = file;
        const preview = document.getElementById('leaf-preview-img');
        const placeholder = document.getElementById('upload-placeholder');
        const previewContainer = document.getElementById('preview-container');
        const diagnoseBtn = document.getElementById('run-diagnosis-btn');
        const qualityAlert = document.getElementById('diagnosis-quality-alert');
        const bboxBox = document.getElementById('symptom-bbox-overlay');

        if (preview && placeholder && previewContainer) {
            preview.src = dataUrl;
            placeholder.style.display = 'none';
            previewContainer.style.display = 'block';
            if (qualityAlert) qualityAlert.style.display = 'none';
            if (bboxBox) bboxBox.style.display = 'none';
            if (diagnoseBtn) diagnoseBtn.disabled = false;
        }

        Components.showToast(`📸 Leaf captured! Smart Camera Score: ${metrics.overallQuality}%`, 'success');
    },

    async submitDiagnosis() {
        if (!this.selectedFile) {
            Components.showToast('Please select or capture a leaf photo first', 'warning');
            return;
        }

        const scanner = document.getElementById('scanner-overlay');
        const diagnoseBtn = document.getElementById('run-diagnosis-btn');
        const cropSelect = document.getElementById('diagnosis-crop-select');
        const qualityAlert = document.getElementById('diagnosis-quality-alert');
        const previewImg = document.getElementById('leaf-preview-img');

        if (scanner) scanner.style.display = 'block';
        if (qualityAlert) qualityAlert.style.display = 'none';
        if (diagnoseBtn) {
            diagnoseBtn.disabled = true;
            diagnoseBtn.innerHTML = '<span>⏳</span> Analyzing Pathology & Symptoms...';
        }

        const cropName = cropSelect ? cropSelect.value : 'Tomato';
        const isOffline = !navigator.onLine || (typeof SyncManager !== 'undefined' && !SyncManager.isOnline());

        // --- OFFLINE DIAGNOSIS PATHWAY ---
        if (isOffline) {
            try {
                console.log('[DiagnosisController] Network offline. Running on-device edge diagnosis pipeline...');
                const edgeResult = await EdgeInferenceEngine.runEdgeDiagnosis(previewImg, cropName);

                const clientUuid = crypto.randomUUID ? crypto.randomUUID() : 'offline_diag_' + Date.now();
                const offlineRecord = {
                    id: 'local_' + Date.now(),
                    client_uuid: clientUuid,
                    crop: edgeResult.crop,
                    disease: edgeResult.disease,
                    confidence: edgeResult.confidence,
                    severity: edgeResult.severity || 'Moderate',
                    diagnostic_certainty: edgeResult.diagnostic_certainty || 'local_preliminary',
                    symptoms: edgeResult.symptoms,
                    cause: edgeResult.cause || "Diagnosed via on-device Edge Engine in offline mode.",
                    next_actions: [
                        "Record saved in local device storage.",
                        "Automatic cloud verification will trigger once internet connectivity resumes.",
                        "Follow standard cultural leaf-aeration practices in the interim."
                    ],
                    chemical_treatment: edgeResult.chemical_treatment || { active_ingredient: "Mancozeb 75% WP @ 2.5 g/L", phi_days: 7 },
                    biological_treatment: edgeResult.biological_treatment || { agent: "Neem Oil 10,000 ppm @ 2 ml/L" },
                    organic_treatment: edgeResult.organic_treatment || { formulation: "Wood ash / bio-stimulant" },
                    cultural_treatment: edgeResult.cultural_treatment || ["Maintain clean plant canopy."],
                    monitoring_recommendations: "Inspect foliar lesion margin progression in 48 hours.",
                    differential_diagnoses: [
                        { disease: "Foliar Stress Complex", confidence: 60.0, differentiating_factor: "Local Edge Screening" }
                    ],
                    is_offline: true,
                    sync_status: 'pending',
                    created_at: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                };

                // Save locally & queue for sync
                await OfflineStorage.saveOfflineDiagnosis(offlineRecord);
                await OfflineStorage.enqueueSyncItem('diagnosis', {
                    client_uuid: clientUuid,
                    diagnosed_crop: offlineRecord.crop,
                    disease_name: offlineRecord.disease,
                    confidence: offlineRecord.confidence,
                    severity: offlineRecord.severity,
                    symptoms: offlineRecord.symptoms,
                    cause: offlineRecord.cause,
                    active_ingredient: offlineRecord.chemical_treatment.active_ingredient,
                    phi_days: offlineRecord.chemical_treatment.phi_days,
                    diagnostic_certainty: offlineRecord.diagnostic_certainty
                });

                if (typeof SyncManager !== 'undefined') {
                    SyncManager.updatePendingCountBadge();
                }

                this.renderResults(offlineRecord);
                Components.showToast('⚡ Local offline diagnosis complete! Queued for cloud sync.', 'warning');
                return;
            } catch (offlineErr) {
                console.error('[DiagnosisController] On-device inference error:', offlineErr);
                Components.showToast('Offline diagnosis failed: ' + offlineErr.message, 'danger');
                return;
            } finally {
                if (scanner) scanner.style.display = 'none';
                if (diagnoseBtn) {
                    diagnoseBtn.disabled = false;
                    diagnoseBtn.innerHTML = '<span>🔍</span> Start AI Crop Diagnosis';
                }
            }
        }

        // --- ONLINE CLOUD DIAGNOSIS PATHWAY ---
        const clientUuid = crypto.randomUUID ? crypto.randomUUID() : 'online_diag_' + Date.now();
        const formData = new FormData();
        formData.append('image', this.selectedFile);
        formData.append('crop_name', cropName);
        formData.append('client_uuid', clientUuid);

        try {
            const response = await fetch('/api/diagnose', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (response.ok && data.success) {
                // Cache diagnosis locally in IndexedDB as well
                data.client_uuid = clientUuid;
                data.is_offline = false;
                await OfflineStorage.saveOfflineDiagnosis(data);

                this.renderResults(data);
                Components.showToast('Diagnosis completed successfully!', 'success');
                if (window.App && window.App.refreshState) window.App.refreshState();
            } else {
                this.renderQualityFailure(data);
            }
        } catch (error) {
            console.warn('[DiagnosisController] Network failed during upload. Falling back to offline queueing:', error);
            // Fallback gracefully without losing image
            try {
                const edgeResult = await EdgeInferenceEngine.runEdgeDiagnosis(previewImg, cropName);
                const offlineRecord = {
                    id: 'local_' + Date.now(),
                    client_uuid: clientUuid,
                    crop: edgeResult.crop,
                    disease: edgeResult.disease,
                    confidence: edgeResult.confidence,
                    severity: 'Moderate',
                    diagnostic_certainty: 'local_preliminary',
                    symptoms: edgeResult.symptoms,
                    is_offline: true,
                    sync_status: 'pending',
                    chemical_treatment: edgeResult.chemical_treatment || { active_ingredient: "Mancozeb 75% WP", phi_days: 7 },
                    biological_treatment: edgeResult.biological_treatment || { agent: "Neem Oil 10,000 ppm" },
                    organic_treatment: edgeResult.organic_treatment || { formulation: "Organic wash" },
                    cultural_treatment: ["Field inspection pending online sync."]
                };

                await OfflineStorage.saveOfflineDiagnosis(offlineRecord);
                await OfflineStorage.enqueueSyncItem('diagnosis', {
                    client_uuid: clientUuid,
                    diagnosed_crop: cropName,
                    disease_name: offlineRecord.disease,
                    confidence: 75.0,
                    severity: 'Moderate'
                });

                if (typeof SyncManager !== 'undefined') {
                    SyncManager.updatePendingCountBadge();
                }

                this.renderResults(offlineRecord);
                Components.showToast('📶 Upload interrupted. Saved locally & queued for sync!', 'warning');
            } catch (fallbackErr) {
                Components.showToast('Connection lost during diagnosis.', 'danger');
            }
        } finally {
            if (scanner) scanner.style.display = 'none';
            if (diagnoseBtn) {
                diagnoseBtn.disabled = false;
                diagnoseBtn.innerHTML = '<span>🔍</span> Start AI Crop Diagnosis';
            }
        }
    },

    renderQualityFailure(data) {
        const qualityAlert = document.getElementById('diagnosis-quality-alert');
        const resultsCard = document.getElementById('diagnosis-results-card');
        const emptyResults = document.getElementById('diagnosis-empty-placeholder');

        if (resultsCard) resultsCard.style.display = 'none';
        if (emptyResults) emptyResults.style.display = 'block';

        if (qualityAlert) {
            qualityAlert.style.display = 'block';
            const issueTitle = document.getElementById('quality-issue-title');
            const issueDesc = document.getElementById('quality-issue-desc');
            const instructionsList = document.getElementById('quality-retake-instructions');

            if (issueTitle) issueTitle.textContent = `Quality Warning: ${data.failure_type ? data.failure_type.replace('_', ' ').toUpperCase() : 'INVALID IMAGE'}`;
            if (issueDesc) issueDesc.textContent = data.error || 'The uploaded photo did not satisfy diagnostic quality thresholds.';

            if (instructionsList && data.retake_instructions) {
                instructionsList.innerHTML = data.retake_instructions.map(inst => `<li>${inst}</li>`).join('');
            }
            qualityAlert.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        Components.showToast('Image quality check failed. Follow retake instructions.', 'warning');
    },

    renderResults(data) {
        const resultsCard = document.getElementById('diagnosis-results-card');
        const emptyResults = document.getElementById('diagnosis-empty-placeholder');
        const qualityAlert = document.getElementById('diagnosis-quality-alert');
        const uncertainBanner = document.getElementById('diagnosis-uncertain-banner');

        if (qualityAlert) qualityAlert.style.display = 'none';
        if (emptyResults) emptyResults.style.display = 'none';
        if (!resultsCard) return;

        resultsCard.style.display = 'block';

        // Uncertain Diagnosis Handling
        if (data.diagnostic_certainty === 'uncertain_diagnosis' && uncertainBanner) {
            uncertainBanner.style.display = 'block';
            document.getElementById('uncertain-banner-text').textContent = data.uncertainty_advisory || 'Ambiguous symptom presentation. Recommend physical expert review.';
        } else if (uncertainBanner) {
            uncertainBanner.style.display = 'none';
        }

        // Render Bounding Box Localization on Preview
        const bbox = data.symptom_localization;
        const bboxOverlay = document.getElementById('symptom-bbox-overlay');
        if (bbox && bbox.detected && bbox.bounding_box_percent && bboxOverlay) {
            bboxOverlay.style.display = 'block';
            bboxOverlay.style.top = `${bbox.bounding_box_percent.top}%`;
            bboxOverlay.style.left = `${bbox.bounding_box_percent.left}%`;
            bboxOverlay.style.width = `${bbox.bounding_box_percent.width}%`;
            bboxOverlay.style.height = `${bbox.bounding_box_percent.height}%`;
            document.getElementById('bbox-coverage-tag').textContent = `${bbox.lesion_foliage_coverage_percent}% Foliage Area`;
        } else if (bboxOverlay) {
            bboxOverlay.style.display = 'none';
        }

        // Set primary details
        document.getElementById('result-disease-name').textContent = data.disease;
        const modeBadge = data.is_offline ? ' [⚡ Local Edge Preview]' : ' [☁️ Cloud Verified]';
        document.getElementById('result-crop-name').textContent = `${data.crop} • ${data.pathogen_type || 'Crop Pathogen'}${modeBadge}`;
        document.getElementById('result-confidence-badge').textContent = `${data.confidence}% Confidence`;
        
        const severityBadge = document.getElementById('result-severity-badge');
        severityBadge.textContent = `Severity: ${data.severity}`;
        severityBadge.className = `badge ${data.severity.includes('None') ? 'badge-healthy' : data.severity.includes('Severe') ? 'badge-danger' : 'badge-warning'}`;

        document.getElementById('result-symptoms').textContent = data.symptoms;
        document.getElementById('result-cause').textContent = data.cause;

        // Next Actions List
        const actionsContainer = document.getElementById('result-next-actions-list');
        if (actionsContainer && data.next_actions) {
            actionsContainer.innerHTML = data.next_actions.map(act => `
                <li style="margin-bottom: 6px;">${act}</li>
            `).join('');
        }

        // 1. Chemical Treatment
        const chem = data.chemical_treatment || {};
        document.getElementById('result-chem-active').textContent = chem.active_ingredient || 'N/A';
        document.getElementById('result-chem-dilution').textContent = chem.dilution_dosage || 'N/A';
        document.getElementById('result-chem-instructions').textContent = chem.application_instructions || 'N/A';
        document.getElementById('result-chem-ppe').textContent = chem.ppe_safety || 'Standard farm attire';
        document.getElementById('result-chem-phi').textContent = `${chem.phi_days || 0} Days`;
        document.getElementById('result-chem-frac').textContent = chem.frac_code || 'N/A';
        document.getElementById('result-chem-resistance').textContent = chem.resistance_management || 'N/A';

        // 2. Biological Treatment
        const bio = data.biological_treatment || {};
        document.getElementById('result-bio-agent').textContent = bio.agent || 'N/A';
        document.getElementById('result-bio-dosage').textContent = bio.dosage || 'N/A';
        document.getElementById('result-bio-instructions').textContent = bio.instructions || 'N/A';

        // 3. Organic Treatment
        const org = data.organic_treatment || {};
        document.getElementById('result-org-formulation').textContent = org.formulation || 'N/A';
        document.getElementById('result-org-dosage').textContent = org.dosage || 'N/A';
        document.getElementById('result-org-instructions').textContent = org.instructions || 'N/A';

        // 4. Cultural & Prevention
        const cultList = document.getElementById('result-cultural-list');
        if (cultList && data.cultural_treatment) {
            cultList.innerHTML = data.cultural_treatment.map(c => `<li>${c}</li>`).join('');
        }

        // Follow-up Monitoring
        const monEl = document.getElementById('result-monitoring');
        if (monEl) monEl.textContent = data.monitoring_recommendations || 'Re-inspect in 7 days.';

        // Differential Diagnoses
        const diffTable = document.getElementById('result-differential-tbody');
        if (diffTable && data.differential_diagnoses) {
            diffTable.innerHTML = data.differential_diagnoses.map(d => `
                <tr style="border-bottom: 1px solid var(--border-color-subtle);">
                    <td style="padding: 10px; font-weight: 600;">${d.disease}</td>
                    <td style="padding: 10px; text-align: center;"><span class="badge badge-info">${d.confidence}%</span></td>
                    <td style="padding: 10px; font-size: 13px; color: var(--text-secondary);">${d.differentiating_factor}</td>
                </tr>
            `).join('');
        }

        // Store latest diagnosis for speech output
        this.latestDiagnosis = data;

        // Trigger Marketplace input recommendations with non-commercial alternatives (Phase 8)
        if (window.MarketplaceController && data.crop && data.disease) {
            window.MarketplaceController.renderDiagnosisRecommendations(
                data.crop,
                data.disease,
                data.chemical_treatment ? data.chemical_treatment.active_ingredient : null
            );
        }

        // Scroll to results
        resultsCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    },

    speakCurrentDiagnosis() {
        if (!this.latestDiagnosis) return;
        const d = this.latestDiagnosis;
        const lang = (window.I18n && window.I18n.getLanguage) ? window.I18n.getLanguage() : 'en';

        let speechText = "";
        if (lang === 'kn') {
            speechText = `${d.crop} ಬೆಳೆಯಲ್ಲಿ ${d.disease} ರೋಗ ಪತ್ತೆಯಾಗಿದೆ. ನಿಖರತೆ ${d.confidence} ಪ್ರತಿಶತ. ${d.chemical_treatment?.active_ingredient ? 'ಸಿಂಪಡಣೆ: ' + d.chemical_treatment.active_ingredient : ''}. ಕಟಾವಿಗೆ ಮುನ್ನ ಕಾಯುವ ಅವಧಿ ${d.chemical_treatment?.phi_days || 5} ದಿನಗಳು.`;
        } else if (lang === 'hi') {
            speechText = `${d.crop} की फसल में ${d.disease} रोग पाया गया है। विश्वसनीयता ${d.confidence} प्रतिशत है। उपचार के लिए ${d.chemical_treatment?.active_ingredient || 'अनुशंसित दवा'} का छिड़काव करें।`;
        } else {
            speechText = `Diagnosed ${d.crop} with ${d.disease} at ${d.confidence}% confidence. Severity is ${d.severity}. Active ingredient recommended is ${d.chemical_treatment?.active_ingredient || 'Mancozeb'}.`;
        }

        if (window.VoiceAssistant) {
            window.VoiceAssistant.speak(speechText, lang);
            Components.showToast('🔊 Speaking diagnosis in selected language...', 'info');
        }
    },

    resetForm() {
        this.selectedFile = null;
        ['leaf-file-input', 'leaf-camera-input'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });

        const preview = document.getElementById('leaf-preview-img');
        const placeholder = document.getElementById('upload-placeholder');
        const previewContainer = document.getElementById('preview-container');
        const diagnoseBtn = document.getElementById('run-diagnosis-btn');
        const resultsCard = document.getElementById('diagnosis-results-card');
        const emptyResults = document.getElementById('diagnosis-empty-placeholder');
        const qualityAlert = document.getElementById('diagnosis-quality-alert');
        const bboxOverlay = document.getElementById('symptom-bbox-overlay');
        const uncertainBanner = document.getElementById('diagnosis-uncertain-banner');

        if (preview) preview.src = '';
        if (placeholder) placeholder.style.display = 'block';
        if (previewContainer) previewContainer.style.display = 'none';
        if (qualityAlert) qualityAlert.style.display = 'none';
        if (bboxOverlay) bboxOverlay.style.display = 'none';
        if (uncertainBanner) uncertainBanner.style.display = 'none';
        if (diagnoseBtn) diagnoseBtn.disabled = true;
        if (resultsCard) resultsCard.style.display = 'none';
        if (emptyResults) emptyResults.style.display = 'block';
    }
};

window.DiagnosisController = DiagnosisController;
