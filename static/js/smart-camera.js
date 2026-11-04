/**
 * Plantix AI Smart Camera System
 * Provides real-time interactive viewfinder guidance:
 * - Leaf positioning target reticle
 * - Live blur / motion detection via Laplacian convolution
 * - Exposure / luminance meter (underexposure / glare warnings)
 * - Distance & leaf framing guidance (move closer / too close)
 * - Live quality score meter (0 - 100%)
 * - Auto-capture readiness feedback
 */

const SmartCamera = (() => {
    let mediaStream = null;
    let videoEl = null;
    let canvasEl = null;
    let overlayEl = null;
    let animationFrameId = null;
    let onCaptureCallback = null;
    let isAnalyzing = false;

    // Real-time analysis metrics
    let latestMetrics = {
        brightness: 0,
        blurScore: 0,
        coveragePercent: 0,
        overallQuality: 0,
        guidance: "Align leaf in target reticle",
        isReady: false
    };

    function createCameraModal() {
        if (document.getElementById('smart-camera-modal')) return;

        const modalHtml = `
        <div id="smart-camera-modal" class="smart-camera-backdrop" style="display: none;">
            <div class="smart-camera-viewfinder">
                <!-- Top Toolbar -->
                <div class="camera-topbar">
                    <button class="camera-icon-btn" onclick="SmartCamera.close()">✕</button>
                    <div class="camera-quality-pill" id="camera-quality-pill">
                        <span class="dot" id="quality-status-dot"></span>
                        <span id="quality-percent-text">Quality: 0%</span>
                    </div>
                    <button class="camera-icon-btn" id="camera-switch-btn" title="Switch Camera" onclick="SmartCamera.switchCamera()">🔄</button>
                </div>

                <!-- Video Viewfinder Stream -->
                <div class="camera-stream-wrapper">
                    <video id="smart-camera-video" playsinline autoplay muted></video>
                    <canvas id="smart-camera-analysis-canvas" style="display: none;"></canvas>

                    <!-- Leaf Positioning Reticle Overlay -->
                    <div class="camera-reticle" id="camera-reticle">
                        <div class="reticle-corner top-left"></div>
                        <div class="reticle-corner top-right"></div>
                        <div class="reticle-corner bottom-left"></div>
                        <div class="reticle-corner bottom-right"></div>
                        <div class="reticle-leaf-icon">🍃</div>
                    </div>

                    <!-- Live Guidance Banner -->
                    <div class="camera-guidance-banner" id="camera-guidance-banner">
                        <span id="guidance-icon">ℹ️</span>
                        <span id="guidance-text">Center the diseased leaf within the green brackets</span>
                    </div>
                </div>

                <!-- Real-time HUD Metrics Bar -->
                <div class="camera-hud-metrics">
                    <div class="hud-item">
                        <span class="hud-label">Lighting</span>
                        <span class="hud-val" id="hud-lighting-val">--</span>
                    </div>
                    <div class="hud-item">
                        <span class="hud-label">Stability</span>
                        <span class="hud-val" id="hud-blur-val">--</span>
                    </div>
                    <div class="hud-item">
                        <span class="hud-label">Framing</span>
                        <span class="hud-val" id="hud-distance-val">--</span>
                    </div>
                </div>

                <!-- Bottom Capture Controls -->
                <div class="camera-controls">
                    <button type="button" class="btn btn-outline btn-pill" style="color: #fff; border-color: rgba(255,255,255,0.4);" onclick="SmartCamera.close()">
                        Cancel
                    </button>

                    <button type="button" class="camera-shutter-btn" id="camera-shutter-btn" onclick="SmartCamera.captureSnapshot()">
                        <div class="shutter-inner"></div>
                    </button>

                    <button type="button" class="btn btn-outline btn-pill" style="color: #fff; border-color: rgba(255,255,255,0.4);" onclick="document.getElementById('leaf-file-input').click(); SmartCamera.close();">
                        Gallery
                    </button>
                </div>

                <!-- Fallback / Permission Assistance Overlay -->
                <div id="camera-fallback-card" style="display: none; position: absolute; inset: 0; background: rgba(18, 30, 20, 0.96); z-index: 20; padding: 24px; flex-direction: column; align-items: center; justify-content: center; text-align: center; color: #fff; border-radius: 20px;">
                    <span style="font-size: 52px; margin-bottom: 12px;" id="camera-fallback-icon">🔒</span>
                    <h3 style="font-size: 19px; font-weight: 800; margin-bottom: 8px; color: #fff;" id="camera-fallback-title">Camera Access Blocked</h3>
                    <div style="font-size: 13.5px; color: rgba(255,255,255,0.85); max-width: 380px; line-height: 1.6; margin-bottom: 22px;" id="camera-fallback-desc">
                        Chrome requires a secure context or permission to access your camera.
                    </div>
                    <div id="camera-fallback-actions" style="display: flex; flex-direction: column; gap: 10px; width: 100%; max-width: 320px;">
                        <button type="button" class="btn btn-primary btn-pill" id="camera-switch-origin-btn" style="display: none; padding: 10px; font-weight: 800;" onclick="window.location.href = 'http://localhost:5000' + window.location.pathname + window.location.hash;">
                            👉 Switch to http://localhost:5000
                        </button>
                        <button type="button" class="btn btn-primary btn-pill" style="padding: 10px; font-weight: 700; background: #2e7d32; border-color: #2e7d32;" onclick="SmartCamera.close(); const cam = document.getElementById('leaf-camera-input') || document.getElementById('leaf-file-input'); if(cam) cam.click();">
                            📸 Snap with Phone / Device Camera
                        </button>
                        <button type="button" class="btn btn-outline btn-pill" style="color: #fff; border-color: rgba(255,255,255,0.7); padding: 9px; font-weight: 600;" onclick="SmartCamera.close(); document.getElementById('leaf-file-input').click();">
                            📁 Choose Photo from Files / Gallery
                        </button>
                        <button type="button" class="btn btn-outline btn-pill" style="color: #fff; border-color: rgba(255,255,255,0.4); padding: 8px;" onclick="SmartCamera.retry()">
                            🔄 Retry Viewfinder
                        </button>
                        <button type="button" class="btn btn-outline btn-pill" style="color: rgba(255,255,255,0.6); border: none; padding: 6px;" onclick="SmartCamera.close()">
                            Close Viewfinder
                        </button>
                    </div>
                </div>
            </div>
        </div>
        `;

        const div = document.createElement('div');
        div.innerHTML = modalHtml;
        document.body.appendChild(div.firstElementChild);

        videoEl = document.getElementById('smart-camera-video');
        canvasEl = document.getElementById('smart-camera-analysis-canvas');
        overlayEl = document.getElementById('camera-reticle');
    }

    async function openCamera(callback) {
        createCameraModal();
        onCaptureCallback = callback;

        const modal = document.getElementById('smart-camera-modal');
        const fallbackCard = document.getElementById('camera-fallback-card');
        if (fallbackCard) fallbackCard.style.display = 'none';
        modal.style.display = 'flex';

        // Check if browser context blocks media devices
        const isLocal = ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname);
        if (!window.isSecureContext && !isLocal) {
            showCameraError({
                name: 'InsecureContext',
                message: 'Chrome strictly restricts camera access to secure origins. You are currently on an IP address.'
            });
            return;
        }

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            showCameraError({
                name: 'NotSupported',
                message: 'Camera device API is not supported or was blocked by Chrome security policy.'
            });
            return;
        }

        try {
            const constraints = {
                video: {
                    facingMode: { ideal: "environment" },
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                },
                audio: false
            };

            try {
                mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
            } catch (idealErr) {
                console.warn('[SmartCamera] Ideal 720p environment camera failed, falling back to basic webcam...', idealErr);
                mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
            }

            videoEl.srcObject = mediaStream;
            await videoEl.play();

            isAnalyzing = true;
            startRealtimeAnalysis();
        } catch (err) {
            console.warn('[SmartCamera] Camera stream access rejected or unavailable:', err);
            showCameraError(err);
        }
    }

    function showCameraError(err) {
        const fallbackCard = document.getElementById('camera-fallback-card');
        const titleEl = document.getElementById('camera-fallback-title');
        const descEl = document.getElementById('camera-fallback-desc');
        const switchBtn = document.getElementById('camera-switch-origin-btn');

        if (!fallbackCard) return;

        const isLocal = ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname);

        if (!window.isSecureContext && !isLocal) {
            if (titleEl) titleEl.textContent = "Chrome Blocks Camera on IP Address";
            if (descEl) descEl.innerHTML = "Chrome requires a secure origin (localhost or HTTPS) to access the camera.<br><br>👉 Switch to <strong>http://localhost:5000</strong> in Chrome to enable full live camera access, or upload a leaf photo from your files below.";
            if (switchBtn) switchBtn.style.display = 'inline-block';
        } else if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
            if (titleEl) titleEl.textContent = "Camera Permission Denied in Chrome";
            if (descEl) descEl.innerHTML = "1. Click the <strong>Tune / Lock icon 🎛️</strong> next to <code>localhost:5000</code> in Chrome's address bar.<br>2. Set <strong>Camera</strong> to <strong>Allow</strong>.<br>3. Reload this page or tap Retry below.";
            if (switchBtn) switchBtn.style.display = 'none';
        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
            if (titleEl) titleEl.textContent = "No Camera Hardware Found";
            if (descEl) descEl.textContent = "No webcam or external camera was detected on this device. You can choose a photo from your files below.";
            if (switchBtn) switchBtn.style.display = 'none';
        } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
            if (titleEl) titleEl.textContent = "Camera in Use by Another Application";
            if (descEl) descEl.textContent = "Your camera is currently opened by another app (e.g. Zoom, Google Meet, or another browser window). Please close that app and retry.";
            if (switchBtn) switchBtn.style.display = 'none';
        } else {
            if (titleEl) titleEl.textContent = "Unable to Open Camera Viewfinder";
            if (descEl) descEl.textContent = "Chrome was unable to start the camera stream. You can upload a leaf photograph directly.";
            if (switchBtn) switchBtn.style.display = 'none';
        }

        fallbackCard.style.display = 'flex';
    }

    function retry() {
        if (onCaptureCallback) {
            openCamera(onCaptureCallback);
        }
    }

    function closeCamera() {
        isAnalyzing = false;
        if (animationFrameId) cancelAnimationFrame(animationFrameId);

        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
            mediaStream = null;
        }

        const modal = document.getElementById('smart-camera-modal');
        if (modal) modal.style.display = 'none';
    }

    /**
     * Continuous 5 FPS Canvas Analysis Loop:
     * - Downsamples video frame to 160x120 for zero battery & memory drain
     * - Evaluates brightness, blur (Laplacian variance), green foliage coverage
     */
    function startRealtimeAnalysis() {
        if (!isAnalyzing || !videoEl || videoEl.paused || videoEl.ended) return;

        const ctx = canvasEl.getContext('2d', { willReadFrequently: true });
        const W = 160;
        const H = 120;
        canvasEl.width = W;
        canvasEl.height = H;

        ctx.drawImage(videoEl, 0, 0, W, H);
        const imgData = ctx.getImageData(0, 0, W, H);
        const data = imgData.data;

        let totalBrightness = 0;
        let greenPixels = 0;
        const gray = new Uint8Array(W * H);

        for (let i = 0, p = 0; i < data.length; i += 4, p++) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            const lum = 0.299 * r + 0.587 * g + 0.114 * b;
            gray[p] = lum;
            totalBrightness += lum;

            // Foliage detection (Green Dominance)
            if (g > 50 && g > r * 0.95 && g > b * 1.1) {
                greenPixels++;
            }
        }

        const totalPixels = W * H;
        const avgBrightness = totalBrightness / totalPixels;
        const plantCoverage = (greenPixels / totalPixels) * 100;

        // Laplacian Variance for Blur Estimation
        let lapSum = 0;
        let lapSqSum = 0;
        let count = 0;

        for (let y = 1; y < H - 1; y += 2) {
            for (let x = 1; x < W - 1; x += 2) {
                const center = gray[y * W + x];
                const top = gray[(y - 1) * W + x];
                const bottom = gray[(y + 1) * W + x];
                const left = gray[y * W + (x - 1)];
                const right = gray[y * W + (x + 1)];

                const lap = top + bottom + left + right - 4 * center;
                lapSum += lap;
                lapSqSum += lap * lap;
                count++;
            }
        }

        const meanLap = lapSum / count;
        const blurScore = (lapSqSum / count) - (meanLap * meanLap);

        // Update HUD metrics
        updateGuidanceUI(avgBrightness, blurScore, plantCoverage);

        // Run analysis at ~8 FPS to prevent mobile overheating
        setTimeout(() => {
            if (isAnalyzing) animationFrameId = requestAnimationFrame(startRealtimeAnalysis);
        }, 120);
    }

    function updateGuidanceUI(brightness, blurScore, plantCoverage) {
        const hudLight = document.getElementById('hud-lighting-val');
        const hudBlur = document.getElementById('hud-blur-val');
        const hudDist = document.getElementById('hud-distance-val');
        const guidanceText = document.getElementById('guidance-text');
        const guidanceIcon = document.getElementById('guidance-icon');
        const qualityDot = document.getElementById('quality-status-dot');
        const qualityText = document.getElementById('quality-percent-text');
        const reticle = document.getElementById('camera-reticle');
        const shutterBtn = document.getElementById('camera-shutter-btn');

        let qualityScore = 100;
        let guidance = "Excellent framing! Hold steady and tap shutter.";
        let icon = "✅";
        let isReady = true;

        // 1. Lighting Guidance
        if (brightness < 42) {
            hudLight.textContent = "Too Dark";
            hudLight.style.color = "#ff5252";
            qualityScore -= 40;
            guidance = "Too dark: Move to daylight or turn on torch";
            icon = "💡";
            isReady = false;
        } else if (brightness > 225) {
            hudLight.textContent = "Harsh Glare";
            hudLight.style.color = "#ffa726";
            qualityScore -= 30;
            guidance = "Harsh glare: Shield camera from direct sun";
            icon = "☀️";
            isReady = false;
        } else {
            hudLight.textContent = "Optimal";
            hudLight.style.color = "#4caf50";
        }

        // 2. Blur / Motion Guidance
        if (blurScore < 10) {
            hudBlur.textContent = "Blurry";
            hudBlur.style.color = "#ff5252";
            qualityScore -= 35;
            guidance = "Steady your smartphone to reduce motion blur";
            icon = "✋";
            isReady = false;
        } else {
            hudBlur.textContent = "Sharp";
            hudBlur.style.color = "#4caf50";
        }

        // 3. Distance & Framing Guidance
        if (plantCoverage < 25) {
            hudDist.textContent = "Too Far";
            hudDist.style.color = "#ffa726";
            qualityScore -= 35;
            guidance = "Move closer: Leaf should fill 60-80% of reticle";
            icon = "🔍";
            isReady = false;
        } else if (plantCoverage > 92) {
            hudDist.textContent = "Too Close";
            hudDist.style.color = "#ffa726";
            qualityScore -= 20;
            guidance = "Move slightly back to frame leaf margins";
            icon = "📐";
        } else {
            hudDist.textContent = "Aligned";
            hudDist.style.color = "#4caf50";
        }

        qualityScore = Math.max(10, Math.min(98, Math.round(qualityScore)));

        // Update UI elements
        if (hudLight && hudBlur && hudDist) {
            guidanceText.textContent = guidance;
            guidanceIcon.textContent = icon;
            qualityText.textContent = `Quality: ${qualityScore}%`;

            if (isReady && qualityScore >= 70) {
                qualityDot.style.background = "#4caf50";
                reticle.classList.add('ready');
                reticle.classList.remove('warning');
                shutterBtn.classList.add('ready');
            } else {
                qualityDot.style.background = qualityScore >= 50 ? "#ffa726" : "#ff5252";
                reticle.classList.remove('ready');
                reticle.classList.add('warning');
                shutterBtn.classList.remove('ready');
            }
        }

        latestMetrics = {
            brightness,
            blurScore,
            coveragePercent: plantCoverage,
            overallQuality: qualityScore,
            guidance,
            isReady
        };
    }

    /**
     * Freezes frame, captures high-res image, and forwards to diagnosis pipeline.
     */
    function captureSnapshot() {
        if (!videoEl) return;

        // Sound / flash effect
        const shutter = document.getElementById('camera-shutter-btn');
        if (shutter) shutter.classList.add('flash');
        setTimeout(() => shutter && shutter.classList.remove('flash'), 200);

        const captureCanvas = document.createElement('canvas');
        captureCanvas.width = videoEl.videoWidth || 1280;
        captureCanvas.height = videoEl.videoHeight || 720;
        const ctx = captureCanvas.getContext('2d');
        ctx.drawImage(videoEl, 0, 0, captureCanvas.width, captureCanvas.height);

        captureCanvas.toBlob((blob) => {
            const capturedFile = new File([blob], `smart_leaf_${Date.now()}.jpg`, { type: 'image/jpeg' });
            closeCamera();
            if (onCaptureCallback) {
                onCaptureCallback(capturedFile, captureCanvas.toDataURL('image/jpeg', 0.9), latestMetrics);
            }
        }, 'image/jpeg', 0.92);
    }

    function switchCamera() {
        // Toggle front/back camera if supported
        closeCamera();
        setTimeout(() => openCamera(onCaptureCallback), 250);
    }

    return {
        open: openCamera,
        close: closeCamera,
        retry,
        captureSnapshot,
        switchCamera,
        getMetrics: () => latestMetrics
    };
})();
