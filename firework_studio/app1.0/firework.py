import random
import math
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor

from particle import Particle
import threading


class Firework:
    def __init__(self, x, y, color, pattern, display_number, number_firings, particle_count):
        self.x = x
        self.y = y
        self.color = color
        self.pattern = pattern
        self.number_firings = number_firings
        self.display_number = display_number
        self.particles = []
        self.exploded = False
        self.velocity_y = -random.uniform(11.5, 12.2)
        self.particle_count = particle_count
        self.delay = 2
        self.timer = QTimer()
        self.timer.setInterval(int(self.delay * 1000))
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._start_explode_thread)
        self.timer.start()

    def _start_explode_thread(self):
        # Run explosion logic in a separate thread to avoid UI blocking
        thread = threading.Thread(target=self.explode)
        thread.start()

    def explode(self):
        self.exploded = True
        base_color = self.color

        distance_factor = 0.3
        fade_factor = 0.4

        def far_color(color):
            hsv = color.toHsv()
            new_sat = int(hsv.saturation() * 0.55)
            new_val = int(hsv.value() * 0.7)
            return QColor.fromHsv(hsv.hue() if hsv.hue() is not None else 0, new_sat, new_val)

        def add_trail_particle(x, y, angle, speed, color, lifetime):
            hsv = color.toHsv()
            trail_hue = hsv.hue() if hsv.hue() is not None else 0
            trail_sat = int(hsv.saturation() * 0.45)
            trail_val = int(hsv.value() * 0.55)
            trail_color = QColor.fromHsv(trail_hue, trail_sat, trail_val, 120)
            trail_angle = angle + random.uniform(-0.08, 0.08)
            trail_speed = speed * random.uniform(0.35, 0.55)
            trail_particle = Particle(x, y, trail_angle, trail_speed, trail_color, lifetime=int(lifetime * 1.3))
            trail_particle.gravity = 0.07
            self.particles.append(trail_particle)

        if self.pattern == "chrysanthemum":
            for i in range(self.particle_count):
                angle = 2 * math.pi * i / self.particle_count
                speed = random.uniform(4.2, 5.0) * distance_factor
                if i % 7 == 0:
                    speed *= 1.18
                    color = far_color(QColor(220, 220, 220, 180))
                else:
                    hsv = base_color.toHsv()
                    hue_shift = random.randint(-18, 18)
                    new_hue = (hsv.hue() + hue_shift) % 360 if hsv.hue() is not None else 0
                    sat = min(255, int(hsv.saturation() * 0.55) + random.randint(-10, 18))
                    val = min(255, int(hsv.value() * 0.7) + random.randint(-10, 10))
                    color = QColor.fromHsv(new_hue, sat, val)
                p = Particle(self.x, self.y, angle, speed, color, lifetime=int(random.randint(130, 155) * fade_factor))
                self.particles.append(p)
                add_trail_particle(self.x, self.y, angle, speed, color, lifetime=int(random.randint(130, 155) * fade_factor))
        elif self.pattern == "palm":
            trunks = 8
            for i in range(trunks):
                angle = 2 * math.pi * i / trunks + random.uniform(-0.08, 0.08)
                speed = random.uniform(4.5, 5.5) * distance_factor
                trunk_color = far_color(QColor(60, 255, 120))
                p1 = Particle(self.x, self.y, angle, speed * 0.7, far_color(QColor(220, 220, 180, 180)), lifetime=int(45 * fade_factor))
                p2 = Particle(self.x, self.y, angle, speed, trunk_color, lifetime=int(100 * fade_factor))
                self.particles.append(p1)
                self.particles.append(p2)
                add_trail_particle(self.x, self.y, angle, speed, trunk_color, lifetime=int(100 * fade_factor))
                for j in range(4):
                    burst_angle = angle + random.uniform(-0.18, 0.18)
                    burst_speed = speed * random.uniform(0.65, 0.95)
                    burst_color = far_color(QColor(255, 200, 80))
                    p3 = Particle(self.x, self.y, burst_angle, burst_speed, burst_color, lifetime=int(75 * fade_factor))
                    self.particles.append(p3)
                    add_trail_particle(self.x, self.y, burst_angle, burst_speed, burst_color, lifetime=int(75 * fade_factor))
        elif self.pattern == "willow":
            for i in range(self.particle_count):
                base_angle = math.pi / 2
                spread = math.pi * 0.7
                angle = base_angle - spread / 2 + spread * (i / (self.particle_count - 1)) + random.uniform(-0.03, 0.03)
                speed = random.uniform(3.2, 3.8) * distance_factor
                if i % 10 == 0:
                    willow_color = far_color(QColor(240, 230, 180, 180))
                else:
                    willow_color = far_color(QColor(220, 200, 120, 180))
                p = Particle(self.x, self.y, angle, speed, willow_color, lifetime=int(200 * fade_factor))
                p.gravity = 0.09
                self.particles.append(p)
                add_trail_particle(self.x, self.y, angle, speed, willow_color, lifetime=int(200 * fade_factor))
        elif self.pattern == "peony":
            for i in range(self.particle_count):
                angle = 2 * math.pi * i / self.particle_count + random.uniform(-0.01, 0.01)
                speed = random.uniform(4.0, 4.5) * distance_factor
                hsv = base_color.toHsv()
                hue = (hsv.hue() + random.randint(-10, 10)) % 360 if hsv.hue() is not None else 0
                peony_color = far_color(QColor.fromHsv(hue, hsv.saturation(), hsv.value()))
                p = Particle(self.x, self.y, angle, speed, peony_color, lifetime=int(110 * fade_factor))
                self.particles.append(p)
                if i % 3 == 0:
                    add_trail_particle(self.x, self.y, angle, speed, peony_color, lifetime=int(110 * fade_factor))
        elif self.pattern == "ring":
            for i in range(self.particle_count):
                angle = 2 * math.pi * i / self.particle_count
                speed = 4.2 * distance_factor
                if i % 8 == 0:
                    ring_color = far_color(QColor(220, 220, 220, 180))
                else:
                    ring_color = far_color(QColor(80, 200, 200, 180))
                p = Particle(self.x, self.y, angle, speed, ring_color, lifetime=int(120 * fade_factor))
                self.particles.append(p)
                if abs(math.sin(angle)) > 0.8:
                    add_trail_particle(self.x, self.y, angle, speed, ring_color, lifetime=int(120 * fade_factor))
        else:
            for i in range(self.particle_count):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(3.5, 4.2) * distance_factor
                hue = int(360 * i / self.particle_count)
                rainbow_color = far_color(QColor.fromHsv(hue, 140, 180))
                if random.random() < 0.18:
                    sparkle_color = far_color(QColor(220, 220, random.randint(180, 220), 180))
                    p = Particle(self.x, self.y, angle, speed * 1.08, sparkle_color, lifetime=int(130 * fade_factor))
                    self.particles.append(p)
                    add_trail_particle(self.x, self.y, angle, speed * 1.08, sparkle_color, lifetime=int(130 * fade_factor))
                elif random.random() < 0.08:
                    white_color = far_color(QColor(220, 220, 220, 180))
                    p = Particle(self.x, self.y, angle, speed, white_color, lifetime=int(110 * fade_factor))
                    self.particles.append(p)
                    add_trail_particle(self.x, self.y, angle, speed, white_color, lifetime=int(110 * fade_factor))
                else:
                    p = Particle(self.x, self.y, angle, speed, rainbow_color, lifetime=int(random.randint(100, 130) * fade_factor))
                    self.particles.append(p)
                    add_trail_particle(self.x, self.y, angle, speed, rainbow_color, lifetime=int(random.randint(100, 130) * fade_factor))

    def update(self):
        if not self.exploded:
            self.y += self.velocity_y
            self.velocity_y += 0.1
            if self.timer.remainingTime() == 0:
                self._start_explode_thread()
        else:
            self.particles = [p for p in self.particles if p.update()]
        return len(self.particles) > 0 or not self.exploded
