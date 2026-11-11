"""
granite_client.py
IBM Granite (watsonx.ai) client – wraps the ibm-watsonx-ai SDK
and exposes a single `generate()` helper used throughout the agent.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── IBM watsonx.ai SDK ────────────────────────────────────────────────────────
try:
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False


# ── Configuration ─────────────────────────────────────────────────────────────
IBM_API_KEY      = os.getenv("IBM_API_KEY", "")
IBM_WATSONX_URL  = os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
IBM_PROJECT_ID   = os.getenv("IBM_PROJECT_ID", "")
GRANITE_MODEL_ID = os.getenv("IBM_GRANITE_MODEL_ID", "ibm/granite-3-1-8b-base")

# Default generation parameters
DEFAULT_PARAMS = {
    "max_new_tokens": 1024,
    "min_new_tokens": 10,
    "temperature":    0.7,
    "top_k":          50,
    "top_p":          0.95,
    "repetition_penalty": 1.1,
    "stop_sequences": ["<|endoftext|>"],
}


class GraniteClient:
    """
    Thin wrapper around IBM watsonx.ai ModelInference for Granite models.
    Falls back to a descriptive stub when the SDK is unavailable or keys
    are not yet configured – keeping the app runnable for demo purposes.
    """

    def __init__(self):
        self._model = None
        self._ready = False
        self._init_model()

    def _init_model(self):
        if not _SDK_AVAILABLE:
            print("[GraniteClient] ibm-watsonx-ai SDK not installed – using stub mode.")
            return

        if not IBM_API_KEY or IBM_API_KEY == "your_ibm_api_key_here":
            print("[GraniteClient] IBM_API_KEY not configured – using stub mode.")
            return

        if not IBM_PROJECT_ID or IBM_PROJECT_ID == "your_project_id_here":
            print("[GraniteClient] IBM_PROJECT_ID not configured – using stub mode.")
            return

        try:
            credentials = Credentials(
                url=IBM_WATSONX_URL,
                api_key=IBM_API_KEY,
            )
            self._model = ModelInference(
                model_id=GRANITE_MODEL_ID,
                credentials=credentials,
                project_id=IBM_PROJECT_ID,
                params=DEFAULT_PARAMS,
            )
            self._ready = True
            print(f"[GraniteClient] Connected to IBM Granite model: {GRANITE_MODEL_ID}")
        except Exception as exc:
            print(f"[GraniteClient] Initialisation failed: {exc} – using stub mode.")

    # ── Public API ─────────────────────────────────────────────────────────────

    def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """
        Send a prompt to IBM Granite and return the generated text.
        Uses stub response when the model is not available.
        """
        if self._ready and self._model:
            try:
                params = {**DEFAULT_PARAMS, "max_new_tokens": max_tokens}
                response = self._model.generate_text(prompt=prompt, params=params)
                return response.strip()
            except Exception as exc:
                return f"[Granite Error] {exc}"

        # ── Stub mode – returns a meaningful placeholder ───────────────────
        return self._stub_response(prompt)

    def generate_stream(self, prompt: str, max_tokens: int = 1024):
        """
        Generator that yields text chunks from Granite (streaming).
        Falls back to yielding the full stub response as one chunk.
        """
        if self._ready and self._model:
            try:
                params = {**DEFAULT_PARAMS, "max_new_tokens": max_tokens}
                for chunk in self._model.generate_text_stream(prompt=prompt, params=params):
                    yield chunk
                return
            except Exception as exc:
                yield f"[Granite Stream Error] {exc}"
                return

        yield self._stub_response(prompt)

    @property
    def is_ready(self) -> bool:
        return self._ready

    # ── Stub helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _stub_response(prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "meal plan" in prompt_lower:
            return (
                "**[Demo Mode – IBM Granite not connected]**\n\n"
                "Here is a sample 7-day meal plan outline:\n"
                "- **Day 1:** Oats with berries (breakfast) | Grilled chicken salad (lunch) | "
                "Baked salmon with quinoa (dinner)\n"
                "- **Day 2:** Greek yogurt parfait (breakfast) | Lentil soup (lunch) | "
                "Stir-fried tofu with vegetables (dinner)\n"
                "*(Connect IBM watsonx.ai to generate a fully personalised plan)*"
            )
        if "swap" in prompt_lower or "alternative" in prompt_lower:
            return (
                "**[Demo Mode]** Smart food swap suggestion:\n"
                "Replace white rice with cauliflower rice to reduce carbs by ~80% while "
                "keeping the meal filling. Alternatively, brown rice retains fibre and "
                "lowers the glycaemic index.\n"
                "*(Connect IBM watsonx.ai for personalised swaps)*"
            )
        if "explain" in prompt_lower or "why" in prompt_lower:
            return (
                "**[Demo Mode]** Nutritional explanation:\n"
                "This food is rich in complex carbohydrates and dietary fibre, which provide "
                "sustained energy and support digestive health. It is also a good source of "
                "B-vitamins essential for metabolism.\n"
                "*(Connect IBM watsonx.ai for in-depth explanations)*"
            )
        return (
            "**[Demo Mode – IBM Granite not connected]**\n\n"
            "I'm your AI Nutrition Assistant powered by IBM Granite. "
            "To enable full personalised responses, please configure your "
            "IBM_API_KEY and IBM_PROJECT_ID in the .env file.\n\n"
            "I can help you with:\n"
            "• Personalised meal plans\n"
            "• Smart food swaps\n"
            "• Nutritional explanations\n"
            "• Diet recommendations for health conditions\n"
            "• Cultural & allergy-aware meal suggestions"
        )


# Singleton instance used across the application
granite = GraniteClient()
