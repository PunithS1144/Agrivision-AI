/**
 * Plantix AI Multilingual Voice Assistant Engine
 * Manages Speech-to-Text (STT), Text-to-Speech (TTS), speech rate calibration,
 * permission handling, Voice-First modal, and voice query routing.
 * Fully supports Kannada, Hindi, Telugu, Tamil, Marathi, Bengali, and English.
 */

const VoiceAssistant = (() => {
    let recognition = null;
    let isListening = false;
    let isSpeaking = false;
    let speechRate = 0.95; // Optimal clarity for rural farmers
    let currentCallback = null;
    let lastSpokenText = "";
    let lastSpokenLang = "kn";
    let lastAudioUrl = null;
    let selectedVoiceLang = "kn";

    // Mapping from internal language code to BCP-47 speech tags
    const BCP47_MAP = {
        kn: 'kn-IN',
        hi: 'hi-IN',
        en: 'en-IN',
        te: 'te-IN',
        ta: 'ta-IN',
        mr: 'mr-IN',
        bn: 'bn-IN'
    };

    const LANG_NAMES = {
        kn: "🌾 ಕನ್ನಡ (Kannada)",
        hi: "🇮🇳 हिंदी (Hindi)",
        te: "🌿 తెలుగు (Telugu)",
        ta: "🍃 தமிழ் (Tamil)",
        mr: "🚜 मराठी (Marathi)",
        bn: "🌾 বাংলা (Bengali)",
        en: "🌐 English"
    };

    // Quick suggestion chips per language
    const SUGGESTIONS = {
        kn: [
            "ಟೊಮೇಟೊ ಎಲೆ ಹಳದಿ ಆಗಲು ಕಾರಣವೇನು?",
            "ಮೆಣಸಿನಕಾಯಿ ಎಲೆ ಮುದುಡು ರೋಗಕ್ಕೆ ಪರಿಹಾರವೇನು?",
            "ಮೆಣಸಿನಕಾಯಿಯ ಪರಿಸ್ಥಿತಿ ಹೇಗಿದೆ ಮತ್ತು ಬೆಳೆ ರಕ್ಷಣೆ ಹೇಗೆ?",
            "ಇಂದು ಬೆಳಿಗ್ಗೆ ಕೀಟನಾಶಕ ಸಿಂಪಡಿಸಬಹುದೇ?",
            "ಆಲೂಗಡ್ಡೆ ಕೊಳೆ ರೋಗ ನಿಯಂತ್ರಣ ಹೇಗೆ?"
        ],
        hi: [
            "टमाटर की पत्तियां पीली क्यों हो रही हैं?",
            "मिर्च में मरोड़िया रोग का क्या इलाज है?",
            "मिर्च की फसल की स्थिति और बचाव के उपाय बताएं",
            "क्या आज कीटनाशक का छिड़काव करना सुरक्षित है?",
            "धान में तना छेदक कीट की रोकथाम कैसे करें?"
        ],
        en: [
            "Why are my tomato leaves turning yellow?",
            "How to treat leaf curl in chili organically?",
            "Chili crop protection and growth guidance",
            "Is today suitable for knapsack spraying?",
            "Dosage of Mancozeb for early blight"
        ],
        te: [
            "టమోటా ఆకులు పసుపు రంగులోకి మారడానికి ಕಾರಣం ఏమిటి?",
            "మిరప ఆకు ముడుత తెగులు నివారణ ఎలా?",
            "ఈ రోజు పురుగుಮందు పిచಿಕారీ చేయవచ్చా?"
        ],
        ta: [
            "தக்காளி இலைகள் மஞ்சள் நிறமாக மாறுவது ஏன்?",
            "மிளகாய் இலை சுருட்டல் நோயை கட்டுப்படுத்துவது எப்படி?",
            "இன்று பூச்சிக்கொல்லி தெளிக்க உகந்த நேரமா?"
        ],
        mr: [
            "टोमॅटोची पाने पिवळी पडण्याची कारणे काय?",
            "मिरचीवरील चुरडा-मुरडा रोगावर काय उपाय आहे?",
            "आज कीटकनाशक फवारणीसाठी योग्य हवामान आहे का?"
        ],
        bn: [
            "টমেটো পাতা হলুদ হয়ে যাওয়ার কারণ কী?",
            "লঙ্কার পাতা কোঁকড়ানো রোগের প্রতিকার কী?",
            "আজ কি স্প্রে করার অনুকূল সময়?"
        ]
    };

    // Smart dual-detection for spoken transcript
    function detectTranscriptLanguage(transcript) {
        if (!transcript) return selectedVoiceLang || 'kn';
        // 1. Native Indic script ranges
        if (/[\u0C80-\u0CFF]/.test(transcript)) return 'kn';
        if (/[\u0900-\u097F]/.test(transcript)) return 'hi';
        if (/[\u0C00-\u0C7F]/.test(transcript)) return 'te';
        if (/[\u0B80-\u0BFF]/.test(transcript)) return 'ta';
        if (/[\u0980-\u09FF]/.test(transcript)) return 'bn';

        // 2. Transliterated / Romanized speech markers
        const lower = transcript.toLowerCase();
        const ROMAN_RULES = [
            { lang: 'kn', patterns: [/\b(nanna|nimage|beku|madodu|enu|gida|ele|haladi|gobbara|kole|roga|roag|koodale|karnataka|namaskara|tumba|en|menasinakayi|paristhiti)\b/i] },
            { lang: 'hi', patterns: [/\b(kya|kaise|kare|rog|patti|peela|khad|kisan|dawai|khet|paani|upchar|ilaj|roktham|namaste|lag|mirch|fasal)\b/i] },
            { lang: 'te', patterns: [/\b(em|cheyali|aaku|pasupu|manta|vyadhi|eruvulu|mandhu|namaskaram|cheyandi)\b/i] },
            { lang: 'ta', patterns: [/\b(enna|seivathu|ilai|manjal|marunthu|eram|noi|vanakkam|seyyavum)\b/i] },
            { lang: 'mr', patterns: [/\b(kay|karave|pane|pivli|khat|aushadh|rog|namaskar)\b/i] },
            { lang: 'bn', patterns: [/\b(ki|korbo|pata|holud|shar|osudh|rog|nomoshkar)\b/i] }
        ];
        for (const rule of ROMAN_RULES) {
            for (const pat of rule.patterns) {
                if (pat.test(lower)) return rule.lang;
            }
        }
        return selectedVoiceLang || 'kn';
    }

    function resetMicUI() {
        const micBtn = document.getElementById('kisan-big-mic-btn');
        if (micBtn) micBtn.classList.remove('listening');
        const ring = document.getElementById('mic-pulse-ring');
        if (ring) ring.classList.remove('active');
        const chatMicBtn = document.getElementById('chat-mic-btn');
        if (chatMicBtn) {
            chatMicBtn.classList.remove('listening');
            chatMicBtn.style.color = '';
            chatMicBtn.style.borderColor = '';
        }
    }

    function getOrCreateRecognition() {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRec) return null;

        if (recognition) {
            try {
                recognition.abort();
            } catch (e) {}
        }

        try {
            recognition = new SpeechRec();
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.maxAlternatives = 1;

            recognition.onstart = () => {
                isListening = true;
                updateVoiceStatus('listening', (window.I18n ? I18n.t('voice_listening') : null) || "Listening... Speak your crop question");
                const micBtn = document.getElementById('kisan-big-mic-btn');
                if (micBtn) micBtn.classList.add('listening');
                const ring = document.getElementById('mic-pulse-ring');
                if (ring) ring.classList.add('active');
                const chatMicBtn = document.getElementById('chat-mic-btn');
                if (chatMicBtn) {
                    chatMicBtn.classList.add('listening');
                    chatMicBtn.style.color = '#e53935';
                    chatMicBtn.style.borderColor = '#e53935';
                }
            };

            recognition.onresult = (event) => {
                if (!event.results || event.results.length === 0) return;
                const result = event.results[0];
                const transcript = result[0].transcript;
                const confidence = result[0].confidence || 0.85;

                // Dynamically detect spoken language live from transcript
                const detected = detectTranscriptLanguage(transcript);
                if (detected && detected !== selectedVoiceLang) {
                    selectedVoiceLang = detected;
                    if (window.App && App.setChatLanguage) {
                        App.setChatLanguage(detected);
                    }
                    updateActiveLangPill();
                }

                const transcriptBox = document.getElementById('voice-transcript-bubble');
                const transcriptText = document.getElementById('voice-transcript-text');
                if (transcriptBox && transcriptText) {
                    transcriptText.textContent = `"${transcript}"`;
                    transcriptBox.style.display = 'block';
                }

                if (result.isFinal) {
                    console.log(`[VoiceAssistant] Recognized (${selectedVoiceLang}): "${transcript}" (Confidence: ${Math.round(confidence * 100)}%)`);
                    updateVoiceStatus('processing', `Processing question in ${selectedVoiceLang.toUpperCase()}...`);
                    if (currentCallback) {
                        currentCallback(transcript, confidence);
                    }
                }
            };

            recognition.onerror = (event) => {
                console.warn('[VoiceAssistant] Speech recognition error:', event.error);
                isListening = false;
                resetMicUI();

                if (event.error === 'not-allowed') {
                    const isLocal = ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname);
                    if (!window.isSecureContext && !isLocal) {
                        showVoicePermissionAlert(
                            "Chrome Blocks Microphone on IP Address",
                            "Chrome restricts the microphone to secure origins. Switch to <strong>http://localhost:5000</strong> in your browser for voice input, or type below.",
                            true
                        );
                        if (window.Components && Components.showToast) {
                            Components.showToast("Switch to http://localhost:5000 to use microphone", "warning");
                        }
                    } else {
                        showVoicePermissionAlert(
                            "Microphone Access Blocked in Chrome",
                            "1. Click the <strong>Tune / Lock icon 🎛️</strong> next to <code>localhost:5000</code> in Chrome's address bar.<br>2. Set <strong>Microphone</strong> to <strong>Allow</strong>.<br>3. Reload this page or tap the mic again.",
                            false
                        );
                        if (window.Components && Components.showToast) {
                            Components.showToast("Microphone blocked. Click the lock icon in Chrome address bar to Allow.", "danger");
                        }
                    }
                } else if (event.error === 'no-speech') {
                    updateVoiceStatus('ready', "No speech detected. Tap mic again or click a suggested question below.");
                    if (window.Components && Components.showToast) {
                        Components.showToast("No speech detected. Tap mic again to speak.", "info");
                    }
                } else if (event.error === 'network') {
                    updateVoiceStatus('ready', "Voice network timeout. You can type your question directly below.");
                    if (window.Components && Components.showToast) {
                        Components.showToast("Voice network timeout. Type question or try again.", "warning");
                    }
                } else if (event.error === 'aborted') {
                    // Normal stop/abort
                } else {
                    updateVoiceStatus('ready', "Voice input stopped. Tap mic to speak again.");
                }
            };

            recognition.onend = () => {
                isListening = false;
                resetMicUI();
            };

            return recognition;
        } catch (e) {
            console.error('[VoiceAssistant] Failed to instantiate SpeechRecognition:', e);
            return null;
        }
    }

    function init() {
        getOrCreateRecognition();
    }

    function openModal() {
        createVoiceModal();
        const modal = document.getElementById('modal-kisan-voice');
        if (modal) {
            modal.style.display = 'flex';
            if (window.App && App.chatLanguage) {
                selectedVoiceLang = App.chatLanguage;
            } else if (!selectedVoiceLang) {
                selectedVoiceLang = 'kn';
            }
            updateActiveLangPill();
            renderSuggestionChips();
        }
    }

    function closeModal() {
        stopListening();
        stopSpeaking();
        const modal = document.getElementById('modal-kisan-voice');
        if (modal) modal.style.display = 'none';
    }

    function updateActiveLangPill() {
        const curLang = selectedVoiceLang || (window.App ? App.chatLanguage : null) || 'kn';
        selectedVoiceLang = curLang;
        document.querySelectorAll('.lang-chip').forEach(btn => {
            if (btn.dataset.lang === curLang) {
                btn.classList.add('btn-primary');
                btn.classList.remove('btn-outline');
            } else {
                btn.classList.remove('btn-primary');
                btn.classList.add('btn-outline');
            }
        });
        const badge = document.getElementById('voice-lang-name-badge');
        if (badge) {
            badge.textContent = LANG_NAMES[curLang] || curLang.toUpperCase();
        }
    }

    function renderSuggestionChips() {
        const curLang = selectedVoiceLang || (window.App ? App.chatLanguage : null) || 'kn';
        const container = document.getElementById('voice-suggestions-container');
        if (!container) return;
        const list = SUGGESTIONS[curLang] || SUGGESTIONS['kn'] || SUGGESTIONS['en'];
        container.innerHTML = list.map(q => `
            <button type="button" class="btn btn-outline btn-pill" style="font-size: 12px; padding: 6px 12px; text-align: left; width: 100%; border-radius: 12px;" onclick="VoiceAssistant.askDirectQuestion('${q.replace(/'/g, "\\'")}')">
                💬 ${q}
            </button>
        `).join('');
    }

    function switchVoiceLang(lang) {
        selectedVoiceLang = lang || 'kn';
        if (window.App && App.setChatLanguage) {
            App.setChatLanguage(selectedVoiceLang);
        }
        updateActiveLangPill();
        renderSuggestionChips();
        stopSpeaking();
        stopListening();
        updateVoiceStatus('ready', `🎙️ Tuned to ${LANG_NAMES[selectedVoiceLang] || selectedVoiceLang}. Tap mic to speak!`);
    }

    function toggleListening() {
        if (isListening) {
            stopListening();
        } else {
            startListening((transcript, confidence) => {
                handleVoiceQuery(transcript);
            });
        }
    }

    function showVoicePermissionAlert(title, desc, isIpOrigin = false) {
        openModal();
        let banner = document.getElementById('voice-permission-banner');
        if (!banner) return;
        const titleEl = document.getElementById('voice-perm-title');
        const descEl = document.getElementById('voice-perm-desc');
        const switchBtn = document.getElementById('voice-switch-origin-btn');

        if (titleEl) titleEl.textContent = title;
        if (descEl) descEl.innerHTML = desc;
        if (switchBtn) switchBtn.style.display = isIpOrigin ? 'inline-block' : 'none';
        banner.style.display = 'block';
    }

    function startListeningForLanguage(targetLang, callback) {
        selectedVoiceLang = targetLang || 'kn';
        updateActiveLangPill();
        startListening(callback);
    }

    function startListening(callback) {
        stopSpeaking();
        currentCallback = callback;
        const curLang = selectedVoiceLang || (window.App ? App.chatLanguage : null) || 'kn';

        const isLocal = ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname);
        if (!window.isSecureContext && !isLocal) {
            showVoicePermissionAlert(
                "Chrome Blocks Microphone on IP Address",
                "Chrome restricts microphone access to secure origins. Please switch to <strong>http://localhost:5000</strong> or type your agricultural question below.",
                true
            );
            updateVoiceStatus('ready', "Microphone restricted by Chrome on IP address.");
            if (window.Components && Components.showToast) {
                Components.showToast("Switch to http://localhost:5000 to use microphone", "warning");
            }
            return;
        }

        const rec = getOrCreateRecognition();
        if (!rec) {
            showVoicePermissionAlert(
                "Speech Recognition Unavailable",
                "Chrome Web Speech API is unavailable in this browser. Please type your question in the box below or click a suggested question.",
                false
            );
            updateVoiceStatus('ready', "Please type your crop question below.");
            if (window.Components && Components.showToast) {
                Components.showToast("Speech recognition not supported in this browser", "warning");
            }
            const input = document.getElementById('voice-fallback-input');
            if (input) input.focus();
            return;
        }

        rec.lang = BCP47_MAP[curLang] || 'kn-IN';
        console.log(`[VoiceAssistant] Starting STT with language: ${rec.lang}`);

        try {
            rec.start();
        } catch (e) {
            console.warn('[VoiceAssistant] Recognition start exception:', e);
            try {
                rec.abort();
                setTimeout(() => {
                    try {
                        const retryRec = getOrCreateRecognition();
                        if (retryRec) {
                            retryRec.lang = BCP47_MAP[curLang] || 'kn-IN';
                            retryRec.start();
                        }
                    } catch (err2) {
                        console.error('[VoiceAssistant] Retry start failed:', err2);
                    }
                }, 100);
            } catch (err3) {}
        }
    }

    function stopListening() {
        if (recognition) {
            try {
                recognition.abort();
            } catch (e) {}
        }
        isListening = false;
        resetMicUI();
    }

    function askDirectQuestion(questionText) {
        const transcriptBox = document.getElementById('voice-transcript-bubble');
        const transcriptText = document.getElementById('voice-transcript-text');
        if (transcriptBox && transcriptText) {
            transcriptText.textContent = `"${questionText}"`;
            transcriptBox.style.display = 'block';
        }
        handleVoiceQuery(questionText);
    }

    function submitManualQuery() {
        const input = document.getElementById('voice-fallback-input');
        if (!input) return;
        const val = input.value.trim();
        if (!val) return;
        askDirectQuestion(val);
        input.value = '';
    }

    async function handleVoiceQuery(userQuery) {
        const detected = detectTranscriptLanguage(userQuery);
        if (detected) {
            selectedVoiceLang = detected;
            if (window.App && App.setChatLanguage) {
                App.setChatLanguage(detected);
            }
            updateActiveLangPill();
        }
        const curLang = selectedVoiceLang || 'kn';
        const respCard = document.getElementById('voice-response-card');
        const respText = document.getElementById('voice-response-text');

        try {
            updateVoiceStatus('processing', (window.I18n ? I18n.t('voice_processing') : null) || `Consulting AI Agronomist in ${LANG_NAMES[curLang] || curLang.toUpperCase()}...`);

            const res = await fetch('/api/voice/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: userQuery,
                    language: curLang
                })
            });

            const data = await res.json();
            if (data.success) {
                const outLang = data.language || curLang;
                lastSpokenText = data.speech_text || data.reply;
                lastSpokenLang = outLang;
                lastAudioUrl = data.audio_url || null;

                if (respCard && respText) {
                    respCard.style.display = 'block';
                    respText.innerHTML = data.reply.replace(/\n/g, '<br>');
                    respCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }

                updateVoiceStatus('ready', `🔊 Speaking response (${outLang.toUpperCase()})...`);
                playVoiceAudio(data.audio_url, lastSpokenText, lastSpokenLang);
            } else {
                updateVoiceStatus('ready', "Could not process query. Tap mic or try another question.");
            }
        } catch (err) {
            console.error('[VoiceAssistant] Query error:', err);
            updateVoiceStatus('ready', "Network issue. Please try typing your question.");
        }
    }

    function playVoiceAudio(audioUrl, fallbackText, lang = 'kn') {
        const audioEl = document.getElementById('voice-response-audio');
        const playIndicator = document.getElementById('voice-audio-playing-indicator');
        const btn = document.getElementById('voice-audio-ctrl-btn');

        if (audioUrl && audioEl) {
            audioEl.src = audioUrl;
            if (playIndicator) playIndicator.style.display = 'flex';
            if (btn) btn.innerHTML = '⏹️ Stop Voice';
            isSpeaking = true;

            audioEl.onended = () => {
                isSpeaking = false;
                if (playIndicator) playIndicator.style.display = 'none';
                if (btn) btn.innerHTML = '🔊 Replay Voice';
                updateVoiceStatus('ready', "✅ Answer complete. Tap mic to ask again!");
            };

            audioEl.onerror = () => {
                console.warn('[VoiceAssistant] Audio stream failed, falling back to Web Speech Synthesis');
                if (playIndicator) playIndicator.style.display = 'none';
                speak(fallbackText, lang);
            };

            const playPromise = audioEl.play();
            if (playPromise !== undefined) {
                playPromise.catch(err => {
                    console.warn('[VoiceAssistant] Audio autoplay blocked, trying speechSynthesis:', err);
                    speak(fallbackText, lang);
                });
            }
        } else {
            speak(fallbackText, lang);
        }
    }

    function speak(text, lang = 'kn') {
        if (!window.speechSynthesis) return;

        window.speechSynthesis.cancel();
        if (window.speechSynthesis.resume) window.speechSynthesis.resume();

        const cleanText = text.replace(/[*#_\x60]/g, '');
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = speechRate;
        const bcp = BCP47_MAP[lang] || 'kn-IN';
        utterance.lang = bcp;

        const voices = window.speechSynthesis.getVoices();
        const langPrefix = bcp.split('-')[0];
        const matchedVoice = voices.find(v => v.lang === bcp) ||
                             voices.find(v => v.lang.toLowerCase() === bcp.toLowerCase()) ||
                             voices.find(v => v.lang.toLowerCase().startsWith(langPrefix));
        if (matchedVoice) {
            utterance.voice = matchedVoice;
        }

        const btn = document.getElementById('voice-audio-ctrl-btn');
        const playIndicator = document.getElementById('voice-audio-playing-indicator');

        utterance.onstart = () => {
            isSpeaking = true;
            if (btn) btn.innerHTML = '⏹️ Stop Voice';
            if (playIndicator) playIndicator.style.display = 'flex';
        };

        utterance.onend = () => {
            isSpeaking = false;
            if (btn) btn.innerHTML = '🔊 Replay Voice';
            if (playIndicator) playIndicator.style.display = 'none';
            updateVoiceStatus('ready', "✅ Answer complete. Tap mic to ask again!");
        };

        utterance.onerror = () => {
            isSpeaking = false;
            if (btn) btn.innerHTML = '🔊 Replay Voice';
            if (playIndicator) playIndicator.style.display = 'none';
        };

        window.speechSynthesis.speak(utterance);
    }

    function stopSpeaking() {
        const audioEl = document.getElementById('voice-response-audio');
        if (audioEl) {
            audioEl.pause();
            audioEl.currentTime = 0;
        }
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
        isSpeaking = false;
        const btn = document.getElementById('voice-audio-ctrl-btn');
        if (btn) btn.innerHTML = '🔊 Replay Voice';
        const playIndicator = document.getElementById('voice-audio-playing-indicator');
        if (playIndicator) playIndicator.style.display = 'none';
    }

    function toggleAudioPlayback() {
        if (isSpeaking) {
            stopSpeaking();
        } else if (lastAudioUrl) {
            playVoiceAudio(lastAudioUrl, lastSpokenText, lastSpokenLang);
        } else if (lastSpokenText) {
            speak(lastSpokenText, lastSpokenLang);
        }
    }

    function setSpeechSpeed(speed) {
        speechRate = parseFloat(speed) || 0.95;
    }

    function updateVoiceStatus(type, msg) {
        const textEl = document.getElementById('voice-status-text');
        if (textEl) {
            textEl.textContent = msg;
            textEl.style.color = type === 'error' ? 'var(--status-danger)' : (type === 'listening' ? 'var(--primary-800)' : 'var(--text-primary)');
        }
    }

    function createVoiceModal() {
        const existingModal = document.getElementById('modal-kisan-voice');
        if (existingModal) existingModal.remove();

        const modalHtml = `
        <div id="modal-kisan-voice" class="modal-backdrop sheet-mode" style="display: none; align-items: center; justify-content: center; z-index: 10000;">
            <div class="modal-dialog" style="max-width: 560px; width: 94%; text-align: center; border-radius: 24px; padding: 22px; background: #ffffff; box-shadow: 0 20px 50px rgba(0,0,0,0.3); max-height: 90vh; overflow-y: auto;">
                <!-- Header -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 26px;">🎙️</span>
                        <h3 style="font-size: 19px; font-weight: 800; color: var(--primary-900); margin: 0;" data-i18n="voice_modal_title">Kisan Voice Agronomist</h3>
                    </div>
                    <button type="button" class="btn btn-outline btn-icon" style="width: 34px; height: 34px; border-radius: 50%;" onclick="VoiceAssistant.closeModal()">✕</button>
                </div>

                <!-- Active Tuned Language Badge -->
                <div style="font-size: 13px; font-weight: 700; color: var(--primary-800); margin-bottom: 10px;">
                    Tuned Language: <span id="voice-lang-name-badge" style="background: var(--primary-100); padding: 3px 12px; border-radius: 12px; color: var(--primary-900); font-weight: 800;">🌾 ಕನ್ನಡ (Kannada)</span>
                </div>

                <!-- Language Quick Selector Pills -->
                <div style="display: flex; gap: 6px; justify-content: center; flex-wrap: wrap; margin-bottom: 14px;">
                    <button class="btn btn-pill lang-chip" data-lang="kn" onclick="VoiceAssistant.switchVoiceLang('kn')">ಕನ್ನಡ</button>
                    <button class="btn btn-pill lang-chip" data-lang="hi" onclick="VoiceAssistant.switchVoiceLang('hi')">हिंदी</button>
                    <button class="btn btn-pill lang-chip" data-lang="te" onclick="VoiceAssistant.switchVoiceLang('te')">తెలుగు</button>
                    <button class="btn btn-pill lang-chip" data-lang="ta" onclick="VoiceAssistant.switchVoiceLang('ta')">தமிழ்</button>
                    <button class="btn btn-pill lang-chip" data-lang="mr" onclick="VoiceAssistant.switchVoiceLang('mr')">मराठी</button>
                    <button class="btn btn-pill lang-chip" data-lang="bn" onclick="VoiceAssistant.switchVoiceLang('bn')">বাংলা</button>
                    <button class="btn btn-pill lang-chip" data-lang="en" onclick="VoiceAssistant.switchVoiceLang('en')">English</button>
                </div>

                <!-- Microphone Permission / Origin Alert Box -->
                <div id="voice-permission-banner" style="display: none; background: #fff8e1; border: 1.5px solid #ffe082; border-radius: var(--radius-md); padding: 12px 14px; margin-bottom: 14px; text-align: left; font-size: 13px; color: #6d4c41;">
                    <div style="font-weight: 800; display: flex; align-items: center; gap: 6px; margin-bottom: 4px; color: #b78103;">
                        <span style="font-size: 16px;">🔒</span> <span id="voice-perm-title">Microphone Access Restricted</span>
                    </div>
                    <div id="voice-perm-desc" style="line-height: 1.5; margin-bottom: 10px; color: #5d4037;">
                        Chrome requires a secure origin (http://localhost:5000) or microphone permission.
                    </div>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                        <button type="button" class="btn btn-primary btn-pill" id="voice-switch-origin-btn" style="display: none; font-size: 11.5px; padding: 5px 12px; font-weight: 700;" onclick="window.location.href = 'http://localhost:5000' + window.location.pathname + window.location.hash;">
                            👉 Switch to localhost:5000
                        </button>
                        <button type="button" class="btn btn-outline btn-pill" style="font-size: 11.5px; padding: 5px 12px; border-color: #b78103; color: #b78103;" onclick="document.getElementById('voice-fallback-input').focus()">
                            ⌨️ Type Question Below
                        </button>
                    </div>
                </div>

                <!-- Giant Central Microphone Button with Pulse -->
                <div style="margin: 8px auto 12px; position: relative; width: 105px; height: 105px;">
                    <div class="mic-pulse-ring" id="mic-pulse-ring"></div>
                    <button type="button" class="kisan-big-mic-btn" id="kisan-big-mic-btn" onclick="VoiceAssistant.toggleListening()" title="Tap to Speak">
                        🎙️
                    </button>
                </div>

                <!-- Live Status and Instruction -->
                <div id="voice-status-text" style="font-size: 14.5px; font-weight: 700; color: var(--text-primary); margin-bottom: 12px;" data-i18n="voice_ready">
                    Tap the microphone and ask your crop question
                </div>

                <!-- Live Transcription Display (Farmer Asked) -->
                <div id="voice-transcript-bubble" style="display: none; background: #e8f5e9; border: 1.5px solid #a5d6a7; padding: 10px 14px; border-radius: 12px; font-size: 14.5px; color: #1b5e20; font-weight: 600; margin-bottom: 14px; text-align: left;">
                    <div style="font-size: 11px; text-transform: uppercase; color: #2e7d32; font-weight: 800; margin-bottom: 2px;">Farmer Asked:</div>
                    <span id="voice-transcript-text">"..."</span>
                </div>

                <!-- 🌾 PROMINENT RESPONSE CARD DIRECTLY BENEATH TRANSCRIPT -->
                <div id="voice-response-card" style="display: none; background: #f1f8e9; border: 2px solid #81c784; border-radius: 16px; padding: 18px; text-align: left; margin-bottom: 18px; box-shadow: 0 4px 15px rgba(46,125,50,0.12);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #c8e6c9; padding-bottom: 8px;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="font-size: 18px;">🌾</span>
                            <strong style="font-size: 14px; color: #1b5e20; font-weight: 800;" id="voice-response-title">AI Agronomist Spoken Advice</strong>
                        </div>
                        <div style="display: flex; gap: 6px; align-items: center;">
                            <button type="button" class="btn btn-primary btn-pill" id="voice-audio-ctrl-btn" style="font-size: 12px; padding: 4px 12px; font-weight: 700;" onclick="VoiceAssistant.toggleAudioPlayback()">
                                🔊 Replay Voice
                            </button>
                        </div>
                    </div>
                    <!-- Native HTML5 audio player for 100% reliable regional sound -->
                    <audio id="voice-response-audio" preload="auto" style="display: none;"></audio>
                    <div id="voice-response-text" style="font-size: 14.5px; color: #263238; line-height: 1.65; font-weight: 500;"></div>
                    <!-- Audio playback indicator -->
                    <div id="voice-audio-playing-indicator" style="display: none; margin-top: 10px; font-size: 12px; font-weight: 700; color: #2e7d32; align-items: center; gap: 6px;">
                        <span>🔊 Playing spoken audio...</span>
                    </div>
                </div>

                <!-- Text-input fallback right inside modal -->
                <div style="display: flex; gap: 8px; margin-bottom: 16px;">
                    <input type="text" id="voice-fallback-input" class="form-control" placeholder="Or type your question here..." style="font-size: 13.5px;" onkeydown="if(event.key==='Enter') VoiceAssistant.submitManualQuery()">
                    <button type="button" class="btn btn-primary" onclick="VoiceAssistant.submitManualQuery()" style="padding: 0 16px; font-weight: 700;">Ask</button>
                </div>

                <!-- Quick Suggestion Questions -->
                <div style="text-align: left; margin-bottom: 14px;">
                    <div style="font-size: 12px; font-weight: 700; color: var(--text-muted); margin-bottom: 6px;">💡 Suggested Questions in your Language:</div>
                    <div id="voice-suggestions-container" style="display: flex; flex-direction: column; gap: 6px;"></div>
                </div>

                <!-- Speech Speed Controls -->
                <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 12px; border-top: 1px solid var(--border-color-subtle);">
                    <div style="font-size: 12px; color: var(--text-muted);">
                        Voice Speed:
                        <select id="voice-speed-select" onchange="VoiceAssistant.setSpeechSpeed(this.value)" style="border: 1px solid var(--border-color); border-radius: 4px; padding: 2px 6px; font-size: 12px; margin-left: 4px;">
                            <option value="0.8">0.8x (Slow)</option>
                            <option value="0.95" selected>1.0x (Normal)</option>
                            <option value="1.15">1.2x (Fast)</option>
                        </select>
                    </div>
                    <button type="button" class="btn btn-secondary btn-pill" style="font-size: 12px; padding: 6px 14px;" onclick="App.navigateTo('chat'); VoiceAssistant.closeModal();">
                        💬 Open Full Chat
                    </button>
                </div>
            </div>
        </div>
        `;

        const div = document.createElement('div');
        div.innerHTML = modalHtml;
        document.body.appendChild(div.firstElementChild);
    }

    return {
        init,
        openModal,
        closeModal,
        toggleListening,
        startListening,
        startListeningForLanguage,
        switchVoiceLang,
        stopListening,
        askDirectQuestion,
        submitManualQuery,
        speak,
        stopSpeaking,
        toggleAudioPlayback,
        setSpeechSpeed,
        detectTranscriptLanguage,
        getIsListening: () => isListening
    };
})();

window.VoiceAssistant = VoiceAssistant;

// Auto-initialize voice assistant
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => VoiceAssistant.init());
} else {
    VoiceAssistant.init();
}
