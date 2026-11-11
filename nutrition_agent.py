"""
nutrition_agent.py
Core AI Nutrition Agent – orchestrates IBM Granite to deliver:
  • Personalised meal plans
  • Smart food swaps
  • Nutritional explanations
  • Conversational Q&A
  • Adaptive suggestions based on feedback
"""

from granite_client import granite
from user_profile import UserProfile


# ── Prompt templates ──────────────────────────────────────────────────────────

SYSTEM_PERSONA = """You are NutriAI, an expert AI Nutrition Assistant powered by IBM Granite.
You are knowledgeable, empathetic, and evidence-based. You always:
- Tailor recommendations to the individual's health profile, goals, and cultural preferences
- Respect allergies, intolerances, and medical conditions absolutely
- Explain the nutritional science behind your suggestions clearly
- Provide practical, affordable, and culturally appropriate options
- Encourage balanced, sustainable eating rather than extreme diets
- Always remind users to consult a registered dietician for medical nutrition therapy

User Profile:
{profile_context}
"""

MEAL_PLAN_PROMPT = """{system}

TASK: Generate a detailed {days}-day personalised meal plan.

Requirements:
- Include {meals_per_day} meals per day (plus snacks if appropriate)
- Match the calorie target of approximately {calories} kcal/day
- Respect all dietary restrictions: {dietary_preference}
- Avoid all allergens: {allergies}
- Incorporate preferred cuisines where possible: {cuisines}
- Align with health goal: {health_goal}
- Include estimated calories, protein, carbs, and fat per meal
- Add a brief shopping list at the end
- Add hydration tips

Format each day clearly with Day X header and meal sections.

Generate the complete {days}-day meal plan now:"""

FOOD_SWAP_PROMPT = """{system}

TASK: Suggest smart food swaps for the foods listed below.

Foods to swap: {foods}
Reason for swap: {reason}

For each food, provide:
1. The recommended healthier alternative
2. Nutritional comparison (calories, key macros)
3. Why this swap benefits the user given their profile
4. Preparation tips for the alternative
5. Any caveats or considerations

Be specific, practical, and encouraging.

Smart food swap analysis:"""

EXPLAIN_FOOD_PROMPT = """{system}

TASK: Explain the nutritional value and health impact of the following food/meal.

Food/Meal: {food}

Provide:
1. Complete nutritional breakdown (macros + key micronutrients)
2. Health benefits relevant to this user's goals
3. Potential concerns given their medical conditions/allergies
4. Optimal preparation methods to preserve nutrition
5. Best time of day to consume
6. Portion size recommendations
7. Foods that pair well for enhanced nutrition

Use clear, accessible language while being scientifically accurate.

Nutritional explanation:"""

CHAT_PROMPT = """{system}

CONVERSATION HISTORY:
{history}

USER: {user_message}

NUTRIAI:"""

IMAGE_FOOD_PROMPT = """{system}

TASK: Analyse the following food information extracted from an image/label.

Extracted text from image:
{extracted_text}

Please:
1. Identify the food item(s) present
2. Provide a nutritional assessment
3. Rate its healthiness for this user (1-10) with explanation
4. Suggest improvements or healthier alternatives
5. Highlight any ingredients the user should be aware of given their allergies/conditions

Analysis:"""

ADAPTIVE_SUGGESTION_PROMPT = """{system}

Based on the user's feedback history and preferences, generate adaptive meal suggestions.

Recent feedback summary:
{feedback_summary}

TASK: Suggest 5 meals the user would likely enjoy and that align with their health goals,
taking into account what they have liked and disliked previously.
For each suggestion include: meal name, brief description, estimated nutrition, and why it suits them.

Personalised suggestions:"""


# ── Agent class ───────────────────────────────────────────────────────────────

