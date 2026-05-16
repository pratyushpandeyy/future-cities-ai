import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


if load_dotenv:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")


DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
