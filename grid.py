"""背景网格：给沙盘一个位置参考。

网格间距是在**世界坐标（米）**上定义的，再按当前缩放挑一档，使屏幕间距落在
[min_pixels, max_pixels] 之间。这样拉近拉远都不会糊成一片，也不会有半条网格。
"""
from __future__ import annotations

import math
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")  # 保持控制台干净

import pygame

# 候选间距（米）：优先用 1/2/5 这类好读的数字
SPACING_LADDER_M = (
    50,
    100,
    200,
    250,
    500,
    1000,
    2000,
    2500,
    5000,
    10000,
    20000,
    25000,
    50000,
    100000,
)


def choose_grid_spacing(
    meters_per_pixel: float,
    ladder=SPACING_LADDER_M,
    min_pixels: float = 48.0,
    max_pixels: float = 160.0,
) -> float:
    """挑一档网格间距（米），使屏幕上的间距落在 [min_pixels, max_pixels]。

    在满足条件的前提下取最密的一档（参考线多一点，但不会挤成一团）。
    """
    meters_per_pixel = max(float(meters_per_pixel), 1e-9)
    for spacing in ladder:
        pixels = spacing / meters_per_pixel
        if min_pixels <= pixels <= max_pixels:
            return float(spacing)
    # 兜底：全太密取最粗的一档，全太疏取最细的一档
    if ladder[-1] / meters_per_pixel < min_pixels:
        return float(ladder[-1])
    return float(ladder[0])


def format_distance(meters: float) -> str:
    """把世界坐标换算成给玩家看的短标签。"""
    if abs(meters) >= 1000.0:
        value = meters / 1000.0
        if abs(value - round(value)) < 0.05:
            return f"{value:.0f}km"
        return f"{value:.1f}km"
    return f"{meters:.0f}m"


def draw_grid(
    screen,
    camera,
    spacing_m: float = None,
    major_every: int = 5,
    color_minor=(26, 30, 36),
    color_major=(44, 52, 62),
    color_origin=(78, 100, 122),
    font=None,
    color_label=(118, 138, 150),
    min_pixels: float = 48.0,
    max_pixels: float = 160.0,
) -> float:
    """按相机画一层网格，返回实际使用的间距（米）。

    font 传 None 就不画坐标标签（测试用）。
    """
    meters_per_pixel = camera.meters_per_pixel
    spacing = float(spacing_m) if spacing_m else choose_grid_spacing(
        meters_per_pixel, min_pixels=min_pixels, max_pixels=max_pixels
    )
    width, height = screen.get_size()
    half_width = camera.visible_width_m() * 0.5
    half_height = camera.visible_height_m() * 0.5

    label_enough_room = font is not None and spacing * major_every / meters_per_pixel >= 70.0

    # 竖线（固定世界坐标 x）
    first = math.floor((camera.center.x - half_width) / spacing)
    last = math.ceil((camera.center.x + half_width) / spacing)
    for index in range(first, last + 1):
        world_x = index * spacing
        pixel_x = int(round(camera.world_to_screen((world_x, 0.0))[0]))
        if index == 0:
            color = color_origin
        elif index % major_every == 0:
            color = color_major
        else:
            color = color_minor
        pygame.draw.line(screen, color, (pixel_x, 0), (pixel_x, height))
        if label_enough_room and index != 0 and index % major_every == 0:
            label = font.render(format_distance(world_x), True, color_label)
            # 竖线标签放屏幕下沿，避免被左上角的 HUD 盖住
            screen.blit(label, (pixel_x + 3, height - 16))

    # 横线（固定世界坐标 y）
    first = math.floor((camera.center.y - half_height) / spacing)
    last = math.ceil((camera.center.y + half_height) / spacing)
    for index in range(first, last + 1):
        world_y = index * spacing
        pixel_y = int(round(camera.world_to_screen((0.0, world_y))[1]))
        if index == 0:
            color = color_origin
        elif index % major_every == 0:
            color = color_major
        else:
            color = color_minor
        pygame.draw.line(screen, color, (0, pixel_y), (width, pixel_y))
        if label_enough_room and index != 0 and index % major_every == 0:
            label = font.render(format_distance(world_y), True, color_label)
            screen.blit(label, (4, pixel_y + 3))

    return spacing
