"""Persist printed order IDs to survive restarts."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_PATH = Path("printed_orders.json")


class PrintedOrderStore:
    """Simple set-backed store serialised to a JSON file."""

    def __init__(self, path: Path = DEFAULT_PATH):
        self._path = path
        self._printed: set[str] = set()
        self._load()

    # -- public API ----------------------------------------------------------

    def is_printed(self, order_id: str) -> bool:
        return order_id in self._printed

    def mark_printed(self, order_id: str) -> None:
        self._printed.add(order_id)
        self._save()
        logger.info("Marked order %s as printed", order_id)

    def clear(self) -> None:
        self._printed.clear()
        self._save()
        logger.info("Cleared all printed orders")

    # -- persistence ---------------------------------------------------------

    def _load(self) -> None:
        if not self._path.exists():
            logger.info("No state file found; starting fresh")
            return
        try:
            data = json.loads(self._path.read_text())
            self._printed = set(data)
            logger.info("Loaded %d printed order ID(s)", len(self._printed))
        except (json.JSONDecodeError, TypeError):
            logger.warning("Corrupt state file; starting fresh")
            self._printed = set()

    def _save(self) -> None:
        self._path.write_text(json.dumps(sorted(self._printed), indent=2))
