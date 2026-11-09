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
APP_VERSION = "1.0.0"
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
    """
    override = os.environ.get("AROOJ_POS_DATA_DIR")
    if override:
        path = Path(override)
    elif sys.platform.startswith("win"):
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            path = Path(local_app_data) / "AroojPOS"
        else:
            path = Path.home() / "AppData" / "Local" / "AroojPOS"
    else:
        path = Path.home() / ".arooj_pos"

    path.mkdir(parents=True, exist_ok=True)
    (path / "backups").mkdir(parents=True, exist_ok=True)
    (path / "logs").mkdir(parents=True, exist_ok=True)
    (path / "receipts").mkdir(parents=True, exist_ok=True)
    (path / "logos").mkdir(parents=True, exist_ok=True)
    return path

def get_db_path() -> Path:
    """Returns the path to the main SQLite database."""
    env_db = os.environ.get("AROOJ_POS_DB_PATH")
    if env_db:
        return Path(env_db)
    return get_app_data_dir() / "arooj_pos.db"

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
