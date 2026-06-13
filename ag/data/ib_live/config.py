"""IB connection and symbol settings for the historical data loader."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

_DEFAULT_CACHE_DIR = Path(__file__).parents[4] / "data" / "ib_live" / "cache"

# CME exchange per symbol
_EXCHANGE: dict[str, str] = {
    "GC":  "COMEX",
    "MGC": "COMEX",
    "6E":  "GLOBEX",
}

# IB bar-size strings
_BAR_SIZE: dict[str, str] = {
    "1m": "1 min",
    "1h": "1 hour",
}

# Conservative per-request duration strings that stay within IB pacing
# (IB allows up to 1 Y for 1-min, 10 Y for 1-hour, but chunking avoids pacing bans)
_CHUNK_DURATION: dict[str, str] = {
    "1m": "180 D",
    "1h": "1 Y",
}

SUPPORTED_SYMBOLS: set[str] = set(_EXCHANGE)
SUPPORTED_TIMEFRAMES: set[str] = set(_BAR_SIZE)


@dataclass
class IBConfig:
    host: str = "127.0.0.1"
    port: int = 7497          # 7497 = TWS live/paper, 4002 = Gateway live/paper
    client_id: int = 1
    cache_dir: Path = field(default_factory=lambda: _DEFAULT_CACHE_DIR)
    pacing_secs: float = 10.0  # mandatory sleep between IB chunk requests
