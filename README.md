# contrast_ratio

A tiny, dependency-free Python library for computing WCAG 2.1 contrast ratios
between two sRGB colours and checking whether they pass the AA or AAA normal-
text thresholds.

## Usage

```python
from contrast_ratio import contrast_ratio, wcag_level, meets_aa, meets_aaa

ratio = contrast_ratio((0, 0, 0), (255, 255, 255))
# 21.0

level = wcag_level((117, 117, 117), (255, 255, 255))
# "AA"

if meets_aa((117, 117, 117), (255, 255, 255)):
    print("passes AA")

if meets_aaa((0, 0, 0), (255, 255, 255)):
    print("passes AAA")
```

## Why this exists

WCAG contrast computation is a handful of lines, but the spec leaves enough room
in input handling and threshold interpretation that ad-hoc copies drift. This
library picks one defensible reading and sticks to it:

- Colours are `(r, g, b)` tuples of `int` in `[0, 255]`. Floats, out-of-range
  values, and bools are rejected with `ValueError` rather than silently
  clamped — in accessibility work, a silent fix is worse than a loud failure.
- The AA (4.5) and AAA (7.0) thresholds are the **normal-text** criteria.
  WCAG also defines large-text thresholds (3.0 and 4.5), but modelling font
  size would mean guessing units and weight. If you need the large-text
  thresholds, call `contrast_ratio()` and compare the number yourself.
- `contrast_ratio()` rounds to two decimal places, matching how ratios are
  reported everywhere in WCAG tooling. This also makes the return value
  safe to compare for equality.
- `wcag_level()` returns the strings `"AAA"`, `"AA"`, or `"Fail"` — a fixed
  vocabulary, never `None`.

## The awkward edge

The sRGB-to-linear transform uses the WCAG cutoff of `0.03928`, not the IEC
value of `0.04045`. They differ slightly and WCAG 2.1 specifies the former; if
you compare against a tool that uses the IEC number you may see tiny differences
in the third decimal place. Since this library rounds to two decimals the
discrepancy almost never surfaces, but it is the one place a careful reader
will spot a divergence from a different implementation.
