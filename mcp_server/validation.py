from datetime import datetime
import re
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

TICKER_REGEX = re.compile(r"^(\^[A-Z0-9]+|[A-Z0-9&\-]{1,20}\.(NS|BO))$")


def validate_nse_ticker(ticker: str) -> str:
    ticker_clean = ticker.strip().upper()
    if not TICKER_REGEX.match(ticker_clean):
        raise ValueError(f"Invalid ticker symbol '{ticker}'. Expected format like 'TATAMOTORS.NS' or '^NSEI'")
    return ticker_clean


class Provenance(BaseModel):
    source: str
    fetched_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    as_of: str
    cache_hit: bool = False
    snapshot_id: str


class MCPResponse(BaseModel, Generic[T]):
    tool: str
    ok: bool
    data: T | None = None
    provenance: Provenance
    warnings: list[str] = Field(default_factory=list)
    latency_ms: float = 0.0