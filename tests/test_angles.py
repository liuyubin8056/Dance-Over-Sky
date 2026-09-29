"""角度约定的回归测试。

这些测试失败，通常意味着又有人用 pygame 的 angle_to() 反推 heading 了。
"""
import os
import unittest

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from pygame.math import Vector2

from angles import (
    angle_diff_deg,
    heading_to_unit,
    vector_heading_deg,
    wrap_deg,
)


class WrapDegTest(unittest.TestCase):
    def test_basic_cases(self):
        cases = {
            0: 0,
            90: 90,
            180: 180,
            -180: 180,
            190: -170,
            -190: 170,
            360: 0,
            540: 180,
            -540: 180,
            725: 5,
        }
        for given, expected in cases.items():
            with self.subTest(given=given):
                self.assertAlmostEqual(wrap_deg(given), expected, places=9)

    def test_always_inside_range(self):
        for deg in range(-1000, 1001, 7):
            value = wrap_deg(deg)
            self.assertGreater(value, -180.0)
            self.assertLessEqual(value, 180.0)


class HeadingTest(unittest.TestCase):
    def test_cardinal_directions(self):
        # 屏幕坐标：x 右、y 下；heading 顺时针为正
        self.assertAlmostEqual(vector_heading_deg(1, 0), 0.0)
        self.assertAlmostEqual(vector_heading_deg(0, 1), 90.0)
        self.assertAlmostEqual(vector_heading_deg(-1, 0), 180.0)
        self.assertAlmostEqual(vector_heading_deg(0, -1), -90.0)

    def test_zero_vector_is_zero(self):
        self.assertEqual(vector_heading_deg(0, 0), 0.0)

    def test_matches_pygame_from_polar(self):
        for heading in (0.0, 30.0, 90.0, 145.0, -170.0):
            with self.subTest(heading=heading):
                vector = Vector2.from_polar((1.0, heading))
                self.assertAlmostEqual(
                    vector_heading_deg(vector.x, vector.y), heading, places=9
                )

    def test_angle_to_is_negated_heading(self):
        """把 pygame 的坑钉住：v.angle_to((1,0)) == -heading(v)。"""
        for heading in (0.0, 30.0, 90.0, -120.0, 180.0):
            with self.subTest(heading=heading):
                vector = Vector2.from_polar((1.0, heading))
                self.assertAlmostEqual(
                    vector.angle_to(Vector2(1, 0)), -heading, places=6
                )

    def test_heading_to_unit_is_inverse_of_heading(self):
        for heading in (-180.0, -33.0, 0.0, 47.0, 179.0):
            with self.subTest(heading=heading):
                unit = heading_to_unit(heading)
                self.assertAlmostEqual(
                    vector_heading_deg(unit[0], unit[1]), heading, places=9
                )

    def test_angle_diff(self):
        self.assertAlmostEqual(angle_diff_deg(10.0, 350.0), 20.0)
        self.assertAlmostEqual(angle_diff_deg(350.0, 10.0), -20.0)
        self.assertAlmostEqual(angle_diff_deg(0.0, 0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
