# Test Suite for Phase 5: Multilingual Voice Assistant & Regional Language Experience

import unittest
from app import app
from database.db import init_db
from services.i18n_service import i18n_service, REGIONAL_LANGUAGES

class TestMultilingualVoicePhase5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        with app.app_context():
            init_db()

    def setUp(self):
        self.client = app.test_client()

    def test_health_phase5(self):
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreaterEqual(data["phase"], 5)
        self.assertEqual(data["voice_assistant"], "active")
        self.assertIn("supported_languages", data)
        self.assertIn("kn", data["supported_languages"])
        self.assertIn("hi", data["supported_languages"])
        self.assertIn("bn", data["supported_languages"])

    def test_languages_endpoint(self):
        res = self.client.get('/api/languages')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        langs = data["languages"]
        for code in ["en", "kn", "hi", "te", "ta", "mr", "bn"]:
            self.assertIn(code, langs)
            self.assertIn("bcp47", langs[code])
            self.assertIn("native", langs[code])

    def test_kannada_voice_query_chlorosis(self):
        # Kannada query: "Tomato leaves are turning yellow, what to do?"
        payload = {
            "query": "ಟೊಮೆಟೊ ಎಲೆಗಳು ಹಳದಿಯಾಗುತ್ತಿವೆ, ಏನು ಮಾಡಬೇಕು?",
            "language": "kn"
        }
        res = self.client.post('/api/voice/query', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["language"], "kn")
        self.assertEqual(data["bcp47"], "kn-IN")
        self.assertIn("ಸಾರಜನಕ", data["reply"]) # Nitrogen in Kannada
        self.assertIn("ಯೂರಿಯಾ", data["reply"]) # Urea in Kannada
        self.assertGreater(len(data["citations"]), 0)
        self.assertGreater(len(data["suggested_followups"]), 0)

    def test_hindi_voice_query_blight(self):
        # Hindi query: "What medicine for tomato blight disease?"
        payload = {
            "query": "टमाटर में झुलसा रोग की दवा क्या है?",
            "language": "hi"
        }
        res = self.client.post('/api/voice/query', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["language"], "hi")
        self.assertEqual(data["bcp47"], "hi-IN")
        self.assertIn("झुलसा", data["reply"])
        self.assertIn("मैंकोजेब", data["reply"]) # Mancozeb in Hindi
        self.assertGreater(len(data["citations"]), 0)

    def test_telugu_voice_query(self):
        payload = {
            "query": "టమోటా ఆకుమచ్చ తెగులు మందు ఏమిటి?",
            "language": "te"
        }
        res = self.client.post('/api/voice/query', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["language"], "te")
        self.assertEqual(data["bcp47"], "te-IN")

    def test_tamil_voice_query(self):
        payload = {
            "query": "தக்காளி இலைக்கருகல் நோய் மருந்து என்ன?",
            "language": "ta"
        }
        res = self.client.post('/api/voice/query', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["language"], "ta")
        self.assertEqual(data["bcp47"], "ta-IN")

    def test_marathi_voice_query(self):
        payload = {
            "query": "टोमॅटो करपा रोगाचे औषध काय आहे?",
            "language": "mr"
        }
        res = self.client.post('/api/voice/query', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["language"], "mr")

    def test_bengali_voice_query(self):
        payload = {
            "query": "টমেটো ধসা রোগের ওষুধ কী?",
            "language": "bn"
        }
        res = self.client.post('/api/voice/query', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["language"], "bn")

    def test_empty_query_validation(self):
        res = self.client.post('/api/voice/query', json={"query": ""})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])

if __name__ == '__main__':
    unittest.main()
