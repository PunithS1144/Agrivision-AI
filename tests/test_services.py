import os
import unittest
from PIL import Image
import numpy as np
from services.fertilizer_service import fertilizer_calculator
from services.ai_diagnosis import diagnosis_engine
from services.weather_service import weather_service
from services.advisory_service import consult_ai_agronomist
from services.rag_knowledge_base import rag_retriever
from services.agronomist_engine import agronomist_engine

class TestAgriServicesPhase3(unittest.TestCase):
    def setUp(self):
        # 1. Valid leaf sample: green leaf with subtle texture
        self.valid_leaf_path = "test_valid_leaf.jpg"
        arr = np.full((300, 300, 3), (35, 140, 45), dtype=np.uint8)
        # Add slight natural leaf variance/texture
        noise = np.random.randint(-15, 15, (300, 300, 3), dtype=np.int16)
        arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        Image.fromarray(arr).save(self.valid_leaf_path)

        # 2. Pitch dark image
        self.dark_path = "test_dark_leaf.jpg"
        Image.new('RGB', (300, 300), color=(10, 10, 10)).save(self.dark_path)

        # 3. Washed out image
        self.bright_path = "test_bright_leaf.jpg"
        Image.new('RGB', (300, 300), color=(245, 245, 245)).save(self.bright_path)

        # 4. Non-plant image (pure blue sky)
        self.non_plant_path = "test_non_plant.jpg"
        Image.new('RGB', (300, 300), color=(30, 80, 230)).save(self.non_plant_path)

    def tearDown(self):
        for p in [self.valid_leaf_path, self.dark_path, self.bright_path, self.non_plant_path]:
            if os.path.exists(p):
                os.remove(p)

    def test_valid_diagnosis_with_4_pillars(self):
        res = diagnosis_engine.diagnose_crop_leaf(self.valid_leaf_path, user_selected_crop="Tomato")
        self.assertTrue(res["success"])
        self.assertTrue(res["quality_passed"])
        self.assertIn("Tomato", res["crop"])
        self.assertGreaterEqual(res["confidence"], 80.0)
        
        # Verify 4-pillar treatments
        self.assertIn("chemical_treatment", res)
        self.assertIn("active_ingredient", res["chemical_treatment"])
        self.assertIn("phi_days", res["chemical_treatment"])
        self.assertIn("frac_code", res["chemical_treatment"])

        self.assertIn("biological_treatment", res)
        self.assertIn("organic_treatment", res)
        self.assertIn("cultural_treatment", res)
        self.assertIn("differential_diagnoses", res)
        self.assertGreaterEqual(len(res["differential_diagnoses"]), 1)

    def test_quality_underexposure_check(self):
        res = diagnosis_engine.diagnose_crop_leaf(self.dark_path, user_selected_crop="Tomato")
        self.assertFalse(res["success"])
        self.assertFalse(res["quality_passed"])
        self.assertEqual(res["failure_type"], "underexposed")
        self.assertGreater(len(res["retake_instructions"]), 0)

    def test_quality_overexposure_check(self):
        res = diagnosis_engine.diagnose_crop_leaf(self.bright_path, user_selected_crop="Tomato")
        self.assertFalse(res["success"])
        self.assertFalse(res["quality_passed"])
        self.assertEqual(res["failure_type"], "overexposed")
        self.assertGreater(len(res["retake_instructions"]), 0)

    def test_quality_non_plant_check(self):
        res = diagnosis_engine.diagnose_crop_leaf(self.non_plant_path, user_selected_crop="Tomato")
        self.assertFalse(res["success"])
        self.assertFalse(res["quality_passed"])
        self.assertEqual(res["failure_type"], "non_plant")
        self.assertGreater(len(res["retake_instructions"]), 0)

    def test_fertilizer_unit_conversions(self):
        # 1 Hectare = 2.471 Acres
        plan_ha = fertilizer_calculator.calculate_fertilizer("Tomato", 1.0, unit="Hectares")
        plan_ac = fertilizer_calculator.calculate_fertilizer("Tomato", 2.471, unit="Acres")
        self.assertTrue(plan_ha["success"])
        self.assertAlmostEqual(plan_ha["normalized_acres"], plan_ac["normalized_acres"], delta=0.1)

    def test_fertilizer_invalid_inputs(self):
        res_zero = fertilizer_calculator.calculate_fertilizer("Tomato", 0)
        self.assertFalse(res_zero["success"])
        self.assertIn("error", res_zero)

        res_neg = fertilizer_calculator.calculate_fertilizer("Tomato", -2.5)
        self.assertFalse(res_neg["success"])

        res_text = fertilizer_calculator.calculate_fertilizer("Tomato", "invalid_area")
        self.assertFalse(res_text["success"])

    def test_weather_7day_and_spray_window(self):
        w = weather_service.get_forecast()
        self.assertIn("current", w)
        self.assertIn("agri_advisory", w)
        self.assertIn("spray_condition", w["agri_advisory"])
        self.assertIn("forecast_days", w)
        self.assertEqual(len(w["forecast_days"]), 7)
        self.assertIn("spray_hours_next_24", w)
        self.assertGreater(len(w["spray_hours_next_24"]), 0)

    def test_agronomist_chatbot_routing(self):
        resp_yellow = consult_ai_agronomist("Why are my chili leaves yellowing?")
        self.assertIn("yellowing", resp_yellow.lower())

        resp_spray = consult_ai_agronomist("What is the best spraying time?")
        self.assertIn("spraying", resp_spray.lower())

    def test_rag_retriever_query_and_citations(self):
        # Query late blight in potato / tomato
        docs = rag_retriever.retrieve("late blight fungicide spray protocol", crop="Potato", top_k=2)
        self.assertGreater(len(docs), 0)
        top_doc = docs[0]
        self.assertIn("content", top_doc)
        self.assertIn("citation", top_doc)
        self.assertTrue(len(top_doc["citation"]) > 0)

    def test_agronomist_engine_contextual_response(self):
        context = {
            "crop": "Tomato",
            "growth_stage": "Flowering",
            "farm": "North Field",
            "weather": {"temp": "28°C", "condition": "High Humidity (88%)"}
        }
        res = agronomist_engine.generate_response(
            "My tomato plants have black water-soaked patches on leaves. What should I spray?",
            context=context
        )
        self.assertIn("reply", res)
        self.assertIn("citations", res)
        self.assertGreater(len(res["citations"]), 0)
        self.assertIn("suggested_followups", res)
        self.assertGreater(len(res["suggested_followups"]), 0)
        self.assertIn("safety_disclaimer", res)

    def test_symptom_localization_boxes(self):
        res = diagnosis_engine.diagnose_crop_leaf(self.valid_leaf_path, user_selected_crop="Tomato")
        self.assertTrue(res["success"])
        self.assertIn("symptom_localization", res)
        loc = res["symptom_localization"]
        self.assertIn("boxes", loc)
        self.assertGreater(len(loc["boxes"]), 0)
        box = loc["boxes"][0]
        self.assertIn("box_2d", box)
        self.assertEqual(len(box["box_2d"]), 4)
        self.assertIn("label", box)
        self.assertIn("confidence", box)

if __name__ == '__main__':
    unittest.main()
