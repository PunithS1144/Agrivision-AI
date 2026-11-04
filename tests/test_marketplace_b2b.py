# ============================================================================
# Unit and Integration Tests for Phase 8: Marketplace, Retailer Connect & B2B API
# Tests product discovery, category filtering, CIBRC compliance, retailer inquiries,
# diagnostic product recommendations with non-commercial alternatives, retailer dashboard,
# and Enterprise B2B REST API authentication.
# ============================================================================

import unittest
from app import app
from database.db import init_db, get_db_connection
from services.marketplace_service import marketplace_service

class TestMarketplaceAndB2BPhase8(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        with app.app_context():
            init_db()

    def setUp(self):
        self.client = app.test_client()

    # 1. Health & Service Status
    def test_health_phase8(self):
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertGreaterEqual(data["phase"], 8)
        self.assertEqual(data["marketplace_engine"], "active")
        self.assertEqual(data["enterprise_b2b_api"], "v1 active")

    # 2. Marketplace Products Discovery & Category Filtering
    def test_marketplace_products_catalog(self):
        res = self.client.get('/api/marketplace/products?page=1&limit=6')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("products", data)
        self.assertGreater(len(data["products"]), 0)
        self.assertIn("available_categories", data)

        # Test Category Filter: Crop Protection
        cp_res = self.client.get('/api/marketplace/products?category=Crop Protection')
        self.assertEqual(cp_res.status_code, 200)
        cp_data = cp_res.get_json()
        for p in cp_data["products"]:
            self.assertEqual(p["category"], "Crop Protection")

        # Test Category Filter: Organic Inputs
        org_res = self.client.get('/api/marketplace/products?category=Organic Inputs')
        self.assertEqual(org_res.status_code, 200)
        org_data = org_res.get_json()
        for p in org_data["products"]:
            self.assertEqual(p["category"], "Organic Inputs")

        # Test Search Filter
        search_res = self.client.get('/api/marketplace/products?search=Trichoderma')
        self.assertEqual(search_res.status_code, 200)
        s_data = search_res.get_json()
        self.assertTrue(any("trichoderma" in p["name"].lower() for p in s_data["products"]))

    # 3. Product Details, CIBRC Regulatory Compliance & Non-Commercial Alternatives
    def test_product_detail_and_safety(self):
        res = self.client.get('/api/marketplace/products/1')
        self.assertEqual(res.status_code, 200)
        p = res.get_json()
        self.assertIn("name", p)
        self.assertIn("cibrc_registration_no", p)
        self.assertIn("dosage_guidance", p)
        self.assertIn("retailer_name", p)
        # Verify non-commercial organic alternative presence (zero-bias agronomy)
        self.assertIn("non_commercial_alternative", p)
        self.assertTrue(len(p["non_commercial_alternative"]) > 0)

        # Test CIBRC Safety Validation
        safe_check = marketplace_service.check_product_compliance("Tata Contaf", "Hexaconazole 5% SC")
        self.assertTrue(safe_check["is_permitted"])

        banned_check = marketplace_service.check_product_compliance("Endosulfan 35 EC", "Endosulfan")
        self.assertFalse(banned_check["is_permitted"])

    # 4. Retailers Directory & Store Connect
    def test_retailers_directory(self):
        res = self.client.get('/api/retailers')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertGreater(len(data["retailers"]), 0)
        r0 = data["retailers"][0]
        self.assertIn("name", r0)
        self.assertIn("phone", r0)
        self.assertIn("license_number", r0)
        self.assertIn("operating_hours", r0)
        self.assertIn("product_count", r0)

        # Detail view
        det_res = self.client.get(f'/api/retailers/{r0["id"]}')
        self.assertEqual(det_res.status_code, 200)
        det_data = det_res.get_json()
        self.assertTrue(det_data["success"])
        self.assertIn("products", det_data["retailer"])

    # 5. Customer Purchase Inquiry Workflow
    def test_retailer_inquiry_workflow(self):
        # Create inquiry
        inq_res = self.client.post('/api/retailers/inquiry', json={
            "user_id": 1,
            "retailer_id": 1,
            "product_id": 1,
            "inquiry_type": "stock_check",
            "message": "Do you have 2 bottles of Contaf Plus in stock for Doddaballapur pickup?",
            "quantity_requested": "2 bottles",
            "farmer_phone": "+91 98450 12345"
        })
        self.assertEqual(inq_res.status_code, 200)
        inq_data = inq_res.get_json()
        self.assertTrue(inq_data["success"])
        inquiry_id = inq_data["inquiry_id"]

        # Fetch inquiries list
        list_res = self.client.get(f'/api/retailers/inquiries?retailer_id=1')
        self.assertEqual(list_res.status_code, 200)
        inquiries = list_res.get_json()["inquiries"]
        self.assertTrue(any(i["id"] == inquiry_id for i in inquiries))

        # Update status
        status_res = self.client.post(f'/api/retailers/inquiries/{inquiry_id}/status', json={
            "status": "fulfilled",
            "notes": "Farmer collected at store counter"
        })
        self.assertEqual(status_res.status_code, 200)
        self.assertTrue(status_res.get_json()["success"])

    # 6. Diagnosis Product Linkage & Bias Prevention
    def test_diagnosis_marketplace_recommendations(self):
        res = self.client.get('/api/marketplace/recommendations?crop=Tomato&disease=Early Blight')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("commercial_products", data)
        self.assertIn("non_commercial_alternatives", data)
        self.assertIn("bias_disclosure", data)

        # Verify non-commercial alternatives are explicitly surfaced
        self.assertGreater(len(data["non_commercial_alternatives"]), 0)

        # Verify matched products belong to target crop/disease
        for p in data["commercial_products"]:
            self.assertTrue("Tomato" in p["target_crops"] or "Early Blight" in p["target_diseases"])

    # 7. Retailer Dashboard & Inventory Updates
    def test_retailer_dashboard(self):
        dash_res = self.client.get('/api/retailer/dashboard?retailer_id=1')
        self.assertEqual(dash_res.status_code, 200)
        d_data = dash_res.get_json()
        self.assertTrue(d_data["success"])
        d = d_data["dashboard"]
        self.assertIn("catalog_metrics", d)
        self.assertIn("inquiry_metrics", d)
        self.assertGreater(d["catalog_metrics"]["total_products"], 0)

        # Update inventory price and stock
        up_res = self.client.post('/api/retailer/inventory/1', json={
            "retailer_id": 1,
            "price_inr": 490.0,
            "stock_quantity": 42
        })
        self.assertEqual(up_res.status_code, 200)
        self.assertTrue(up_res.get_json()["success"])

    # 8. Enterprise B2B REST API Authentication & Endpoints
    def test_enterprise_b2b_api(self):
        # 1. Unauthorized request without key
        unauth_res = self.client.get('/api/v1/b2b/products')
        self.assertEqual(unauth_res.status_code, 401)

        # 2. Valid request with X-API-Key
        headers = {"X-API-Key": "b2b_kisan_enterprise_key_2026"}
        auth_res = self.client.get('/api/v1/b2b/products', headers=headers)
        self.assertEqual(auth_res.status_code, 200)
        b2b_data = auth_res.get_json()
        self.assertEqual(b2b_data["version"], "v1.0")
        self.assertIn("catalog", b2b_data)
        # Check rate limit headers
        self.assertIn("X-RateLimit-Limit", auth_res.headers)
        self.assertIn("X-Enterprise-Client", auth_res.headers)

        # 3. Batch Inventory Update via B2B API
        batch_payload = {
            "items": [
                {"product_id": 1, "price_inr": 485.0, "stock_quantity": 50},
                {"product_id": 2, "price_inr": 915.0, "stock_quantity": 25}
            ]
        }
        batch_res = self.client.post('/api/v1/b2b/inventory/batch', json=batch_payload, headers=headers)
        self.assertEqual(batch_res.status_code, 200)
        b_data = batch_res.get_json()
        self.assertTrue(b_data["success"])
        self.assertEqual(b_data["updated_count"], 2)

        # 4. Inquiries stream for B2B CRM
        inq_stream = self.client.get('/api/v1/b2b/inquiries', headers=headers)
        self.assertEqual(inq_stream.status_code, 200)
        self.assertIn("inquiries", inq_stream.get_json())

        # 5. OpenAPI specification documentation endpoint
        docs_res = self.client.get('/api/v1/b2b/docs')
        self.assertEqual(docs_res.status_code, 200)
        docs_data = docs_res.get_json()
        self.assertEqual(docs_data["openapi"], "3.0.0")

if __name__ == '__main__':
    unittest.main()
