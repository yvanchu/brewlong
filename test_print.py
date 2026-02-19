#!/usr/bin/env python3
"""Test script — generate a sample label and (optionally) print it.

Usage:
    # 1. Generate a label image only (no printer needed):
    python test_print.py

    # 2. Generate AND send to the NIIMBOT B1 via BLE:
    python test_print.py --print
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# We import from the service_integration package, but label_generator pulls
# pixel dimensions from config.py which reads .env.  To avoid needing a real
# .env just for a test, we set safe defaults before importing.
# ---------------------------------------------------------------------------
import os

os.environ.setdefault("SQUARE_ACCESS_TOKEN", "test")
os.environ.setdefault("SQUARE_LOCATION_ID", "test")

from service_integration.label_generator import generate_label  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sample orders that exercise different label layouts
# ---------------------------------------------------------------------------
SAMPLE_ORDERS = [
    {
        "item_name": "Milk Tea - Jasmine Oolong",
        "modifiers": ["Iced", "Whole Milk", "Regular Sugar", "Extra Ice"],
        "order_number": "T3ST",
    },
]


def generate_samples(output_dir: Path) -> list[Path]:
    """Generate label PNGs for all sample orders. Returns list of paths."""
    output_dir.mkdir(exist_ok=True)
    paths: list[Path] = []
    for order in SAMPLE_ORDERS:
        path = generate_label(
            item_name=order["item_name"],
            modifiers=order["modifiers"],
            order_number=order["order_number"],
            output_dir=str(output_dir),
        )
        paths.append(path)
        logger.info("✅ Generated: %s", path)
    return paths


async def print_labels(paths: list[Path]) -> None:
    """Send each generated label to the NIIMBOT B1 printer."""
    from service_integration.printer_service import PrinterService

    printer = PrinterService()
    try:
        for path in paths:
            logger.info("🖨  Printing %s …", path.name)
            ok = await printer.print_label(path)
            if ok:
                logger.info("✅ Printed %s", path.name)
            else:
                logger.error("❌ Failed to print %s", path.name)
    finally:
        await printer.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate sample labels and optionally print them."
    )
    parser.add_argument(
        "--print",
        dest="do_print",
        action="store_true",
        help="Send generated labels to the NIIMBOT B1 via BLE",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("labels"),
        help="Directory to save label PNGs (default: labels/)",
    )
    args = parser.parse_args()

    paths = generate_samples(args.output_dir)
    print(f"\n{'─' * 40}")
    print(f"Generated {len(paths)} label(s) in {args.output_dir}/")
    for p in paths:
        print(f"  • {p}")
    print(f"{'─' * 40}\n")

    if args.do_print:
        asyncio.run(print_labels(paths))
    else:
        print("Run with --print to send these to the printer.")


if __name__ == "__main__":
    main()
