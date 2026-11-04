# Test Suite for Phase 6: Precision Farming, Satellite Integration & Outbreak Surveillance

import unittest
import json
from app import app
from database.db import init_db, get_db_connection
from services.precision_service import precision_service

class TestPrecisionFarmingPhase6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        with app.app_context():
            init_db()

    def setUp(self):
        self.client = app.test_client()

    def test_health_phase6(self):
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreaterEqual(data["phase"], 6)
        self.assertEqual(data["precision_farming"], "active")
        self.assertEqual(data["satellite_provider"], "Copernicus Sentinel-2 L2A")
        self.assertEqual(data["status"], "healthy")

    def test_geodesic_polygon_area_calculation(self):
        # Sample rectangular field around Doddaballapur coordinates
        polygon = [
            [13.2995, 77.5445],
            [13.2998, 77.5475],
            [13.2970, 77.5472],
            [13.2968, 77.5448],
            [13.2995, 77.5445]
        ]
        area = precision_service.calculate_polygon_area(polygon)
        self.assertGreater(area["area_sq_m"], 10000.0) # > 1 Hectare
        self.assertGreater(area["area_hectares"], 1.0)
        self.assertAlmostEqual(area["area_acres"], area["area_hectares"] * 2.47105, delta=0.05)

        # Degenerate polygon test (< 3 points)
        bad_area = precision_service.calculate_polygon_area([[13.29, 77.54], [13.30, 77.55]])
        self.assertEqual(bad_area["area_sq_m"], 0.0)
        self.assertEqual(bad_area["area_hectares"], 0.0)

    def test_satellite_ndvi_history_and_disclaimer(self):
        res = self.client.get('/api/precision/satellite/ndvi?farm_id=1')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("Copernicus Sentinel-2", data["satellite_provider"])
        self.assertGreater(data["current_mean_ndvi"], 0.3)
        self.assertLessEqual(data["current_mean_ndvi"], 1.0)
        self.assertGreaterEqual(data["cloud_cover_percent"], 0.0)
        self.assertGreaterEqual(data["stress_area_percent"], 0.0)
        self.assertGreater(len(data["time_series"]), 0)
        self.assertIn("spatial_grid", data)
        # Verify strict scientific disclaimer (do not claim satellite detects specific diseases)
        self.assertIn("scientific_disclaimer", data)
        self.assertIn("does not constitute a laboratory diagnosis", data["scientific_disclaimer"].lower())

    def test_precision_fields_endpoint(self):
        res = self.client.get('/api/precision/fields')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertGreater(len(data["fields"]), 0)
        f = data["fields"][0]
        self.assertIn("boundary_geojson", f)
        self.assertIn("calculated_area_ha", f)
        self.assertIn("crops", f)

    def test_update_field_boundary(self):
        new_coords = [
            [13.3000, 77.5450],
            [13.3000, 77.5480],
            [13.2970, 77.5480],
            [13.2970, 77.5450]
        ]
        payload = {
            "farm_id": 1,
            "coordinates": new_coords
        }
        res = self.client.post('/api/precision/fields/boundary', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("area_metrics", data)
        self.assertGreater(data["area_metrics"]["area_acres"], 0.5)

    def test_crop_calendar_stages_and_reminders(self):
        res = self.client.get('/api/precision/crop-calendar?crop=Tomato&sowing_date=2026-09-15')
        self.assertEqual(res.status_code, 200)
        cal = res.get_json()
        self.assertTrue(cal["success"])
        self.assertEqual(cal["crop"], "Tomato")
        self.assertIn("current_stage_name", cal)
        self.assertIn("irrigation_reminder", cal)
        self.assertIn("fertilizer_reminder", cal)
        self.assertIn("pest_monitoring_reminder", cal)
        self.assertIn("expected_harvest_date", cal)
        self.assertGreater(len(cal["all_stages"]), 3)

    def test_privacy_preserved_outbreaks(self):
        res = self.client.get('/api/precision/outbreaks?lat=13.2984&lon=77.5458&radius_km=60')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertGreater(data["total_outbreaks"], 0)
        ob = data["outbreaks"][0]
        self.assertIn("approx_lat", ob)
        self.assertIn("approx_lon", ob)
        self.assertIn("privacy_notice", ob)
        self.assertIn("distance_km", ob)
        # Ensure proximity sorting
        distances = [o["distance_km"] for o in data["outbreaks"]]
        self.assertEqual(distances, sorted(distances))

if __name__ == '__main__':
    unittest.main()
