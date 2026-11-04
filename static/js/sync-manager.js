/**
 * Plantix AI Offline Synchronization Manager
 * Coordinates online/offline connectivity events, sync queue processing,
 * batch synchronization with duplicate prevention (client_uuid), and retry handling.
 */

const SyncManager = (() => {
    let isOnline = navigator.onLine;
    let isSyncing = false;
    let syncIntervalId = null;

    function init() {
        // Listen to browser network state transitions
        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        updateConnectivityUI();

        // Check pending queue immediately on launch
        setTimeout(checkAndSyncPendingItems, 2000);

        // Periodically verify sync queue if online
        syncIntervalId = setInterval(() => {
            if (isOnline && !isSyncing) {
                checkAndSyncPendingItems();
            }
        }, 30000);
    }

    function handleOnline() {
        isOnline = true;
        console.log('[SyncManager] Network restored. Online mode active.');
        updateConnectivityUI();
        Components.showToast('🌐 Internet connection restored. Syncing offline records...', 'success');
        checkAndSyncPendingItems();
    }

    function handleOffline() {
        isOnline = false;
        console.warn('[SyncManager] Internet disconnected. Offline mode active.');
        updateConnectivityUI();
        Components.showToast('📶 You are in Offline Mode. Diagnoses and records will be saved locally.', 'warning');
    }

    function updateConnectivityUI() {
        const statusBadge = document.getElementById('network-status-badge');
        const syncBadge = document.getElementById('pending-sync-badge');
        const offlineBanner = document.getElementById('global-offline-banner');

        if (statusBadge) {
            if (isOnline) {
                statusBadge.className = 'network-pill online';
                statusBadge.innerHTML = `<span class="dot"></span> Online`;
                statusBadge.title = "Connected to AgriVision Cloud & Meteorological Services";
            } else {
                statusBadge.className = 'network-pill offline';
                statusBadge.innerHTML = `<span class="dot"></span> Offline Mode`;
                statusBadge.title = "Operating with on-device local storage and edge triage";
            }
        }

        if (offlineBanner) {
            offlineBanner.style.display = isOnline ? 'none' : 'block';
        }

        updatePendingCountBadge();
    }

    async function updatePendingCountBadge() {
        const syncBadge = document.getElementById('pending-sync-badge');
        if (!syncBadge) return;

        const queue = await OfflineStorage.getPendingSyncQueue();
        if (queue.length > 0) {
            syncBadge.style.display = 'inline-flex';
            syncBadge.innerHTML = `☁️ ${queue.length} Pending Sync`;
            syncBadge.title = `Click to sync ${queue.length} offline records to the cloud`;
        } else {
            syncBadge.style.display = 'none';
        }
    }

    /**
     * Executes batch synchronization of pending items with duplicate prevention (client_uuid).
     */
    async function checkAndSyncPendingItems() {
        if (!isOnline || isSyncing) return;

        const pendingItems = await OfflineStorage.getPendingSyncQueue();
        if (pendingItems.length === 0) {
            updatePendingCountBadge();
            return;
        }

        isSyncing = true;
        const syncBadge = document.getElementById('pending-sync-badge');
        if (syncBadge) {
            syncBadge.style.display = 'inline-flex';
            syncBadge.innerHTML = `🔄 Syncing (${pendingItems.length})...`;
        }

        console.log(`[SyncManager] Syncing ${pendingItems.length} pending items to backend...`);

        try {
            const batchPayload = {
                items: pendingItems.map(item => ({
                    client_uuid: item.client_uuid,
                    entity_type: item.entity_type,
                    payload: item.payload
                }))
            };

            const response = await fetch('/api/sync/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(batchPayload)
            });

            if (!response.ok) {
                throw new Error(`Sync HTTP Error: ${response.status}`);
            }

            const data = await response.json();
            console.log('[SyncManager] Sync batch response:', data);

            // Mark each successfully processed item
            if (data.items && Array.isArray(data.items)) {
                for (const resItem of data.items) {
                    await OfflineStorage.markSyncItemSuccess(resItem.client_uuid, resItem.server_id);
                }
            }

            Components.showToast(`✅ Synced ${data.synced_count} records to cloud database!`, 'success');

            // Refresh app state if online
            if (window.App && typeof window.App.loadState === 'function') {
                window.App.loadState();
            }
        } catch (err) {
            console.error('[SyncManager] Batch sync error:', err);
            // Mark items as failed with retry count
            for (const item of pendingItems) {
                await OfflineStorage.markSyncItemFailed(item.client_uuid, err.message);
            }
        } finally {
            isSyncing = false;
            updateConnectivityUI();
        }
    }

    return {
        init,
        isOnline: () => isOnline,
        triggerSync: checkAndSyncPendingItems,
        updateConnectivityUI,
        updatePendingCountBadge
    };
})();
