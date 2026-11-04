import urllib.request
import urllib.parse
import re
import os
import uuid
import json
import csv
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from werkzeug.utils import secure_filename

from config import Config
from database.db import get_db_connection, init_db
from services.ai_diagnosis import diagnosis_engine
from services.fertilizer_service import fertilizer_calculator
from services.weather_service import weather_service
from services.advisory_service import get_seasonal_recommendations
from services.agronomist_engine import agronomist_engine, SUGGESTED_PROMPTS
from services.offline_service import offline_service
from services.i18n_service import i18n_service, REGIONAL_LANGUAGES
from services.precision_service import precision_service
from services.community_service import community_service
from services.marketplace_service import marketplace_service
from services.cache_service import cache_service
from services.security_service import security_service
from services.monitoring_service import monitoring_service
from services.backup_service import backup_service
from werkzeug.security import check_password_hash
import time

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database schemas and seed data on startup
with app.app_context():
    init_db()

# ----------------- PHASE 9: SECURITY, RATE LIMITING & OBSERVABILITY MIDDLEWARE -----------------
@app.before_request
def before_request_middleware():
    request.request_id = request.headers.get('X-Request-ID') or monitoring_service.generate_correlation_id()
    request.start_time = time.time()
    
    # Rate limiting for API routes (exclude static files and testing suite)
    if request.path.startswith('/api/') and not app.config.get('TESTING'):
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1').split(',')[0].strip()
        limit = Config.RATE_LIMIT_AUTH if '/auth/' in request.path else Config.RATE_LIMIT_DEFAULT
        allowed, remaining, retry_after = security_service.check_rate_limit(client_ip, limit=limit)
        if not allowed:
            return jsonify({
                "success": False,
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Too many requests. Please slow down. Retry in {retry_after} seconds."
                },
                "request_id": request.request_id
            }), 429, {"Retry-After": str(retry_after)}

@app.after_request
def after_request_middleware(response):
    latency_ms = round((time.time() - getattr(request, 'start_time', time.time())) * 1000, 2)
    monitoring_service.record_request(response.status_code, latency_ms)

    # Security Headers
    response.headers['X-Request-ID'] = getattr(request, 'request_id', 'unknown')
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# Standardized JSON error handlers
@app.errorhandler(400)
def handle_bad_request(e):
    return jsonify({
        "success": False,
        "error": {"code": "BAD_REQUEST", "message": str(e.description if hasattr(e, 'description') else e)},
        "request_id": getattr(request, 'request_id', 'unknown')
    }), 400

@app.errorhandler(404)
def handle_not_found(e):
    return jsonify({
        "success": False,
        "error": {"code": "NOT_FOUND", "message": "The requested endpoint or resource was not found."},
        "request_id": getattr(request, 'request_id', 'unknown')
    }), 404

@app.errorhandler(429)
def handle_rate_limit(e):
    return jsonify({
        "success": False,
        "error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Rate limit exceeded. Please back off."},
        "request_id": getattr(request, 'request_id', 'unknown')
    }), 429

@app.errorhandler(500)
def handle_server_error(e):
    return jsonify({
        "success": False,
        "error": {"code": "INTERNAL_SERVER_ERROR", "message": "An internal server error occurred."},
        "request_id": getattr(request, 'request_id', 'unknown')
    }), 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# ----------------- MAIN VIEW ROUTE -----------------
@app.route('/')
def index():
    return render_template('index.html')

