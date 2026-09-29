"""世界：以米为单位保存所有实体，按固定步长推进。"""
from __future__ import annotations


class World:
    def __init__(self):
        self.entities = []
        self.time = 0.0

    def add(self, entity) -> None:
        self.entities.append(entity)

    def update(self, dt: float) -> None:
        for entity in self.entities:
            entity.update(dt)
        self.time += dt

    def draw(self, screen, camera) -> None:
        for entity in self.entities:
            entity.draw(screen, camera)
