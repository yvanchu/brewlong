"""Allow running the service with: python -m service_integration

Usage:
    python -m service_integration                   Start the polling service
    python -m service_integration --reprint <ID>    Reprint labels for a specific order
"""

import argparse
import asyncio

from .main import main, reprint_order


def _cli() -> None:
    parser = argparse.ArgumentParser(
        prog="service_integration",
        description="Brewlong label-printing service for Square POS",
    )
    parser.add_argument(
        "--reprint",
        metavar="ORDER",
        help=(
            "Reprint labels for a given order. "
            "Accepts the 4-character order number (e.g. A1B2) "
            "or a full Square order UUID."
        ),
    )

    args = parser.parse_args()

    if args.reprint:
        asyncio.run(reprint_order(args.reprint))
    else:
        main()


_cli()
