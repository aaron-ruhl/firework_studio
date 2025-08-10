import math
from PyQt6.QtGui import QColor


class Particle:
    def __init__(self, x, y, angle, speed, color, lifetime=100):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.color = color
        self.lifetime = lifetime
        self.current_life = lifetime
        self.gravity = 0.1
        self.velocity_x = math.cos(angle) * speed
        self.velocity_y = math.sin(angle) * speed

    def update(self):
        self.velocity_y += self.gravity
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.current_life -= 1
        return self.current_life > 0

    def get_color(self):
        fade = self.current_life / self.lifetime
        return QColor(
            self.color.red(),
            self.color.green(),
            self.color.blue(),
            int(255 * fade)
        )