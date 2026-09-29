"""主循环：物理固定 60Hz，渲染帧率独立。"""
from __future__ import annotations

import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")  # 保持控制台干净

import pygame
from pygame.math import Vector2

from air_object import Air_Object
from aircraft_spec import AircraftSpec
from camera import Camera
from flight_model import FlightDynamics
from grid import draw_grid
from settings import Settings
from world import World


class Dance_over_sky:
    """管理游戏资源和主循环。"""

    def __init__(self):
        pygame.init()
        self.settings = Settings()
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height)
        )
        pygame.display.set_caption("Dance Over Sky")
        self.font = pygame.font.Font(None, 18)

        self.camera = Camera(
            (self.settings.screen_width, self.settings.screen_height),
            self.settings.meters_per_pixel,
        )
        self.world = World()
        self.accumulator = 0.0
        self.running = True

        self._spawn_entities()

    # ------------------------------------------------------------------ 初始化

    def _spawn_entities(self):
        s = self.settings

        player_spec = AircraftSpec.from_json(s.player_spec_path)
        self.player = Air_Object(
            FlightDynamics(
                player_spec,
                position=(0.0, 0.0),
                velocity=(s.initial_speed, 0.0),
                air_density=s.air_density,
            ),
            player_spec.icon,
            player_spec.icon_size_px,
        )
        self.world.add(self.player)

        # 敌机目前只会直线飞：AI 是计划里最后也最难的一块
        enemy_spec = AircraftSpec.from_json(s.enemy_spec_path)
        enemy = Air_Object(
            FlightDynamics(
                enemy_spec,
                position=(s.spawn_gap_m, 0.0),
                velocity=(-s.initial_speed, 0.0),
                air_density=s.air_density,
            ),
            enemy_spec.icon,
            enemy_spec.icon_size_px,
            tint=(255, 110, 110),
        )
        self.world.add(enemy)

    # ------------------------------------------------------------------ 主循环

    def run_game(self, max_frames: int = None):
        """max_frames 只给自动化冒烟测试用。"""
        frames = 0
        try:
            while self.running:
                frame_seconds = self.clock.tick(self.settings.render_fps) / 1000.0
                self._check_events()
                self._update_physics(frame_seconds)
                self._update_camera()
                self._draw()
                frames += 1
                if max_frames is not None and frames >= max_frames:
                    break
        finally:
            pygame.quit()

    def _update_physics(self, frame_seconds: float):
        """固定步长累加器：物理与渲染帧率解耦，dt 永远是 1/60。"""
        s = self.settings
        frame_seconds = min(max(frame_seconds, 0.0), s.max_frame_time)
        self.accumulator += frame_seconds
        dt = s.physics_dt
        steps = 0
        while self.accumulator >= dt and steps < s.max_steps_per_frame:
            self.world.update(dt)
            self.accumulator -= dt
            steps += 1
        if steps >= s.max_steps_per_frame:
            self.accumulator = 0.0  # 追不上就丢掉，别让卡顿越滚越大

    def _update_camera(self):
        if self.settings.camera_follow:
            self.camera.look_at(self.player.dynamics.position)

    # ------------------------------------------------------------------ 输入

    def _check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)

        # 转向直接读键盘状态：避免「按键只触发一次」导致输入被吞
        keys = pygame.key.get_pressed()
        turn = 0.0
        if keys[pygame.K_q] or keys[pygame.K_LEFT]:
            turn -= 1.0
        if keys[pygame.K_e] or keys[pygame.K_RIGHT]:
            turn += 1.0
        self.player.turn_cmd = turn

    def _check_keydown_events(self, event):
        if event.key == pygame.K_ESCAPE:
            self.quit_game()
        elif event.key == pygame.K_F3:
            self.settings.show_debug = not self.settings.show_debug
        elif event.key in (pygame.K_z, pygame.K_MINUS):
            self._zoom(1.0 / self.settings.zoom_step)
        elif event.key in (pygame.K_x, pygame.K_EQUALS):
            self._zoom(self.settings.zoom_step)
        elif event.key == pygame.K_g:
            self.settings.grid_enabled = not self.settings.grid_enabled

    def _zoom(self, factor: float):
        self.camera.zoom(
            factor,
            self.settings.min_meters_per_pixel,
            self.settings.max_meters_per_pixel,
        )

    def quit_game(self):
        self.running = False

    # ------------------------------------------------------------------ 绘制

    def _draw(self):
        self.screen.fill(self.settings.bg_color)
        if self.settings.grid_enabled:
            draw_grid(
                self.screen,
                self.camera,
                major_every=self.settings.grid_major_every,
                color_minor=self.settings.grid_color_minor,
                color_major=self.settings.grid_color_major,
                color_origin=self.settings.grid_color_origin,
                font=self.font,
                color_label=self.settings.grid_label_color,
                min_pixels=self.settings.grid_min_pixels,
                max_pixels=self.settings.grid_max_pixels,
            )
        self.world.draw(self.screen, self.camera)
        if self.settings.show_debug:
            for entity in self.world.entities:
                entity.draw_debug(self.screen, self.camera)
            self._draw_hud()
        pygame.display.flip()

    def _draw_hud(self):
        st = self.player.dynamics.state_dict()
        lines = [
            f"t={st['time']:6.1f}s   speed={st['speed']:6.1f} m/s",
            f"heading={st['heading_deg']:7.2f}   vel_heading={st['velocity_heading_deg']:7.2f}",
            f"alpha={st['alpha_deg']:6.2f}/{st['alpha_limit_deg']:5.2f} deg   n={st['load_factor']:5.2f} g",
            f"L={st['lift_n'] / 1000:6.1f}kN  D={st['drag_n'] / 1000:6.1f}kN  T={st['thrust_n'] / 1000:6.1f}kN",
            f"physics={self.settings.physics_hz}Hz   scale={self.camera.meters_per_pixel:.1f} m/px"
            f"   view={self.camera.visible_width_m() / 1000:.1f}x{self.camera.visible_height_m() / 1000:.1f}km",
            "Q/E or arrows: turn   Z/X: zoom   G: grid   F3: HUD   Esc: quit",
        ]
        for index, text in enumerate(lines):
            surface = self.font.render(text, True, (205, 225, 205))
            self.screen.blit(surface, (10, 8 + index * 16))


if __name__ == '__main__':
    Dance_over_sky().run_game()
