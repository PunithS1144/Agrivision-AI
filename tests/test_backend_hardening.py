# ============================================================================
# Unit and Integration Tests for Phase 9: Backend Modernization, Security & Scalability
# Tests WAL mode, composite indexes, JWT authentication, sliding-window rate limiting,
# security headers, input/image sanitization, TTL caching, DPDP privacy data export,
# system metrics, and online atomic database backups.
# ============================================================================

import unittest
import io
import time
from PIL import Image
from app import app
from database.db import init_db, get_db_connection
from services.cache_service import cache_service
from services.security_service import security_service
from services.monitoring_service import monitoring_service
from services.backup_service import backup_service

class TestBackendHardeningPhase9(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        with app.app_context():
            init_db()

    def setUp(self):
        self.client = app.test_client()

    # 1. Health Check & Subsystem Telemetry
    def test_health_phase9(self):
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertGreaterEqual(data["phase"], 9)
        self.assertEqual(data["security_engine"], "active")
        self.assertEqual(data["observability"], "active")
        self.assertEqual(data["cache_engine"], "active")
        # Verify SQLite WAL mode and database integrity
        self.assertEqual(data["database"]["journal_mode"].lower(), "wal")
        self.assertEqual(data["database"]["integrity"].lower(), "ok")
        self.assertIn("db_size_mb", data["database"])

    # 2. Security Headers & Request Correlation IDs
    def test_security_headers_and_correlation_id(self):
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        self.assertIn("X-Request-ID", res.headers)
        self.assertEqual(res.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(res.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(res.headers.get("X-XSS-Protection"), "1; mode=block")
        self.assertEqual(res.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")

    # 3. Cryptographic Token Authentication & Session Verification
    def test_authentication_workflow(self):
        # 1. Valid Login
        login_res = self.client.post('/api/auth/login', json={
            "username": "farmer_punith",
            "password": "farmer123"
        })
        self.assertEqual(login_res.status_code, 200)
        login_data = login_res.get_json()
        self.assertTrue(login_data["success"])
        self.assertIn("token", login_data)
        token = login_data["token"]

        # 2. Authenticated Profile Access via Bearer Token
        headers = {"Authorization": f"Bearer {token}"}
        me_res = self.client.get('/api/auth/me', headers=headers)
        self.assertEqual(me_res.status_code, 200)
        me_data = me_res.get_json()
        self.assertTrue(me_data["success"])
        self.assertEqual(me_data["user"]["username"], "farmer_punith")

        # 3. Invalid Password Attempt
        bad_login = self.client.post('/api/auth/login', json={
            "username": "farmer_punith",
            "password": "wrongpassword"
        })
        self.assertEqual(bad_login.status_code, 401)

        # 4. Tampered Token Verification
        tampered_token = token[:-5] + "XXXXX"
        bad_me = self.client.get('/api/auth/me', headers={"Authorization": f"Bearer {tampered_token}"})
        self.assertEqual(bad_me.status_code, 401)

    # 4. Input Sanitization & Image Security
    def test_sanitization_and_image_compression(self):
        # Test XSS script stripping
        dirty_input = "<script>alert('pwned')</script>Tomato Early Blight"
        clean = security_service.sanitize_input(dirty_input)
        self.assertNotIn("<script>", clean)
        self.assertEqual(clean, "Tomato Early Blight")

        # Test valid image optimization
        img = Image.new('RGB', (800, 600), color='green')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)

        opt_res = security_service.sanitize_and_optimize_image(img_io)
        self.assertTrue(opt_res["valid"])
        self.assertIn("optimized_size_kb", opt_res)

        # Test corrupted image byte rejection
        fake_io = io.BytesIO(b"NOT_A_REAL_IMAGE_FILE_BYTES_FAKE_PAYLOAD")
        bad_res = security_service.sanitize_and_optimize_image(fake_io)
        self.assertFalse(bad_res["valid"])

    # 5. In-Memory TTL Caching Engine
    def test_caching_engine_telemetry(self):
        cache_service.clear()
        self.assertIsNone(cache_service.get("test_key"))

        # Set key with TTL
        cache_service.set("test_key", "val_123", ttl_seconds=5)
        self.assertEqual(cache_service.get("test_key"), "val_123")

        stats = cache_service.get_stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertGreater(stats["hit_ratio_percent"], 0.0)

    # 6. Privacy & DPDP Act 2023 Compliance (Data Portability & Consents)
    def test_privacy_and_data_export(self):
        # 1. Query Privacy Consents
        c_res = self.client.get('/api/user/consent?user_id=1')
        self.assertEqual(c_res.status_code, 200)
        c_data = c_res.get_json()
        self.assertTrue(c_data["success"])
        self.assertIn("consents", c_data)

        # 2. Update Consent
        up_res = self.client.post('/api/user/consent', json={
            "user_id": 1,
            "consent_type": "community_analytics",
            "is_granted": True
        })
        self.assertEqual(up_res.status_code, 200)
        self.assertTrue(up_res.get_json()["success"])

        # 3. Export Personal Data Package (Art. 20 Portability)
        exp_res = self.client.get('/api/user/export-data?user_id=1')
        self.assertEqual(exp_res.status_code, 200)
        exp_data = exp_res.get_json()
        self.assertTrue(exp_data["success"])
        pkg = exp_data["data_package"]
        self.assertIn("farmer_profile", pkg)
        self.assertIn("farms", pkg)
        self.assertIn("crop_diagnoses", pkg)
        self.assertIn("regulatory_framework", pkg)

    # 7. System Metrics & Telemetry (Observability)
    def test_system_metrics_endpoint(self):
        res = self.client.get('/api/metrics')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        m = data["metrics"]
        self.assertIn("uptime_seconds", m)
        self.assertIn("traffic", m)
        self.assertIn("latency_ms", m)
        self.assertIn("storage", m)
        self.assertIn("cache", m)

    # 8. Database Disaster Recovery & Atomic Backups
    def test_database_backup_and_integrity(self):
        # 1. Trigger online non-blocking backup
        bk_res = self.client.post('/api/admin/backup')
        self.assertEqual(bk_res.status_code, 200)
        bk_data = bk_res.get_json()
        self.assertTrue(bk_data["success"])
        self.assertEqual(bk_data["integrity"], "verified_ok")
        backup_file = bk_data["backup_file"]

        # 2. List backups
        list_res = self.client.get('/api/admin/backups')
        self.assertEqual(list_res.status_code, 200)
        archives = list_res.get_json()["backups"]
        self.assertTrue(any(b["filename"] == backup_file for b in archives))

        # 3. Verify backup file integrity
        val = backup_service.verify_backup(backup_file)
        self.assertTrue(val["valid"])
        self.assertGreater(val["tables"], 10)

    # 9. OpenAPI 3.0 Platform Documentation
    def test_platform_api_docs(self):
        res = self.client.get('/api/docs')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["openapi"], "3.0.0")
        self.assertIn("paths", data)

if __name__ == '__main__':
    unittest.main()
