"""
food_database.py
Built-in nutritional reference data and USDA/Nutritionix API integration.
Provides calorie lookup, macro data, and food search capabilities.
"""

import os
import json
import requests
from typing import Optional, Dict, List

NUTRITIONIX_APP_ID  = os.getenv("NUTRITIONIX_APP_ID", "")
NUTRITIONIX_API_KEY = os.getenv("NUTRITIONIX_API_KEY", "")
USDA_API_KEY        = os.getenv("USDA_API_KEY", "")

# ── Built-in common foods reference (per 100g) ────────────────────────────────
COMMON_FOODS: Dict[str, Dict] = {
    "apple":           {"calories": 52,  "protein": 0.3, "carbs": 14.0, "fat": 0.2, "fiber": 2.4},
    "banana":          {"calories": 89,  "protein": 1.1, "carbs": 23.0, "fat": 0.3, "fiber": 2.6},
    "chicken breast":  {"calories": 165, "protein": 31.0,"carbs": 0.0,  "fat": 3.6, "fiber": 0.0},
    "brown rice":      {"calories": 216, "protein": 4.5, "carbs": 45.0, "fat": 1.8, "fiber": 3.5},
    "white rice":      {"calories": 206, "protein": 4.3, "carbs": 45.0, "fat": 0.4, "fiber": 0.6},
    "broccoli":        {"calories": 34,  "protein": 2.8, "carbs": 7.0,  "fat": 0.4, "fiber": 2.6},
    "salmon":          {"calories": 208, "protein": 20.0,"carbs": 0.0,  "fat": 13.0,"fiber": 0.0},
    "egg":             {"calories": 155, "protein": 13.0,"carbs": 1.1,  "fat": 11.0,"fiber": 0.0},
    "oats":            {"calories": 389, "protein": 17.0,"carbs": 66.0, "fat": 7.0, "fiber": 11.0},
    "lentils":         {"calories": 116, "protein": 9.0, "carbs": 20.0, "fat": 0.4, "fiber": 8.0},
    "spinach":         {"calories": 23,  "protein": 2.9, "carbs": 3.6,  "fat": 0.4, "fiber": 2.2},
    "almonds":         {"calories": 579, "protein": 21.0,"carbs": 22.0, "fat": 50.0,"fiber": 12.5},
    "sweet potato":    {"calories": 86,  "protein": 1.6, "carbs": 20.0, "fat": 0.1, "fiber": 3.0},
    "greek yogurt":    {"calories": 59,  "protein": 10.0,"carbs": 3.6,  "fat": 0.4, "fiber": 0.0},
    "avocado":         {"calories": 160, "protein": 2.0, "carbs": 9.0,  "fat": 15.0,"fiber": 7.0},
    "quinoa":          {"calories": 222, "protein": 8.1, "carbs": 39.0, "fat": 3.6, "fiber": 5.2},
    "tofu":            {"calories": 76,  "protein": 8.1, "carbs": 1.9,  "fat": 4.8, "fiber": 0.3},
    "whole wheat bread":{"calories": 247,"protein": 13.0,"carbs": 41.0, "fat": 3.4, "fiber": 7.0},
    "olive oil":       {"calories": 884, "protein": 0.0, "carbs": 0.0,  "fat": 100.0,"fiber": 0.0},
    "milk (whole)":    {"calories": 61,  "protein": 3.2, "carbs": 4.8,  "fat": 3.3, "fiber": 0.0},
    "orange":          {"calories": 47,  "protein": 0.9, "carbs": 12.0, "fat": 0.1, "fiber": 2.4},
    "blueberries":     {"calories": 57,  "protein": 0.7, "carbs": 14.0, "fat": 0.3, "fiber": 2.4},
    "kale":            {"calories": 49,  "protein": 4.3, "carbs": 9.0,  "fat": 0.9, "fiber": 3.6},
    "chickpeas":       {"calories": 164, "protein": 8.9, "carbs": 27.0, "fat": 2.6, "fiber": 7.6},
    "tuna (canned)":   {"calories": 116, "protein": 26.0,"carbs": 0.0,  "fat": 1.0, "fiber": 0.0},
    "beef (lean)":     {"calories": 250, "protein": 26.0,"carbs": 0.0,  "fat": 15.0,"fiber": 0.0},
    "cottage cheese":  {"calories": 98,  "protein": 11.0,"carbs": 3.4,  "fat": 4.3, "fiber": 0.0},
    "walnuts":         {"calories": 654, "protein": 15.0,"carbs": 14.0, "fat": 65.0,"fiber": 6.7},
    "cauliflower":     {"calories": 25,  "protein": 1.9, "carbs": 5.0,  "fat": 0.3, "fiber": 2.0},
    "cucumber":        {"calories": 15,  "protein": 0.7, "carbs": 3.6,  "fat": 0.1, "fiber": 0.5},
}


