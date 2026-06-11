# Vercel serverless entry point — re-exports the FastAPI app for @vercel/python
import sys
import os

# Ensure the repo root is on the path so `agent`, `dtmcp`, `api` are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api.main import app  # noqa: F401, E402  — Vercel discovers `app` automatically
