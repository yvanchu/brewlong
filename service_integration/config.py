"""Centralised configuration loaded from .env."""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Required ---
SQUARE_ACCESS_TOKEN: str = os.environ["SQUARE_ACCESS_TOKEN"]
SQUARE_LOCATION_ID: str = os.environ["SQUARE_LOCATION_ID"]

# --- Optional (with defaults) ---
PRINTER_MODEL: str = os.getenv("PRINTER_MODEL", "b1")
PRINTER_DENSITY: int = int(os.getenv("PRINTER_DENSITY", "3"))
POLL_INTERVAL: int = int(os.getenv("POLL_INTERVAL", "15"))
LABEL_WIDTH_MM: int = int(os.getenv("LABEL_WIDTH_MM", "50"))   # long edge
LABEL_HEIGHT_MM: int = int(os.getenv("LABEL_HEIGHT_MM", "30"))  # short edge

# --- Derived pixel dimensions (203 DPI) ---
DPI = 203
LABEL_WIDTH_PX: int = int(LABEL_WIDTH_MM / 25.4 * DPI)   # 50 mm → 399 px (long edge)
LABEL_HEIGHT_PX: int = int(LABEL_HEIGHT_MM / 25.4 * DPI)  # 30 mm → 239 px (short edge)
