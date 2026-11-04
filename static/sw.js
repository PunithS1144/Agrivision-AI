/**
 * Plantix AI Service Worker (PWA Offline Cache v8)
 * Network-first strategy for dynamic updates with robust offline fallback.
 */

const CACHE_NAME = 'plantix-cache-v13';
const STATIC_ASSETS = [
    '/',
    '/static/css/design-system.css',
    '/static/css/components.css',
    '/static/css/layout.css',
    '/static/js/i18n.js',
    '/static/js/voice-assistant.js',
    '/static/js/offline-storage.js',
    '/static/js/edge-inference.js',
    '/static/js/smart-camera.js',
    '/static/js/sync-manager.js',
    '/static/js/components.js',
    '/static/js/diagnosis.js',
    '/static/js/calculator.js',
    '/static/js/weather.js',
    '/static/js/precision-map.js',
    '/static/js/community.js',
    '/static/js/marketplace.js',
    '/static/js/app.js'
];

self.addEventListener('install', (event) => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[ServiceWorker v6] Pre-caching static assets for offline use...');
            return cache.addAll(STATIC_ASSETS).catch((err) => {
                console.warn('[ServiceWorker] Pre-cache partial fail (safe to ignore in dev):', err);
            });
        })
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.map((key) => {
                    if (key !== CACHE_NAME) {
                        console.log('[ServiceWorker] Purging obsolete cache:', key);
                        return caches.delete(key);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    // Only handle GET requests
    if (event.request.method !== 'GET') {
        return;
    }

    const url = new URL(event.request.url);

    // Bypass API calls that require real-time freshness
    if (url.pathname.startsWith('/api/')) {
        return;
    }

    // Network-First with Cache Fallback for static assets and HTML pages
    // Ensures users always get the freshest bugfixes while retaining offline capability
    event.respondWith(
        fetch(event.request)
            .then((networkResponse) => {
                if (networkResponse && networkResponse.status === 200) {
                    const responseClone = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
                }
                return networkResponse;
            })
            .catch(() => {
                return caches.match(event.request).then((cachedResponse) => {
                    if (cachedResponse) return cachedResponse;
                    if (event.request.headers.get('accept')?.includes('text/html')) {
                        return caches.match('/');
                    }
                    return new Response('Network error or resource offline', {
                        status: 503,
                        statusText: 'Service Unavailable',
                        headers: { 'Content-Type': 'text/plain' }
                    });
                });
            })
    );
});
