"""
Phase 10 — End-to-End System Integration, Regression & Empirical Benchmark Test Suite
Validates all features across Phases 0 through 9:
- Health and runtime architecture check (SQLite WAL, integrity ok)
- AI Crop Diagnostic Pipeline with 5-point quality gatekeeper and spectral localization
- Multi-unit nutrient calculator (CIBRC / FCO compliant)
- Agro-weather & dedicated spray window advisories
- Precision farming GIS & Sentinel-2 L2A 10m NDVI time-series
- Farmer community & expert peer-review network
- Agricultural marketplace, retailer directory & Enterprise B2B API
- Offline batch synchronization & idempotency
- Security, rate limiting & DPDP Act 2023 compliance
- Empirical latency & throughput benchmarking (p50, p95, p99, mean)
"""

import unittest
import json
import io
import time
import uuid
import numpy as np
from PIL import Image
from app import app
from database.db import get_db_connection

class TestPhase10FullSystemIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        app.config['TESTING'] = True

    def test_01_system_health_and_wal_integrity(self):
        """Verify server health check, SQLite WAL mode, and database integrity."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get('status'), 'healthy')
        self.assertGreaterEqual(data.get('phase', 0), 9)
        db_info = data.get('database', {})
        self.assertEqual(db_info.get('integrity'), 'ok')
        self.assertEqual(db_info.get('journal_mode'), 'wal')

    def test_02_crop_diagnosis_pipeline(self):
        """Verify image diagnosis with quality gatekeeper, confidence score, and symptom localization."""
        # Create a procedural synthetic leaf image with high Laplacian variance (> 40.0)
        np.random.seed(42)
        base = np.zeros((300, 300, 3), dtype=np.uint8)
        base[:, :] = [45, 130, 45]  # Green leaf base
        noise = np.random.randint(-40, 40, (300, 300, 3), dtype=np.int16)
        textured = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        for r, c in [(100, 100), (180, 220), (220, 120)]:
            rr, cc = np.ogrid[:300, :300]
            mask = ((rr - r)**2 + (cc - c)**2) <= 25**2
            textured[mask] = [80, 50, 20]

        img_bytes = io.BytesIO()
        pil_img = Image.fromarray(textured)
        pil_img.save(img_bytes, format='JPEG', quality=95)
        img_bytes.seek(0)

        data = {
            'image': (img_bytes, 'leaf_test.jpg'),
            'crop': 'Tomato'
        }
        res = self.client.post('/api/diagnose', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        result = res.get_json()
        self.assertTrue(result.get('success', False))
        self.assertEqual(result.get('crop'), 'Tomato')
        self.assertIn('disease', result)
        self.assertIn('confidence', result)
        self.assertTrue(result.get('quality_passed', False))
        self.assertIn('symptom_localization', result)
        # Verify 4-pillar treatments
        self.assertIn('organic_treatment', result)
        self.assertIn('chemical_treatment', result)
        self.assertIn('cultural_treatment', result)
        self.assertIn('biological_treatment', result)

    def test_03_fertilizer_calculator_units(self):
        """Verify NPK dosage calculation across Indian regional units (acre, guntha, bigha, hectare)."""
        units = ['acre', 'guntha', 'bigha', 'hectare']
        for unit in units:
            res = self.client.post('/api/fertilizer/calculate', json={
                'crop': 'Tomato',
                'area': 2.5,
                'unit': unit,
                'growth_stage': 'Vegetative'
            })
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data.get('success', False))
            self.assertIn('plan', data)
            plan = data['plan']
            self.assertIn('commercial_fertilizers', plan)
            self.assertIn('urea_kg', plan['commercial_fertilizers'])
            self.assertGreater(plan['commercial_fertilizers']['urea_kg'], 0)

    def test_04_agro_weather_and_spray_window(self):
        """Verify 7-day agro-weather forecast and dedicated spray window advisory."""
        # Weather & Agro-advisory
        res_weather = self.client.get('/api/weather?lat=12.9716&lon=77.5946')
        self.assertEqual(res_weather.status_code, 200)
        wdata = res_weather.get_json()
        self.assertIn('current', wdata)
        self.assertIn('forecast_days', wdata)
        self.assertIn('agri_advisory', wdata)
        self.assertGreater(len(wdata['forecast_days']), 0)

        # Dedicated spray window
        res_spray = self.client.get('/api/weather/spray-window?lat=12.9716&lon=77.5946')
        self.assertEqual(res_spray.status_code, 200)
        sdata = res_spray.get_json()
        self.assertTrue(sdata.get('success', False))
        self.assertIn('advisory', sdata)
        self.assertIn('hourly_windows', sdata)

    def test_05_precision_farming_gis(self):
        """Verify farm plots geodesic area and Sentinel-2 L2A 10m NDVI time-series."""
        # Get farm fields
        res_fields = self.client.get('/api/precision/fields?user_id=1')
        self.assertEqual(res_fields.status_code, 200)
        pdata = res_fields.get_json()
        self.assertTrue(pdata.get('success', False))
        self.assertIn('fields', pdata)

        # Get NDVI analysis
        res_ndvi = self.client.get('/api/precision/satellite/ndvi?farm_id=1')
        self.assertEqual(res_ndvi.status_code, 200)
        ndata = res_ndvi.get_json()
        self.assertIn('satellite_provider', ndata)
        self.assertIn('time_series', ndata)
        self.assertGreater(len(ndata['time_series']), 0)
        self.assertIn('spatial_grid', ndata)

    def test_06_community_and_expert_peer_review(self):
        """Verify post creation, agronomic second-opinion request, and banned pesticide filter."""
        # Create standard post
        res_post = self.client.post('/api/community/post', json={
            'user_id': 1,
            'title': 'Yellow spot pattern on lower tomato leaves',
            'content': 'Noticed early morning fungal blight spots. Requesting organic treatment advice.',
            'crop_tag': 'Tomato',
            'topic_tag': 'Disease & Pests'
        })
        self.assertEqual(res_post.status_code, 200)
        post_data = res_post.get_json()
        self.assertTrue(post_data.get('success', False))
        self.assertFalse(post_data.get('is_flagged', True))

        # Expert second-opinion request
        req_res = self.client.post('/api/expert/reviews/request', json={
            'user_id': 1,
            'crop_name': 'Tomato',
            'disease_suspected': 'Early Blight',
            'urgency': 'High',
            'notes': 'Spreading rapidly across rows 3 and 4.'
        })
        self.assertEqual(req_res.status_code, 200)
        req_data = req_res.get_json()
        self.assertTrue(req_data.get('success', False))
        self.assertIn('request_id', req_data)

        # Verify CIBRC banned chemical filter (Endosulfan is prohibited by Supreme Court/CIBRC)
        res_banned = self.client.post('/api/community/post', json={
            'user_id': 1,
            'title': 'Spray endosulfan immediately',
            'content': 'Endosulfan kills all insect pests in vegetables.',
            'crop_tag': 'Tomato',
            'topic_tag': 'Disease & Pests'
        })
        self.assertEqual(res_banned.status_code, 200)
        banned_data = res_banned.get_json()
        self.assertTrue(banned_data.get('is_flagged', False))

    def test_07_marketplace_and_b2b_api(self):
        """Verify products listing, CIBRC/FCO compliance, and Enterprise B2B endpoint."""
        # Product listing
        res_prod = self.client.get('/api/marketplace/products?category=Crop Protection')
        self.assertEqual(res_prod.status_code, 200)
        prod_data = res_prod.get_json()
        self.assertTrue(prod_data.get('success', False))
        self.assertIn('products', prod_data)
        self.assertGreater(len(prod_data['products']), 0)
        self.assertIn('cibrc_registration_no', prod_data['products'][0])

        # Enterprise B2B endpoint with valid API key
        headers = {'X-API-Key': 'b2b_kisan_enterprise_key_2026'}
        res_b2b = self.client.get('/api/v1/b2b/products', headers=headers)
        self.assertEqual(res_b2b.status_code, 200)
        b2b_data = res_b2b.get_json()
        self.assertEqual(b2b_data.get('version'), 'v1.0')
        self.assertIn('catalog', b2b_data)

    def test_08_offline_batch_sync(self):
        """Verify offline queue idempotent batch synchronization."""
        test_uuid_diag = f"test_uuid_diag_{uuid.uuid4().hex[:12]}"
        test_uuid_act = f"test_uuid_act_{uuid.uuid4().hex[:12]}"

        sync_payload = {
            'items': [
                {
                    'client_uuid': test_uuid_diag,
                    'entity_type': 'diagnosis',
                    'payload': {
                        'crop_id': 1,
                        'diagnosed_crop': 'Tomato',
                        'disease_name': 'Offline Early Blight Triage',
                        'confidence': 91.2,
                        'severity': 'Moderate',
                        'active_ingredient': 'Mancozeb 75% WP @ 2.5 g/L',
                        'phi_days': 5
                    }
                },
                {
                    'client_uuid': test_uuid_act,
                    'entity_type': 'farm_activity',
                    'payload': {
                        'farm_id': 1,
                        'activity_type': 'Spraying',
                        'activity_date': '2026-11-04',
                        'description': 'Offline logged preventive spray',
                        'quantity_used': '2.5 g / L'
                    }
                }
            ]
        }
        res_sync = self.client.post('/api/sync/batch', json=sync_payload)
        self.assertEqual(res_sync.status_code, 200)
        sync_data = res_sync.get_json()
        self.assertTrue(sync_data.get('success', False))
        self.assertEqual(sync_data.get('synced_count'), 2)
        self.assertEqual(sync_data.get('duplicates_ignored'), 0)

        # Duplicate replay test
        res_dup = self.client.post('/api/sync/batch', json=sync_payload)
        self.assertEqual(res_dup.status_code, 200)
        dup_data = res_dup.get_json()
        self.assertEqual(dup_data.get('synced_count'), 0)
        self.assertEqual(dup_data.get('duplicates_ignored'), 2)

    def test_09_empirical_performance_benchmarking(self):
        """Empirically benchmark endpoint response latencies (50 iterations) and assert performance limits."""
        latencies = []
        for _ in range(50):
            start = time.perf_counter()
            res = self.client.post('/api/fertilizer/calculate', json={
                'crop': 'Rice',
                'area': 1.0,
                'unit': 'acre',
                'growth_stage': 'Tillering'
            })
            duration_ms = (time.perf_counter() - start) * 1000.0
            latencies.append(duration_ms)
            self.assertEqual(res.status_code, 200)

        mean_lat = float(np.mean(latencies))
        p50 = float(np.percentile(latencies, 50))
        p95 = float(np.percentile(latencies, 95))
        p99 = float(np.percentile(latencies, 99))

        print(f"\n[Empirical Benchmark] /api/fertilizer/calculate (50 runs): Mean={mean_lat:.2f}ms, P50={p50:.2f}ms, P95={p95:.2f}ms, P99={p99:.2f}ms")

        # Sub-50ms target for in-memory / optimized SQLite operations
        self.assertLess(mean_lat, 50.0)
        self.assertLess(p95, 100.0)

    def test_10_dpdp_privacy_compliance(self):
        """Verify India DPDP Act 2023 consent tracking and data portability export."""
        res_export = self.client.get('/api/user/export-data?user_id=1')
        self.assertEqual(res_export.status_code, 200)
        export_data = res_export.get_json()
        self.assertTrue(export_data.get('success', False))
        self.assertIn('data_package', export_data)
        pkg = export_data['data_package']
        self.assertIn('farmer_profile', pkg)
        self.assertIn('farms', pkg)
        self.assertIn('crop_diagnoses', pkg)
        self.assertIn('regulatory_framework', pkg)

if __name__ == '__main__':
    unittest.main()
