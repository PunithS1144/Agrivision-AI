# Seasonal Agronomy Advice & AI Agronomist Query Engine

FARMING_TIPS = [
    {
        "id": 1,
        "title": "Morning Spraying Principle",
        "category": "Plant Protection",
        "tip": "Always apply systemic fungicides and neem formulations between 7:00 AM and 10:00 AM after morning dew has evaporated. Avoid mid-day spray when stomata close to prevent leaf scorch.",
        "crop": "All Crops"
    },
    {
        "id": 2,
        "title": "Tomato Blossom Drop Prevention",
        "category": "Horticulture",
        "tip": "During heavy flowering, high nighttime temperatures (>24°C) or boron deficiency cause flower abscission. Spray 20% Boron @ 1 g/L combined with Planofix @ 0.25 ml/4.5 L water.",
        "crop": "Tomato"
    },
    {
        "id": 3,
        "title": "Drip Fertigation Efficiency",
        "category": "Irrigation & Nutrients",
        "tip": "Follow the 4-part fertigation cycle: 1) Run clean water for 15 mins to pressurize lines, 2) Inject fertilizer solution over 30-40 mins, 3) Flush lines with clean water for 15 mins to eliminate salt clogging.",
        "crop": "General"
    },
    {
        "id": 4,
        "title": "Biological Root Health Boost",
        "category": "Organic & Soil Health",
        "tip": "Incorporate 2 kg of Pseudomonas fluorescens mixed with 100 kg farmyard manure per acre at planting to establish defensive colonies against bacterial wilt and damping-off.",
        "crop": "Chili & Solanaceous"
    }
]

BOT_KNOWLEDGE = {
    "yellowing": "Leaf yellowing (chlorosis) can stem from: 1) Nitrogen deficiency (starts on older bottom leaves), 2) Iron/Zinc deficiency (interveinal yellowing on young upper leaves), 3) Over-watering or root asphyxiation, or 4) Viral infection like Leaf Curl. Would you like to upload a photo for automated diagnosis?",
    "curling": "Leaf curling in chili and tomato is often caused by sap-sucking pests (Thrips curl leaves upward; Mites curl leaves downward like an inverted cup). Spray Diafenthiuron 50% WP @ 1.2 g/L or Bio-Neem oil 10,000 ppm @ 2 ml/L.",
    "fertilizer": "For balanced vegetable nutrition, split NPK applications: 100% Phosphorus and 50% Potash at basal planting, and Nitrogen in 3 equal splits to avoid leaching losses.",
    "weather": "Current humidity in your region is favorable for fungal sporulation. Avoid overhead sprinkler irrigation and inspect lower leaves for water-soaked spots.",
    "tomato": "For tomatoes, monitor for Early Blight (target-board spots) and Late Blight (water-soaked dark patches). Ensure good vine staking and drip irrigation.",
    "spray": "Best spraying window is early morning with wind speeds below 12 km/h and relative humidity between 60% and 80%."
}

def get_seasonal_recommendations():
    return FARMING_TIPS

# Priority ordered keywords: Specific symptoms first, then generic crop topics
PRIORITY_KEYWORDS = [
    "yellowing", "yellow", "chlorosis",
    "curling", "curl",
    "blight", "spots", "fungus",
    "fertilizer", "npk", "urea", "dap",
    "spray", "spraying", "pesticide",
    "weather", "rain", "humidity",
    "tomato", "chili", "potato"
]

def consult_ai_agronomist(user_query):
    query_lower = user_query.lower()
    
    # Check priority keywords first
    for kw in PRIORITY_KEYWORDS:
        if kw in query_lower:
            # Map keyword variant to knowledge base key
            if kw in ["yellowing", "yellow", "chlorosis"]:
                return BOT_KNOWLEDGE["yellowing"]
            if kw in ["curling", "curl"]:
                return BOT_KNOWLEDGE["curling"]
            if kw in ["fertilizer", "npk", "urea", "dap"]:
                return BOT_KNOWLEDGE["fertilizer"]
            if kw in ["spray", "spraying", "pesticide"]:
                return BOT_KNOWLEDGE["spray"]
            if kw in ["weather", "rain", "humidity"]:
                return BOT_KNOWLEDGE["weather"]
            if kw in ["tomato"]:
                return BOT_KNOWLEDGE["tomato"]
            
    # Default comprehensive response
    return (
        f"Thank you for your agronomic question regarding: '{user_query}'. "
        "As an AI Agronomist, I recommend checking three core factors: "
        "1) Soil moisture and root aeration at 10 cm depth, "
        "2) Signs of sap-sucking pests (whiteflies, thrips, mites) on leaf undersides, and "
        "3) Soil electrical conductivity (EC) and pH balance (ideal 6.2 - 6.8). "
        "For immediate diagnosis, capture a close photo of the affected leaf in our Crop Diagnosis tab!"
    )