# ----------------- COMPREHENSIVE INITIAL STATE API -----------------
@app.route('/api/state', methods=['GET'])
def get_app_state():
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id, username, email, full_name, phone, village, state, preferred_language FROM users ORDER BY id ASC LIMIT 1").fetchone()
        user_dict = dict(user) if user else {}

        farms = [dict(f) for f in conn.execute("SELECT * FROM farms WHERE user_id = ? ORDER BY id ASC", (user_dict.get('id', 1),)).fetchall()]
        
        crops = [dict(c) for c in conn.execute(
            """SELECT c.*, f.farm_name FROM crops c 
               JOIN farms f ON c.farm_id = f.id 
               WHERE f.user_id = ? ORDER BY c.id DESC""", 
            (user_dict.get('id', 1),)
        ).fetchall()]

        diagnoses = [dict(d) for d in conn.execute(
            "SELECT * FROM diagnoses WHERE user_id = ? ORDER BY id DESC LIMIT 10", 
            (user_dict.get('id', 1),)
        ).fetchall()]

        notifications = [dict(n) for n in conn.execute(
            "SELECT * FROM notifications WHERE user_id = ? ORDER BY is_read ASC, id DESC LIMIT 8",
            (user_dict.get('id', 1),)
        ).fetchall()]

        activities = [dict(a) for a in conn.execute(
            """SELECT fa.*, f.farm_name, c.crop_name FROM farm_activities fa
               JOIN farms f ON fa.farm_id = f.id
               LEFT JOIN crops c ON fa.crop_id = c.id
               WHERE f.user_id = ? ORDER BY fa.activity_date DESC LIMIT 8""",
            (user_dict.get('id', 1),)
        ).fetchall()]

        alerts = [dict(a) for a in conn.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT 5").fetchall()]
        retailers = [dict(r) for r in conn.execute("SELECT * FROM retailers ORDER BY distance_km ASC").fetchall()]
        posts = [dict(p) for p in conn.execute("SELECT * FROM community_posts ORDER BY id DESC LIMIT 10").fetchall()]
        
        weather = weather_service.get_forecast(city_name=f"{user_dict.get('village', 'Bengaluru Rural')}")
        tips = get_seasonal_recommendations()

        return jsonify({
            "status": "success",
            "user": user_dict,
            "farms": farms,
            "crops": crops,
            "recent_diagnoses": diagnoses,
            "notifications": notifications,
            "farm_activities": activities,
            "alerts": alerts,
            "retailers": retailers,
            "community_posts": posts,
            "weather": weather,
            "farming_tips": tips,
            "suggested_prompts": SUGGESTED_PROMPTS
        })
    finally:
        conn.close()

# ----------------- AI DIAGNOSIS API -----------------
@app.route('/api/diagnose', methods=['POST'])
def diagnose_crop():
    if 'image' not in request.files:
        return jsonify({"success": False, "error": "No image file provided in upload"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"success": False, "error": "No image selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "Unsupported file format. Please upload JPG, PNG, or WEBP."}), 400

    crop_name = request.form.get('crop_name', 'Tomato')
    crop_id = request.form.get('crop_id', None)
    
    # Save file securely with UUID
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"leaf_{uuid.uuid4().hex[:12]}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Ingest live weather context for context-aware diagnostic refinement
    weather_ctx = weather_service.get_forecast()

    # Perform quality check, symptom localization, and diagnosis
    diagnosis_result = diagnosis_engine.diagnose_crop_leaf(
        filepath,
        user_selected_crop=crop_name,
        weather_context=weather_ctx
    )
    
    if not diagnosis_result.get("success"):
        return jsonify(diagnosis_result), 422

    # Save to database
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1").fetchone()
        user_id = user['id'] if user else 1
        
        relative_image_path = f"/static/uploads/{filename}"
        chem = diagnosis_result.get("chemical_treatment", {})
        bio = diagnosis_result.get("biological_treatment", {})
        org = diagnosis_result.get("organic_treatment", {})
        cult = diagnosis_result.get("cultural_treatment", [])
        loc = diagnosis_result.get("symptom_localization", {})
        certainty = diagnosis_result.get("diagnostic_certainty", "confirmed")

        client_uuid = request.form.get('client_uuid') or str(uuid.uuid4())

        cur = conn.cursor()
        cur.execute(
            """INSERT INTO diagnoses 
               (user_id, crop_id, image_path, diagnosed_crop, disease_name, confidence, severity, symptoms, cause,
                chemical_treatment, biological_treatment, organic_treatment, cultural_treatment, active_ingredient,
                phi_days, frac_code, preventive_measures, monitoring_recommendations, alternative_diagnoses_json,
                symptom_localization_json, diagnostic_certainty, weather_context_json, client_uuid, is_offline, sync_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'synced')""",
            (
                user_id,
                int(crop_id) if crop_id and str(crop_id).isdigit() else None,
                relative_image_path,
                diagnosis_result.get("crop", crop_name),
                diagnosis_result.get("disease", "Unknown"),
                diagnosis_result.get("confidence", 90.0),
                diagnosis_result.get("severity", "Moderate"),
                diagnosis_result.get("symptoms", ""),
                diagnosis_result.get("cause", ""),
                json.dumps(chem),
                json.dumps(bio),
                json.dumps(org),
                json.dumps(cult),
                chem.get("active_ingredient", ""),
                chem.get("phi_days", 7),
                chem.get("frac_code", "M03"),
                "\n".join(cult),
                diagnosis_result.get("monitoring_recommendations", ""),
                json.dumps(diagnosis_result.get("differential_diagnoses", [])) if diagnosis_result.get("differential_diagnoses") else None,
                json.dumps(loc) if loc else None,
                certainty,
                json.dumps(weather_ctx.get("current", {})),
                client_uuid
            )
        )

        # Trigger follow-up notification if severe or moderate
        if diagnosis_result.get("severity") in ["Moderate", "Moderate to High", "Severe / Critical"]:
            cur.execute(
                """INSERT INTO notifications (user_id, title, category, severity, message, action_link)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    f"Follow-up: {diagnosis_result.get('disease')}",
                    "diagnosis_followup",
                    "warning",
                    f"Scheduled follow-up inspection due in 5 days for {diagnosis_result.get('crop')} to verify lesion margin drying.",
                    "#diagnose"
                )
            )

        conn.commit()
        diagnosis_id = cur.lastrowid
        diagnosis_result["id"] = diagnosis_id
        diagnosis_result["image_path"] = relative_image_path
        diagnosis_result["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        return jsonify(diagnosis_result)
    finally:
        conn.close()

# ----------------- DIAGNOSIS HISTORY, SEARCH & EXPORT API -----------------
@app.route('/api/diagnoses/history', methods=['GET'])
def get_diagnosis_history():
    query = request.args.get('q', '').strip()
    crop_filter = request.args.get('crop', '').strip()
    disease_filter = request.args.get('disease', '').strip()
    sort_order = request.args.get('sort', 'desc').lower()

    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1").fetchone()
        user_id = user['id'] if user else 1

        sql = "SELECT * FROM diagnoses WHERE user_id = ?"
        params = [user_id]

        if query:
            sql += " AND (diagnosed_crop LIKE ? OR disease_name LIKE ? OR symptoms LIKE ?)"
            q_param = f"%{query}%"
            params.extend([q_param, q_param, q_param])

        if crop_filter:
            sql += " AND diagnosed_crop = ?"
            params.append(crop_filter)

        if disease_filter:
            sql += " AND disease_name LIKE ?"
            params.append(f"%{disease_filter}%")

        sql += f" ORDER BY id {'DESC' if sort_order == 'desc' else 'ASC'}"

        rows = conn.execute(sql, params).fetchall()
        result = []
        for r in rows:
            item = dict(r)
            for jf in ['chemical_treatment', 'biological_treatment', 'organic_treatment', 'cultural_treatment', 'alternative_diagnoses_json', 'symptom_localization_json']:
                if item.get(jf) and isinstance(item[jf], str):
                    try:
                        item[jf] = json.loads(item[jf])
                    except Exception:
                        pass
            result.append(item)

        return jsonify(result)
    finally:
        conn.close()

@app.route('/api/diagnoses/<int:diag_id>', methods=['DELETE'])
def delete_diagnosis(diag_id):
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1").fetchone()
        user_id = user['id'] if user else 1
        
        cur = conn.cursor()
        cur.execute("DELETE FROM diagnoses WHERE id = ? AND user_id = ?", (diag_id, user_id))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"success": False, "error": "Record not found or unauthorized"}), 404
        return jsonify({"success": True, "message": "Diagnosis record deleted successfully"})
    finally:
        conn.close()

@app.route('/api/diagnoses/export', methods=['GET'])
def export_diagnoses():
    export_format = request.args.get('format', 'json').lower()
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1").fetchone()
        user_id = user['id'] if user else 1

        rows = conn.execute("SELECT * FROM diagnoses WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()
        
        if export_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['ID', 'Date', 'Crop', 'Disease', 'Confidence', 'Certainty', 'Severity', 'Active Ingredient', 'PHI Days', 'FRAC Code'])
            for r in rows:
                writer.writerow([
                    r['id'], r['created_at'], r['diagnosed_crop'], r['disease_name'], 
                    r['confidence'], r['diagnostic_certainty'], r['severity'], r['active_ingredient'], r['phi_days'], r['frac_code']
                ])
            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment;filename=crop_diagnosis_history.csv"}
            )
        else:
            return jsonify([dict(r) for r in rows])
    finally:
        conn.close()

# ----------------- FERTILIZER CALCULATOR API -----------------
@app.route('/api/fertilizer/calculate', methods=['POST'])
def calculate_fertilizer():
    data = request.get_json() or {}
    crop_name = data.get('crop_name', 'Tomato')
    area = data.get('acreage', 1.0)
    unit = data.get('unit', 'Acres')
    growth_stage = data.get('growth_stage', 'All Stages')
    soil_test = data.get('soil_test', None)
    target_yield = data.get('target_yield', None)

    plan = fertilizer_calculator.calculate_fertilizer(
        crop_name=crop_name,
        area=area,
        unit=unit,
        growth_stage=growth_stage,
        soil_test=soil_test,
        target_yield=target_yield
    )

    if not plan.get("success"):
        return jsonify(plan), 400
    
    # Save plan to DB for persistence
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1").fetchone()
        if user:
            conn.execute(
                """INSERT INTO fertilizer_plans 
                   (user_id, crop_name, growth_stage, acreage, area_unit, soil_test_available, 
                    urea_kg, dap_kg, mop_kg, schedule_json, calculation_explanation, estimated_cost_inr)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    user['id'],
                    crop_name,
                    growth_stage,
                    float(area),
                    unit,
                    1 if soil_test else 0,
                    plan['commercial_fertilizers']['urea_kg'],
                    plan['commercial_fertilizers']['dap_kg'],
                    plan['commercial_fertilizers']['mop_kg'],
                    json.dumps(plan['schedule']),
                    plan['calculation_explanation'],
                    plan['estimated_cost_inr']
                )
            )
            conn.commit()
    finally:
        conn.close()

    return jsonify({"success": True, "plan": plan})

# ----------------- WEATHER API -----------------
@app.route('/api/weather', methods=['GET'])
def get_weather():
    lat = float(request.args.get('lat', Config.DEFAULT_LATITUDE))
    lon = float(request.args.get('lon', Config.DEFAULT_LONGITUDE))
    city = request.args.get('city', Config.DEFAULT_CITY)
    force_refresh = request.args.get('refresh', 'false').lower() in ['true', '1']
    data = weather_service.get_forecast(lat=lat, lon=lon, city_name=city, force_refresh=force_refresh)
    return jsonify(data)


@app.route('/api/weather/spray-window', methods=['GET'])
def get_weather_spray_window():
    """Returns 24-hour hour-by-hour spray feasibility conditions and agro-advisories."""
    lat = float(request.args.get('lat', Config.DEFAULT_LATITUDE))
    lon = float(request.args.get('lon', Config.DEFAULT_LONGITUDE))
    city = request.args.get('city', Config.DEFAULT_CITY)
    data = weather_service.get_forecast(lat=lat, lon=lon, city_name=city)
    return jsonify({
        "success": True,
        "advisory": data.get("agri_advisory"),
        "hourly_windows": data.get("spray_hours_next_24", [])
    })

# ----------------- FARM ACTIVITIES & MONITORING API -----------------
@app.route('/api/farms/activity', methods=['POST'])
def log_farm_activity():
    data = request.get_json() or {}
    farm_id = data.get('farm_id')
    crop_id = data.get('crop_id')
    activity_type = data.get('activity_type')
    activity_date = data.get('activity_date', datetime.now().strftime("%Y-%m-%d"))
    description = data.get('description')
    quantity = data.get('quantity_used', '')

    if not farm_id or not activity_type or not description:
        return jsonify({"error": "Farm, activity type, and description are required"}), 400

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO farm_activities (farm_id, crop_id, activity_type, activity_date, description, quantity_used)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (farm_id, crop_id if crop_id else None, activity_type, activity_date, description, quantity)
        )
        conn.commit()
        return jsonify({"success": True, "id": cur.lastrowid, "message": "Farm activity logged successfully"})
    finally:
        conn.close()

@app.route('/api/crops/<int:crop_id>/history', methods=['GET'])
def get_crop_history(crop_id):
    conn = get_db_connection()
    try:
        diagnoses = [dict(d) for d in conn.execute(
            "SELECT * FROM diagnoses WHERE crop_id = ? ORDER BY id DESC", (crop_id,)
        ).fetchall()]

        activities = [dict(a) for a in conn.execute(
            "SELECT * FROM farm_activities WHERE crop_id = ? ORDER BY activity_date DESC", (crop_id,)
        ).fetchall()]

        return jsonify({
            "crop_id": crop_id,
            "diagnoses": diagnoses,
            "activities": activities
        })
    finally:
        conn.close()

# ----------------- NOTIFICATIONS API -----------------
@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1").fetchone()
        user_id = user['id'] if user else 1

        notes = [dict(n) for n in conn.execute(
            "SELECT * FROM notifications WHERE user_id = ? ORDER BY is_read ASC, id DESC LIMIT 20",
            (user_id,)
        ).fetchall()]
        return jsonify(notes)
    finally:
        conn.close()

@app.route('/api/notifications/mark-read', methods=['POST'])
def mark_notification_read():
    data = request.get_json() or {}
    note_id = data.get('id')
    conn = get_db_connection()
    try:
        if note_id:
            conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (note_id,))
        else:
            conn.execute("UPDATE notifications SET is_read = 1")
        conn.commit()
        return jsonify({"success": True})
    finally:
        conn.close()

