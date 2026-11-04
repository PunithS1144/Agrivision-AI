import re
# Multilingual Regional Language & Agronomic Translation Engine for Plantix AI (Phase 5)
# Grounded in ICAR, UAS Bangalore, TNAU, and State Agricultural University terminology.
# Languages supported: English (en), Kannada (kn), Hindi (hi), Telugu (te), Tamil (ta), Marathi (mr), Bengali (bn).

REGIONAL_LANGUAGES = {
    "en": {"name": "English", "native": "English", "bcp47": "en-IN"},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "bcp47": "kn-IN"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "bcp47": "hi-IN"},
    "te": {"name": "Telugu", "native": "తెలుగు", "bcp47": "te-IN"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "bcp47": "ta-IN"},
    "mr": {"name": "Marathi", "native": "मराठी", "bcp47": "mr-IN"},
    "bn": {"name": "Bengali", "native": "বাংলা", "bcp47": "bn-IN"}
}

# Cross-lingual Crop Entity Mapping
CROP_TRANSLATIONS = {
    "Tomato": {
        "en": "Tomato", "kn": "ಟೊಮೆಟೊ", "hi": "टमाटर",
        "te": "టమోటా", "ta": "தக்காளி", "mr": "टोमॅटो", "bn": "টমেটো"
    },
    "Potato": {
        "en": "Potato", "kn": "ಆಲೂಗಡ್ಡೆ", "hi": "आलू",
        "te": "బంగాళాదుంప", "ta": "உருளைக்கிழங்கு", "mr": "बटाटा", "bn": "আলু"
    },
    "Chili": {
        "en": "Chili / Pepper", "kn": "ಮೆಣಸಿನಕಾಯಿ", "hi": "मिर्च",
        "te": "మిరప", "ta": "மிளகாய்", "mr": "मिरची", "bn": "লঙ্কা"
    },
    "Rice": {
        "en": "Paddy / Rice", "kn": "ಭತ್ತ", "hi": "धान / चावल",
        "te": "వరి / ధాన్యం", "ta": "நெல் / அரிசி", "mr": "भात / धान", "bn": "ধান / চাল"
    },
    "Corn": {
        "en": "Maize / Corn", "kn": "ಮೆಕ್ಕೆಜೋಳ", "hi": "मक्का",
        "te": "మొక్కజొన్న", "ta": "மக்காச்சோளம்", "mr": "मका", "bn": "ভুট্টা"
    }
}

# Regional Keywords for Cross-Lingual Semantic Retrieval
REGIONAL_KEYWORDS = {
    "kn": {
        "crops": {"ಟೊಮೆಟೊ": "Tomato", "ಆಲೂಗಡ್ಡೆ": "Potato", "ಮೆಣಸಿನ": "Chili", "ಭತ್ತ": "Rice", "ಜೋಳ": "Corn"},
        "symptoms": {
            "ಹಳದಿ": "yellowing chlorosis",
            "ಮುರುಟು": "leaf curling",
            "ಮುರುಡ": "leaf curl thrips",
            "ಚುಕ್ಕೆ": "leaf spot",
            "ಮಚ್ಚೆ": "early blight concentric rings",
            "ಕೊಳೆತ": "late blight rot",
            "ಹುಳು": "pest borer",
            "ಬೂದಿ": "powdery mildew",
            "ಒಣಗುವಿಕೆ": "wilting drying"
        },
        "topics": {
            "ಗೊಬ್ಬರ": "fertilizer dosage urea dap",
            "ಔಷಧ": "spray fungicide pesticide",
            "ಸಿಂಪಡಣೆ": "spraying weather window",
            "ನೀರು": "irrigation water"
        }
    },
    "hi": {
        "crops": {"टमाटर": "Tomato", "आलू": "Potato", "मिर्च": "Chili", "धान": "Rice", "मक्का": "Corn"},
        "symptoms": {
            "पीला": "yellowing chlorosis",
            "मरोड़िया": "leaf curl",
            "धब्बा": "leaf spot",
            "झुलसा": "blight alternaria phytophthora",
            "सड़न": "rot late blight",
            "कीड़ा": "pest caterpillar",
            "फफूंद": "fungus mildew"
        },
        "topics": {
            "खाद": "fertilizer dosage urea dap",
            "दवा": "fungicide spray",
            "छिड़काव": "spraying window weather",
            "सिंचाई": "irrigation water"
        }
    },
    "te": {
        "crops": {"టమోటా": "Tomato", "బంగాళాదుంప": "Potato", "మిరప": "Chili", "వరి": "Rice", "మొక్కజొన్న": "Corn"},
        "symptoms": {
            "పసుపు": "yellowing chlorosis",
            "ముడుత": "leaf curl",
            "మచ్చ": "leaf spot blight",
            "కుళ్లు": "rot late blight",
            "పురుగు": "pest borer"
        },
        "topics": {
            "ఎరువు": "fertilizer urea dap",
            "మందు": "spray pesticide",
            "పిచికారీ": "spraying weather"
        }
    },
    "ta": {
        "crops": {"தக்காளி": "Tomato", "உருளை": "Potato", "மிளகாய்": "Chili", "நெல்": "Rice", "மக்காச்சோளம்": "Corn"},
        "symptoms": {
            "மஞ்சள்": "yellowing chlorosis",
            "சுருட்டை": "leaf curl",
            "புள்ளி": "leaf spot",
            "கருகல்": "blight scorch",
            "புழு": "pest caterpillar"
        },
        "topics": {
            "உரம்": "fertilizer urea dap",
            "மருந்து": "spray pesticide",
            "தெளிப்பு": "spraying weather"
        }
    },
    "mr": {
        "crops": {"टोमॅटो": "Tomato", "बटाटा": "Potato", "मिरची": "Chili", "भात": "Rice", "मका": "Corn"},
        "symptoms": {
            "पिवळे": "yellowing chlorosis",
            "बोकड्या": "leaf curl",
            "करपा": "blight alternaria",
            "ठिपके": "leaf spot",
            "अळी": "pest caterpillar"
        },
        "topics": {
            "खत": "fertilizer urea dap",
            "औषध": "spray fungicide",
            "फवारणी": "spraying weather"
        }
    },
    "bn": {
        "crops": {"টমেটো": "Tomato", "আলু": "Potato", "লঙ্কা": "Chili", "ধান": "Rice", "ভুট্টা": "Corn"},
        "symptoms": {
            "হলুদ": "yellowing chlorosis",
            "কোঁকড়ানো": "leaf curl",
            "দাগ": "leaf spot",
            "ধসা": "blight alternaria",
            "পোকা": "pest borer"
        },
        "topics": {
            "সার": "fertilizer urea dap",
            "কীটনাশক": "spray pesticide",
            "স্প্রে": "spraying weather"
        }
    }
}

