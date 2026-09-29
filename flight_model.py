"""点质量飞行力学模型（俯视沙盘：水平面内机动）。

模型假设（与开发计划一致）：

* 二维俯视平面，y 向下；不做高度、不做重力。所以「升力」就是水平面内的向心力，
  「过载」n = |L| / (m * g) 是水平面内的法向过载。
* 受力 = 升力 L + 阻力 D + 推力 T，加速度 a = F / m，半隐式欧拉积分。
* 阻力含诱导阻力：Cd = Cd0 + k * CL^2，k = 1 / (pi * e * AR)。
  少了这一项，拉 9g 不掉速，能量战就不存在了。
* 攻角 alpha = heading - 速度方向，升力系数 CL = CL_alpha * alpha。
  本版只做线性段 + cl_max 截断，不模拟失速后的抖振与掉升力。
* 攻角上限同时受结构过载 n_max 与失速 cl_max 约束，取更严的那个，
  这就是计划里「通过限制攻角把过载维持在最大过载以下」的实现。
* 机头转动：输入是杆量（-1..1），先变成角速度指令，再限制到不使攻角超过上限。
  这样机头不会转得比气流能提供的升力还快，攻角不会无限增大。

时间步长由主循环固定为 60Hz，本模块只按给定 dt 推进，不读时钟。
"""
from __future__ import annotations

import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")  # 保持控制台干净

from pygame.math import Vector2

from aircraft_spec import AircraftSpec, G0
from angles import deg_to_rad, rad_to_deg, vector_heading_deg, wrap_deg


def _clamp(value: float, low: float, high: float) -> float:
    return low if value < low else (high if value > high else value)


