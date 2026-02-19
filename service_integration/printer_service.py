"""Thin wrapper around NiimPrintX for printing label images on the NIIMBOT B1."""

import asyncio
import logging
import sys
from pathlib import Path

from PIL import Image

# Ensure the NiimPrintX *project* directory is on sys.path so that
# `NiimPrintX.nimmy` resolves to the inner package, not the outer folder.
_niim_root = str(Path(__file__).resolve().parent.parent / "NiimPrintX")
if _niim_root not in sys.path:
    sys.path.insert(0, _niim_root)

from NiimPrintX.nimmy.bluetooth import find_device  # noqa: E402
from NiimPrintX.nimmy.printer import PrinterClient  # noqa: E402

# Suppress verbose loguru DEBUG output from NiimPrintX
from loguru import logger as _loguru_logger  # noqa: E402
_loguru_logger.remove()
_loguru_logger.add(sys.stderr, level="INFO")

from .config import PRINTER_DENSITY, PRINTER_MODEL

logger = logging.getLogger(__name__)


class PrinterService:
    """Manages the BLE connection to the NIIMBOT B1 and prints label images."""

    def __init__(self) -> None:
        self._printer: PrinterClient | None = None
        self._connected: bool = False

    async def connect(self) -> None:
        """Scan for the printer via BLE and establish a connection."""
        device = await find_device(PRINTER_MODEL)
        self._printer = PrinterClient(device)
        if await self._printer.connect():
            self._connected = True
            logger.info("Printer connected: %s", device.name)
        else:
            raise ConnectionError("Failed to connect to printer")

    async def disconnect(self) -> None:
        """Gracefully disconnect from the printer."""
        if self._printer and self._connected:
            await self._printer.disconnect()
            self._connected = False
            logger.info("Printer disconnected")

    async def _ensure_connected(self) -> None:
        if not self._connected or self._printer is None:
            await self.connect()

    async def print_label(self, image_path: Path) -> bool:
        """Send a label image to the printer.

        Returns True on success, False on failure.
        """
        try:
            await self._ensure_connected()
            image = Image.open(image_path)
            image = image.rotate(-90, expand=True)
            await self._printer.print_imageV2(
                image,
                density=PRINTER_DENSITY,
                quantity=1,
            )
            logger.info("Printed label: %s", image_path.name)
            return True
        except Exception:
            logger.exception("Failed to print %s", image_path.name)
            self._connected = False
            return False
