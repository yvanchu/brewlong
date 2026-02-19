"""Brewlong label-printing service — main entry point.

Polls Square POS for completed orders, generates a drink label for each
line item, and prints it on the NIIMBOT B1 via BLE.
"""

import asyncio
import logging
import signal
from pathlib import Path

from .config import POLL_INTERVAL
from .label_generator import generate_label
from .printer_service import PrinterService
from .square_client import (
    fetch_completed_orders,
    fetch_order_by_id,
    fetch_order_by_number,
)
from .state import PrintedOrderStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

LABEL_OUTPUT_DIR = Path("labels")


async def process_orders(
    store: PrintedOrderStore,
    printer: PrinterService,
) -> None:
    """Fetch new orders from Square, generate & print a label per drink."""
    orders = fetch_completed_orders()

    for order in orders:
        order_id = order["order_id"]

        if store.is_printed(order_id):
            continue

        logger.info(
            "New order %s (%s) — %d item(s)",
            order["order_number"],
            order_id,
            len(order["line_items"]),
        )

        all_ok = True

        for item in order["line_items"]:
            for copy in range(item["quantity"]):
                label_path = generate_label(
                    item_name=item["name"],
                    modifiers=item["modifiers"],
                    order_number=order["order_number"],
                    output_dir=str(LABEL_OUTPUT_DIR),
                )

                success = await printer.print_label(label_path)

                if success:
                    label_path.unlink(missing_ok=True)
                else:
                    all_ok = False
                    break

            if not all_ok:
                break

        if all_ok:
            store.mark_printed(order_id)
        else:
            logger.warning(
                "Order %s incomplete — will retry next cycle", order_id
            )


async def run() -> None:
    """Start the polling loop with graceful shutdown."""
    LABEL_OUTPUT_DIR.mkdir(exist_ok=True)

    store = PrintedOrderStore()
    printer = PrinterService()

    shutdown = asyncio.Event()

    def _on_signal() -> None:
        logger.info("Shutdown signal received")
        shutdown.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _on_signal)

    logger.info("Brewlong service started — polling every %ds", POLL_INTERVAL)

    try:
        while not shutdown.is_set():
            try:
                await process_orders(store, printer)
            except Exception:
                logger.exception("Error during poll cycle")

            # Wait for POLL_INTERVAL seconds, but wake immediately on shutdown
            try:
                await asyncio.wait_for(shutdown.wait(), timeout=POLL_INTERVAL)
            except asyncio.TimeoutError:
                pass  # normal — time to poll again
    finally:
        await printer.disconnect()
        logger.info("Brewlong service stopped")


async def reprint_order(order_identifier: str) -> None:
    """Reprint all labels for a previously completed order.

    *order_identifier* can be either:
      - a full Square order UUID, or
      - the short 4-character order number shown on labels (e.g. "A1B2")
    """
    LABEL_OUTPUT_DIR.mkdir(exist_ok=True)

    # Resolve the order — try short number first, then full UUID
    identifier = order_identifier.strip().lstrip("#")

    if len(identifier) <= 4:
        logger.info("Looking up order by number: %s", identifier)
        order = fetch_order_by_number(identifier)
    else:
        logger.info("Looking up order by ID: %s", identifier)
        order = fetch_order_by_id(identifier)

    if order is None:
        logger.error("Order '%s' not found — cannot reprint", order_identifier)
        return

    logger.info(
        "Reprinting order %s (%s) — %d item(s)",
        order["order_number"],
        order["order_id"],
        len(order["line_items"]),
    )

    printer = PrinterService()

    try:
        for item in order["line_items"]:
            for copy in range(item["quantity"]):
                label_path = generate_label(
                    item_name=item["name"],
                    modifiers=item["modifiers"],
                    order_number=order["order_number"],
                    output_dir=str(LABEL_OUTPUT_DIR),
                )

                success = await printer.print_label(label_path)

                if success:
                    label_path.unlink(missing_ok=True)
                else:
                    logger.error("Reprint failed for %s", label_path.name)
                    return
    finally:
        await printer.disconnect()

    logger.info("Reprint complete for order %s", order["order_number"])


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
