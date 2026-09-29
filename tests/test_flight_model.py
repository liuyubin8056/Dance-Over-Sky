"""飞行力学的验收测试。

覆盖开发计划里的验收标准：攻角符号、过载限制、转弯角速度、诱导阻力掉速、
以及固定步长的收敛性。
"""
import os
import unittest
from dataclasses import replace
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from pygame.math import Vector2

from aircraft_spec import G0, AircraftSpec
from angles import rad_to_deg, wrap_deg
from flight_model import FlightDynamics

SPEC_PATH = Path(__file__).resolve().parents[1] / "data" / "f16.json"
DT = 1.0 / 60.0  # 固定物理步长


def make_dynamics(speed=250.0, velocity=None, heading_deg=0.0, spec=None):
    spec = spec or AircraftSpec.from_json(str(SPEC_PATH))
    if velocity is None:
        velocity = Vector2.from_polar((speed, heading_deg))
    return FlightDynamics(
        spec,
        position=(0.0, 0.0),
        velocity=velocity,
        heading_deg=heading_deg,
        air_density=0.660,
    )


class StraightFlightTest(unittest.TestCase):
    def test_level_flight_has_no_lift_and_accelerates(self):
        dynamics = make_dynamics(250.0, heading_deg=0.0)
        dynamics.step(DT, turn_cmd=0.0)

        self.assertAlmostEqual(dynamics.alpha_deg, 0.0, places=9)
        self.assertAlmostEqual(dynamics.lift.length(), 0.0, places=6)
        self.assertAlmostEqual(dynamics.load_factor, 0.0, places=9)
        # 250 m/s 平飞时推力大于阻力，应该加速
        self.assertGreater(dynamics.speed, 250.0)
        self.assertGreater(dynamics.thrust.length(), dynamics.drag.length())

    def test_nose_up_has_no_phantom_force(self):
        """回归测试：机头与速度同向朝上飞时，攻角必须是 0。

        初版代码在这里算出了 180° 攻角，凭空产生约 2e6 N（约 21g）。
        """
        dynamics = make_dynamics(250.0, heading_deg=-90.0)  # 朝屏幕上方
        dynamics.step(DT, turn_cmd=0.0)

        self.assertAlmostEqual(dynamics.alpha_deg, 0.0, places=9)
        self.assertAlmostEqual(dynamics.lift.length(), 0.0, places=6)
        self.assertLess(dynamics.force.length(), 200_000.0)

    def test_positive_alpha_turns_velocity_towards_nose(self):
        """机头偏向速度顺时针侧（攻角为正）时，速度方向应被升力推向机头。"""
        dynamics = make_dynamics(
            250.0, velocity=Vector2.from_polar((250.0, 10.0)), heading_deg=0.0
        )
        dynamics.step(DT, turn_cmd=0.0)

        # 速度为 +10°、机头为 0°，攻角 = 0 - 10 = -10°
        self.assertAlmostEqual(dynamics.alpha_deg, -10.0, places=6)
        # 速度方向应向机头（0°）靠拢，即角度变小
        self.assertLess(dynamics.velocity_heading_deg, 10.0)

    def test_thrust_curve_hook(self):
        spec = AircraftSpec.from_json(str(SPEC_PATH))
        curved = replace(spec, thrust_curve_coeffs=[1000.0, 2.0])
        dynamics = make_dynamics(100.0, spec=curved)
        # 1000 + 2 * 100 = 1200 N
        self.assertAlmostEqual(dynamics.thrust_magnitude(100.0, 1.0), 1200.0)


