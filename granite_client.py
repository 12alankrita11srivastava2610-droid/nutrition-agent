"""
granite_client.py
IBM Granite (watsonx.ai) client – uses direct REST API calls via `requests`.
No ibm-watsonx-ai SDK required, eliminating the pandas/numpy build dependency.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────
IBM_API_KEY      = os.getenv("IBM_API_KEY", "")
IBM_WATSONX_URL  = os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
IBM_PROJECT_ID   = os.getenv("IBM_PROJECT_ID", "")
GRANITE_MODEL_ID = os.getenv("IBM_GRANITE_MODEL_ID", "ibm/granite-3-1-8b-base")

# IBM IAM token endpoint
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"


class GraniteClient:
    """
    Calls IBM watsonx.ai REST API directly using `requests`.
    Obtains an IAM bearer token from the API key and calls the
    /ml/v1/text/generation endpoint.
    Falls back to stub responses when credentials are not configured.
    """

    def __init__(self):
        self._iam_token: str = ""
        self._ready: bool = False
        self._init()

    # ── Init ───────────────────────────────────────────────────────────────────

    def _init(self):
        if not IBM_API_KEY or IBM_API_KEY == "your_ibm_api_key_here":
            print("[GraniteClient] IBM_API_KEY not configured – using stub mode.")
            return
        if not IBM_PROJECT_ID or IBM_PROJECT_ID == "your_project_id_here":
            print("[GraniteClient] IBM_PROJECT_ID not configured – using stub mode.")
            return

        token = self._fetch_iam_token()
        if token:
            self._iam_token = token
            self._ready = True
            print(f"[GraniteClient] Connected to IBM Granite model: {GRANITE_MODEL_ID}")
        else:
            print("[GraniteClient] Failed to obtain IAM token – using stub mode.")

    def _fetch_iam_token(self) -> str:
        """Exchange IBM API key for a Bearer token."""
        try:
            resp = requests.post(
                IAM_TOKEN_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey": IBM_API_KEY,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                return resp.json().get("access_token", "")
            print(f"[GraniteClient] IAM token error {resp.status_code}: {resp.text[:200]}")
        except Exception as exc:
            print(f"[GraniteClient] IAM token request failed: {exc}")
        return ""

    def _refresh_token_if_needed(self):
        """Re-fetch token (called on 401 responses)."""
        self._iam_token = self._fetch_iam_token()

    # ── Public API ─────────────────────────────────────────────────────────────

    def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """Send a prompt to IBM Granite REST API and return generated text."""
        if not self._ready:
            return self._stub_response(prompt)

        url = (
            f"{IBM_WATSONX_URL}/ml/v1/text/generation"
            f"?version=2023-05-29"
        )
        payload = {
            "model_id":   GRANITE_MODEL_ID,
            "project_id": IBM_PROJECT_ID,
            "input":      prompt,
            "parameters": {
                "max_new_tokens":     max_tokens,
                "min_new_tokens":     10,
                "temperature":        0.7,
                "top_k":              50,
                "top_p":              0.95,
                "repetition_penalty": 1.1,
                "stop_sequences":     ["<|endoftext|>"],
            },
        }
        headers = {
            "Authorization": f"Bearer {self._iam_token}",
            "Content-Type":  "application/json",
            "Accept":        "application/json",
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=90)

            # Token expired – refresh and retry once
            if resp.status_code == 401:
                self._refresh_token_if_needed()
                headers["Authorization"] = f"Bearer {self._iam_token}"
                resp = requests.post(url, json=payload, headers=headers, timeout=90)

            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    return results[0].get("generated_text", "").strip()
                return "[No text generated]"

            return f"[Granite API Error {resp.status_code}] {resp.text[:300]}"

        except requests.Timeout:
            return "[Granite Error] Request timed out. Please try again."
        except Exception as exc:
            return f"[Granite Error] {exc}"

    def generate_stream(self, prompt: str, max_tokens: int = 1024):
        """Yield the full response as one chunk (streaming not used in this app)."""
        yield self.generate(prompt, max_tokens)

    @property
    def is_ready(self) -> bool:
        return self._ready

    # ── Stub responses (demo mode) ─────────────────────────────────────────────

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
                "*(Configure IBM_API_KEY and IBM_PROJECT_ID to generate a fully personalised plan)*"
            )
        if "swap" in prompt_lower or "alternative" in prompt_lower:
            return (
                "**[Demo Mode]** Smart food swap suggestion:\n"
                "Replace white rice with cauliflower rice to reduce carbs by ~80% "
                "while keeping the meal filling.\n"
                "*(Connect IBM watsonx.ai for personalised swaps)*"
            )
        if "explain" in prompt_lower or "why" in prompt_lower:
            return (
                "**[Demo Mode]** Nutritional explanation:\n"
                "This food is rich in complex carbohydrates and dietary fibre, providing "
                "sustained energy and supporting digestive health.\n"
                "*(Connect IBM watsonx.ai for in-depth explanations)*"
            )
        return (
            "**[Demo Mode – IBM Granite not connected]**\n\n"
            "I'm your AI Nutrition Assistant powered by IBM Granite. "
            "Configure IBM_API_KEY and IBM_PROJECT_ID to enable live AI responses.\n\n"
            "I can help you with:\n"
            "• Personalised meal plans\n"
            "• Smart food swaps\n"
            "• Nutritional explanations\n"
            "• Diet recommendations for health conditions\n"
            "• Cultural & allergy-aware meal suggestions"
        )


# Singleton instance used across the application
granite = GraniteClient()
