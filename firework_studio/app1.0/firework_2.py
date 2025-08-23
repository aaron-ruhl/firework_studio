import random
import threading
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QTimer
from particle import Particle
import numpy as np
class Firework:
    def __init__(self, x, y, color, pattern, display_number, particle_count, handle=None, explode_callback=None):
        self.x = x
        self.y = y
        # Ensure color is always a QColor instance
        if isinstance(color, tuple):
            self.color = QColor(*color)
        else:
            self.color = color
        self.pattern = pattern
        self.display_number = display_number
        self.particles = []
        self.exploded = False
        self.velocity_y = -random.uniform(10, 11)
        self.particle_count = particle_count
        self.delay = 2
        self.frozen = False
        self._explosion_time = None
        self._start_time = None
        self.handle = handle  # Store handle reference

        self.timer = QTimer()
        self.timer.setInterval(int(self.delay * 1000))
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._on_timer_timeout)
        self.timer.start()

        self._remaining_time = 0
        self.explode_callback = explode_callback  # External callback for threading

    def get_current_color(self):
        # If handle is provided and has an explosion color, use that
        if self.handle and hasattr(self.handle, 'explosion_color'):
            color = self.handle.explosion_color
            if not isinstance(color, QColor):
                return QColor(*color) if isinstance(color, tuple) else QColor(color)
            return color
        # Ensure self.color is a QColor
        if not isinstance(self.color, QColor):
            return QColor(*self.color) if isinstance(self.color, tuple) else QColor(self.color)
        return self.color

    def pause_explode(self):
        self.frozen = True
        if self.timer.isActive():
            self._remaining_time = self.timer.remainingTime()
            self.timer.stop()
        else:
            self._remaining_time = 0

    def resume_explode(self):
        self.frozen = False
        if not self.timer.isActive() and self._remaining_time > 0:
            self.timer.setInterval(self._remaining_time)
            self.timer.start()

    def _on_timer_timeout(self):
        # Call the external explode_callback if provided, otherwise call explode directly
        if self.explode_callback:
            self.explode_callback(self)
        else:
            self.explode()

    def explode(self):
        self.exploded = True
        base_color = self.get_current_color()
        distance_factor = 0.7

        def vibrant_color(color):
            hsv = color.toHsv()
            new_sat = min(255, int(hsv.saturation() * 1.3) + 60)
            new_val = min(255, int(hsv.value() * 1.2) + 40)
            return QColor.fromHsv(hsv.hue() if hsv.hue() is not None else 0, new_sat, new_val)

        def random_tail():
            tail_particles = []
            count = random.randint(2, 5)
            tail_angles = np.random.uniform(0, 2 * np.pi, count)
            tail_speeds = np.random.uniform(0.8, 1.5, count)
            tail_lifetimes = np.random.randint(18, 36, count)
            # Keep white flash particles pure white, don't apply vibrant_color
            tail_color = QColor(255, 255, 255, 180)
            for angle, speed, lifetime in zip(tail_angles, tail_speeds, tail_lifetimes):
                tail = Particle(self.x, self.y, angle, speed, tail_color, lifetime=lifetime)
                tail.gravity = 0.04
                tail_particles.append(tail)
            return tail_particles

        if self.pattern == "chrysanthemum":
            angles = np.linspace(0, 2 * np.pi, self.particle_count, endpoint=False)
            angles += np.random.uniform(-0.02, 0.02, self.particle_count)
            speeds = np.random.uniform(5.5, 7.2, self.particle_count) * distance_factor
            lifetimes = np.random.randint(160, 211, self.particle_count)
            fades = np.random.uniform(0.96, 0.99, self.particle_count)
            color = vibrant_color(base_color)
            for angle, speed, lifetime, fade_val in zip(angles, speeds, lifetimes, fades):
                p = Particle(self.x, self.y, angle, speed, color, lifetime=lifetime)
                p.gravity = 0.07
                p.fade = fade_val
                self.particles.append(p)
                # Reduce white particles in the middle of palm by decreasing trunk particles
                # and making random_tail less frequent for palm
                if random.random() < 0.5:  # Only add random_tail to half of trunks
                    self.particles.extend(random_tail())

        elif self.pattern == "palm":
            trunks = 8
            angles = np.linspace(0, 2 * np.pi, trunks, endpoint=False)
            angles += np.random.uniform(-0.08, 0.08, trunks)
            speeds = np.random.uniform(6.0, 7.5, trunks) * distance_factor
            for i in range(trunks):
                # White flash particles for the trunk effect
                trunk_color = QColor(255, 255, 255, 220)
                p1 = Particle(self.x, self.y, angles[i], speeds[i] * 0.7, trunk_color, lifetime=60)
                # Use user's chosen color for the main colorful explosion
                p2 = Particle(self.x, self.y, angles[i], speeds[i], vibrant_color(base_color), lifetime=130)
                p1.gravity = 0.08
                p2.gravity = 0.09
                self.particles.append(p1)
                self.particles.append(p2)
                burst_angles = angles[i] + np.random.uniform(-0.22, 0.22, 5)
                burst_speeds = speeds[i] * np.random.uniform(0.65, 0.95, 5)
                # Use user's chosen color for burst particles too
                burst_color = vibrant_color(base_color)
                for burst_angle, burst_speed in zip(burst_angles, burst_speeds):
                    p3 = Particle(self.x, self.y, burst_angle, burst_speed, burst_color, lifetime=90)
                    p3.gravity = 0.07
                    self.particles.append(p3)
                # Only add random_tail to some trunks to reduce white particles
                if i % 2 == 0:
                    self.particles.extend(random_tail())
        elif self.pattern == "willow":
            spread = np.pi * 0.8
            base_angle = np.pi / 2
            angles = base_angle - spread / 2 + spread * (np.arange(self.particle_count) / (self.particle_count - 1))
            angles += np.random.uniform(-0.04, 0.04, self.particle_count)
            speeds = np.random.uniform(4.2, 5.2, self.particle_count) * distance_factor
            lifetimes = np.random.randint(220, 261, self.particle_count)
            fades = np.random.uniform(0.94, 0.97, self.particle_count)
            # Use user's chosen color for willow effect
            willow_color = vibrant_color(base_color)
            for angle, speed, lifetime, fade_val in zip(angles, speeds, lifetimes, fades):
                p = Particle(self.x, self.y, angle, speed, willow_color, lifetime=lifetime)
                p.gravity = 0.11
                p.fade = fade_val
                self.particles.append(p)
                self.particles.extend(random_tail())
        elif self.pattern == "peony":
            angles = np.linspace(0, 2 * np.pi, self.particle_count, endpoint=False)
            angles += np.random.uniform(-0.02, 0.02, self.particle_count)
            speeds = np.random.uniform(5.0, 6.0, self.particle_count) * distance_factor
            lifetimes = np.random.randint(140, 181, self.particle_count)
            fades = np.random.uniform(0.96, 0.99, self.particle_count)
            hsv = base_color.toHsv()
            base_hue = hsv.hue() if hsv.hue() is not None else 0
            hues = (base_hue + np.random.randint(-18, 19, self.particle_count)) % 360
            peony_colors = [vibrant_color(QColor.fromHsv(int(hue), hsv.saturation(), hsv.value())) for hue in hues]
            for angle, speed, lifetime, fade_val, color in zip(angles, speeds, lifetimes, fades, peony_colors):
                p = Particle(self.x, self.y, angle, speed, color, lifetime=lifetime)
                p.gravity = 0.08
                p.fade = fade_val
                self.particles.append(p)
                self.particles.extend(random_tail())
        elif self.pattern == "ring":
            angles = np.linspace(0, 2 * np.pi, self.particle_count, endpoint=False)
            speeds = np.full(self.particle_count, 5.2 * distance_factor)
            lifetimes = np.random.randint(120, 151, self.particle_count)
            fades = np.random.uniform(0.97, 0.99, self.particle_count)
            # Use user's chosen color for ring effect
            ring_color = vibrant_color(base_color)
            for angle, speed, lifetime, fade_val in zip(angles, speeds, lifetimes, fades):
                p = Particle(self.x, self.y, angle, speed, ring_color, lifetime=lifetime)
                p.gravity = 0.06
                p.fade = fade_val
                self.particles.append(p)
                self.particles.extend(random_tail())
                
        elif self.pattern == "rainbow":
            # Special rainbow pattern that creates multi-colored particles
            angles = np.random.uniform(0, 2 * np.pi, self.particle_count)
            speeds = np.random.uniform(4.5, 6.0, self.particle_count) * distance_factor
            lifetimes = np.random.randint(120, 171, self.particle_count)
            fades = np.random.uniform(0.96, 0.99, self.particle_count)
            hues = (360 * np.arange(self.particle_count) / self.particle_count).astype(int)
            rainbow_colors = [vibrant_color(QColor.fromHsv(hue, 220, 255)) for hue in hues]
            for angle, speed, lifetime, fade_val, color in zip(angles, speeds, lifetimes, fades, rainbow_colors):
                p = Particle(self.x, self.y, angle, speed, color, lifetime=lifetime)
                p.gravity = 0.07
                p.fade = fade_val
                self.particles.append(p)
                self.particles.extend(random_tail())
        else:
            # Default circle pattern - use the explosion color instead of rainbow
            angles = np.random.uniform(0, 2 * np.pi, self.particle_count)
            speeds = np.random.uniform(4.5, 6.0, self.particle_count) * distance_factor
            lifetimes = np.random.randint(120, 171, self.particle_count)
            fades = np.random.uniform(0.96, 0.99, self.particle_count)
            # Use the explosion color instead of rainbow colors
            circle_color = vibrant_color(base_color)
            for angle, speed, lifetime, fade_val in zip(angles, speeds, lifetimes, fades):
                p = Particle(self.x, self.y, angle, speed, circle_color, lifetime=lifetime)
                p.gravity = 0.07
                p.fade = fade_val
                self.particles.append(p)
                self.particles.extend(random_tail())

    def update(self, current_time):
        if not self.exploded and not self.frozen:
            self.y += self.velocity_y
            self.velocity_y += 0.1
            if self._explosion_time is not None and current_time >= self._explosion_time:
                self.explode()
            else:
                self.check_explode(current_time)
        else:
            self.particles = [p for p in self.particles if p.update()]
        return len(self.particles) > 0 or not self.exploded

    def check_explode(self, current_time):
        # Default behavior: explode after a delay if _start_time is set
        if self._start_time is None:
            self._start_time = current_time
        if current_time - self._start_time >= self.delay:
            self._explosion_time = current_time
            self.explode()

    def draw(self, gl):
        if not self.exploded:
            # Draw the firework shell as a point or small circle
            shell_color = self.get_current_color()
            gl.glColor4f(shell_color.redF(), shell_color.greenF(), shell_color.blueF(), 1.0)
            gl.glPointSize(6)
            gl.glBegin(gl.GL_POINTS)
            gl.glVertex2f(self.x, self.y)
            gl.glEnd()
        else:
            for p in self.particles:
                p.draw(gl)