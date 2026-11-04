# Test Suite for Phase 4: Offline Mode, Edge Inference & Smart Camera Architecture

import unittest
import uuid
import json
import numpy as np
from PIL import Image
from app import app
from database.db import init_db, get_db_connection
from services.offline_service import offline_service, EDGE_MODEL_MANIFEST

class TestOfflineEdgePhase4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        with app.app_context():
            init_db()

    def setUp(self):
        self.client = app.test_client()

    def test_health_phase4(self):
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreaterEqual(data["phase"], 4)
        self.assertEqual(data["offline_sync"], "active")
        self.assertEqual(data["status"], "healthy")
        self.assertIn("edge_model", data)

    def test_edge_model_manifest_specs(self):
        res = self.client.get('/api/edge/model-manifest')
        self.assertEqual(res.status_code, 200)
        manifest = res.get_json()

        self.assertEqual(manifest["model_name"], "PlantixMobileNetV3-AgriQuant")
        self.assertEqual(manifest["version"], "1.2.0")
        self.assertIn("INT8", manifest["quantization"])
        self.assertEqual(manifest["input_specs"]["shape"], [1, 224, 224, 3])
        self.assertEqual(manifest["output_specs"]["shape"], [1, 18])
        self.assertIn("Tomato - Early Blight (Alternaria solani)", manifest["supported_classes"])
        self.assertIn("edge_status", manifest)
        self.assertIn("missing_dependency_notice", manifest["edge_status"])

    def test_offline_guides_pack(self):
        res = self.client.get('/api/guides/offline-pack')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["guides"]), 4)
        guide_crops = [g["crop"] for g in data["guides"]]
        self.assertIn("Tomato", guide_crops)
        self.assertIn("Potato", guide_crops)

    def test_batch_sync_with_idempotency_and_deduplication(self):
        test_client_uuid_1 = f"test_uuid_diag_{uuid.uuid4().hex[:12]}"
        test_client_uuid_2 = f"test_uuid_act_{uuid.uuid4().hex[:12]}"

        batch_payload = {
            "items": [
                {
                    "client_uuid": test_client_uuid_1,
                    "entity_type": "diagnosis",
                    "payload": {
                        "crop_id": 1,
                        "diagnosed_crop": "Tomato",
                        "disease_name": "Offline Early Blight Triage",
                        "confidence": 84.5,
                        "severity": "Moderate",
                        "active_ingredient": "Mancozeb 75% WP @ 2.5 g/L",
                        "phi_days": 5
                    }
                },
                {
                    "client_uuid": test_client_uuid_2,
                    "entity_type": "farm_activity",
                    "payload": {
                        "farm_id": 1,
                        "activity_type": "Spraying",
                        "activity_date": "2026-11-04",
                        "description": "Offline logged preventive spray",
                        "quantity_used": "2.5 g / L"
                    }
                }
            ]
        }

        # 1. First sync batch -> Both items should be inserted
        res1 = self.client.post('/api/sync/batch', json=batch_payload)
        self.assertEqual(res1.status_code, 200)
        data1 = res1.get_json()
        self.assertTrue(data1["success"])
        self.assertEqual(data1["synced_count"], 2)
        self.assertEqual(data1["duplicates_ignored"], 0)

        # 2. Duplicate sync replay -> Both items should be detected as duplicates and ignored
        res2 = self.client.post('/api/sync/batch', json=batch_payload)
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertTrue(data2["success"])
        self.assertEqual(data2["synced_count"], 0)
        self.assertEqual(data2["duplicates_ignored"], 2)
        self.assertEqual(data2["items"][0]["status"], "already_synced")

        # 3. Verify in database that diagnoses has client_uuid and is_offline = 1
        conn = get_db_connection()
        try:
            row = conn.execute("SELECT * FROM diagnoses WHERE client_uuid = ?", (test_client_uuid_1,)).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["is_offline"], 1)
            self.assertEqual(row["sync_status"], "synced")
            self.assertEqual(row["disease_name"], "Offline Early Blight Triage")

            act_row = conn.execute("SELECT * FROM farm_activities WHERE client_uuid = ?", (test_client_uuid_2,)).fetchone()
            self.assertIsNotNone(act_row)
            self.assertEqual(act_row["is_offline"], 1)
        finally:
            conn.close()

    def test_tensor_preprocessing_dimensions(self):
        # Verify local input tensor requirements matching MobileNetV3 specs
        img = Image.new('RGB', (320, 240), color=(50, 150, 60))
        resized = img.resize((224, 224))
        arr = np.array(resized, dtype=np.float32)

        # Preprocess matching MobileNet (-1.0 to 1.0)
        normalized = (arr / 127.5) - 1.0
        self.assertEqual(normalized.shape, (224, 224, 3))
        self.assertGreaterEqual(float(np.min(normalized)), -1.0)
        self.assertLessEqual(float(np.max(normalized)), 1.0)

if __name__ == '__main__':
    unittest.main()
