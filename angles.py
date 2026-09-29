"""角度与朝向工具（全项目统一的坐标、角度约定）。

**改动任何涉及角度/朝向的代码之前，先读这一页。**

约定
----
1. 坐标：世界坐标和屏幕坐标都是 x 向右、y 向下（pygame 默认）。
2. heading（机头指向 / 速度方向角）：以 +x 为 0°，顺时针为正，范围 (-180, 180]。

       0°  → 右        90° → 下（屏幕下方）      -90° → 上        180° → 左

3. heading 与 pygame 的关系：本模块的 heading 就是
   ``Vector2.from_polar((r, heading))`` 里的角度。注意 pygame 的
   ``Vector2.angle_to()`` 返回的是「从 self 转到 other」的角度，符号与 heading
   相反：``Vector2(1, 0).angle_to(Vector2(0, 1)) == 90``，而 ``Vector2(0, 1)``
   的 heading 是 +90、``Vector2(1, 0)`` 的 heading 是 0，所以
   ``v.angle_to(Vector2(1, 0)) == -heading(v)``。

   **不要用 angle_to 反推 heading**，请用 :func:`vector_heading_deg`。
   （初版代码就是在这里把攻角的符号弄反的：机头与速度同向朝上飞时算出 180° 攻角。）

4. 攻角 ``alpha = wrap_deg(heading - velocity_heading)``，
   正值表示机头偏向速度方向的顺时针侧（屏幕上看是下方那一侧）。
"""
from __future__ import annotations

import math

__all__ = [
    "wrap_deg",
    "deg_to_rad",
    "rad_to_deg",
    "angle_diff_deg",
    "vector_heading_deg",
    "heading_to_unit",
]


def wrap_deg(deg: float) -> float:
    """把任意角度规整到 (-180, 180]。"""
    d = math.fmod(float(deg), 360.0)
    if d <= -180.0:
        d += 360.0
    elif d > 180.0:
        d -= 360.0
    return d


def deg_to_rad(deg: float) -> float:
    return math.radians(deg)


def rad_to_deg(rad: float) -> float:
    return math.degrees(rad)


def angle_diff_deg(a: float, b: float) -> float:
    """a 相对 b 的最小夹角，范围 (-180, 180]。"""
    return wrap_deg(a - b)


def vector_heading_deg(x: float, y: float) -> float:
    """矢量的朝向角（度）。零矢量返回 0。"""
    if x == 0.0 and y == 0.0:
        return 0.0
    return math.degrees(math.atan2(y, x))


def heading_to_unit(deg: float) -> tuple:
    """heading 转单位矢量，与 Vector2.from_polar((1, deg)) 等价。"""
    rad = math.radians(deg)
    return (math.cos(rad), math.sin(rad))
