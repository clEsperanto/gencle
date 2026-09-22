"""
Regression tests protecting kernelj.hpp regeneration from silently dropping
top-level classes that do not map to a "tierN" CLIc namespace (e.g. FFT,
Transform). See clesperantoj@fcdad13 / clesperantoj@c0e4c99 for the incident
this guards against.

Run with: python -m unittest discover -s update_scripts/tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gencle


OLD_HEADER = """
#ifndef __INCLUDE_KERNEL_HPP
#define __INCLUDE_KERNEL_HPP

#include "clesperantoj.hpp"

class Tier1
{
public:
    static ArrayJ add_images(DeviceJ * device, ArrayJ * src1, ArrayJ * src2, ArrayJ * dst);
};

class FFT
{
public:
    static ArrayJ fft(DeviceJ * device, ArrayJ * src, ArrayJ * dst);
    static ArrayJ ifft(DeviceJ * device, ArrayJ * src, ArrayJ * dst);
    static std::vector<int> smooth_shape(std::vector<int> shape);
};

class Transform
{
public:
    static ArrayJ affine_transform(DeviceJ * device, ArrayJ * src, ArrayJ * dst, AffineTransformJ * transform, bool interpolate, bool resize);
};

#endif // __INCLUDE_KERNEL_HPP
"""


class TestListDeclaredClasses(unittest.TestCase):
    def test_lists_all_top_level_classes(self):
        self.assertEqual(
            gencle.list_declared_classes(OLD_HEADER), ["Tier1", "FFT", "Transform"]
        )

    def test_empty_header(self):
        self.assertEqual(gencle.list_declared_classes(""), [])
        self.assertEqual(gencle.list_declared_classes(None), [])


class TestExtractClassBlock(unittest.TestCase):
    def test_extracts_existing_class(self):
        block = gencle.extract_class_block(OLD_HEADER, "FFT")
        self.assertIsNotNone(block)
        self.assertIn("class FFT", block)
        self.assertIn("smooth_shape", block)
        self.assertNotIn("Transform", block)

    def test_missing_class_returns_none(self):
        self.assertIsNone(gencle.extract_class_block(OLD_HEADER, "DoesNotExist"))


class TestRegenerationPreservesOverriddenClasses(unittest.TestCase):
    """Simulates a regeneration pass from CLIc tiers only, and verifies that
    FFT/Transform survive because they are treated as overridden classes,
    reproducing the fix for the fcdad13 -> c0e4c99 regression."""

    def test_overridden_classes_are_preserved_and_no_regression_raised(self):
        regenerated_tier_header = """
class Tier1
{
public:
    static ArrayJ add_images(DeviceJ * device, ArrayJ * src1, ArrayJ * src2, ArrayJ * dst);
};
"""
        header_blocks = [regenerated_tier_header]

        namespace_overrides = gencle.DEFAULT_NAMESPACE_CLASS_OVERRIDES if hasattr(
            gencle, "DEFAULT_NAMESPACE_CLASS_OVERRIDES"
        ) else {"fft": "FFT", "transform": "Transform"}

        for class_name in sorted(set(namespace_overrides.values())):
            block = gencle.extract_class_block(OLD_HEADER, class_name)
            self.assertIsNotNone(block, f"expected {class_name} in OLD_HEADER fixture")
            header_blocks.append(block)

        new_header = gencle.merger_classes_in_header(header_blocks)

        self.assertIn("class FFT", new_header)
        self.assertIn("class Transform", new_header)

        # Must not raise: nothing unexpectedly disappeared.
        gencle.check_class_regression(OLD_HEADER, new_header, allowed_removals=[])


class TestCheckClassRegression(unittest.TestCase):
    def test_raises_when_class_silently_disappears(self):
        new_header_missing_fft = """
class Tier1
{
public:
    static ArrayJ add_images(DeviceJ * device, ArrayJ * src1, ArrayJ * src2, ArrayJ * dst);
};

class Transform
{
public:
    static ArrayJ affine_transform(DeviceJ * device, ArrayJ * src, ArrayJ * dst, AffineTransformJ * transform, bool interpolate, bool resize);
};
"""
        with self.assertRaises(ValueError) as ctx:
            gencle.check_class_regression(OLD_HEADER, new_header_missing_fft)
        self.assertIn("FFT", str(ctx.exception))

    def test_allowed_removal_does_not_raise(self):
        new_header_missing_fft = """
class Tier1
{
public:
    static ArrayJ add_images(DeviceJ * device, ArrayJ * src1, ArrayJ * src2, ArrayJ * dst);
};

class Transform
{
public:
    static ArrayJ affine_transform(DeviceJ * device, ArrayJ * src, ArrayJ * dst, AffineTransformJ * transform, bool interpolate, bool resize);
};
"""
        removed = gencle.check_class_regression(
            OLD_HEADER, new_header_missing_fft, allowed_removals=["FFT"]
        )
        self.assertEqual(removed, ["FFT"])


if __name__ == "__main__":
    unittest.main()
