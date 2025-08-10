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
        self.particle_count = 100
        self.firework_color = QColor(255, 0, 0)
        self.background = None
        self.fired_times = set()  # Track fired times
        self._fireworks_enabled = True  # Initialize attribute
        self.delay = 0.0  # Delay for fireworks to explode
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

    def add_firework(self, x=None, color=None):
        if x is None:
            x = random.randint(0, self.width())
        if color is None:
            color = self.firework_color
        firework = Firework(x, self.height(), 
                             color,
                             self.particle_count)
        firework.choose_firework_pattern(self.pattern)
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
        if preview_widget and preview_widget.firework_firing is not None:
            time_list = preview_widget.firework_firing
            for idx, t in enumerate(time_list):
                if abs(preview_widget.current_time - t) < 0.08 and t not in self.fired_times:
                    if hasattr(preview_widget, "firework_colors") and isinstance(preview_widget.firework_colors, list) and idx < len(preview_widget.firework_colors):
                        self.firework_color = preview_widget.firework_colors[idx]
                    else:
                        self.firework_color = QColor(255, 0, 0)
                    self.add_firework()
                    self.fired_times.add(t)
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
                if not firework.exploded:
                    painter.setPen(QPen(firework.color, 4))
                    painter.drawPoint(int(firework.x), int(firework.y))
                else:
                    for particle in firework.particles:
                        color = particle.get_color()
                        painter.setPen(QPen(color, 3))
                        painter.drawPoint(int(particle.x), int(particle.y))

    def load_custom_background(self, path=None):
        if path:
            self._custom_bg_pixmap = QPixmap(path)
        else:
            self._custom_bg_pixmap = None

    def draw_background_night(self, painter):
            # Draw background - night sky with a coastline
            # Draw sky gradient
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0.0, QColor(10, 10, 40))
            gradient.setColorAt(0.7, QColor(20, 20, 60))
            gradient.setColorAt(1.0, QColor(30, 30, 80))
            painter.fillRect(self.rect(), gradient)

            # Draw stars (drawn down to waterline)
            coastline_height = int(self.height() * 0.15)
            coastline_y = self.height() - coastline_height
            random.seed()  # Reset random seed
            star_count = 180
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
            for sx, sy in self._dynamic_stars:
                brightness = random.randint(180, 255)
                painter.setPen(QColor(brightness, brightness, brightness))
                painter.drawPoint(sx, sy)

            moon_radius = 38  # Increased from 28 to 38 for a bigger moon
            moon_x = int(self.width() * 0.8)
            moon_y = int(self.height() * 0.18)

            # Draw moon with texture and slightly yellow tint
            moon_color = QColor(245, 235, 180, 220)  # Slightly yellowish
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
            painter.setPen(QColor(230, 230, 210, 220))  # Restore pen

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
            
    
    def draw_background_sunset(self, painter):
        # Draw background - advanced sunset transitioning to night
        gradient = QLinearGradient(0, 0, 0, self.height())
        # Deepen the colors for a tranquil, late sunset
        gradient.setColorAt(0.0, QColor(40, 20, 60))      # Deep indigo at top
        gradient.setColorAt(0.25, QColor(90, 40, 120))    # Purple
        gradient.setColorAt(0.5, QColor(255, 120, 80))    # Orange-pink
        gradient.setColorAt(0.7, QColor(255, 180, 120))   # Soft peach
        gradient.setColorAt(1.0, QColor(40, 30, 80))      # Night blue at bottom
        painter.fillRect(self.rect(), gradient)

        # Draw sun, low on horizon, partially set
        sun_radius = 200
        # Draw only the upper half of the sun above the horizon (cut off at horizon)
        horizon_y = int(self.height() * 0.73)
        sun_x = int(self.width() * 0.75)
        sun_y = int(self.height() * 0.82)
        sun_color = QColor(255, 220, 140, 180)
        sun_rect = QRectF(sun_x - sun_radius // 2, sun_y - sun_radius // 2, sun_radius, sun_radius)
        painter.save()
        painter.setClipRect(0, 0, self.width(), horizon_y)
        painter.setBrush(sun_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(sun_rect)
        painter.restore()

        # Draw tranquil, layered clouds with soft edges
        cloud_color = QColor(255, 255, 255, 180)
        painter.setBrush(cloud_color)
        painter.setPen(Qt.PenStyle.NoPen)
        # Draw clouds at fixed positions for consistency
        clouds = [
            # Main cloud layer (amorphous, overlapping)
            (60, horizon_y - 120, 220, 60),
            (180, horizon_y - 130, 120, 50),   # Overlaps first
            (250, horizon_y - 110, 180, 40),
            (320, horizon_y - 120, 100, 35),   # Overlaps second and third
            (480, horizon_y - 100, 200, 55),
            (600, horizon_y - 110, 120, 40),   # Overlaps fourth and fifth
            (700, horizon_y - 105, 170, 35),
            (820, horizon_y - 120, 120, 50),   # Overlaps sixth and seventh
            (900, horizon_y - 110, 250, 70),
            # Near the sun, but at same height as other clouds
            (sun_x - 60, horizon_y - 110, 110, 28),
            (sun_x + 40, horizon_y - 110, 90, 22),
            (sun_x - 20, horizon_y - 110, 120, 30),
        ]
        for cloud_x, cloud_y, cloud_width, cloud_height in clouds:
            painter.drawEllipse(cloud_x, cloud_y, cloud_width, cloud_height)

        # Add a faint crescent moon for a tranquil, late sunset
        moon_radius = 28
        moon_x = int(self.width() * 0.18)
        moon_y = int(self.height() * 0.22)
        moon_color = QColor(230, 230, 255, 120)
        painter.setBrush(moon_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(moon_x, moon_y, moon_radius, moon_radius)
        # Crescent effect
        painter.setBrush(QColor(40, 20, 60, 0))
        painter.drawEllipse(moon_x + 7, moon_y, moon_radius, moon_radius)

        # Optionally, add a few early stars
        painter.setPen(QColor(255, 255, 255, 80))
        for _ in range(18):
            x = random.randint(0, self.width())
            y = random.randint(0, int(self.height() * 0.4))
            painter.drawPoint(x, y)

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
