/**
 * Plantix AI Offline Storage Manager (IndexedDB)
 * Handles client-side offline storage for farms, crops, diagnosis history,
 * agricultural guides, and pending sync queues.
 */

const OfflineStorage = (() => {
    const DB_NAME = 'PlantixOfflineDB';
    const DB_VERSION = 1;
    let dbInstance = null;

    function openDatabase() {
        return new Promise((resolve, reject) => {
            if (dbInstance) {
                return resolve(dbInstance);
            }
            const req = indexedDB.open(DB_NAME, DB_VERSION);

            req.onupgradeneeded = (e) => {
                const db = e.target.result;
                if (!db.objectStoreNames.contains('app_state')) {
                    db.createObjectStore('app_state', { keyPath: 'key' });
                }
                if (!db.objectStoreNames.contains('offline_diagnoses')) {
                    db.createObjectStore('offline_diagnoses', { keyPath: 'client_uuid' });
                }
                if (!db.objectStoreNames.contains('offline_guides')) {
                    db.createObjectStore('offline_guides', { keyPath: 'id' });
                }
                if (!db.objectStoreNames.contains('sync_queue')) {
                    const queueStore = db.createObjectStore('sync_queue', { keyPath: 'client_uuid' });
                    queueStore.createIndex('status', 'status', { unique: false });
                    queueStore.createIndex('timestamp', 'timestamp', { unique: false });
                }
            };

            req.onsuccess = (e) => {
                dbInstance = e.target.result;
                resolve(dbInstance);
            };

            req.onerror = (e) => {
                console.error('[OfflineStorage] IndexedDB Open Error:', e.target.error);
                reject(e.target.error);
            };
        });
    }

    async function setAppState(state) {
        try {
            const db = await openDatabase();
            const tx = db.transaction('app_state', 'readwrite');
            const store = tx.objectStore('app_state');
            store.put({ key: 'cached_state', data: state, updatedAt: Date.now() });
        } catch (err) {
            console.warn('[OfflineStorage] Failed to cache app state:', err);
        }
    }

    async function getAppState() {
        try {
            const db = await openDatabase();
            return new Promise((resolve) => {
                const tx = db.transaction('app_state', 'readonly');
                const store = tx.objectStore('app_state');
                const req = store.get('cached_state');
                req.onsuccess = () => resolve(req.result ? req.result.data : null);
                req.onerror = () => resolve(null);
            });
        } catch (err) {
            return null;
        }
    }

    async function enqueueSyncItem(entityType, payload) {
        const db = await openDatabase();
        const client_uuid = payload.client_uuid || (crypto.randomUUID ? crypto.randomUUID() : 'uuid_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9));
        payload.client_uuid = client_uuid;

        const queueItem = {
            client_uuid,
            entity_type: entityType,
            payload,
            timestamp: Date.now(),
            status: 'pending', // 'pending' | 'syncing' | 'synced' | 'failed'
            retries: 0,
            last_error: null
        };

        return new Promise((resolve, reject) => {
            const tx = db.transaction('sync_queue', 'readwrite');
            const store = tx.objectStore('sync_queue');
            store.put(queueItem);
            tx.oncomplete = () => {
                console.log(`[OfflineStorage] Enqueued ${entityType} for sync:`, client_uuid);
                resolve(queueItem);
            };
            tx.onerror = (e) => reject(e.target.error);
        });
    }

    async function getPendingSyncQueue() {
        try {
            const db = await openDatabase();
            return new Promise((resolve) => {
                const tx = db.transaction('sync_queue', 'readonly');
                const store = tx.objectStore('sync_queue');
                const req = store.getAll();
                req.onsuccess = () => {
                    const items = (req.result || []).filter(item => item.status === 'pending' || item.status === 'failed');
                    resolve(items);
                };
                req.onerror = () => resolve([]);
            });
        } catch (err) {
            return [];
        }
    }

    async function markSyncItemSuccess(clientUuid, serverId) {
        try {
            const db = await openDatabase();
            const tx = db.transaction(['sync_queue', 'offline_diagnoses'], 'readwrite');
            const qStore = tx.objectStore('sync_queue');
            qStore.delete(clientUuid);

            // Also update status in offline_diagnoses store if present
            const diagStore = tx.objectStore('offline_diagnoses');
            const getReq = diagStore.get(clientUuid);
            getReq.onsuccess = () => {
                if (getReq.result) {
                    const diag = getReq.result;
                    diag.sync_status = 'synced';
                    diag.server_id = serverId;
                    diagStore.put(diag);
                }
            };
        } catch (err) {
            console.error('[OfflineStorage] Error marking sync success:', err);
        }
    }

    async function markSyncItemFailed(clientUuid, errorMsg) {
        try {
            const db = await openDatabase();
            const tx = db.transaction('sync_queue', 'readwrite');
            const store = tx.objectStore('sync_queue');
            const req = store.get(clientUuid);
            req.onsuccess = () => {
                if (req.result) {
                    const item = req.result;
                    item.status = 'failed';
                    item.retries = (item.retries || 0) + 1;
                    item.last_error = errorMsg;
                    store.put(item);
                }
            };
        } catch (err) {
            console.error('[OfflineStorage] Error marking sync failed:', err);
        }
    }

    async function saveOfflineDiagnosis(diagRecord) {
        const db = await openDatabase();
        return new Promise((resolve, reject) => {
            const tx = db.transaction('offline_diagnoses', 'readwrite');
            const store = tx.objectStore('offline_diagnoses');
            store.put(diagRecord);
            tx.oncomplete = () => resolve(diagRecord);
            tx.onerror = (e) => reject(e.target.error);
        });
    }

    async function getOfflineDiagnoses() {
        try {
            const db = await openDatabase();
            return new Promise((resolve) => {
                const tx = db.transaction('offline_diagnoses', 'readonly');
                const store = tx.objectStore('offline_diagnoses');
                const req = store.getAll();
                req.onsuccess = () => resolve(req.result || []);
                req.onerror = () => resolve([]);
            });
        } catch (err) {
            return [];
        }
    }

    async function saveGuides(guides) {
        try {
            const db = await openDatabase();
            const tx = db.transaction('offline_guides', 'readwrite');
            const store = tx.objectStore('offline_guides');
            guides.forEach(g => store.put(g));
        } catch (err) {
            console.warn('[OfflineStorage] Error caching guides:', err);
        }
    }

    async function getGuides() {
        try {
            const db = await openDatabase();
            return new Promise((resolve) => {
                const tx = db.transaction('offline_guides', 'readonly');
                const store = tx.objectStore('offline_guides');
                const req = store.getAll();
                req.onsuccess = () => resolve(req.result || []);
                req.onerror = () => resolve([]);
            });
        } catch (err) {
            return [];
        }
    }

    return {
        init: openDatabase,
        setAppState,
        getAppState,
        enqueueSyncItem,
        getPendingSyncQueue,
        markSyncItemSuccess,
        markSyncItemFailed,
        saveOfflineDiagnosis,
        getOfflineDiagnoses,
        saveGuides,
        getGuides
    };
})();