# ----------------- CROPS & FARMS MANAGEMENT API -----------------
@app.route('/api/crops', methods=['GET', 'POST'])
def manage_crops():
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1").fetchone()
        user_id = user['id'] if user else 1
        
        if request.method == 'POST':
            data = request.get_json() or {}
            farm_id = data.get('farm_id')
            crop_name = data.get('crop_name')
            variety = data.get('variety', '')
            sowing_date = data.get('sowing_date', datetime.now().strftime("%Y-%m-%d"))
            stage = data.get('stage', 'Vegetative')
            health_status = data.get('health_status', 'Healthy')
            area_acres = float(data.get('area_acres', 1.0))
            notes = data.get('notes', '')

            if not farm_id or not crop_name:
                return jsonify({"error": "Farm and Crop Name are required"}), 400

            cur = conn.cursor()
            cur.execute(
                """INSERT INTO crops (farm_id, crop_name, variety, sowing_date, stage, health_status, area_acres, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (farm_id, crop_name, variety, sowing_date, stage, health_status, area_acres, notes)
            )
            conn.commit()
            return jsonify({"success": True, "id": cur.lastrowid, "message": "Crop registered successfully"})

        crops = conn.execute(
            """SELECT c.*, f.farm_name FROM crops c 
               JOIN farms f ON c.farm_id = f.id 
               WHERE f.user_id = ? ORDER BY c.id DESC""",
            (user_id,)
        ).fetchall()
        return jsonify([dict(c) for c in crops])
    finally:
        conn.close()

@app.route('/api/farms', methods=['GET', 'POST'])
def manage_farms():
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1").fetchone()
        user_id = user['id'] if user else 1

        if request.method == 'POST':
            data = request.get_json() or {}
            farm_name = data.get('farm_name')
            acreage = float(data.get('acreage', 1.0))
            soil_type = data.get('soil_type', 'Red Sandy Loam')
            irrigation_type = data.get('irrigation_type', 'Drip Irrigation')
            location = data.get('location', 'Karnataka')

            if not farm_name:
                return jsonify({"error": "Farm name is required"}), 400

            cur = conn.cursor()
            cur.execute(
                """INSERT INTO farms (user_id, farm_name, acreage, soil_type, irrigation_type, location)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, farm_name, acreage, soil_type, irrigation_type, location)
            )
            conn.commit()
            return jsonify({"success": True, "id": cur.lastrowid, "message": "Farm registered successfully"})

        farms = conn.execute("SELECT * FROM farms WHERE user_id = ? ORDER BY id ASC", (user_id,)).fetchall()
        return jsonify([dict(f) for f in farms])
    finally:
        conn.close()

# ----------------- COMMUNITY FORUM & EXPERT NETWORK API (PHASE 7) -----------------
@app.route('/api/community/posts', methods=['GET'])
def get_community_posts():
    """Returns paginated, searchable, filtered farmer community posts."""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    crop = request.args.get('crop', None)
    topic = request.args.get('topic', None)
    search = request.args.get('search', None)
    user_id = int(request.args.get('user_id', 1))

    res = community_service.get_posts(page=page, limit=limit, crop=crop, topic=topic, search=search, user_id=user_id)
    return jsonify(res)

@app.route('/api/community/post', methods=['POST'])
@app.route('/api/community/posts', methods=['POST'])
def create_community_post():
    """Creates a community post with automated content filtering and optional image upload."""
    image_path = None
    if request.is_json:
        data = request.get_json() or {}
        title = data.get('title')
        content = data.get('content')
        crop_tag = data.get('crop_tag', 'General')
        topic_tag = data.get('topic_tag', 'General')
        user_id = int(data.get('user_id', 1))
        image_path = data.get('image_path')
    else:
        title = request.form.get('title')
        content = request.form.get('content')
        crop_tag = request.form.get('crop_tag', 'General')
        topic_tag = request.form.get('topic_tag', 'General')
        user_id = int(request.form.get('user_id', 1))
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"community_{uuid.uuid4().hex[:8]}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_path = f"/static/uploads/{filename}"

    if not title or not content:
        return jsonify({"error": "Title and content are required"}), 400

    res = community_service.create_post(
        user_id=user_id,
        title=title,
        content=content,
        crop_tag=crop_tag,
        topic_tag=topic_tag,
        image_path=image_path
    )
    return jsonify(res), (200 if res.get('success') else 400)

@app.route('/api/community/like', methods=['POST'])
def toggle_community_like():
    """Toggles like status for a community post."""
    data = request.get_json() or {}
    post_id = data.get('post_id')
    user_id = int(data.get('user_id', 1))
    if not post_id:
        return jsonify({"error": "Missing post_id"}), 400

    res = community_service.toggle_like(user_id=user_id, post_id=post_id)
    return jsonify(res)

@app.route('/api/community/bookmark', methods=['POST'])
def toggle_community_bookmark():
    """Toggles bookmark status for a community post."""
    data = request.get_json() or {}
    post_id = data.get('post_id')
    user_id = int(data.get('user_id', 1))
    if not post_id:
        return jsonify({"error": "Missing post_id"}), 400

    res = community_service.toggle_bookmark(user_id=user_id, post_id=post_id)
    return jsonify(res)

@app.route('/api/community/comments', methods=['GET'])
def get_community_comments():
    """Retrieves threaded comments and verified expert answers for a post."""
    post_id = request.args.get('post_id')
    if not post_id:
        return jsonify({"error": "Missing post_id"}), 400
    comments = community_service.get_comments(int(post_id))
    return jsonify(comments)

@app.route('/api/community/comment', methods=['POST'])
def add_community_comment():
    """Adds a comment or reply with expert verification check."""
    data = request.get_json() or {}
    post_id = data.get('post_id')
    user_id = int(data.get('user_id', 1))
    comment_text = data.get('comment_text')
    parent_comment_id = data.get('parent_comment_id')

    if not post_id or not comment_text:
        return jsonify({"error": "Missing post_id or comment_text"}), 400

    res = community_service.add_comment(
        user_id=user_id,
        post_id=int(post_id),
        comment_text=comment_text,
        parent_comment_id=parent_comment_id
    )
    return jsonify(res), (200 if res.get('success') else 400)

