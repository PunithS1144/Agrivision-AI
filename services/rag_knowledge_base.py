# Retrieval-Augmented Generation (RAG) Agronomic Knowledge Base
# Grounded in official publications: ICAR, UAS Bangalore, TNAU, IIHR, and CIBRC.

import re
import math
from collections import Counter

AGRONOMIC_CORPUS = [
    {
        "id": "DOC-TOM-001",
        "crop": "Tomato",
        "topic": "Early Blight & Alternaria Management",
        "keywords": ["early blight", "alternaria", "concentric rings", "target board", "mancozeb", "azoxystrobin", "yellow halo"],
        "content": (
            "Early blight (Alternaria solani) initiates as small brown-black spots with concentric rings ('target board') on older foliage. "
            "Under warm humid weather (24-29°C), yellow chlorotic halos develop around spots, inducing premature leaf drop. "
            "Standard ICAR protocol recommends prophylactic Mancozeb 75% WP @ 2.5 g/L or curative Azoxystrobin 23% SC @ 1.0 ml/L. "
            "To manage FRAC 11 resistance, never apply strobilurins consecutively more than twice; rotate with multi-site Mancozeb (FRAC M03). "
            "Biocontrol: Spray Bacillus subtilis or Trichoderma harzianum @ 5 g/L at first flowering."
        ),
        "citation": "ICAR-IIHR Technical Bulletin No. 44: Integrated Disease Management in Solanaceous Vegetables (2024)",
        "frac_code": "FRAC M03 / FRAC 11",
        "phi_days": 5
    },
    {
        "id": "DOC-TOM-002",
        "crop": "Tomato",
        "topic": "Late Blight Epidemic Management",
        "keywords": ["late blight", "phytophthora", "downy mildew", "water soaked", "metalaxyl", "cymoxanil", "humidity"],
        "content": (
            "Late blight (Phytophthora infestans) is an oomycete disease triggered by cool (15-22°C), overcast weather with relative humidity > 90%. "
            "Symptom: Large irregular water-soaked oily spots turning rapidly dark brown to purplish with delicate white downy mold on leaf undersides in morning fog. "
            "Curative treatment: Cymoxanil 8% + Mancozeb 64% WP @ 2 g/L or Dimethomorph 50% WP @ 1 g/L. "
            "Ensure full coverage of both leaf surfaces. Rogue and deeply bury severely infected plants outside the plot. "
            "Avoid overhead sprinkler irrigation to keep canopy dry."
        ),
        "citation": "UAS Bangalore Agricultural Extension Leaflet: Late Blight Forecasting and Management (2023)",
        "frac_code": "FRAC 27 + M03",
        "phi_days": 7
    },
    {
        "id": "DOC-NUT-001",
        "crop": "Tomato",
        "topic": "Nitrogen Deficiency vs Chlorosis",
        "keywords": ["nitrogen", "yellowing", "chlorosis", "older leaves", "urea", "stunting", "bottom leaves"],
        "content": (
            "Nitrogen deficiency exhibits uniform pale yellowing (chlorosis) beginning strictly on older, bottom mature leaves, progressing upward as mobile N is translocated to young shoots. "
            "Veins and leaf lamina yellow simultaneously; plants show stunted upright growth and thin spindly stems. "
            "Corrective action: Drip fertigation with water-soluble Urea (46% N) @ 3-5 kg/acre or 1% foliar Urea spray (10 g/L water) in the morning. "
            "Distinguish from Iron deficiency (which causes interveinal yellowing on young top leaves) and viral leaf curl."
        ),
        "citation": "ICAR-IARI Agronomy Guide: Nutrient Deficiency Diagnostics in Horticulture (2023)",
        "frac_code": "Nutritional",
        "phi_days": 0
    },
    {
        "id": "DOC-CHL-001",
        "crop": "Chili",
        "topic": "Leaf Curling: Thrips vs Mites vs Viral Murda Complex",
        "keywords": ["curling", "curl", "thrips", "mites", "yellow leaf curl", "murda", "boat shaped", "upward", "downward"],
        "content": (
            "Chili leaf curl complex ('Murda complex') stems from two major sucking pests: "
            "1) Yellow Mites (Polyphagotarsonemus latus): Cause downward curling (inverted boat shape) with thickened, brittle, bronzed lower leaf surfaces. Spray Spiromesifen 22.9% SC @ 1 ml/L or wettable sulfur @ 3 g/L. "
            "2) Thrips (Scirtothrips dorsalis): Cause upward curling (cup shape) with silvery feeding scars along midribs. Spray Diafenthiuron 50% WP @ 1.2 g/L or Bio-Neem oil 10,000 ppm @ 2.5 ml/L. "
            "3) Viral Leaf Curl: Transmitted by Bemisia tabaci whiteflies; causes severe puckering and stunted bushy growth."
        ),
        "citation": "TNAU Agritech Portal: Chili Pest & Vector Integrated Management Guidelines (2024)",
        "frac_code": "IRAC 23 (Spiromesifen) / IRAC 12A (Diafenthiuron)",
        "phi_days": 7
    },
    {
        "id": "DOC-WTH-001",
        "crop": "General",
        "topic": "Agro-Meteorological Spraying Windows & Drift Guidelines",
        "keywords": ["spraying", "spray window", "wind speed", "drift", "rain washout", "morning spray", "temperature", "humidity"],
        "content": (
            "Optimal chemical and biological foliar spraying parameters: "
            "1) Wind Velocity: Must remain strictly between 3 km/h and 12 km/h. Wind > 15 km/h causes high droplet drift onto non-target areas; calm air < 3 km/h causes thermal inversion. "
            "2) Temperature: Spray during morning (7:00 AM - 9:30 AM) when temperature is < 28°C to prevent droplet evaporation. "
            "3) Rain Washout: Avoid spraying if rain probability > 40% within 4-6 hours unless using an organosilicone rainfast adjuvant. "
            "4) Operator Safety: Always spray across or downwind, never walking into the spray cloud."
        ),
        "citation": "Central Insecticide Board & Registration Committee (CIBRC): Good Agricultural Spraying Practices (2024)",
        "frac_code": "Agricultural Engineering Standard",
        "phi_days": 0
    },
    {
        "id": "DOC-POT-001",
        "crop": "Potato",
        "topic": "Potato Tuber Health & Haulm Destruction",
        "keywords": ["potato", "late blight", "earthing up", "haulm cutting", "dimethomorph", "tuber rot"],
        "content": (
            "Potato Late Blight protection requires cultural shield ridges: "
            "Earth up ridge height to at least 25 cm around tuber roots. This prevents swimming Phytophthora zoospores from washing down into developing tubers during rain. "
            "Spray Dimethomorph 50% WP @ 1 g/L or Fenamidone + Mancozeb WG @ 2 g/L. "
            "Cut haulms (foliage vines) 10 to 12 days prior to tuber lifting to allow tuber skins to harden and prevent infection during harvest."
        ),
        "citation": "ICAR-Central Potato Research Institute (CPRI): Potato Package of Practices (2023)",
        "frac_code": "FRAC 40 / FRAC 11",
        "phi_days": 10
    },
    {
        "id": "DOC-FRT-001",
        "crop": "General",
        "topic": "Precision N-P-K Split Fertigation Principles",
        "keywords": ["fertilizer", "npk", "urea", "dap", "mop", "basal", "top dressing", "fertigation", "phosphorus", "potash"],
        "content": (
            "Scientific N-P-K fertigation principles for vegetable crops: "
            "100% of Phosphorus (DAP) must be applied as a basal dose during transplanting because phosphorus binds tightly to soil colloids and is immobile. "
            "Apply 50% of Potassium (MOP) basal and 50% during fruit setting to expand fruit diameter. "
            "Split Nitrogen (Urea) into 3 equal splits: 25% Basal, 40% Vegetative, 35% Flowering to prevent nitrogen leaching losses and groundwater contamination. "
            "Flush drip irrigation lines with fresh water for 15 minutes post-injection to prevent emitter salt crystallization."
        ),
        "citation": "UAS Dharwad & Karnataka State Department of Agriculture: Precision Horticulture Guidelines (2024)",
        "frac_code": "Plant Nutrition Protocol",
        "phi_days": 0
    }
]

