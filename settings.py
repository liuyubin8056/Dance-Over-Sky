class Settings:
    """全局设置（循环、渲染、相机与环境）。

    机型相关的数据不写在这里，放到 data/*.json，见 aircraft_spec.py。
    """

    def __init__(self):
        # 显示
        self.screen_width = 800
        self.screen_height = 600
        self.bg_color = (10, 10, 10)

        # 时间：物理步长固定 60Hz，渲染帧率与之解耦
        self.physics_hz = 60
        self.render_fps = 60
        self.max_frame_time = 0.25  # 单帧最多补算的真实时间，防止卡顿后疯狂追帧
        self.max_steps_per_frame = 8  # 单帧最多补算的物理步数

        # 相机与尺度：世界坐标一律用米，1 像素 = meters_per_pixel 米
        self.meters_per_pixel = 10.0
        self.min_meters_per_pixel = 1.0
        self.max_meters_per_pixel = 60.0
        self.zoom_step = 1.25
        self.camera_follow = True  # 相机跟随玩家（关掉就是固定沙盘视角）

        # 环境与初始状态
        self.air_density = 0.660  # 6000m 标准大气密度 kg/m^3
        self.initial_speed = 250.0  # m/s
        self.spawn_gap_m = 3500.0  # 敌机出生在玩家正前方（+x 方向）的距离

        # 资源
        self.player_spec_path = 'data/f16.json'
        self.enemy_spec_path = 'data/f16.json'

        # 背景网格（位置参考）：间距按当前缩放自适应
        self.grid_enabled = True
        self.grid_min_pixels = 48.0
        self.grid_max_pixels = 160.0
        self.grid_major_every = 5
        self.grid_color_minor = (26, 30, 36)
        self.grid_color_major = (44, 52, 62)
        self.grid_color_origin = (78, 100, 122)
        self.grid_label_color = (118, 138, 150)

        # 调试
        self.show_debug = True

    @property
    def physics_dt(self):
        """固定物理步长（秒）。"""
        return 1.0 / self.physics_hz
