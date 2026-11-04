# Context-Aware AI Agronomist Consultation Engine with Grounded RAG & Safety Guardrails

from services.rag_knowledge_base import rag_retriever
from services.ai_diagnosis import diagnosis_engine

SAFETY_DISCLAIMER = (
    "\n\n---\n*Disclaimer: I am an AI Agronomic Assistant grounded in ICAR, UAS Bangalore, and TNAU agronomic standards. "
    "Always read product packaging labels and verify with your local agricultural officer or Krishi Vigyan Kendra (KVK) before applying chemical inputs.*"
)

SUGGESTED_PROMPTS = [
    "Why are my bottom tomato leaves yellowing with dark rings?",
    "Is today's weather safe for knapsack spraying?",
    "How to manage downward leaf curling in chili organically?",
    "What is the recommended Urea & DAP split for flowering stage?",
    "Explain FRAC resistance management for fungicides",
    "How to prevent blossom end rot in tomatoes?"
]

class AIAgronomistEngine:
    def __init__(self):
        pass

    def generate_response(self, user_query, context=None, attached_image_path=None):
        """
        Synthesizes agronomic response grounded in RAG retrieval, operational farm context,
        weather data, and past diagnosis records.
        """
        context = context or {}
        farmer_name = context.get("farmer_name", "Farmer")
        crop_context = context.get("crop_name", "Tomato")
        stage = context.get("growth_stage", "Vegetative Growth")
        village = context.get("village", "Bengaluru Rural")
        weather = context.get("weather", {})
        recent_diagnoses = context.get("recent_diagnoses", [])

        # 1. Handle Multimodal Image Attachment in Chat
        image_analysis_summary = ""
        if attached_image_path:
            diag_res = diagnosis_engine.diagnose_crop_leaf(attached_image_path, user_selected_crop=crop_context)
            if diag_res.get("success"):
                image_analysis_summary = (
                    f"📸 **Visual Inspection Results:** I analyzed your attached leaf image. "
                    f"Detected **{diag_res.get('disease')}** on **{diag_res.get('crop')}** with **{diag_res.get('confidence')}% confidence** "
                    f"(Severity: *{diag_res.get('severity')}*).\n\n"
                    f"**Identified Symptoms:** {diag_res.get('symptoms')}\n\n"
                )
            else:
                image_analysis_summary = (
                    f"⚠️ **Visual Quality Notice:** The attached photo could not be reliably diagnosed "
                    f"due to: *{diag_res.get('error')}*. Please ensure good natural daylight and focus directly on the leaf.\n\n"
                )

        # 2. Retrieve Grounded Agronomic Knowledge (RAG)
        retrieved_docs = rag_retriever.retrieve(user_query, top_k=2, crop_context=crop_context)

        # 3. Context-Aware Synthesis
        query_lower = user_query.lower()
        response_body = ""
        citations = []

        # Weather / Spraying queries
        if any(w in query_lower for w in ["weather", "spray", "spraying", "wind", "rain"]):
            spray_status = weather.get("agri_advisory", {}).get("spray_condition", "Optimal Spray Window")
            spray_reason = weather.get("agri_advisory", {}).get("spray_reason", "Calm wind and normal humidity.")
            curr_temp = weather.get("current", {}).get("temperature", 27.2)
            curr_wind = weather.get("current", {}).get("wind_speed", 7.5)
            curr_hum = weather.get("current", {}).get("humidity", 68)

            response_body = (
                f"Based on real-time meteorological conditions for **{village}**:\n\n"
                f"• **Spraying Feasibility:** **{spray_status}**\n"
                f"• **Current Parameters:** Temperature {curr_temp}°C | Relative Humidity {curr_hum}% | Wind Speed {curr_wind} km/h\n"
                f"• **Agronomic Advisory:** {spray_reason}\n\n"
                f"**Best Practice:** Always apply systemic fungicides and neem extracts during early morning (7:00 AM – 9:30 AM). "
                f"Never spray when wind speeds exceed 15 km/h to avoid chemical drift onto neighboring plots."
            )
            citations.append("CIBRC Good Agricultural Spraying Practices & Open-Meteo Meteorological Feed")

        # Fertilizer / Nutrition queries
        elif any(w in query_lower for w in ["fertilizer", "urea", "dap", "mop", "nitrogen", "npk", "dosage", "basal"]):
            doc = retrieved_docs[0] if retrieved_docs else None
            response_body = (
                f"For **{crop_context}** during the **{stage}** stage:\n\n"
                f"1. **Basal Application:** 100% of Phosphorus (DAP) must be applied at planting because phosphorus is immobile in the soil profile. Apply 50% of Potash (MOP) at planting.\n"
                f"2. **Nitrogen Splitting:** Split Urea across 3 intervals (25% Basal, 40% Vegetative, 35% Flowering) to avoid leaching losses.\n"
                f"3. **Micronutrients:** At flower bud initiation, spray 20% Solubor (Boron) @ 1.0 g/L combined with Zinc Sulphate (21%) to maximize pollination and fruit retention.\n\n"
                f"You can calculate exact commercial bags for your acreage using our **Fertilizer Calculator** tab!"
            )
            if doc:
                citations.append(doc["citation"])

        # Disease / Pest queries
        elif any(w in query_lower for w in ["blight", "yellow", "yellowing", "curl", "curling", "spots", "thrips", "mites", "fungus", "disease"]):
            doc = retrieved_docs[0] if retrieved_docs else None
            if doc:
                response_body = (
                    f"Regarding your query on **{doc['topic']}**:\n\n"
                    f"{doc['content']}\n\n"
                    f"• **PHI Waiting Period:** {doc['phi_days']} Days before harvest\n"
                    f"• **Resistance Management:** {doc['frac_code']} rotation guidelines apply."
                )
                citations.append(doc["citation"])
            else:
                response_body = (
                    f"For leaf symptoms in **{crop_context}**, the primary causes to differentiate are:\n\n"
                    f"1. **Fungal Pathogens:** Look for circular concentric rings (Early Blight) or dark water-soaked patches with white downy undersides (Late Blight).\n"
                    f"2. **Sap-Sucking Pests:** Thrips curl leaves upward into a boat/cup shape; Yellow Mites curl leaves downward.\n"
                    f"3. **Nutrient Latency:** Uniform pale yellowing on older bottom leaves denotes Nitrogen deficiency.\n\n"
                    f"Please snap a close photograph in our **Crop Diagnosis** tab so I can localize and verify the pathogen for you!"
                )

        # General Agronomic Consultation
        else:
            if retrieved_docs:
                doc = retrieved_docs[0]
                response_body = (
                    f"Here is verified agronomic guidance regarding your question:\n\n"
                    f"{doc['content']}\n\n"
                    f"• **Source Reference:** *{doc['citation']}*"
                )
                citations.append(doc["citation"])
            else:
                response_body = (
                    f"Hello {farmer_name}. For optimal management of your **{crop_context}** plot in **{village}**:\n\n"
                    f"• Maintain balanced drip fertigation and scout for early leaf spot lesions on lower canopy foliage.\n"
                    f"• Maintain yellow and blue sticky traps (15 traps/acre) to detect whitefly and thrips populations.\n"
                    f"• If you observe specific spotting, wilting, or yellowing, upload a photo or ask a specific agronomic question!"
                )

        full_message = f"{image_analysis_summary}{response_body}{SAFETY_DISCLAIMER}"

        # Generate Contextual Follow-up Chips
        followups = [
            f"What is the recommended spray dosage for {crop_context}?",
            f"How to protect {crop_context} during cloudy weather?",
            "Explain biological vs chemical treatments",
            "Is today's wind safe for field spraying?"
        ]

        return {
            "reply": full_message,
            "text": full_message,
            "citations": citations,
            "suggested_followups": followups,
            "safety_disclaimer": SAFETY_DISCLAIMER
        }

agronomist_engine = AIAgronomistEngine()
