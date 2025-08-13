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
        # Use handle.firing_color if set, else use self.firework_color
        color = getattr(handle, "firing_color", None)
        if not isinstance(color, QColor):
            color = QColor(*color) if isinstance(color, (tuple, list)) else QColor(255, 0, 0)
        firework = Firework(
            x, self.height(),
            color, handle.pattern,
            handle.display_number,
            self.particle_count
        )
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
        self.fireworks = [fw for fw in self.fireworks if fw.update()]
        parent = self.parentWidget()
        preview_widget = None
        # Find the parent FireworkShowApp to access firework_firing
        while parent:
            # Avoid direct import to prevent unknown symbol error
            if parent.__class__.__name__ == "FireworkShowApp":
                preview_widget = getattr(parent, "preview_widget", None)
                break
            parent = parent.parentWidget()
        if preview_widget and getattr(preview_widget, "firework_times", None) is not None and self._fireworks_enabled:
            handles = getattr(preview_widget, "fireworks", [])
            for handle in handles:
                if (getattr(preview_widget, "current_time", 0) >= handle.firing_time - self.delay and
                        getattr(preview_widget, "current_time", 0) < handle.firing_time - self.delay + 0.016 and
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
                    color = firework.color if isinstance(firework.color, QColor) else QColor(255, 0, 0)
                    painter.setPen(QPen(color, 4))
                    painter.drawPoint(int(firework.x), int(firework.y))
                # Draw the explosion particles
                for particle in firework.particles:
                    px = particle.x
                    py = particle.y
                    color = particle.get_color()
                    if not isinstance(color, QColor):
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


        # --- Draw detailed coastline silhouette in foreground with palm tree ---

        coastline_height = int(self.height() * 0.15)
        coastline_y = self.height() - coastline_height

        # Draw detailed coastline silhouette (foreground, black and shorter)
        # Cache the coastline path so it doesn't change every frame
        if not hasattr(self, "_coastline_cache") or \
           self._coastline_cache is None or \
           self._coastline_cache.get("width") != self.width() or \
           self._coastline_cache.get("height") != self.height():
            # Recompute coastline path if size changes or not cached
            path = QPainterPath()
            path.moveTo(0, self.height())
            # Use a fixed random seed for consistent coastline shape per size
            rng = random.Random(self.width() * 10000 + self.height())
            for i in range(0, self.width() + 1, 4):
                wave = (
                    math.sin(i * 0.025) * 6 +
                    math.cos(i * 0.012) * 4 +
                    rng.uniform(-1, 1)
                )
                path.lineTo(i, coastline_y + 10 + wave)
            path.lineTo(self.width(), self.height())
            path.closeSubpath()
            self._coastline_cache = {
                "width": self.width(),
                "height": self.height(),
                "path": path
            }
        painter.setPen(Qt.PenStyle.NoPen)
        black_color = QColor(0, 0, 0, 255)
        painter.setBrush(black_color)
        painter.drawPath(self._coastline_cache["path"])
        

        # Draw a palm tree silhouette on the left foreground
        palm_base_x = int(self.width() * 0.13)
        palm_base_y = int(coastline_y + 18)
        trunk_height = int(self.height() * 0.18)
        trunk_width = 9
        # Draw several palm trees (all black silhouette)
        palm_color = QColor(0, 0, 0, 255)
        painter.setPen(QPen(palm_color, trunk_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # List of palm tree positions and trunk heights (relative to coastline)
        palms = [
            (int(self.width() * 0.13), int(coastline_y + 18), int(self.height() * 0.18)),  # main left
            (int(self.width() * 0.19), int(coastline_y + 24), int(self.height() * 0.13)),  # right of main
            (int(self.width() * 0.10), int(coastline_y + 28), int(self.height() * 0.11)),  # left of main
            (int(self.width() * 0.16), int(coastline_y + 32), int(self.height() * 0.09)),  # short, in front
            (int(self.width() * 0.09), int(coastline_y + 12), int(self.height() * 0.15)),  # far left
        ]

        for palm_base_x, palm_base_y, trunk_height in palms:
            # Draw trunk (curved)
            trunk_path = QPainterPath()
            trunk_path.moveTo(palm_base_x, palm_base_y)
            trunk_path.cubicTo(
            palm_base_x + 10, palm_base_y - trunk_height // 3,
            palm_base_x - 18, palm_base_y - trunk_height * 2 // 3,
            palm_base_x + 8, palm_base_y - trunk_height
            )
            painter.drawPath(trunk_path)
            # Draw palm leaves (silhouette, 7-8 leaves) - cache per palm so leaves don't change every frame
            if not hasattr(self, "_palm_leaves_cache"):
                self._palm_leaves_cache = {}
            palm_id = (palm_base_x, palm_base_y, trunk_height)
            if palm_id not in self._palm_leaves_cache:
                # Generate and cache leaf geometry for this palm
                center_x = palm_base_x + 8
                center_y = palm_base_y - trunk_height
                # Fan leaves evenly in a radial pattern (like a real palm)
                n_leaves = 8
                leaf_angles = np.linspace(-110, 110, n_leaves)
                leaves = []
                for angle in leaf_angles:
                    radians = math.radians(angle)
                    leaf_len = random.randint(54, 62)
                    # Make leaves more arched and symmetric
                    ctrl1_x = center_x + math.cos(radians) * (leaf_len * 0.33)
                    ctrl1_y = center_y + math.sin(radians) * (leaf_len * 0.33) - 8
                    ctrl2_x = center_x + math.cos(radians) * (leaf_len * 0.66)
                    ctrl2_y = center_y + math.sin(radians) * (leaf_len * 0.66) + 8
                    end_x = center_x + math.cos(radians) * leaf_len
                    end_y = center_y + math.sin(radians) * leaf_len
                    # Leaflets: short, perpendicular lines, evenly spaced
                    leaflets = []
                    for t in np.linspace(0.18, 0.82, 5):
                        lx = center_x + (end_x - center_x) * t
                        ly = center_y + (end_y - center_y) * t
                        perp_angle = radians + math.pi / 2
                        leaflet_len = 8 + 2 * math.cos((t - 0.5) * math.pi)  # slightly longer in middle
                        leaflets.append((
                            int(lx - math.cos(perp_angle) * leaflet_len / 2),
                            int(ly - math.sin(perp_angle) * leaflet_len / 2),
                            int(lx + math.cos(perp_angle) * leaflet_len / 2),
                            int(ly + math.sin(perp_angle) * leaflet_len / 2)
                        ))
                    leaves.append({
                        "ctrl1": (ctrl1_x, ctrl1_y),
                        "ctrl2": (ctrl2_x, ctrl2_y),
                        "end": (end_x, end_y),
                        "angle": radians,
                        "leaflets": leaflets,
                        "center": (center_x, center_y),
                    })
                self._palm_leaves_cache[palm_id] = leaves
            # Draw cached leaves
            painter.setPen(QPen(palm_color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for leaf in self._palm_leaves_cache[palm_id]:
                center_x, center_y = leaf["center"]
                ctrl1_x, ctrl1_y = leaf["ctrl1"]
                ctrl2_x, ctrl2_y = leaf["ctrl2"]
                end_x, end_y = leaf["end"]
                leaf_path = QPainterPath()
                leaf_path.moveTo(center_x, center_y)
                leaf_path.cubicTo(ctrl1_x, ctrl1_y, ctrl2_x, ctrl2_y, end_x, end_y)
                painter.drawPath(leaf_path)
                # Draw leaflets as short lines
                for lx1, ly1, lx2, ly2 in leaf["leaflets"]:
                    painter.drawLine(lx1, ly1, lx2, ly2)

        # Restore pen
        painter.setPen(QColor(230, 230, 210, 220))
    # --- Animated Clouds for Sunset Scene ---
    def _init_sunset_clouds(self):
        # Called once to initialize clouds for sunset background
        self._sunset_clouds = []
        n_clouds = 10
        for _ in range(n_clouds):
            cloud = {
                "x": random.randint(-200, self.width()),
                "y": random.randint(int(self.height() * 0.05), int(self.height() * 0.22)),
                "width": random.randint(90, 220),
                "height": random.randint(28, 60),
                "color_idx": random.randint(0, 3),
                "speed": random.uniform(0.18, 0.55),
                "layer": random.choice([0, 1]),  # 0: back, 1: front
            }
            self._sunset_clouds.append(cloud)

    def _update_sunset_clouds(self):
        # Move clouds and respawn if off screen
        if not hasattr(self, "_sunset_clouds") or self._sunset_clouds is None:
            self._init_sunset_clouds()
        for cloud in self._sunset_clouds:
            cloud["x"] += cloud["speed"]
        # Remove clouds that are off right edge and add new ones at left
        width = self.width()
        for cloud in self._sunset_clouds:
            if cloud["x"] > width + 60:
                # Respawn at left with new random properties
                cloud["x"] = -random.randint(100, 220)
                cloud["y"] = random.randint(int(self.height() * 0.05), int(self.height() * 0.22))
                cloud["width"] = random.randint(90, 220)
                cloud["height"] = random.randint(28, 60)
                cloud["color_idx"] = random.randint(0, 3)
                cloud["speed"] = random.uniform(0.18, 0.55)
                cloud["layer"] = random.choice([0, 1])

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

        # Sun glow
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

        # 3. Animated Clouds: endless supply, moving left to right
        cloud_colors = [
            QColor(255, 200, 180, 120),  # Peach
            QColor(255, 255, 255, 90),   # White
            QColor(255, 180, 120, 80),   # Orange
            QColor(200, 160, 220, 60),   # Purple
        ]
        # Update and draw clouds
        self._update_sunset_clouds()
        # Draw back layer first, then front for parallax effect
        for layer in [0, 1]:
            for cloud in self._sunset_clouds:
                if cloud["layer"] == layer:
                    painter.setBrush(cloud_colors[cloud["color_idx"] % len(cloud_colors)])
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(
                        int(cloud["x"]),
                        int(cloud["y"]),
                        int(cloud["width"]),
                        int(cloud["height"])
                    )

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

    # Ensure sunset clouds are initialized on resize or show
    def resizeEvent(self, event):
        if self.background == "sunset":
            self._init_sunset_clouds()
        super().resizeEvent(event)

    def draw_background_city(self, painter):
        # Draw city night sky gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(32, 32, 60))
        gradient.setColorAt(1.0, QColor(8, 8, 22))
        painter.fillRect(self.rect(), gradient)

        # Draw simple buildings and store their geometry for windows
        building_colors = [QColor(45, 45, 90), QColor(60, 60, 110), QColor(38, 38, 80)]
        buildings = []
        x = 0
        # Cache building geometry so buildings don't change every frame
        if not hasattr(self, "_city_buildings") or self._city_buildings is None or self.width() != getattr(self, "_city_buildings_width", None) or self.height() != getattr(self, "_city_buildings_height", None):
            # Recompute buildings if size changes or not cached
            buildings = []
            x = 0
            while x < self.width():
                bw = random.randint(50, 110)
                bh = random.randint(140, 260)
                by = self.height() - bh
                color = random.choice(building_colors)
                buildings.append((x, by, bw, bh, color))
                x += bw - random.randint(0, 10)
            self._city_buildings = buildings
            self._city_buildings_width = self.width()
            self._city_buildings_height = self.height()
        else:
            buildings = self._city_buildings

        # Draw buildings
        for bx, by, bw, bh, color in buildings:
            painter.setBrush(color)
            painter.setPen(QColor(25, 25, 50))
            painter.drawRect(bx, by, bw, bh)

        # Prepare window state cache (lit/unlit) and update it very slowly
        if self._city_window_states is None or len(self._city_window_states) != len(buildings):
            # Initialize window states for each building
            self._city_window_states = []
            for bx, by, bw, bh, color in buildings:
                window_cols = max(1, (bw - 16) // 16)
                window_rows = max(1, (bh - 24) // 24)
                states = np.random.choice([True, False], size=(window_cols, window_rows), p=[0.45, 0.55])
                self._city_window_states.append(states)
            self._city_window_ticks = 0
        else:
            # Slowly update a few windows at random every ~6 seconds
            if not hasattr(self, "_city_window_ticks"):
                self._city_window_ticks = 0
            self._city_window_ticks += 1
            if self._city_window_ticks > 360:  # ~6 seconds at 60 FPS
                self._city_window_ticks = 0
                for states in self._city_window_states:
                    # Flip a single random window per building
                    if states.size > 0:
                        col = random.randint(0, states.shape[0] - 1)
                        row = random.randint(0, states.shape[1] - 1)
                        states[col, row] = not states[col, row]

        # Draw windows (lit/unlit) within each building using cached state
        for bidx, (bx, by, bw, bh, color) in enumerate(buildings):
            window_cols = max(1, (bw - 16) // 16)
            window_rows = max(1, (bh - 24) // 24)
            states = self._city_window_states[bidx] if bidx < len(self._city_window_states) else None
            for col in range(window_cols):
                for row in range(window_rows):
                    wx = bx + 8 + col * 16
                    wy = by + 8 + row * 24
                    # Ensure window is within building
                    if wx + 10 < bx + bw and wy + 18 < by + bh:
                        lit = states[col, row] if states is not None and col < states.shape[0] and row < states.shape[1] else False
                        if lit:
                            painter.setBrush(QColor(255, 255, 180, 200))
                        else:
                            painter.setBrush(QColor(60, 60, 40, 80))
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.drawRect(wx, wy, 10, 18)

        # Draw a few stars above buildings (static)
        if self._city_stars is None:
            self._city_stars = []
            for _ in range(40):
                sx = random.randint(0, self.width())
                sy = random.randint(0, int(self.height() * 0.4))
                brightness = random.randint(180, 255)
                self._city_stars.append((sx, sy, brightness))
        for sx, sy, brightness in self._city_stars:
            painter.setPen(QColor(brightness, brightness, brightness))
            painter.drawPoint(sx, sy)

        # Draw a small crescent moon (waxing/waning) in the sky
        moon_radius = 28
        moon_x = int(self.width() * 0.13)
        moon_y = int(self.height() * 0.14)
        # Main moon body
        painter.setBrush(QColor(240, 240, 210, 210))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(moon_x, moon_y, moon_radius, moon_radius)
        # Crescent shadow (to create crescent effect)
        painter.setBrush(QColor(32, 32, 60, 0))
        painter.drawEllipse(moon_x + 8, moon_y, moon_radius, moon_radius)

        # --- Plane flyby event ---
        # Plane flies slowly from left to right near the top of the screen with a flashing red light
        if not hasattr(self, "_plane_flyby"):
            # Initialize plane state: x position, flash tick, flash state
            self._plane_flyby = {
                "x": -40,
                "y": int(self.height() * 0.09),
                "speed": max(1, self.width() // 900),  # Slow, scales with width
                "flash_tick": 0,
                "flash_on": True,
            }
        plane = self._plane_flyby
        # Move plane
        plane["x"] += plane["speed"]
        if plane["x"] > self.width() + 40:
            # Reset to left, randomize y a bit
            plane["x"] = -40
            plane["y"] = int(self.height() * 0.07) + random.randint(0, int(self.height() * 0.05))
        # Flashing logic: flash every ~0.7s (about 44 frames at 16ms)
        plane["flash_tick"] += 1
        if plane["flash_tick"] > 44:
            plane["flash_tick"] = 0
            plane["flash_on"] = not plane["flash_on"]
        # Draw the plane as a tiny dark shape with a flashing red light
        px = int(plane["x"])
        py = int(plane["y"])
        # Plane body (tiny, dark gray)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(80, 80, 90, 180))
        painter.drawEllipse(px, py, 16, 4)
        # Plane tail (vertical stabilizer)
        painter.setBrush(QColor(60, 60, 70, 180))
        painter.drawRect(px + 12, py - 2, 3, 6)
        # Flashing red light (on top of plane)
        if plane["flash_on"]:
            painter.setBrush(QColor(255, 40, 40, 230))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(px + 14, py + 1, 4, 4)

    def draw_background_mountains(self, painter):
        # Draw background - mountainous landscape at night with stars and a moon

        # 1. Draw sky gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(15, 15, 40))
        gradient.setColorAt(0.7, QColor(25, 25, 60))
        gradient.setColorAt(1.0, QColor(35, 35, 80))
        painter.fillRect(self.rect(), gradient)

        # Ensure shooting stars list is initialized
        if not hasattr(self, "_mountain_shooting_stars"):
            self._mountain_shooting_stars = []

        # --- Caching for mountains and stars ---
        if not hasattr(self, "_mountain_cache") or self._mountain_cache is None \
            or self._mountain_cache.get("width") != self.width() \
            or self._mountain_cache.get("height") != self.height():
            # Cache for all mountain data
            self._mountain_cache = {
                "width": self.width(),
                "height": self.height(),
                "mountain_xnew": None,
                "mountain_ynew": None,
                "dynamic_stars": None,
                "ridges": None,
                "rocks": None,
            }

            # 2. Generate mountain silhouette using smooth curves (taller)
            mountain_base_y = int(self.height() * 0.70)  # Lower base for taller mountains
            mountain_heights = [
                (0, mountain_base_y + 30),
                (int(self.width() * 0.10), mountain_base_y - 120),
                (int(self.width() * 0.22), mountain_base_y - 80),
                (int(self.width() * 0.35), mountain_base_y - 210),
                (int(self.width() * 0.48), mountain_base_y - 100),
                (int(self.width() * 0.60), mountain_base_y - 180),
                (int(self.width() * 0.72), mountain_base_y - 70),
                (int(self.width() * 0.85), mountain_base_y - 160),
                (self.width(), mountain_base_y + 20),
            ]
            mountain_x = [pt[0] for pt in mountain_heights]
            mountain_y = [pt[1] for pt in mountain_heights]
            # Generate smooth mountain silhouette using spline
            xnew = np.linspace(0, self.width(), 400)
            spl = make_interp_spline(mountain_x, mountain_y, k=3)
            ynew = spl(xnew)
            self._mountain_cache["mountain_xnew"] = xnew
            self._mountain_cache["mountain_ynew"] = ynew
            _coastline_y = int(min(ynew))  # Top of the tallest mountain (unused, so prefix with _)
            star_count = 220
            dynamic_stars = set()
            for _ in range(star_count):
                sx = random.randint(0, self.width())
                idx = int((sx / self.width()) * (len(xnew) - 1))
                mountain_y_at_x = int(ynew[idx])
                sy = random.randint(0, max(0, mountain_y_at_x - 1))
                dynamic_stars.add((sx, sy))
            self._mountain_cache["dynamic_stars"] = dynamic_stars
            dynamic_stars = set()
            for _ in range(star_count):
                sx = random.randint(0, self.width())
                idx = int((sx / self.width()) * (len(xnew) - 1))
                mountain_y_at_x = int(ynew[idx])
                sy = random.randint(0, max(0, mountain_y_at_x - 1))
                dynamic_stars.add((sx, sy))
            self._mountain_cache["dynamic_stars"] = dynamic_stars

            # 5. Cache all ridges for the foreground
            def ridge_points(y_offset, n_peaks, noise_scale=1.0, rocky=False):
                base_y = int(self.height() * y_offset)
                points = []
                for i in range(n_peaks):
                    x = int(i * self.width() / (n_peaks - 1))
                    peak = base_y - random.randint(24, 80) if i % 2 == 1 else base_y + random.randint(0, 30)
                    points.append((x, peak))
                ridge_x = [pt[0] for pt in points]
                ridge_y = [pt[1] for pt in points]
                ridge_xnew = np.linspace(0, self.width(), 400)
                ridge_spl = make_interp_spline(ridge_x, ridge_y, k=3)
                ridge_ynew = ridge_spl(ridge_xnew)
                rng = np.random.default_rng(seed=int(y_offset*1000))
                for i in range(len(ridge_ynew)):
                    ridge_ynew[i] += rng.integers(-8, 8) * noise_scale
                    if rocky and i % 23 == 0:
                        ridge_ynew[i] -= rng.integers(10, 22)
                return ridge_xnew, ridge_ynew
            self._mountain_cache["ridges"] = [
                {
                    "y_offset": 0.68,
                    "color": (60, 70, 100),
                    "alpha": 120,
                    "noise_scale": 0.7,
                    "tree_density": 0.05,
                    "rocky": False,
                    "ridge": ridge_points(0.68, random.randint(7, 11), 0.7, False),
                },
                {
                    "y_offset": 0.74,
                    "color": (40, 50, 70),
                    "alpha": 170,
                    "noise_scale": 1.0,
                    "tree_density": 0.08,
                    "rocky": False,
                    "ridge": ridge_points(0.74, random.randint(7, 11), 1.0, False),
                },
                {
                    "y_offset": 0.81,
                    "color": (30, 35, 45),
                    "alpha": 210,
                    "noise_scale": 1.5,
                    "tree_density": 0.18,
                    "rocky": True,
                    "ridge": ridge_points(0.81, random.randint(7, 11), 1.5, True),
                },
                {
                    "y_offset": 0.87,
                    "color": (18, 20, 25),
                    "alpha": 255,
                    "noise_scale": 2.2,
                    "tree_density": 0.32,
                    "rocky": True,
                    "ridge": ridge_points(0.87, random.randint(7, 11), 2.2, True),
                },
            ]

            # Cache boulders/rocks in the foreground
            rng = np.random.default_rng(seed=123)
            rocks = []
            for _ in range(8):
                rx = rng.integers(0, self.width())
                ry = int(self.height() * 0.92) + rng.integers(-8, 8)
                rwidth = rng.integers(18, 38)
                rheight = rng.integers(10, 22)
                rocks.append((rx, ry, rwidth, rheight))
            self._mountain_cache["rocks"] = rocks

        if not hasattr(self, "_mountain_star_tick"):
            self._mountain_star_tick = 0
        self._mountain_star_tick += 1
        # Twinkle: every ~2 seconds, remove/add a star
        if self._mountain_star_tick > 120:
            self._mountain_star_tick = 0
            dynamic_stars = self._mountain_cache.get("dynamic_stars", set())
            if isinstance(dynamic_stars, set) and len(dynamic_stars) > 0:
                dynamic_stars.pop()
            # Add a new star at a random position above the mountains
            sx = random.randint(0, self.width())
            xnew = self._mountain_cache.get("mountain_xnew")
            ynew = self._mountain_cache.get("mountain_ynew")
            if xnew is not None and ynew is not None:
                idx = int((sx / self.width()) * (len(xnew) - 1))
                mountain_y_at_x = int(ynew[idx])
                sy = random.randint(0, max(0, mountain_y_at_x - 1))
                dynamic_stars.add((sx, sy))
            self._mountain_cache["dynamic_stars"] = dynamic_stars
        dynamic_stars = self._mountain_cache.get("dynamic_stars", set())
        if isinstance(dynamic_stars, set):
            for sx, sy in dynamic_stars:
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
                    color = QColor(255, 240, 200, 255)  # Yellow-white
            else:
                brightness = random.randint(180, 255)
        if random.random() < 0.0002:
            xnew = self._mountain_cache.get("mountain_xnew")
            ynew = self._mountain_cache.get("mountain_ynew")
            if xnew is not None and ynew is not None:
                sx = random.randint(int(self.width() * 0.1), int(self.width() * 0.9))
                idx = int((sx / self.width()) * (len(xnew) - 1))
                mountain_y_at_x = int(ynew[idx])
                sy = random.randint(10, max(10, mountain_y_at_x - 30))
                length = random.randint(30, 60)
                angle = random.uniform(-0.3, 0.3)
                ex = sx + int(length * math.cos(angle))
                ey = sy + int(length * math.sin(angle))
                self._mountain_shooting_stars.append({
                    "sx": sx, "sy": sy, "ex": ex, "ey": ey, "life": 24
                })
            ynew = self._mountain_cache["mountain_ynew"]
            sx = random.randint(int(self.width() * 0.1), int(self.width() * 0.9))
            idx = int((sx / self.width()) * (len(xnew) - 1))
            mountain_y_at_x = int(ynew[idx])
            sy = random.randint(10, max(10, mountain_y_at_x - 30))
            length = random.randint(30, 60)
            angle = random.uniform(-0.3, 0.3)
            ex = sx + int(length * math.cos(angle))
            ey = sy + int(length * math.sin(angle))
            self._mountain_shooting_stars.append({
                "sx": sx, "sy": sy, "ex": ex, "ey": ey, "life": 24
            })
        # Draw and update shooting stars
        for star in list(self._mountain_shooting_stars):
            grad = QLinearGradient(star["sx"], star["sy"], star["ex"], star["ey"])
            grad.setColorAt(0.0, QColor(255, 255, 255, 180))
            grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setPen(QPen(grad, 2))
            painter.drawLine(int(star["sx"]), int(star["sy"]), int(star["ex"]), int(star["ey"]))
            star["sx"] += (star["ex"] - star["sx"]) / star["life"]
            star["sy"] += (star["ey"] - star["sy"]) / star["life"]
            star["life"] -= 1
            if star["life"] <= 0:
                self._mountain_shooting_stars.remove(star)

        # --- Random event: flock of ducks in V formation ---
        # Ducks fly above the mountains in a V, appear randomly, animate every 16ms
        if not hasattr(self, "_duck_flock"):
            self._duck_flock = None
        if not hasattr(self, "_duck_flock_timer"):
            self._duck_flock_timer = 0
        # Chance to spawn a flock if none is present (about once every 10-20 seconds)
        if self._duck_flock is None and random.random() < 0.001:
            # Flock parameters
            flock_size = random.randint(5, 8)
            # Start just off left or right edge, randomize direction
            direction = random.choice(["right", "left"])
            if direction == "right":
                start_x = -40
                dx = random.uniform(3.0, 4.5)
                v_angle = math.radians(25)
            else:
                start_x = self.width() + 40
                dx = -random.uniform(3.0, 4.5)
                v_angle = -math.radians(25)
            # Y position: above the highest mountain, but not at the very top, and not above 50% of screen height
            y_min = int(self.height() * 0.13)
            y_max = int(self.height() * 0.50)
            start_y = random.randint(y_min, y_max)
            # V formation: point of V faces direction of flight
            ducks = []
            for i in range(flock_size):
                if i == 0:
                    offset_x = 0
                    offset_y = 0
                else:
                    row = (i + 1) // 2
                    side = -1 if i % 2 == 0 else 1
                    offset_x = math.cos(v_angle) * 18 * row * side
                    offset_y = math.sin(abs(v_angle)) * 18 * row
                ducks.append({
                    "offset_x": offset_x,
                    "offset_y": offset_y,
                })
            self._duck_flock = {
                "x": start_x,
                "y": start_y,
                "dx": dx,
                "ducks": ducks,
                "direction": direction,
                "timer": 0,
            }
        # Animate and draw flock if present
        if self._duck_flock is not None:
            flock = self._duck_flock
            flock["x"] += flock["dx"]
            flock["timer"] += 1
            # Remove flock if off screen
            if (flock["direction"] == "right" and flock["x"] - 40 > self.width()) or \
                (flock["direction"] == "left" and flock["x"] + 40 < 0):
                self._duck_flock = None
            else:
                # Draw each duck (smaller size)
                for duck in flock["ducks"]:
                    duck_x = int(flock["x"] + duck["offset_x"])
                    duck_y = int(flock["y"] + duck["offset_y"])
                    # Clamp duck_y to not go above 50% of screen height
                    duck_y = max(int(self.height() * 0.13), min(duck_y, int(self.height() * 0.50)))
                    # Duck body: small ellipse, brownish
                    painter.setBrush(QColor(120, 90, 60, 220))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(duck_x, duck_y, 8, 4)
                    # Duck head: smaller ellipse, darker
                    painter.setBrush(QColor(80, 60, 40, 220))
                    painter.drawEllipse(duck_x + 5 if flock["dx"] > 0 else duck_x - 3, duck_y + 1, 3, 3)
                    # Duck beak: small triangle, orange
                    painter.setBrush(QColor(220, 140, 40, 220))
                    if flock["dx"] > 0:
                        beak = [
                            QPointF(duck_x + 10, duck_y + 2),
                            QPointF(duck_x + 13, duck_y + 2.5),
                            QPointF(duck_x + 10, duck_y + 4),
                        ]
                    else:
                        beak = [
                            QPointF(duck_x - 1, duck_y + 2),
                            QPointF(duck_x - 4, duck_y + 2.5),
                            QPointF(duck_x - 1, duck_y + 4),
                        ]
                    painter.drawPolygon(*beak)
                    # Duck wing: arc or ellipse, slightly lighter
                    painter.setBrush(QColor(160, 120, 80, 180))
                    painter.drawEllipse(duck_x + 1, duck_y + 1, 5, 2)
                    # Optionally, animate wing up/down (flap) using timer
                    if ((flock["timer"] // 6) % 2) == 0:
                        painter.drawEllipse(duck_x + 1, duck_y - 1, 5, 2)
                    else:
                        painter.drawEllipse(duck_x + 1, duck_y + 3, 5, 2)

        # 4. Draw the moon (above mountains, not touching peaks)
        # Place moon before drawing ridges so it appears behind the peaks
        moon_radius = 38
        moon_x = int(self.width() * 0.78)
        moon_y = int(self.height() * 0.13)  # Move moon higher so it doesn't overlap peaks
        moon_color = QColor(245, 235, 200, 220)
        painter.setBrush(moon_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(moon_x, moon_y, moon_radius, moon_radius)
        # Subtle radial gradient for moon shading
        grad = QRadialGradient(
            moon_x + moon_radius // 2, moon_y + moon_radius // 2, moon_radius
        )
        grad.setColorAt(0.0, QColor(255, 255, 230, 180))
        grad.setColorAt(0.7, QColor(230, 230, 210, 80))
        grad.setColorAt(1.0, QColor(180, 180, 170, 40))
        painter.setBrush(grad)
        painter.drawEllipse(moon_x, moon_y, moon_radius, moon_radius)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QColor(230, 230, 210, 220))
        painter.setPen(moon_color)
        ridges = self._mountain_cache.get("ridges")
        if isinstance(ridges, list):
            for idx, ridge_info in enumerate(ridges):
                ridge_xnew, ridge_ynew = ridge_info["ridge"]
                color = ridge_info["color"]
                alpha = ridge_info["alpha"]
                tree_density = ridge_info["tree_density"]
                # Draw the ridge
                path = QPainterPath()
                path.moveTo(0, self.height())
                for xi, yi in zip(ridge_xnew, ridge_ynew):
                    path.lineTo(float(xi), float(yi))
                path.lineTo(self.width(), self.height())
                path.closeSubpath()
                # For the furthest back mountain, ensure the path is closed and filled
                painter.setBrush(QColor(int(color[0]), int(color[1]), int(color[2]), int(alpha)))
                painter.setPen(QColor(int(color[0]), int(color[1]), int(color[2]), int(alpha * 0.8)))
                painter.drawPath(path)
                # Optionally, draw trees as small triangles
                if tree_density > 0:
                    rng = np.random.default_rng(seed=int(ridge_info["y_offset"]*1000))
                    for i in range(0, len(ridge_xnew), max(1, int(20 / tree_density))):
                        if rng.random() < tree_density:
                            tx = float(ridge_xnew[i])
                            ty = float(ridge_ynew[i])
                            tree_height = float(rng.integers(16, 28))
                            tree_width = float(rng.integers(7, 13))
                            tree_color = QColor(20, 30, 20, min(255, int(alpha * 1.1)))
                            painter.setBrush(tree_color)
                            painter.setPen(Qt.PenStyle.NoPen)
                            points = [
                                QPointF(tx, ty - tree_height),
                                QPointF(tx - tree_width / 2, ty),
                                QPointF(tx + tree_width / 2, ty),
                            ]
        rocks = self._mountain_cache.get("rocks")
        if isinstance(rocks, list):
            for rx, ry, rwidth, rheight in rocks:
                rock_color = QColor(30, 32, 38, 255)
                painter.setBrush(rock_color)
                painter.setPen(QColor(18, 18, 22, 200))
                painter.drawEllipse(int(rx), int(ry), int(rwidth), int(rheight))
                tree_color = QColor(20, 30, 20, int(alpha * 1.1))
                painter.setBrush(tree_color)
                painter.setPen(Qt.PenStyle.NoPen)
                points = [
                    QPointF(tx, ty - tree_height),
                    QPointF(tx - tree_width // 2, ty),
                    QPointF(tx + tree_width // 2, ty),
                ]
                painter.drawPolygon(*points)

        # Draw cached boulders/rocks in the foreground
        for rx, ry, rwidth, rheight in self._mountain_cache["rocks"]:
            rock_color = QColor(30, 32, 38, 255)
            painter.setBrush(rock_color)
            painter.setPen(QColor(18, 18, 22, 200))
            painter.drawEllipse(int(rx), int(ry), int(rwidth), int(rheight))
