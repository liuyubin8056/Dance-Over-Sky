"""背景网格的测试：间距选择 + 真的画到屏幕上了。"""
import os
import unittest

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from camera import Camera
from grid import SPACING_LADDER_M, choose_grid_spacing, draw_grid, format_distance

BG = (10, 10, 10)


class ChooseGridSpacingTest(unittest.TestCase):
    def test_spacing_keeps_pixel_size_in_range(self):
        for meters_per_pixel in (1.0, 2.5, 5.0, 10.0, 20.0, 37.5, 60.0):
            with self.subTest(meters_per_pixel=meters_per_pixel):
                spacing = choose_grid_spacing(meters_per_pixel)
                pixels = spacing / meters_per_pixel
                self.assertGreaterEqual(pixels, 48.0)
                self.assertLessEqual(pixels, 160.0)

    def test_spacing_is_from_ladder(self):
        for meters_per_pixel in (1.0, 10.0, 33.0, 60.0):
            self.assertIn(
                choose_grid_spacing(meters_per_pixel), [float(m) for m in SPACING_LADDER_M]
            )

    def test_spacing_never_shrinks_when_zooming_out(self):
        previous = 0.0
        for meters_per_pixel in (1.0, 2.0, 5.0, 10.0, 15.0, 25.0, 40.0, 60.0):
            spacing = choose_grid_spacing(meters_per_pixel)
            self.assertGreaterEqual(spacing, previous)
            previous = spacing

    def test_never_denser_than_limit_when_extreme(self):
        # 极端缩放也不该返回小于最细一档的值
        spacing = choose_grid_spacing(10000.0)
        self.assertEqual(spacing, float(SPACING_LADDER_M[-1]))

    def test_format_distance(self):
        self.assertEqual(format_distance(500), "500m")
        self.assertEqual(format_distance(2000), "2km")
        self.assertEqual(format_distance(-5000), "-5km")
        self.assertEqual(format_distance(2500), "2.5km")


class DrawGridTest(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.screen = pygame.Surface((800, 600))
        self.screen.fill(BG)
        self.camera = Camera((800, 600), meters_per_pixel=10.0)

    def tearDown(self):
        pygame.quit()

    def test_returns_spacing_and_draws_lines(self):
        spacing = draw_grid(self.screen, self.camera)  # 不传 font，只画线
        self.assertAlmostEqual(spacing, 500.0)

        # 取一条不是横向网格线的行，数一下被改动的像素
        row = 310
        changed = [x for x in range(800) if self.screen.get_at((x, row))[:3] != BG]
        self.assertGreater(len(changed), 0)
        self.assertLess(len(changed), 200)  # 是线，不是底色被填满

    def test_origin_and_major_line_colors(self):
        draw_grid(self.screen, self.camera, color_origin=(1, 2, 3), color_major=(4, 5, 6))
        row = 310
        # 世界坐标 x=0 落在屏幕中心
        self.assertEqual(self.screen.get_at((400, row))[:3], (1, 2, 3))
        # 世界坐标 x=2500m（第 5 条）是主线
        self.assertEqual(self.screen.get_at((650, row))[:3], (4, 5, 6))
        # 世界坐标 x=500m 是普通线
        self.assertNotIn(self.screen.get_at((450, row))[:3], [(1, 2, 3), (4, 5, 6)])

    def test_grid_follows_camera_center(self):
        self.camera.look_at((1000.0, 0.0))
        draw_grid(self.screen, self.camera, color_origin=(1, 2, 3))
        row = 310
        # 相机中心移到 x=1000m 后，原点竖线应出现在 400 - 100 = 300
        self.assertEqual(self.screen.get_at((300, row))[:3], (1, 2, 3))
        self.assertNotEqual(self.screen.get_at((400, row))[:3], (1, 2, 3))

    def test_spacing_argument_is_respected(self):
        spacing = draw_grid(
            self.screen,
            self.camera,
            spacing_m=1000.0,
            color_origin=(1, 2, 3),
            color_minor=(7, 8, 9),
        )
        self.assertEqual(spacing, 1000.0)
        row = 310
        # 原点竖线仍在屏幕中心；1000m 处的普通线落在 100 像素外
        self.assertEqual(self.screen.get_at((400, row))[:3], (1, 2, 3))
        self.assertEqual(self.screen.get_at((500, row))[:3], (7, 8, 9))

    def test_labels_are_drawn_at_bottom_edge(self):
        """坐标标签画在屏幕下沿，不会被左上角的 HUD 盖住。"""
        font = pygame.font.Font(None, 18)
        label_color = (11, 22, 33)
        draw_grid(self.screen, self.camera, font=font, color_label=label_color)

        bottom = range(self.screen.get_height() - 16, self.screen.get_height() - 2)
        found = any(
            self.screen.get_at((x, y))[:3] == label_color
            for x in range(650, 780)
            for y in bottom
        )
        self.assertTrue(found, "主刻度标签应该出现在屏幕下沿")


if __name__ == "__main__":
    unittest.main()
