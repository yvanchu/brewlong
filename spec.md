# Spec: Square POS → NIIMBOT B1 Label Printer

## 1. Overview

A Python service for Brewlong, a tea shop pop-up, that polls Square POS for completed orders and prints a drink label for each item on a NIIMBOT B1 thermal printer via Bluetooth Low Energy (BLE).

**Hardware:**

- **POS:** Square (orders entered on an iPad)
- **Printer:** NIIMBOT B1 — 203 DPI, 384 px max width, BLE connection
- **Host:** macOS laptop running the Python service

## 2. Technical Stack

| Component        | Technology                                            |
| ---------------- | ----------------------------------------------------- |
| Language         | Python 3.12+                                          |
| Square SDK       | `squareup` — polls for COMPLETED orders               |
| Image generation | `Pillow` — 1-bit monochrome label rendering           |
| Printer driver   | `niimprintX`- See project folder                      |
| Configuration    | `python-dotenv` — secrets loaded from `.env`          |
| State            | JSON file (`printed_orders.json`) — survives restarts |

## 3. Architecture

```
┌──────────┐  HTTP/API   ┌─────────────┐  Pillow   ┌─────────────┐  BLE   ┌──────────┐
│ Square   │ ──────────▸ │  main.py    │ ────────▸ │ label_gen   │ ─────▸ │ NIIMBOT  │
│ POS      │             │ (poll loop) │           │ (PNG image) │        │ B1       │
└──────────┘             └─────────────┘           └─────────────┘        └──────────┘
                               │
                               ▼
                         printed_orders.json
```

### File Structure

```
brewlong/                      ← workspace root
├── .env                       ← secrets (git-ignored)
├── .env.example               ← template for .env
├── .gitignore
├── requirements.txt
├── spec.md
├── printed_orders.json        ← runtime state (git-ignored)
├── labels/                    ← temp label PNGs (git-ignored)
├── service_integration/       ← service package
│   ├── __init__.py
│   ├── __main__.py            ← python -m service_integration entry point
│   ├── main.py                ← async poll loop & orchestration
│   ├── config.py              ← .env loading & derived constants
│   ├── square_client.py       ← Square API polling
│   ├── label_generator.py     ← Pillow-based label rendering
│   ├── printer_service.py     ← NiimPrintX BLE printer wrapper
│   └── state.py               ← printed-order persistence
└── NiimPrintX/                ← local printer driver (pip install -e)
```

## 4. Functional Requirements

### A. Square Polling (`square_client.py`)

- **Interval:** Every 15 seconds (configurable via `POLL_INTERVAL`).
- **Filter:** `state = COMPLETED` orders created in the last 4 hours, sorted `ASC` by `CREATED_AT`.
- **Extracted fields:**
  - `order_id` — full Square UUID
  - `order_number` — last 4 chars of UUID, uppercased (e.g. `"A3F2"`)
  - For each line item: `name`, `quantity`, `modifiers[]`

### B. Label Generation (`label_generator.py`)

**Dimensions:** 30 mm × 50 mm portrait → 239 × 399 px at 203 DPI.

**Layout (top → bottom):**

```
┌────────────────┐
│  banana SP     │  ← item name (30 px bold, up to 2 wrapped lines)
│────────────────│  ← separator line
│  • jasmine     │  ← modifiers (22 px regular, up to 4 lines)
│  • milk tea    │
│  • dairy       │
│  • 50% sweet   │
│                │
│    #T3ST       │  ← order number (42 px bold, centred at bottom)
└────────────────┘
```

- Output: 1-bit monochrome PNG saved as `temp_label_{order_number}.png`
- One label generated per drink (respects quantity field)

### C. State Management (`state.py`)

- Persists printed order IDs to `printed_orders.json`.
- On startup, loads previously printed IDs to avoid reprinting.
- `is_printed(order_id)` / `mark_printed(order_id)` / `clear()`.

### D. Main Loop (`main.py`)

1. Initialise `PrintedOrderStore` and `PrinterService`.
2. Poll Square every `POLL_INTERVAL` seconds.
3. For each new order: generate one label per drink (× quantity), send to printer.
4. Mark order as printed only if **all** labels succeed; otherwise retry next cycle.
5. Graceful shutdown on `SIGINT` / `SIGTERM` (Ctrl+C).

## 5. Configuration

All settings via `.env` (loaded by `python-dotenv`):

| Variable              | Required | Default | Description                          |
| --------------------- | -------- | ------- | ------------------------------------ |
| `SQUARE_ACCESS_TOKEN` | ✅       | —       | Square production API token          |
| `SQUARE_LOCATION_ID`  | ✅       | —       | Square location to poll              |
| `PRINTER_MODEL`       |          | `b1`    | Device name prefix for BLE scan      |
| `PRINTER_DENSITY`     |          | `3`     | Print darkness (1 = light, 5 = dark) |
| `POLL_INTERVAL`       |          | `15`    | Seconds between Square API polls     |
| `LABEL_WIDTH_MM`      |          | `50`    | Label long edge in mm                |
| `LABEL_HEIGHT_MM`     |          | `30`    | Label short edge in mm               |

## 6. Dependencies

```
squareup          # Square Python SDK
pillow            # Image generation
bleak             # Bluetooth Low Energy (macOS/Linux/Windows)
python-dotenv     # .env file loading
```

### Printer Details (discovered via BLE scan)

- **Device:** `B1-H801122686`
- **BLE Address:** `3D60FD62-348E-8AC7-9619-E2A1213681C1`
- **Characteristic:** `bef8d6c9-9c21-4c9e-b632-bd58c1009f9f` (read + write-without-response + notify)