class FlightDynamics:
    """一架飞机的运动状态与受力计算。"""

    def __init__(
        self,
        spec: AircraftSpec,
        position=(0.0, 0.0),
        velocity=(250.0, 0.0),
        heading_deg: float = None,
        air_density: float = 0.660,
    ):
        self.spec = spec
        self.air_density = float(air_density)

        self.position = Vector2(position)
        self.velocity = Vector2(velocity)
        # 默认机头与速度同向（攻角 0）
        self.heading_deg = (
            vector_heading_deg(self.velocity.x, self.velocity.y)
            if heading_deg is None
            else wrap_deg(heading_deg)
        )

        # 由 step() 每步刷新的量
        self.alpha_deg = 0.0
        self.alpha_limit_deg = 0.0
        self.load_factor = 0.0
        self.lift = Vector2(0.0, 0.0)
        self.drag = Vector2(0.0, 0.0)
        self.thrust = Vector2(0.0, 0.0)
        self.force = Vector2(0.0, 0.0)
        self.acceleration = Vector2(0.0, 0.0)
        self.time = 0.0

    @property
    def speed(self) -> float:
        return self.velocity.length()

    @property
    def velocity_heading_deg(self) -> float:
        return vector_heading_deg(self.velocity.x, self.velocity.y)

    @property
    def dynamic_pressure(self) -> float:
        return 0.5 * self.air_density * self.velocity.length_squared()

    def alpha_limit_deg_at(self, speed: float) -> float:
        """给定速度下允许的最大攻角：过载上限与失速上限里更严的那个。"""
        stall_limit = self.spec.alpha_stall_deg
        if speed < 1e-3:
            return stall_limit
        q_s = 0.5 * self.air_density * speed * speed * self.spec.wing_area_m2
        if q_s <= 1e-9:
            return stall_limit
        # 要达到 n_max 需要的升力系数
        cl_for_n_max = self.spec.max_load_factor_g * self.spec.mass_kg * G0 / q_s
        alpha_from_load = rad_to_deg(cl_for_n_max / self.spec.cl_alpha_per_rad)
        return max(0.0, min(alpha_from_load, stall_limit))

    def thrust_magnitude(self, speed: float, throttle: float) -> float:
        """推力大小：有曲线就按曲线（速度的函数），否则取恒定最大推力。"""
        coeffs = self.spec.thrust_curve_coeffs
        if coeffs:
            value = 0.0
            for c in reversed(coeffs):  # 霍纳法，从最高次系数开始
                value = value * speed + float(c)
            thrust = value
        else:
            thrust = self.spec.thrust_max_n
        return max(0.0, thrust) * _clamp(throttle, 0.0, 1.0)

    def step(self, dt: float, turn_cmd: float = 0.0, throttle: float = 1.0) -> None:
        """推进一个固定步长。

        turn_cmd: 杆量，-1（左转/屏幕逆时针）.. +1（右转/屏幕顺时针）
        throttle: 油门 0..1（本版恒为 1）
        """
        dt = max(0.0, float(dt))
        speed = self.speed
        alpha_limit = self.alpha_limit_deg_at(speed)
        self.alpha_limit_deg = alpha_limit

        # 1) 机头转动：角速度指令，并限制到不使攻角超过上限
        turn_cmd = _clamp(float(turn_cmd), -1.0, 1.0)
        if speed > 1e-3:
            vel_heading = self.velocity_heading_deg
            alpha_now = wrap_deg(self.heading_deg - vel_heading)
            delta = turn_cmd * self.spec.turn_rate_max_dps * dt
            # 本步机头最多转到攻角刚好触到上限
            delta = _clamp(delta, -alpha_limit - alpha_now, alpha_limit - alpha_now)
            self.heading_deg = wrap_deg(self.heading_deg + delta)
            alpha = wrap_deg(self.heading_deg - vel_heading)
        else:
            self.heading_deg = wrap_deg(
                self.heading_deg + turn_cmd * self.spec.turn_rate_max_dps * dt
            )
            alpha = 0.0

        # 2) 数值兜底：攻角再夹一次，保证升力不越界
        alpha = _clamp(alpha, -alpha_limit, alpha_limit)
        self.alpha_deg = alpha

        # 3) 气动力
        q = self.dynamic_pressure
        q_s = q * self.spec.wing_area_m2
        cl = _clamp(
            self.spec.cl_alpha_per_rad * deg_to_rad(alpha),
            -self.spec.cl_max,
            self.spec.cl_max,
        )
        lift_magnitude = q_s * cl
        drag_magnitude = q_s * (self.spec.cd0 + self.spec.induced_drag_k * cl * cl)

        if speed > 1e-3:
            ux, uy = self.velocity.x / speed, self.velocity.y / speed
            # 升力垂直于速度：正攻角时把速度朝机头那一侧（屏幕顺时针侧）推
            lift_dir = Vector2(-uy, ux)
            drag_dir = Vector2(-ux, -uy)
        else:
            lift_dir = Vector2(0.0, 0.0)
            drag_dir = Vector2(0.0, 0.0)

        self.lift = lift_dir * lift_magnitude
        self.drag = drag_dir * drag_magnitude
        self.thrust = Vector2.from_polar(
            (self.thrust_magnitude(speed, throttle), self.heading_deg)
        )

        # 4) 合力 -> 加速度 -> 积分
        self.force = self.lift + self.drag + self.thrust
        self.acceleration = self.force / self.spec.mass_kg
        self.velocity += self.acceleration * dt
        self.position += self.velocity * dt

        self.load_factor = abs(lift_magnitude) / (self.spec.mass_kg * G0)
        self.time += dt

    def instantaneous_turn_rate_dps(self) -> float:
        """当前瞬时航迹角速度（度/秒）：omega = L / (m * V) = n * g / V。"""
        speed = self.speed
        if speed < 1e-3:
            return 0.0
        return rad_to_deg(self.lift.length() / (self.spec.mass_kg * speed))

    def state_dict(self) -> dict:
        """给 HUD / 日志用的一份快照。"""
        return {
            "time": self.time,
            "speed": self.speed,
            "heading_deg": self.heading_deg,
            "velocity_heading_deg": self.velocity_heading_deg,
            "alpha_deg": self.alpha_deg,
            "alpha_limit_deg": self.alpha_limit_deg,
            "load_factor": self.load_factor,
            "lift_n": self.lift.length(),
            "drag_n": self.drag.length(),
            "thrust_n": self.thrust.length(),
            "position": (self.position.x, self.position.y),
        }
