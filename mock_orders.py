"""Mock order generator for employee training.

Generates realistic random orders based on the teas_block.json menu,
generates drink labels, and optionally prints them on the NIIMBOT B1.

Usage:
    python mock_orders.py
"""

import asyncio
import random
import sys
from pathlib import Path

# Ensure project root is on sys.path for service_integration imports
_root = str(Path(__file__).resolve().parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from service_integration.label_generator import generate_label  # noqa: E402
from service_integration.printer_service import PrinterService  # noqa: E402

# ---------------------------------------------------------------------------
# Menu — derived from teas_block.json  (slash-separated names split apart)
#   "Banana Cream/Red Oolong Milk Tea [300ml]" → two milk-tea drinks
#   "Red"      → hot-only
#   "Jasmine"  → hot-only
#   "Orange Cart" → pre-made signature (ice modifier only)
# ---------------------------------------------------------------------------
MILK_TEA_DRINKS = ["Banana Cream", "Red Oolong Milk Tea"]
HOT_ONLY_DRINKS = ["Red", "Jasmine"]
SIGNATURE_DRINKS = ["Orange Cart"]

# Drink frequency weights (roughly based on 2026-02-22 real sales data)
# Banana Cream ≈ 40%, Orange Cart ≈ 20%, Red ≈ 15%, Jasmine ≈ 15%,
# Red Oolong Milk Tea ≈ 10%
DRINK_WEIGHTS: dict[str, int] = {
    "Banana Cream": 40,
    "Orange Cart": 20,
    "Red": 15,
    "Jasmine": 15,
    "Red Oolong Milk Tea": 10,
}

# Order size weights (1–3 drinks per order)
ORDER_SIZE_WEIGHTS: dict[int, int] = {1: 60, 2: 30, 3: 10}

# ---------------------------------------------------------------------------
# Modifier pools — weighted toward the default option
# ---------------------------------------------------------------------------
MILK_CHOICES = [
    ("Whole Milk", 60),
    ("Oat Milk", 40),
]

SUGAR_CHOICES = [
    ("Light Sugar (Default)", 70),
    ("Add Sugar", 15),
    ("No Sugar", 15),
]

ICE_CHOICES = [
    ("Regular Ice (Default)", 65),
    ("Less Ice", 20),
    ("Light Ice", 15),
]

# Orange Cart — ice level only, strongly skewed to default
ICE_ONLY_CHOICES = [
    ("Regular Ice (Default)", 75),
    ("Less Ice", 15),
    ("Light Ice", 10),
]

LABEL_OUTPUT_DIR = Path("labels")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _weighted_choice(choices: list[tuple[str, int]]) -> str:
    values, weights = zip(*choices)
    return random.choices(values, weights=weights, k=1)[0]


def _pick_drink() -> str:
    drinks = list(DRINK_WEIGHTS.keys())
    weights = list(DRINK_WEIGHTS.values())
    return random.choices(drinks, weights=weights, k=1)[0]


def _pick_order_size() -> int:
    sizes = list(ORDER_SIZE_WEIGHTS.keys())
    weights = list(ORDER_SIZE_WEIGHTS.values())
    return random.choices(sizes, weights=weights, k=1)[0]


def _generate_modifiers(drink: str) -> list[str]:
    if drink in MILK_TEA_DRINKS:
        return [
            _weighted_choice(MILK_CHOICES),
            _weighted_choice(SUGAR_CHOICES),
            _weighted_choice(ICE_CHOICES),
        ]
    if drink in HOT_ONLY_DRINKS:
        return ["Hot"]
    if drink in SIGNATURE_DRINKS:
        return [_weighted_choice(ICE_ONLY_CHOICES)]
    return []


# ---------------------------------------------------------------------------
# Order generation
# ---------------------------------------------------------------------------
def generate_order(order_number: int) -> dict:
    size = _pick_order_size()
    line_items = []
    for _ in range(size):
        drink = _pick_drink()
        line_items.append({
            "name": drink,
            "quantity": 1,
            "modifiers": _generate_modifiers(drink),
        })
    return {
        "order_number": f"Test_{order_number}",
        "line_items": line_items,
    }


def display_order(order: dict) -> None:
    print(f"\n{'=' * 44}")
    print(f"  ORDER: {order['order_number']}  ({len(order['line_items'])} item(s))")
    print(f"{'=' * 44}")
    for i, item in enumerate(order["line_items"], 1):
        print(f"  {i}. {item['name']}")
        for mod in item["modifiers"]:
            print(f"     • {mod}")
    print()


# ---------------------------------------------------------------------------
# Label generation & printing
# ---------------------------------------------------------------------------
async def process_order(order: dict, printer: PrinterService | None) -> None:
    order_num = order["order_number"]

    for idx, item in enumerate(order["line_items"], 1):
        label_path = generate_label(
            item_name=item["name"],
            modifiers=item["modifiers"],
            order_number=order_num,
            output_dir=str(LABEL_OUTPUT_DIR),
            note="",
        )

        # Rename to include item index so multi-item orders don't overwrite
        unique_path = label_path.with_name(
            f"temp_label_{order_num}_{idx}.png"
        )
        label_path.rename(unique_path)

        if printer is not None:
            success = await printer.print_label(unique_path)
            if success:
                unique_path.unlink(missing_ok=True)
                print(f"  ✓ Printed: {item['name']}")
            else:
                print(f"  ✗ Print failed — label kept: {unique_path.name}")
        else:
            print(f"  📄 Label saved: {unique_path.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main() -> None:
    LABEL_OUTPUT_DIR.mkdir(exist_ok=True)

    # ── Startup: choose print mode ────────────────────────────────────────
    print("\n╔══════════════════════════════════════╗")
    print("║     Brewlong Mock Order Trainer      ║")
    print("╠══════════════════════════════════════╣")
    print("║  1. Generate labels only (PNG)       ║")
    print("║  2. Generate & print to NIIMBOT B1   ║")
    print("╚══════════════════════════════════════╝")

    while True:
        mode = input("\nSelect mode [1/2]: ").strip()
        if mode in ("1", "2"):
            break
        print("Invalid choice. Enter 1 or 2.")

    printer = None
    if mode == "2":
        print("\nConnecting to printer…")
        printer = PrinterService()
        try:
            await printer.connect()
            print("✓ Printer connected!\n")
        except Exception as exc:
            print(f"✗ Could not connect: {exc}")
            print("Falling back to PNG-only mode.\n")
            printer = None
    else:
        print("\nPNG-only mode — labels saved to labels/\n")

    # ── Main loop ─────────────────────────────────────────────────────────
    order_counter = 1

    print("─" * 44)
    print("  Press 1 → Generate new order")
    print("  Press 2 → Stop and exit")
    print("─" * 44)

    while True:
        choice = input("\n> ").strip()

        if choice == "1":
            order = generate_order(order_counter)
            display_order(order)
            await process_order(order, printer)
            order_counter += 1

        elif choice == "2":
            print("\nShutting down…")
            break

        else:
            print("Invalid input. Press 1 (new order) or 2 (exit).")

    if printer is not None:
        await printer.disconnect()

    print("Done. Goodbye!\n")


if __name__ == "__main__":
    asyncio.run(main())