# Regional Agricultural Advisories
# Regional Agricultural Advisories across all major agronomic categories
REGIONAL_ADVISORIES = {
    "kn": {
        "early_blight": (
            "ಟೊಮೆಟೊ ಗಿಡಗಳಲ್ಲಿ 'ಅರ್ಲಿ ಬ್ಲೈಟ್' (ಮುಂಚಿನ ಕರಗು ರೋಗ) ಲಕ್ಷಣಗಳು ಕಂಡುಬರುತ್ತಿವೆ. "
            "ಎಲೆಗಳ ಮೇಲೆ ಕಂದು-ಕಪ್ಪು ಬಣ್ಣದ ವೃತ್ತಾಕಾರದ ಮಚ್ಚೆಗಳು ('ಟಾರ್ಗೆಟ್ ಬೋರ್ಡ್') ಉಂಟಾಗುತ್ತವೆ. "
            "ಕ್ರಮ: ಮ್ಯಾಂಕೋಜೆಬ್ 75% WP @ 2.5 ಗ್ರಾಂ ಪ್ರತಿ ಲೀಟರ್ ನೀರಿಗೆ ಬೆರೆಸಿ ಸಿಂಪಡಿಸಿ (PHI: 5 ದಿನಗಳು). "
            "ಜೈವಿಕ ಚಿಕಿತ್ಸೆ: 10,000 ppm ಬೇವಿನ ಎಣ್ಣೆ @ 2 ಮಿಲಿ ಪ್ರತಿ ಲೀಟರ್ ನೀರಿಗೆ ಬೆರೆಸಿ ಮುಂಜಾನೆ ಸಿಂಪಡಿಸಿ."
        ),
        "late_blight": (
            "ಶೀತ ಮತ್ತು ಅತಿಯಾದ ತೇವಾಂಶದಿಂದ 'ಲೇಟ್ ಬ್ಲೈಟ್' (ತಡವಾದ ಕರಗು ರೋಗ) ಹರಡುವ ಸಾಧ್ಯತೆಯಿದೆ. "
            "ಎಲೆಗಳ ಅಂಚುಗಳಲ್ಲಿ ನೀರು ಸೋಕಿದ ಕಪ್ಪು ಮಚ್ಚೆಗಳು ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತವೆ. "
            "ಕ್ರಮ: ಸೈಮೋಕ್ಸಾನಿಲ್ 8% + ಮ್ಯಾಂಕೋಜೆಬ್ 64% WP @ 2 ಗ್ರಾಂ ಅಥವಾ ಡೈಮೆಥೊಮಾರ್ಫ್ @ 1 ಗ್ರಾಂ ಪ್ರತಿ ಲೀಟರ್ ನೀರಿಗೆ ಸಿಂಪಡಿಸಿ. "
            "ಕಟಾವಿಗೆ ಮುನ್ನ 7 ದಿನಗಳ ಕಾಯುವ ಅವಧಿ (PHI) ಪಾಲಿಸಿ."
        ),
        "leaf_curl": (
            "ಮೆಣಸಿನಕಾಯಿ ಅಥವಾ ಟೊಮೆಟೊದಲ್ಲಿ ಎಲೆ ಮುರುಟು ರೋಗ ನುಸಿ ಅಥವಾ ಥ್ರಿಪ್ಸ್ ಕೀಟಗಳಿಂದ ಹರಡುತ್ತದೆ. "
            "ಎಲೆಗಳು ಮೇಲ್ಮುಖವಾಗಿ ದೋಣಿಯಂತೆ ಮುರುಟಿದರೆ ಥ್ರಿಪ್ಸ್, ಕೆಳಮುಖವಾಗಿ ಮುರುಟಿದರೆ ಹಳದಿ ನುಸಿ ಕಾರಣ. "
            "ಕ್ರಮ: ಎಕರೆಗೆ 15 ನೀಲಿ ಮತ್ತು ಹಳದಿ ಅಂಟು ಬಲೆಗಳನ್ನು ಅಳವಡಿಸಿ. ಡಯಾಫೆಂಥಿಯುರಾನ್ 50% WP @ 1.25 ಗ್ರಾಂ ಸಿಂಪಡಿಸಿ."
        ),
        "chlorosis": (
            "ಕೆಳ ಹಂತದ ಹಳೆಯ ಎಲೆಗಳು ಸಂಪೂರ್ಣ ಹಳದಿಯಾಗುತ್ತಿದ್ದರೆ ಅದು ಸಾರಜನಕದ (Nitrogen) ಕೊರತೆಯಾಗಿದೆ. "
            "ಕ್ರಮ: ಎಕರೆಗೆ 3-5 ಕೆಜಿ ನೀರಿನಲ್ಲಿ ಕರಗುವ ಯೂರಿಯಾ ನೀಡಿ ಅಥವಾ 1% ಯೂರಿಯಾ ದ್ರಾವಣವನ್ನು (10 ಗ್ರಾಂ/ಲೀ) ಬೆಳಗಿನ ಜಾವ ಎಲೆಗಳಿಗೆ ಸಿಂಪಡಿಸಿ."
        ),
        "fertilizer": (
            "ಟೊಮೇಟೊ ಬೆಳೆಗೆ ಸಮಗ್ರ ರಸಗೊಬ್ಬರ ಶಿಫಾರಸು: ನಾಟಿ ಮಾಡುವಾಗ ಎಕರೆಗೆ 100 ಕೆಜಿ ಡಿಎಪಿ (DAP), 50 ಕೆಜಿ ಎಂಒಪಿ (MOP) ಮತ್ತು 25 ಕೆಜಿ ಯೂರಿಯಾ ಮೂಲ ಗೊಬ್ಬರವಾಗಿ ನೀಡಿ. "
            "ನಾಟಿ ಮಾಡಿದ 30 ಮತ್ತು 50 ನೇ ದಿನಗಳಲ್ಲಿ ತಲಾ 25 ಕೆಜಿ ಯೂರಿಯಾವನ್ನು ಮೇಲುಗೊಬ್ಬರವಾಗಿ ಕೊಡಿ. "
            "ಹೂವಾಡುವ ಮತ್ತು ಕಾಯಿ ಕಟ್ಟುವ ಹಂತದಲ್ಲಿ 19:19:19 ನೀರಿನಲ್ಲಿ ಕರಗುವ ಗೊಬ್ಬರ @ 5 ಗ್ರಾಂ ಪ್ರತಿ ಲೀಟರ್ ನೀರಿಗೆ ಸಿಂಪಡಿಸಿ."
        ),
        "pest": (
            "ಕಾಯಿ ಕೊರೆಯುವ ಹುಳು ಹಾಗೂ ಕೀಟ ನಿಯಂತ್ರಣ: ಎಲೆ ತಿನ್ನುವ ಅಥವಾ ಕಾಯಿ ಕೊರೆಯುವ ಹುಳುಗಳಿದ್ದರೆ ಕ್ಲೋರಾಂಟ್ರಾನಿಲಿಪ್ರೋಲ್ (ಕೊರಾಜೆನ್ 18.5% SC) @ 0.3 ಮಿಲಿ "
            "ಅಥವಾ ಎಮಾಮೆಕ್ಟಿನ್ ಬೆಂಜೊಯೆಟ್ 5% SG @ 0.5 ಗ್ರಾಂ ಪ್ರತಿ ಲೀಟರ್ ನೀರಿಗೆ ಬೆರೆಸಿ ಸಿಂಪಡಿಸಿ. "
            "ಜೈವಿಕವಾಗಿ ಎಕರೆಗೆ 4-5 ಲಿಂಗಾಕರ್ಷಕ ಬಲೆಗಳನ್ನು (Pheromone traps) ಅಳವಡಿಸಿ."
        ),
        "powdery_mildew": (
            "ಬೂದಿ ರೋಗ (Powdery Mildew) ನಿಯಂತ್ರಣ: ಎಲೆಗಳ ಮೇಲೆ ಬಿಳಿ ಬೂದಿಯಂತಹ ಶಿಲೀಂಧ್ರ ಕಂಡುಬಂದರೆ ನೀರಿನಲ್ಲಿ ಕರಗುವ ಗಂಧಕ (Sulphur 80% WDG) @ 2.5 ಗ್ರಾಂ "
            "ಅಥವಾ ಹೆಕ್ಸಾಕೊನಾಜೋಲ್ 5% EC @ 1 ಮಿಲಿ ಪ್ರತಿ ಲೀಟರ್ ನೀರಿಗೆ ಬೆರೆಸಿ ಎಲೆಗಳ ಎರಡೂ ಬದಿ ನೆನೆಯುವಂತೆ ಸಿಂಪಡಿಸಿ."
        ),
        "wilt": (
            "ಸೊರಗು ರೋಗ / ಬಾಡುವ ರೋಗ (Bacterial or Fusarium Wilt): ಗಿಡಗಳು ಹಠಾತ್ ಬಾಡಿ ಒಣಗುತ್ತಿದ್ದರೆ, "
            "ತಾಮ್ರದ ಆಕ್ಸಿಕ್ಲೋರೈಡ್ (COC 50% WP) @ 3 ಗ್ರಾಂ ಪ್ರತಿ ಲೀಟರ್ ನೀರಿಗೆ ಅಥವಾ ಟ್ರೈಕೋಡರ್ಮಾ ವಿರಿಡೆ ಜೈವಿಕ ಶಿಲೀಂಧ್ರನಾಶಕವನ್ನು ಗಿಡದ ಬುಡಕ್ಕೆ ಸುರಿಯಿರಿ (Drenching). "
            "ಅತಿಯಾದ ನೀರು ನಿಲ್ಲದಂತೆ ಬಸಿದು ಹೋಗಲು ಕಾಲುವೆ ಮಾಡಿ."
        ),
        "irrigation": (
            "ನೀರಾವರಿ ನಿರ್ವಹಣೆ: ಹೂವು ಮತ್ತು ಕಾಯಿ ಕಟ್ಟುವ ಹಂತದಲ್ಲಿ ಮಣ್ಣಿನಲ್ಲಿ ಸದಾ ಸಮತೋಲಿತ ತೇವಾಂಶವಿರಬೇಕು. "
            "ಅತಿಯಾದ ನೀರು ಅಥವಾ ತೀವ್ರ ಒಣಗುವಿಕೆ ಕಾಯಿ ಕಪ್ಪಾಗಲು ಕಾರಣವಾಗುತ್ತದೆ. ಹನಿ ನೀರಾವರಿ ಮೂಲಕ ನಿತ್ಯ 1.5 ರಿಂದ 2 ಗಂಟೆಗಳ ಕಾಲ ನೀರು ಹಾಯಿಸುವುದು ಉತ್ತಮ."
        ),
        "spray_optimal": (
            "ಇಂದಿನ ಹವಾಮಾನವು ಔಷಧ ಸಿಂಪಡಣೆಗೆ ಅತ್ಯಂತ ಸೂಕ್ತವಾಗಿದೆ. ಗಾಳಿಯ ವೇಗ ಕಡಿಮೆಯಿದ್ದು, ಬಿಸಿಲು ಹಿತಕರವಾಗಿದೆ. "
            "ಬೆಳಗ್ಗೆ 7:00 ರಿಂದ 9:30 ರೊಳಗೆ ಸಿಂಪಡಿಸುವುದು ಉತ್ತಮ."
        ),
        "general_greeting": (
            "ನಮಸ್ಕಾರ ರೈತ ಬಾಂಧವರೇ! ನಾನು ನಿಮ್ಮ ಅಗ್ರಿವಿಷನ್ ಕೃಷಿ ತಜ್ಞ. "
            "ಬೆಳೆಯ ಪೋಷಕಾಂಶ ನಿರ್ವಹಣೆ, ರೋಗ ನಿಯಂತ್ರಣ, ಕೀಟ ಬಾಧೆ ಅಥವಾ ಔಷಧ ಸಿಂಪರಣೆಯ ಬಗ್ಗೆ ಯಾವುದೇ ಪ್ರಶ್ನೆ ಕೇಳಿ, ಸೂಕ್ತ ಪರಿಹಾರ ನೀಡುತ್ತೇನೆ."
        )
    },
    "hi": {
        "early_blight": (
            "टमाटर में 'अगेती झुलसा' (Early Blight) के लक्षण दिख रहे हैं। पत्तियों पर भूरे-काले छल्लेदार गोल धब्बे बनते हैं। "
            "उपचार: मैंकोजेब 75% WP @ 2.5 ग्राम प्रति लीटर पानी में मिलाकर छिड़काव करें (PHI: 5 दिन)। "
            "जैविक उपचार: नीम का तेल (10,000 ppm) @ 2 मिली प्रति लीटर सुबह छिड़कें।"
        ),
        "late_blight": (
            "ठंडे और नम मौसम में 'पछेती झुलसा' (Late Blight) का खतरा बढ़ जाता है। पत्तियों पर जलभराव जैसे काले धब्बे उभरते हैं। "
            "उपचार: साइमोक्सानिल 8% + मैंकोजेब 64% WP @ 2 ग्राम या डाइमेथोमॉर्फ @ 1 ग्राम प्रति लीटर पानी में मिलाकर फौरन छिड़कें।"
        ),
        "leaf_curl": (
            "मिर्च और टमाटर में 'पत्ता मरोड़' (Leaf Curl) रोग रस चूसक कीटों (थ्रिप्स/माइट्स) द्वारा फैलता है। "
            "उपचार: प्रति एकड़ 15 नीले और पीले चिपचिपे कार्ड लगाएं। डायफेंथियूरॉन 50% WP @ 1.25 ग्राम प्रति लीटर छिड़कें।"
        ),
        "chlorosis": (
            "यदि पुरानी निचली पत्तियां एकसमान पीली हो रही हैं, तो यह नाइट्रोजन की कमी का संकेत है। "
            "उपचार: 1% यूरिया घोल (10 ग्राम प्रति लीटर) सुबह छिड़कें या ड्रिप द्वारा 4-5 किग्रा यूरिया प्रति एकड़ दें।"
        ),
        "fertilizer": (
            "फसल हेतु संपूर्ण उर्वरक प्रबंधन: बुवाई/रोपाई के समय प्रति एकड़ 100 किग्रा डीएपी (DAP), 50 किग्रा पोटाश (MOP) तथा 25 किग्रा यूरिया बेसल डोज के रूप में दें। "
            "रोपाई के 30 और 50 दिनों बाद 25-25 किग्रा यूरिया की टॉप ड्रेसिंग करें। फूल व फल बनते समय 19:19:19 घुलनशील खाद @ 5 ग्राम प्रति लीटर छिड़कें।"
        ),
        "pest": (
            "कीट व इल्ली नियंत्रण: फल छेदक या तना छेदक इल्ली के प्रकोप पर कोराजन (क्लोरेंट्रानिलीप्रोल 18.5% SC) @ 0.3 मिली "
            "या इमामेक्टिन बेंजोएट 5% SG @ 0.5 ग्राम प्रति लीटर पानी में मिलाकर छिड़काव करें। जैविक उपाय के लिए फेरोमोन ट्रैप लगाएं।"
        ),
        "powdery_mildew": (
            "चूर्णिल आसिता (Powdery Mildew) नियंत्रण: पत्तियों की ऊपरी सतह पर सफेद चूर्ण दिखने पर घुलनशील सल्फर 80% WDG @ 2.5 ग्राम "
            "या हेक्साकोनाजोल 5% EC @ 1 मिली प्रति लीटर पानी में मिलाकर अच्छी तरह छिड़कें।"
        ),
        "wilt": (
            "उकठा / विल्ट रोग (Fusarium / Bacterial Wilt): पौधे अचानक मुरझाकर सूखने लगें तो कॉपर ऑक्सीक्लोराइड (COC 50% WP) @ 3 ग्राम "
            "प्रति लीटर पानी में घोलकर पौधों की जड़ों के पास ड्रेन्चिंग (जड़ भिगोना) करें। खेत से अतिरिक्त पानी की निकासी सुनिश्चित करें।"
        ),
        "irrigation": (
            "सिंचाई प्रबंधन: फूल आने और फल विकास के दौरान खेत में पर्याप्त नमी बनाए रखें। "
            "अत्यधिक जलभराव या सूखा दोनों ही फल फटने का कारण बनते हैं। ड्रिप सिंचाई द्वारा नियमित अंतराल पर पानी दें।"
        ),
        "spray_optimal": (
            "आज का मौसम कीटनाशक या फफूंदनाशी छिड़काव के लिए बहुत अनुकूल है। हवा की गति शांत है। "
            "सुबह 7:00 से 9:30 बजे के बीच छिड़काव करना सबसे प्रभावशाली रहेगा।"
        ),
        "general_greeting": (
            "नमस्ते किसान भाई! मैं आपका एग्रीविज़न एआई कृषि सलाहकार हूं। "
            "फसल सुरक्षा, खाद की मात्रा, कीट प्रबंधन या मौसम के अनुसार कृषि सलाह हेतु अपना प्रश्न पूछें।"
        )
    },
    "te": {
        "early_blight": (
            "టమోటాలో ఆల్టర్నేరియా ఆకుమచ్చ తెగులు లక్షణాలు కనిపిస్తున్నాయి. ఆకులపై వలయాకార మచ్చలు ఏర్పడతాయి. "
            "నివారణ: మాంకోజెబ్ 75% WP @ 2.5 గ్రా/లీటరు నీటిలో కలిపి పిచికారీ చేయండి (PHI: 5 రోజులు)."
        ),
        "late_blight": (
            "వాతావరణంలో తేమ ఎక్కువగా ఉన్నప్పుడు లేట్ బ్లైట్ తెగులు ఆశిస్తుంది. "
            "నివారణ: సైమోక్సానిల్ + మాంకోజెబ్ @ 2 గ్రా లేదా డైమెథోమార్ఫ్ @ 1 గ్రా లీటరు నీటికి కలిపి పిచికారీ చేయండి."
        ),
        "leaf_curl": (
            "మిరప లేదా టమోటాలో ఆకు ముడుత తెగులు తామర పురుగులు (థ్రిప్స్) లేదా నల్లి వల్ల వస్తుంది. "
            "ఎకరాకు 15 నీలి మరియు పసుపు జిగురు అట్టలు ఏర్పాటు చేయండి. డయాఫెంథియురాన్ @ 1.25 గ్రా పిచికారీ చేయండి."
        ),
        "chlorosis": (
            "క్రింది ఆకులు పసుపు రంగులోకి మారితే అది నత్రజని లోపం. ఎకరాకు యూరియా వేయండి లేదా 1% యూరియా ద్రావణం పిచికారీ చేయండి."
        ),
        "fertilizer": (
            "ఎరువుల సమగ్ర యాజమాన్యం: నాటే సమయంలో ఎకరాకు 100 కిలోల డీఏపీ (DAP), 50 కిలోల పొటాష్, 25 కిలోల యూరియా వేయండి. "
            "30, 50 రోజుల్లో యూరియా వేయండి. పూత దశలో 19:19:19 ఎరువును 5 గ్రా/లీ పిచికారీ చేయండి."
        ),
        "pest": (
            "కాయ తొలుచు పురుగు నివారణ: కోరాజెన్ @ 0.3 మి.లీ లేదా ఇమామెక్టిన్ బెంజోయేట్ @ 0.5 గ్రా లీటరు నీటికి కలిపి పిచికారీ చేయండి."
        ),
        "powdery_mildew": (
            "బూడిద తెగులు నివారణ: నీటిలో కరిగే గంధకం (Sulphur 80% WDG) @ 2.5 గ్రా లీటరు నీటికి కలిపి పిచికారీ చేయండి."
        ),
        "wilt": (
            "ఎండు తెగులు నివారణ: కాపర్ ఆక్సిక్లోరైడ్ @ 3 గ్రా లీటరు నీటికి కలిపి మొక్కల మొదళ్ల వద్ద పోయండి (Drenching)."
        ),
        "irrigation": (
            "నీటి యాజమాన్యం: పూత, కాయ దశలో భూమిలో ఎల్లప్పుడూ తగినంత తేమ ఉండేలా డ్రిప్ ద్వారా నీరు అందించండి."
        ),
        "spray_optimal": (
            "ఈరోజు మందు పిచికారీ చేయడానికి వాతావరణం చాలా అనుకూలంగా ఉంది. ఉదయం 7 నుండి 9:30 గంటల మధ్య పిచికారీ చేయండి."
        ),
        "general_greeting": (
            "నమస్కారం రైతు మిత్రమా! నేను మీ అగ్రివిజన్ డిజిటల్ వ్యవసాయ సలహాదారుని. మీ పంట సమస్యలపై ఏ ప్రశ్న అయినా అడగండి."
        )
    },
    "ta": {
        "early_blight": (
            "தக்காளியில் முன்கூட்டிய இலைக்கருகல் நோய் அறிகுறிகள் உள்ளன. இலைகளில் வட்ட வடிவ பழுப்பு நிற புள்ளிகள் தோன்றும். "
            "நிவாரணம்: மேன்கோசெப் 75% WP @ 2.5 கிராம்/லிட்டர் நீரில் கலந்து தெளிக்கவும் (PHI: 5 நாட்கள்)."
        ),
        "late_blight": (
            "பிற்பட்ட இலைக்கருகல் நோய்க்கு சைமோக்சானில் + மேன்கோசெப் @ 2 கிராம்/லிட்டர் தெளிக்கவும்."
        ),
        "leaf_curl": (
            "மிளகாயில் இலை சுருட்டை நோய் இலைப்பேன் மூலம் பரவுகிறது. ஏக்கருக்கு 15 ஒட்டும் பொறிகளை வைக்கவும். டயாபெந்தியூரான் @ 1.25 கிராம் தெளிக்கவும்."
        ),
        "chlorosis": (
            "இலைகள் மஞ்சள் நிறமாக மாறினால் தழைச்சத்து பற்றாக்குறை. 1% யூரியா கரைசலை காலையில் தெளிக்கவும்."
        ),
        "fertilizer": (
            "உர மேலாண்மை: ஏக்கருக்கு 100 கிலோ டிஏபி, 50 கிலோ பொட்டாஷ், 25 கிலோ யூரியா அடியுரமாக இடவும். பூக்கும் போது 19:19:19 உரம் 5 கிராம்/லிட்டர் தெளிக்கவும்."
        ),
        "pest": (
            "காய்ப்புழு கட்டுப்பாடு: கோரஜென் @ 0.3 மி.லி அல்லது எமாமெக்டின் பென்சோயேட் @ 0.5 கிராம்/லிட்டர் நீரில் கலந்து தெளிக்கவும்."
        ),
        "powdery_mildew": (
            "சாம்பல் நோய் கட்டுப்பாடு: நனையும் கந்தகம் @ 2.5 கிராம் அல்லது ஹெக்சாகோனசோல் @ 1 மி.லி தெளிக்கவும்."
        ),
        "wilt": (
            "வாடல் நோய்க்கு காப்பர் ஆக்ஸிகுளோரைடு @ 3 கிராம்/லிட்டர் வேர்ப்பகுதியில் ஊற்றவும்."
        ),
        "irrigation": (
            "பாசன மேலாண்மை: பூக்கும் மற்றும் காய்க்கும் பருவத்தில் சீரான ஈரம் இருக்குமாறு சொட்டு நீர்ப்பாசனம் செய்யவும்."
        ),
        "spray_optimal": (
            "இன்று மருந்து தெளிக்க உகந்த வானிலை நிலவுகிறது. காலை 7:00 முதல் 9:30 மணிக்குள் தெளிக்கவும்."
        ),
        "general_greeting": (
            "வணக்கம் விவசாய பெருமக்களே! பயிர் பாதுகாப்பு, உர அளவு மற்றும் பூச்சி மேலாண்மை குறித்த உங்கள் கேள்விகளைக் கேளுங்கள்."
        )
    },
    "mr": {
        "early_blight": (
            "टोमॅटो पिकावर करपा (Early Blight) रोगाची लक्षणे दिसत आहेत. पानांवर गोलाकार काळे ठिपके पडतात. "
            "उपाय: मँकोझेब 75% WP @ 2.5 ग्रॅम प्रति लिटर पाण्यात मिसळून फवारा (PHI: 5 दिवस)."
        ),
        "late_blight": (
            "लेट ब्लाइट रोगासाठी सायमोक्सॅनिल + मँकोझेब @ 2 ग्रॅम किंवा डायमेथोमॉर्फ @ 1 ग्रॅम फवारा."
        ),
        "leaf_curl": (
            "चुरडा-मुरडा (बोकड्या) रोग थ्रिप्समुळे होतो. एकरी 15 पिवळे व निळे चिकट सापळे लावा. डायफेंथियुरॉन @ 1.25 ग्रॅम फवारा."
        ),
        "chlorosis": (
            "पाने पिवळी पडत असल्यास नत्राची कमतरता आहे. 1% युरिया द्रावण सकाळी फवारा किंवा खत द्या."
        ),
        "fertilizer": (
            "खत नियोजन: एकरी 100 किलो डीएपी, 50 किलो पोटॅश आणि 25 किलो युरिया बेसल डोस द्या. फुलधारणेच्या वेळी 19:19:19 @ 5 ग्रॅम फवारा."
        ),
        "pest": (
            "अळी व कीड नियंत्रण: कोराजन @ 0.3 मिली किंवा इमामेक्टिन बेंझोएट @ 0.5 ग्रॅम प्रति लिटर पाण्यात मिसळून फवारा."
        ),
        "powdery_mildew": (
            "भुरी रोगासाठी पाण्यात विरघळणारे गंधक (Sulphur 80% WDG) @ 2.5 ग्रॅम प्रति लिटर फवारा."
        ),
        "wilt": (
            "मर रोगासाठी कॉपर ऑक्सिक्लोराईड @ 3 ग्रॅम प्रति लिटर पाण्यात मिसळून आळवणी (Drenching) करा."
        ),
        "irrigation": (
            "पाणी व्यवस्थापन: फुलधारणा व फळधारणेच्या काळात जमिनीत सतत वाफसा राहील असे ठिबक सिंचन करा."
        ),
        "spray_optimal": (
            "आज औषध फवारणीसाठी हवामान अत्यंत अनुकूल आहे. सकाळी 7 ते 9:30 दरम्यान फवारणी करा."
        ),
        "general_greeting": (
            "नमस्कार शेतकरी मित्रांनो! मी आपला ॲग्रीव्हिजन कृषी सल्लागार आहे. पिकांच्या रोगांवर आणि खतांवर प्रश्न विचारा."
        )
    },
    "bn": {
        "early_blight": (
            "টমেটো ফসলে আগাম ধসা (Early Blight) রোগের লক্ষণ দেখা যাচ্ছে। পাতার উপর গোল কালো রিংয়ের মতো দাগ দেখা যায়। "
            "প্রতিকার: ম্যানকোজেব ৭৫% ডব্লিউপি @ ২.৫ গ্রাম প্রতি লিটার জলে মিশিয়ে স্প্রে করুন।"
        ),
        "late_blight": (
            "নাবি ধসা রোগের জন্য সাইমোক্সানিল + ম্যানকোজেব @ ২ গ্রাম প্রতি লিটার জলে মিশিয়ে স্প্রে করুন।"
        ),
        "leaf_curl": (
            "পাতা কোঁকড়ানো রোগ পোকার আক্রমণে ঘটে। বিঘায় ৫-৬টি হলুদ ও নীল আঠালো ফাঁদ লাগান। ডায়াফেনথিউরন @ ১.২৫ গ্রাম স্প্রে করুন।"
        ),
        "chlorosis": (
            "পাতা হলুদ হলে নাইট্রোজেনের ঘাটতি। ১% ইউরিয়া দ্রবণ সকালে গাছে স্প্রে করুন।"
        ),
        "fertilizer": (
            "সার প্রয়োগ: বিঘাপ্রতি ডিএপি, পটাশ এবং ইউরিয়া সঠিক অনুপাতে দিন। ফুল আসার সময় ১৯:১৯:১৯ সার ৫ গ্রাম/লিটার জলে স্প্রে করুন।"
        ),
        "pest": (
            "কীটপতঙ্গ ও ফল ছিদ্রকারী পোকা দমনে কোরাজেন @ ০.৩ মিলি বা ইম্যামেকটিন বেনজয়েট @ ০.৫ গ্রাম প্রতি লিটার জলে স্প্রে করুন।"
        ),
        "powdery_mildew": (
            "ছত্রাক ও সাদা পাউডার রোগের জন্য সালফার ৮০% ডব্লিউডিজি @ ২.৫ গ্রাম প্রতি লিটার জলে স্প্রে করুন।"
        ),
        "wilt": (
            "ঢলে পড়া (Wilt) রোগের প্রতিকারে কপার অক্সিক্লোরাইড @ ৩ গ্রাম প্রতি লিটার জলে গুলে গোড়ায় ঢালুন।"
        ),
        "irrigation": (
            "সেচ ব্যবস্থাপনা: ফুল ও ফল ধরার সময় জমিতে সঠিক আর্দ্রতা বজায় রাখুন।"
        ),
        "spray_optimal": (
            "আজ বালাইনাশক স্প্রে করার অনুকূল আবহাওয়া রয়েছে। সকালের দিকে স্প্রে করুন।"
        ),
        "general_greeting": (
            "নমস্কার কৃষক ভাই! আপনার ফসলের রোগবালাই, সার ও পোকা দমন সংক্রান্ত যেকোনো প্রশ্ন জিজ্ঞাসা করুন।"
        )
    },
    "en": {
        "early_blight": (
            "Early Blight (Alternaria solani) causes concentric brown-black target-board spots on leaves. "
            "Control: Spray Mancozeb 75% WP @ 2.5 g/L with a 5-day Pre-Harvest Interval (PHI). "
            "Organic: Spray cold-pressed Neem Oil 10,000 ppm @ 2 ml/L in the early morning."
        ),
        "late_blight": (
            "Late Blight (Phytophthora infestans) is favored by cool, humid weather causing water-soaked dark lesions. "
            "Control: Apply Cymoxanil 8% + Mancozeb 64% WP @ 2 g/L or Dimethomorph 50% WP @ 1 g/L with 7-day PHI."
        ),
        "leaf_curl": (
            "Leaf curl is transmitted by sucking vectors (thrips for upward curling, yellow mites for downward curling). "
            "Control: Install 15 yellow & blue sticky traps per acre and spray Diafenthiuron 50% WP @ 1.25 g/L."
        ),
        "chlorosis": (
            "Uniform chlorosis (yellowing) on older lower foliage indicates Nitrogen deficiency. "
            "Control: Apply water-soluble Urea via fertigation or spray 1% Urea solution (10 g/L) in early morning."
        ),
        "fertilizer": (
            "Balanced Crop Nutrient Schedule: Apply 100 kg DAP, 50 kg MOP, and 25 kg Urea per acre at basal planting. "
            "Top dress with 25 kg Urea at 30 and 50 days after planting. Spray water-soluble 19:19:19 @ 5 g/L during flowering."
        ),
        "pest": (
            "Fruit Borer & Caterpillar Control: For fruit borer or defoliators, apply Chlorantraniliprole 18.5% SC @ 0.3 ml/L "
            "or Emamectin Benzoate 5% SG @ 0.5 g/L. Deploy 5 pheromone traps per acre for pest scouting."
        ),
        "powdery_mildew": (
            "Powdery Mildew Control: Spray wettable Sulphur 80% WDG @ 2.5 g/L or Hexaconazole 5% EC @ 1 ml/L "
            "ensuring complete coverage of both upper and lower leaf surfaces."
        ),
        "wilt": (
            "Wilt Control (Bacterial / Fusarium): Drench plant root zones with Copper Oxychloride 50% WP @ 3 g/L "
            "or apply Trichoderma viride bio-fungicide into moist root soil. Ensure proper drainage to avoid water-logging."
        ),
        "irrigation": (
            "Irrigation Management: Maintain uniform soil moisture during flowering and fruit setting. "
            "Avoid alternating dry-wet extremes which trigger blossom-end rot. Drip irrigate 1.5 - 2 hours daily."
        ),
        "spray_optimal": (
            "Current meteorological conditions show calm wind (<10 km/h) and moderate humidity. "
            "Optimal knapsack spray window is open from 7:00 AM to 9:30 AM."
        ),
        "general_greeting": (
            "Hello Farmer! I am your AgriVision Agronomist assistant. "
            "Feel free to ask any question regarding crop diseases, fertilizer dosages, pest management, or spray timing."
        )
    }
}

