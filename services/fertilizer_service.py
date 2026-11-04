# Precision Fertilizer & Nutrient Calculator (Phase 2 Enhanced)

UNIT_TO_ACRES = {
    "acre": 1.0,
    "acres": 1.0,
    "hectare": 2.47105,
    "hectares": 2.47105,
    "guntha": 0.025,
    "gunthas": 0.025,
    "bigha": 0.625,
    "bighas": 0.625
}

RECOMMENDED_DOSES = {
    "Tomato": {"N": 60, "P": 40, "K": 40, "name": "Tomato (Hybrid F1)", "base_yield_tons": 25},
    "Potato": {"N": 50, "P": 40, "K": 50, "name": "Potato (Commercial)", "base_yield_tons": 18},
    "Chili": {"N": 40, "P": 25, "K": 25, "name": "Chili / Hot Pepper", "base_yield_tons": 8},
    "Corn": {"N": 50, "P": 25, "K": 20, "name": "Maize / Corn", "base_yield_tons": 3.5},
    "Rice": {"N": 45, "P": 20, "K": 20, "name": "Paddy / Rice", "base_yield_tons": 3.0},
    "Cotton": {"N": 40, "P": 20, "K": 20, "name": "Cotton (Bt)", "base_yield_tons": 1.5},
    "Cabbage": {"N": 60, "P": 35, "K": 35, "name": "Cabbage / Cauliflower", "base_yield_tons": 20},
    "Banana": {"N": 80, "P": 30, "K": 90, "name": "Banana (Grand Naine)", "base_yield_tons": 35}
}

