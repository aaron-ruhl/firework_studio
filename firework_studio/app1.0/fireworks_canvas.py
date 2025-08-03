import random
import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor, QPainter, QPen


'''THIS SECTION CONTAINS THE CODE FOR FIREWORKS SHOW PREVIEW AND PARTICLE EFFECTS'''
class FireworksCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.fireworks = []
        self.background_color = QColor(0, 0, 0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # ~60 FPS
        self.particle_count = 50
        self.firework_color = QColor(255, 0, 0)
        self.pattern = None
        self.background = None
        self.fired_times = set()  # Track fired times

    def add_firework(self, x=None):
        if x is None:
            x = random.randint(0, self.width())
        self.fireworks.append(Firework(x, self.height(), 
                                     self.firework_color,
                                     self.particle_count))

    def update_animation(self):
        self.fireworks = [fw for fw in self.fireworks if fw.update()]
        parent = self.parentWidget()
        preview_widget = None
        # Import here to avoid circular import
        from firework_show_app import FireworkShowApp
        while parent:
            if isinstance(parent, FireworkShowApp):
                preview_widget = parent.preview_widget
                break
            parent = parent.parentWidget()
        if preview_widget and preview_widget.firework_firing is not None:
            time_list = preview_widget.firework_firing
            for t in time_list:
                if abs(preview_widget.current_time - t) < 0.1 and t not in self.fired_times:
                    self.add_firework()
                    self.fired_times.add(t)
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background
        painter.fillRect(self.rect(), self.background_color)

        # Draw fireworks
        for firework in self.fireworks:
            if not firework.exploded:
                painter.setPen(QPen(firework.color, 4))
                painter.drawPoint(int(firework.x), int(firework.y))
            else:
                for particle in firework.particles:
                    color = particle.get_color()
                    painter.setPen(QPen(color, 2))
                    painter.drawPoint(int(particle.x), int(particle.y))
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

class Firework:
    def __init__(self, x, y, color, particle_count=50):
        self.x = x
        self.y = y
        self.color = color
        self.particles = []
        self.exploded = False
        self.velocity_y = -random.uniform(7, 10)
        self.particle_count = particle_count

    def explode(self):
        self.exploded = True
        for _ in range(self.particle_count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3.7, 5)
            self.particles.append(Particle(self.x, self.y, angle, speed, self.color))

    def update(self):
        if not self.exploded:
            self.y += self.velocity_y
            self.velocity_y += 0.1
            if self.velocity_y >= 0:
                self.explode()
        else:
            self.particles = [p for p in self.particles if p.update()]
        return len(self.particles) > 0 or not self.exploded