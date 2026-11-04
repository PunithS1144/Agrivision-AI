-- SQLite Schema for AgriVision / Plantix AI (Phase 3 RAG & Agronomist)

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    phone TEXT,
    village TEXT,
    state TEXT DEFAULT 'Karnataka',
    preferred_language TEXT DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS farms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    farm_name TEXT NOT NULL,
    acreage REAL DEFAULT 1.0,
    soil_type TEXT DEFAULT 'Red Sandy Loam',
    irrigation_type TEXT DEFAULT 'Drip Irrigation',
    location TEXT DEFAULT 'Bengaluru Rural',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS crops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id INTEGER NOT NULL,
    crop_name TEXT NOT NULL,
    variety TEXT,
    sowing_date DATE,
    stage TEXT DEFAULT 'Vegetative',
    health_status TEXT DEFAULT 'Healthy',
    area_acres REAL DEFAULT 1.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(farm_id) REFERENCES farms(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS diagnoses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    crop_id INTEGER,
    image_path TEXT NOT NULL,
    diagnosed_crop TEXT NOT NULL,
    disease_name TEXT NOT NULL,
    confidence REAL NOT NULL,
    severity TEXT DEFAULT 'Moderate',
    symptoms TEXT,
    cause TEXT,
    chemical_treatment TEXT,
    biological_treatment TEXT,
    organic_treatment TEXT,
    cultural_treatment TEXT,
    active_ingredient TEXT,
    phi_days INTEGER DEFAULT 7,
    frac_code TEXT DEFAULT 'M03',
    preventive_measures TEXT,
    monitoring_recommendations TEXT,
    alternative_diagnoses_json TEXT,
    symptom_localization_json TEXT,
    diagnostic_certainty TEXT DEFAULT 'confirmed', -- confirmed, uncertain_diagnosis, poor_quality, local_preliminary
    weather_context_json TEXT,
    client_uuid TEXT UNIQUE,
    is_offline INTEGER DEFAULT 0,
    sync_status TEXT DEFAULT 'synced',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(crop_id) REFERENCES crops(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS fertilizer_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    crop_name TEXT NOT NULL,
    growth_stage TEXT DEFAULT 'Basal',
    acreage REAL NOT NULL,
    area_unit TEXT DEFAULT 'Acres',
    soil_test_available INTEGER DEFAULT 0,
    urea_kg REAL NOT NULL,
    dap_kg REAL NOT NULL,
    mop_kg REAL NOT NULL,
    schedule_json TEXT,
    calculation_explanation TEXT,
    estimated_cost_inr INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS farm_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id INTEGER NOT NULL,
    crop_id INTEGER,
    activity_type TEXT NOT NULL,
    activity_date DATE NOT NULL,
    description TEXT NOT NULL,
    quantity_used TEXT,
    client_uuid TEXT UNIQUE,
    is_offline INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(farm_id) REFERENCES farms(id) ON DELETE CASCADE,
    FOREIGN KEY(crop_id) REFERENCES crops(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT DEFAULT 'info',
    message TEXT NOT NULL,
    action_link TEXT,
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT DEFAULT 'Pest & Disease',
    severity TEXT DEFAULT 'warning',
    message TEXT NOT NULL,
    region TEXT DEFAULT 'Karnataka',
    date_posted DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS community_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    author_name TEXT NOT NULL,
    author_village TEXT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    crop_tag TEXT,
    image_path TEXT,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS community_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    author_name TEXT NOT NULL,
    comment_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(post_id) REFERENCES community_posts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS retailers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    shop_type TEXT DEFAULT 'Agri-Input & Pesticide Store',
    phone TEXT NOT NULL,
    address TEXT NOT NULL,
    distance_km REAL DEFAULT 3.5,
    rating REAL DEFAULT 4.7,
    verified INTEGER DEFAULT 1,
    products_available TEXT DEFAULT 'Bio-fungicides, Urea, DAP, Micronutrients, Neem Oil, Sprayers'
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    sender TEXT NOT NULL, -- 'user' or 'agronomist'
    text TEXT NOT NULL,
    attached_image_path TEXT,
    sources_json TEXT,
    context_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);
