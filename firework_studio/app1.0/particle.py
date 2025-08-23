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
        self.fade = 2  # Base fade value
        self.dynamic_fade_multiplier = 1.0  # Additional multiplier for dynamic fading

    def freeze(self):
        self._frozen = True

    def resume(self):
        self._frozen = False

    def is_frozen(self):
        return getattr(self, '_frozen', False)

    def set_dynamic_fade_multiplier(self, multiplier):
        """Set the dynamic fade multiplier to speed up fading when there are many fireworks"""
        self.dynamic_fade_multiplier = multiplier

    def update(self):
        if self.is_frozen():
            return self.current_life > 0
        self.velocity_y += self.gravity
        self.x += self.velocity_x
        self.y += self.velocity_y
        # Apply dynamic fading - reduce life faster when there are many fireworks
        life_reduction = int(1 * self.dynamic_fade_multiplier)
        self.current_life -= max(1, life_reduction)
        return self.current_life > 0
    
    def get_color(self):
        # Apply both base fade and dynamic fade multiplier
        effective_fade = self.fade * self.dynamic_fade_multiplier
        fade = (self.current_life / self.lifetime) ** effective_fade
        return QColor(
            self.color.red(),
            self.color.green(),
            self.color.blue(),
            int(255 * fade)
        )