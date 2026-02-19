# Brewlong Brew Timer — UX Reference

## Full Viewport Layout (iPad Mini Landscape)

Four identical independent columns fill the entire screen. No header or footer.

```
+------------+--------------+--------------+--------------+
|            |              |              |              |
|  Column 1  |   Column 2   |   Column 3   |   Column 4   |
|            |              |              |              |
| (idle or   |  (idle or    |  (idle or    |  (idle or    |
|  brewing)  |   brewing)   |   brewing)   |   brewing)   |
|            |              |              |              |
+------------+--------------+--------------+--------------+
```

---

## Screen 1 -- Selection (per column)

Shown when column is idle. Employee picks a tea and a type, then taps Start.

```
+--------------------------+
|                          |
|  +--------------------+  |
|  | Tea            v   |  |
|  |--------------------|  |
|  | Special 1          |  |
|  | Special 2          |  |
|  | Jasmine            |  |
|  | Green         <----|--|-- selected (highlighted)
|  | Red                |  |
|  | Black              |  |
|  +--------------------+  |
|                          |
|  +--------------------+  |
|  | Type               |  |
|  |--------------------|  |
|  | Hot                |  |
|  | Ice           <----|--|-- selected (highlighted)
|  | Milk               |  |
|  +--------------------+  |
|                          |
|       +----------+       |
|       |  Start   |       |
|       +----------+       |
|                          |
+--------------------------+
```

- Only types available in `teas.json` for the selected tea are enabled.
- Start is disabled until both tea and type are selected.

---

## Screen 2 -- Brewing (per column, 3-stage example)

After tapping Start. Shows info + up to 3 stage boxes + cancel.

### Initial State (nothing started yet)

Info box is outlined to draw attention to the grams.

```
+--------------------------+
| +=======================+|
| ||     Ice Green        ||
| ||        7g            ||  <-- outlined (expected)
| +=======================+|
| +------------------------+|
| |                        ||
| |       :30    100ml     ||  <-- stage 1 (idle)
| |                        ||
| +------------------------+|
| +------------------------+|
| |                        ||
| |       :30    100ml     ||  <-- stage 2 (idle)
| |                        ||
| +------------------------+|
| +------------------------+|
| |                        ||
| |       :45    100ml     ||  <-- stage 3 (idle)
| |                        ||
| +------------------------+|
|       +----------+        |
|       |  Cancel  |        |
|       +----------+        |
+--------------------------+
```

### Stage 1 Running

User tapped stage 1. Info box outline removed. Stage 1 has active teal border.

```
+--------------------------+
| +------------------------+|
| |     Ice Green          ||
| |        7g              ||
| +------------------------+|
| +=======================+|
| ||                       ||
| ||      :24    100ml     ||  <-- RUNNING (teal border, counting down)
| ||                       ||
| +=======================+|
| +------------------------+|
| |       :30    100ml     ||  <-- stage 2 (idle)
| +------------------------+|
| +------------------------+|
| |       :45    100ml     ||  <-- stage 3 (idle)
| +------------------------+|
|       +----------+        |
|       |  Cancel  |        |
|       +----------+        |
+--------------------------+
```

### Stage 1 Completed

Timer hit 0:00. Stage 1 fills with bright coral red. Tap to dismiss.

```
+--------------------------+
| +------------------------+|
| |     Ice Green          ||
| |        7g              ||
| +------------------------+|
| +------------------------+|
| |########################||
| |#### 0:00  100ml #######||  <-- COMPLETED (bright coral fill)
| |########################||      tap to dismiss
| +------------------------+|
| +------------------------+|
| |       :30    100ml     ||  <-- stage 2 (idle)
| +------------------------+|
| +------------------------+|
| |       :45    100ml     ||  <-- stage 3 (idle)
| +------------------------+|
|       +----------+        |
|       |  Cancel  |        |
|       +----------+        |
+--------------------------+
```

### Stage 1 Done, Stage 2 Outlined

After dismissing stage 1. It goes to neutral Done state. Stage 2 gets the outline.

```
+--------------------------+
| +------------------------+|
| |     Ice Green          ||
| |        7g              ||
| +------------------------+|
| +------------------------+|
| |     Done          check||  <-- DONE (neutral, no interaction)
| +------------------------+|
| +=======================+|
| ||                       ||
| ||      :30    100ml     ||  <-- stage 2 (idle, OUTLINED = expected next)
| ||                       ||
| +=======================+|
| +------------------------+|
| |       :45    100ml     ||  <-- stage 3 (idle)
| +------------------------+|
|       +----------+        |
|       |  Cancel  |        |
|       +----------+        |
+--------------------------+
```

### Stage Paused

If user taps a running timer, it pauses (amber indicator).

```
| + - - - - - - - - - - - +|
| |                        ||
| |      :17    100ml      ||  <-- PAUSED (amber dashed border)
| |                        ||
| + - - - - - - - - - - - +|
```

---

## Screen 2 -- Brewing (1-stage example)

Some teas (e.g. ice milk tea) may only have 1 stage. The stage box is larger.

```
+--------------------------+
| +=======================+|
| ||    Ice Milk Green    ||
| ||        10g           ||
| +=======================+|
|                          |
| +------------------------+|
| |                        ||
| |                        ||
| |       :30    150ml     ||  <-- only stage (idle)
| |                        ||
| |                        ||
| +------------------------+|
|                          |
|       +----------+        |
|       |  Cancel  |        |
|       +----------+        |
+--------------------------+
```

After this single stage is dismissed, column auto-resets to Selection Screen.

---

## State Machine (per stage box)

```
          tap              tap              tap
 Idle ----------> Running ------> Paused ------> Running
                    |                               |
                    | timer hits 0:00                | timer hits 0:00
                    v                                v
                Completed ------ tap ------------> Done
```

- **Single-active rule:** Only 1 stage per column can be Running at a time.
- Starting/resuming a stage auto-pauses any other Running stage in that column.

---

## Interaction Quick Reference

| Tap target | Current state | Result |
|---|---|---|
| Stage box | Idle | Start timer -> Running |
| Stage box | Running | Pause timer -> Paused |
| Stage box | Paused | Resume timer -> Running |
| Stage box | Completed | Dismiss -> Done. Next idle stage gets outline. |
| Stage box | Done | Nothing |
| Cancel button | Any | Reset column to Selection Screen |
