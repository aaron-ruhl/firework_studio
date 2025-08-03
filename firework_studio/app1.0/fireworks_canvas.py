import random
import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, QPointF
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
    def reset_fireworks(self):
        self.fireworks.clear()
        self.fired_times.clear()

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

        # Draw background - night sky with a coastline
        # Draw sky gradient
        from PyQt6.QtGui import QLinearGradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(10, 10, 40))
        gradient.setColorAt(0.7, QColor(20, 20, 60))
        gradient.setColorAt(1.0, QColor(30, 30, 80))
        painter.fillRect(self.rect(), gradient)

        # Draw stars
        star_count = 120
        for _ in range(star_count):
            x = random.randint(0, self.width())
            y = random.randint(0, int(self.height() * 0.5))
            brightness = random.randint(180, 255)
            painter.setPen(QColor(brightness, brightness, brightness))
            painter.drawPoint(x, y)

        # Draw moon
        moon_radius = 28
        moon_x = int(self.width() * 0.8)
        moon_y = int(self.height() * 0.18)
        painter.setBrush(QColor(230, 230, 210, 220))
        painter.setPen(QColor(230, 230, 210, 220))
        painter.drawEllipse(moon_x, moon_y, moon_radius, moon_radius)

        # Draw coastline silhouette
        coastline_height = int(self.height() * 0.15)
        coastline_y = self.height() - coastline_height
        painter.setPen(QColor(10, 10, 20))
        painter.setBrush(QColor(10, 10, 20))
        # Draw a wavy coastline
        path = []
        for i in range(0, self.width(), 10):
            wave = math.sin(i * 0.03) * 10 + math.cos(i * 0.015) * 7
            path.append((i, coastline_y + wave))
        path.append((self.width(), self.height()))
        path.append((0, self.height()))
        painter.drawPolygon(*[QPointF(x, y) for x, y in path])

        water_rect = self.rect()
        water_rect.setTop(coastline_y)
        water_gradient = QLinearGradient(0, coastline_y, 0, self.height())
        water_gradient.setColorAt(0.0, QColor(30, 40, 90, 180))
        water_gradient.setColorAt(1.0, QColor(10, 20, 40, 220))
        painter.fillRect(water_rect, water_gradient)
        painter.fillRect(water_rect, water_gradient)

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
        # Use a brighter color palette for particles
        base_color = self.color
        for _ in range(self.particle_count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(4.5, 7)  # Faster, more energetic
            # Vary color for brilliance
            hue_shift = random.randint(-30, 30)
            hsv = base_color.toHsv()
            new_hue = (hsv.hue() + hue_shift) % 360 if hsv.hue() is not None else 0
            new_color = QColor.fromHsv(new_hue, 255, 255)
            # Add a few "sparkle" particles with white/yellow
            if random.random() < 0.15:
                sparkle_color = QColor(255, 255, random.randint(180, 255))
                self.particles.append(Particle(self.x, self.y, angle, speed * 1.2, sparkle_color, lifetime=120))
            else:
                self.particles.append(Particle(self.x, self.y, angle, speed, new_color, lifetime=random.randint(90, 120)))

    def update(self):
        if not self.exploded:
            self.y += self.velocity_y
            self.velocity_y += 0.1
            if self.velocity_y >= 0:
                self.explode()
        else:
            self.particles = [p for p in self.particles if p.update()]
        return len(self.particles) > 0 or not self.exploded