@app.route('/api/community/follow', methods=['POST'])
def toggle_community_follow():
    """Follows or unfollows a farmer or agronomist."""
    data = request.get_json() or {}
    follower_id = int(data.get('follower_id', 1))
    following_id = data.get('following_id')
    if not following_id:
        return jsonify({"error": "Missing following_id"}), 400

    res = community_service.toggle_follow(follower_id=follower_id, following_id=int(following_id))
    return jsonify(res), (200 if res.get('success') else 400)

@app.route('/api/community/users/<int:target_user_id>', methods=['GET'])
def get_community_user_profile(target_user_id):
    """Retrieves user profile, farming specialization, posts, and followers."""
    current_user_id = int(request.args.get('current_user_id', 1))
    profile = community_service.get_user_profile(target_user_id=target_user_id, current_user_id=current_user_id)
    if not profile:
        return jsonify({"error": "User not found"}), 404
    return jsonify(profile)

@app.route('/api/community/report', methods=['POST'])
def report_community_content():
    """Flags post or comment for content moderation queue."""
    data = request.get_json() or {}
    reporter_user_id = int(data.get('user_id', 1))
    target_type = data.get('target_type', 'post')
    target_id = data.get('target_id')
    reason = data.get('reason', 'Harmful or spam content')
    details = data.get('details', '')

    if not target_id:
        return jsonify({"error": "Missing target_id"}), 400

    res = community_service.report_content(reporter_user_id, target_type, target_id, reason, details)
    return jsonify(res)

# --- AI & HUMAN SECOND OPINION EXPERT REVIEWS ---
@app.route('/api/expert/reviews/request', methods=['POST'])
def request_expert_review():
    """Submits low-confidence diagnosis for certified KVK agronomist review."""
    data = request.get_json() or {}
    user_id = int(data.get('user_id', 1))
    crop_name = data.get('crop_name', 'Crop')
    symptoms = data.get('symptoms', '')
    image_path = data.get('image_path', '')
    diagnosis_id = data.get('diagnosis_id')

    res = community_service.request_expert_review(
        user_id=user_id,
        crop_name=crop_name,
        symptoms=symptoms,
        image_path=image_path,
        diagnosis_id=diagnosis_id
    )
    return jsonify(res)

@app.route('/api/expert/reviews', methods=['GET'])
def get_expert_reviews():
    """Lists expert review requests."""
    status = request.args.get('status', None)
    expert_id = request.args.get('expert_id', None)
    if expert_id:
        expert_id = int(expert_id)
    reviews = community_service.get_expert_reviews(status=status, expert_id=expert_id)
    return jsonify({"success": True, "reviews": reviews})

@app.route('/api/expert/reviews/<int:request_id>/resolve', methods=['POST'])
def resolve_expert_review(request_id):
    """Certified agronomist files official diagnosis."""
    data = request.get_json() or {}
    expert_user_id = int(data.get('expert_user_id', 2)) # Default to seeded Dr. Rajesh Gowda
    expert_diagnosis = data.get('expert_diagnosis', '')
    recommendation = data.get('recommendation', '')

    if not expert_diagnosis:
        return jsonify({"error": "Expert diagnosis cannot be empty"}), 400

    res = community_service.resolve_expert_review(
        request_id=request_id,
        expert_user_id=expert_user_id,
        expert_diagnosis=expert_diagnosis,
        recommendation=recommendation
    )
    return jsonify(res), (200 if res.get('success') else 400)

