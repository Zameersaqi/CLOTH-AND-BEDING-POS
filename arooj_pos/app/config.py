"""
Arooj Cloth and Bedsheet Parda - Application Configuration & Utilities
"""

import os
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Union

APP_NAME = "Arooj Cloth and Bedsheet Parda POS"
APP_SHORT_NAME = "Arooj POS"
APP_VERSION = "2.1.0"
COMPANY_NAME = "Arooj Cloth and Bedsheet Parda"
DEFAULT_CURRENCY = "PKR"
DEFAULT_CURRENCY_SYMBOL = "Rs. "

def get_base_dir() -> Path:
    """Returns the base project root directory."""
    return Path(__file__).resolve().parent.parent

def get_app_data_dir() -> Path:
    """
    Returns the persistent application data directory on Windows or POSIX.
    Ensures user data, database, backups, and logos survive app updates.
    Isolated to AroojPOS_v2 to prevent legacy cache and database conflicts.
    """
    override = os.environ.get("AROOJ_POS_DATA_DIR")
    if override:
        path = Path(override)
    elif sys.platform.startswith("win") or "LOCALAPPDATA" in os.environ:
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            path = Path(local_app_data) / "AroojPOS_v2"
        else:
            path = Path.home() / "AppData" / "Local" / "AroojPOS_v2"
    else:
        path = Path.home() / "AroojPOS_v2"

    path.mkdir(parents=True, exist_ok=True)
    (path / "backups").mkdir(parents=True, exist_ok=True)
    (path / "logs").mkdir(parents=True, exist_ok=True)
    (path / "receipts").mkdir(parents=True, exist_ok=True)
    (path / "logos").mkdir(parents=True, exist_ok=True)
    return path

def get_db_path() -> Path:
    """Returns the path to the main SQLite database (arooj_pos_v2.db)."""
    env_db = os.environ.get("AROOJ_POS_DB_PATH")
    if env_db:
        return Path(env_db)
    return get_app_data_dir() / "arooj_pos_v2.db"

def get_legacy_db_paths() -> list[Path]:
    """
    Returns candidate paths for legacy databases from older POS versions
    (e.g. %LOCALAPPDATA%/AroojPOS/arooj_pos.db) to safely preserve past business data.
    """
    candidates = []
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "AroojPOS" / "arooj_pos.db")
        candidates.append(Path(local_app_data) / "AroojPOS" / "arooj_pos_v2.db")
    candidates.append(Path.home() / "AppData" / "Local" / "AroojPOS" / "arooj_pos.db")
    candidates.append(Path.home() / "AroojPOS" / "arooj_pos.db")
    candidates.append(get_base_dir() / "arooj_pos.db")
    return [p for p in candidates if p.exists() and p.is_file()]

# Fabric & Unit conversion constants
METERS_PER_GAZ = Decimal("0.9144")  # Standard 1 Yard/Gaz = 0.9144 Meters
GAZ_PER_METER = Decimal("1.09361") # 1 Meter = 1.09361 Gaz/Yards

def gaz_to_meters(gaz_val: Union[int, float, str, Decimal, None]) -> Decimal:
    """Converts fabric measured in Gaz / Yards to standard Meters."""
    d = to_qty_decimal(gaz_val)
    return (d * METERS_PER_GAZ).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

def meters_to_gaz(meters_val: Union[int, float, str, Decimal, None]) -> Decimal:
    """Converts fabric measured in Meters to Gaz / Yards."""
    d = to_qty_decimal(meters_val)
    return (d * GAZ_PER_METER).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

def format_pakistani_whatsapp_number(phone: str) -> str:
    """Converts a local Pakistani phone (e.g. 0300-1234567) to international WhatsApp format (923001234567)."""
    import re
    cleaned = re.sub(r"\D", "", phone or "")
    if cleaned.startswith("0") and len(cleaned) == 11:
        return "92" + cleaned[1:]
    elif not cleaned.startswith("92") and len(cleaned) == 10:
        return "92" + cleaned
    return cleaned

def to_decimal(val: Union[int, float, str, Decimal, None]) -> Decimal:
    """
    Safely convert numeric values to Decimal with 2 decimal places to avoid
    floating-point inaccuracies in all retail financial transactions.
    """
    if val is None or val == "":
        return Decimal("0.00")
    if isinstance(val, Decimal):
        return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    try:
        # Convert via string representation to avoid float binary inaccuracy
        return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal("0.00")

def format_currency(amount: Union[Decimal, float, int, str], show_symbol: bool = True) -> str:
    """Formats an amount into standard Pakistani Rupee representation."""
    d = to_decimal(amount)
    formatted = f"{d:,.2f}"
    if show_symbol:
        return f"{DEFAULT_CURRENCY_SYMBOL}{formatted}"
    return formatted

def to_qty_decimal(val: Union[int, float, str, Decimal, None]) -> Decimal:
    """Quantity decimal representation supporting lengths (meters, yards) and weights up to 3 decimals."""
    if val is None or val == "":
        return Decimal("0.000")
    if isinstance(val, Decimal):
        return val.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    try:
        return Decimal(str(val)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal("0.000")
