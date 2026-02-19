# Brewlong Brew Timer — Spec

## 1. Overview

A single-page web app used on an iPad Mini (landscape) to help Brewlong tea shop employees manage timing for multiple brews simultaneously. Four identical, independent columns fill the entire viewport. Each column operates its own tea selection → brewing timer flow.

**Tech stack:** Plain HTML + CSS + JS (no framework). Tea data is loaded from a bundled static `teas.json` file.

---

## 2. Layout

- **Viewport:** Full-screen, landscape orientation on iPad Mini (1024 × 768 logical points).
- **Grid:** 4 equal-width columns spanning the full viewport. No header, no footer, no gaps between columns. Thin vertical dividers separate columns.
- **Each column** is fully independent — selecting tea, starting timers, and resetting in one column has zero effect on the others.

---

## 3. Screens Per Column

Each column has exactly two states:

### 3.1 Selection Screen

Displayed when the column is idle (initial load, or after a brew cycle completes).

| Element          | Description                                                                                                                                                             |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Tea list**     | A scrollable/tappable list of tea names (e.g. Special 1, Special 2, Jasmine, Green, Red, Black). Sourced from `teas.json`. Single-select; selected item is highlighted. |
| **Type list**    | Three options: **Hot**, **Ice**, **Milk**. Single-select; selected item is highlighted. Only types that exist in `teas.json` for the selected tea are shown/enabled.    |
| **Start button** | Disabled until both a tea and a type are selected. Tap transitions the column to the Brewing Screen.                                                                    |

### 3.2 Brewing Screen

Displays the brew stages for the selected tea + type combination.

The column is divided into vertically stacked boxes:

| Box                        | Content                                                                                                                      | Behavior                                                                                                                                |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Info box** (top)         | Tea name + type label, grams of tea (e.g. "7g").                                                                             | Purely informational. Outlined (highlighted border) on initial load to draw attention. Outline removed once any stage timer is started. |
| **Stage boxes** (1–3)      | Timer countdown (e.g. `:30`), water volume (e.g. `100ml`). Number of stage boxes depends on `teas.json` — can be 1, 2, or 3. | Interactive — see §4 Timer Interaction.                                                                                                 |
| **Cancel button** (bottom) | Fixed at the bottom of the column.                                                                                           | Tap resets the column back to the Selection Screen, abandoning any in-progress brew.                                                    |

All boxes share the column width and divide the remaining vertical space equally (after the cancel button).

---

## 4. Timer Interaction

### 4.1 Stage States

Each stage box is in one of four states:

| State         | Visual                                                                                | Tap action                                        |
| ------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------- |
| **Idle**      | Dim/muted. Shows timer duration and volume.                                           | Tap → starts the timer (transitions to Running).  |
| **Running**   | Active appearance — countdown is live, subtle pulsing or animated border.             | Tap → pauses the timer (transitions to Paused).   |
| **Paused**    | Timer frozen at current value, visually distinct (e.g. blinking or dimmed countdown). | Tap → resumes the timer (transitions to Running). |
| **Completed** | Bright fill color to signal "time is up — pour now." Timer shows `0:00`.              | Tap → dismisses (transitions to Done).            |
| **Done**      | Neutral/muted. Timer replaced with a checkmark or "Done" label.                       | No further interaction.                           |

### 4.2 Single-Active Rule

At most **one** stage box across the column may be in the **Running** state at any time.

- When a user taps an Idle or Paused stage to start/resume it, any other Running stage in that same column is automatically **paused**.
- This guarantees exactly 0 or 1 running timer per column.
- Completed and Done stages are unaffected by this rule.

### 4.3 Expected-Stage Outline

To guide the employee through the sequential flow:

- On entering the Brewing Screen, the **Info box** is outlined.
- Once the first stage starts, the Info box outline is removed, and Stage 1 is the active focus.
- When a stage transitions to **Done**, the **next sequential stage** (if any) receives an outline to indicate it's the expected next step.
- The employee is free to ignore the outline and tap any Idle/Paused stage — the outline is a suggestion, not a constraint.

### 4.4 Timer Completion

When a timer reaches `0:00`:

- The stage immediately transitions to **Completed** state.
- The box fills with a bright, high-visibility color (see §7 Color Palette).
- The timer stays in Completed state until the employee taps to dismiss.

