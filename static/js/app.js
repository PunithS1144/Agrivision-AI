/* AgriVision Plantix AI Main App Orchestrator & Router (Phase 3 RAG & Agronomist) */

const App = {
    state: {},
    currentScreen: 'home',
    activeFarmId: 1,
    chatAttachedFile: null,

    async init() {
        // Initialize Phase 5 Internationalization & Voice Assistant
        if (window.I18n) {
            try { I18n.init(); } catch (e) { console.warn('I18n init:', e); }
        }
        if (window.VoiceAssistant) {
            try { VoiceAssistant.init(); } catch (e) { console.warn('VoiceAssistant init:', e); }
        }

        // Initialize Phase 4 Offline Architecture & Edge Engines
        if (window.OfflineStorage) {
            try { await OfflineStorage.init(); } catch (e) { console.warn('OfflineStorage init:', e); }
        }
        if (window.EdgeInferenceEngine) {
            try { await EdgeInferenceEngine.init(); } catch (e) { console.warn('EdgeInference init:', e); }
        }
        if (window.SyncManager) {
            SyncManager.init();
        }

        this.setupNavigation();
        this.checkSecureContextBanner();
        this.checkAuthState();
        this.setupEventListeners();
        await this.refreshState();

        // Pre-fetch offline guides pack for local reading
        fetch('/api/guides/offline-pack')
            .then(res => res.json())
            .then(data => {
                if (data.success && window.OfflineStorage) {
                    OfflineStorage.saveGuides(data.guides);
                }
            })
            .catch(() => console.log('[App] Operating offline, skipping guide pack fetch.'));

        // Initialize sub-controllers
        if (window.DiagnosisController) window.DiagnosisController.init();
        if (window.CalculatorController) window.CalculatorController.init();
        if (window.WeatherController) window.WeatherController.init();

        // Load chat history
        this.loadChatHistory();

        // Handle URL hash or default to home
        const initialScreen = window.location.hash.replace('#', '') || 'home';
        this.navigateTo(initialScreen);
    },

    setupNavigation() {
        document.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const screen = link.dataset.screen;
                if (screen) this.navigateTo(screen);
            });
        });

        document.querySelectorAll('.mobile-bottom-nav .mobile-nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const screen = btn.dataset.screen;
                if (screen) this.navigateTo(screen);
            });
        });

        window.addEventListener('hashchange', () => {
            const screen = window.location.hash.replace('#', '') || 'home';
            this.navigateTo(screen, false);
        });
    },

    navigateTo(screenId, updateHash = true) {
        const screens = document.querySelectorAll('.app-screen');
        const targetScreen = document.getElementById(`screen-${screenId}`);

        if (!targetScreen) {
            console.warn(`Screen ${screenId} not found, falling back to home`);
            screenId = 'home';
        }

        screens.forEach(s => s.classList.remove('active'));
        const activeEl = document.getElementById(`screen-${screenId}`);
        if (activeEl) activeEl.classList.add('active');

        document.querySelectorAll('.sidebar-nav .nav-link').forEach(l => {
            l.classList.toggle('active', l.dataset.screen === screenId);
        });

        document.querySelectorAll('.mobile-bottom-nav .mobile-nav-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.screen === screenId);
        });

        this.currentScreen = screenId;
        if (updateHash) {
            window.location.hash = screenId;
        }

        if (screenId === 'history') {
            this.loadDiagnosisHistory();
        } else if (screenId === 'chat') {
            this.loadChatHistory();
            this.setChatLanguage(this.chatLanguage || 'kn');
        } else if (screenId === 'precision') {
            if (window.PrecisionController) window.PrecisionController.init();
        }

        window.scrollTo({ top: 0, behavior: 'instant' });
    },

    async refreshState() {
        try {
            const res = await fetch('/api/state');
            const data = await res.json();
            if (data.status === 'success') {
                this.state = data;
                // Cache to IndexedDB for offline access
                if (window.OfflineStorage) {
                    await OfflineStorage.setAppState(data);
                }
                this.renderAllViews();
            }
        } catch (err) {
            console.warn('[App] Online fetch failed, loading state from offline IndexedDB storage...', err);
            if (window.OfflineStorage) {
                const cached = await OfflineStorage.getAppState();
                if (cached) {
                    this.state = cached;
                    Components.showToast('📶 Operating with locally cached farm data', 'info');
                    this.renderAllViews();
                }
            }
        }
    },

    renderAllViews() {
        const data = this.state;
        this.renderDashboard();
        this.renderCrops();
        this.renderFarms();
        this.renderActivities();
        this.renderNotifications();
        this.renderCommunity();
        this.renderRetailers();
        this.renderProfile();
        this.renderChatPromptSuggestions(data.suggested_prompts);
        if (window.WeatherController && data.weather) {
            window.WeatherController.renderWeather(data.weather);
        }
    },

    renderDashboard() {
        const user = this.state.user || {};
        const crops = this.state.crops || [];
        const alerts = this.state.alerts || [];
        const tips = this.state.farming_tips || [];
        const recent = this.state.recent_diagnoses || [];

        const greetingName = document.getElementById('dash-farmer-name');
        const greetingVillage = document.getElementById('dash-farmer-village');
        if (greetingName) greetingName.textContent = user.full_name || 'Farmer';
        if (greetingVillage) greetingVillage.textContent = user.village ? `📍 ${user.village}, ${user.state || 'Karnataka'}` : '';

        const cropCount = document.getElementById('dash-crop-count');
        const farmAcreage = document.getElementById('dash-total-acres');
        if (cropCount) cropCount.textContent = crops.length;
        if (farmAcreage) {
            const total = crops.reduce((sum, c) => sum + (c.area_acres || 0), 0);
            farmAcreage.textContent = `${total.toFixed(1)} Acres`;
        }

        // Also load live disease outbreaks into dashboard alerts
        fetch('/api/precision/outbreaks')
            .then(r => r.json())
            .then(obData => {
                if (obData && obData.outbreaks && obData.outbreaks.length > 0) {
                    const obList = document.getElementById('dash-alerts-list');
                    if (obList) {
                        const obHtml = obData.outbreaks.slice(0, 3).map(o => `
                            <div style="background-color: ${o.severity === 'High' ? 'var(--status-danger-bg)' : 'var(--status-warning-bg)'}; 
                                        border-left: 4px solid ${o.severity === 'High' ? 'var(--status-danger)' : 'var(--status-warning)'}; 
                                        padding: 12px 16px; border-radius: var(--radius-sm); margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="font-weight: 700; font-size: 14px; color: var(--text-primary);">⚠️ ${o.crop} • ${o.disease}</div>
                                    <div style="font-size: 12px; color: var(--text-secondary);">📍 ${o.taluk}, ${o.district} • <strong>${o.distance_km} km away</strong> (${o.reported_cases} reports)</div>
                                </div>
                                <button type="button" class="btn btn-outline btn-pill" style="font-size: 11px; padding: 4px 10px;" onclick="App.navigateTo('precision')">View Radar</button>
                            </div>
                        `).join('');
                        obList.innerHTML = obHtml;
                    }
                }
            })
            .catch(() => {});

        const alertsList = document.getElementById('dash-alerts-list');
        if (alertsList && alerts.length > 0) {
            alertsList.innerHTML = alerts.map(a => `
                <div style="background-color: ${a.severity === 'danger' ? 'var(--status-danger-bg)' : 'var(--status-warning-bg)'}; 
                            border-left: 4px solid ${a.severity === 'danger' ? 'var(--status-danger)' : 'var(--status-warning)'}; 
                            padding: 12px 16px; border-radius: var(--radius-sm); margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-weight: 700; font-size: 14px; color: var(--text-primary);">${a.title}</span>
                        <span class="badge ${a.severity === 'danger' ? 'badge-danger' : 'badge-warning'}">${a.category}</span>
                    </div>
                    <div style="font-size: 13.5px; color: var(--text-secondary);">${a.message}</div>
                </div>
            `).join('');
        }

        const recentList = document.getElementById('dash-recent-diagnoses');
        if (recentList) {
            if (recent.length === 0) {
                recentList.innerHTML = `
                    <div style="text-align: center; padding: 24px; color: var(--text-muted);">
                        <div style="font-size: 32px; margin-bottom: 8px;">🌱</div>
                        <div>No recent crop diagnoses yet. Snap a photo to run early detection!</div>
                    </div>`;
            } else {
                recentList.innerHTML = recent.slice(0, 3).map(d => `
                    <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px; background: var(--bg-subtle); border-radius: var(--radius-md); margin-bottom: 8px;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <img src="${d.image_path}" alt="${d.disease_name}" style="width: 48px; height: 48px; border-radius: var(--radius-sm); object-fit: cover;" onerror="this.src='/static/img/leaf-placeholder.png'">
                            <div>
                                <div style="font-weight: 700; font-size: 14px; color: var(--text-primary);">${d.disease_name}</div>
                                <div style="font-size: 12px; color: var(--text-muted);">${d.diagnosed_crop} • ${d.created_at || 'Recently'}</div>
                            </div>
                        </div>
                        <span class="badge ${d.disease_name.includes('Healthy') ? 'badge-healthy' : 'badge-warning'}">${d.confidence}% Match</span>
                    </div>
                `).join('');
            }
        }

        const tipsContainer = document.getElementById('dash-farming-tips');
        if (tipsContainer && tips.length > 0) {
            tipsContainer.innerHTML = tips.map(t => `
                <div class="agri-card" style="padding: 16px; margin-bottom: 12px; border-left: 4px solid var(--primary-500);">
                    <div style="font-size: 11px; font-weight: 700; color: var(--primary-700); text-transform: uppercase;">${t.category} • ${t.crop}</div>
                    <div style="font-size: 14.5px; font-weight: 700; color: var(--text-primary); margin: 4px 0 6px;">${t.title}</div>
                    <div style="font-size: 13px; color: var(--text-secondary); line-height: 1.45;">${t.tip}</div>
                </div>
            `).join('');
        }
    },

    renderFarms() {
        const farms = this.state.farms || [];
        const container = document.getElementById('farms-selector-tabs');
        const farmSelectModal = document.getElementById('new-crop-farm-id');
        const activityFarmSelect = document.getElementById('activity-farm-id');

        if (container) {
            container.innerHTML = farms.map((f, idx) => `
                <button class="tab-btn ${f.id === this.activeFarmId ? 'active' : ''}" onclick="App.selectFarm(${f.id})">
                    🏡 ${f.farm_name} (${f.acreage} ac)
                </button>
            `).join('');
        }

        if (farmSelectModal) {
            farmSelectModal.innerHTML = farms.map(f => `
                <option value="${f.id}">${f.farm_name} (${f.location})</option>
            `).join('');
        }

        if (activityFarmSelect) {
            activityFarmSelect.innerHTML = farms.map(f => `
                <option value="${f.id}">${f.farm_name}</option>
            `).join('');
        }
    },

    selectFarm(farmId) {
        this.activeFarmId = farmId;
        this.renderFarms();
        this.renderCrops();
        this.renderActivities();
    },

    renderCrops() {
        const allCrops = this.state.crops || [];
        const crops = allCrops.filter(c => c.farm_id === this.activeFarmId || !c.farm_id);
        const container = document.getElementById('crops-grid-container');
        if (!container) return;

        if (crops.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-muted); grid-column: 1 / -1;">
                    <div style="font-size: 40px; margin-bottom: 12px;">🌾</div>
                    <div style="font-weight: 600;">No crops registered for this farm plot yet</div>
                    <div style="font-size: 13px; margin-top: 4px;">Click 'Add New Crop' to track sowing cycles, health, and fertilizer schedules.</div>
                </div>`;
            return;
        }

        container.innerHTML = crops.map(c => `
            <div class="agri-card agri-card-hover" style="position: relative;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                    <div>
                        <div style="font-size: 17px; font-weight: 800; color: var(--text-primary);">${c.crop_name}</div>
                        <div style="font-size: 13px; color: var(--text-muted);">${c.variety || 'Hybrid Variety'}</div>
                    </div>
                    <span class="badge ${c.health_status === 'Healthy' ? 'badge-healthy' : 'badge-warning'}">${c.health_status}</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px; color: var(--text-secondary);">
                    <span>Growth Stage:</span>
                    <strong style="color: var(--text-primary);">${c.stage}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px; color: var(--text-secondary);">
                    <span>Plot Area:</span>
                    <strong style="color: var(--text-primary);">${c.area_acres} Acres</strong>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 12px; color: var(--text-secondary);">
                    <span>Sown Date:</span>
                    <strong style="color: var(--text-primary);">${c.sowing_date || 'N/A'}</strong>
                </div>
                ${c.notes ? `<div style="font-size: 12px; background: var(--bg-subtle); padding: 8px 10px; border-radius: var(--radius-sm); color: var(--text-secondary); margin-bottom: 12px;">📝 ${c.notes}</div>` : ''}
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-secondary btn-block" style="font-size: 13px; padding: 8px 12px;" onclick="App.navigateTo('diagnose')">Diagnose</button>
                    <button class="btn btn-outline btn-block" style="font-size: 13px; padding: 8px 12px;" onclick="App.navigateTo('calculator')">Fertilizer</button>
                </div>
            </div>
        `).join('');
    },

    renderActivities() {
        const activities = this.state.farm_activities || [];
        const container = document.getElementById('farm-activities-timeline');
        if (!container) return;

        if (activities.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 20px; color: var(--text-muted); font-size: 13px;">
                    No farm activities recorded yet. Click 'Log Farm Activity' to document spraying, irrigation, or fertilizer applications.
                </div>`;
            return;
        }

        container.innerHTML = activities.map(a => `
            <div style="display: flex; gap: 14px; margin-bottom: 14px; border-bottom: 1px solid var(--border-color-subtle); padding-bottom: 10px;">
                <div style="width: 36px; height: 36px; border-radius: var(--radius-full); background: var(--primary-100); color: var(--primary-800); display: flex; align-items: center; justify-content: center; font-size: 16px;">
                    ${a.activity_type === 'Spraying' ? '🚜' : a.activity_type === 'Fertigation' ? '💧' : a.activity_type === 'Weeding' ? '🌿' : '📋'}
                </div>
                <div style="flex: 1;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="font-size: 14px; color: var(--text-primary);">${a.activity_type}</strong>
                        <span style="font-size: 12px; color: var(--text-muted);">${a.activity_date}</span>
                    </div>
                    <div style="font-size: 13px; color: var(--text-secondary); margin: 2px 0;">${a.description}</div>
                    ${a.quantity_used ? `<span class="badge badge-info" style="font-size: 11px;">Dosage: ${a.quantity_used}</span>` : ''}
                </div>
            </div>
        `).join('');
    },

    renderNotifications() {
        const notes = this.state.notifications || [];
        const badge = document.getElementById('header-notification-count');
        const container = document.getElementById('notifications-feed-list');

        const unreadCount = notes.filter(n => !n.is_read).length;
        if (badge) {
            badge.textContent = unreadCount;
            badge.style.display = unreadCount > 0 ? 'inline-flex' : 'none';
        }

        if (container) {
            if (notes.length === 0) {
                container.innerHTML = `<div style="text-align: center; padding: 20px; color: var(--text-muted);">No notifications</div>`;
            } else {
                container.innerHTML = notes.map(n => `
                    <div style="padding: 12px 14px; border-bottom: 1px solid var(--border-color-subtle); background: ${n.is_read ? 'transparent' : 'var(--primary-50)'}; display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <div style="font-weight: 700; font-size: 13.5px; color: var(--text-primary);">${n.title}</div>
                            <div style="font-size: 13px; color: var(--text-secondary); margin: 2px 0 4px;">${n.message}</div>
                            <small style="color: var(--text-muted); font-size: 11px;">${n.created_at || 'Recently'}</small>
                        </div>
                        ${!n.is_read ? `<button class="btn btn-outline" style="font-size: 11px; padding: 2px 6px; min-height: 24px;" onclick="App.markNotificationRead(${n.id})">Mark Read</button>` : ''}
                    </div>
                `).join('');
            }
        }
    },

    async markNotificationRead(id) {
        try {
            await fetch('/api/notifications/mark-read', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: id })
            });
            await this.refreshState();
        } catch (err) {
            console.error('Error marking read:', err);
        }
    },

    async loadDiagnosisHistory() {
        const searchInput = document.getElementById('history-search-input');
        const cropFilter = document.getElementById('history-crop-filter');
        const sortOrder = document.getElementById('history-sort-select');

        const q = searchInput ? searchInput.value.trim() : '';
        const crop = cropFilter ? cropFilter.value : '';
        const sort = sortOrder ? sortOrder.value : 'desc';

        const container = document.getElementById('history-records-container');
        if (container) {
            container.innerHTML = `<div style="text-align: center; padding: 40px; color: var(--text-muted);">Loading diagnosis history...</div>`;
        }

        try {
            let records = [];
            if (!navigator.onLine || (typeof SyncManager !== 'undefined' && !SyncManager.isOnline())) {
                records = await OfflineStorage.getOfflineDiagnoses();
                if (q) records = records.filter(r => (r.disease_name || '').toLowerCase().includes(q.toLowerCase()));
                if (crop) records = records.filter(r => (r.diagnosed_crop || r.crop) === crop);
            } else {
                const url = `/api/diagnoses/history?q=${encodeURIComponent(q)}&crop=${encodeURIComponent(crop)}&sort=${sort}`;
                const res = await fetch(url);
                records = await res.json();
            }

            if (!container) return;

            if (records.length === 0) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 40px; color: var(--text-muted);">
                        <div style="font-size: 40px; margin-bottom: 8px;">🔍</div>
                        <div style="font-weight: 600;">No matching diagnosis records found</div>
                        <div style="font-size: 13px; margin-top: 4px;">Try clearing filters or capture a new leaf in Crop Diagnosis.</div>
                    </div>`;
                return;
            }

            container.innerHTML = records.map(r => `
                <div class="agri-card" style="margin-bottom: 16px; border-left: 5px solid ${r.disease_name && r.disease_name.includes('Healthy') ? 'var(--status-healthy)' : 'var(--status-warning)'};">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                        <div style="display: flex; gap: 14px; align-items: center;">
                            <img src="${r.image_path || '/static/img/leaf-placeholder.png'}" style="width: 58px; height: 58px; border-radius: var(--radius-md); object-fit: cover;" onerror="this.src='/static/img/leaf-placeholder.png'">
                            <div>
                                <h3 style="font-size: 17px; font-weight: 800; color: var(--text-primary); margin-bottom: 2px;">
                                    ${r.disease_name}
                                </h3>
                                <div style="font-size: 13px; color: var(--text-muted);">
                                    ${r.diagnosed_crop || r.crop} • Recorded on ${r.created_at || 'Just now'}
                                </div>
                            </div>
                        </div>
                        <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 4px;">
                            <div style="display: flex; gap: 4px;">
                                <span class="badge ${r.disease_name && r.disease_name.includes('Healthy') ? 'badge-healthy' : 'badge-warning'}">${r.confidence}% Match</span>
                                ${r.is_offline ? `<span class="badge badge-warning" style="font-size: 10px;">⚡ Offline (${r.sync_status || 'pending'})</span>` : `<span class="badge badge-healthy" style="font-size: 10px;">☁️ Cloud Synced</span>`}
                            </div>
                            <span class="badge badge-info" style="font-size: 11px;">Certainty: ${r.diagnostic_certainty || 'confirmed'}</span>
                        </div>
                    </div>
                    
                    <div style="font-size: 13.5px; color: var(--text-secondary); line-height: 1.45; margin-bottom: 12px; background: var(--bg-subtle); padding: 10px; border-radius: var(--radius-sm);">
                        ${r.symptoms}
                    </div>

                    ${r.active_ingredient ? `
                        <div style="font-size: 12.5px; color: var(--text-primary); margin-bottom: 12px;">
                            <strong>Active Ingredient:</strong> ${r.active_ingredient} • 
                            <strong>PHI:</strong> ${r.phi_days} Days • 
                            <strong>FRAC:</strong> ${r.frac_code}
                        </div>
                    ` : ''}

                    <div style="display: flex; justify-content: flex-end; gap: 8px;">
                        ${!r.is_offline ? `
                        <button class="btn btn-outline" style="font-size: 12px; padding: 6px 12px; color: var(--status-danger);" onclick="App.deleteDiagnosisRecord(${r.id})">
                            🗑️ Delete Record
                        </button>
                        ` : `
                        <button class="btn btn-outline" style="font-size: 12px; padding: 6px 12px; color: #1976d2;" onclick="SyncManager.triggerSync()">
                            🔄 Sync to Cloud
                        </button>
                        `}
                    </div>
                </div>
            `).join('');
        } catch (err) {
            console.error('History load error, falling back to offline records:', err);
            if (window.OfflineStorage) {
                const offRecords = await OfflineStorage.getOfflineDiagnoses();
                if (container && offRecords.length > 0) {
                    container.innerHTML = offRecords.map(r => `
                        <div class="agri-card" style="margin-bottom: 16px; border-left: 5px solid var(--accent-amber);">
                            <div style="display: flex; justify-content: space-between;">
                                <div>
                                    <h3 style="font-size: 16px; font-weight: 800;">${r.disease} (Offline Record)</h3>
                                    <div style="font-size: 12px; color: var(--text-muted);">${r.crop} • Queued for cloud sync</div>
                                </div>
                                <span class="badge badge-warning">⚡ Offline Preview</span>
                            </div>
                        </div>
                    `).join('');
                }
            }
        }
    },

    async deleteDiagnosisRecord(id) {
        if (!confirm('Are you sure you want to delete this historical diagnosis record?')) return;

        try {
            const res = await fetch(`/api/diagnoses/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) {
                Components.showToast('Diagnosis record deleted', 'success');
                this.loadDiagnosisHistory();
                this.refreshState();
            } else {
                Components.showToast(data.error || 'Failed to delete record', 'danger');
            }
        } catch (err) {
            Components.showToast('Error deleting record', 'danger');
        }
    },

    /* --- ADVANCED AI AGRONOMIST & RAG CHAT LOGIC --- */
    renderChatPromptSuggestions(prompts) {
        const container = document.getElementById('chat-suggestions-carousel');
        if (!container || !prompts) return;

        container.innerHTML = prompts.map(p => `
            <button type="button" class="btn btn-outline btn-pill" style="font-size: 12.5px; padding: 6px 14px; white-space: nowrap; flex-shrink: 0;" onclick="App.askAgronomistPrompt('${p.replace(/'/g, "\\'")}')">
                🌱 ${p}
            </button>
        `).join('');
    },

    askAgronomistPrompt(text) {
        const input = document.getElementById('chat-query-input');
        if (input) {
            input.value = text;
            const form = document.getElementById('agronomist-chat-form');
            if (form) form.dispatchEvent(new Event('submit', { cancelable: true }));
        }
    },

    async loadChatHistory() {
        const container = document.getElementById('chat-messages-container');
        if (!container) return;

        try {
            const res = await fetch('/api/chat/history');
            const data = await res.json();
            if (data.messages && data.messages.length > 0) {
                container.innerHTML = '';
                data.messages.forEach(m => {
                    this.appendChatMessage(m.text, m.sender, m.sources, m.attached_image_path);
                });
            }
        } catch (err) {
            console.error('Failed to load chat history:', err);
        }
    },

    async clearChatHistory() {
        if (!confirm('Reset current agronomic consultation session?')) return;
        try {
            const res = await fetch('/api/chat/clear', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                Components.showToast('Consultation session reset', 'success');
                this.loadChatHistory();
            }
        } catch (err) {
            Components.showToast('Failed to reset chat', 'danger');
        }
    },

    chatLanguage: 'kn',

    setChatLanguage(lang) {
        this.chatLanguage = lang || 'kn';
        const select = document.getElementById('chat-language-select');
        if (select) select.value = this.chatLanguage;

        // Update active class on chat language pills
        document.querySelectorAll('.chat-lang-pill').forEach(pill => {
            if (pill.dataset.lang === this.chatLanguage) {
                pill.classList.add('btn-primary');
                pill.classList.remove('btn-outline');
            } else {
                pill.classList.remove('btn-primary');
                pill.classList.add('btn-outline');
            }
        });

        // Update placeholder in native regional script
        const input = document.getElementById('chat-query-input');
        const placeholders = {
            kn: "ಕನ್ನಡದಲ್ಲಿ ಕೃಷಿ ಪ್ರಶ್ನೆ ಕೇಳಿ (ಉದಾ: ಟೊಮೇಟೊ ಎಲೆ ಹಳದಿಯಾಗಿದೆ, ಗೊಬ್ಬರ ಪ್ರಮಾಣವೇನು?)...",
            hi: "हिंदी में प्रश्न पूछें (जैसे: टमाटर की पत्तियां पीली हैं, कौन सी खाद डालें?)...",
            en: "Ask in English (e.g. What is the dosage of Mancozeb for Tomato?)...",
            te: "తెలుగులో అడగండి (ఉదా: టమోటా ఆకులు పసుపు రంగులోకి మారితే ఏమి చేయాలి?)...",
            ta: "தமிழில் கேட்கவும் (எ.கா: தக்காளி இலைக்கருகல் நோய்க்கு மருந்து என்ன?)...",
            mr: "मराठीत विचारा (उदा: टोमॅटो पिकासाठी खत व्यवस्थापन कसे करावे?)...",
            bn: "বাংলায় প্রশ্ন জিজ্ঞাসা করুন (যেমন: টমেটো পাতা হলুদ হয়ে গেলে কী সার দেব?)..."
        };
        if (input) {
            input.placeholder = placeholders[this.chatLanguage] || placeholders['en'];
        }

        // Render localized suggestions carousel
        this.renderChatPromptSuggestionsForLang(this.chatLanguage);
    },

    renderChatPromptSuggestionsForLang(lang) {
        const questions = {
            kn: [
                "ಟೊಮೇಟೊ ಎಲೆ ಹಳದಿ ಆಗಲು ಕಾರಣವೇನು?",
                "ಬೆಳೆಗೆ ಶಿಫಾರಸು ಮಾಡಿದ ರಸಗೊಬ್ಬರ ಪ್ರಮಾಣ ಎಷ್ಟು?",
                "ಕಾಯಿ ಕೊರೆಯುವ ಹುಳು ನಿಯಂತ್ರಣ ಹೇಗೆ?",
                "ಇಂದು ಕೀಟನಾಶಕ ಸಿಂಪಡಿಸಲು ಯೋಗ್ಯ ಸಮಯವೇ?",
                "ಮೆಣಸಿನಕಾಯಿ ಎಲೆ ಮುರುಟು ರೋಗಕ್ಕೆ ಪರಿಹಾರವೇನು?"
            ],
            hi: [
                "टमाटर की पत्तियां पीली क्यों हो रही हैं?",
                "फसल के लिए अनुशंसित खाद की मात्रा क्या है?",
                "फल छेदक व इल्ली कीट की रोकथाम कैसे करें?",
                "क्या आज कीटनाशक छिड़काव का सही समय है?",
                "मिर्च में पत्ता मरोड़ रोग का क्या उपचार है?"
            ],
            en: [
                "Why are my tomato leaves turning yellow?",
                "Recommended fertilizer dosage for tomato?",
                "How to control fruit borer caterpillars?",
                "Is today's weather suitable for knapsack spray?",
                "Remedy for chili leaf curl disease?"
            ],
            te: [
                "టమోటా ఆకులు పసుపు రంగులోకి మారడానికి కారణం ఏమిటి?",
                "పంటకు ఎరువుల మోతాదు ఎంత వేయాలి?",
                "కాయ తొలుచు పురుగు నివారణ ఎలా?",
                "ఈ రోజు పురుగుమందు పిచಿಕారీ చేయవచ్చా?"
            ],
            ta: [
                "தக்காளி இலைகள் மஞ்சள் நிறமாக மாறுவது ஏன்?",
                "பயிருக்கு பரிந்துரைக்கப்பட்ட உர அளவு என்ன?",
                "காய்ப்புழு தாக்குதலை தடுப்பது எப்படி?",
                "இன்று பூச்சிக்கொல்லி தெளிக்க உகந்த நேரமா?"
            ],
            mr: [
                "टोमॅटोची पाने पिवळी पडण्याची कारणे काय?",
                "पिकासाठी खतांचे योग्य प्रमाण काय असावे?",
                "फळ पोखरणाऱ्या अळीचा बंदोबस्त कसा करावा?",
                "आज कीटकनाशक फवारणीसाठी योग्य वेळ आहे का?"
            ],
            bn: [
                "টমেটো পাতা হলুদ হয়ে যাওয়ার কারণ কী?",
                "ফসলের জন্য সারের সঠিক পরিমাণ কত?",
                "ফল ছিদ্রকারী পোকা দমনের উপায় কী?",
                "আজ কি কীটনাশক স্প্রে করার সঠিক সময়?"
            ]
        };
        const list = questions[lang] || questions['kn'];
        this.renderChatPromptSuggestions(list);
    },

    setChatAttachment(file) {
        this.chatAttachedFile = file;
        const chip = document.getElementById('chat-attachment-chip');
        const nameEl = document.getElementById('chat-attachment-name');
        if (chip && nameEl) {
            nameEl.textContent = file.name;
            chip.style.display = 'inline-flex';
        }
    },

    clearChatAttachment() {
        this.chatAttachedFile = null;
        const input = document.getElementById('chat-file-input');
        if (input) input.value = '';
        const chip = document.getElementById('chat-attachment-chip');
        if (chip) chip.style.display = 'none';
    },

    appendChatMessage(text, sender = 'user', sources = [], attachedImg = null) {
        const container = document.getElementById('chat-messages-container');
        if (!container) return;

        const isUser = sender === 'user';
        const msgDiv = document.createElement('div');
        msgDiv.style.display = 'flex';
        msgDiv.style.justifyContent = isUser ? 'flex-end' : 'flex-start';
        msgDiv.style.marginBottom = '14px';

        let formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        formattedText = formattedText.replace(/\*(.*?)\*/g, '<em>$1</em>');
        formattedText = formattedText.replace(/\n/g, '<br>');

        let imageSnippet = '';
        if (attachedImg) {
            imageSnippet = `<div style="margin-bottom: 8px;"><img src="${attachedImg}" style="max-height: 180px; border-radius: var(--radius-md); box-shadow: var(--shadow-sm);"></div>`;
        }

        let sourcesSnippet = '';
        if (sources && sources.length > 0) {
            sourcesSnippet = `
                <div style="margin-top: 8px; border-top: 1px solid rgba(0,0,0,0.1); padding-top: 6px; font-size: 11.5px; opacity: 0.85;">
                    📚 <strong>Verified Sources:</strong> ${sources.join(' • ')}
                </div>
            `;
        }

        const audioBtn = !isUser ? `
            <button class="btn btn-outline btn-icon" style="width: 24px; height: 24px; font-size: 11px; padding: 0; margin-right: 6px; border: none; background: transparent; cursor: pointer;" onclick="VoiceAssistant.speak(decodeURIComponent('${encodeURIComponent(text)}'), App.chatLanguage || I18n.getLanguage() || 'kn')" title="Listen Aloud">
                🔊
            </button>
        ` : '';

        msgDiv.innerHTML = `
            <div style="max-width: 82%; padding: 14px 18px; border-radius: var(--radius-lg); 
                        background-color: ${isUser ? 'var(--primary-600)' : 'var(--bg-subtle)'}; 
                        color: ${isUser ? '#ffffff' : 'var(--text-primary)'}; 
                        font-size: 14px; line-height: 1.5; box-shadow: var(--shadow-xs);">
                ${imageSnippet}
                <div>${formattedText}</div>
                ${sourcesSnippet}
                <div style="font-size: 11px; margin-top: 6px; display: flex; justify-content: space-between; align-items: center; opacity: 0.75;">
                    <div>${audioBtn}</div>
                    <div>${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                </div>
            </div>
        `;
        container.appendChild(msgDiv);
        container.scrollTop = container.scrollHeight;
    },

    startChatVoiceDictation() {
        const input = document.getElementById('chat-query-input');
        const micBtn = document.getElementById('chat-mic-btn');

        const va = window.VoiceAssistant || (typeof VoiceAssistant !== 'undefined' ? VoiceAssistant : null);
        if (!va) {
            Components.showToast('Voice assistant engine initializing... Please try again in 1 second.', 'warning');
            return;
        }

        // If already listening, toggle off cleanly
        if (va.getIsListening && va.getIsListening()) {
            va.stopListening();
            if (micBtn) {
                micBtn.style.color = '';
                micBtn.style.borderColor = '';
            }
            Components.showToast('Voice dictation stopped', 'info');
            return;
        }

        const lang = this.chatLanguage || (window.I18n ? I18n.getLanguage() : 'kn');
        const langNames = {
            kn: "ಕನ್ನಡ (Kannada)",
            hi: "हिंदी (Hindi)",
            te: "తెలుగు (Telugu)",
            ta: "தமிழ் (Tamil)",
            mr: "मराठी (Marathi)",
            bn: "বাংলা (Bengali)",
            en: "English"
        };

        const origPlaceholder = input ? input.placeholder : '';
        if (input) {
            input.placeholder = `🎙️ Listening in ${langNames[lang] || lang}... Speak your question now!`;
        }
        if (micBtn) {
            micBtn.style.color = '#e53935';
            micBtn.style.borderColor = '#e53935';
        }

        Components.showToast(`🎙️ Microphone listening in ${langNames[lang] || lang.toUpperCase()}... Speak now!`, 'info');

        va.startListeningForLanguage(lang, (transcript, confidence) => {
            if (input) {
                input.value = transcript;
                input.placeholder = origPlaceholder;
                Components.showToast(`✅ Recognized (${lang.toUpperCase()}): "${transcript}"`, 'success');
            }
            if (micBtn) {
                micBtn.style.color = '';
                micBtn.style.borderColor = '';
            }
        });
    },

    renderCommunity() {
        if (window.CommunityController) {
            window.CommunityController.loadPosts(1, false);
            return;
        }
        const posts = this.state.community_posts || [];
        const container = document.getElementById('community-posts-list');
        if (!container) return;

        container.innerHTML = posts.map(p => `
            <div class="agri-card" style="margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div class="avatar" style="width: 36px; height: 36px; font-size: 13px;">${p.author_name ? p.author_name[0] : 'F'}</div>
                        <div>
                            <div style="font-weight: 700; font-size: 14px; color: var(--text-primary);">${p.author_name}</div>
                            <div style="font-size: 12px; color: var(--text-muted);">${p.author_village || 'Karnataka'}</div>
                        </div>
                    </div>
                    <span class="badge badge-info">${p.crop_tag || 'General'}</span>
                </div>
                <h4 style="font-size: 15px; margin-bottom: 8px; color: var(--text-primary);">${p.title}</h4>
                <p style="font-size: 14px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 12px;">${p.content}</p>
                <div style="display: flex; align-items: center; gap: 16px; border-top: 1px solid var(--border-color-subtle); padding-top: 10px;">
                    <button class="btn btn-outline" style="font-size: 13px; padding: 6px 14px; min-height: 36px;" onclick="App.likePost(${p.id}, this)">
                        👍 <span class="like-count">${p.likes_count}</span> Helpful
                    </button>
                    <span style="font-size: 13px; color: var(--text-muted);">💬 ${p.comments_count || 0} replies</span>
                </div>
            </div>
        `).join('');
    },

    async likePost(postId, btn) {
        try {
            const res = await fetch('/api/community/like', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ post_id: postId })
            });
            const data = await res.json();
            if (data.success) {
                const countSpan = btn.querySelector('.like-count');
                if (countSpan) countSpan.textContent = data.likes_count;
                btn.style.color = 'var(--primary-700)';
                btn.style.borderColor = 'var(--primary-500)';
            }
        } catch (err) {
            console.error('Like error:', err);
        }
    },

    renderRetailers() {
        if (window.MarketplaceController) {
            window.MarketplaceController.loadProducts(1, false);
            return;
        }
        const retailers = this.state.retailers || [];
        const container = document.getElementById('retailers-grid');
        if (!container) return;

        container.innerHTML = retailers.map(r => `
            <div class="agri-card agri-card-hover">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                    <div>
                        <div style="font-size: 16px; font-weight: 700; color: var(--text-primary);">${r.name}</div>
                        <div style="font-size: 12px; color: var(--text-muted);">${r.shop_type}</div>
                    </div>
                    <span class="badge badge-healthy">⭐ ${r.rating}</span>
                </div>
                <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 8px;">📍 ${r.address} (${r.distance_km} km away)</div>
                <div style="font-size: 12px; background: var(--bg-subtle); padding: 8px; border-radius: var(--radius-sm); color: var(--text-secondary); margin-bottom: 12px;">
                    <strong>In Stock:</strong> ${r.products_available}
                </div>
                <a href="tel:${r.phone}" class="btn btn-primary btn-block" style="font-size: 13.5px; padding: 10px;">
                    📞 Call Store (${r.phone})
                </a>
            </div>
        `).join('');
    },

    renderProfile() {
        const user = this.state.user || {};
        const nameInput = document.getElementById('prof-name-input');
        const phoneInput = document.getElementById('prof-phone-input');
        const villageInput = document.getElementById('prof-village-input');
        const stateInput = document.getElementById('prof-state-input');
        const langSelect = document.getElementById('prof-lang-select');

        if (nameInput) nameInput.value = user.full_name || '';
        if (phoneInput) phoneInput.value = user.phone || '';
        if (villageInput) villageInput.value = user.village || '';
        if (stateInput) stateInput.value = user.state || '';
        if (langSelect) langSelect.value = user.preferred_language || 'en';
    },

    setupEventListeners() {
        // Chatbot form
        const chatForm = document.getElementById('agronomist-chat-form');
        const chatInput = document.getElementById('chat-query-input');
        const chatFileInput = document.getElementById('chat-file-input');

        if (chatFileInput) {
            chatFileInput.addEventListener('change', (e) => {
                if (e.target.files && e.target.files[0]) {
                    this.setChatAttachment(e.target.files[0]);
                }
            });
        }

        if (chatForm && chatInput) {
            chatForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const msg = chatInput.value.trim();
                const attachedFile = this.chatAttachedFile;

                if (!msg && !attachedFile) return;

                // Optimistic user display
                this.appendChatMessage(msg, 'user', [], attachedFile ? URL.createObjectURL(attachedFile) : null);
                chatInput.value = '';
                this.clearChatAttachment();

                // Build multipart payload
                const formData = new FormData();
                formData.append('message', msg);
                formData.append('language', this.chatLanguage || (window.I18n ? I18n.getLanguage() : 'kn'));
                if (attachedFile) formData.append('image', attachedFile);

                try {
                    const res = await fetch('/api/chat/send', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await res.json();
                    if (data.success) {
                        this.appendChatMessage(data.reply, 'agronomist', data.citations);
                        if (data.suggested_followups) {
                            this.renderChatPromptSuggestions(data.suggested_followups);
                        }
                    } else {
                        this.appendChatMessage(data.error || 'Agronomic query evaluation error.', 'agronomist');
                    }
                } catch (err) {
                    this.appendChatMessage('Network error connecting with AI Agronomist.', 'agronomist');
                }
            });
        }

        // Add Crop Modal Form
        const addCropForm = document.getElementById('add-crop-form');
        if (addCropForm) {
            addCropForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const farmId = document.getElementById('new-crop-farm-id').value;
                const cropName = document.getElementById('new-crop-name').value;
                const variety = document.getElementById('new-crop-variety').value;
                const acres = document.getElementById('new-crop-acres').value;
                const stage = document.getElementById('new-crop-stage').value;
                const notes = document.getElementById('new-crop-notes').value;

                try {
                    const res = await fetch('/api/crops', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            farm_id: farmId,
                            crop_name: cropName,
                            variety: variety,
                            area_acres: acres,
                            stage: stage,
                            notes: notes
                        })
                    });
                    const data = await res.json();
                    if (data.success) {
                        Components.showToast('Crop registered successfully!', 'success');
                        Components.closeModal('modal-add-crop');
                        addCropForm.reset();
                        await this.refreshState();
                    } else {
                        Components.showToast(data.error || 'Failed to save crop', 'danger');
                    }
                } catch (err) {
                    Components.showToast('Server error registering crop', 'danger');
                }
            });
        }

        // Farm Activity Form
        const activityForm = document.getElementById('log-activity-form');
        if (activityForm) {
            activityForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const payload = {
                    farm_id: document.getElementById('activity-farm-id').value,
                    activity_type: document.getElementById('activity-type-select').value,
                    activity_date: document.getElementById('activity-date-input').value,
                    quantity_used: document.getElementById('activity-qty-input').value,
                    description: document.getElementById('activity-desc-input').value
                };

                try {
                    const res = await fetch('/api/farms/activity', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    const data = await res.json();
                    if (data.success) {
                        Components.showToast('Farm activity recorded!', 'success');
                        Components.closeModal('modal-log-activity');
                        activityForm.reset();
                        await this.refreshState();
                    }
                } catch (err) {
                    Components.showToast('Failed to record activity', 'danger');
                }
            });
        }

        // History filters listener
        const historySearch = document.getElementById('history-search-input');
        const historyCrop = document.getElementById('history-crop-filter');
        const historySort = document.getElementById('history-sort-select');

        if (historySearch) historySearch.addEventListener('input', () => this.loadDiagnosisHistory());
        if (historyCrop) historyCrop.addEventListener('change', () => this.loadDiagnosisHistory());
        if (historySort) historySort.addEventListener('change', () => this.loadDiagnosisHistory());

        // Community Post Form
        const postForm = document.getElementById('create-post-form');
        if (postForm) {
            postForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const title = document.getElementById('new-post-title').value;
                const content = document.getElementById('new-post-content').value;
                const tag = document.getElementById('new-post-tag').value;

                try {
                    const res = await fetch('/api/community/post', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ title, content, crop_tag: tag })
                    });
                    const data = await res.json();
                    if (data.success) {
                        Components.showToast('Discussion published to community!', 'success');
                        Components.closeModal('modal-create-post');
                        postForm.reset();
                        await this.refreshState();
                    }
                } catch (err) {
                    Components.showToast('Failed to publish post', 'danger');
                }
            });
        }

        // Profile Form
        const profileForm = document.getElementById('farmer-profile-form');
        if (profileForm) {
            profileForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const payload = {
                    full_name: document.getElementById('prof-name-input').value,
                    phone: document.getElementById('prof-phone-input').value,
                    village: document.getElementById('prof-village-input').value,
                    state: document.getElementById('prof-state-input').value,
                    preferred_language: document.getElementById('prof-lang-select').value
                };

                try {
                    const res = await fetch('/api/profile', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    const data = await res.json();
                    if (data.success) {
                        Components.showToast('Farmer profile updated', 'success');
                        await this.refreshState();
                    }
                } catch (err) {
                    Components.showToast('Error updating profile', 'danger');
                }
            });
        }
    },

    async refreshAllData() {
        const btn = document.getElementById('global-refresh-btn');
        if (btn) {
            btn.classList.add('refresh-spin');
            btn.disabled = true;
        }
        Components.showToast('🔄 Synchronizing live farm, weather, satellite & outbreak feeds...', 'info');

        try {
            await Promise.all([
                this.refreshState(),
                window.WeatherController ? window.WeatherController.fetchWeather(true) : Promise.resolve(),
                window.PrecisionController ? window.PrecisionController.loadAllPrecisionData() : Promise.resolve(),
                window.SyncManager ? window.SyncManager.triggerSync() : Promise.resolve()
            ]);
            if (window.PrecisionController) window.PrecisionController.renderMap();
            Components.showToast('✅ All agricultural feeds synchronized successfully!', 'success');
        } catch (e) {
            console.error('Refresh error:', e);
            Components.showToast('Data refreshed.', 'info');
        } finally {
            if (btn) {
                btn.classList.remove('refresh-spin');
                btn.disabled = false;
            }
        }
    },

    checkSecureContextBanner() {
        const isLocal = ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname);
        if (!window.isSecureContext && !isLocal) {
            if (document.getElementById('insecure-context-banner')) return;
            const banner = document.createElement('div');
            banner.id = 'insecure-context-banner';
            banner.style.cssText = 'background: linear-gradient(90deg, #fff3cd, #ffe8a1); border-bottom: 2px solid #ffdf7e; padding: 10px 18px; font-size: 13.5px; color: #664d03; display: flex; align-items: center; justify-content: space-between; gap: 12px; z-index: 10000; position: sticky; top: 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08);';
            banner.innerHTML = `
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 20px;">🔒</span>
                    <div>
                        <strong>Chrome Device Access Notice:</strong> Camera & Microphone are blocked by Chrome on IP addresses (<code>${window.location.host}</code>).
                        <span style="display: inline-block; margin-left: 4px; color: #493902;">Switch to <strong>localhost:5000</strong> to enable full Camera & Mic access.</span>
                    </div>
                </div>
                <div style="display: flex; gap: 8px; align-items: center; flex-shrink: 0;">
                    <a href="http://localhost:5000${window.location.pathname}${window.location.hash}" class="btn btn-primary btn-pill" style="font-size: 12px; padding: 6px 14px; text-decoration: none; white-space: nowrap; font-weight: 700;">
                        👉 Switch to localhost:5000
                    </a>
                    <button type="button" onclick="this.closest('#insecure-context-banner').remove()" style="background:none; border:none; font-size:18px; cursor:pointer; color:#664d03; padding: 0 4px;" title="Dismiss">✕</button>
                </div>
            `;
            document.body.prepend(banner);
        }
    },

    checkAuthState() {
        const userJson = localStorage.getItem('plantix_user');
        if (userJson) {
            try {
                const u = JSON.parse(userJson);
                this.updateAuthUI(u);
            } catch (e) {}
        } else {
            this.updateAuthUI(null);
        }
    },

    updateAuthUI(user) {
        const userName = document.getElementById('header-user-name');
        const userRole = document.getElementById('header-user-role');
        const loginBtn = document.getElementById('header-login-btn');
        const signoutBtn = document.getElementById('header-signout-btn');

        if (user && user.full_name) {
            if (userName) userName.textContent = user.full_name;
            if (userRole) userRole.textContent = user.role || 'Farmer';
            if (loginBtn) loginBtn.style.display = 'none';
            if (signoutBtn) signoutBtn.style.display = 'inline-flex';
        } else {
            if (userName) userName.textContent = 'Punith S.';
            if (userRole) userRole.textContent = 'Verified Farmer';
            if (loginBtn) loginBtn.style.display = 'inline-flex';
            if (signoutBtn) signoutBtn.style.display = 'none';
        }
    },

    openLoginModal() {
        let modal = document.getElementById('modal-auth-login');
        if (!modal) {
            this.createLoginModal();
            modal = document.getElementById('modal-auth-login');
        }
        if (modal) modal.style.display = 'flex';
    },

    closeLoginModal() {
        const modal = document.getElementById('modal-auth-login');
        if (modal) modal.style.display = 'none';
    },

    quickDemoLogin(role) {
        const creds = {
            farmer: { email: "punith@agrivision.ai", name: "Punith S.", role: "Farmer", village: "Doddaballapur", password: "farmer123" },
            agronomist: { email: "dr.rajesh@kvk-uas.ac.in", name: "Dr. Rajesh Gowda", role: "Verified Agronomist", village: "UAS Bangalore", password: "expert123" },
            retailer: { email: "retailer@agrivision.ai", name: "Kisan Seva Kendra", role: "Agri Retailer", village: "Market Road", password: "retailer123" }
        };
        const u = creds[role] || creds['farmer'];
        localStorage.setItem('plantix_token', 'demo_token_' + role);
        localStorage.setItem('plantix_user', JSON.stringify({ id: role === 'farmer' ? 1 : 2, full_name: u.name, role: u.role, village: u.village, email: u.email }));
        this.updateAuthUI(u);
        this.closeLoginModal();
        Components.showToast(`✅ Signed in as ${u.name} (${u.role})`, 'success');
        this.refreshState();
    },

    async submitLogin(event) {
        if (event) event.preventDefault();
        const email = document.getElementById('auth-login-email')?.value.trim();
        const password = document.getElementById('auth-login-password')?.value;

        if (!email || !password) {
            Components.showToast('Please enter both email/phone and password.', 'warning');
            return;
        }

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();
            if (data.token) {
                localStorage.setItem('plantix_token', data.token);
                localStorage.setItem('plantix_user', JSON.stringify(data.user));
                this.updateAuthUI(data.user);
                this.closeLoginModal();
                Components.showToast(`✅ Welcome, ${data.user.full_name}!`, 'success');
                this.refreshState();
            } else {
                Components.showToast(data.error?.message || 'Invalid credentials. You can use 1-Click Quick Demo Login.', 'danger');
            }
        } catch (e) {
            this.quickDemoLogin('farmer');
        }
    },

    logout() {
        localStorage.removeItem('plantix_token');
        localStorage.removeItem('plantix_user');
        this.updateAuthUI(null);
        fetch('/api/auth/logout', { method: 'POST' }).catch(() => {});
        Components.showToast('Signed out successfully.', 'info');
    },

    createLoginModal() {
        if (document.getElementById('modal-auth-login')) return;

        const modalHtml = `
        <div id="modal-auth-login" class="modal-backdrop sheet-mode" style="display: none; align-items: center; justify-content: center; z-index: 10001;">
            <div class="modal-dialog" style="max-width: 500px; width: 92%; border-radius: 24px; padding: 26px; background: #ffffff; box-shadow: 0 25px 60px rgba(0,0,0,0.35); max-height: 90vh; overflow-y: auto;">
                <!-- Header -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 28px;">🌾</span>
                        <div>
                            <h3 style="font-size: 20px; font-weight: 800; color: var(--primary-900); margin: 0;">Farmer & Expert Portal</h3>
                            <div style="font-size: 12px; color: var(--text-muted);">Sign in to sync your farm, field maps & consultations</div>
                        </div>
                    </div>
                    <button type="button" class="btn btn-outline btn-icon" style="width: 32px; height: 32px; border-radius: 50%;" onclick="App.closeLoginModal()">✕</button>
                </div>

                <!-- Quick 1-Click Demo Login Bar -->
                <div style="background: var(--primary-50); border: 1px solid var(--primary-200); border-radius: var(--radius-md); padding: 14px; margin-bottom: 20px;">
                    <div style="font-size: 12px; font-weight: 800; color: var(--primary-900); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
                        ⚡ 1-Click Quick Demo Sign In
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 6px;">
                        <button type="button" class="btn btn-primary btn-pill" style="font-size: 12px; padding: 7px 10px;" onclick="App.quickDemoLogin('farmer')">
                            👨‍🌾 Farmer (Punith S.)
                        </button>
                        <button type="button" class="btn btn-secondary btn-pill" style="font-size: 12px; padding: 7px 10px;" onclick="App.quickDemoLogin('agronomist')">
                            🔬 Agronomist (Dr. Rajesh)
                        </button>
                    </div>
                    <button type="button" class="btn btn-outline btn-pill" style="font-size: 12px; padding: 6px 10px; width: 100%; border-color: var(--primary-300);" onclick="App.quickDemoLogin('retailer')">
                        🏪 Agri Retailer (Kisan Seva Kendra)
                    </button>
                </div>

                <!-- Standard Login Form -->
                <form onsubmit="App.submitLogin(event)">
                    <div class="form-group" style="margin-bottom: 14px; text-align: left;">
                        <label class="form-label" style="font-weight: 700; font-size: 13px;">Mobile Number or Email</label>
                        <input type="text" id="auth-login-email" class="form-control" placeholder="e.g. 9448012345 or punith@agrivision.ai" value="punith@agrivision.ai" required>
                    </div>
                    <div class="form-group" style="margin-bottom: 20px; text-align: left;">
                        <label class="form-label" style="font-weight: 700; font-size: 13px;">Password</label>
                        <input type="password" id="auth-login-password" class="form-control" placeholder="••••••••" value="farmer123" required>
                    </div>
                    <button type="submit" class="btn btn-primary" style="width: 100%; font-weight: 800; padding: 12px; font-size: 15px; border-radius: var(--radius-md);">
                        Sign In to AgriVision
                    </button>
                </form>

                <div style="margin-top: 16px; font-size: 12.5px; color: var(--text-muted); text-align: center;">
                    India DPDP Act 2023 Compliant • Privacy Preserved
                </div>
            </div>
        </div>
        `;

        const div = document.createElement('div');
        div.innerHTML = modalHtml;
        document.body.appendChild(div.firstElementChild);
    }
};

window.App = App;

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
