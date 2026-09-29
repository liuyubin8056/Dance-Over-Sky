"""素材测试：图标必须是透明底，否则深色沙盘上会出现白框。"""
import json
import os
import unittest
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

ROOT = Path(__file__).resolve().parents[1]


class IconAssetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.spec = json.loads((ROOT / "data" / "f16.json").read_text(encoding="utf-8"))

    def setUp(self):
        self.icon_path = ROOT / self.spec["icon"]

    def test_icon_file_exists(self):
        self.assertTrue(self.icon_path.exists(), f"缺少图标文件：{self.icon_path}")

    def test_icon_has_transparent_corners(self):
        icon = pygame.image.load(str(self.icon_path))
        self.assertTrue(icon.get_flags() & pygame.SRCALPHA, "图标应带逐像素 alpha 通道")
        width, height = icon.get_size()
        for corner in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
            with self.subTest(corner=corner):
                self.assertEqual(icon.get_at(corner).a, 0, f"角落 {corner} 不是透明的")

    def test_icon_actually_has_lines(self):
        icon = pygame.image.load(str(self.icon_path))
        width, height = icon.get_size()
        opaque = sum(
            1
            for x in range(0, width, 3)
            for y in range(0, height, 3)
            if icon.get_at((x, y)).a > 128
        )
        self.assertGreater(opaque, 50, "图标几乎全是透明的，可能扣错了")
        # 也不能整张不透明（那就意味着背景没扣掉）
        self.assertLess(opaque, (width // 3) * (height // 3))

    def test_icon_size_matches_aspect_ratio(self):
        icon = pygame.image.load(str(self.icon_path))
        icon_w, icon_h = icon.get_size()
        draw_w, draw_h = self.spec["icon_size_px"]
        self.assertAlmostEqual(
            icon_w / icon_h, draw_w / draw_h, delta=0.05, msg="图标会被拉伸变形"
        )


if __name__ == "__main__":
    unittest.main()
