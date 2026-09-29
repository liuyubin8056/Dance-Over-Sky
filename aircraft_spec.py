"""机型参数：从 JSON 读取，物理层不写死任何数字。

加新机型 = 加一个 data/<型号>.json，不用改代码。
``thrust_curve_coeffs`` 是可选推力曲线（关于速度 v 的多项式系数，
从常数项开始），为空时使用恒定推力 ``thrust_max_n``。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Tuple

from angles import rad_to_deg

G0 = 9.80665  # 标准重力加速度 m/s^2


@dataclass(frozen=True)
class AircraftSpec:
    """一个机型的全部参数（质量、气动、结构限制、外观）。"""

    name: str
    mass_kg: float
    wing_area_m2: float
    aspect_ratio: float
    oswald_efficiency: float
    cd0: float
    cl_alpha_per_rad: float
    cl_max: float
    max_load_factor_g: float
    thrust_max_n: float
    turn_rate_max_dps: float
    thrust_curve_coeffs: Optional[Sequence[float]] = None
    icon: str = "images/f-16.jpg"
    icon_size_px: Tuple[int, int] = (50, 30)
    notes: str = ""

    @property
    def induced_drag_k(self) -> float:
        """诱导阻力因子 k = 1 / (pi * e * AR)，用于 Cd = Cd0 + k * CL^2。"""
        return 1.0 / (3.141592653589793 * self.oswald_efficiency * self.aspect_ratio)

    @property
    def alpha_stall_deg(self) -> float:
        """失速攻角（把 cl_max 当作线性升力线的终点）。"""
        return rad_to_deg(self.cl_max / self.cl_alpha_per_rad)

    @property
    def thrust_to_weight(self) -> float:
        return self.thrust_max_n / (self.mass_kg * G0)

    @classmethod
    def from_json(cls, path: str) -> "AircraftSpec":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        icon_size = data.get("icon_size_px", (50, 30))
        return cls(
            name=str(data["name"]),
            mass_kg=float(data["mass_kg"]),
            wing_area_m2=float(data["wing_area_m2"]),
            aspect_ratio=float(data["aspect_ratio"]),
            oswald_efficiency=float(data["oswald_efficiency"]),
            cd0=float(data["cd0"]),
            cl_alpha_per_rad=float(data["cl_alpha_per_rad"]),
            cl_max=float(data["cl_max"]),
            max_load_factor_g=float(data["max_load_factor_g"]),
            thrust_max_n=float(data["thrust_max_n"]),
            turn_rate_max_dps=float(data["turn_rate_max_dps"]),
            thrust_curve_coeffs=data.get("thrust_curve_coeffs"),
            icon=str(data.get("icon", "images/f-16.jpg")),
            icon_size_px=(int(icon_size[0]), int(icon_size[1])),
            notes=str(data.get("notes", "")),
        )
