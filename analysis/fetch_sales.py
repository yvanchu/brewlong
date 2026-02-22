#!/usr/bin/env python3
"""Fetch completed-order sales data from Square and save to JSON files.

Usage
-----
    # All completed orders on a single day
    python -m analysis.fetch_sales 2026-02-20

    # Orders in a date range (both ends inclusive)
    python -m analysis.fetch_sales 2026-02-01 2026-02-20

Output is written to  analysis/data/<start>_to_<end>.json
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from square.client import Square
from square.core.api_error import ApiError

# ── config ────────────────────────────────────────────────────
load_dotenv()

SQUARE_ACCESS_TOKEN: str = os.environ["SQUARE_ACCESS_TOKEN"]
SQUARE_LOCATION_ID: str = os.environ["SQUARE_LOCATION_ID"]

DATA_DIR = Path(__file__).resolve().parent / "data"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger(__name__)


# ── Square helpers ────────────────────────────────────────────

def _build_client() -> Square:
    return Square(token=SQUARE_ACCESS_TOKEN)


def _fetch_all_orders(start_at: str, end_at: str) -> list[dict]:
    """Paginate through all completed orders in the given time window.

    Parameters
    ----------
    start_at : str   ISO-8601 timestamp (inclusive)
    end_at   : str   ISO-8601 timestamp (exclusive – Square convention)

    Returns list of raw order dicts.
    """
    client = _build_client()
    all_orders: list[dict] = []
    cursor: str | None = None

    while True:
        body: dict = {
            "location_ids": [SQUARE_LOCATION_ID],
            "query": {
                "filter": {
                    "state_filter": {"states": ["COMPLETED"]},
                    "date_time_filter": {
                        "created_at": {
                            "start_at": start_at,
                            "end_at": end_at,
                        },
                    },
                },
                "sort": {
                    "sort_field": "CREATED_AT",
                    "sort_order": "ASC",
                },
            },
        }
        if cursor:
            body["cursor"] = cursor

        try:
            result = client.orders.search(**body)
        except ApiError as exc:
            logger.error("Square API error: %s", exc.errors)
            sys.exit(1)

        for order in result.orders or []:
            all_orders.append(_serialize_order(order))

        cursor = result.cursor
        if not cursor:
            break

    return all_orders


def _serialize_order(order) -> dict:
    """Convert a Square Order object into a JSON-friendly dict."""
    line_items = []
    for item in order.line_items or []:
        modifiers = [m.name for m in (item.modifiers or [])]
        line_items.append({
            "name": item.name or "Unknown",
            "quantity": int(item.quantity or "1"),
            "variation_name": item.variation_name or "",
            "base_price": _money(item.base_price_money),
            "total_money": _money(item.total_money),
            "modifiers": modifiers,
        })

    discounts = []
    for d in order.discounts or []:
        discounts.append({
            "name": d.name or "",
            "type": d.type or "",
            "applied_money": _money(d.applied_money),
        })

    return {
        "order_id": order.id,
        "order_number": order.ticket_name or (order.id or "")[-4:].upper(),
        "state": order.state,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "total_money": _money(order.total_money),
        "total_tax_money": _money(order.total_tax_money),
        "total_discount_money": _money(order.total_discount_money),
        "total_tip_money": _money(order.total_tip_money),
        "line_items": line_items,
        "discounts": discounts,
    }


def _money(money_obj) -> dict | None:
    """Convert a Square Money object to {amount, currency}."""
    if money_obj is None:
        return None
    return {"amount": money_obj.amount, "currency": money_obj.currency}


# ── CLI ───────────────────────────────────────────────────────

def _parse_date(s: str) -> datetime:
    """Parse YYYY-MM-DD into a timezone-aware datetime at midnight UTC."""
    try:
        return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{s}'. Expected YYYY-MM-DD."
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch completed sales data from Square.",
    )
    parser.add_argument(
        "start_date",
        type=_parse_date,
        help="Start date inclusive (YYYY-MM-DD)",
    )
    parser.add_argument(
        "end_date",
        nargs="?",
        type=_parse_date,
        default=None,
        help="End date inclusive (YYYY-MM-DD). Defaults to start_date.",
    )
    args = parser.parse_args()

    start: datetime = args.start_date
    end: datetime = args.end_date or start

    if end < start:
        parser.error("end_date must be on or after start_date")

    # Square's end_at is exclusive, so add one day to make it inclusive.
    start_iso = start.isoformat()
    end_iso = (end + timedelta(days=1)).isoformat()

    logger.info(
        "Fetching orders from %s to %s (inclusive) …",
        start.strftime("%Y-%m-%d"),
        end.strftime("%Y-%m-%d"),
    )

    orders = _fetch_all_orders(start_iso, end_iso)
    logger.info("Fetched %d order(s)", len(orders))

    # ── write output ──────────────────────────────────────────
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    filename = (
        f"{start_str}.json" if start_str == end_str
        else f"{start_str}_to_{end_str}.json"
    )
    out_path = DATA_DIR / filename

    with open(out_path, "w") as f:
        json.dump(
            {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "start_date": start_str,
                "end_date": end_str,
                "order_count": len(orders),
                "orders": orders,
            },
            f,
            indent=2,
            default=str,
        )

    logger.info("Saved → %s", out_path)


if __name__ == "__main__":
    main()