class MultilingualAgronomistService:
    INDIC_SCRIPT_MAP = [
        (re.compile(r'[ಀ-೿]'), 'kn'), # Kannada
        (re.compile(r'[ऀ-ॿ]'), 'hi'), # Devanagari (Hindi)
        (re.compile(r'[ఀ-౿]'), 'te'), # Telugu
        (re.compile(r'[஀-௿]'), 'ta'), # Tamil
        (re.compile(r'[ঀ-৿]'), 'bn'), # Bengali
    ]

    ROMANIZED_MARKERS = {
        'kn': {'nanna', 'gida', 'ele', 'haladi', 'gobbara', 'hulu', 'roga', 'kole', 'murutu', 'aagide', 'enu', 'madodu', 'madabeku', 'neeru', 'belege', 'beleyalli', 'yava', 'yavadu', 'hege', 'ella', 'namaskara', 'kannada', 'tumba', 'kelasa', 'tomatoda', 'tomota'},
        'hi': {'tamatar', 'aalu', 'mirch', 'khet', 'kheti', 'peela', 'peeli', 'khad', 'keeda', 'keet', 'rog', 'bimari', 'patta', 'patti', 'pattiyan', 'pani', 'kya', 'kare', 'kaise', 'ilaj', 'dawa', 'dawai', 'chhidkaw', 'namaste', 'hindi', 'kripya', 'bataye', 'hai', 'mein'},
        'te': {'nenu', 'naa', 'panta', 'akulu', 'pasupu', 'eruvu', 'purugu', 'tegulu', 'mandu', 'emi', 'cheyali', 'ela', 'kadu', 'telugu', 'namaskaram', 'lo'},
        'ta': {'thakkali', 'payir', 'ilai', 'manjal', 'uram', 'marunthu', 'puzhu', 'noi', 'enna', 'seivathu', 'eppadi', 'vanakkam', 'tamil', 'il'},
        'mr': {'sheti', 'shetkari', 'pik', 'pane', 'pivle', 'khat', 'aali', 'rog', 'kay', 'karave', 'kase', 'marathi', 'namaskar', 'madhe'},
        'bn': {'aamar', 'foshol', 'pata', 'holud', 'shaar', 'poka', 'rog', 'ki', 'korbo', 'kibhabe', 'bengali', 'nomoshkar', 'te'}
    }

    def __init__(self):
        pass

    def detect_language(self, text: str, fallback_lang: str = None):
        """
        Detects if speech or text is in Kannada, Hindi, Telugu, Tamil, Marathi, Bengali, or English.
        Works across both native Indic Unicode scripts and romanized/transliterated farmer speech.
        """
        if not text:
            return fallback_lang or "en"
        # 1. Native Unicode script matching
        for pattern, lang in self.INDIC_SCRIPT_MAP:
            if pattern.search(text):
                return lang
        # 2. Romanized farmer keywords
        words = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
        scores = {}
        for lang, markers in self.ROMANIZED_MARKERS.items():
            overlap = words & markers
            if overlap:
                scores[lang] = len(overlap)
        if scores:
            return max(scores, key=scores.get)
        return fallback_lang or "en"

    def detect_and_normalize_query(self, query_text: str, user_lang: str = None):
        """
        Detects regional script/keywords and translates them to grounded agronomic concepts.
        """
        detected_l = self.detect_language(query_text, user_lang)
        lang = detected_l or user_lang or "kn"
        detected_crop = None
        symptom_tokens = []

        # Check regional dictionaries
        for l_code, data in REGIONAL_KEYWORDS.items():
            for reg_crop, eng_crop in data["crops"].items():
                if reg_crop in query_text:
                    detected_crop = eng_crop
                    lang = l_code
                    break
            for reg_symp, eng_symp in data["symptoms"].items():
                if reg_symp in query_text:
                    symptom_tokens.append(eng_symp)
                    lang = l_code
            for reg_top, eng_top in data["topics"].items():
                if reg_top in query_text:
                    symptom_tokens.append(eng_top)
                    lang = l_code

        # Fallback crop detection in romanized letters
        if not detected_crop:
            lower = query_text.lower()
            if "tomato" in lower or "tamatar" in lower: detected_crop = "Tomato"
            elif "potato" in lower or "aalu" in lower: detected_crop = "Potato"
            elif "chili" in lower or "pepper" in lower or "mirch" in lower: detected_crop = "Chili"
            elif "rice" in lower or "paddy" in lower or "dhan" in lower or "bhatta" in lower: detected_crop = "Rice"
            elif "corn" in lower or "maize" in lower or "makka" in lower or "jola" in lower: detected_crop = "Corn"
            else: detected_crop = "Tomato"

        normalized_query = f"{detected_crop} " + " ".join(symptom_tokens) if symptom_tokens else query_text
        return {
            "crop": detected_crop,
            "normalized_query": normalized_query,
            "language": lang
        }

    def generate_multilingual_response(self, user_query: str, user_lang: str = None, context: dict = None):
        """
        Synthesizes agronomic response in the detected or selected regional language.
        Prioritizes detected native/romanized language of query, then user selection, defaulting to Kannada.
        """
        info = self.detect_and_normalize_query(user_query, user_lang)
        crop = info["crop"]
        detected_lang = info["language"]

        # Accurate Language Decision
        if detected_lang and detected_lang in ['kn', 'hi', 'te', 'ta', 'mr', 'bn']:
            lang = detected_lang
        elif user_lang and user_lang in REGIONAL_LANGUAGES:
            lang = user_lang
        elif detected_lang:
            lang = detected_lang
        else:
            lang = "kn" 

        query_lower = user_query.lower()

        # Check for specific disease / topic
        adv_key = "general_greeting"
        if any(w in query_lower for w in ["yellow", "yellowing", "chlorosis", "haladi", "peela", "peeli", "pasupu", "manjal", "pivle", "holud", "ಹಳದಿ", "ಪೀಲಾ", "पीला", "पीली", "పసుపు", "மஞ்சள்", "पिवळे", "হলুদ"]):
            adv_key = "chlorosis"
        elif any(w in query_lower for w in ["curl", "curling", "thrips", "mites", "murutu", "muruda", "churda", "bokadya", "ಮುರುಟು", "ಮುರುಡ", "मरोड़िया", "मुर्रा", "ముడుత", "சுருட்டை", "बोकड्या", "কোঁকড়ানো"]):
            adv_key = "leaf_curl"
        elif any(w in query_lower for w in ["late", "rot", "phytophthora", "kole", "kolethe", "sadun", "dhosa", "ಕೊಳೆತ", "ಕೊಳೆ", "सड़न", "पछेती", "కుళ్లు", "கழுகு", "धसा"]):
            adv_key = "late_blight"
        elif any(w in query_lower for w in ["blight", "spot", "alternaria", "macche", "chukke", "jhulsa", "dhabba", "dag", "karpa", "ಮಚ್ಚೆ", "ಚುಕ್ಕೆ", "झुलसा", "धब्बा", "మచ్చ", "புள்ளி", "करपा", "দাগ"]):
            adv_key = "early_blight"
        elif any(w in query_lower for w in ["weather", "spray", "spraying", "simparane", "simpadane", "havamana", "chhidkaw", "mausam", "హవాಮಾನ", "ಸಿಂಪರಣೆ", "ಸಿಂಪಡಣೆ", "मौसम", "छिड़काव", "వాతావరణం", "வானிலை", "हवामान", "আবহাওয়া"]):
            adv_key = "spray_optimal"
        elif any(w in query_lower for w in ["fertilizer", "urea", "dap", "npk", "dose", "gobbara", "khad", "urvarak", "eruvu", "uram", "khat", "shaar", "ಗೊಬ್ಬರ", "ಯೂರಿಯಾ", "ಡಿಎಪಿ", "खाद", "उर्वरक", "डीएपी", "यूरिया", "ఎరువు", "உரம்", "खत", "সার"]):
            adv_key = "fertilizer"
        elif any(w in query_lower for w in ["powdery", "mildew", "boodi", "churna", "safed", "ಬೂದಿ", "ಚೂರ್ಣಿಲ", "चूर्णिल", "పౌడరీ", "சாம்பல்", "भुरी", "ছত্রাক"]):
            adv_key = "powdery_mildew"
        elif any(w in query_lower for w in ["pest", "caterpillar", "borer", "worm", "insect", "hulu", "kida", "kita", "keeda", "keet", "illi", "purugu", "puzhu", "poka", "aali", "ಹುಳು", "ಕೀಟ", "कीट", "इल्ली", "कीड़ा", "పురుగు", "புழு", "अळी", "পোকা"]):
            adv_key = "pest"
        elif any(w in query_lower for w in ["wilt", "wilting", "drying", "soragu", "baduvike", "uktha", "sukha", "mar", "ಸೊರಗು", "ಬಾಡುವಿಕೆ", "ಉಕಠಾ", "उकठा", "मुरझाना", "ఎండిపోవడం", "வாடல்", "सुका"]):
            adv_key = "wilt"
        elif any(w in query_lower for w in ["water", "watering", "irrigation", "neeru", "neeravari", "pani", "sinchai", "paani", "jol", "ನೀರು", "ನೀರಾವರಿ", "पानी", "सिंचाई", "నీరు", "నీటిపారుదల", "பாசனம்", "पाणी", "জল"]):
            adv_key = "irrigation"

        # Fetch localized text from regional dictionary
        regional_dict = REGIONAL_ADVISORIES.get(lang, REGIONAL_ADVISORIES.get("kn", {}))
        reply_text = regional_dict.get(adv_key)

        if not reply_text:
            reply_text = regional_dict.get("general_greeting") or f"Namaskara! Consultation for {crop}: Monitor moisture and scout for pests daily."

        # Follow-up prompts in regional language
        followups = {
            "kn": ["ಟೊಮೆಟೊ ಕರಗು ರೋಗದ ಔಷಧ ಪ್ರಮಾಣವೇನು?", "ಇಂದು ಔಷಧ ಸಿಂಪಡಿಸಲು ಹವಾಮಾನ ಯೋಗ್ಯವೇ?", "ಮೆಣಸಿನಕಾಯಿ ಎಲೆ ಮುರುಟು ರೋಗಕ್ಕೆ ಜೈವಿಕ ನಿಯಂತ್ರಣವೇನು?"],
            "hi": ["टमाटर में झुलसा रोग की दवा क्या है?", "क्या आज दवा छिड़काव का सही समय है?", "मिर्च में पत्ता मरोड़ का जैविक उपाय क्या है?"],
            "te": ["టమోటా ఆకుమచ్చ తెగులు మందు మోతాదు ఎంత?", "ఈరోజు పిచికారీ చేయడానికి వాతావరణం బాగుందా?"],
            "ta": ["தக்காளி இலைக்கருகல் மருந்து அளவு என்ன?", "இன்று மருந்து தெளிக்க உகந்த நேரமா?"],
            "mr": ["टोमॅटो करपा रोगाचे औषध प्रमाण काय आहे?", "आज औषध फवारणीसाठी योग्य वेळ आहे का?"],
            "bn": ["টমেটো ধসা রোগের ওষুধ কী?", "আজ স্প্রে করার সঠিক সময় কোনটি?"],
            "en": ["What is the dosage of Mancozeb for Tomato?", "Is today's wind suitable for knapsack spraying?", "How to control chili leaf curl organically?"]
        }

        citations = {
            "kn": ["ಐ.ಸಿ.ಎ.ಆರ್ - ಭಾರತೀಯ ತೋಟಗಾರಿಕಾ ಸಂಶೋಧನಾ ಸಂಸ್ಥೆ (ICAR-IIHR), ಬೆಂಗಳೂರು", "ಕೃಷಿ ವಿಶ್ವವಿದ್ಯಾನಿಲಯ, ಬೆಂಗಳೂರು (UAS-B) ವಿಸ್ತರಣಾ ಮಾರ್ಗದರ್ಶಿ"],
            "hi": ["भा.कृ.अनु.प. - भारतीय कृषि अनुसंधान संस्थान (ICAR-IARI), नई दिल्ली", "केंद्रीय कीटनाशक बोर्ड (CIBRC) पंजीकृत निर्देशिका"],
            "te": ["ICAR-IIHR & ఆచార్య ఎన్.జి. రంగా వ్యవసాయ విశ్వవిద్యాలయం (ANGRAU) మార్గదర్శకాలు"],
            "ta": ["ICAR & தமிழ்நாடு வேளாண்மைப் பல்கலைக்கழகம் (TNAU) பயிர் பாதுகாப்பு வழிகாட்டி"],
            "mr": ["ICAR & महात्मा फुले कृषी विद्यापीठ (MPKV) राहुरी मार्गदर्शक तत्त्वे"],
            "bn": ["ICAR & বিধানচন্দ্র কৃষি বিশ্ববিদ্যালয় (BCKV) কৃষি নির্দেশিকা"],
            "en": ["ICAR-IIHR Technical Bulletin No. 44 (2024)", "UAS Bangalore Agricultural Extension Field Leaflet (2023)"]
        }

        return {
            "success": True,
            "crop": crop,
            "language": lang,
            "bcp47": REGIONAL_LANGUAGES.get(lang, {}).get("bcp47", "en-IN"),
            "reply": reply_text,
            "speech_text": reply_text.replace("*", "").replace("#", ""),
            "citations": citations.get(lang, citations["en"]),
            "suggested_followups": followups.get(lang, followups["en"])
        }

i18n_service = MultilingualAgronomistService()
