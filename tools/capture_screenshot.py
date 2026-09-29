"""无头跑几帧游戏并截图，用来快速检查渲染（网格、图标、HUD）。

用法：

    python tools/capture_screenshot.py --frames 150 --turn 1 --out images/_screenshot.png

不依赖真实时间，直接按固定步长推进，所以结果稳定、跑得也快。
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # 离屏渲染，不需要窗口

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame

from dance_over_sky import Dance_over_sky


def main():
    parser = argparse.ArgumentParser(description="无头运行游戏并截图")
    parser.add_argument("--frames", type=int, default=150, help="渲染帧数")
    parser.add_argument("--turn", type=float, default=0.0, help="-1..1 的杆量")
    parser.add_argument("--zoom", type=float, default=None, help="覆盖 m/px")
    parser.add_argument("--no-grid", action="store_true", help="关掉网格")
    parser.add_argument("--out", default="images/_screenshot.png")
    args = parser.parse_args()

    game = Dance_over_sky()
    if args.turn:
        game._check_events = lambda: setattr(game.player, "turn_cmd", float(args.turn))
    if args.zoom:
        game._zoom(args.zoom / game.settings.meters_per_pixel)
    if args.no_grid:
        game.settings.grid_enabled = False

    for _ in range(args.frames):
        game._check_events()
        game._update_physics(game.settings.physics_dt)
        game._update_camera()
        game._draw()

    pygame.image.save(game.screen, args.out)
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
