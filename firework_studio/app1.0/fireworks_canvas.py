import random
import math
import numpy as np
from scipy.interpolate import make_interp_spline

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, QPointF, Qt, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QLinearGradient, QRadialGradient, QPainterPath, QPixmap

from firework import Firework

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
        self.background = None
        self.fired_times = set()  # Track (firing_time, firing_index)
        self._fireworks_enabled = True  # Initialize attribute
        self.delay = 2.0  # Delay for fireworks to explode
        self.background = "night"  # Default background
        self.custom_background_image_path = None
        self.pattern = "circle"
        self._dynamic_stars = None
        self._star_tick = 0
        self._city_window_states = None
        self._city_window_ticks = 0
        self._city_stars = None
        self._mountain_stars = None
        self._custom_bg_pixmap = None

    def choose_firework_pattern(self, pattern):
        self.pattern = pattern

    def add_firework(self, handle, x=None):
        margin = 40
        x = random.randint(margin, max(margin, self.width() - margin))
        firework = Firework(x, self.height(),
                            handle.firing_color, handle.pattern,
                            handle.display_number,
                            self.particle_count)
        self.fireworks.append(firework)

    def reset_fireworks(self):
        self.fireworks.clear()
        self.fired_times.clear()
    
    def set_background(self, background, path=None):
        self.background = background
        if background == "custom" and path:
            self.custom_background_image_path = path
            self._custom_bg_pixmap = QPixmap(path)
        else:
            self._custom_bg_pixmap = None
        # Reset cached background elements so they redraw for new background
        self._dynamic_stars = None
        self._city_window_states = None
        self._city_stars = None
        self._mountain_stars = None
        self.update()
    
    def reset_firings(self):
        self.fired_times.clear()
    
    def set_fireworks_enabled(self, enabled: bool):
        self._fireworks_enabled = enabled
    
    def update_animation(self):
        if not self._fireworks_enabled:
            return
        self.fireworks = [fw for fw in self.fireworks if fw.update()]
        parent = self.parentWidget()
        preview_widget = None
        # Import here to avoid circular import
        from firework_show_app import FireworkShowApp
        # Find the parent FireworkShowApp to access firework_firing
        while parent:
            if isinstance(parent, FireworkShowApp):
                preview_widget = parent.preview_widget
                break
            parent = parent.parentWidget()
        if preview_widget and preview_widget.firework_times is not None:
            handles = preview_widget.fireworks
            for handle in handles:
                if (preview_widget.current_time >= handle.firing_time - self.delay and
                        preview_widget.current_time < handle.firing_time and
                        (handle.firing_time, 0) not in self.fired_times):
                    for _ in range(handle.number_firings):
                        # Add firework at random x position
                        self.add_firework(handle)
                    self.fired_times.add((handle.firing_time, 0))
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.background == "night":
            self.draw_background_night(painter)
        elif self.background == "sunset":
            self.draw_background_sunset(painter)
        elif self.background == "city":
            self.draw_background_city(painter)
        elif self.background == "mountains":
            self.draw_background_mountains(painter)
        elif self.background == "custom":
            if self._custom_bg_pixmap:
                painter.drawPixmap(self.rect(), self._custom_bg_pixmap)
        # Draw fireworks particles after background
        self.draw_fireworks(painter)

    def draw_fireworks(self, painter):
        # Draw fireworks
        if self._fireworks_enabled:
            for firework in self.fireworks:
                # Draw the firework launch point if not exploded
                if not firework.exploded:
                    color = firework.color if firework.color is not None else QColor(255, 0, 0)
                    painter.setPen(QPen(color, 4))
                    painter.drawPoint(int(firework.x), int(firework.y))
                # Draw the explosion particles
                for particle in firework.particles:
                    px = particle.x
                    py = particle.y
                    color = particle.get_color()
                    if color is None:
                        color = QColor(255, 255, 255)
                    painter.setPen(QPen(color, 3))
                    painter.drawPoint(int(px), int(py))

    def load_custom_background(self, path=None):
        if path:
            self._custom_bg_pixmap = QPixmap(path)
        else:
            self._custom_bg_pixmap = None

    def draw_background_night(self, painter):
        # Draw background - night sky with a coastline
        # Draw sky gradient (deeper, more vibrant blues)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(12, 10, 48))
        gradient.setColorAt(0.3, QColor(18, 18, 60))
        gradient.setColorAt(0.7, QColor(28, 28, 80))
        gradient.setColorAt(1.0, QColor(38, 38, 100))
        painter.fillRect(self.rect(), gradient)

        # Draw stars (drawn down to waterline)
        coastline_height = int(self.height() * 0.15)
        coastline_y = self.height() - coastline_height
        random.seed()  # Reset random seed
        star_count = 220  # More stars for a denser sky
        # Dynamic stars: add/remove stars slowly
        if self._dynamic_stars is None:
            self._dynamic_stars = set()
            for _ in range(star_count):
                sx = random.randint(0, self.width())
                sy = random.randint(0, coastline_y)
                self._dynamic_stars.add((sx, sy))
        if not hasattr(self, "_star_tick"):
            self._star_tick = 0
        self._star_tick += 1
        if self._star_tick > 120:  # About every 2 seconds at 60 FPS
            self._star_tick = 0
            # Remove a random star
            if len(self._dynamic_stars) > 0:
                self._dynamic_stars.pop()
                # Add a new star
                sx = random.randint(0, self.width())
                sy = random.randint(0, coastline_y)
                self._dynamic_stars.add((sx, sy))
        # Draw stars with some twinkling and color variation
        for sx, sy in self._dynamic_stars:
            twinkle = random.randint(0, 10)
            if twinkle < 2:
                # Occasional blue or yellowish star
                if random.random() < 0.5:
                    color = QColor(180, 200, 255, 255)  # Blue-white
                else:
                    color = QColor(255, 240, 200, 255)  # Yellow-white
            else:
                brightness = random.randint(180, 255)
                color = QColor(brightness, brightness, brightness)
            painter.setPen(color)
            painter.drawPoint(sx, sy)
            # Occasionally draw a slightly larger star
            if random.random() < 0.02:
                painter.drawPoint(sx+1, sy)
                painter.drawPoint(sx, sy+1)

        # Draw a few shooting stars
        for _ in range(2):
            if random.random() < 0.0002:  # Rarely appear
                sx = random.randint(int(self.width() * 0.1), int(self.width() * 0.9))
                sy = random.randint(10, int(coastline_y * 0.7))
                length = random.randint(30, 60)
                angle = random.uniform(-0.3, 0.3)
                ex = sx + int(length * math.cos(angle))
                ey = sy + int(length * math.sin(angle))
                grad = QLinearGradient(sx, sy, ex, ey)
                grad.setColorAt(0.0, QColor(255, 255, 255, 180))
                grad.setColorAt(1.0, QColor(255, 255, 255, 0))
                painter.setPen(QPen(grad, 2))
                painter.drawLine(sx, sy, ex, ey)

        # Draw moon with texture and slightly yellow tint
        moon_radius = 44  # Larger moon
        moon_x = int(self.width() * 0.8)
        moon_y = int(self.height() * 0.16)
        moon_color = QColor(245, 235, 180, 230)  # Slightly yellowish
        painter.setBrush(moon_color)
        painter.setPen(moon_color)
        painter.drawEllipse(moon_x, moon_y, moon_radius, moon_radius)

        # Subtle radial gradient for moon shading
        grad = QRadialGradient(
            moon_x + moon_radius // 2, moon_y + moon_radius // 2, moon_radius
        )
        grad.setColorAt(0.0, QColor(255, 255, 230, 200))
        grad.setColorAt(0.7, QColor(230, 230, 210, 120))
        grad.setColorAt(1.0, QColor(180, 180, 170, 80))
        painter.setBrush(grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(moon_x, moon_y, moon_radius, moon_radius)
        painter.setPen(QColor(230, 230, 210, 220))  # Restore pen

        # Add subtle moon craters (texture)
        painter.setBrush(QColor(220, 210, 160, 80))
        painter.setPen(Qt.PenStyle.NoPen)
        for _ in range(7):
            cr_x = moon_x + random.randint(7, moon_radius-12)
            cr_y = moon_y + random.randint(7, moon_radius-12)
            cr_r = random.randint(3, 7)
            painter.drawEllipse(cr_x, cr_y, cr_r, cr_r)

        # Draw a faint moon halo
        halo_grad = QRadialGradient(
            moon_x + moon_radius // 2, moon_y + moon_radius // 2, moon_radius * 2
        )
        halo_grad.setColorAt(0.0, QColor(255, 255, 200, 60))
        halo_grad.setColorAt(1.0, QColor(255, 255, 200, 0))
        painter.setBrush(halo_grad)
        painter.drawEllipse(
            moon_x - moon_radius // 2, moon_y - moon_radius // 2, moon_radius * 2, moon_radius * 2
        )

        # Draw coastline silhouette (unchanged)
        coastline_height = int(self.height() * 0.15)
        coastline_y = self.height() - coastline_height
        painter.setPen(QColor(10, 10, 20))
        painter.setBrush(QColor(10, 10, 20))
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
            
    
    def draw_background_sunset(self, painter):
        # Draw background - realistic sunset over water

        # 1. Sky gradient: deep indigo to warm orange, fading to blue at horizon
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(30, 20, 70))      # Deep indigo at top
        gradient.setColorAt(0.24, QColor(90, 40, 120))    # Purple (taller indigo section)
        gradient.setColorAt(0.42, QColor(255, 120, 80))   # Orange-pink
        gradient.setColorAt(0.60, QColor(255, 180, 120))  # Peach
        gradient.setColorAt(0.77, QColor(120, 140, 200))  # Blue at horizon
        gradient.setColorAt(1.0, QColor(40, 60, 110))     # Water blue
        painter.fillRect(self.rect(), gradient)

        # 2. Sun: low, half-dipped at horizon, with glow
        sun_radius = 180
        horizon_y = int(self.height() * 0.76)  # Move water line further down
        sun_x = int(self.width() * 0.7)
        sun_y = horizon_y + sun_radius // 3
        sun_color = QColor(255, 220, 140, 220)
        sun_rect = QRectF(sun_x - sun_radius // 2, sun_y - sun_radius // 2, sun_radius, sun_radius)
        painter.save()
        painter.setClipRect(0, 0, self.width(), horizon_y)
        painter.setBrush(sun_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(sun_rect)
        painter.restore()

        # Sun glow (radial gradient)
        glow = QRadialGradient(sun_x, sun_y, sun_radius * 1.2)
        glow.setColorAt(0.0, QColor(255, 230, 180, 120))
        glow.setColorAt(0.5, QColor(255, 200, 120, 60))
        glow.setColorAt(1.0, QColor(255, 180, 100, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.save()
        painter.setClipRect(0, 0, self.width(), horizon_y)
        painter.drawEllipse(sun_x - sun_radius, sun_y - sun_radius, sun_radius * 2, sun_radius * 2)
        painter.restore()

        # 3. Clouds: layered, semi-transparent, warm colors
        cloud_colors = [
            QColor(255, 200, 180, 120),  # Peach
            QColor(255, 255, 255, 90),   # White
            QColor(255, 180, 120, 80),   # Orange
            QColor(200, 160, 220, 60),   # Purple
        ]
        clouds = [
            (60, horizon_y - 120, 220, 60, 0),
            (180, horizon_y - 130, 120, 50, 1),
            (250, horizon_y - 110, 180, 40, 2),
            (320, horizon_y - 120, 100, 35, 3),
            (480, horizon_y - 100, 200, 55, 0),
            (600, horizon_y - 110, 120, 40, 1),
            (700, horizon_y - 105, 170, 35, 2),
            (820, horizon_y - 120, 120, 50, 3),
            (900, horizon_y - 110, 250, 70, 0),
            (sun_x - 60, horizon_y - 110, 110, 28, 1),
            (sun_x + 40, horizon_y - 110, 90, 22, 2),
            (sun_x - 20, horizon_y - 110, 120, 30, 0),
        ]
        painter.setPen(Qt.PenStyle.NoPen)
        for cloud_x, cloud_y, cloud_width, cloud_height, color_idx in clouds:
            painter.setBrush(cloud_colors[color_idx % len(cloud_colors)])
            painter.drawEllipse(cloud_x, cloud_y, cloud_width, cloud_height)

        # 4. Crescent moon, faint, high in sky
        moon_radius = 26
        moon_x = int(self.width() * 0.16)
        moon_y = int(self.height() * 0.18)
        moon_color = QColor(230, 230, 255, 80)
        painter.setBrush(moon_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(moon_x, moon_y, moon_radius, moon_radius)
        painter.setBrush(QColor(30, 20, 70, 0))
        painter.drawEllipse(moon_x + 7, moon_y, moon_radius, moon_radius)

        # 5. Early stars, faint, only in upper sky
        painter.setPen(QColor(255, 255, 255, 60))
        for _ in range(16):
            x = random.randint(0, self.width())
            y = random.randint(0, int(self.height() * 0.35))
            painter.drawPoint(x, y)

        # 6. Water: horizontal gradient, subtle reflection of sun and sky
        water_rect = QRectF(0, horizon_y, self.width(), self.height() - horizon_y)
        water_gradient = QLinearGradient(0, horizon_y, 0, self.height())
        water_gradient.setColorAt(0.0, QColor(80, 110, 180, 220))
        water_gradient.setColorAt(0.5, QColor(40, 60, 110, 255))
        water_gradient.setColorAt(1.0, QColor(20, 30, 60, 255))
        painter.fillRect(water_rect, water_gradient)

        # 7. Sun reflection: vertical streaks, shimmering
        reflection_width = sun_radius // 2
        reflection_x = sun_x - reflection_width // 2
        reflection_y = horizon_y
        reflection_height = int(self.height() - horizon_y)
        for i in range(18):
            alpha = 120 - i * 6
            width = reflection_width - i * 6
            if width <= 0:
                break
            color = QColor(255, 230, 180, max(0, alpha))
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(reflection_x + i * 3, reflection_y + i * 10, width, 12)

    def draw_background_city(self, painter):
        # Draw background - cityscape at night with gently flickering lights in windows
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(30, 30, 60))
        gradient.setColorAt(1.0, QColor(10, 10, 30))
        painter.fillRect(self.rect(), gradient)

        # Draw buildings
        building_color = QColor(50, 50, 100)
        # Draw buildings with fixed heights for consistency
        building_heights = [180, 240, 200, 150, 220, 170, 260, 210, 190, 230]
        for idx, i in enumerate(range(0, self.width(), 100)):
            building_height = building_heights[idx % len(building_heights)]
            painter.fillRect(i, self.height() - building_height, 80, building_height, building_color)

        # Draw windows with slow flicker, always below building_height
        if self._city_window_states is None:
            # Initialize window states: {(building_idx, window_row): is_on}
            self._city_window_states = {}
            self._city_window_ticks = 0
        self._city_window_ticks += 1
        if self._city_window_ticks > 30:  # Update every 30 frames
            self._city_window_ticks = 0
            # Randomly toggle a few windows
            for key in self._city_window_states:
                if random.random() < 0.0005:  # 0.05% chance to toggle
                    self._city_window_states[key] = not self._city_window_states[key]

        for idx, i in enumerate(range(0, self.width(), 100)):
            building_height = building_heights[idx % len(building_heights)]
            window_rows = building_height // 40
            for row in range(window_rows):
                key = (idx, row)
                if key not in self._city_window_states:
                    self._city_window_states[key] = random.random() < 0.5
                if self._city_window_states[key]:
                    window_color = QColor(255, 255, 100, 180)
                    y = self.height() - building_height + row * 40 + 10
                    # Ensure window is always within building
                    if y + 30 <= self.height():
                        painter.fillRect(i + 10, y, 20, 30, window_color)
        # Draw a few Doors
        door_color = QColor(200, 200, 210)  # Light off-gray color
        for i in range(0, self.width(), 100):
            painter.fillRect(i + 40, self.height() - 40, 20, 40, door_color)

        # Draw stars in the sky above the buildings (not inside buildings)
        if self._city_stars is None:
            # Precompute star positions above buildings
            self._city_stars = []
            star_count = 120
            building_heights = [180, 240, 200, 150, 220, 170, 260, 210, 190, 230]
            for _ in range(star_count):
                while True:
                    sx = random.randint(0, self.width())
                    # Determine the building height at this x
                    building_idx = (sx // 100) % len(building_heights)
                    building_left = (sx // 100) * 100
                    building_right = building_left + 80
                    if building_left <= sx < building_right:
                        building_height = building_heights[building_idx]
                        building_top = self.height() - building_height
                    else:
                        building_top = 0
                    sy = random.randint(0, max(0, building_top - 1))
                    # Only accept stars above the building tops
                    if sy < building_top:
                        self._city_stars.append((sx, sy))
                        break
        for sx, sy in self._city_stars:
            brightness = random.randint(180, 255)
            painter.setPen(QColor(brightness, brightness, brightness))
            painter.drawPoint(sx, sy)

    def draw_background_mountains(self, painter):
        
        # Draw background - mountainous landscape at night with stars and a moon

        # 1. Draw sky gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(15, 15, 40))
        gradient.setColorAt(0.7, QColor(25, 25, 60))
        gradient.setColorAt(1.0, QColor(35, 35, 80))
        painter.fillRect(self.rect(), gradient)

        # 2. Generate mountain silhouette using smooth curves
        mountain_base_y = int(self.height() * 0.65)
        mountain_heights = [
            (0, mountain_base_y + 40),
            (int(self.width() * 0.10), mountain_base_y - 60),
            (int(self.width() * 0.22), mountain_base_y - 30),
            (int(self.width() * 0.35), mountain_base_y - 110),
            (int(self.width() * 0.48), mountain_base_y - 40),
            (int(self.width() * 0.60), mountain_base_y - 90),
            (int(self.width() * 0.72), mountain_base_y - 30),
            (int(self.width() * 0.85), mountain_base_y - 70),
            (self.width(), mountain_base_y + 30),
        ]
        # Smooth the mountain path using spline interpolation
        mountain_x = [pt[0] for pt in mountain_heights]
        mountain_y = [pt[1] for pt in mountain_heights]
        xnew = np.linspace(0, self.width(), 300)
        spl = make_interp_spline(mountain_x, mountain_y, k=3)
        ynew = spl(xnew)

        # 3. Draw stars above the mountains (dense star field)
        if self._mountain_stars is None:
            # Precompute star positions above the mountains
            self._mountain_stars = []
            star_count = 350  # Increased for a denser star field
            for _ in range(star_count):
                sx = random.randint(0, self.width())
                # Find the y of the mountain at this x
                idx = int((sx / self.width()) * (len(xnew) - 1))
                mountain_y_at_x = int(ynew[idx])
                sy = random.randint(0, max(0, mountain_y_at_x - 8))
                self._mountain_stars.append((sx, sy))
        for sx, sy in self._mountain_stars:
            brightness = random.randint(180, 255)
            painter.setPen(QColor(brightness, brightness, brightness))
            painter.drawPoint(sx, sy)

        # 4. Draw the moon (above mountains, not touching peaks)
        moon_radius = 38
        moon_x = int(self.width() * 0.78)
        moon_y = int(self.height() * 0.18)
        moon_color = QColor(245, 235, 200, 220)
        painter.setBrush(moon_color)
        painter.setPen(moon_color)
        painter.drawEllipse(moon_x, moon_y, moon_radius, moon_radius)
        # Subtle radial gradient for moon shading
        grad = QRadialGradient(
            moon_x + moon_radius // 2, moon_y + moon_radius // 2, moon_radius
        )
        grad.setColorAt(0.0, QColor(255, 255, 230, 180))
        grad.setColorAt(0.7, QColor(230, 230, 210, 120))
        grad.setColorAt(1.0, QColor(180, 180, 170, 80))
        painter.setBrush(grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(moon_x, moon_y, moon_radius, moon_radius)
        painter.setPen(QColor(230, 230, 210, 220))

        # 5. Draw the mountains (foreground silhouette)
        # Add jagged peaks and valleys for a more dramatic silhouette
        # We'll perturb the y-coordinates with some random noise for ruggedness
        rng = np.random.default_rng(seed=42)  # Fixed seed for consistent look
        rugged_ynew = ynew.copy()
        for i in range(1, len(rugged_ynew) - 1):
            # Add more jaggedness at peaks/valleys
            if i % 25 == 0:
                rugged_ynew[i] -= rng.integers(18, 38)
            elif i % 17 == 0:
                rugged_ynew[i] += rng.integers(10, 22)
            elif i % 7 == 0:
                rugged_ynew[i] += rng.integers(-8, 8)
            else:
                rugged_ynew[i] += rng.integers(-3, 3)
        # Optionally, add a few sharp spires
        for idx in [60, 120, 180, 240]:
            if idx < len(rugged_ynew):
                rugged_ynew[idx] -= rng.integers(30, 55)
        mountain_path = QPainterPath()
        mountain_path.moveTo(0, self.height())
        for xi, yi in zip(xnew, rugged_ynew):
            mountain_path.lineTo(xi, yi)
        mountain_path.lineTo(self.width(), self.height())
        mountain_path.closeSubpath()
        mountain_color = QColor(25, 25, 35)
        painter.setBrush(mountain_color)
        painter.setPen(QColor(20, 20, 30))
        painter.drawPath(mountain_path)
        mountain_path = QPainterPath()
        mountain_path.moveTo(0, self.height())
        for xi, yi in zip(xnew, ynew):
            mountain_path.lineTo(xi, yi)
        mountain_path.lineTo(self.width(), self.height())
        mountain_path.closeSubpath()
        mountain_color = QColor(25, 25, 35)
        painter.setBrush(mountain_color)
        painter.setPen(QColor(20, 20, 30))
        painter.drawPath(mountain_path)

        # 6. Add a second, lighter mountain range for depth
        back_mountain_base_y = int(self.height() * 0.72)
        back_mountain_heights = [
            (0, back_mountain_base_y + 30),
            (int(self.width() * 0.13), back_mountain_base_y - 40),
            (int(self.width() * 0.28), back_mountain_base_y - 10),
            (int(self.width() * 0.45), back_mountain_base_y - 60),
            (int(self.width() * 0.62), back_mountain_base_y - 20),
            (int(self.width() * 0.78), back_mountain_base_y - 50),
            (self.width(), back_mountain_base_y + 20),
        ]
        back_x = [pt[0] for pt in back_mountain_heights]
        back_y = [pt[1] for pt in back_mountain_heights]
        back_xnew = np.linspace(0, self.width(), 200)
        back_spl = make_interp_spline(back_x, back_y, k=3)
        back_ynew = back_spl(back_xnew)
        back_path = QPainterPath()
        back_path.moveTo(0, self.height())
        for xi, yi in zip(back_xnew, back_ynew):
            back_path.lineTo(xi, yi)
        back_path.lineTo(self.width(), self.height())
        back_path.closeSubpath()
        back_color = QColor(40, 40, 60, 180)
        painter.setBrush(back_color)
        painter.setPen(QColor(35, 35, 50, 180))
        painter.drawPath(back_path)
