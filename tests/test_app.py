import io
import unittest
from PIL import Image
import numpy as np
from app import app
from database.db import init_db, get_db_connection

class TestAppRoutesPhase3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        with app.app_context():
            init_db()

    def setUp(self):
        self.client = app.test_client()

    def test_health_endpoint(self):
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertGreaterEqual(data["phase"], 6)
        self.assertEqual(data["rag_engine"], "active")
        self.assertEqual(data["offline_sync"], "active")
        self.assertEqual(data["voice_assistant"], "active")
        self.assertEqual(data["precision_farming"], "active")
        self.assertEqual(data.get("community_engine"), "active")
        self.assertEqual(data.get("expert_network"), "active")

    def test_state_api_phase2(self):
        res = self.client.get('/api/state')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("notifications", data)
        self.assertIn("farm_activities", data)
        self.assertGreater(len(data["farms"]), 0)

    def test_fertilizer_calculate_units(self):
        # Test Guntha unit calculation
        payload = {"crop_name": "Tomato", "acreage": 40, "unit": "Gunthas"}
        res = self.client.post('/api/fertilizer/calculate', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        # 40 Gunthas == 1.0 Acre
        self.assertAlmostEqual(data["plan"]["normalized_acres"], 1.0, delta=0.05)

    def test_fertilizer_invalid_payload(self):
        payload = {"crop_name": "Tomato", "acreage": -5}
        res = self.client.post('/api/fertilizer/calculate', json=payload)
        self.assertEqual(res.status_code, 400)

    def test_diagnosis_upload_and_history(self):
        # Create textured green test image
        img_arr = np.full((250, 250, 3), (40, 145, 50), dtype=np.uint8)
        noise = np.random.randint(-10, 10, (250, 250, 3), dtype=np.int16)
        img_arr = np.clip(img_arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        img_io = io.BytesIO()
        Image.fromarray(img_arr).save(img_io, 'JPEG')
        img_io.seek(0)

        data = {
            'crop_name': 'Tomato',
            'image': (img_io, 'test_phase2_leaf.jpg')
        }
        res = self.client.post('/api/diagnose', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        diag = res.get_json()
        self.assertTrue(diag["success"])
        self.assertIn("differential_diagnoses", diag)
        diag_id = diag["id"]

        # Test history query with search filter
        hist_res = self.client.get(f'/api/diagnoses/history?crop=Tomato')
        self.assertEqual(hist_res.status_code, 200)
        records = hist_res.get_json()
        self.assertGreater(len(records), 0)

        # Test export CSV
        csv_res = self.client.get('/api/diagnoses/export?format=csv')
        self.assertEqual(csv_res.status_code, 200)
        self.assertIn(b"Active Ingredient", csv_res.data)

        # Test delete diagnosis record
        del_res = self.client.delete(f'/api/diagnoses/{diag_id}')
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.get_json()["success"])

    def test_farm_activity_logging(self):
        payload = {
            "farm_id": 1,
            "activity_type": "Spraying",
            "activity_date": "2026-11-04",
            "quantity_used": "2.5 g / L Mancozeb",
            "description": "Prophylactic spray across Tomato field"
        }
        res = self.client.post('/api/farms/activity', json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["success"])

    def test_notifications_read(self):
        # Mark all read
        res = self.client.post('/api/notifications/mark-read', json={})
        self.assertEqual(res.status_code, 200)

    def test_chat_flow_and_history(self):
        # 1. Fetch initial chat history
        hist_res = self.client.get('/api/chat/history')
        self.assertEqual(hist_res.status_code, 200)
        hist_data = hist_res.get_json()
        self.assertTrue(hist_data["success"])
        self.assertIn("messages", hist_data)

        # 2. Send agricultural message with farm context
        payload = {
            "message": "What is the recommended dosage of Chlorantraniliprole for tomato pinworm?",
            "context": {
                "crop": "Tomato",
                "growth_stage": "Fruiting",
                "farm": "Green Acres"
            }
        }
        send_res = self.client.post('/api/chat/send', json=payload)
        self.assertEqual(send_res.status_code, 200)
        reply = send_res.get_json()
        self.assertTrue(reply["success"])
        self.assertIn("reply", reply)
        self.assertIn("citations", reply)
        self.assertGreater(len(reply["citations"]), 0)
        self.assertIn("suggested_followups", reply)

        # 3. Clear chat session
        clear_res = self.client.post('/api/chat/clear', json={})
        self.assertEqual(clear_res.status_code, 200)
        self.assertTrue(clear_res.get_json()["success"])

if __name__ == '__main__':
    unittest.main()
