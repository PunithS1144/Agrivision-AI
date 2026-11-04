import sqlite3
import os
from werkzeug.security import generate_password_hash
from config import Config

def get_db_connection():
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute(f"PRAGMA busy_timeout = {Config.DB_BUSY_TIMEOUT_MS}")
    conn.execute(f"PRAGMA cache_size = {Config.DB_CACHE_SIZE_KB}")
    conn.execute("PRAGMA temp_store = MEMORY")
    return conn

def init_db():
    conn = get_db_connection()
    with open(os.path.join(Config.BASE_DIR, 'database', 'schema.sql'), 'r') as f:
        conn.executescript(f.read())

    # Phase 9: Schema Migration Tracking Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 9: Privacy Consents Table (DPDP Act 2023 & GDPR Compliance)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS privacy_consents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            consent_type TEXT NOT NULL,
            is_granted INTEGER DEFAULT 1,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, consent_type)
        )
    """)

    # Migration checks for Phase 3 & Phase 4 columns in diagnoses
    for col in [
        "symptom_localization_json TEXT",
        "diagnostic_certainty TEXT DEFAULT 'confirmed'",
        "weather_context_json TEXT",
        "client_uuid TEXT",
        "is_offline INTEGER DEFAULT 0",
        "sync_status TEXT DEFAULT 'synced'"
    ]:
        try:
            conn.execute(f"ALTER TABLE diagnoses ADD COLUMN {col}")
        except Exception:
            pass

    # Migration checks for Phase 4 columns in farm_activities and crops
    for col in [
        "client_uuid TEXT",
        "is_offline INTEGER DEFAULT 0"
    ]:
        try:
            conn.execute(f"ALTER TABLE farm_activities ADD COLUMN {col}")
        except Exception:
            pass

    for col in [
        "client_uuid TEXT"
    ]:
        try:
            conn.execute(f"ALTER TABLE crops ADD COLUMN {col}")
        except Exception:
            pass

    # Unique index enforcement and composite performance indexes (Phase 9)
    for idx_sql in [
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_diagnoses_client_uuid ON diagnoses(client_uuid)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_farm_activities_client_uuid ON farm_activities(client_uuid)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_crops_client_uuid ON crops(client_uuid)",
        "CREATE INDEX IF NOT EXISTS idx_crops_farm_id ON crops(farm_id)",
        "CREATE INDEX IF NOT EXISTS idx_diagnoses_user_created ON diagnoses(user_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_diagnoses_crop_id ON diagnoses(crop_id)",
        "CREATE INDEX IF NOT EXISTS idx_farm_activities_farm_date ON farm_activities(farm_id, activity_date DESC)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_community_posts_flagged_crop ON community_posts(is_flagged, crop_tag, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_community_posts_user ON community_posts(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_community_comments_post ON community_comments(post_id, is_verified_expert_answer DESC)",
        "CREATE INDEX IF NOT EXISTS idx_products_category_instock ON products(category, is_in_stock, price_inr)",
        "CREATE INDEX IF NOT EXISTS idx_products_retailer ON products(retailer_id, is_in_stock)",
        "CREATE INDEX IF NOT EXISTS idx_retailer_inquiries_retailer ON retailer_inquiries(retailer_id, status, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_retailer_inquiries_user ON retailer_inquiries(user_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_satellite_ndvi_farm_date ON satellite_ndvi_history(farm_id, pass_date DESC)",
        "CREATE INDEX IF NOT EXISTS idx_outbreak_reports_location ON outbreak_reports(crop_name, report_date DESC)"
    ]:
        try:
            conn.execute(idx_sql)
        except Exception:
            pass

    # Migration checks for Phase 6: Precision GIS & Satellite Integration
    for col in [
        "boundary_geojson TEXT",
        "latitude REAL DEFAULT 13.2984",
        "longitude REAL DEFAULT 77.5458",
        "location_consent INTEGER DEFAULT 1",
        "calculated_area_ha REAL DEFAULT 1.416"
    ]:
        try:
            conn.execute(f"ALTER TABLE farms ADD COLUMN {col}")
        except Exception:
            pass

    try:
        conn.execute("ALTER TABLE crops ADD COLUMN expected_harvest_date DATE")
    except Exception:
        pass

    # Create Phase 6 Tables
    conn.execute("""
        CREATE TABLE IF NOT EXISTS outbreak_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            district TEXT NOT NULL,
            taluk TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            crop_name TEXT NOT NULL,
            disease_name TEXT NOT NULL,
            severity TEXT NOT NULL, -- Low, Moderate, High, Epidemic
            case_count INTEGER DEFAULT 1,
            report_date DATE DEFAULT CURRENT_DATE
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS satellite_ndvi_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farm_id INTEGER NOT NULL,
            pass_date DATE NOT NULL,
            satellite_source TEXT DEFAULT 'Sentinel-2 L2A',
            mean_ndvi REAL NOT NULL,
            min_ndvi REAL NOT NULL,
            max_ndvi REAL NOT NULL,
            cloud_cover_percent REAL DEFAULT 8.2,
            stress_area_percent REAL DEFAULT 12.0,
            stress_alert_status TEXT DEFAULT 'Normal Canopy Vigor',
            FOREIGN KEY(farm_id) REFERENCES farms(id) ON DELETE CASCADE
        )
    """)

    # Migration checks for Phase 7: Community, Expert Network & Moderation
    for col in [
        "is_expert INTEGER DEFAULT 0",
        "expert_title TEXT",
        "expert_organization TEXT",
        "expert_badge TEXT",
        "farming_interests TEXT",
        "crop_specialization TEXT"
    ]:
        try:
            conn.execute(f"ALTER TABLE users ADD COLUMN {col}")
        except Exception:
            pass

    for col in [
        "topic_tag TEXT DEFAULT 'General'",
        "is_flagged INTEGER DEFAULT 0",
        "bookmarks_count INTEGER DEFAULT 0"
    ]:
        try:
            conn.execute(f"ALTER TABLE community_posts ADD COLUMN {col}")
        except Exception:
            pass

    for col in [
        "user_id INTEGER",
        "parent_comment_id INTEGER",
        "is_verified_expert_answer INTEGER DEFAULT 0",
        "likes_count INTEGER DEFAULT 0"
    ]:
        try:
            conn.execute(f"ALTER TABLE community_comments ADD COLUMN {col}")
        except Exception:
            pass

    # Phase 7 New Tables
    conn.execute("""
        CREATE TABLE IF NOT EXISTS post_likes (
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, post_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS post_bookmarks (
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, post_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_follows (
            follower_id INTEGER NOT NULL,
            following_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (follower_id, following_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS expert_review_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            diagnosis_id INTEGER,
            image_path TEXT NOT NULL,
            crop_name TEXT NOT NULL,
            symptoms_description TEXT NOT NULL,
            status TEXT DEFAULT 'pending', -- pending, assigned, reviewed
            assigned_expert_id INTEGER,
            expert_diagnosis TEXT,
            expert_recommendation TEXT,
            reviewed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS content_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_user_id INTEGER NOT NULL,
            target_type TEXT NOT NULL, -- post, comment
            target_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            details TEXT,
            status TEXT DEFAULT 'pending', -- pending, action_taken, dismissed
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 8: Marketplace, Retailers & B2B Enterprise Integration
    for col in [
        "license_number TEXT DEFAULT 'KA-BLR-AGR-2023-8841'",
        "operating_hours TEXT DEFAULT '08:30 AM - 08:00 PM'",
        "latitude REAL DEFAULT 13.2984",
        "longitude REAL DEFAULT 77.5458",
        "whatsapp_number TEXT DEFAULT '+919448023456'",
        "delivery_available INTEGER DEFAULT 1",
        "is_verified_retailer INTEGER DEFAULT 1",
        "verification_badge TEXT DEFAULT 'Verified Agri-Dealer (Dept of Agriculture)'",
        "total_orders_fulfilled INTEGER DEFAULT 45"
    ]:
        try:
            conn.execute(f"ALTER TABLE retailers ADD COLUMN {col}")
        except Exception:
            pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            retailer_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL, -- Seeds, Fertilizers, Crop Protection, Organic Inputs, Farming Equipment, Irrigation
            subcategory TEXT,
            brand TEXT NOT NULL,
            active_ingredient TEXT,
            cibrc_registration_no TEXT,
            description TEXT NOT NULL,
            dosage_guidance TEXT,
            package_size TEXT NOT NULL,
            price_inr REAL NOT NULL,
            mrp_inr REAL,
            stock_quantity INTEGER DEFAULT 25,
            is_in_stock INTEGER DEFAULT 1,
            is_sponsored INTEGER DEFAULT 0,
            sponsored_label TEXT,
            image_url TEXT,
            target_crops TEXT,
            target_diseases TEXT,
            non_commercial_alternative TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(retailer_id) REFERENCES retailers(id) ON DELETE CASCADE
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS retailer_inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            retailer_id INTEGER NOT NULL,
            product_id INTEGER,
            inquiry_type TEXT DEFAULT 'stock_check', -- stock_check, price_quote, bulk_order, agronomic_advice
            message TEXT NOT NULL,
            quantity_requested TEXT,
            farmer_phone TEXT NOT NULL,
            status TEXT DEFAULT 'pending', -- pending, contacted, fulfilled, cancelled
            retailer_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(retailer_id) REFERENCES retailers(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            retailer_id INTEGER,
            client_name TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            rate_limit_per_minute INTEGER DEFAULT 60,
            total_calls INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(retailer_id) REFERENCES retailers(id) ON DELETE SET NULL
        )
    """)

    for col in [
        "growth_stage TEXT DEFAULT 'Basal'",
        "area_unit TEXT DEFAULT 'Acres'",
        "calculation_explanation TEXT",
        "estimated_cost_inr INTEGER"
    ]:
        try:
            conn.execute(f"ALTER TABLE fertilizer_plans ADD COLUMN {col}")
        except Exception:
            pass

    # Ensure expert user and user profile specialization are seeded
    expert_user = conn.execute("SELECT id FROM users WHERE username = 'dr_rajesh_agronomist'").fetchone()
    if not expert_user:
        pwd_hash = generate_password_hash("expert123")
        conn.execute(
            """INSERT INTO users 
               (username, email, password_hash, full_name, phone, village, state, preferred_language,
                is_expert, expert_title, expert_organization, expert_badge, farming_interests, crop_specialization)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?)""",
            (
                'dr_rajesh_agronomist',
                'dr.rajesh@kvk-uas.ac.in',
                pwd_hash,
                'Dr. Rajesh K. Gowda, Ph.D.',
                '+91 80 2333 0153',
                'UAS GKVK Campus, Bengaluru',
                'Karnataka',
                'kn',
                'Senior Extension Plant Pathologist',
                'Krishi Vigyan Kendra (KVK) / UAS Bangalore',
                'Verified ICAR Agronomist',
                'Epidemiology, Fungicide Resistance (FRAC), Organic Bio-inputs',
                'Solanaceous Vegetables, Chili, Tomato'
            )
        )
        conn.commit()

    conn.execute(
        """UPDATE users SET 
           farming_interests = 'Precision Drip Fertigation, Integrated Pest Management, Tomato Grafting',
           crop_specialization = 'Tomato (Arka Rakshak), Potato (Kufri Jyoti)'
           WHERE username = 'farmer_punith'"""
    )
    conn.commit()

    user = conn.execute("SELECT id FROM users WHERE username = 'farmer_punith'").fetchone()
    if not user:
        pwd_hash = generate_password_hash("farmer123")
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO users (username, email, password_hash, full_name, phone, village, state, preferred_language)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ('farmer_punith', 'punith@agrivision.ai', pwd_hash, 'Punith S.', '+91 98450 12345', 'Doddaballapur', 'Karnataka', 'en')
        )
        user_id = cur.lastrowid
        
        # Add primary & secondary farms
        cur.execute(
            """INSERT INTO farms (user_id, farm_name, acreage, soil_type, irrigation_type, location)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, 'Green Valley Organic Plot', 3.5, 'Red Sandy Loam', 'Drip System (Precision)', 'Doddaballapur, Bengaluru Rural')
        )
        farm_id_1 = cur.lastrowid

        cur.execute(
            """INSERT INTO farms (user_id, farm_name, acreage, soil_type, irrigation_type, location)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, 'Shantinagar Horticultural Block', 2.0, 'Clay Loam', 'Borewell Micro-Sprinklers', 'Hoskote, Bengaluru Rural')
        )
        farm_id_2 = cur.lastrowid
        
        # Add sample crops
        cur.execute(
            """INSERT INTO crops (farm_id, crop_name, variety, sowing_date, stage, health_status, area_acres, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (farm_id_1, 'Tomato', 'Arka Rakshak (F1)', '2026-09-15', 'Flowering & Fruiting', 'Healthy', 1.5, 'Regular drip fertigation applied. Good canopy vigor.')
        )
        crop_id_1 = cur.lastrowid

        cur.execute(
            """INSERT INTO crops (farm_id, crop_name, variety, sowing_date, stage, health_status, area_acres, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (farm_id_1, 'Potato', 'Kufri Jyoti', '2026-10-01', 'Vegetative Growth', 'Attention Needed', 1.0, 'Early signs of leaf spot observed on bottom foliage.')
        )

        cur.execute(
            """INSERT INTO crops (farm_id, crop_name, variety, sowing_date, stage, health_status, area_acres, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (farm_id_2, 'Chili', 'Byadagi', '2026-08-20', 'Harvesting', 'Healthy', 1.0, 'Second picking cycle in progress.')
        )

        # Seed Farm Activities
        activities = [
            (farm_id_1, crop_id_1, 'Spraying', '2026-10-25', 'Prophylactic spray of Neem Oil 10,000 ppm against whiteflies', '2 ml / Liter water'),
            (farm_id_1, crop_id_1, 'Fertigation', '2026-10-28', 'Injected water soluble NPK 19-19-19 through drip venturi', '3 kg / acre'),
            (farm_id_1, None, 'Weeding', '2026-11-01', 'Manual inter-row weeding and mulching adjustment', 'Manual labor 4 hrs')
        ]
        for fid, cid, atype, adate, desc, qty in activities:
            cur.execute(
                """INSERT INTO farm_activities (farm_id, crop_id, activity_type, activity_date, description, quantity_used)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (fid, cid, atype, adate, desc, qty)
            )

        # Seed Notifications
        notifications = [
            (user_id, 'High Humidity Warning', 'weather_warning', 'danger', 'Relative humidity > 85% with night fog. Monitor Tomato for Late Blight signs.', '#weather'),
            (user_id, 'Diagnosis Follow-up Due', 'diagnosis_followup', 'warning', 'Re-check Potato plot (Kufri Jyoti) for lesion margin drying after Mancozeb spray.', '#diagnose'),
            (user_id, 'Fertigation Schedule Due', 'farm_reminder', 'info', 'Stage 2 Top-dressing scheduled for Tomato plot within the next 48 hours.', '#calculator'),
            (user_id, 'Regional Outbreak Notice', 'outbreak_alert', 'danger', 'Fall Armyworm trap counts rising in Doddaballapur & Devanahalli taluks.', '#community')
        ]
        for uid, title, cat, sev, msg, link in notifications:
            cur.execute(
                """INSERT INTO notifications (user_id, title, category, severity, message, action_link)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (uid, title, cat, sev, msg, link)
            )

        # Seed Chat Session
        cur.execute(
            """INSERT INTO chat_sessions (user_id, title) VALUES (?, ?)""",
            (user_id, 'Agronomic Consultation: Tomato & Chili Management')
        )
        session_id = cur.lastrowid
        cur.execute(
            """INSERT INTO chat_messages (session_id, sender, text, sources_json)
               VALUES (?, ?, ?, ?)""",
            (
                session_id,
                'agronomist',
                "Namaskara! I am your AI Agronomist assistant grounded in ICAR, UAS Bangalore, and TNAU agronomic standards. How can I assist your farm plots today?",
                "[]"
            )
        )
        
        # Seed initial alerts
        alerts_data = [
            ("Tomato Late Blight Advisory", "Pest & Disease", "danger", "High humidity and continuous cloudy weather trigger Late Blight risk in Bengaluru Rural. Prophylactic copper spray advised.", "Bengaluru Rural"),
            ("Rabi Sowing Subsidy Notification", "Government Scheme", "info", "Department of Agriculture opens DBT subsidy window for hybrid seeds and drip kits until Nov 30.", "Karnataka"),
            ("Fall Armyworm Alert in Maize", "Pest & Disease", "warning", "Pheromone trap catches exceeding economic threshold levels in adjacent taluks. Inspect whorls.", "Chikkaballapur")
        ]
        for title, cat, sev, msg, reg in alerts_data:
            cur.execute("INSERT INTO alerts (title, category, severity, message, region) VALUES (?, ?, ?, ?, ?)", (title, cat, sev, msg, reg))
            
        # Seed retailers
        retailers_data = [
            ("Kisan Seva Kendra & Agri Inputs", "Certified Agri-Input Store", "+91 94480 23456", "Main Road, Doddaballapur Market", 2.3, 4.8, "Copper oxychloride, Trichoderma, NPK 19-19-19, Urea, Neem extract"),
            ("Bengaluru Krishi Bio-Products", "Organic & Bio-Agri Specialist", "+91 80 2345 6789", "Yelahanka Old Town, Bengaluru", 6.8, 4.9, "Pseudomonas fluorescens, Bio-NPK consortia, Neem oil 10000 ppm, Sticky traps"),
            ("Raitha Mitra Fertilizer Depot", "Cooperative Fertilizer Society", "+91 94812 34567", "APMC Yard, Devanahalli", 8.1, 4.6, "Urea, DAP, MOP, Zinc sulphate, Borax, Knapsack sprayers")
        ]
        for name, stype, ph, addr, dist, rat, prods in retailers_data:
            cur.execute("INSERT INTO retailers (name, shop_type, phone, address, distance_km, rating, products_available) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (name, stype, ph, addr, dist, rat, prods))
            
        # Seed community posts
        community_data = [
            (user_id, "Punith S.", "Doddaballapur", "Excellent yield using drip-applied Trichoderma in Tomato", 
             "We tried soil drenching with Trichoderma viride 2 weeks after transplanting Arka Rakshak tomatoes. Root rot is completely absent compared to last season!", 
             "Tomato", 18, 4),
            (user_id, "Manjunath Gowda", "Hoskote", "Is this Yellow Leaf Curl or Micronutrient deficiency?", 
             "Noticed upward curling on tender chili leaves with slight vein clearing. What spray gives immediate recovery?", 
             "Chili", 9, 7)
        ]
        for uid, aname, avill, title, content, ctag, likes, comms in community_data:
            cur.execute("INSERT INTO community_posts (user_id, author_name, author_village, title, content, crop_tag, likes_count, comments_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (uid, aname, avill, title, content, ctag, likes, comms))
            
        conn.commit()

    # Phase 8: Ensure seed products and enterprise API key exist
    prod_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if prod_count == 0:
        ret_1 = conn.execute("SELECT id FROM retailers WHERE name LIKE '%Kisan Seva%' LIMIT 1").fetchone()
        ret_2 = conn.execute("SELECT id FROM retailers WHERE name LIKE '%Bengaluru Krishi%' LIMIT 1").fetchone()
        ret_3 = conn.execute("SELECT id FROM retailers WHERE name LIKE '%Raitha Mitra%' LIMIT 1").fetchone()

        r1_id = ret_1[0] if ret_1 else 1
        r2_id = ret_2[0] if ret_2 else 2
        r3_id = ret_3[0] if ret_3 else 3

        seed_products = [
            (r1_id, "Tata Rallis Contaf Plus", "Crop Protection", "Fungicide", "Tata Rallis",
             "Hexaconazole 5% SC", "CIR-18234/2019-Hexaconazole(SC)-312",
             "Systemic triazole fungicide with protective and curative action against powdery mildew and early blight.",
             "2 ml / liter water", "500 ml", 480.0, 550.0, 35, 1, 0, None,
             "/static/img/products/contaf_plus.jpg", "Tomato, Chili, Potato, Grape", "Early Blight, Powdery Mildew, Leaf Spot",
             "5% Neem Seed Kernel Extract (NSKE) or fermented sour buttermilk foliar spray"),

            (r1_id, "Bayer Nativo 75 WG", "Crop Protection", "Fungicide", "Bayer CropScience",
             "Tebuconazole 50% + Trifloxystrobin 25% WG", "CIR-11928/2012-Tebuconazole+Trifloxystrobin-41",
             "Dual active broad-spectrum fungicide with mesostemic and systemic activity providing long-duration control.",
             "0.7 g / liter water (follow 15-day PHI)", "100 g", 920.0, 990.0, 20, 1, 1, "Sponsored Partner Listing",
             "/static/img/products/nativo.jpg", "Tomato, Chili, Rice", "Early Blight, Anthracnose, Sheath Blight",
             "Trichoderma viride 1% WP foliar spray with fermented bio-extract"),

            (r3_id, "Syngenta Ridomil Gold", "Crop Protection", "Fungicide", "Syngenta",
             "Metalaxyl-M 4% + Mancozeb 64% WP", "CIR-6214/2006-Metalaxyl-M-88",
             "Specialized systemic and contact fungicide for controlling Late Blight and Downy Mildew.",
             "2.5 g / liter water", "500 g", 540.0, 610.0, 28, 1, 0, None,
             "/static/img/products/ridomil.jpg", "Potato, Tomato, Grapes", "Late Blight, Downy Mildew, Damping Off",
             "1% Bordeaux Mixture (Copper sulphate + Slaked lime) or Copper soap spray"),

            (r2_id, "Multiplex Samras Bio-Nutrient", "Organic Inputs", "Bio-stimulant", "Multiplex Bio-Tech",
             "Amino Acids (12%) + Fulvic acid organic complex", "FCO Karnataka Approved 2021",
             "Organic liquid bio-stimulant promoting vegetative vigor, chlorophyll density, and floral retention.",
             "2 to 3 ml / liter water", "500 ml", 380.0, 420.0, 45, 1, 0, None,
             "/static/img/products/samras.jpg", "Tomato, Chili, Potato, Onion, Flowers", "Micronutrient Deficiency, Abiotic Stress",
             "Homemade Jeevamrutha or Panchagavya solution (3% foliar spray)"),

            (r2_id, "Arka Trichoderma viride 1.5% WP", "Organic Inputs", "Bio-fungicide", "ICAR - IIHR Bengaluru",
             "Trichoderma viride strain IIHR-Tv-1 (CFU 2x10^8 / g)", "CIBRC Bio-Fungicide Reg. 2017",
             "Govt certified biological agent against soil-borne root rot, collar rot, and fusarium wilt.",
             "5 g / liter water for root drenching, 2.5 kg / acre with FYM", "1 kg", 160.0, 190.0, 60, 1, 0, None,
             "/static/img/products/trichoderma.jpg", "Tomato, Chili, Potato, Ginger, Banana", "Root Rot, Collar Rot, Fusarium Wilt, Damping Off",
             "Composted farmyard manure enriched with native forest soil antagonistic fungi"),

            (r1_id, "Kisan Bio Neem 10000 PPM", "Organic Inputs", "Bio-insecticide", "Kisan Bio-Products",
             "Azadirachtin 1% (10,000 ppm) EC", "CIBRC Reg. CIR-33912/2018-Azadirachtin-101",
             "Botanical insecticide disrupting feeding, egg-laying, and molting of sucking pests.",
             "2 ml / liter water with 0.5 ml sticker", "1 Liter", 450.0, 520.0, 40, 1, 0, None,
             "/static/img/products/neem_oil.jpg", "Chili, Tomato, Cotton, Brinjal", "Thrips, Whiteflies, Aphids, Leafminer",
             "Freshly prepared 5% Neem Seed Kernel Extract (NSKE) or Agniastra formulation"),

            (r3_id, "IFFCO Drip Grade NPK 19-19-19", "Fertilizers", "Water Soluble NPK", "IFFCO",
             "Total Nitrogen 19%, Available P2O5 19%, Soluble K2O 19%", "FCO 1985 Schedule I",
             "100% water-soluble fertigation fertilizer for balanced vegetative flush and root vigor.",
             "3 to 5 kg / acre through drip fertigation", "1 kg Bag", 195.0, 225.0, 80, 1, 0, None,
             "/static/img/products/npk_191919.jpg", "All field crops and vegetables", "Nutrient Deficiency, Stunted Growth",
             "Well-composted vermicompost tea or fermented oilcake liquid manure"),

            (r1_id, "Mahadhan Calci-Boron Drip Grade", "Fertilizers", "Secondary & Micronutrient", "Mahadhan",
             "Nitrate Nitrogen 15.5%, Calcium 18.8%, Boron 0.2%", "FCO F-1204/2019",
             "Prevents blossom end rot in tomato and fruit cracking in pomegranate and vegetables.",
             "3 to 4 kg / acre via drip or 5 g / liter foliar", "1 kg", 280.0, 320.0, 30, 1, 0, None,
             "/static/img/products/calci_bor.jpg", "Tomato, Chili, Pomegranate, Melon", "Blossom End Rot, Fruit Cracking, Calcium Deficiency",
             "Crushed eggshell steeped in natural vinegar for bio-available calcium acetate"),

            (r1_id, "Arka Rakshak F1 Hybrid Tomato Seeds", "Seeds", "Vegetable Seeds", "ICAR - IIHR Bengaluru",
             "Solanum lycopersicum L. Hybrid", "National Seed Certification No. 2020/BLR/88",
             "High yielding triple-disease resistant hybrid: Resistant to ToLCV, Early Blight, and Bacterial Wilt.",
             "50 to 60 g seeds / acre for nursery raising", "10 g Pack (approx 3,000 seeds)", 450.0, 500.0, 50, 1, 0, None,
             "/static/img/products/arka_rakshak.jpg", "Tomato", "ToLCV, Early Blight, Bacterial Wilt",
             "Farmer-saved heirloom seeds treated with Trichoderma bio-priming"),

            (r3_id, "Syngenta Sitara Chili F1", "Seeds", "Vegetable Seeds", "Syngenta Seeds",
             "Capsicum annuum L. Hybrid", "ISTA Certified Lot 2024",
             "Prolific bearer with uniform dark green fruits, high pungency, and strong tolerance to leaf curl virus.",
             "70 to 80 g seeds / acre", "10 g Pack", 680.0, 750.0, 25, 1, 0, None,
             "/static/img/products/sitara.jpg", "Chili", "Chili Leaf Curl Virus, Anthracnose",
             "Local Byadgi / Guntur seed selection with ash and cow urine seed treatment"),

            (r1_id, "Neptune 16L Dual-Motor Battery Sprayer", "Farming Equipment", "Sprayers", "Neptune Agro",
             "12V / 12Ah Lead-acid battery with dual micro-diaphragm pump", "ISI Certified IS:11313",
             "Ergonomic knapsack sprayer delivering 4.5 L/min with extendable telescopic brass lance.",
             "Full charge covers 25 to 30 tanks (approx 2 acres)", "1 Unit with 4 Nozzle set", 2850.0, 3400.0, 15, 1, 0, None,
             "/static/img/products/sprayer.jpg", "All field crops", "Spray equipment",
             "Manual lever knapsack sprayer or cooperative custom hiring center equipment"),

            (r3_id, "Jain 16mm Hydrogol Inline Drip Pipe", "Irrigation Supplies", "Drip Laterals", "Jain Irrigation Systems",
             "Virgin grade LDPE, Class 2, 2.0 LPH dripper discharge at 40cm spacing", "BIS License CM/L-7200142385",
             "Clog-resistant labyrinth drippers designed for high-uniformity vegetable and horticultural cultivation.",
             "Spaced at 40cm along rows", "400 Meter Bundle", 3400.0, 3900.0, 12, 1, 0, None,
             "/static/img/products/drip_lateral.jpg", "Vegetables, Orchards, Sugarcane", "Water stress, Drought mitigation",
             "Traditional furrow or ridge irrigation with organic straw conservation mulching")
        ]

        for p in seed_products:
            conn.execute(
                """INSERT INTO products 
                   (retailer_id, name, category, subcategory, brand, active_ingredient, cibrc_registration_no,
                    description, dosage_guidance, package_size, price_inr, mrp_inr, stock_quantity, is_in_stock,
                    is_sponsored, sponsored_label, image_url, target_crops, target_diseases, non_commercial_alternative)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                p
            )
        conn.commit()

    # Seed Default Enterprise B2B API Key
    api_key_entry = conn.execute("SELECT id FROM api_keys WHERE client_name = 'AgriCorp Enterprise Dist'").fetchone()
    if not api_key_entry:
        conn.execute(
            """INSERT INTO api_keys (retailer_id, client_name, api_key, rate_limit_per_minute, total_calls)
               VALUES (1, 'AgriCorp Enterprise Dist', 'b2b_kisan_enterprise_key_2026', 120, 0)"""
        )
        conn.commit()

    conn.close()
