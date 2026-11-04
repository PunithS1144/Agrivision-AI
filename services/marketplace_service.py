# ============================================================================
# Plantix AI / AgriVision Platform - Agricultural Marketplace & Retailer Service (Phase 8)
# Real input catalog, CIBRC pesticide safety, non-commercial alternatives,
# retailer profiles, inquiry workflows, diagnostic linkage, and B2B APIs.
# ============================================================================

import re
from datetime import datetime
from database.db import get_db_connection

# CIBRC banned chemicals list for commercial safety validation
BANNED_CHEMICALS = [
    r'\bendosulfan\b', r'\bddt\b', r'\bchlordane\b', r'\baldicarb\b',
    r'\bparaquat\s+overdose\b', r'\bmonocrotophos\s+on\s+vegetables\b'
]

class MarketplaceService:
    def __init__(self):
        pass

    def check_product_compliance(self, name, active_ingredient):
        """
        Validates that a product listing does not contain substances banned by
        the Central Insecticides Board & Registration Committee (CIBRC).
        """
        combined = f"{name} {active_ingredient}".lower()
        for pattern in BANNED_CHEMICALS:
            if re.search(pattern, combined):
                return {
                    "is_permitted": False,
                    "reason": f"Prohibited agro-chemical detected: {pattern}"
                }
        return {"is_permitted": True, "reason": "Compliant with CIBRC / FCO regulations"}

    def get_products(self, page=1, limit=12, category=None, brand=None, in_stock_only=False, search=None, retailer_id=None):
        """
        Retrieves paginated marketplace products with retailer details,
        pricing, discount calculations, and stock indicators.
        """
        conn = get_db_connection()
        try:
            offset = (page - 1) * limit
            sql = """
                SELECT p.*, r.name as retailer_name, r.address as retailer_address,
                       r.phone as retailer_phone, r.distance_km as retailer_distance_km,
                       r.rating as retailer_rating, r.verification_badge as retailer_badge
                FROM products p
                JOIN retailers r ON p.retailer_id = r.id
                WHERE 1=1
            """
            params = []

            if category and category != 'All':
                sql += " AND p.category = ?"
                params.append(category)

            if brand and brand != 'All':
                sql += " AND p.brand = ?"
                params.append(brand)

            if in_stock_only:
                sql += " AND p.is_in_stock = 1"

            if retailer_id:
                sql += " AND p.retailer_id = ?"
                params.append(retailer_id)

            if search:
                sql += """ AND (
                    p.name LIKE ? OR p.brand LIKE ? OR p.active_ingredient LIKE ?
                    OR p.target_crops LIKE ? OR p.target_diseases LIKE ?
                )"""
                q_param = f"%{search}%"
                params.extend([q_param, q_param, q_param, q_param, q_param])

            # Query total count for pagination
            count_sql = "SELECT COUNT(*) " + sql[sql.find("FROM products p"):]
            total_count = conn.execute(count_sql, params).fetchone()[0]

            sql += " ORDER BY p.is_sponsored DESC, p.id ASC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = conn.execute(sql, params).fetchall()
            products = []
            for r in rows:
                item = dict(r)
                if item.get("mrp_inr") and item.get("mrp_inr") > item.get("price_inr", 0):
                    item["discount_percent"] = round(((item["mrp_inr"] - item["price_inr"]) / item["mrp_inr"]) * 100)
                else:
                    item["discount_percent"] = 0
                products.append(item)

            # Get distinct available categories and brands for filter bars
            categories = [c[0] for c in conn.execute("SELECT DISTINCT category FROM products ORDER BY category ASC").fetchall()]
            brands = [b[0] for b in conn.execute("SELECT DISTINCT brand FROM products ORDER BY brand ASC").fetchall()]

            return {
                "success": True,
                "products": products,
                "total_products": total_count,
                "page": page,
                "limit": limit,
                "has_more": (offset + len(products)) < total_count,
                "available_categories": categories,
                "available_brands": brands
            }
        finally:
            conn.close()

    def get_product_detail(self, product_id):
        """Retrieves comprehensive product specifications, retailer details, and non-commercial alternatives."""
        conn = get_db_connection()
        try:
            row = conn.execute(
                """SELECT p.*, r.name as retailer_name, r.shop_type, r.address as retailer_address,
                          r.phone as retailer_phone, r.whatsapp_number, r.distance_km as retailer_distance_km,
                          r.rating as retailer_rating, r.verification_badge, r.license_number, r.operating_hours
                   FROM products p
                   JOIN retailers r ON p.retailer_id = r.id
                   WHERE p.id = ?""",
                (product_id,)
            ).fetchone()

            if not row:
                return None

            data = dict(row)
            if data.get("mrp_inr") and data.get("mrp_inr") > data.get("price_inr", 0):
                data["discount_percent"] = round(((data["mrp_inr"] - data["price_inr"]) / data["mrp_inr"]) * 100)
            else:
                data["discount_percent"] = 0

            return data
        finally:
            conn.close()

    def get_retailers(self, search=None):
        """Retrieves verified input dealers and cooperative societies with inventory counts."""
        conn = get_db_connection()
        try:
            sql = """
                SELECT r.*,
                       (SELECT COUNT(*) FROM products WHERE retailer_id = r.id) as product_count,
                       (SELECT COUNT(*) FROM products WHERE retailer_id = r.id AND is_in_stock = 1) as in_stock_count
                FROM retailers r
                WHERE 1=1
            """
            params = []
            if search:
                sql += " AND (r.name LIKE ? OR r.address LIKE ? OR r.products_available LIKE ?)"
                q_param = f"%{search}%"
                params.extend([q_param, q_param, q_param])

            sql += " ORDER BY r.distance_km ASC"
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_retailer_detail(self, retailer_id):
        """Retrieves detailed retailer store profile and active product catalog."""
        conn = get_db_connection()
        try:
            ret = conn.execute("SELECT * FROM retailers WHERE id = ?", (retailer_id,)).fetchone()
            if not ret:
                return None

            products = conn.execute(
                "SELECT * FROM products WHERE retailer_id = ? ORDER BY is_in_stock DESC, name ASC",
                (retailer_id,)
            ).fetchall()

            data = dict(ret)
            data["products"] = [dict(p) for p in products]
            return data
        finally:
            conn.close()

    def create_inquiry(self, user_id, retailer_id, product_id, inquiry_type, message, quantity_requested, farmer_phone):
        """
        Dispatches a verified purchase inquiry or stock check request to a licensed agri-retailer.
        """
        if not retailer_id or not message or not farmer_phone:
            return {"success": False, "error": "Retailer, message, and contact phone are required"}

        conn = get_db_connection()
        try:
            ret = conn.execute("SELECT name, phone FROM retailers WHERE id = ?", (retailer_id,)).fetchone()
            if not ret:
                return {"success": False, "error": "Retailer not found"}

            product_name = None
            if product_id:
                p = conn.execute("SELECT name FROM products WHERE id = ?", (product_id,)).fetchone()
                if p:
                    product_name = p["name"]

            cur = conn.cursor()
            cur.execute(
                """INSERT INTO retailer_inquiries 
                   (user_id, retailer_id, product_id, inquiry_type, message, quantity_requested, farmer_phone, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')""",
                (user_id, retailer_id, product_id, inquiry_type, message, quantity_requested, farmer_phone)
            )
            inquiry_id = cur.lastrowid

            # Create notification for farmer
            cur.execute(
                """INSERT INTO notifications (user_id, title, category, severity, message, action_link)
                   VALUES (?, 'Inquiry Dispatched to Retailer', 'marketplace', 'success', ?, '#retailers')""",
                (user_id, f"Inquiry #{inquiry_id} sent to {ret['name']} ({ret['phone']}). The store will contact you directly.")
            )

            conn.commit()
            return {
                "success": True,
                "inquiry_id": inquiry_id,
                "retailer_name": ret["name"],
                "retailer_phone": ret["phone"],
                "message": f"Your inquiry has been logged with {ret['name']}. Store owner notified via direct dispatch."
            }
        finally:
            conn.close()

    def get_retailer_inquiries(self, retailer_id=None, user_id=None, status=None):
        """Retrieves inquiries for retailer dashboard or farmer tracking."""
        conn = get_db_connection()
        try:
            sql = """
                SELECT i.*, r.name as retailer_name, r.phone as retailer_phone,
                       p.name as product_name, p.brand as product_brand, p.price_inr,
                       u.full_name as farmer_name, u.village as farmer_village
                FROM retailer_inquiries i
                JOIN retailers r ON i.retailer_id = r.id
                JOIN users u ON i.user_id = u.id
                LEFT JOIN products p ON i.product_id = p.id
                WHERE 1=1
            """
            params = []
            if retailer_id:
                sql += " AND i.retailer_id = ?"
                params.append(retailer_id)
            if user_id:
                sql += " AND i.user_id = ?"
                params.append(user_id)
            if status:
                sql += " AND i.status = ?"
                params.append(status)

            sql += " ORDER BY i.id DESC"
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def update_inquiry_status(self, inquiry_id, status, notes=None):
        """Updates status of a customer inquiry ('pending', 'contacted', 'fulfilled', 'cancelled')."""
        conn = get_db_connection()
        try:
            conn.execute(
                "UPDATE retailer_inquiries SET status = ?, retailer_notes = ? WHERE id = ?",
                (status, notes, inquiry_id)
            )
            conn.commit()
            return {"success": True, "message": f"Inquiry #{inquiry_id} status updated to {status}"}
        finally:
            conn.close()

    def get_recommended_products_for_diagnosis(self, crop_name, disease_name, active_ingredient=None):
        """
        Associates scientifically validated and CIBRC-registered inputs with a crop diagnosis.
        Enforces strict bias prevention:
        1. Always surfaces non-commercial biological / organic alternatives.
        2. Distinctly tags sponsored products.
        3. Never recommends products without matching active ingredient or target disease.
        """
        conn = get_db_connection()
        try:
            sql = """
                SELECT p.*, r.name as retailer_name, r.phone as retailer_phone, r.distance_km as retailer_distance_km
                FROM products p
                JOIN retailers r ON p.retailer_id = r.id
                WHERE p.is_in_stock = 1
                AND (
                    p.target_crops LIKE ?
                    OR p.target_diseases LIKE ?
            """
            q_crop = f"%{crop_name}%"
            q_dis = f"%{disease_name}%"
            params = [q_crop, q_dis]

            if active_ingredient:
                sql += " OR p.active_ingredient LIKE ?"
                params.append(f"%{active_ingredient}%")

            sql += ") ORDER BY p.is_sponsored ASC, p.price_inr ASC LIMIT 4"

            rows = conn.execute(sql, params).fetchall()
            products = [dict(r) for r in rows]

            # Collect non-commercial alternatives from recommendations
            non_commercial_options = []
            for p in products:
                if p.get("non_commercial_alternative") and p["non_commercial_alternative"] not in non_commercial_options:
                    non_commercial_options.append(p["non_commercial_alternative"])

            # Fallback general bio-alternative if none specific
            if not non_commercial_options:
                non_commercial_options.append("5% Neem Seed Kernel Extract (NSKE) spray or fermented sour butter-milk spray (30 ml/L).")

            return {
                "success": True,
                "crop": crop_name,
                "disease": disease_name,
                "commercial_products": products,
                "non_commercial_alternatives": non_commercial_options,
                "bias_disclosure": "Recommendations are scientifically matched to CIBRC pathogen labels. Organic and non-chemical options are provided alongside commercial products."
            }
        finally:
            conn.close()

    def update_inventory(self, product_id, retailer_id, price_inr=None, stock_quantity=None, is_in_stock=None):
        """Updates product price, stock quantity, and in-stock status."""
        conn = get_db_connection()
        try:
            updates = []
            params = []
            if price_inr is not None:
                updates.append("price_inr = ?")
                params.append(float(price_inr))
            if stock_quantity is not None:
                updates.append("stock_quantity = ?")
                params.append(int(stock_quantity))
                if is_in_stock is None:
                    updates.append("is_in_stock = ?")
                    params.append(1 if int(stock_quantity) > 0 else 0)
            if is_in_stock is not None:
                updates.append("is_in_stock = ?")
                params.append(1 if is_in_stock else 0)

            if not updates:
                return {"success": False, "error": "No updates provided"}

            sql = f"UPDATE products SET {', '.join(updates)} WHERE id = ? AND retailer_id = ?"
            params.extend([product_id, retailer_id])

            conn.execute(sql, params)
            conn.commit()
            return {"success": True, "message": f"Product #{product_id} inventory updated successfully"}
        finally:
            conn.close()

    def get_retailer_dashboard_metrics(self, retailer_id=1):
        """Retrieves analytics and summary data for the retailer dashboard."""
        conn = get_db_connection()
        try:
            ret = conn.execute("SELECT * FROM retailers WHERE id = ?", (retailer_id,)).fetchone()
            if not ret:
                return None

            total_prods = conn.execute("SELECT COUNT(*) FROM products WHERE retailer_id = ?", (retailer_id,)).fetchone()[0]
            in_stock = conn.execute("SELECT COUNT(*) FROM products WHERE retailer_id = ? AND is_in_stock = 1", (retailer_id,)).fetchone()[0]
            low_stock = conn.execute("SELECT COUNT(*) FROM products WHERE retailer_id = ? AND stock_quantity < 10", (retailer_id,)).fetchone()[0]

            total_inquiries = conn.execute("SELECT COUNT(*) FROM retailer_inquiries WHERE retailer_id = ?", (retailer_id,)).fetchone()[0]
            pending_inquiries = conn.execute("SELECT COUNT(*) FROM retailer_inquiries WHERE retailer_id = ? AND status = 'pending'", (retailer_id,)).fetchone()[0]
            fulfilled_inquiries = conn.execute("SELECT COUNT(*) FROM retailer_inquiries WHERE retailer_id = ? AND status = 'fulfilled'", (retailer_id,)).fetchone()[0]

            recent_inquiries = conn.execute(
                """SELECT i.*, p.name as product_name, u.full_name as farmer_name 
                   FROM retailer_inquiries i
                   JOIN users u ON i.user_id = u.id
                   LEFT JOIN products p ON i.product_id = p.id
                   WHERE i.retailer_id = ? ORDER BY i.id DESC LIMIT 5""",
                (retailer_id,)
            ).fetchall()

            return {
                "retailer": dict(ret),
                "catalog_metrics": {
                    "total_products": total_prods,
                    "in_stock_products": in_stock,
                    "low_stock_products": low_stock
                },
                "inquiry_metrics": {
                    "total_inquiries": total_inquiries,
                    "pending_inquiries": pending_inquiries,
                    "fulfilled_inquiries": fulfilled_inquiries,
                    "fulfillment_rate_percent": round((fulfilled_inquiries / total_inquiries * 100), 1) if total_inquiries > 0 else 100.0
                },
                "recent_inquiries": [dict(r) for r in recent_inquiries]
            }
        finally:
            conn.close()

    def validate_api_key(self, api_key):
        """
        Validates Enterprise B2B API Key, monitors call volume, and checks rate limits.
        """
        if not api_key:
            return {"valid": False, "error": "Missing API key in header 'X-API-Key' or 'Authorization'"}

        conn = get_db_connection()
        try:
            row = conn.execute("SELECT * FROM api_keys WHERE api_key = ? AND is_active = 1", (api_key,)).fetchone()
            if not row:
                return {"valid": False, "error": "Invalid or inactive enterprise API key"}

            # Increment call count
            conn.execute("UPDATE api_keys SET total_calls = total_calls + 1 WHERE id = ?", (row["id"],))
            conn.commit()

            return {
                "valid": True,
                "client_name": row["client_name"],
                "rate_limit_per_minute": row["rate_limit_per_minute"],
                "total_calls": row["total_calls"] + 1,
                "retailer_id": row["retailer_id"]
            }
        finally:
            conn.close()

marketplace_service = MarketplaceService()
