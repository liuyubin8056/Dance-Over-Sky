import os
import unittest

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from camera import Camera


class CameraTest(unittest.TestCase):
    def setUp(self):
        self.camera = Camera((800, 600), meters_per_pixel=10.0)

    def test_center_maps_to_screen_center(self):
        self.assertEqual(self.camera.world_to_screen((0.0, 0.0)), (400.0, 300.0))

    def test_scale_100m_is_10px(self):
        px, py = self.camera.world_to_screen((100.0, 0.0))
        self.assertAlmostEqual(px, 410.0)
        self.assertAlmostEqual(py, 300.0)

    def test_screen_to_world_round_trip(self):
        world = (1234.0, -567.0)
        px, py = self.camera.world_to_screen(world)
        back = self.camera.screen_to_world(px, py)
        self.assertAlmostEqual(back.x, world[0], places=6)
        self.assertAlmostEqual(back.y, world[1], places=6)

    def test_look_at_shifts_view(self):
        self.camera.look_at((1000.0, 500.0))
        self.assertEqual(self.camera.world_to_screen((1000.0, 500.0)), (400.0, 300.0))

    def test_zoom_limits(self):
        self.camera.set_meters_per_pixel(0.01, low=1.0, high=60.0)
        self.assertAlmostEqual(self.camera.meters_per_pixel, 1.0)
        self.camera.set_meters_per_pixel(1000.0, low=1.0, high=60.0)
        self.assertAlmostEqual(self.camera.meters_per_pixel, 60.0)

    def test_visible_size(self):
        self.assertAlmostEqual(self.camera.visible_width_m(), 8000.0)
        self.assertAlmostEqual(self.camera.visible_height_m(), 6000.0)


if __name__ == "__main__":
    unittest.main()
