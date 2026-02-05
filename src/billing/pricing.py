# src/billing/pricing.py
import math
from datetime import datetime

PRICE_PER_UNIT = 5        # 5 zł
SECONDS_PER_UNIT = 2      # co 2 sekundy


def fee_for(entry: datetime, exit_: datetime) -> int:
    """
    Naliczanie opłaty:
    - każde rozpoczęte 2 sekundy = 5 zł
    """
    seconds = (exit_ - entry).total_seconds()
    if seconds <= 0:
        return PRICE_PER_UNIT

    units = seconds / SECONDS_PER_UNIT
    return int(math.ceil(units) * PRICE_PER_UNIT)