def lookup_food_local(food_name: str) -> Optional[Dict]:
    """Search the built-in food database (case-insensitive partial match)."""
    food_lower = food_name.lower().strip()
    # Exact match first
    if food_lower in COMMON_FOODS:
        return {"name": food_lower, **COMMON_FOODS[food_lower], "source": "built-in"}
    # Partial match
    for key, data in COMMON_FOODS.items():
        if food_lower in key or key in food_lower:
            return {"name": key, **data, "source": "built-in"}
    return None


def lookup_food_nutritionix(food_name: str) -> Optional[Dict]:
    """Query the Nutritionix API for nutritional data."""
    if not NUTRITIONIX_APP_ID or NUTRITIONIX_APP_ID == "your_nutritionix_app_id_here":
        return None

    try:
        url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
        headers = {
            "x-app-id":  NUTRITIONIX_APP_ID,
            "x-app-key": NUTRITIONIX_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {"query": food_name}
        response = requests.post(url, headers=headers, json=payload, timeout=8)
        if response.status_code == 200:
            data = response.json()
            foods = data.get("foods", [])
            if foods:
                f = foods[0]
                return {
                    "name":     f.get("food_name", food_name),
                    "calories": f.get("nf_calories", 0),
                    "protein":  f.get("nf_protein", 0),
                    "carbs":    f.get("nf_total_carbohydrate", 0),
                    "fat":      f.get("nf_total_fat", 0),
                    "fiber":    f.get("nf_dietary_fiber", 0),
                    "serving":  f.get("serving_qty", 1),
                    "unit":     f.get("serving_unit", "serving"),
                    "source":   "Nutritionix",
                }
    except Exception:
        pass
    return None


def lookup_food_usda(food_name: str) -> Optional[Dict]:
    """Query the USDA FoodData Central API."""
    if not USDA_API_KEY or USDA_API_KEY == "your_usda_api_key_here":
        return None

    try:
        search_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
        params = {"query": food_name, "api_key": USDA_API_KEY, "pageSize": 1}
        response = requests.get(search_url, params=params, timeout=8)
        if response.status_code == 200:
            data = response.json()
            foods = data.get("foods", [])
            if foods:
                f = foods[0]
                nutrients = {n["nutrientName"]: n["value"] for n in f.get("foodNutrients", [])}
                return {
                    "name":     f.get("description", food_name),
                    "calories": nutrients.get("Energy", 0),
                    "protein":  nutrients.get("Protein", 0),
                    "carbs":    nutrients.get("Carbohydrate, by difference", 0),
                    "fat":      nutrients.get("Total lipid (fat)", 0),
                    "fiber":    nutrients.get("Fiber, total dietary", 0),
                    "source":   "USDA FoodData Central",
                }
    except Exception:
        pass
    return None


def lookup_food(food_name: str) -> Dict:
    """
    Unified food lookup: tries built-in → Nutritionix → USDA.
    Always returns a dict (with error key if not found).
    """
    result = lookup_food_local(food_name)
    if result:
        return result

    result = lookup_food_nutritionix(food_name)
    if result:
        return result

    result = lookup_food_usda(food_name)
    if result:
        return result

    return {"name": food_name, "error": "Food not found in database", "source": "none"}


def format_nutrition_card(food_data: Dict) -> str:
    """Format nutritional data as a readable text card."""
    if "error" in food_data:
        return f"Could not find nutritional data for: {food_data.get('name', 'unknown')}"

    lines = [
        f"**{food_data.get('name', 'Food').title()}** (per 100g / serving)",
        f"• Calories: {food_data.get('calories', 'N/A')} kcal",
        f"• Protein:  {food_data.get('protein', 'N/A')} g",
        f"• Carbs:    {food_data.get('carbs', 'N/A')} g",
        f"• Fat:      {food_data.get('fat', 'N/A')} g",
        f"• Fiber:    {food_data.get('fiber', 'N/A')} g",
        f"*Source: {food_data.get('source', 'unknown')}*",
    ]
    return "\n".join(lines)


def search_foods(query: str, limit: int = 5) -> List[Dict]:
    """Return a list of matching foods from the built-in database."""
    query_lower = query.lower().strip()
    matches = []
    for name, data in COMMON_FOODS.items():
        if query_lower in name:
            matches.append({"name": name, **data})
        if len(matches) >= limit:
            break
    return matches
