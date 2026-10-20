import hashlib
import json
from pathlib import Path
from typing import Any

SNAPSHOT_DIR = Path("data/snapshots")
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def compute_snapshot_id(ticker: str, period: str, data: Any) -> str:
    """Generates a reproducible sha256 hash snapshot id from payload content."""
    payload = json.dumps({"ticker": ticker, "period": period, "data": data}, sort_keys=True)
    return "snap_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def save_snapshot(snapshot_id: str, data: Any) -> Path:
    """Stores the raw JSON snapshot to disk."""
    filepath = SNAPSHOT_DIR / f"{snapshot_id}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return filepath


def load_snapshot(snapshot_id: str) -> Any:
    """Loads a snapshot by id for exact reproducible replay."""
    filepath = SNAPSHOT_DIR / f"{snapshot_id}.json"
    if not filepath.exists():
        raise FileNotFoundError(f"Snapshot {snapshot_id} not found at {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)