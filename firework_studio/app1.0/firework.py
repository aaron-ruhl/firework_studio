import random
import math
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor

from particle import Particle
import threading


class Firework:
    def __init__(self, x, y, color, pattern, display_number, particle_count):
        self.x = x
        self.y = y
        self.color = color
        self.pattern = pattern
        self.display_number = display_number
        self.particles = []
        self.exploded = False
        self.velocity_y = -random.uniform(11.3, 11.8)
        self.particle_count = particle_count
        self.delay = 2
        self.timer = QTimer()
        self.timer.setInterval(int(self.delay * 1000))
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._start_explode_thread)
        self.timer.start()
        self.frozen = False
        self._pause_event = threading.Event()
        self._pause_event.set()

    def pause_explode(self):
        self.frozen = True
        self._pause_event.clear()
        if self.timer.isActive():
            self._remaining_time = self.timer.remainingTime()
            self.timer.stop()
        else:
            self._remaining_time = 0

    def resume_explode(self):
        self.frozen = False
        self._pause_event.set()
        if not self.timer.isActive() and hasattr(self, '_remaining_time') and self._remaining_time > 0:
            self.timer.setInterval(self._remaining_time)
            self.timer.start()
        
    def _start_explode_thread(self):
        # Run explosion logic in a separate thread to avoid UI blocking
        thread = threading.Thread(target=self.explode)
        thread.start()

    def explode(self):
        self.exploded = True
        base_color = self.color

        distance_factor = 0.5
        fade_factor = 0.8

        def vibrant_color(color):
            hsv = color.toHsv()
            new_sat = min(255, int(hsv.saturation() * 1.2) + 40)
            new_val = min(255, int(hsv.value() * 1.15) + 30)
            return QColor.fromHsv(hsv.hue() if hsv.hue() is not None else 0, new_sat, new_val)

        if self.pattern == "chrysanthemum":
            for i in range(self.particle_count):
                angle = 2 * math.pi * i / self.particle_count
                speed = random.uniform(4.2, 5.0) * distance_factor
                if i % 7 == 0:
                    speed *= 1.18
                    color = vibrant_color(QColor(255, 255, 255, 220))
                else:
                    hsv = base_color.toHsv()
                    hue_shift = random.randint(-18, 18)
                    new_hue = (hsv.hue() + hue_shift) % 360 if hsv.hue() is not None else 0
                    sat = min(255, int(hsv.saturation() * 1.2) + random.randint(20, 40))
                    val = min(255, int(hsv.value() * 1.15) + random.randint(20, 40))
                    color = QColor.fromHsv(new_hue, sat, val)
                p = Particle(self.x, self.y, angle, speed, color, lifetime=int(random.randint(130, 155) * fade_factor))
                self.particles.append(p)
        elif self.pattern == "palm":
            trunks = 8
            for i in range(trunks):
                angle = 2 * math.pi * i / trunks + random.uniform(-0.08, 0.08)
                speed = random.uniform(4.5, 5.5) * distance_factor
                trunk_color = vibrant_color(QColor(60, 255, 120))
                p1 = Particle(self.x, self.y, angle, speed * 0.7, vibrant_color(QColor(255, 255, 180, 220)), lifetime=int(45 * fade_factor))
                p2 = Particle(self.x, self.y, angle, speed, trunk_color, lifetime=int(100 * fade_factor))
                self.particles.append(p1)
                self.particles.append(p2)
                for j in range(4):
                    burst_angle = angle + random.uniform(-0.18, 0.18)
                    burst_speed = speed * random.uniform(0.65, 0.95)
                    burst_color = vibrant_color(QColor(255, 200, 80))
                    p3 = Particle(self.x, self.y, burst_angle, burst_speed, burst_color, lifetime=int(75 * fade_factor))
                    self.particles.append(p3)
        elif self.pattern == "willow":
            for i in range(self.particle_count):
                base_angle = math.pi / 2
                spread = math.pi * 0.7
                angle = base_angle - spread / 2 + spread * (i / (self.particle_count - 1)) + random.uniform(-0.03, 0.03)
                speed = random.uniform(3.2, 3.8) * distance_factor
                if i % 10 == 0:
                    willow_color = vibrant_color(QColor(255, 255, 180, 220))
                else:
                    willow_color = vibrant_color(QColor(255, 220, 120, 220))
                p = Particle(self.x, self.y, angle, speed, willow_color, lifetime=int(200 * fade_factor))
                p.gravity = 0.09
                self.particles.append(p)
        elif self.pattern == "peony":
            for i in range(self.particle_count):
                angle = 2 * math.pi * i / self.particle_count + random.uniform(-0.01, 0.01)
                speed = random.uniform(4.0, 4.5) * distance_factor
                hsv = base_color.toHsv()
                hue = (hsv.hue() + random.randint(-10, 10)) % 360 if hsv.hue() is not None else 0
                peony_color = vibrant_color(QColor.fromHsv(hue, hsv.saturation(), hsv.value()))
                p = Particle(self.x, self.y, angle, speed, peony_color, lifetime=int(110 * fade_factor))
                self.particles.append(p)
        elif self.pattern == "ring":
            for i in range(self.particle_count):
                angle = 2 * math.pi * i / self.particle_count
                speed = 4.2 * distance_factor
                if i % 8 == 0:
                    ring_color = vibrant_color(QColor(255, 255, 255, 220))
                else:
                    ring_color = vibrant_color(QColor(80, 255, 255, 220))
                p = Particle(self.x, self.y, angle, speed, ring_color, lifetime=int(120 * fade_factor))
                self.particles.append(p)
        else:
            for i in range(self.particle_count):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(3.5, 4.2) * distance_factor
                hue = int(360 * i / self.particle_count)
                rainbow_color = vibrant_color(QColor.fromHsv(hue, 220, 255))
                if random.random() < 0.18:
                    sparkle_color = vibrant_color(QColor(255, 255, random.randint(220, 255), 220))
                    p = Particle(self.x, self.y, angle, speed * 1.08, sparkle_color, lifetime=int(130 * fade_factor))
                    self.particles.append(p)
                elif random.random() < 0.08:
                    white_color = vibrant_color(QColor(255, 255, 255, 220))
                    p = Particle(self.x, self.y, angle, speed, white_color, lifetime=int(110 * fade_factor))
                    self.particles.append(p)
                else:
                    p = Particle(self.x, self.y, angle, speed, rainbow_color, lifetime=int(random.randint(100, 130) * fade_factor))
                    self.particles.append(p)

    def update(self, current_time):
        if not self.exploded and not self.frozen:
            self.y += self.velocity_y
            self.velocity_y += 0.1
            if self.timer.remainingTime() == 0:
                self._start_explode_thread()
        else:
            self.particles = [p for p in self.particles if p.update()]
        return len(self.particles) > 0 or not self.exploded
