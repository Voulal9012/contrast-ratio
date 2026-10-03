import math
import unittest

from contrast_ratio import (
    relative_luminance,
    contrast_ratio,
    wcag_level,
    meets_aa,
    meets_aaa,
)


class TestRelativeLuminance(unittest.TestCase):
    def test_black_is_zero(self):
        self.assertEqual(relative_luminance((0, 0, 0)), 0.0)

    def test_white_is_one(self):
        self.assertEqual(relative_luminance((255, 255, 255)), 1.0)

    def test_red_channel_weighting(self):
        # Pure red (255, 0, 0) should have luminance 0.2126.
        lum = relative_luminance((255, 0, 0))
        self.assertAlmostEqual(lum, 0.2126, places=4)

    def test_green_is_brightest(self):
        # Of the three pure primaries at full intensity, green has the
        # highest luminance, blue the lowest.
        r = relative_luminance((255, 0, 0))
        g = relative_luminance((0, 255, 0))
        b = relative_luminance((0, 0, 255))
        self.assertLess(r, g)
        self.assertLess(b, r)

    def test_rejects_float_components(self):
        with self.assertRaises(ValueError):
            relative_luminance((128.0, 0, 0))

    def test_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            relative_luminance((256, 0, 0))
        with self.assertRaises(ValueError):
            relative_luminance((-1, 0, 0))

    def test_rejects_bool_components(self):
        # bool is a subclass of int but should be rejected to avoid
        # True silently becoming 1.
        with self.assertRaises(ValueError):
            relative_luminance((True, False, False))

    def test_rejects_wrong_length(self):
        with self.assertRaises(ValueError):
            relative_luminance((0, 0))
        with self.assertRaises(ValueError):
            relative_luminance((0, 0, 0, 0))

    def test_rejects_non_tuple(self):
        with self.assertRaises(ValueError):
            relative_luminance([0, 0, 0])


class TestContrastRatio(unittest.TestCase):
    def test_identical_colors_are_one(self):
        self.assertEqual(contrast_ratio((128, 64, 200), (128, 64, 200)), 1.0)

    def test_black_on_white(self):
        # Canonical maximum contrast: 21.0 when rounded to 2 decimals.
        self.assertEqual(contrast_ratio((0, 0, 0), (255, 255, 255)), 21.0)

    def test_white_on_black_same_as_black_on_white(self):
        # Order must not matter.
        self.assertEqual(
            contrast_ratio((255, 255, 255), (0, 0, 0)),
            contrast_ratio((0, 0, 0), (255, 255, 255)),
        )

    def test_result_is_float(self):
        self.assertIsInstance(contrast_ratio((0, 0, 0), (255, 255, 255)), float)

    def test_result_is_rounded_to_two_decimals(self):
        # A mid-grey pair that would otherwise have many decimals.
        ratio = contrast_ratio((100, 100, 100), (200, 200, 200))
        # round(x, 2) always has at most 2 decimal places; verify by
        # checking it equals itself re-rounded.
        self.assertEqual(ratio, round(ratio, 2))

    def test_rejects_bad_color(self):
        with self.assertRaises(ValueError):
            contrast_ratio((0, 0, 0), (256, 256, 256))


class TestWcagLevel(unittest.TestCase):
    def test_black_on_white_is_aaa(self):
        self.assertEqual(wcag_level((0, 0, 0), (255, 255, 255)), "AAA")

    def test_just_below_aaa_still_aa(self):
        # (118, 118, 118) on white gives a ratio just under 7.0 but
        # above 4.5, so it should be AA.
        ratio = contrast_ratio((118, 118, 118), (255, 255, 255))
        self.assertGreaterEqual(ratio, 4.5)
        self.assertLess(ratio, 7.0)
        self.assertEqual(wcag_level((118, 118, 118), (255, 255, 255)), "AA")

    def test_low_contrast_is_fail(self):
        # Light grey on white: very low contrast.
        self.assertEqual(wcag_level((230, 230, 230), (255, 255, 255)), "Fail")

    def test_exact_4_5_boundary_passes_aa(self):
        # Find a grey value whose ratio rounds to exactly 4.5 on white.
        # (117, 117, 117) against white is ~4.5; verify it passes AA.
        ratio = contrast_ratio((117, 117, 117), (255, 255, 255))
        self.assertGreaterEqual(ratio, 4.5)
        self.assertEqual(wcag_level((117, 117, 117), (255, 255, 255)), "AA")

    def test_just_below_4_5_is_fail(self):
        # (122, 122, 122) on white rounds to ~4.48, below AA.
        ratio = contrast_ratio((122, 122, 122), (255, 255, 255))
        self.assertLess(ratio, 4.5)
        self.assertEqual(wcag_level((122, 122, 122), (255, 255, 255)), "Fail")


class TestMeetsAaAaa(unittest.TestCase):
    def test_meets_aa_true_for_black_on_white(self):
        self.assertTrue(meets_aa((0, 0, 0), (255, 255, 255)))

    def test_meets_aaa_true_for_black_on_white(self):
        self.assertTrue(meets_aaa((0, 0, 0), (255, 255, 255)))

    def test_meets_aaa_false_for_grey_on_white(self):
        # Grey that passes AA but not AAA.
        self.assertTrue(meets_aa((118, 118, 118), (255, 255, 255)))
        self.assertFalse(meets_aaa((118, 118, 118), (255, 255, 255)))

    def test_meets_aa_false_for_low_contrast(self):
        self.assertFalse(meets_aa((230, 230, 230), (255, 255, 255)))

    def test_meets_aa_returns_bool(self):
        self.assertIsInstance(meets_aa((0, 0, 0), (255, 255, 255)), bool)

    def test_meets_aaa_returns_bool(self):
        self.assertIsInstance(meets_aaa((0, 0, 0), (255, 255, 255)), bool)


if __name__ == "__main__":
    unittest.main()
