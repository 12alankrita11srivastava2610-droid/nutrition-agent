"""
user_profile.py
In-memory user profile store with session-based persistence.
Holds health data, preferences, allergies, and feedback history.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import json


# ── Supported categories ───────────────────────────────────────────────────────

HEALTH_GOALS = [
    "weight_loss", "weight_gain", "muscle_building",
    "maintenance", "heart_health", "diabetes_management",
    "gut_health", "energy_boost", "athletic_performance",
]

DIETARY_PREFERENCES = [
    "none", "vegetarian", "vegan", "pescatarian",
    "keto", "paleo", "mediterranean", "gluten_free",
    "dairy_free", "halal", "kosher", "jain",
]

ACTIVITY_LEVELS = ["sedentary", "lightly_active", "moderately_active", "very_active", "extra_active"]

CUISINES = [
    "Indian", "Mediterranean", "East Asian", "Mexican", "Italian",
    "Middle Eastern", "American", "Japanese", "Thai", "African",
]


@dataclass
class UserProfile:
    """Complete user health & preference profile."""

    # ── Demographics ──────────────────────────────────────────────────────────
    name:             str  = "User"
    age:              Optional[int]   = None
    gender:           Optional[str]   = None        # male / female / other
    height_cm:        Optional[float] = None
    weight_kg:        Optional[float] = None
    target_weight_kg: Optional[float] = None

    # ── Health ────────────────────────────────────────────────────────────────
    health_goal:      str  = "maintenance"
    activity_level:   str  = "moderately_active"
    medical_conditions: List[str] = field(default_factory=list)
    # e.g. ["diabetes_type2", "hypertension", "lactose_intolerance"]

    # ── Food preferences ──────────────────────────────────────────────────────
    dietary_preference: str  = "none"
    allergies:          List[str] = field(default_factory=list)
    # e.g. ["peanuts", "shellfish", "gluten"]
    disliked_foods:     List[str] = field(default_factory=list)
    preferred_cuisines: List[str] = field(default_factory=list)
    meals_per_day:      int = 3

    # ── Fitness ───────────────────────────────────────────────────────────────
    fitness_routine:    str = ""      # free-text description

    # ── Feedback history (for adaptive learning) ──────────────────────────────
    feedback_history:   List[Dict[str, Any]] = field(default_factory=list)

    # ── Computed properties ───────────────────────────────────────────────────

    def bmi(self) -> Optional[float]:
        if self.height_cm and self.weight_kg:
            h = self.height_cm / 100
            return round(self.weight_kg / (h * h), 1)
        return None

    def bmi_category(self) -> str:
        bmi = self.bmi()
        if bmi is None:
            return "unknown"
        if bmi < 18.5:
            return "Underweight"
        if bmi < 25.0:
            return "Normal weight"
        if bmi < 30.0:
            return "Overweight"
        return "Obese"

    def daily_calories(self) -> Optional[int]:
        """Estimate TDEE using Mifflin-St Jeor + activity multiplier."""
        if not all([self.age, self.height_cm, self.weight_kg, self.gender]):
            return None
        if self.gender and self.gender.lower() in ("male", "m"):
            bmr = 10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age + 5
        else:
            bmr = 10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age - 161
        multipliers = {
            "sedentary": 1.2,
            "lightly_active": 1.375,
            "moderately_active": 1.55,
            "very_active": 1.725,
            "extra_active": 1.9,
        }
        factor = multipliers.get(self.activity_level, 1.55)
        tdee = int(bmr * factor)
        if self.health_goal == "weight_loss":
            return max(1200, tdee - 500)
        if self.health_goal == "weight_gain":
            return tdee + 500
        if self.health_goal == "muscle_building":
            return tdee + 300
        return tdee

    def add_feedback(self, feedback_type: str, item: str, rating: int, note: str = ""):
        """Record user feedback for adaptive recommendations."""
        self.feedback_history.append({
            "type":  feedback_type,   # "meal" | "swap" | "plan"
            "item":  item,
            "rating": rating,         # 1-5
            "note":  note,
        })
        # Keep only last 50 entries
        if len(self.feedback_history) > 50:
            self.feedback_history = self.feedback_history[-50:]

    def to_dict(self) -> dict:
        return asdict(self)

    def to_prompt_context(self) -> str:
        """Format profile as a concise context string for Granite prompts."""
        parts = []
        if self.name and self.name != "User":
            parts.append(f"Name: {self.name}")
        if self.age:
            parts.append(f"Age: {self.age}")
        if self.gender:
            parts.append(f"Gender: {self.gender}")
        if self.height_cm and self.weight_kg:
            parts.append(f"Height: {self.height_cm}cm, Weight: {self.weight_kg}kg, BMI: {self.bmi()} ({self.bmi_category()})")
        if self.target_weight_kg:
            parts.append(f"Target weight: {self.target_weight_kg}kg")
        parts.append(f"Health goal: {self.health_goal.replace('_', ' ').title()}")
        parts.append(f"Activity level: {self.activity_level.replace('_', ' ').title()}")
        if self.medical_conditions:
            parts.append(f"Medical conditions: {', '.join(self.medical_conditions)}")
        parts.append(f"Dietary preference: {self.dietary_preference.replace('_', ' ').title()}")
        if self.allergies:
            parts.append(f"Allergies/Intolerances: {', '.join(self.allergies)}")
        if self.disliked_foods:
            parts.append(f"Dislikes: {', '.join(self.disliked_foods)}")
        if self.preferred_cuisines:
            parts.append(f"Preferred cuisines: {', '.join(self.preferred_cuisines)}")
        parts.append(f"Meals per day: {self.meals_per_day}")
        if self.fitness_routine:
            parts.append(f"Fitness routine: {self.fitness_routine}")
        cal = self.daily_calories()
        if cal:
            parts.append(f"Estimated daily calorie target: {cal} kcal")
        if self.feedback_history:
            dislikes = [f['item'] for f in self.feedback_history if f.get('rating', 5) <= 2]
            likes    = [f['item'] for f in self.feedback_history if f.get('rating', 0) >= 4]
            if likes:
                parts.append(f"Previously liked: {', '.join(likes[-5:])}")
            if dislikes:
                parts.append(f"Previously disliked: {', '.join(dislikes[-5:])}")
        return "\n".join(parts)

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Simple session-based profile store ────────────────────────────────────────

_profiles: Dict[str, UserProfile] = {}


def get_profile(session_id: str) -> UserProfile:
    if session_id not in _profiles:
        _profiles[session_id] = UserProfile()
    return _profiles[session_id]


def update_profile(session_id: str, data: dict) -> UserProfile:
    profile = get_profile(session_id)
    allowed = UserProfile.__dataclass_fields__.keys()
    for key, value in data.items():
        if key in allowed and key != "feedback_history":
            setattr(profile, key, value)
    return profile


def delete_profile(session_id: str):
    _profiles.pop(session_id, None)