class AgronomicRAGRetriever:
    def __init__(self, corpus=None):
        self.corpus = corpus or AGRONOMIC_CORPUS
        self._build_index()

    def _build_index(self):
        self.doc_tokens = []
        self.doc_freqs = Counter()
        for doc in self.corpus:
            # Tokenize keywords + content + title
            text = f"{doc['topic']} {' '.join(doc['keywords'])} {doc['content']}".lower()
            tokens = re.findall(r'\b[a-z]{3,}\b', text)
            self.doc_tokens.append(tokens)
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.doc_freqs[t] += 1
        self.num_docs = len(self.corpus)

    def retrieve(self, query, top_k=2, crop_context=None, crop=None):
        """
        Retrieves top relevant agronomic reference passages based on BM25-style lexical scoring
        with crop-affinity weighting.
        """
        crop_context = crop or crop_context
        query_tokens = re.findall(r'\b[a-z]{3,}\b', query.lower())
        if not query_tokens:
            return []

        scores = []
        for idx, doc in enumerate(self.corpus):
            tokens = self.doc_tokens[idx]
            doc_len = len(tokens)
            token_counts = Counter(tokens)
            score = 0.0

            # Match tokens
            for qt in query_tokens:
                if qt in token_counts:
                    tf = token_counts[qt]
                    df = self.doc_freqs[qt]
                    idf = math.log((self.num_docs - df + 0.5) / (df + 0.5) + 1.0)
                    score += idf * (tf * 2.2) / (tf + 1.2 * (0.25 + 0.75 * doc_len / 120.0))

            # Crop Context Affinity Boost
            if crop_context and (crop_context.lower() in doc['crop'].lower() or doc['crop'] == "General"):
                score *= 1.35

            scores.append((score, doc))

        # Sort descending
        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for s, doc in scores:
            if s > 0.8:
                results.append({
                    "id": doc["id"],
                    "topic": doc["topic"],
                    "crop": doc["crop"],
                    "content": doc["content"],
                    "citation": doc["citation"],
                    "frac_code": doc.get("frac_code", ""),
                    "phi_days": doc.get("phi_days", 0),
                    "relevance_score": round(s, 2)
                })
            if len(results) >= top_k:
                break
        return results

rag_retriever = AgronomicRAGRetriever()
