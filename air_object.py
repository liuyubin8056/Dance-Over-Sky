"""飞行物实体：物理状态（FlightDynamics）+ 绘制。

物理不在这里，改受力/积分请看 flight_model.py。
本类只做三件事：持有 dynamics、把杆量传给它、按相机把它画到屏幕上。
"""
from __future__ import annotations

import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")  # 保持控制台干净

import pygame

from angles import heading_to_unit


class Air_Object:
    """一个可以在沙盘上显示的飞行物。"""

    def __init__(self, dynamics, icon_path: str, icon_size=(50, 30), tint=None):
        self.dynamics = dynamics
        self.turn_cmd = 0.0  # 杆量 -1..1，由主循环每帧写入
        self.throttle = 1.0
        self.icon_path = icon_path
        self.icon_size = (int(icon_size[0]), int(icon_size[1]))
        self.tint = tint
        self._source_icon = self._load_icon(icon_path, self.icon_size, tint)
        self._rotation_cache = {}

    # ------------------------------------------------------------------ 资源

    @staticmethod
    def _load_icon(path: str, size, tint=None) -> pygame.Surface:
        """图标尺寸和物理尺度无关：15m 的飞机不可能按 10m/px 画成 1.5 像素。"""
        image = pygame.image.load(path).convert_alpha()
        image = pygame.transform.smoothscale(image, size)
        if tint is not None:
            tinted = image.copy()
            tinted.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
            image = tinted
        return image

    def rotated_icon(self, heading_deg: float) -> pygame.Surface:
        key = int(round(heading_deg)) % 360
        icon = self._rotation_cache.get(key)
        if icon is None:
            # 屏幕坐标下 heading 顺时针为正，pygame.transform.rotate 逆时针为正，所以取负
            icon = pygame.transform.rotate(self._source_icon, -heading_deg)
            self._rotation_cache[key] = icon
        return icon

    # ------------------------------------------------------------------ 推进

    def update(self, dt: float) -> None:
        self.dynamics.step(dt, self.turn_cmd, self.throttle)

    # ------------------------------------------------------------------ 绘制

    def draw(self, screen, camera) -> None:
        icon = self.rotated_icon(self.dynamics.heading_deg)
        center = camera.world_to_screen(self.dynamics.position)
        screen.blit(icon, icon.get_rect(center=(int(center[0]), int(center[1]))))

    def draw_debug(self, screen, camera) -> None:
        """画机头指向与速度方向：两条线的夹角就是攻角，用来肉眼验证符号对不对。"""
        center = camera.world_to_screen(self.dynamics.position)
        origin = (int(center[0]), int(center[1]))
        nose = heading_to_unit(self.dynamics.heading_deg)
        vel = heading_to_unit(self.dynamics.velocity_heading_deg)
        length = 45
        pygame.draw.line(
            screen,
            (255, 220, 90),
            origin,
            (int(origin[0] + nose[0] * length), int(origin[1] + nose[1] * length)),
            2,
        )
        pygame.draw.line(
            screen,
            (90, 220, 255),
            origin,
            (int(origin[0] + vel[0] * length), int(origin[1] + vel[1] * length)),
            2,
        )
