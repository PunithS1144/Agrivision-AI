import unittest
from app import app

class TestMultilingualChatAndFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        app.config['TESTING'] = True

    def test_kannada_chat_query_returns_kannada(self):
        res = self.client.post('/api/chat/send', data={
            'message': 'ಟೊಮೇಟೊ ಎಲೆ ಹಳದಿ ಆಗಲು ಕಾರಣವೇನು?',
            'language': 'kn'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['language'], 'kn')
        # Check that response contains Kannada characters
        self.assertTrue(any('\u0C80' <= c <= '\u0CFF' for c in data['reply']))

    def test_hindi_chat_query_returns_hindi(self):
        res = self.client.post('/api/chat/send', data={
            'message': 'टमाटर की पत्तियां पीली क्यों हो रही हैं?',
            'language': 'hi'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['language'], 'hi')
        # Check that response contains Devanagari characters
        self.assertTrue(any('\u0900' <= c <= '\u097F' for c in data['reply']))

    def test_weather_force_refresh_and_coordinates(self):
        res = self.client.get('/api/weather?lat=13.3100&lon=77.5520&city=Doddaballapur%20North&refresh=true')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['latitude'], 13.31)
        self.assertEqual(data['longitude'], 77.552)
        self.assertIn('Doddaballapur', data['city'])
        self.assertIn('updated_at', data)

    def test_satellite_sync_overpass(self):
        res = self.client.get('/api/precision/satellite/ndvi?farm_id=1&sync=true')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertTrue(data.get('synced', False))
        self.assertIn('satellite_provider', data)

    def test_auth_logout(self):
        res = self.client.post('/api/auth/logout')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])

if __name__ == '__main__':
    unittest.main()