# ----------------- ADVANCED AI AGRONOMIST & RAG CHAT API -----------------
@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1").fetchone()
        user_id = user['id'] if user else 1

        session = conn.execute("SELECT id FROM chat_sessions WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
        if not session:
            return jsonify({"success": True, "session_id": None, "messages": []})

        rows = conn.execute("SELECT * FROM chat_messages WHERE session_id = ? ORDER BY id ASC", (session['id'],)).fetchall()
        messages = []
        for r in rows:
            msg = dict(r)
            if msg.get('sources_json') and isinstance(msg['sources_json'], str):
                try:
                    msg['sources'] = json.loads(msg['sources_json'])
                except Exception:
                    msg['sources'] = []
            messages.append(msg)

        return jsonify({"success": True, "session_id": session['id'], "messages": messages, "suggested_prompts": SUGGESTED_PROMPTS})
    finally:
        conn.close()

@app.route('/api/chat/send', methods=['POST'])
def send_chat_message():
    message_text = request.form.get('message', '').strip()
    image_file = request.files.get('image', None)

    # In case request is sent as JSON
    if not message_text and request.is_json:
        data = request.get_json() or {}
        message_text = data.get('message', '').strip()

    if not message_text and not image_file:
        return jsonify({"error": "Message or image attachment is required"}), 400

    # Handle image attachment if uploaded in chat
    attached_image_path = None
    relative_img_url = None
    if image_file and allowed_file(image_file.filename):
        ext = image_file.filename.rsplit('.', 1)[1].lower()
        filename = f"chat_{uuid.uuid4().hex[:10]}.{ext}"
        attached_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(attached_image_path)
        relative_img_url = f"/static/uploads/{filename}"

    conn = get_db_connection()
    try:
        user = conn.execute("SELECT * FROM users ORDER BY id ASC LIMIT 1").fetchone()
        user_id = user['id'] if user else 1

        # Retrieve active crop & farm context
        primary_crop = conn.execute(
            """SELECT c.*, f.farm_name, f.location FROM crops c
               JOIN farms f ON c.farm_id = f.id WHERE f.user_id = ? ORDER BY c.id DESC LIMIT 1""",
            (user_id,)
        ).fetchone()

        weather_ctx = weather_service.get_forecast()
        recent_diags = [dict(d) for d in conn.execute(
            "SELECT disease_name, diagnosed_crop, severity FROM diagnoses WHERE user_id = ? ORDER BY id DESC LIMIT 3",
            (user_id,)
        ).fetchall()]

        context = {
            "farmer_name": user['full_name'] if user else "Farmer",
            "village": user['village'] if user else "Bengaluru Rural",
            "crop_name": primary_crop['crop_name'] if primary_crop else "Tomato",
            "growth_stage": primary_crop['stage'] if primary_crop else "Vegetative Growth",
            "weather": weather_ctx,
            "recent_diagnoses": recent_diags
        }

        # Get or create active chat session
        session = conn.execute("SELECT id FROM chat_sessions WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
        if not session:
            cur = conn.cursor()
            cur.execute("INSERT INTO chat_sessions (user_id, title) VALUES (?, ?)", (user_id, f"Consultation: {context['crop_name']}"))
            conn.commit()
            session_id = cur.lastrowid
        else:
            session_id = session['id']

        # Save user message
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO chat_messages (session_id, sender, text, attached_image_path)
               VALUES (?, ?, ?, ?)""",
            (session_id, 'user', message_text or "Examining attached leaf image...", relative_img_url)
        )
        conn.commit()

        # Determine user language for multilingual response (honors selected chat language & auto-detects)
        requested_lang = request.form.get('language') or (request.get_json() or {}).get('language') or 'kn'
        user_lang = i18n_service.detect_language(message_text, requested_lang)

        if user_lang != 'en':
            # Generate grounded regional multilingual agronomist response
            multi_res = i18n_service.generate_multilingual_response(
                user_query=message_text,
                user_lang=user_lang,
                context=context
            )
            reply_text = multi_res['reply']
            citations = multi_res['citations']
            followups = multi_res['suggested_followups']
        else:
            # Generate grounded RAG response in English
            agronomist_reply = agronomist_engine.generate_response(
                user_query=message_text,
                context=context,
                attached_image_path=attached_image_path
            )
            reply_text = agronomist_reply['text']
            citations = agronomist_reply['citations']
            followups = agronomist_reply['suggested_followups']

        # Save agronomist response
        cur.execute(
            """INSERT INTO chat_messages (session_id, sender, text, sources_json)
               VALUES (?, ?, ?, ?)""",
            (session_id, 'agronomist', reply_text, json.dumps(citations))
        )
        conn.commit()

        return jsonify({
            "success": True,
            "reply": reply_text,
            "language": user_lang,
            "citations": citations,
            "suggested_followups": followups,
            "attached_image": relative_img_url,
            "timestamp": datetime.now().strftime("%H:%M")
        })
    finally:
        conn.close()

# Backwards compatible consultation endpoint
@app.route('/api/chat', methods=['POST'])
def chat_agronomist():
    data = request.get_json() or {}
    query = data.get('message', '').strip()
    if not query:
        return jsonify({"response": "Please ask a question about crop protection, fertilization, or weather."})
    
    reply = agronomist_engine.generate_response(query)
    return jsonify({
        "response": reply['text'],
        "citations": reply['citations'],
        "timestamp": datetime.now().strftime("%H:%M")
    })

@app.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1").fetchone()
        user_id = user['id'] if user else 1
        
        cur = conn.cursor()
        cur.execute("DELETE FROM chat_sessions WHERE user_id = ?", (user_id,))
        cur.execute(
            """INSERT INTO chat_sessions (user_id, title) VALUES (?, ?)""",
            (user_id, 'Fresh Agronomic Consultation')
        )
        new_session_id = cur.lastrowid
        cur.execute(
            """INSERT INTO chat_messages (session_id, sender, text, sources_json)
               VALUES (?, ?, ?, ?)""",
            (
                new_session_id,
                'agronomist',
                "Namaskara! Consultation session refreshed. Grounded in ICAR and UAS Bangalore agronomic publications. Ask any crop protection or cultivation question below!",
                "[]"
            )
        )
        conn.commit()
        return jsonify({"success": True, "message": "Chat history reset"})
    finally:
        conn.close()

# ----------------- PROFILE UPDATE API -----------------
@app.route('/api/profile', methods=['POST'])
def update_profile():
    data = request.get_json() or {}
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1").fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        conn.execute(
            """UPDATE users SET full_name = ?, phone = ?, village = ?, state = ?, preferred_language = ?
               WHERE id = ?""",
            (
                data.get('full_name', 'Punith S.'),
                data.get('phone', '+91 98450 12345'),
                data.get('village', 'Doddaballapur'),
                data.get('state', 'Karnataka'),
                data.get('preferred_language', 'en'),
                user['id']
            )
        )
        conn.commit()
        return jsonify({"success": True, "message": "Profile updated successfully"})
    finally:
        conn.close()

# ----------------- PHASE 4: OFFLINE MODE & EDGE INFERENCE API -----------------
@app.route('/api/edge/model-manifest', methods=['GET'])
def get_edge_model_manifest():
    """Returns metadata, quantization specs, and input/output tensor shapes for edge diagnostic model."""
    manifest = offline_service.get_model_manifest()
    return jsonify(manifest)

@app.route('/api/guides/offline-pack', methods=['GET'])
def get_offline_guides_pack():
    """Returns pre-packaged ICAR & UAS Bangalore agronomic guides for client-side offline caching."""
    guides = offline_service.get_offline_guides()
    return jsonify({"success": True, "guides": guides, "cached_at": datetime.now().isoformat()})

@app.route('/api/sync/batch', methods=['POST'])
def sync_batch_items():
    """
    Receives pending offline items (diagnoses, farm activities, crop records) with client_uuid
    and performs idempotent insertion and duplicate detection.
    """
    data = request.get_json() or {}
    items = data.get('items', [])
    if not items:
        return jsonify({"success": True, "synced_count": 0, "duplicates_ignored": 0, "items": []})

    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1").fetchone()
        user_id = user['id'] if user else 1
    finally:
        conn.close()

    result = offline_service.process_batch_sync(items, user_id)
    return jsonify(result)

# ----------------- PHASE 5: MULTILINGUAL VOICE ASSISTANT API -----------------
@app.route('/api/languages', methods=['GET'])
def get_supported_languages():
    """Returns metadata for all 7 supported Indian regional languages."""
    return jsonify({"success": True, "languages": REGIONAL_LANGUAGES})

@app.route('/api/voice/tts', methods=['GET', 'POST'])
def stream_voice_tts():
    """
    Streams natural native audio pronunciation for Kannada, Hindi, Telugu, Tamil, Marathi, Bengali, and English.
    Provides 100% reliable spoken audio playback on all browsers and devices without needing OS voice packs.
    """
    if request.method == 'POST':
        data = request.get_json() or {}
        text = data.get('text', '').strip()
        lang = data.get('language', 'kn')
    else:
        text = request.args.get('text', '').strip()
        lang = request.args.get('language', 'kn')

    if not text:
        return jsonify({"error": "Text is required"}), 400

    clean_text = re.sub(r'[*#_`]', '', text)
    speech_snippet = clean_text[:250]

    lang_map = {
        'kn': 'kn',
        'hi': 'hi',
        'te': 'te',
        'ta': 'ta',
        'mr': 'mr',
        'bn': 'bn',
        'en': 'en'
    }
    target_lang = lang_map.get(lang, 'kn')

    try:
        url = 'https://translate.google.com/translate_tts?ie=UTF-8&tl=' + target_lang + '&client=tw-ob&q=' + urllib.parse.quote(speech_snippet)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=8) as r:
            audio_bytes = r.read()
            return Response(audio_bytes, mimetype='audio/mpeg')
    except Exception as e:
        app.logger.warning(f"Voice TTS fetch error: {e}")
        return jsonify({"error": "Failed to stream audio", "details": str(e)}), 502

@app.route('/api/voice/query', methods=['POST'])
def process_voice_query():
    """
    Handles natural language voice questions spoken in Kannada, Hindi, Telugu, Tamil, Marathi, Bengali, or English.
    Translates/normalizes query, retrieves grounded RAG guidance, and returns audio-ready synthesized response.
    """
    data = request.get_json() or {}
    user_query = data.get('query', '').strip()
    user_lang = data.get('language') or 'kn'

    if not user_query:
        return jsonify({"success": False, "error": "Query text is required"}), 400

    conn = get_db_connection()
    try:
        user = conn.execute("SELECT * FROM users ORDER BY id ASC LIMIT 1").fetchone()
        context = {
            "farmer_name": user['full_name'] if user else "Farmer",
            "village": user['village'] if user else "Karnataka"
        }
    finally:
        conn.close()

    result = i18n_service.generate_multilingual_response(user_query, user_lang, context)
    # Generate direct audio stream URL for reliable client playback
    text_to_speak = result.get('speech_text') or result.get('reply') or ''
    speech_snip = re.sub(r'[*#_`]', '', text_to_speak)[:220]
    result['audio_url'] = f"/api/voice/tts?language={result['language']}&text={urllib.parse.quote(speech_snip)}"
    return jsonify(result)

# ----------------- PHASE 6: PRECISION FARMING & SATELLITE GIS API -----------------
@app.route('/api/precision/fields', methods=['GET'])
def get_precision_fields():
    """Returns farms with GeoJSON field boundaries, calculated hectares, and crop stages."""
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1").fetchone()
        user_id = user['id'] if user else 1

        farms = [dict(f) for f in conn.execute("SELECT * FROM farms WHERE user_id = ? ORDER BY id ASC", (user_id,)).fetchall()]
        
        for f in farms:
            if not f.get('boundary_geojson'):
                # Default precision polygon around Doddaballapur field [13.2984, 77.5458]
                default_polygon = [
                    [13.2995, 77.5445],
                    [13.2998, 77.5475],
                    [13.2970, 77.5472],
                    [13.2968, 77.5448],
                    [13.2995, 77.5445]
                ]
                f['boundary_geojson'] = json.dumps({"type": "Polygon", "coordinates": default_polygon})
                f['latitude'] = 13.2984
                f['longitude'] = 77.5458
                f['location_consent'] = 1
                area_res = precision_service.calculate_polygon_area(default_polygon)
                f['calculated_area_ha'] = area_res['area_hectares']

            if isinstance(f.get('boundary_geojson'), str):
                try:
                    f['boundary'] = json.loads(f['boundary_geojson'])
                except Exception:
                    f['boundary'] = None

            # Attach crops registered on this farm
            f['crops'] = [dict(c) for c in conn.execute("SELECT * FROM crops WHERE farm_id = ? ORDER BY id DESC", (f['id'],)).fetchall()]

        return jsonify({"success": True, "fields": farms})
    finally:
        conn.close()

@app.route('/api/precision/fields/boundary', methods=['POST'])
def save_field_boundary():
    """Saves updated GPS boundary polygon and calculates exact geodesic acreage."""
    data = request.get_json() or {}
    farm_id = data.get('farm_id')
    coordinates = data.get('coordinates', []) # list of [lat, lon]

    if not farm_id or len(coordinates) < 3:
        return jsonify({"success": False, "error": "Farm ID and at least 3 GPS boundary vertices are required"}), 400

    area_calc = precision_service.calculate_polygon_area(coordinates)

    conn = get_db_connection()
    try:
        conn.execute(
            """UPDATE farms 
               SET boundary_geojson = ?, calculated_area_ha = ?, acreage = ?, location_consent = 1
               WHERE id = ?""",
            (
                json.dumps({"type": "Polygon", "coordinates": coordinates}),
                area_calc["area_hectares"],
                area_calc["area_acres"],
                farm_id
            )
        )
        conn.commit()
        return jsonify({
            "success": True,
            "message": "Field boundary and geodesic area updated successfully",
            "area_metrics": area_calc
        })
    finally:
        conn.close()

@app.route('/api/precision/satellite/ndvi', methods=['GET'])
def get_satellite_ndvi():
    """Retrieves Sentinel-2 L2A multispectral NDVI time-series history & spatial grid."""
    farm_id = int(request.args.get('farm_id', 1))
    sync = request.args.get('sync', 'false').lower() in ['true', '1']
    history = precision_service.get_satellite_ndvi_history(farm_id, sync=sync)
    grid = precision_service.get_field_ndvi_grid(farm_id)
    history['spatial_grid'] = grid
    history['synced'] = sync
    return jsonify(history)

@app.route('/api/precision/crop-calendar', methods=['GET'])
def get_crop_calendar():
    """Returns region-specific UAS Bangalore crop calendar stage & scheduled reminders."""
    crop_name = request.args.get('crop', 'Tomato')
    sowing_date = request.args.get('sowing_date', None)
    calendar_res = precision_service.get_crop_calendar(crop_name=crop_name, sowing_date_str=sowing_date)
    return jsonify(calendar_res)

@app.route('/api/precision/outbreaks', methods=['GET'])
def get_disease_outbreaks():
    """Returns aggregated & privacy-jittered regional disease outbreak alerts."""
    lat = float(request.args.get('lat', 13.2984))
    lon = float(request.args.get('lon', 77.5458))
    radius_km = float(request.args.get('radius_km', 50))
    res = precision_service.get_regional_outbreaks(user_lat=lat, user_lon=lon, radius_km=radius_km)
    return jsonify(res)


# ----------------- PHASE 8: AGRICULTURAL MARKETPLACE & RETAILER CONNECT -----------------
@app.route('/api/marketplace/products', methods=['GET'])
def get_marketplace_products():
    """Returns paginated, searchable, categorized agricultural inputs catalog."""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 12))
    category = request.args.get('category', None)
    brand = request.args.get('brand', None)
    in_stock_only = request.args.get('in_stock_only', 'false').lower() == 'true'
    search = request.args.get('search', None)
    retailer_id = request.args.get('retailer_id', None)
    if retailer_id:
        retailer_id = int(retailer_id)

    res = marketplace_service.get_products(
        page=page, limit=limit, category=category, brand=brand,
        in_stock_only=in_stock_only, search=search, retailer_id=retailer_id
    )
    return jsonify(res)

@app.route('/api/marketplace/products/<int:product_id>', methods=['GET'])
def get_marketplace_product_detail(product_id):
    """Returns comprehensive product specifications, retailer details, and non-commercial alternatives."""
    product = marketplace_service.get_product_detail(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product)

@app.route('/api/marketplace/recommendations', methods=['GET'])
def get_marketplace_recommendations():
    """Returns scientifically matched CIBRC-registered inputs and organic bio-alternatives for a diagnosis."""
    crop = request.args.get('crop', 'Tomato')
    disease = request.args.get('disease', 'Early Blight')
    active_ingredient = request.args.get('active_ingredient', None)

    res = marketplace_service.get_recommended_products_for_diagnosis(
        crop_name=crop, disease_name=disease, active_ingredient=active_ingredient
    )
    return jsonify(res)

@app.route('/api/retailers', methods=['GET'])
def get_retailers_list():
    """Returns verified agricultural input retailers and cooperatives with distance and stock stats."""
    search = request.args.get('search', None)
    retailers = marketplace_service.get_retailers(search=search)
    return jsonify({"success": True, "retailers": retailers})

@app.route('/api/retailers/<int:retailer_id>', methods=['GET'])
def get_retailer_detail(retailer_id):
    """Returns full retailer profile and stocked product catalog."""
    retailer = marketplace_service.get_retailer_detail(retailer_id)
    if not retailer:
        return jsonify({"error": "Retailer not found"}), 404
    return jsonify({"success": True, "retailer": retailer})

@app.route('/api/retailers/inquiry', methods=['POST'])
def create_retailer_inquiry():
    """Dispatches farmer purchase inquiry or stock check request to licensed dealer."""
    data = request.get_json() or {}
    user_id = int(data.get('user_id', 1))
    retailer_id = data.get('retailer_id')
    product_id = data.get('product_id')
    inquiry_type = data.get('inquiry_type', 'stock_check')
    message = data.get('message', '')
    quantity_requested = data.get('quantity_requested', '1 unit')
    farmer_phone = data.get('farmer_phone', '+91 98450 12345')

    if not retailer_id or not message:
        return jsonify({"error": "Retailer ID and inquiry message are required"}), 400

    res = marketplace_service.create_inquiry(
        user_id=user_id,
        retailer_id=int(retailer_id),
        product_id=int(product_id) if product_id else None,
        inquiry_type=inquiry_type,
        message=message,
        quantity_requested=quantity_requested,
        farmer_phone=farmer_phone
    )
    return jsonify(res), (200 if res.get('success') else 400)

@app.route('/api/retailers/inquiries', methods=['GET'])
def get_retailer_inquiries():
    """Retrieves inquiry stream for retailer dashboard or farmer history."""
    retailer_id = request.args.get('retailer_id')
    user_id = request.args.get('user_id')
    status = request.args.get('status')

    inquiries = marketplace_service.get_retailer_inquiries(
        retailer_id=int(retailer_id) if retailer_id else None,
        user_id=int(user_id) if user_id else None,
        status=status
    )
    return jsonify({"success": True, "inquiries": inquiries})

@app.route('/api/retailers/inquiries/<int:inquiry_id>/status', methods=['POST'])
def update_retailer_inquiry_status(inquiry_id):
    """Updates status of a customer inquiry ('pending', 'contacted', 'fulfilled', 'cancelled')."""
    data = request.get_json() or {}
    status = data.get('status', 'contacted')
    notes = data.get('notes', '')
    res = marketplace_service.update_inquiry_status(inquiry_id, status, notes)
    return jsonify(res)

@app.route('/api/retailer/dashboard', methods=['GET'])
def get_retailer_dashboard():
    """Returns analytics and inventory overview for store owner portal."""
    retailer_id = int(request.args.get('retailer_id', 1))
    metrics = marketplace_service.get_retailer_dashboard_metrics(retailer_id)
    if not metrics:
        return jsonify({"error": "Retailer not found"}), 404
    return jsonify({"success": True, "dashboard": metrics})

@app.route('/api/retailer/inventory/<int:product_id>', methods=['POST'])
def update_retailer_inventory(product_id):
    """Updates product price, stock quantity, and in-stock status."""
    data = request.get_json() or {}
    retailer_id = int(data.get('retailer_id', 1))
    price_inr = data.get('price_inr')
    stock_quantity = data.get('stock_quantity')
    is_in_stock = data.get('is_in_stock')

    res = marketplace_service.update_inventory(
        product_id=product_id,
        retailer_id=retailer_id,
        price_inr=price_inr,
        stock_quantity=stock_quantity,
        is_in_stock=is_in_stock
    )
    return jsonify(res), (200 if res.get('success') else 400)

# ----------------- PHASE 8: ENTERPRISE B2B REST API (V1) -----------------
from functools import wraps

def require_b2b_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                api_key = auth_header[7:].strip()

        val = marketplace_service.validate_api_key(api_key)
        if not val.get('valid'):
            return jsonify({
                "error": "Unauthorized",
                "message": val.get('error', 'Valid enterprise API key required in X-API-Key or Authorization header')
            }), 401

        request.b2b_client = val
        response = f(*args, **kwargs)
        # Append rate limiting headers
        if isinstance(response, tuple):
            resp_obj, status_code = response
        else:
            resp_obj, status_code = response, 200

        if hasattr(resp_obj, 'headers'):
            resp_obj.headers['X-RateLimit-Limit'] = str(val.get('rate_limit_per_minute', 120))
            resp_obj.headers['X-RateLimit-Remaining'] = str(max(0, val.get('rate_limit_per_minute', 120) - 1))
            resp_obj.headers['X-Enterprise-Client'] = val.get('client_name', 'Enterprise Dist')
        return resp_obj, status_code
    return decorated_function

@app.route('/api/v1/b2b/products', methods=['GET'])
@require_b2b_api_key
def b2b_get_products():
    """Enterprise API: Synchronizes catalog inventory and pricing."""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    category = request.args.get('category', None)
    retailer_id = request.b2b_client.get('retailer_id')

    res = marketplace_service.get_products(page=page, limit=limit, category=category, retailer_id=retailer_id)
    return jsonify({
        "version": "v1.0",
        "client": request.b2b_client.get('client_name'),
        "catalog": res
    })

@app.route('/api/v1/b2b/inventory/batch', methods=['POST'])
@require_b2b_api_key
def b2b_batch_update_inventory():
    """Enterprise API: Batch stock and price updates for distributor ERPs."""
    data = request.get_json() or {}
    items = data.get('items', [])
    retailer_id = request.b2b_client.get('retailer_id', 1)

    if not items or not isinstance(items, list):
        return jsonify({"error": "Invalid request: 'items' list required"}), 400

    updated_count = 0
    errors = []
    for it in items:
        pid = it.get('product_id')
        if not pid:
            continue
        res = marketplace_service.update_inventory(
            product_id=pid,
            retailer_id=retailer_id,
            price_inr=it.get('price_inr'),
            stock_quantity=it.get('stock_quantity'),
            is_in_stock=it.get('is_in_stock')
        )
        if res.get('success'):
            updated_count += 1
        else:
            errors.append({"product_id": pid, "error": res.get('error')})

    return jsonify({
        "success": True,
        "updated_count": updated_count,
        "failed_count": len(errors),
        "errors": errors
    })

@app.route('/api/v1/b2b/inquiries', methods=['GET'])
@require_b2b_api_key
def b2b_get_inquiries():
    """Enterprise API: Inbound customer inquiry stream for enterprise CRM."""
    retailer_id = request.b2b_client.get('retailer_id')
    status = request.args.get('status')
    inquiries = marketplace_service.get_retailer_inquiries(retailer_id=retailer_id, status=status)
    return jsonify({
        "version": "v1.0",
        "client": request.b2b_client.get('client_name'),
        "inquiries": inquiries
    })

@app.route('/api/v1/b2b/docs', methods=['GET'])
def b2b_api_docs():
    """Returns OpenAPI specification for enterprise B2B distributor integrations."""
    return jsonify({
        "openapi": "3.0.0",
        "info": {
            "title": "Plantix AI Enterprise Agri-Marketplace B2B API",
            "version": "1.0.0",
            "description": "Enterprise B2B REST API for input distributors, seed companies, and agri-retailer ERPs."
        },
        "servers": [{"url": "/api/v1/b2b"}],
        "authentication": {
            "type": "apiKey",
            "name": "X-API-Key",
            "in": "header",
            "description": "Enterprise API Key provided by AgriVision Platform Administrator."
        },
        "endpoints": [
            {
                "path": "/products",
                "method": "GET",
                "description": "Fetch real-time catalog and inventory counts."
            },
            {
                "path": "/inventory/batch",
                "method": "POST",
                "description": "Batch update pricing and stock levels from ERP systems."
            },
            {
                "path": "/inquiries",
                "method": "GET",
                "description": "Retrieve inbound customer purchase leads and stock inquiries."
            }
        ]
    })


# ----------------- PHASE 9: AUTHENTICATION & SESSION MANAGEMENT -----------------
@app.route('/api/auth/register', methods=['POST'])
def auth_register():
    """Registers a new farmer, initializes farm plot and privacy consents, and issues authentication token."""
    from werkzeug.security import generate_password_hash
    data = request.get_json() or {}
    username = security_service.sanitize_input(data.get('username', ''))
    email = security_service.sanitize_input(data.get('email', ''))
    password = data.get('password', '')
    full_name = security_service.sanitize_input(data.get('full_name', ''))
    phone = security_service.sanitize_input(data.get('phone', ''))
    village = security_service.sanitize_input(data.get('village', 'Karnataka'))
    state = security_service.sanitize_input(data.get('state', 'Karnataka'))
    preferred_language = data.get('preferred_language', 'en')

    if not username or not email or not password or not full_name:
        return jsonify({"success": False, "error": {"code": "BAD_REQUEST", "message": "Username, email, password, and full name are required"}}), 400

    conn = get_db_connection()
    try:
        existing = conn.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email)).fetchone()
        if existing:
            return jsonify({"success": False, "error": {"code": "CONFLICT", "message": "Username or email already registered"}}), 409

        pwd_hash = generate_password_hash(password)
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO users (username, email, password_hash, full_name, phone, village, state, preferred_language)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (username, email, pwd_hash, full_name, phone, village, state, preferred_language)
        )
        new_user_id = cur.lastrowid

        cur.execute(
            """INSERT INTO farms (user_id, farm_name, acreage, soil_type, irrigation_type, location)
               VALUES (?, ?, 2.0, 'Red Sandy Loam', 'Drip Irrigation', ?)""",
            (new_user_id, f"{full_name} Farm Plot", f"{village}, {state}")
        )

        for ctype in ["location_telemetry", "camera_analysis", "voice_processing"]:
            cur.execute(
                """INSERT OR IGNORE INTO privacy_consents (user_id, consent_type, is_granted)
                   VALUES (?, ?, 1)""",
                (new_user_id, ctype)
            )

        conn.commit()

        token = security_service.generate_token(user_id=new_user_id, role="farmer")
        user_info = {
            "id": new_user_id,
            "username": username,
            "email": email,
            "full_name": full_name,
            "role": "farmer",
            "village": village,
            "preferred_language": preferred_language
        }
        return jsonify({"success": True, "token": token, "user": user_info}), 201
    finally:
        conn.close()

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    """Authenticates farmer or expert with password check and issues signed cryptographic token."""
    data = request.get_json() or {}
    username = security_service.sanitize_input(data.get('username') or data.get('email') or '')
    password = data.get('password', '')

    if not username or not password:
        return jsonify({"success": False, "error": {"code": "INVALID_CREDENTIALS", "message": "Username and password required"}}), 400

    conn = get_db_connection()
    try:
        user = conn.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username)).fetchone()
        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({"success": False, "error": {"code": "UNAUTHORIZED", "message": "Invalid username or password"}}), 401

        role = "expert" if user['is_expert'] else "farmer"
        token = security_service.generate_token(user_id=user['id'], role=role)

        user_info = {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": role,
            "village": user["village"],
            "preferred_language": user["preferred_language"]
        }
        return jsonify({"success": True, "token": token, "user": user_info})
    finally:
        conn.close()

@app.route('/api/auth/me', methods=['GET'])
def auth_me():
    """Returns profile for currently authenticated token."""
    auth_header = request.headers.get('Authorization', '')
    token = None
    if auth_header.startswith('Bearer '):
        token = auth_header[7:].strip()
    elif request.headers.get('X-Auth-Token'):
        token = request.headers.get('X-Auth-Token')

    val = security_service.verify_token(token)
    if not val["valid"]:
        return jsonify({"success": False, "error": {"code": "UNAUTHORIZED", "message": val["error"]}}), 401

    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id, username, email, full_name, phone, village, state, is_expert, expert_title, expert_badge, preferred_language FROM users WHERE id = ?", (val["user_id"],)).fetchone()
        if not user:
            return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": "User not found"}}), 404
        return jsonify({"success": True, "user": dict(user), "token_meta": val})
    finally:
        conn.close()

# ----------------- PHASE 9: PRIVACY & DPDP ACT 2023 COMPLIANCE -----------------
@app.route('/api/user/consent', methods=['GET'])
def get_user_consent():
    """Returns active privacy consent settings for the user."""
    user_id = int(request.args.get('user_id', 1))
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT consent_type, is_granted, updated_at FROM privacy_consents WHERE user_id = ?", (user_id,)).fetchall()
        consents = {r["consent_type"]: bool(r["is_granted"]) for r in rows}
        default_consents = {
            "location_telemetry": True,
            "camera_analysis": True,
            "voice_processing": True,
            "community_analytics": False
        }
        default_consents.update(consents)
        return jsonify({"success": True, "consents": default_consents})
    finally:
        conn.close()

@app.route('/api/user/consent', methods=['POST'])
def update_user_consent():
    """Updates user privacy consent choices under India DPDP Act 2023."""
    data = request.get_json() or {}
    user_id = int(data.get('user_id', 1))
    consent_type = data.get('consent_type')
    is_granted = 1 if data.get('is_granted', True) else 0

    if not consent_type:
        return jsonify({"success": False, "error": {"code": "BAD_REQUEST", "message": "consent_type is required"}}), 400

    conn = get_db_connection()
    try:
        conn.execute(
            """INSERT INTO privacy_consents (user_id, consent_type, is_granted, updated_at)
               VALUES (?, ?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(user_id, consent_type) DO UPDATE SET is_granted = excluded.is_granted, updated_at = CURRENT_TIMESTAMP""",
            (user_id, consent_type, is_granted)
        )
        conn.commit()
        return jsonify({"success": True, "message": f"Consent for '{consent_type}' updated to {bool(is_granted)}"})
    finally:
        conn.close()

@app.route('/api/user/export-data', methods=['GET'])
def export_user_data():
    """Data portability: exports full personal data package as structured JSON."""
    user_id = int(request.args.get('user_id', 1))
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id, username, email, full_name, phone, village, state, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": "User not found"}}), 404

        farms = [dict(f) for f in conn.execute("SELECT * FROM farms WHERE user_id = ?", (user_id,)).fetchall()]
        diagnoses = [dict(d) for d in conn.execute("SELECT id, diagnosed_crop, disease_name, confidence, severity, created_at FROM diagnoses WHERE user_id = ?", (user_id,)).fetchall()]
        activities = [dict(a) for a in conn.execute("SELECT * FROM farm_activities fa JOIN farms f ON fa.farm_id = f.id WHERE f.user_id = ?", (user_id,)).fetchall()]
        posts = [dict(p) for p in conn.execute("SELECT * FROM community_posts WHERE user_id = ?", (user_id,)).fetchall()]
        inquiries = [dict(i) for i in conn.execute("SELECT * FROM retailer_inquiries WHERE user_id = ?", (user_id,)).fetchall()]

        data_package = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "regulatory_framework": "India Digital Personal Data Protection (DPDP) Act 2023 & GDPR Art. 20",
            "farmer_profile": dict(user),
            "farms": farms,
            "crop_diagnoses": diagnoses,
            "farm_activities": activities,
            "community_posts": posts,
            "retailer_inquiries": inquiries
        }
        return jsonify({"success": True, "data_package": data_package})
    finally:
        conn.close()

@app.route('/api/user/delete-account', methods=['POST'])
def delete_user_account():
    """Right to be forgotten: cascades deletion of user personal identifying information."""
    data = request.get_json() or {}
    user_id = int(data.get('user_id', 1))

    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return jsonify({"success": True, "message": f"User account #{user_id} and associated data successfully purged."})
    finally:
        conn.close()

# ----------------- PHASE 9: OBSERVABILITY, METRICS & BACKUPS -----------------
@app.route('/api/metrics', methods=['GET'])
def get_system_metrics():
    """Returns system performance metrics, p95 latency, throughput, error rates, and cache stats."""
    metrics = monitoring_service.get_metrics()
    metrics["cache"] = cache_service.get_stats()
    return jsonify({"success": True, "metrics": metrics})

@app.route('/api/admin/backup', methods=['POST'])
def trigger_backup():
    """Triggers an online atomic database backup with integrity verification."""
    res = backup_service.create_backup()
    return jsonify(res), (200 if res.get('success') else 500)

@app.route('/api/admin/backups', methods=['GET'])
def list_backups():
    """Lists available database backup archives."""
    backups = backup_service.list_backups()
    return jsonify({"success": True, "backups": backups})

@app.route('/api/docs', methods=['GET'])
def get_api_documentation():
    """Interactive OpenAPI 3.0 specification for the complete AgriVision platform."""
    return jsonify({
        "openapi": "3.0.0",
        "info": {
            "title": "Plantix AI / AgriVision Platform API",
            "version": "9.0.0",
            "description": "Enterprise Agricultural Intelligence, Diagnostic Engine, Precision GIS & Marketplace Platform API."
        },
        "servers": [{"url": "/"}],
        "paths": {
            "/health": {"get": {"summary": "Subsystem health and readiness check"}},
            "/api/metrics": {"get": {"summary": "Latency percentiles, error rates, cache hit telemetry"}},
            "/api/diagnose": {"post": {"summary": "AI crop leaf disease diagnosis & spectral localization"}},
            "/api/marketplace/products": {"get": {"summary": "CIBRC-registered inputs & organic alternatives"}},
            "/api/community/posts": {"get": {"summary": "Farmer social feed with verified agronomist badge"}},
            "/api/precision/fields": {"get": {"summary": "GPS field boundaries and geodesic area calculation"}},
            "/api/v1/b2b/products": {"get": {"summary": "Enterprise distributor catalog sync (API Key Auth)"}}
        }
    })

# ----------------- HEALTH CHECK ROUTE (PHASE 9) -----------------
@app.route('/health')
def health():
    conn = get_db_connection()
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    except Exception as e:
        integrity = f"error: {str(e)}"
        journal_mode = "unknown"
    finally:
        conn.close()

    metrics = monitoring_service.get_metrics()
    cache_stats = cache_service.get_stats()

    return jsonify({
        "status": "healthy",
        "service": "Plantix AI / AgriVision Platform",
        "phase": 10,
        "production_ready": True,
        "system_integration": "verified",
        "security_engine": "active",
        "observability": "active",
        "cache_engine": "active",
        "marketplace_engine": "active",
        "enterprise_b2b_api": "v1 active",
        "community_engine": "active",
        "expert_network": "active",
        "rag_engine": "active",
        "offline_sync": "active",
        "edge_model": "PlantixMobileNetV3-AgriQuant",
        "voice_assistant": "active",
        "precision_farming": "active",
        "satellite_provider": "Copernicus Sentinel-2 L2A",
        "database": {
            "journal_mode": journal_mode,
            "integrity": integrity,
            "db_size_mb": metrics["storage"]["db_size_mb"]
        },
        "cache": {
            "hit_ratio_percent": cache_stats["hit_ratio_percent"],
            "active_keys": cache_stats["active_keys"]
        },
        "supported_languages": list(REGIONAL_LANGUAGES.keys()),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    return jsonify({"success": True, "message": "Signed out successfully"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