class LoadFactorLimitTest(unittest.TestCase):
    def test_alpha_and_load_factor_never_exceed_limits(self):
        for speed in (120.0, 200.0, 250.0, 400.0, 600.0):
            for turn_cmd in (-1.0, 1.0):
                with self.subTest(speed=speed, turn_cmd=turn_cmd):
                    dynamics = make_dynamics(speed)
                    spec = dynamics.spec
                    worst_alpha = 0.0
                    worst_load = 0.0
                    for _ in range(240):  # 4 秒硬拉杆
                        dynamics.step(DT, turn_cmd)
                        worst_alpha = max(worst_alpha, abs(dynamics.alpha_deg))
                        worst_load = max(worst_load, dynamics.load_factor)
                    self.assertLessEqual(
                        worst_alpha, dynamics.alpha_limit_deg + 1e-6
                    )
                    self.assertLessEqual(worst_load, spec.max_load_factor_g + 1e-6)

    def test_low_speed_is_stall_limited(self):
        """低速时够不到 9g：攻角先被 cl_max 卡住。"""
        dynamics = make_dynamics(120.0)
        for _ in range(240):
            dynamics.step(DT, turn_cmd=1.0)
        self.assertGreater(dynamics.load_factor, 1.0)
        self.assertLess(dynamics.load_factor, dynamics.spec.max_load_factor_g - 0.5)

    def test_corner_speed_reaches_almost_max_g(self):
        """角点速度附近（约 250 m/s）应该接近最大过载。"""
        dynamics = make_dynamics(250.0)
        spec = dynamics.spec
        for _ in range(60):
            dynamics.step(DT, turn_cmd=1.0)
            dynamics.velocity = (
                dynamics.velocity.normalize() * 250.0
            )  # 保持角点速度，只看瞬时过载
        self.assertGreater(dynamics.load_factor, 0.95 * spec.max_load_factor_g)
        self.assertLessEqual(dynamics.load_factor, spec.max_load_factor_g + 1e-6)


class TurnPerformanceTest(unittest.TestCase):
    def test_turn_rate_matches_newton(self):
        """航迹角速度 = 垂直于速度方向的合力 / (m * V)，误差 < 1%。

        注意升力不是唯一的法向力：机头有攻角时推力也有法向分量
        （本机型满攻角时约占 3%），所以 n * g / V 只是近似值，
        真正精确的写法是下面这个投影式。
        """
        dynamics = make_dynamics(250.0)
        for _ in range(120):  # 先进入稳定盘旋
            dynamics.step(DT, turn_cmd=1.0)

        heading_before = dynamics.velocity_heading_deg
        velocity_before = Vector2(dynamics.velocity)
        dynamics.step(DT, turn_cmd=1.0)

        speed_before = velocity_before.length()
        ux, uy = velocity_before.x / speed_before, velocity_before.y / speed_before
        normal = Vector2(-uy, ux)  # 速度方向的法向（屏幕顺时针侧）
        normal_force = (
            dynamics.lift.dot(normal)
            + dynamics.thrust.dot(normal)
            + dynamics.drag.dot(normal)
        )
        expected = rad_to_deg(normal_force / (dynamics.spec.mass_kg * speed_before))
        measured = wrap_deg(dynamics.velocity_heading_deg - heading_before) / DT

        self.assertGreater(measured, 0.0)  # 右转：速度方向角增大
        self.assertAlmostEqual(measured, expected, delta=0.01 * expected + 1e-6)

        # 只用升力的近似式 n*g/V 应落在 5% 以内
        lift_only = rad_to_deg(dynamics.load_factor * G0 / speed_before)
        self.assertAlmostEqual(measured, lift_only, delta=0.05 * measured)

    def test_hard_turn_bleeds_energy(self):
        """有诱导阻力，硬拉杆必须掉速（能量战的物理基础）。"""
        dynamics = make_dynamics(250.0)
        for _ in range(180):  # 3 秒
            dynamics.step(DT, turn_cmd=1.0)
        self.assertLess(dynamics.speed, 250.0)

    def test_turn_command_direction(self):
        left = make_dynamics(250.0)
        right = make_dynamics(250.0)
        for _ in range(30):
            left.step(DT, turn_cmd=-1.0)
            right.step(DT, turn_cmd=1.0)
        # 屏幕坐标下 y 向下：正杆量向右（顺时针，heading 增大）
        self.assertLess(wrap_deg(left.velocity_heading_deg), 0.0)
        self.assertGreater(wrap_deg(right.velocity_heading_deg), 0.0)


class FixedStepTest(unittest.TestCase):
    def test_two_half_steps_match_one_full_step(self):
        """步长减半结果应基本一致：说明 60Hz 固定步长下的积分是收敛的。"""
        coarse = make_dynamics(250.0)
        fine = make_dynamics(250.0)
        for _ in range(60):  # 1 秒
            coarse.step(DT, turn_cmd=1.0)
            fine.step(DT / 2.0, turn_cmd=1.0)
            fine.step(DT / 2.0, turn_cmd=1.0)

        self.assertAlmostEqual(
            coarse.velocity_heading_deg, fine.velocity_heading_deg, delta=0.5
        )
        self.assertAlmostEqual(coarse.speed, fine.speed, delta=1.0)


if __name__ == "__main__":
    unittest.main()
