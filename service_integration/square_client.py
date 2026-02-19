"""Square POS client — polls for completed orders."""

import logging
from datetime import datetime, timedelta, timezone

from square.client import Client

from .config import SQUARE_ACCESS_TOKEN, SQUARE_LOCATION_ID

logger = logging.getLogger(__name__)


def _build_client() -> Client:
    return Client(
        access_token=SQUARE_ACCESS_TOKEN,
        environment="production",
    )


def fetch_completed_orders(lookback_hours: int = 4) -> list[dict]:
    """Return completed orders from the last *lookback_hours* hours.

    Each returned dict has:
        order_id      – full Square UUID
        order_number  – last 4 chars of UUID, uppercased
        line_items    – list of {name, quantity, modifiers}
    """
    client = _build_client()
    start_at = (
        datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    ).isoformat()

    body = {
        "location_ids": [SQUARE_LOCATION_ID],
        "query": {
            "filter": {
                "state_filter": {"states": ["COMPLETED"]},
                "date_time_filter": {
                    "created_at": {"start_at": start_at},
                },
            },
            "sort": {
                "sort_field": "CREATED_AT",
                "sort_order": "ASC",
            },
        },
    }

    result = client.orders.search_orders(body=body)

    if result.is_error():
        logger.error("Square API error: %s", result.errors)
        return []

    orders = result.body.get("orders", [])
    parsed: list[dict] = [_parse_order(o) for o in orders]

    logger.info("Fetched %d completed order(s) from Square", len(parsed))
    return parsed


def _parse_order(order: dict) -> dict:
    """Parse a raw Square order dict into our simplified format."""
    order_id: str = order["id"]
    order_number = order_id[-4:].upper()

    line_items: list[dict] = []
    for item in order.get("line_items", []):
        modifiers = [m["name"] for m in item.get("modifiers", [])]
        line_items.append(
            {
                "name": item.get("name", "Unknown"),
                "quantity": int(item.get("quantity", "1")),
                "modifiers": modifiers,
            }
        )

    return {
        "order_id": order_id,
        "order_number": order_number,
        "line_items": line_items,
    }


def fetch_order_by_id(order_id: str) -> dict | None:
    """Retrieve a single order by its full Square UUID.

    Returns the parsed order dict, or None if not found.
    """
    client = _build_client()
    result = client.orders.retrieve_order(order_id=order_id)

    if result.is_error():
        logger.error("Square API error: %s", result.errors)
        return None

    order = result.body.get("order")
    if order is None:
        return None

    return _parse_order(order)


def fetch_order_by_number(
    order_number: str, lookback_hours: int = 12
) -> dict | None:
    """Search recent completed orders for one matching the short order number.

    *order_number* is the 4-character code baristas see on the cup label
    (last 4 chars of the Square UUID, uppercased).  Returns the first
    match or None.
    """
    orders = fetch_completed_orders(lookback_hours=lookback_hours)
    target = order_number.upper().lstrip("#")

    for order in orders:
        if order["order_number"] == target:
            return order

    logger.warning("No order found with number %s", target)
    return None
