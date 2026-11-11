"""
api/index.py
Vercel serverless entry point for NutriAI Flask app.
Vercel's @vercel/python runtime calls the `app` object as a WSGI handler.
"""

import sys
import os

# Add the project root to the Python path so all modules are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402 – import after sys.path is patched

# Vercel looks for a variable named `app` in this file
# The Flask app object IS the WSGI callable