### 4.5 Auto-Reset After Final Dismiss

When the **last** stage in the column transitions to **Done**, the column automatically resets to the Selection Screen after a brief delay (~1 second).

---

## 5. Data Format — `teas.json`

A single JSON file bundled in the app's static assets. Structure:

```json
{
  "teas": [
    {
      "name": "Jasmine",
      "types": {
        "hot": {
          "grams": 7,
          "stages": [
            { "time": 30, "volume": 100 },
            { "time": 30, "volume": 100 },
            { "time": 45, "volume": 100 }
          ]
        },
        "ice": {
          "grams": 10,
          "stages": [{ "time": 30, "volume": 150 }]
        }
      }
    }
  ]
}
```

| Field                          | Type   | Description                                                                         |
| ------------------------------ | ------ | ----------------------------------------------------------------------------------- |
| `teas[].name`                  | string | Display name of the tea.                                                            |
| `teas[].types`                 | object | Keys are `"hot"`, `"ice"`, and/or `"milk"`. Only present keys are valid selections. |
| `teas[].types.<type>.grams`    | number | Grams of tea leaves to use.                                                         |
| `teas[].types.<type>.stages[]` | array  | 1–3 stage objects.                                                                  |
| `stages[].time`                | number | Brew time in **seconds**.                                                           |
| `stages[].volume`              | number | Water volume in **milliliters**.                                                    |

---

## 6. Timer Display Format

- Times ≥ 60 seconds: `M:SS` (e.g. `1:30`)
- Times < 60 seconds: `:SS` (e.g. `:30`)
- Timer at zero: `0:00`
- Countdown updates every second.

---

## 7. Color Palette

Clean, high-contrast palette optimized for glanceability in a busy shop environment.

| Role                 | Color                  | Usage                                                  |
| -------------------- | ---------------------- | ------------------------------------------------------ |
| **Background**       | `#1A1A2E` (dark navy)  | App background, idle boxes.                            |
| **Column divider**   | `#2D2D44`              | Thin vertical lines between columns.                   |
| **Surface**          | `#16213E` (deep blue)  | Box backgrounds in default state.                      |
| **Text primary**     | `#EAEAEA` (off-white)  | All primary text — tea names, timers, volumes.         |
| **Text secondary**   | `#8A8A9A` (muted gray) | Labels, done-state text.                               |
| **Accent / outline** | `#00D4AA` (teal)       | Selected items, expected-stage outlines, Start button. |
| **Running**          | `#00D4AA` (teal)       | Running timer border/glow.                             |
| **Paused**           | `#FFB347` (amber)      | Paused timer indicator.                                |
| **Completed**        | `#FF6B6B` (coral red)  | Bright fill for "time's up — pour now."                |
| **Done**             | `#2D2D44` (dark gray)  | Neutral done-state fill.                               |
| **Cancel**           | `#FF4757` (red)        | Cancel button.                                         |

---

## 8. Interaction Summary Table

| User Action                   | Result                                                                                                      |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Select tea + type → tap Start | Column transitions to Brewing Screen. Info box outlined.                                                    |
| Tap an Idle stage             | Timer starts. Any other Running stage in the column is paused. Info box outline removed (if still present). |
| Tap a Running stage           | Timer pauses.                                                                                               |
| Tap a Paused stage            | Timer resumes. Any other Running stage in the column is paused.                                             |
| Tap a Completed stage         | Stage dismissed → Done state. Next sequential Idle stage gets outline.                                      |
| Tap a Done stage              | Nothing.                                                                                                    |
| Tap Cancel                    | Column resets to Selection Screen.                                                                          |
| Last stage dismissed          | Column auto-resets to Selection Screen after ~1s delay.                                                     |

---

## 9. Non-Functional Requirements

- **No server required.** The app runs entirely client-side from static files.
- **No authentication.**
- **No persistent state.** Page refresh resets everything.
- **No audio alerts** (may be added in a future revision).
- **Touch-optimized.** All tap targets ≥ 44×44 points. No hover states relied upon.
- **Landscape lock.** App should use a CSS/meta approach to encourage landscape. If portrait is detected, show a "Rotate to landscape" message.
- **Performance.** Timers must be accurate to ±1 second. Use `requestAnimationFrame` or `setInterval` with drift correction.
