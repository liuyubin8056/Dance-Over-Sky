"""相机：世界坐标（米）到屏幕坐标（像素）的换算。

世界坐标永远是米，像素只是渲染层的事。这样改比例尺（缩放）不用动任何物理代码，
以后加大地图、加雷达、加导弹射程都不会被「1px = 10m」写死。
"""
from __future__ import annotations

import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from pygame.math import Vector2


class Camera:
    def __init__(self, screen_size, meters_per_pixel: float = 10.0):
        self.screen_width = int(screen_size[0])
        self.screen_height = int(screen_size[1])
        self.meters_per_pixel = float(meters_per_pixel)
        self.center = Vector2(0.0, 0.0)  # 屏幕中心对应的世界坐标

    @property
    def pixels_per_meter(self) -> float:
        return 1.0 / self.meters_per_pixel

    def world_to_screen(self, position) -> tuple:
        """世界坐标（米）-> 屏幕像素（浮点，取整交给调用方）。"""
        px = (position[0] - self.center.x) * self.pixels_per_meter
        py = (position[1] - self.center.y) * self.pixels_per_meter
        return (px + self.screen_width * 0.5, py + self.screen_height * 0.5)

    def screen_to_world(self, px: float, py: float) -> Vector2:
        return Vector2(
            (px - self.screen_width * 0.5) * self.meters_per_pixel + self.center.x,
            (py - self.screen_height * 0.5) * self.meters_per_pixel + self.center.y,
        )

    def visible_width_m(self) -> float:
        return self.screen_width * self.meters_per_pixel

    def visible_height_m(self) -> float:
        return self.screen_height * self.meters_per_pixel

    def look_at(self, position) -> None:
        self.center = Vector2(position)

    def set_meters_per_pixel(self, value: float, low: float = 1.0, high: float = 60.0) -> None:
        self.meters_per_pixel = min(max(float(value), low), high)

    def zoom(self, factor: float, low: float = 1.0, high: float = 60.0) -> None:
        """factor > 1 拉远（1 像素代表更多米），factor < 1 拉近。"""
        self.set_meters_per_pixel(self.meters_per_pixel * factor, low, high)
