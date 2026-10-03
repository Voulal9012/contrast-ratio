"""WCAG contrast ratio computation and conformance checking.

This module implements the relative luminance and contrast ratio formulas
defined by WCAG 2.1, along with helpers to check conformance against the
AA and AAA success criteria for normal-sized text.

Interpretation decisions (stated plainly so the behaviour is unambiguous):

- Colours are accepted as (r, g, b) tuples of integers in 0-255. Passing a
  float or an out-of-range value raises ValueError rather than being silently
  clamped; clamping hides mistakes and WCAG conformance is a legal/accessibility
  matter where silent fixes are dangerous.
- The AA/AAA thresholds follow the *normal text* criteria (AA = 4.5, AAA = 7.0).
  WCAG defines separate large-text thresholds (AA = 3.0, AAA = 4.5), but this
  library intentionally does not model font size. If you need the large-text
  thresholds, call contrast_ratio() directly and compare yourself. Picking one
  interpretation here is better than a "smart" flag that half the callers get
  wrong.
- contrast_ratio() returns a float rounded to two decimal places. WCAG tools
  universally report two decimals; returning the full float would make tests
  and user code compare against a moving target.
- wcag_level() returns the string "AAA", "AA", or "Fail" (in that priority
  order). It does not return None; a fixed controlled vocabulary is easier
  to handle at call sites than a nullable.
"""

from __future__ import annotations


def _srgb_channel_luminance(channel: int) -> float:
    """Convert a single 8-bit sRGB channel to its linearised value.

    WCAG defines a piecewise transform: values <= 0.03928 use a linear divide,
    larger values use the standard gamma expansion of ((v + 0.055) / 1.055) ** 2.4.
    The 0.03928 cutoff is the WCAG-specified threshold (it predates the IEC
    update to 0.04045); we keep the WCAG value so our numbers match the spec.
    """
    v = channel / 255.0
    if v <= 0.03928:
        return v / 12.92
    return ((v + 0.055) / 1.055) ** 2.4


def _validate_rgb(color: tuple[int, int, int]) -> None:
    """Validate that color is a 3-tuple of ints in [0, 255].

    Raising early on malformed input gives a clear error at the call site
    rather than producing a nonsensical ratio downstream.
    """
    if not isinstance(color, tuple) or len(color) != 3:
        raise ValueError(
            f"color must be a 3-tuple (r, g, b), got {color!r}"
        )
    for component in color:
        # bool is a subclass of int; reject it explicitly so True/False
        # don't silently become 1/0 channels.
        if isinstance(component, bool) or not isinstance(component, int):
            raise ValueError(
                f"color components must be int, got {type(component).__name__}"
            )
        if component < 0 or component > 255:
            raise ValueError(
                f"color component out of range [0, 255]: {component}"
            )


def relative_luminance(color: tuple[int, int, int]) -> float:
    """Return the WCAG relative luminance of an sRGB colour.

    Args:
        color: A (r, g, b) tuple of integers in 0-255.

    Returns:
        A float in [0, 1]; 0 for black, 1 for white.

    Raises:
        ValueError: if color is not a 3-tuple of ints in range.
    """
    _validate_rgb(color)
    r, g, b = color
    return (
        0.2126 * _srgb_channel_luminance(r)
        + 0.7152 * _srgb_channel_luminance(g)
        + 0.0722 * _srgb_channel_luminance(b)
    )


def contrast_ratio(
    color1: tuple[int, int, int],
    color2: tuple[int, int, int],
) -> float:
    """Return the WCAG contrast ratio between two sRGB colours.

    The ratio is always >= 1.0; identical colours yield 1.0, black-on-white
    yields 21.0 (rounded). The result is rounded to two decimal places to
    match how contrast is universally reported.

    Args:
        color1: A (r, g, b) tuple of integers in 0-255.
        color2: A (r, g, b) tuple of integers in 0-255.

    Returns:
        A float contrast ratio rounded to 2 decimals.

    Raises:
        ValueError: if either colour is malformed.
    """
    l1 = relative_luminance(color1)
    l2 = relative_luminance(color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    ratio = (lighter + 0.05) / (darker + 0.05)
    return round(ratio, 2)


def wcag_level(
    color1: tuple[int, int, int],
    color2: tuple[int, int, int],
) -> str:
    """Return the highest WCAG normal-text level the contrast satisfies.

    Returns one of "AAA", "AA", or "Fail". AAA (>= 7.0) takes precedence
    over AA (>= 4.5). Anything below 4.5 is a failure.
    """
    ratio = contrast_ratio(color1, color2)
    if ratio >= 7.0:
        return "AAA"
    if ratio >= 4.5:
        return "AA"
    return "Fail"


def meets_aa(
    color1: tuple[int, int, int],
    color2: tuple[int, int, int],
) -> bool:
    """Return True if the contrast ratio meets the WCAG AA threshold (4.5)."""
    return contrast_ratio(color1, color2) >= 4.5


def meets_aaa(
    color1: tuple[int, int, int],
    color2: tuple[int, int, int],
) -> bool:
    """Return True if the contrast ratio meets the WCAG AAA threshold (7.0)."""
    return contrast_ratio(color1, color2) >= 7.0