class FertilizerCalculator:
    @staticmethod
    def convert_area_to_acres(area_value, unit="Acres"):
        unit_clean = (unit or "Acres").lower().strip()
        conversion_factor = UNIT_TO_ACRES.get(unit_clean, 1.0)
        return float(area_value) * conversion_factor

    @classmethod
    def calculate_fertilizer(cls, crop_name, area, unit="Acres", growth_stage="All Stages", soil_test=None, target_yield=None):
        """
        Validates inputs, converts units to standardized acres, applies soil test adjustments
        and growth stage focus, and returns nutrient breakdown with commercial bag estimates.
        """
        # Input validation
        try:
            area_float = float(area)
            if area_float <= 0:
                return {"success": False, "error": "Field area must be a positive number greater than 0."}
            if area_float > 500:
                return {"success": False, "error": "Field area exceeds maximum supported single plot limit (500 units)."}
        except (ValueError, TypeError):
            return {"success": False, "error": "Invalid area value. Please enter a valid numerical area."}

        unit_str = str(unit or "Acres").capitalize()
        norm_acres = cls.convert_area_to_acres(area_float, unit_str)

        # Match crop
        norm_crop = "Tomato"
        for key in RECOMMENDED_DOSES:
            if key.lower() in crop_name.lower():
                norm_crop = key
                break
                
        rec = RECOMMENDED_DOSES[norm_crop]
        base_n = rec["N"] * norm_acres
        base_p = rec["P"] * norm_acres
        base_k = rec["K"] * norm_acres

        # Adjust for soil test values if available
        soil_adjustments = {"N": "Standard (100%)", "P": "Standard (100%)", "K": "Standard (100%)"}
        if soil_test:
            n_status = soil_test.get("nitrogen", "Medium")
            p_status = soil_test.get("phosphorus", "Medium")
            k_status = soil_test.get("potassium", "Medium")

            if n_status == "Low": 
                base_n *= 1.25; soil_adjustments["N"] = "Low Soil N (+25% Dosage)"
            elif n_status == "High": 
                base_n *= 0.75; soil_adjustments["N"] = "High Soil N (-25% Dosage)"
                
            if p_status == "Low": 
                base_p *= 1.25; soil_adjustments["P"] = "Low Soil P (+25% Dosage)"
            elif p_status == "High": 
                base_p *= 0.75; soil_adjustments["P"] = "High Soil P (-25% Dosage)"
                
            if k_status == "Low": 
                base_k *= 1.25; soil_adjustments["K"] = "Low Soil K (+25% Dosage)"
            elif k_status == "High": 
                base_k *= 0.75; soil_adjustments["K"] = "High Soil K (-25% Dosage)"

        # Target yield scaling (if target yield specified)
        if target_yield and float(target_yield) > 0:
            yield_multiplier = float(target_yield) / float(rec["base_yield_tons"])
            yield_multiplier = max(0.8, min(1.4, yield_multiplier)) # Restrict realistic agronomic bounds
            base_n *= yield_multiplier
            base_p *= yield_multiplier
            base_k *= yield_multiplier

        # Chemistry Conversion:
        # 1. DAP (18-46-0) supplies all Phosphorus (46% P2O5)
        dap_kg = round(base_p / 0.46, 1)
        n_supplied_by_dap = dap_kg * 0.18

        # 2. Urea (46% N) supplies remaining Nitrogen
        rem_n = max(0.0, base_n - n_supplied_by_dap)
        urea_kg = round(rem_n / 0.46, 1)

        # 3. MOP (60% K2O) supplies all Potassium
        mop_kg = round(base_k / 0.60, 1)

        # Bag conversion
        urea_bags = round(urea_kg / 45.0, 1)
        dap_bags = round(dap_kg / 50.0, 1)
        mop_bags = round(mop_kg / 50.0, 1)

        # Subsidized Indicative Cost (Government of India DBT subsidized baseline prices)
        # Urea: ~₹268 per 45kg bag; DAP: ~₹1350 per 50kg bag; MOP: ~₹1700 per 50kg bag
        est_cost = int(round((urea_bags * 268) + (dap_bags * 1350) + (mop_bags * 1700)))

        # Split Application Schedule
        schedule = [
            {
                "stage": "Basal Dose (Final Land Preparation & Transplanting)",
                "timing": "Day 0",
                "urea_kg": round(urea_kg * 0.25, 1),
                "dap_kg": dap_kg, # 100% DAP applied at basal because phosphorus is immobile in soil
                "mop_kg": round(mop_kg * 0.50, 1),
                "method": "Soil placement 5-7 cm below and beside seed/transplant furrow.",
                "agronomic_rationale": "Phosphorus establishes rapid root architecture. 50% Potash builds early cell wall strength."
            },
            {
                "stage": "1st Top Dressing (Active Vegetative Tillering & Branching)",
                "timing": "25-30 Days After Sowing",
                "urea_kg": round(urea_kg * 0.40, 1),
                "dap_kg": 0.0,
                "mop_kg": 0.0,
                "method": "Band placement followed by immediate light irrigation or drip fertigation.",
                "agronomic_rationale": "High nitrogen demand for canopy expansion and chlorophyll synthesis."
            },
            {
                "stage": "2nd Top Dressing (Flowering & Fruit/Tuber Setting)",
                "timing": "50-55 Days After Sowing",
                "urea_kg": round(urea_kg * 0.35, 1),
                "dap_kg": 0.0,
                "mop_kg": round(mop_kg * 0.50, 1),
                "method": "Foliar side band or venturi injection. Avoid direct contact with stem collar.",
                "agronomic_rationale": "Potassium drives carbohydrate translocation to filling fruits/tubers."
            }
        ]

        calculation_explanation = (
            f"For {area_float} {unit_str} ({round(norm_acres, 2)} normalized acres) of {rec['name']}, "
            f"target elemental requirement is {round(base_n, 1)} kg N, {round(base_p, 1)} kg P₂O₅, and {round(base_k, 1)} kg K₂O. "
            f"Phosphorus is supplied entirely by DAP (which additionally supplies {round(n_supplied_by_dap, 1)} kg N). "
            f"The remaining nitrogen is supplied via subsidized 46% Urea. Potassium is supplied via 60% MOP. "
            f"Application is split across 3 physiological stages to avoid leaching."
        )

        return {
            "success": True,
            "crop": norm_crop,
            "crop_display": rec["name"],
            "input_area": area_float,
            "input_unit": unit_str,
            "normalized_acres": round(norm_acres, 2),
            "target_npk_kg": {
                "N": round(base_n, 1),
                "P": round(base_p, 1),
                "K": round(base_k, 1)
            },
            "commercial_fertilizers": {
                "urea_kg": urea_kg,
                "urea_bags": urea_bags,
                "dap_kg": dap_kg,
                "dap_bags": dap_bags,
                "mop_kg": mop_kg,
                "mop_bags": mop_bags
            },
            "soil_adjustments": soil_adjustments,
            "schedule": schedule,
            "calculation_explanation": calculation_explanation,
            "estimated_cost_inr": est_cost,
            "cost_disclaimer": "Cost estimate is based on prevailing central government subsidized MRP guidelines and may vary by cooperative society or local transport freight."
        }

fertilizer_calculator = FertilizerCalculator()