class NutritionAgent:
    """
    Orchestrates all nutrition AI capabilities using IBM Granite.
    """

    def __init__(self):
        self.client = granite

    # ── Meal Plan ─────────────────────────────────────────────────────────────

    def generate_meal_plan(self, profile: UserProfile, days: int = 7) -> str:
        """Generate a personalised multi-day meal plan."""
        calories = profile.daily_calories() or 2000
        system   = SYSTEM_PERSONA.format(profile_context=profile.to_prompt_context())

        prompt = MEAL_PLAN_PROMPT.format(
            system=system,
            days=days,
            meals_per_day=profile.meals_per_day,
            calories=calories,
            dietary_preference=profile.dietary_preference or "no specific restriction",
            allergies=", ".join(profile.allergies) if profile.allergies else "none",
            cuisines=", ".join(profile.preferred_cuisines) if profile.preferred_cuisines else "any",
            health_goal=profile.health_goal.replace("_", " "),
        )
        return self.client.generate(prompt, max_tokens=2048)

    # ── Food Swaps ────────────────────────────────────────────────────────────

    def suggest_food_swaps(self, profile: UserProfile, foods: list, reason: str = "") -> str:
        """Suggest healthier alternatives for the given foods."""
        system = SYSTEM_PERSONA.format(profile_context=profile.to_prompt_context())
        prompt = FOOD_SWAP_PROMPT.format(
            system=system,
            foods=", ".join(foods),
            reason=reason or f"to better support {profile.health_goal.replace('_', ' ')} goals",
        )
        return self.client.generate(prompt, max_tokens=1500)

    # ── Nutritional Explanation ───────────────────────────────────────────────

    def explain_food(self, profile: UserProfile, food: str) -> str:
        """Provide a detailed nutritional explanation for a food or meal."""
        system = SYSTEM_PERSONA.format(profile_context=profile.to_prompt_context())
        prompt = EXPLAIN_FOOD_PROMPT.format(
            system=system,
            food=food,
        )
        return self.client.generate(prompt, max_tokens=1200)

    # ── Conversational Q&A ────────────────────────────────────────────────────

    def chat(self, profile: UserProfile, user_message: str, history: list) -> str:
        """
        Handle a free-form nutrition question in a conversational manner.
        history: list of {"role": "user"|"assistant", "content": str}
        """
        system = SYSTEM_PERSONA.format(profile_context=profile.to_prompt_context())

        # Format last 6 turns to keep context manageable
        recent = history[-6:] if len(history) > 6 else history
        history_str = "\n".join(
            f"{'USER' if m['role'] == 'user' else 'NUTRIAI'}: {m['content']}"
            for m in recent
        )

        prompt = CHAT_PROMPT.format(
            system=system,
            history=history_str,
            user_message=user_message,
        )
        return self.client.generate(prompt, max_tokens=800)

    # ── Image / Label Analysis ────────────────────────────────────────────────

    def analyse_image_text(self, profile: UserProfile, extracted_text: str) -> str:
        """Analyse food info extracted from an image/label."""
        system = SYSTEM_PERSONA.format(profile_context=profile.to_prompt_context())
        prompt = IMAGE_FOOD_PROMPT.format(
            system=system,
            extracted_text=extracted_text,
        )
        return self.client.generate(prompt, max_tokens=1200)

    # ── Adaptive Suggestions ──────────────────────────────────────────────────

    def get_adaptive_suggestions(self, profile: UserProfile) -> str:
        """Generate personalised suggestions based on feedback history."""
        if not profile.feedback_history:
            return self.chat(
                profile,
                "Suggest 5 healthy meals that would be great for me to try this week.",
                []
            )

        likes    = [f['item'] for f in profile.feedback_history if f.get('rating', 5) >= 4]
        dislikes = [f['item'] for f in profile.feedback_history if f.get('rating', 5) <= 2]
        feedback_summary = (
            f"Liked: {', '.join(likes[-5:]) if likes else 'nothing recorded yet'}\n"
            f"Disliked: {', '.join(dislikes[-5:]) if dislikes else 'nothing recorded yet'}"
        )

        system = SYSTEM_PERSONA.format(profile_context=profile.to_prompt_context())
        prompt = ADAPTIVE_SUGGESTION_PROMPT.format(
            system=system,
            feedback_summary=feedback_summary,
        )
        return self.client.generate(prompt, max_tokens=1000)


# Singleton agent
agent = NutritionAgent()
