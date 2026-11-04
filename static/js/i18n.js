/**
 * Plantix AI Client-Side Internationalization & Localization Engine
 * Complete translations for English, Kannada, Hindi, Telugu, Tamil, Marathi, and Bengali.
 */

const I18n = (() => {
    let currentLang = localStorage.getItem('plantix_lang') || 'en';

    const TRANSLATIONS = {
        en: {
            app_title: "AgriVision AI",
            app_subtitle: "Plantix Precision v2.0",
            nav_dashboard: "Dashboard",
            nav_diagnose: "Crop Diagnosis",
            nav_history: "Diagnosis History",
            nav_calculator: "Fertilizer Calculator",
            nav_weather: "Weather & Spray",
            nav_precision: "Precision & Satellite",
            nav_crops: "My Crops & Farms",
            nav_community: "Farmer Community",
            nav_retailers: "Marketplace",
            nav_agronomist: "AI Agronomist",
            nav_settings: "Profile & Settings",
            nav_login: "Sign In / Register",
            nav_signout: "Sign Out",
            refresh_btn: "Refresh App",
            live_gps_btn: "Live GPS Location",
            gps_lock_btn: "GPS Map Lock",
            sync_satellite_btn: "Sync Satellite Pass",
            ask_agronomist_btn: "Ask Agronomist",
            voice_assistant_btn: "Kisan Voice",
            hero_badge: "Advanced AI Diagnostic Engine & Generative Agronomist v3.0",
            hero_title: "Clinical Crop Pathology & Grounded Agronomic Consultation",
            hero_desc: "Context-aware disease diagnosis with symptom localization, calibrated confidence thresholds, and grounded RAG agronomist advice verified against ICAR and university publications.",
            snap_leaf_btn: "📸 Snap Leaf Photo",
            consult_agro_btn: "💬 Consult AI Agronomist",
            diag_history_btn: "📋 Diagnosis History",
            alerts_title: "🚨 Agricultural Alerts & Regional Advisories",
            alerts_badge: "Real-time Regional Feed",
            reg_crops_label: "REGISTERED CROPS",
            active_plots_label: "Active Field Plots",
            outbreak_label: "DISEASE OUTBREAKS",
            nearby_radar_label: "Nearby Regional Radar",
            spraying_window_label: "SPRAYING WINDOW",
            optimal: "Optimal",
            soil_status_label: "SOIL STATUS",
            adequate: "Adequate",
            recent_diagnoses_title: "Recent Leaf Diagnoses",
            seasonal_tips_title: "Seasonal Farming Tips",
            offline_guides_title: "Offline Agricultural Knowledge Guides",
            offline_guides_desc: "Cached locally in browser. Fully accessible in fields with zero mobile network.",
            diag_title: "AI Crop Disease Diagnostic Engine",
            diag_subtitle: "Instant diagnosis with multi-symptom localization, severity scoring, and CIBRC-compliant treatments",
            select_crop_label: "Select Crop Species",
            open_camera: "Open Smart Camera",
            choose_gallery: "Select from Gallery",
            start_diagnosis: "Run Diagnostic Analysis",
            ready_for_diag: "Ready for Image Quality Check",
            ready_desc: "The 5-point gatekeeper validates blur, lighting, exposure, and foliage coverage before neural inference.",
            chemical_tab: "Chemical (CIBRC)",
            biological_tab: "Biological",
            organic_tab: "Organic",
            prevention_tab: "Preventive",
            active_ingredient: "Active Ingredient",
            phi_period: "Pre-Harvest Interval (PHI)",
            frac_resistance: "FRAC Fungicide Code",
            application_directions: "Application & Dilution Dosage",
            listen_explanation: "🔊 Listen to Voice Explanation",
            stop_listening: "⏹️ Stop Audio Playback",
            voice_modal_title: "Kisan Voice Agronomist",
            voice_modal_desc: "Speak your crop health question in your regional language. Powered by ICAR & University research.",
            voice_listening: "Listening... Please speak your crop question",
            voice_processing: "Processing with AI Agronomist...",
            voice_ready: "Tap the microphone and ask your crop question",
            offline_pill: "Offline Mode Active",
            online_pill: "Connected to Cloud",
            weather_forecast_title: "🌦️ 7-Day Precision Agro Forecast",
            weather_spray_title: "Hourly Knapsack Spray Suitability",
            precision_title: "Precision Farming & Satellite Intelligence",
            precision_desc: "Field boundary polygons, 10-meter multispectral Sentinel-2 NDVI canopy health, and privacy-preserved regional outbreak surveillance.",
            boundary_layer: "Field Boundary",
            ndvi_layer: "Sentinel-2 NDVI",
            outbreaks_layer: "Disease Outbreaks",
            save_boundary_btn: "💾 Save Field Boundary",
            draw_boundary_btn: "✏️ Draw / Edit Points",
            walk_boundary_btn: "🚶 Walk Perimeter (GPS)",
            outbreak_radar_title: "⚠️ Regional Outbreak Surveillance Radar"
        },
        kn: {
            app_title: "ಅಗ್ರಿವಿಷನ್ ಎಐ",
            app_subtitle: "ಪ್ಲಾಂಟಿಕ್ಸ್ ಪ್ರೆಸಿಷನ್ ಆವೃತ್ತಿ 2.0",
            nav_dashboard: "ಮುಖಪುಟ (ಡ್ಯಾಶ್‌ಬೋರ್ಡ್)",
            nav_diagnose: "ಬೆಳೆ ರೋಗ ಪರೀಕ್ಷೆ",
            nav_history: "ಹಿಂದಿನ ಪರೀಕ್ಷಾ ಇತಿಹಾಸ",
            nav_calculator: "ರಸಗೊಬ್ಬರ ಲೆಕ್ಕಾಚಾರ",
            nav_weather: "ಹವಾಮಾನ ಮತ್ತು ಸಿಂಪರಣೆ",
            nav_precision: "ಉಪಗ್ರಹ ಮತ್ತು ಜಿಪಿಎಸ್",
            nav_crops: "ನನ್ನ ಬೆಳೆಗಳು ಮತ್ತು ಜಮೀನು",
            nav_community: "ರೈತರ ಸಮುದಾಯ",
            nav_retailers: "ಕೃಷಿ ಮಾರುಕಟ್ಟೆ",
            nav_agronomist: "ಕೃಷಿ ತಜ್ಞರ ಸಲಹೆ",
            nav_settings: "ಪ್ರೊಫೈಲ್ ಮತ್ತು ಸೆಟ್ಟಿಂಗ್ಸ್",
            nav_login: "ಲಾಗಿನ್ / ಖಾತೆ ತೆರೆಯಿರಿ",
            nav_signout: "ಲಾಗ್ ಔಟ್",
            refresh_btn: "ಮಾಹಿತಿ ನವೀಕರಿಸಿ",
            live_gps_btn: "ಪ್ರಸ್ತುತ ಜಿಪಿಎಸ್ ಸ್ಥಳ",
            gps_lock_btn: "ಜಿಪಿಎಸ್ ಮ್ಯಾಪ್ ಲಾಕ್",
            sync_satellite_btn: "ಉಪಗ್ರಹ ಚಿತ್ರ ನವೀಕರಿಸಿ",
            ask_agronomist_btn: "ಕೃಷಿ ತಜ್ಞರನ್ನು ಕೇಳಿ",
            voice_assistant_btn: "ಕಿಸಾನ್ ಧ್ವನಿ ಸಹಾಯಕ",
            hero_badge: "ಸುಧಾರಿತ ಎಐ ಬೆಳೆ ರೋಗ ಪರೀಕ್ಷೆ & ಕೃಷಿ ತಜ್ಞರ ಸಲಹೆಗಾರ",
            hero_title: "ನಿಖರ ಬೆಳೆ ರೋಗ ನಿರ್ಣಯ ಮತ್ತು ವಿಜ್ಞಾನ ಆಧಾರಿತ ಕೃಷಿ ಸಲಹೆ",
            hero_desc: "ಎಲೆಗಳ ಫೋಟೋ ಮೂಲಕ ನಿಖರ ರೋಗ ಪತ್ತೆ, ಲಕ್ಷಣಗಳ ಗುರುತಿಸುವಿಕೆ ಮತ್ತು ಭಾರತೀಯ ಕೃಷಿ ಅನುಸಂಧಾನ ಪರಿಷತ್ (ICAR) ಹಾಗೂ ಬೆಂಗಳೂರು ಕೃಷಿ ವಿಶ್ವವಿದ್ಯಾನಿಲಯ ಆಧಾರಿತ ವಿಶ್ವಾಸಾರ್ಹ ಪರಿಹಾರಗಳು.",
            snap_leaf_btn: "📸 ಎಲೆಯ ಫೋಟೋ ತೆಗೆಯಿರಿ",
            consult_agro_btn: "💬 ಕೃಷಿ ತಜ್ಞರನ್ನು ಸಂಪರ್ಕಿಸಿ",
            diag_history_btn: "📋 ಪರೀಕ್ಷಾ ಇತಿಹಾಸ ನೋಡಿ",
            alerts_title: "🚨 ಪ್ರಾದೇಶಿಕ ಕೃಷಿ ಎಚ್ಚರಿಕೆಗಳು ಮತ್ತು ಹವಾಮಾನ ಸಲಹೆಗಳು",
            alerts_badge: "ಲೈವ್ ಪ್ರಾದೇಶಿಕ ವರದಿ",
            reg_crops_label: "ನೋಂದಾಯಿತ ಬೆಳೆಗಳು",
            active_plots_label: "ಸಕ್ರಿಯ ಜಮೀನುಗಳು",
            outbreak_label: "ರೋಗದ ಹರಡುವಿಕೆ",
            nearby_radar_label: "ಹತ್ತಿರದ ರೋಗ ಎಚ್ಚರಿಕೆ",
            spraying_window_label: "ಸಿಂಪರಣೆ ಸಮಯ",
            optimal: "ಅತ್ಯುತ್ತಮ ಸಮಯ",
            soil_status_label: "ಮಣ್ಣಿನ ತೇವಾಂಶ",
            adequate: "ಸಮರ್ಪಕವಾಗಿದೆ",
            recent_diagnoses_title: "ಇತ್ತೀಚಿನ ರೋಗ ತಪಾಸಣೆಗಳು",
            seasonal_tips_title: "ಋತುಮಾನದ ಕೃಷಿ ಸಲಹೆಗಳು",
            offline_guides_title: "ನೆಟ್‌ವರ್ಕ್ ಇಲ್ಲದಿದ್ದರೂ ಲಭ್ಯವಿರುವ ಕೃಷಿ ಕೈಪಿಡಿಗಳು",
            offline_guides_desc: "ನಿಮ್ಮ ಮೊಬೈಲ್‌ನಲ್ಲಿ ಉಳಿಸಲಾಗಿದೆ. ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕವಿಲ್ಲದಿದ್ದರೂ ತೋಟದಲ್ಲಿ ಸಂಪೂರ್ಣವಾಗಿ ಲಭ್ಯವಿದೆ.",
            diag_title: "ಎಐ ಬೆಳೆ ರೋಗ ಪರೀಕ್ಷಾ ವ್ಯವಸ್ಥೆ",
            diag_subtitle: "ಎಲೆ ಫೋಟೋ ಮೂಲಕ ತಕ್ಷಣದ ರೋಗ ಪತ್ತೆ, ತೀವ್ರತೆಯ ಅಳತೆ ಮತ್ತು ಸಿಐಬಿಆರ್‌ಸಿ ಅನುಮೋದಿತ ಔಷಧೋಪಚಾರ",
            select_crop_label: "ಬೆಳೆಯ ಹೆಸರನ್ನು ಆಯ್ಕೆಮಾಡಿ",
            open_camera: "ಕ್ಯಾಮೆರಾ ತೆರೆಯಿರಿ",
            choose_gallery: "ಗ್ಯಾಲರಿಯಿಂದ ಫೋಟೋ ಆರಿಸಿ",
            start_diagnosis: "ರೋಗ ತಪಾಸಣೆ ನಡೆಸಿ",
            ready_for_diag: "ಚಿತ್ರದ ಗುಣಮಟ್ಟ ಪರಿಶೀಲನೆಗೆ ಸಿದ್ಧವಾಗಿದೆ",
            ready_desc: "ಫೋಟೋ ಮಸುಕಾಗಿದೆಯೇ, ಬೆಳಕು ಸರಿಯಾಗಿದೆಯೇ ಎಂಬುದನ್ನು ಎಐ ತಂತ್ರಜ್ಞಾನ ತಪಾಸಣೆ ಮಾಡುತ್ತದೆ.",
            chemical_tab: "ರಾಸಾಯನಿಕ ಪರಿಹಾರ (CIBRC)",
            biological_tab: "ಜೈವಿಕ ಪರಿಹಾರ",
            organic_tab: "ಸಾವಯವ ಪರಿಹಾರ",
            prevention_tab: "ಮುನ್ನೆಚ್ಚರಿಕೆ ಕ್ರಮಗಳು",
            active_ingredient: "ರಾಸಾಯನಿಕ ಸೂತ್ರ / ಘಟಕ",
            phi_period: "ಕೊಯ್ಲಿಗೆ ಮುಂಚಿನ ಅಂತರ (PHI ದಿನಗಳು)",
            frac_resistance: "ಎಫ್‌ಆರ್‌ಎಸಿ ಶಿಲೀಂಧ್ರನಾಶಕ ಕೋಡ್",
            application_directions: "ಔಷಧ ಸಿಂಪಡಿಸುವ ಪ್ರಮಾಣ ಮತ್ತು ಸೂಚನೆ",
            listen_explanation: "🔊 ಧ್ವನಿ ಮೂಲಕ ಪರಿಹಾರವನ್ನು ಆಲಿಸಿ",
            stop_listening: "⏹️ ಧ್ವನಿ ನಿಲ್ಲಿಸಿ",
            voice_modal_title: "ಕಿಸಾನ್ ಧ್ವನಿ ಸಹಾಯಕ (ಕನ್ನಡ)",
            voice_modal_desc: "ನಿಮ್ಮ ಮಾತಿನಲ್ಲಿ ಬೆಳೆ ರೋಗ ಅಥವಾ ಕೃಷಿ ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳಿ. ಐಸಿಎಆರ್ ಮತ್ತು ಕೃಷಿ ವಿವಿ ತಜ್ಞರ ಸಲಹೆ ಲಭ್ಯ.",
            voice_listening: "ಕೇಳಿಸಿಕೊಳ್ಳಲಾಗುತ್ತಿದೆ... ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪ್ರಶ್ನೆ ಮಾತನಾಡಿ",
            voice_processing: "ಉತ್ತರವನ್ನು ಸಿದ್ಧಪಡಿಸಲಾಗುತ್ತಿದೆ...",
            voice_ready: "ಮೈಕ್ರೋಫೋನ್ ಒತ್ತಿ ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ",
            offline_pill: "ಆಫ್‌ಲೈನ್ ಮೋಡ್ ಸಕ್ರಿಯವಾಗಿದೆ",
            online_pill: "ಆನ್‌ಲೈನ್ ನೆಟ್‌ವರ್ಕ್ ಲಭ್ಯವಿದೆ",
            weather_forecast_title: "🌦️ 7 ದಿನಗಳ ನಿಖರ ಕೃಷಿ ಹವಾಮಾನ ಮುನ್ಸೂಚನೆ",
            weather_spray_title: "ಗಂಟೆಗಳ ಪ್ರಕಾರ ಕೀಟನಾಶಕ ಸಿಂಪರಣೆ ಸೂಕ್ತತೆ",
            precision_title: "ನಿಖರ ಕೃಷಿ ಮತ್ತು ಸೆಂಟಿನೆಲ್-2 ಉಪಗ್ರಹ ತಂತ್ರಜ್ಞಾನ",
            precision_desc: "ಜಮೀನಿನ ಗಡಿ ನಕ್ಷೆ, 10-ಮೀಟರ್ ಎನ್‌ಡಿವಿಐ ಸಸ್ಯ ಹಸಿರುಮಯ ಆರೋಗ್ಯ ಮತ್ತು ಪ್ರಾದೇಶಿಕ ರೋಗ ಎಚ್ಚರಿಕೆಗಳು.",
            boundary_layer: "ಜಮೀನಿನ ಗಡಿ",
            ndvi_layer: "ಉಪಗ್ರಹ ಎನ್‌ಡಿವಿಐ ಹಸಿರುಮಯತೆ",
            outbreaks_layer: "ರೋಗದ ಹರಡುವಿಕೆ",
            save_boundary_btn: "💾 ಜಮೀನಿನ ಗಡಿ ನಕ್ಷೆ ಉಳಿಸಿ",
            draw_boundary_btn: "✏️ ಗಡಿ ಬಿಂದುಗಳನ್ನು ಎಳೆಯಿರಿ",
            walk_boundary_btn: "🚶 ಜಮೀನಿನ ಸುತ್ತ ನಡೆದು ಅಳೆಯಿರಿ (GPS)",
            outbreak_radar_title: "⚠️ ಪ್ರಾದೇಶಿಕ ಬೆಳೆ ರೋಗ ಹರಡುವಿಕೆ ರಾಡಾರ್"
        },
        hi: {
            app_title: "एग्रीविज़न एआई",
            app_subtitle: "प्लांटिक्स प्रिसिजन 2.0",
            nav_dashboard: "डैशबोर्ड",
            nav_diagnose: "फसल रोग निदान",
            nav_history: "निदान इतिहास",
            nav_calculator: "उर्वरक कैलकुलेटर",
            nav_weather: "मौसम और छिड़काव",
            nav_precision: "उपग्रह और जीपीएस",
            nav_crops: "मेरी फसलें और खेत",
            nav_community: "किसान समुदाय",
            nav_retailers: "कृषि बाज़ार",
            nav_agronomist: "कृषि विशेषज्ञ",
            nav_settings: "प्रोफ़ाइल और सेटिंग्स",
            nav_login: "लॉग इन / रजिस्टर करें",
            nav_signout: "लॉग आउट",
            refresh_btn: "डेटा रीफ्रेश करें",
            live_gps_btn: "लाइव जीपीएस स्थान",
            gps_lock_btn: "जीपीएस मैप लॉक",
            sync_satellite_btn: "उपग्रह डेटा सिंक करें",
            ask_agronomist_btn: "कृषि विशेषज्ञ से पूछें",
            voice_assistant_btn: "किसान आवाज़",
            hero_badge: "उन्नत एआई फसल निदान एवं विशेषज्ञ परामर्श प्रणाली",
            hero_title: "सटीक फसल रोग निदान और प्रामाणिक कृषि सलाह",
            hero_desc: "पत्ती की तस्वीर से त्वरित रोग पहचान, लक्षण विश्लेषण तथा भारतीय कृषि अनुसंधान परिषद (ICAR) द्वारा सत्यापित उपचार।",
            snap_leaf_btn: "📸 पत्ती की फोटो लें",
            consult_agro_btn: "💬 कृषि विशेषज्ञ से पूछें",
            diag_history_btn: "📋 पिछला इतिहास देखें",
            alerts_title: "🚨 कृषि चेतावनी और मौसमी सलाह",
            alerts_badge: "लाइव क्षेत्रीय फ़ीड",
            reg_crops_label: "पंजीकृत फसलें",
            active_plots_label: "सक्रिय खेत",
            outbreak_label: "रोग प्रकोप",
            nearby_radar_label: "नज़दीकी रोग रडार",
            spraying_window_label: "छिड़काव का समय",
            optimal: "उत्कृष्ट समय",
            soil_status_label: "मिट्टी की नमी",
            adequate: "पर्याप्त",
            recent_diagnoses_title: "हाल के फसल निदान",
            seasonal_tips_title: "मौसमी कृषि सुझाव",
            offline_guides_title: "ऑफ़लाइन कृषि मार्गदर्शिकाएँ",
            offline_guides_desc: "बिना इंटरनेट के भी खेत में पूरी तरह से उपलब्ध।",
            diag_title: "एआई फसल रोग निदान इंजन",
            diag_subtitle: "तत्काल रोग पहचान, गंभीरता स्कोर और सीआईबीआरसी अनुमोदित उपचार",
            select_crop_label: "फसल का प्रकार चुनें",
            open_camera: "कैमरा खोलें",
            choose_gallery: "गैलरी से फोटो चुनें",
            start_diagnosis: "रोग जांच शुरू करें",
            ready_for_diag: "छवि गुणवत्ता जांच के लिए तैयार",
            ready_desc: "धुंधलापन, प्रकाश और पत्ती कवरेज की एआई जांच की जाती है।",
            chemical_tab: "रासायनिक उपचार (CIBRC)",
            biological_tab: "जैविक उपचार",
            organic_tab: "प्राकृतिक/ऑर्गेनिक",
            prevention_tab: "रोकथाम के उपाय",
            active_ingredient: "सक्रिय घटक",
            phi_period: "तुड़ाई पूर्व अंतराल (PHI दिन)",
            frac_resistance: "कवकनाशी कोड (FRAC)",
            application_directions: "छिड़काव की मात्रा और निर्देश",
            listen_explanation: "🔊 आवाज़ में उपाय सुनें",
            stop_listening: "⏹️ आवाज़ बंद करें",
            voice_modal_title: "किसान आवाज़ सहायक (हिंदी)",
            voice_modal_desc: "अपनी भाषा में बोलकर फसल के रोग या खेती का कोई भी सवाल पूछें।",
            voice_listening: "सुन रहे हैं... कृपया अपना सवाल बोलें",
            voice_processing: "जवाब तैयार किया जा रहा है...",
            voice_ready: "माइक बटन दबाएं और अपना सवाल पूछें",
            offline_pill: "ऑफ़लाइन मोड सक्रिय",
            online_pill: "इंटरनेट से जुड़ा हुआ",
            weather_forecast_title: "🌦️ 7 दिवसीय सटीक कृषि मौसम पूर्वानुमान",
            weather_spray_title: "घंटे-वार छिड़काव उपयुक्तता",
            precision_title: "सटीक खेती और सेंटिनल-2 उपग्रह बुद्धिमत्ता",
            precision_desc: "खेत की सीमा, 10-मीटर एनडीवीआई हरियाली स्वास्थ्य और क्षेत्रीय रोग प्रकोप निगरानी।",
            boundary_layer: "खेत की सीमा",
            ndvi_layer: "उपग्रह एनडीवीआई हरियाली",
            outbreaks_layer: "रोग का प्रकोप",
            save_boundary_btn: "💾 खेत की सीमा सुरक्षित करें",
            draw_boundary_btn: "✏️ सीमा बिंदु बनाएं",
            walk_boundary_btn: "🚶 खेत में चलकर नापें (GPS)",
            outbreak_radar_title: "⚠️ क्षेत्रीय फसल रोग प्रकोप रडार"
        },
        te: {
            app_title: "అగ్రివిజన్ AI",
            app_subtitle: "ప్లాంటిక్స్ ప్రెసిషన్ 2.0",
            nav_dashboard: "డాష్‌బోర్డ్",
            nav_diagnose: "పంట తెగుళ్ల గుర్తింపు",
            nav_history: "నిర్ధారణ చరిత్ర",
            nav_calculator: "ఎరువుల కాలిక్యులేటర్",
            nav_weather: "వాతావరణం & పిచికారీ",
            nav_precision: "ఉపగ్రహ & జీపీఎస్",
            nav_crops: "నా పంటలు & పొలాలు",
            nav_community: "రైతు సమూహం",
            nav_retailers: "రైతు మార్కెట్",
            nav_agronomist: "వ్యవసాయ నిపుణుడు",
            nav_settings: "ప్రొఫైల్ & సెట్టింగ్‌లు",
            nav_login: "లాగిన్ / రిజిస్టర్",
            nav_signout: "లాగ్ అవుట్",
            refresh_btn: "డేటా రీఫ్రెష్",
            live_gps_btn: "లైవ్ జీపీఎస్ లొకేషన్",
            gps_lock_btn: "జీపీఎస్ మ్యాప్ లాక్",
            sync_satellite_btn: "ఉపగ్రహ సమాచారం సింక్ చేయండి",
            ask_agronomist_btn: "వ్యవసాయ నిపుణుడిని అడగండి",
            voice_assistant_btn: "కిసాన్ వాయిస్",
            hero_title: "ఖచ్చితమైన పంట తెగుళ్ల నిర్ధారణ & వ్యవసాయ సలహాలు",
            snap_leaf_btn: "📸 ఆకు ఫోటో తీయండి",
            consult_agro_btn: "💬 నిపుణుడిని సంప్రదించండి",
            alerts_title: "🚨 ప్రాంతీయ వ్యవసాయ హెచ్చరికలు",
            spraying_window_label: "పిచికారీ సమయం",
            optimal: "అనుకూలమైనది",
            weather_forecast_title: "🌦️ 7 రోజుల ఖచ్చితమైన వాతావరణ అంచనా",
            precision_title: "ఖచ్చితమైన వ్యవసాయం & శాటిలైట్ సమాచారం"
        },
        ta: {
            app_title: "அக்ரிவிஷன் AI",
            app_subtitle: "பிளான்டிக்ஸ் துல்லியம் 2.0",
            nav_dashboard: "முகப்பு",
            nav_diagnose: "பயிர் நோய் கண்டறிதல்",
            nav_history: "முந்தைய வரலாறு",
            nav_calculator: "உரக் கணக்கீடு",
            nav_weather: "வானிலை & தெளிப்பு",
            nav_precision: "செயற்கைக்கோள் & ஜிபிஎஸ்",
            nav_crops: "எனது பயிர்கள் & பண்ணை",
            nav_community: "விவசாயிகள் சமூகம்",
            nav_retailers: "வேளாண் சந்தை",
            nav_agronomist: "வேளாண் நிபுணர்",
            nav_settings: "சுயவிவரம் & அமைப்புகள்",
            nav_login: "உள்நுழைக / பதிவு செய்க",
            nav_signout: "வெளியேறுக",
            refresh_btn: "புதுப்பிக்கவும்",
            live_gps_btn: "நேரலை ஜிபிஎஸ்",
            gps_lock_btn: "ஜிபிஎஸ் பூட்டு",
            sync_satellite_btn: "செயற்கைக்கோள் புதுப்பிப்பு",
            ask_agronomist_btn: "நிபுணரிடம் கேளுங்கள்",
            voice_assistant_btn: "கிசான் குரல்",
            hero_title: "துல்லியமான பயிர் நோய் கண்டறிதல் மற்றும் பரிந்துரைகள்",
            snap_leaf_btn: "📸 இலை புகைப்படம் எடுங்கள்",
            consult_agro_btn: "💬 நிபுணரிடம் பேசுங்கள்",
            alerts_title: "🚨 பிராந்திய விவசாய எச்சரிக்கைகள்",
            spraying_window_label: "தெளிப்பு நேரம்",
            optimal: "மிகச் சிறந்தது",
            weather_forecast_title: "🌦️ 7 நாட்கள் துல்லிய வானிலை முன்னறிவிப்பு",
            precision_title: "துல்லிய வேளாண்மை மற்றும் செயற்கைக்கோள் தகவல்"
        },
        mr: {
            app_title: "अॅग्रीव्हिजन AI",
            app_subtitle: "प्लँटिक्स प्रिसिजन 2.0",
            nav_dashboard: "डॅशबोर्ड",
            nav_diagnose: "पीक रोग निदान",
            nav_history: "निदान इतिहास",
            nav_calculator: "खत कॅल्क्युलेटर",
            nav_weather: "हवामान आणि फवारणी",
            nav_precision: "उपग्रह आणि जीपीएस",
            nav_crops: "माझी पिके आणि शेत",
            nav_community: "शेतकरी समुदाय",
            nav_retailers: "कृषी बाजार",
            nav_agronomist: "कृषी तज्ञ",
            nav_settings: "प्रोफाइल आणि सेटिंग्ज",
            nav_login: "लॉगिन / नोंदणी करा",
            nav_signout: "लॉग आउट",
            refresh_btn: "माहिती ताजी करा",
            live_gps_btn: "लाइव्ह जीपीएस स्थान",
            gps_lock_btn: "जीपीएस मॅप लॉक",
            sync_satellite_btn: "उपग्रह डेटा सिंक करा",
            ask_agronomist_btn: "कृषी तज्ञांना विचारा",
            voice_assistant_btn: "किसान व्हॉइस",
            hero_title: "अचूक पीक रोग निदान आणि कृषी सल्ला",
            snap_leaf_btn: "📸 पानाचा फोटो काढा",
            consult_agro_btn: "💬 तज्ञांशी बोला",
            alerts_title: "🚨 प्रादेशिक कृषी इशारे आणि सल्ला",
            spraying_window_label: "फवारणी वेळ",
            optimal: "उत्तम वेळ",
            weather_forecast_title: "🌦️ 7 दिवसांचा अचूक हवामान अंदाज",
            precision_title: "अचूक शेती आणि उपग्रह तंत्रज्ञान"
        },
        bn: {
            app_title: "এগ্রিভিশন AI",
            app_subtitle: "প্ল্যান্টিক্স প্রিসিশন ২.০",
            nav_dashboard: "ড্যাশবোর্ড",
            nav_diagnose: "ফসল রোগ নির্ণয়",
            nav_history: "পূর্ববর্তী ইতিহাস",
            nav_calculator: "সার ক্যালকুলেটর",
            nav_weather: "আবহাওয়া ও স্প্রে",
            nav_precision: "স্যাটেলাইট ও জিপিএস",
            nav_crops: "আমার ফসল ও খামার",
            nav_community: "কৃষক সমাজ",
            nav_retailers: "কৃষি বাজার",
            nav_agronomist: "কৃষি বিশেষজ্ঞ",
            nav_settings: "প্রোফাইল ও সেটিংস",
            nav_login: "লগইন / নিবন্ধন",
            nav_signout: "লগ আউট",
            refresh_btn: "রিফ্রেশ করুন",
            live_gps_btn: "লাইভ জিপিএস লোকেশন",
            gps_lock_btn: "জিপিএস ম্যাপ লক",
            sync_satellite_btn: "স্যাটেলাইট তথ্য সিঙ্ক করুন",
            ask_agronomist_btn: "বিশেষজ্ঞকে জিজ্ঞাসা করুন",
            voice_assistant_btn: "কিসান ভয়েস",
            hero_title: "সঠিক ফসল রোগ নির্ণয় এবং বৈজ্ঞানিক পরামর্শ",
            snap_leaf_btn: "📸 পাতার ছবি তুলুন",
            consult_agro_btn: "💬 বিশেষজ্ঞের সাথে কথা বলুন",
            alerts_title: "🚨 আঞ্চলিক কৃষি সতর্কতা",
            spraying_window_label: "স্প্রে করার উপযুক্ত সময়",
            optimal: "অনুকূল",
            weather_forecast_title: "🌦️ ৭ দিনের নির্ভুল কৃষি আবহাওয়ার পূর্বাভাস",
            precision_title: "নির্ভুল কৃষি ও উপগ্রহ পর্যবেক্ষণ"
        }
    };

    function translateText(key) {
        const langDict = TRANSLATIONS[currentLang] || TRANSLATIONS['en'];
        return langDict[key] || TRANSLATIONS['en'][key] || key;
    }

    function applyLanguage(lang) {
        if (!TRANSLATIONS[lang]) lang = 'en';
        currentLang = lang;
        localStorage.setItem('plantix_lang', lang);
        document.documentElement.lang = lang;

        // 1. Translate all text nodes with data-i18n
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const translation = translateText(key);
            if (el.getAttribute('data-i18n-attr') === 'placeholder') {
                el.placeholder = translation;
            } else if (el.getAttribute('data-i18n-attr') === 'title') {
                el.title = translation;
            } else {
                el.textContent = translation;
            }
        });

        // 2. Update language dropdowns
        const headerLangSelect = document.getElementById('header-lang-picker');
        const profLangSelect = document.getElementById('prof-lang-select');
        if (headerLangSelect) headerLangSelect.value = lang;
        if (profLangSelect) profLangSelect.value = lang;

        // 3. Update voice assistant active pill
        if (window.VoiceAssistant && typeof window.VoiceAssistant.switchVoiceLang === 'function') {
            document.querySelectorAll('.lang-chip').forEach(btn => {
                if (btn.dataset.lang === lang) {
                    btn.classList.add('btn-primary');
                    btn.classList.remove('btn-outline');
                } else {
                    btn.classList.remove('btn-primary');
                    btn.classList.add('btn-outline');
                }
            });
        }

        // 4. Dispatch global custom event for other controllers
        window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
        console.log(`[I18n] Language applied successfully: ${lang}`);
    }

    function init() {
        applyLanguage(currentLang);
    }

    return {
        init,
        t: translateText,
        setLanguage: applyLanguage,
        getLanguage: () => currentLang,
        languages: TRANSLATIONS
    };
})();

// Auto-initialize when DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => I18n.init());
} else {
    I18n.init();
}
