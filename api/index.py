"""
api/index.py
Vercel serverless WSGI entry point for NutriAI.
Vercel's @vercel/python runtime auto-detects this file and calls `app`.
"""

import sys
import os

# Add project root to path so all modules resolve correctly
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app import app  # noqa: E402

# Vercel looks for the `app` variable as the WSGI callable
