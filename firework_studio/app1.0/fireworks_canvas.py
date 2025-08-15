import random
import math
import numpy as np
from scipy.interpolate import make_interp_spline

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, QPointF, Qt, QRectF, QPoint
from PyQt6.QtGui import QColor, QPainter, QPen, QLinearGradient, QRadialGradient, QPainterPath, QPixmap, QPolygon

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
        # Reduce particle count if too many fireworks are being drawn
        if len(self.fireworks) >= 20:
            self.particle_count = 5
        elif len(self.fireworks) >= 10:
            self.particle_count = 15
        else:
            self.particle_count = 50
        
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
            self.draw_background_desert(painter)
        elif self.background == "custom":
            if self._custom_bg_pixmap:
                painter.drawPixmap(self.rect(), self._custom_bg_pixmap)
        # Draw fireworks particles after background
        self.draw_fireworks(painter)

    def draw_fireworks(self, painter):
        # Draw fireworks
        for firework in self.fireworks:
            # Draw the firework launch point if not exploded
            if not firework.exploded:
                color = firework.color if isinstance(firework.color, QColor) else QColor(255, 0, 0)
                painter.setPen(QPen(color, 4))
                painter.drawPoint(int(firework.x), int(firework.y))
            # Draw the explosion particles
            if self._fireworks_enabled:
                for particle in firework.particles:
                    particle.resume()
                    px = particle.x
                    py = particle.y
                    color = particle.get_color()
                    if not isinstance(color, QColor):
                        color = QColor(255, 255, 255)
                    painter.setPen(QPen(color, 3))
                    painter.drawPoint(int(px), int(py))
            else:
                # Freeze frame: draw particles at their last positions
                for particle in firework.particles:
                    particle.freeze()
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

        # Add subtle moon craters (texture) - cache so craters don't change every frame
        if not hasattr(self, "_moon_craters_cache") or self._moon_craters_cache is None \
            or self._moon_craters_cache.get("moon_x") != moon_x \
            or self._moon_craters_cache.get("moon_y") != moon_y \
            or self._moon_craters_cache.get("moon_radius") != moon_radius:
            # Use a deterministic random seed based on moon position and radius
            seed_str = f"{moon_x},{moon_y},{moon_radius}"
            rng = random.Random(seed_str)
            craters = []
            for _ in range(7):
                cr_x = moon_x + rng.randint(7, moon_radius - 12)
                cr_y = moon_y + rng.randint(7, moon_radius - 12)
                cr_r = rng.randint(3, 7)
                craters.append((cr_x, cr_y, cr_r))
            self._moon_craters_cache = {
                "moon_x": moon_x,
                "moon_y": moon_y,
                "moon_radius": moon_radius,
                "craters": craters
            }
        painter.setBrush(QColor(200, 190, 120, 130))  # Brighter, more opaque for visibility
        painter.setPen(Qt.PenStyle.NoPen)
        for cr_x, cr_y, cr_r in self._moon_craters_cache["craters"]:
            painter.drawEllipse(cr_x, cr_y, cr_r, cr_r)

        # --- Draw detailed coastline silhouette in foreground with palm tree ---

        coastline_height = int(self.height() * 0.15)
        coastline_y = self.height() - coastline_height

        # Draw detailed, rough coastline silhouette (foreground, black, jagged and irregular)
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
            # Generate jagged coastline silhouette
            points = []
            n_points = max(40, self.width() // 18)
            for i in range(n_points + 1):
                x = int(i * self.width() / n_points)
                # Main base line
                base_y = coastline_y + 12
                # Add large-scale jaggedness
                jag = (
                    math.sin(i * 0.7) * 18 +
                    math.cos(i * 0.33) * 11 +
                    rng.uniform(-10, 10)
                )
                # Add small-scale roughness
                rough = (
                    math.sin(i * 2.2) * 4 +
                    math.cos(i * 1.7) * 3 +
                    rng.uniform(-3, 3)
                )
                y = int(base_y + jag + rough)
                # Add occasional "rock outcrop" (sharp dip)
                if i > 2 and rng.random() < 0.09:
                    y += rng.uniform(18, 38)
                points.append((x, y))
            # Draw the jagged coastline
            for x, y in points:
                path.lineTo(x, y)
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

        # --- Palm trees with gentle sway ---
        # Animate sway using time (frame count)
        if not hasattr(self, "_palm_sway_tick"):
            self._palm_sway_tick = 0
        self._palm_sway_tick += 1
        sway_phase = self._palm_sway_tick / 32.0  # Slow, gentle
        # List of palm tree positions and trunk heights (relative to coastline)
        palm_vertical_shift = int(self.height() * 0.025)  # Shift all palms down by ~2.5% of height
        palms = [
            (int(self.width() * 0.13), int(coastline_y + 18 + palm_vertical_shift), int(self.height() * 0.18)),  # main left
            (int(self.width() * 0.19), int(coastline_y + 20 + palm_vertical_shift), int(self.height() * 0.12)),  # right of main
            (int(self.width() * 0.10), int(coastline_y + 28 + palm_vertical_shift), int(self.height() * 0.11)),  # left of main
            (int(self.width() * 0.16), int(coastline_y + 32 + palm_vertical_shift), int(self.height() * 0.09)),  # short, in front
            (int(self.width() * 0.09), int(coastline_y + 12 + palm_vertical_shift), int(self.height() * 0.15)),  # far left
        ]

        palm_color = QColor(0, 0, 0, 255)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        for palm_idx, (palm_base_x, palm_base_y, trunk_height) in enumerate(palms):
            # Sway offset: each palm has a slightly different phase and amplitude
            sway_amp = 10 + palm_idx * 2
            sway = math.sin(sway_phase + palm_idx * 0.7) * sway_amp
            # Draw trunk (curved, swaying)
            trunk_path = QPainterPath()
            trunk_path.moveTo(palm_base_x, palm_base_y)
            trunk_path.cubicTo(
                palm_base_x + 10 + sway * 0.3, palm_base_y - trunk_height // 3,
                palm_base_x - 18 + sway * 0.7, palm_base_y - trunk_height * 2 // 3,
                palm_base_x + 8 + sway, palm_base_y - trunk_height
            )
            painter.setPen(QPen(palm_color, 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawPath(trunk_path)
            # Draw palm leaves (silhouette, 7-8 leaves) - cache per palm so leaves don't change every frame
            if not hasattr(self, "_palm_leaves_cache"):
                self._palm_leaves_cache = {}
            palm_id = (palm_base_x, palm_base_y, trunk_height)
            if palm_id not in self._palm_leaves_cache:
                # Generate and cache leaf geometry for this palm
                center_x = palm_base_x + 8
                center_y = palm_base_y - trunk_height
                n_leaves = 8
                leaf_angles = np.linspace(-110, 110, n_leaves)
                leaves = []
                for angle in leaf_angles:
                    radians = math.radians(angle)
                    leaf_len = random.randint(54, 62)
                    ctrl1_x = center_x + math.cos(radians) * (leaf_len * 0.33)
                    ctrl1_y = center_y + math.sin(radians) * (leaf_len * 0.33) - 8
                    ctrl2_x = center_x + math.cos(radians) * (leaf_len * 0.66)
                    ctrl2_y = center_y + math.sin(radians) * (leaf_len * 0.66) + 8
                    end_x = center_x + math.cos(radians) * leaf_len
                    end_y = center_y + math.sin(radians) * leaf_len
                    leaflets = []
                    for t in np.linspace(0.18, 0.82, 5):
                        lx = center_x + (end_x - center_x) * t
                        ly = center_y + (end_y - center_y) * t
                        perp_angle = radians + math.pi / 2
                        leaflet_len = 8 + 2 * math.cos((t - 0.5) * math.pi)
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
            # Draw cached leaves, but sway the leaves' base with the trunk
            painter.setPen(QPen(palm_color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for leaf in self._palm_leaves_cache[palm_id]:
                center_x, center_y = leaf["center"]
                # Sway the leaf base with the trunk
                sway_leaf = sway * 0.7
                ctrl1_x, ctrl1_y = leaf["ctrl1"]
                ctrl2_x, ctrl2_y = leaf["ctrl2"]
                end_x, end_y = leaf["end"]
                leaf_path = QPainterPath()
                leaf_path.moveTo(center_x + sway_leaf, center_y)
                leaf_path.cubicTo(
                    ctrl1_x + sway_leaf, ctrl1_y,
                    ctrl2_x + sway_leaf, ctrl2_y,
                    end_x + sway_leaf, end_y
                )
                painter.drawPath(leaf_path)
                # Draw leaflets as short lines
                for lx1, ly1, lx2, ly2 in leaf["leaflets"]:
                    painter.drawLine(int(lx1 + sway_leaf), int(ly1), int(lx2 + sway_leaf), int(ly2))

        # --- Seagulls (animated, silhouetted, flying across the screen) ---
        # Each seagull is a dict: {x, y, speed, wing_phase, direction}
        if not hasattr(self, "_seagulls"):
            self._seagulls = []
        # Occasionally spawn a new seagull (randomly, but not too many)
        if random.random() < 0.012 and len(self._seagulls) < 2:
            direction = random.choice(["right", "left"])
            if direction == "right":
                x = -40
                speed = random.uniform(2.0, 3.5)
            else:
                x = self.width() + 40
                speed = -random.uniform(2.0, 3.5)
            y = random.randint(int(self.height() * 0.18), int(self.height() * 0.45))
            wing_phase = random.uniform(0, 2 * math.pi)
            self._seagulls.append({
                "x": x,
                "y": y,
                "speed": speed,
                "wing_phase": wing_phase,
                "direction": direction,
            })
        # Animate and draw seagulls with more natural movement (flapping, bobbing, slight up/down drift)
        new_seagulls = []
        for gull in self._seagulls:
            # Horizontal movement
            gull["x"] += gull["speed"]
            # Wing phase for flapping
            gull["wing_phase"] += 0.18 + random.uniform(-0.02, 0.02)
            # Add vertical bobbing and gentle up/down drift
            if "drift_phase" not in gull:
                gull["drift_phase"] = random.uniform(0, 2 * math.pi)
            if "drift_speed" not in gull:
                gull["drift_speed"] = random.uniform(0.008, 0.018)
            gull["drift_phase"] += gull["drift_speed"]
            drift = math.sin(gull["drift_phase"]) * 2.5  # gentle up/down drift
            # Remove if off screen
            if -60 < gull["x"] < self.width() + 60:
                new_seagulls.append(gull)
                # Draw seagull as a simple "M" shape (two arcs)
                x = int(gull["x"])
                y = int(gull["y"] + drift)
                wing_span = 32 + random.randint(-2, 2)
                # Flapping: wings go up and down
                flap = math.sin(gull["wing_phase"])
                wing_flap = flap * 12  # more pronounced flapping
                body_y = y + 4 + math.sin(gull["wing_phase"] * 0.7) * 2
                # Draw left and right wings as arcs, with flapping
                painter.setPen(QPen(QColor(0, 0, 0, 255), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                if gull["direction"] == "right":
                    # Left wing
                    painter.drawArc(
                        x - wing_span // 2,
                        int(body_y - 8 - wing_flap),
                        wing_span,
                        18 + int(wing_flap),
                        200 * 16,
                        70 * 16
                    )
                    # Right wing
                    painter.drawArc(
                        x - wing_span // 2,
                        int(body_y - 8 - wing_flap),
                        wing_span,
                        18 + int(wing_flap),
                        270 * 16,
                        70 * 16
                    )
                else:
                    # Left wing
                    painter.drawArc(
                        x - wing_span // 2,
                        int(body_y - 8 - wing_flap),
                        wing_span,
                        18 + int(wing_flap),
                        200 * 16,
                        70 * 16
                    )
                    # Right wing
                    painter.drawArc(
                        x - wing_span // 2,
                        int(body_y - 8 - wing_flap),
                        wing_span,
                        18 + int(wing_flap),
                        270 * 16,
                        70 * 16
                    )
        self._seagulls = new_seagulls

        # Restore pen
        painter.setPen(QColor(230, 230, 210, 220))
    # --- Animated, Detailed Clouds for Sunset Scene ---
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
                # Add sub-ellipses for detail
                "parts": [
                    {
                        "dx": random.randint(-20, 20),
                        "dy": random.randint(-8, 8),
                        "w": random.uniform(0.5, 1.1),
                        "h": random.uniform(0.5, 1.1),
                        "alpha": random.randint(60, 120)
                    }
                    for _ in range(random.randint(3, 7))
                ]
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
                cloud["parts"] = [
                    {
                        "dx": random.randint(-20, 20),
                        "dy": random.randint(-8, 8),
                        "w": random.uniform(0.5, 1.1),
                        "h": random.uniform(0.5, 1.1),
                        "alpha": random.randint(60, 120)
                    }
                    for _ in range(random.randint(3, 7))
                ]

    # Override: draw detailed clouds in draw_background_sunset
    def draw_detailed_cloud(self, painter, cloud, cloud_colors):
        # Draw main ellipse
        painter.setBrush(cloud_colors[cloud["color_idx"] % len(cloud_colors)])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            int(cloud["x"]),
            int(cloud["y"]),
            int(cloud["width"]),
            int(cloud["height"])
        )
        # Draw sub-ellipses for detail
        for part in cloud.get("parts", []):
            color = cloud_colors[cloud["color_idx"] % len(cloud_colors)]
            color = QColor(color.red(), color.green(), color.blue(), part["alpha"])
            painter.setBrush(color)
            painter.drawEllipse(
                int(cloud["x"] + part["dx"] + cloud["width"] * 0.2),
                int(cloud["y"] + part["dy"] + cloud["height"] * 0.2),
                int(cloud["width"] * part["w"]),
                int(cloud["height"] * part["h"])
            )

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

        # 8. Fish fin random event (animated)
        # Fish fin appears randomly, moves across water, then disappears
        if not hasattr(self, "_fish_fin"):
            self._fish_fin = None
            self._fish_fin_timer = 0

        # Chance to spawn a fish fin if none is present (about once every 8-16 seconds)
        if self._fish_fin is None and random.random() < 0.001:
            direction = random.choice(["right", "left"])
            if direction == "right":
                start_x = -40
                dx = random.uniform(2.0, 3.5)
            else:
                start_x = self.width() + 40
                dx = -random.uniform(2.0, 3.5)
            # Water area: from horizon_y to self.height()
            water_top = horizon_y + 8
            water_bottom = self.height() - 12
            y = random.randint(water_top, water_bottom)
            self._fish_fin = {
                "x": start_x,
                "y": y,
                "dx": dx,
                "dy": 0.0,
                "direction": direction,
                "timer": 0,
                "target_dx": dx,
                "target_dy": 0.0,
                "change_tick": 0,
                "life": random.randint(240, 400),  # frames
            }

        # Animate and draw fish fin if present
        if self._fish_fin is not None:
            fin = self._fish_fin
            # Every 18-36 frames, pick a new random dx/dy target
            fin["change_tick"] += 1
            if fin["change_tick"] > random.randint(18, 36):
                # Randomly adjust dx and dy, but keep general direction
                if fin["direction"] == "right":
                    fin["target_dx"] = random.uniform(1.8, 4.0)
                else:
                    fin["target_dx"] = -random.uniform(1.8, 4.0)
                fin["target_dy"] = random.uniform(-1.2, 1.2)
                fin["change_tick"] = 0
            # Smoothly approach target dx/dy
            fin["dx"] += (fin["target_dx"] - fin["dx"]) * 0.18
            fin["dy"] += (fin["target_dy"] - fin["dy"]) * 0.18

            # Move fin
            fin["x"] += fin["dx"]
            fin["y"] += fin["dy"]
            fin["timer"] += 1
            fin["life"] -= 1

            # Keep fin within water area
            water_top = horizon_y + 8
            water_bottom = self.height() - 12
            if fin["y"] < water_top:
                fin["y"] = water_top
                fin["dy"] = abs(fin["dy"])
                fin["target_dy"] = abs(fin["target_dy"])
            elif fin["y"] > water_bottom:
                fin["y"] = water_bottom
                fin["dy"] = -abs(fin["dy"])
                fin["target_dy"] = -abs(fin["target_dy"])

            # Draw fish fin (triangle)
            base_x = int(fin["x"])
            base_y = int(fin["y"])
            width = 22
            height = 18
            painter.setBrush(QColor(60, 60, 70, 220))
            painter.setPen(Qt.PenStyle.NoPen)
            if fin["direction"] == "right":
                points = [
                    QPointF(base_x, base_y),
                    QPointF(base_x + width, base_y),
                    QPointF(base_x + width // 2, base_y - height + int(math.sin(fin["timer"] * 0.18) * 3)),
                ]
            else:
                points = [
                    QPointF(base_x, base_y),
                    QPointF(base_x - width, base_y),
                    QPointF(base_x - width // 2, base_y - height + int(math.sin(fin["timer"] * 0.18) * 3)),
                ]
            painter.drawPolygon(*points)
            # Draw a subtle wake behind the fin
            painter.setBrush(QColor(255, 255, 255, 60))
            if fin["direction"] == "right":
                painter.drawEllipse(base_x - 10, base_y + 2, 16, 4)
            else:
                painter.drawEllipse(base_x - 6, base_y + 2, 16, 4)
            # Remove if off screen or life expired
            if (fin["direction"] == "right" and fin["x"] > self.width() + 40) or \
               (fin["direction"] == "left" and fin["x"] < -40) or \
               fin["life"] <= 0:
                self._fish_fin = None

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
            # Slowly update only one random window in one random building every ~6 seconds
            if not hasattr(self, "_city_window_ticks"):
                self._city_window_ticks = 0
            self._city_window_ticks += 1
            if self._city_window_ticks > 360:  # ~6 seconds at 60 FPS
                self._city_window_ticks = 0
                if self._city_window_states:
                    bidx = random.randint(0, len(self._city_window_states) - 1)
                    states = self._city_window_states[bidx]
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

        # --- Plane flyby event with waving banner ---
        # Plane flies slowly from left to right near the top of the screen with a flashing red light
        # Now: plane appears much less frequently, and carries a waving banner

        # Plane spawn logic: only spawn a new plane if none is present, and with low probability
        if not hasattr(self, "_plane_flyby") or self._plane_flyby is None:
            if not hasattr(self, "_plane_flyby_cooldown"):
                self._plane_flyby_cooldown = random.randint(0, 1)  # 20-36 seconds at 60 FPS
            if self._plane_flyby_cooldown > 0:
                self._plane_flyby_cooldown -= 1
            else:
                # Spawn plane
                self._plane_flyby = {
                    "x": -60,
                    "y": int(self.height() * 0.09) + random.randint(-10, 10),
                    "speed": max(0.5, self.width() / 4000),  # Much slower plane
                    "flash_tick": 0,
                    "flash_on": True,
                    "banner_wave_tick": 0,
                }
                self._plane_flyby_cooldown = random.randint(1200, 2200)  # Reset cooldown
        plane = getattr(self, "_plane_flyby", None)
        if plane is not None:
            # Move plane
            plane["x"] += plane["speed"]
            if plane["x"] > self.width() + 200:
            # Remove plane when off screen
                self._plane_flyby = None
            else:
                # Flashing logic: flash every ~0.7s (about 44 frames at 16ms)
                plane["flash_tick"] += 1
                if plane["flash_tick"] > 44:
                    plane["flash_tick"] = 0
                    plane["flash_on"] = not plane["flash_on"]
                px = int(plane["x"])
                py = int(plane["y"])

                # --- Draw waving banner advertising Firework Studio ---
                banner_text = "FIREWORK STUDIO"
                banner_length = 120
                banner_height = 18
                n_points = 18
                wave_amplitude = 8
                plane["banner_wave_tick"] += 1
                t_wave = plane["banner_wave_tick"]

                # The banner should start behind the plane, so the cable attaches to the back of the banner.
                # The cable attaches at (px + 8, py + 3), so set banner_x0 to be at the far end of the banner.
                banner_x0 = px - 80 - banner_length
                banner_y0 = py + 3 - banner_height // 2

                banner_points = []
                for i in range(n_points):
                    x = banner_x0 + i * (banner_length / (n_points - 1))
                    phase = (i / (n_points - 1)) * math.pi * 2
                    # Make the wave much slower by reducing the multiplier on t_wave
                    y = banner_y0 + math.sin(phase + t_wave * 0.045) * (wave_amplitude * 0.7)
                    banner_points.append(QPointF(x, y))
                # Draw the string/rope connecting plane to banner (drawn after banner, so in front of banner but behind plane)
                painter.setPen(QPen(QColor(90, 90, 90, 180), 2))
                painter.drawLine(px + 8, py + 3, banner_x0, banner_y0 + banner_height // 2)

                # Plane body (tiny, dark gray) - drawn after cable so plane is in front
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
                    
                # Draw banner background as a polygon (top and bottom)
                top_points = banner_points
                bottom_points = [QPointF(p.x(), p.y() + banner_height) for p in reversed(banner_points)]
                banner_polygon = top_points + bottom_points
                painter.setBrush(QColor(255, 255, 230, 230))
                painter.setPen(QPen(QColor(180, 180, 180, 180), 2))
                painter.drawPolygon(*banner_polygon)
                # Draw banner outline
                painter.setPen(QPen(QColor(120, 120, 120, 180), 2))
                painter.drawPolyline(*top_points)
                painter.drawPolyline(*bottom_points)

                # Draw text on banner (each letter follows the wave)
                painter.setPen(QColor(80, 40, 0, 255))
                font = painter.font()
                font.setBold(True)
                font.setPointSize(10)
                painter.setFont(font)
                text = banner_text
                n_letters = len(text)
                # Only draw if there is enough room
                if n_letters > 1 and len(banner_points) >= n_letters:
                    # Place letters evenly along the banner's actual length, with a small margin
                    margin = 7  # pixels margin at each end
                    usable_points = banner_points
                    usable_len = len(usable_points)
                    for i, ch in enumerate(text):
                        # Compute the proportional position along the banner, with margin
                        t = (i + 0.5) / n_letters  # center letters, avoid cut-off
                        idx_f = margin / banner_length + t * (1 - 2 * margin / banner_length)
                        idx_f = idx_f * (usable_len - 1)
                        idx = int(idx_f)
                        frac = idx_f - idx
                        if idx < usable_len - 1:
                            pt1 = usable_points[idx]
                            pt2 = usable_points[idx + 1]
                            x = pt1.x() + (pt2.x() - pt1.x()) * frac
                            y = pt1.y() + (pt2.y() - pt1.y()) * frac
                            dx = pt2.x() - pt1.x()
                            dy = pt2.y() - pt1.y()
                        else:
                            x = usable_points[idx].x()
                            y = usable_points[idx].y()
                            dx = 1
                            dy = 0
                        angle = math.degrees(math.atan2(dy, dx))
                        painter.save()
                        painter.translate(x, y + banner_height / 2)
                        painter.rotate(angle)
                        painter.drawText(QRectF(-7, -banner_height / 2 + 1, 14, banner_height), Qt.AlignmentFlag.AlignCenter, ch)
                        painter.restore()

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

        if not hasattr(self, "_mountain_star_tick"):
            self._mountain_star_tick = 0
        self._mountain_star_tick += 1
        # Twinkle: every ~8 seconds, remove/add a star (was 2 seconds)
        if self._mountain_star_tick > 480:
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
                twinkle = random.randint(0, 100)
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
            # Draw a few shooting stars (above the mountains)
            xnew = self._mountain_cache.get("mountain_xnew")
            ynew = self._mountain_cache.get("mountain_ynew")
            if xnew is not None and ynew is not None:
                for _ in range(2):
                    if random.random() < 0.0002:  # Rarely appear
                        sx = random.randint(int(self.width() * 0.1), int(self.width() * 0.9))
                        idx = int((sx / self.width()) * (len(xnew) - 1))
                        mountain_y_at_x = int(ynew[idx])
                        sy = random.randint(10, max(10, mountain_y_at_x - 30))
                        length = random.randint(30, 60)
                        angle = random.uniform(-0.3, 0.3)
                        ex = sx + int(length * math.cos(angle))
                        ey = sy + int(length * math.sin(angle))
                        grad = QLinearGradient(sx, sy, ex, ey)
                        grad.setColorAt(0.0, QColor(255, 255, 255, 180))
                        grad.setColorAt(1.0, QColor(255, 255, 255, 0))
                        painter.setPen(QPen(grad, 2))
                        painter.drawLine(sx, sy, ex, ey)
        # Draw a large waxing moon with texture and slightly yellow tint
        moon_radius = 76  # Larger moon
        moon_x = int(self.width() * 0.8)
        moon_y = int(self.height() * 0.13)
        moon_color = QColor(245, 235, 180, 230)  # Slightly yellowish

        # Draw full moon base
        painter.setBrush(moon_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(moon_x, moon_y, moon_radius, moon_radius)

        # Subtle radial gradient for moon shading
        grad = QRadialGradient(
            moon_x + moon_radius // 2, moon_y + moon_radius // 2, moon_radius
        )
        grad.setColorAt(0.0, QColor(255, 255, 230, 200))
        grad.setColorAt(0.7, QColor(230, 230, 210, 120))
        grad.setColorAt(1.0, QColor(180, 180, 170, 80))
        painter.setBrush(grad)
        painter.drawEllipse(moon_x, moon_y, moon_radius, moon_radius)

        # Add more detailed moon craters (texture) - cache so craters don't change every frame
        if not hasattr(self, "_moon_craters_cache") or self._moon_craters_cache is None \
            or self._moon_craters_cache.get("moon_x") != moon_x \
            or self._moon_craters_cache.get("moon_y") != moon_y \
            or self._moon_craters_cache.get("moon_radius") != moon_radius:
            # Use a deterministic random seed based on moon position and radius
            seed_str = f"{moon_x},{moon_y},{moon_radius}"
            rng = random.Random(seed_str)
            craters = []
            n_main_craters = 18
            n_small_craters = 22
            # Main craters (larger, more visible)
            for _ in range(n_main_craters):
                cr_x = moon_x + rng.randint(10, moon_radius - 22)
                cr_y = moon_y + rng.randint(10, moon_radius - 22)
                cr_r = rng.randint(6, 13)
                craters.append((cr_x, cr_y, cr_r))
            # Small craters (fine detail)
            for _ in range(n_small_craters):
                cr_x = moon_x + rng.randint(6, moon_radius - 10)
                cr_y = moon_y + rng.randint(6, moon_radius - 10)
                cr_r = rng.randint(2, 5)
                craters.append((cr_x, cr_y, cr_r))
            # Add some crater clusters for realism
            for _ in range(5):
                base_x = moon_x + rng.randint(14, moon_radius - 18)
                base_y = moon_y + rng.randint(14, moon_radius - 18)
                for _ in range(rng.randint(2, 4)):
                    cr_x = base_x + rng.randint(-6, 6)
                    cr_y = base_y + rng.randint(-6, 6)
                    cr_r = rng.randint(2, 6)
                    craters.append((cr_x, cr_y, cr_r))
            self._moon_craters_cache = {
            "moon_x": moon_x,
            "moon_y": moon_y,
            "moon_radius": moon_radius,
            "craters": craters
            }
        painter.setBrush(QColor(200, 190, 120, 130))  # Brighter, more opaque for visibility
        painter.setPen(Qt.PenStyle.NoPen)
        for cr_x, cr_y, cr_r in self._moon_craters_cache["craters"]:
            # Only draw craters that are not fully covered by the shadow (right side of moon)
            if cr_x > moon_x + moon_radius // 2 - 6:
                painter.drawEllipse(cr_x, cr_y, cr_r, cr_r)

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
            # Y position: above the highest mountain, but not at the very top, and not above 15% of screen height
            y_min = int(self.height() * 0.13)
            y_max = int(self.height() * 0.15)
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
        # 3. Draw ducks in flock (if present) - black silhouette for night
        if self._duck_flock is not None:
            flock = self._duck_flock
            # Animate flock movement
            flock["x"] += flock["dx"]
            flock["timer"] += 1
            # Remove flock if it moves off screen
            if (flock["direction"] == "right" and flock["x"] > self.width() + 40) or \
               (flock["direction"] == "left" and flock["x"] < -40):
                self._duck_flock = None
            else:
                for duck in flock["ducks"]:
                    duck_x = int(flock["x"] + duck["offset_x"])
                    duck_y = int(flock["y"] + duck["offset_y"])
                    duck_y = max(int(self.height() * 0.13), min(duck_y, int(self.height() * 0.30)))
                    # All black silhouette for night
                    painter.setBrush(QColor(0, 0, 0, 230))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(duck_x, duck_y, 8, 4)  # body
                    painter.drawEllipse(duck_x + 5 if flock["dx"] > 0 else duck_x - 3, duck_y + 1, 3, 3)  # head
                    # Beak (black, blends in)
                    if flock["dx"] > 0:
                        beak = [
                            QPointF(duck_x + 10, duck_y + 2),
                            QPointF(duck_x + 13, duck_y + 2.5),
                            QPointF(duck_x + 10, duck_y + 4),
                        ]
                        painter.drawPolygon(*beak)
                    else:
                        beak = [
                            QPointF(duck_x - 1, duck_y + 2),
                            QPointF(duck_x - 4, duck_y + 2.5),
                            QPointF(duck_x - 1, duck_y + 4),
                        ]
                        painter.drawPolygon(*beak)
                    # Wing (black, silhouette)
                    painter.drawEllipse(duck_x + 1, duck_y + 1, 5, 2)
                    if ((flock["timer"] // 6) % 2) == 0:
                        painter.drawEllipse(duck_x + 1, duck_y - 1, 5, 2)
                    else:
                        painter.drawEllipse(duck_x + 1, duck_y + 3, 5, 2)
                        
        
        # Draw ridges in the foreground
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

    def draw_background_desert(self, painter):
        # Draw desert night sky (reuse night sky gradient)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(12, 10, 48))
        gradient.setColorAt(0.3, QColor(18, 18, 60))
        gradient.setColorAt(0.7, QColor(28, 28, 80))
        gradient.setColorAt(1.0, QColor(38, 38, 100))
        painter.fillRect(self.rect(), gradient)

        # Draw stars (same as night)
        sky_height = int(self.height() * 0.85)
        if not hasattr(self, "_desert_stars") or self._desert_stars is None or self.width() != getattr(self, "_desert_stars_width", None) or self.height() != getattr(self, "_desert_stars_height", None):
            self._desert_stars = []
            for _ in range(180):
                sx = random.randint(0, self.width())
                sy = random.randint(0, sky_height)
                brightness = random.randint(180, 255)
                self._desert_stars.append((sx, sy, brightness))
            self._desert_stars_width = self.width()
            self._desert_stars_height = self.height()
        for sx, sy, brightness in self._desert_stars:
            painter.setPen(QColor(brightness, brightness, brightness))
            painter.drawPoint(sx, sy)
            if random.random() < 0.02:
                painter.drawPoint(sx+1, sy)
                painter.drawPoint(sx, sy+1)

        # Draw moon (slightly yellow, textured)
        moon_radius = 38
        moon_x = int(self.width() * 0.82)
        moon_y = int(self.height() * 0.17)
        moon_color = QColor(245, 235, 180, 230)
        painter.setBrush(moon_color)
        painter.setPen(moon_color)
        painter.drawEllipse(moon_x, moon_y, moon_radius, moon_radius)
        grad = QRadialGradient(moon_x + moon_radius // 2, moon_y + moon_radius // 2, moon_radius)
        grad.setColorAt(0.0, QColor(255, 255, 230, 200))
        grad.setColorAt(0.7, QColor(230, 230, 210, 120))
        grad.setColorAt(1.0, QColor(180, 180, 170, 80))
        painter.setBrush(grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(moon_x, moon_y, moon_radius, moon_radius)
        painter.setPen(QColor(230, 230, 210, 220))

        # Moon craters (cache)
        if not hasattr(self, "_desert_moon_craters") or self._desert_moon_craters is None or self._desert_moon_craters.get("moon_x") != moon_x or self._desert_moon_craters.get("moon_y") != moon_y or self._desert_moon_craters.get("moon_radius") != moon_radius:
            seed_str = f"{moon_x},{moon_y},{moon_radius}"
            rng = random.Random(seed_str)
            craters = []
            for _ in range(7):
                cr_x = moon_x + rng.randint(7, moon_radius - 12)
                cr_y = moon_y + rng.randint(7, moon_radius - 12)
                cr_r = rng.randint(3, 7)
                craters.append((cr_x, cr_y, cr_r))
            self._desert_moon_craters = {
                "moon_x": moon_x,
                "moon_y": moon_y,
                "moon_radius": moon_radius,
                "craters": craters
            }
        painter.setBrush(QColor(200, 190, 120, 130))
        painter.setPen(Qt.PenStyle.NoPen)
        for cr_x, cr_y, cr_r in self._desert_moon_craters["craters"]:
            painter.drawEllipse(cr_x, cr_y, cr_r, cr_r)

        # Draw flat desert ground (dark brown)
        ground_y = int(self.height() * 0.85)
        ground_color = QColor(0, 0, 0, 210)
        painter.setBrush(ground_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, ground_y, self.width(), self.height() - ground_y)

        # Draw a large, distant hoodoo (rock spire) silhouette
        # Place it far away, but visually prominent, matching the dark style
        if not hasattr(self, "_desert_hoodoo") or self._desert_hoodoo is None or self.width() != getattr(self, "_desert_hoodoo_width", None) or self.height() != getattr(self, "_desert_hoodoo_height", None):
            rng = random.Random(self.width() * 10000 + self.height())
            # Place hoodoo near horizon, not at edge, but visually prominent
            hoodoo_base_x = int(self.width() * rng.uniform(0.62, 0.78))
            hoodoo_base_y = ground_y - int(self.height() * rng.uniform(0.07, 0.11))
            hoodoo_height = int(self.height() * rng.uniform(0.13, 0.17))
            hoodoo_width = int(self.width() * rng.uniform(0.04, 0.07))
            # Generate rough silhouette with bulges and a caprock
            n_points = 9
            points = []
            for i in range(n_points):
                x = hoodoo_base_x + int(i * hoodoo_width / (n_points - 1))
                # Main shaft: mostly vertical, but add bulges
                if i == 0 or i == n_points - 1:
                    y = ground_y
                elif i == n_points // 2:
                    # Caprock: bulge at top
                    y = hoodoo_base_y - hoodoo_height + rng.randint(-6, 6)
                else:
                    # Shaft: add bulges and roughness
                    bulge = rng.randint(-8, 8) if i % 2 == 1 else rng.randint(-4, 4)
                    y = hoodoo_base_y - int(hoodoo_height * (0.85 - abs(i - n_points // 2) * 0.13)) + bulge
                points.append((x, y))
            # Caprock: jagged ellipse as the top
            caprock_width = int(hoodoo_width * rng.uniform(0.5, 0.7))
            caprock_height = max(4, int(hoodoo_height * rng.uniform(0.06, 0.09)))  # Very flat
            caprock_x = hoodoo_base_x + (hoodoo_width - caprock_width) // 2
            caprock_y = min(y for x, y in points) - caprock_height // 2
            # Generate jagged ellipse points for caprock
            n_caprock_pts = 16
            caprock_pts = []
            cx = caprock_x + caprock_width / 2
            cy = caprock_y + caprock_height / 2
            for i in range(n_caprock_pts):
                angle = 2 * math.pi * i / n_caprock_pts
                # Jaggedness: vary radius randomly
                rx = caprock_width / 2 + rng.randint(-3, 3)
                ry = caprock_height / 2 + rng.randint(-2, 2)
                x = int(cx + rx * math.cos(angle))
                y = int(cy + ry * math.sin(angle))
                caprock_pts.append(QPointF(x, y))
                self._desert_hoodoo = {
                "base_x": hoodoo_base_x,
                "base_y": hoodoo_base_y,
                "width": hoodoo_width,
                "height": hoodoo_height,
                "points": points,
                "caprock_x": caprock_x,
                "caprock_y": caprock_y,
                "caprock_width": caprock_width,
                "caprock_height": caprock_height,
                "caprock_pts": caprock_pts,
                }
                self._desert_hoodoo_width = self.width()
                self._desert_hoodoo_height = self.height()

        hoodoo = self._desert_hoodoo
        hoodoo_color = QColor(0, 0, 0, 255)
        painter.setBrush(hoodoo_color)
        painter.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        # Start at base left
        path.moveTo(hoodoo["points"][0][0], ground_y)
        # Go up left side
        for x, y in hoodoo["points"]:
            path.lineTo(x, y)
        # Go down right side
        for x, y in reversed(hoodoo["points"]):
            path.lineTo(x, ground_y)
        path.closeSubpath()
        painter.drawPath(path)
        # Draw caprock (jagged ellipse)
        painter.setBrush(QColor(10, 10, 10, 255))
        caprock_path = QPainterPath()
        pts = hoodoo["caprock_pts"]
        if pts:
            caprock_path.moveTo(pts[0])
            for pt in pts[1:]:
                caprock_path.lineTo(pt)
            caprock_path.closeSubpath()
            painter.drawPath(caprock_path)

        # Draw two large majestic plateaus touching ground and edges, with a larger gap and more realistic shapes
        if not hasattr(self, "_majestic_plateaus") or self._majestic_plateaus is None or self.width() != getattr(self, "_majestic_plateaus_width", None) or self.height() != getattr(self, "_majestic_plateaus_height", None):
            rng = random.Random(self.width() * 10000 + self.height())
            gap_ratio = rng.uniform(0.18, 0.24)
            gap_width = int(self.width() * gap_ratio)
            left_width = int((self.width() - gap_width) // 2)
            left_height = int(self.height() * rng.uniform(0.09, 0.13))
            left_x = 0
            left_y = ground_y - left_height - int(self.height() * 0.04)
            right_width = int((self.width() - gap_width) // 2)
            right_height = int(self.height() * rng.uniform(0.09, 0.13))
            right_x = left_x + left_width + gap_width
            right_y = ground_y - right_height - int(self.height() * 0.04)
            n_points = 14

            # Generate more realistic plateau tops with flat sections and some jaggedness
            def realistic_plateau_top(x0, y0, width, flat_ratio=0.55):
                points = []
                flat_start = int(n_points * rng.uniform(0.18, 0.28))
                flat_end = int(n_points * flat_ratio)
                for i in range(n_points):
                    tx = x0 + int(i * width / (n_points - 1))
                    # Flat section in the middle, rough/jagged at ends
                    if flat_start <= i <= flat_end:
                        ty = y0 + rng.randint(-2, 2)
                    else:
                        ty = y0 + rng.randint(-10, 10)
                    # Occasional small "pillar" or "spike" for realism
                    if i > 0 and rng.random() < 0.13:
                        ty -= rng.randint(8, 18)
                    points.append((tx, ty))
                return points

            left_top_rough = realistic_plateau_top(left_x, left_y, left_width)
            right_top_rough = realistic_plateau_top(right_x, right_y, right_width)

            # Add some eroded sides and base bulges for realism
            def add_eroded_sides(x, y, width, ground_y):
                # Left side bulge
                bulge_left = [
                    (x, ground_y),
                    (x - rng.randint(4, 12), ground_y - rng.randint(8, 18)),
                    (x, y + rng.randint(8, 18))
                ]
                # Right side bulge
                bulge_right = [
                    (x + width, ground_y),
                    (x + width + rng.randint(4, 12), ground_y - rng.randint(8, 18)),
                    (x + width, y + rng.randint(8, 18))
                ]
                return bulge_left, bulge_right

            left_bulge_left, left_bulge_right = add_eroded_sides(left_x, left_y, left_width, ground_y)
            right_bulge_left, right_bulge_right = add_eroded_sides(right_x, right_y, right_width, ground_y)

            self._majestic_plateaus = [
            {
                "x": left_x,
                "y": left_y,
                "width": left_width,
                "height": left_height,
                "top_rough": left_top_rough,
                "ground_y": ground_y,
                "bulge_left": left_bulge_left,
                "bulge_right": left_bulge_right,
            },
            {
                "x": right_x,
                "y": right_y,
                "width": right_width,
                "height": right_height,
                "top_rough": right_top_rough,
                "ground_y": ground_y,
                "bulge_left": right_bulge_left,
                "bulge_right": right_bulge_right,
            }
            ]
            self._majestic_plateaus_width = self.width()
            self._majestic_plateaus_height = self.height()

        plateau_color = QColor(0, 0, 0, 255)
        painter.setBrush(plateau_color)
        painter.setPen(Qt.PenStyle.NoPen)
        rng = random.Random(self.width() * 10000 + self.height())
        for plateau in self._majestic_plateaus:
            path = QPainterPath()
            # Start at left ground edge
            path.moveTo(plateau["x"], plateau["ground_y"])
            # Left eroded bulge
            for pt in plateau["bulge_left"]:
                path.lineTo(pt[0], pt[1])
            # Top edge
            for tx, ty in plateau["top_rough"]:
                path.lineTo(tx, ty)
            # Right eroded bulge
            for pt in plateau["bulge_right"]:
                path.lineTo(pt[0], pt[1])
            # End at right ground edge
            path.lineTo(plateau["x"] + plateau["width"], plateau["ground_y"])
            path.closeSubpath()
            painter.drawPath(path)

            # Draw subtle striations (sedimentary layers) - muted tones for night
            n_layers = rng.randint(4, 7)
            layer_height = plateau["height"] // n_layers if n_layers > 0 else 1
            # Use shades of black, even darker for night scene
            for i in range(n_layers):
                shade = max(0, min(10, 4 + i * 3))  # Range: 4 to 10 (darker)
                r = g = b = shade
                layer_color = QColor(r, g, b)
                painter.setBrush(layer_color)
                painter.setPen(Qt.PenStyle.NoPen)
                # Compute layer top and bottom y
                layer_top_y = plateau["y"] + i * layer_height
                layer_bottom_y = layer_top_y + layer_height
                # Draw a polygon for the layer, following the plateau's top rough edge and ground
                layer_path = QPainterPath()
                # Clamp left/right edge for left/right plateau
                left_edge = plateau["x"]
                right_edge = plateau["x"] + plateau["width"]
                # For left plateau, don't let layers poke out left; for right plateau, don't let layers poke out right
                if plateau is self._majestic_plateaus[0]:
                    # Left plateau: clamp left edge to plateau["x"]
                    layer_path.moveTo(left_edge, min(layer_bottom_y, plateau["ground_y"]))
                else:
                    # Right plateau: clamp right edge to plateau["x"] + plateau["width"]
                    layer_path.moveTo(right_edge, min(layer_bottom_y, plateau["ground_y"]))
                # Left bulge for this layer (interpolate between bulge and top)
                if plateau.get("bulge_left"):
                    for pt in plateau["bulge_left"]:
                        # Clamp left bulge x for left plateau
                        x = max(pt[0], left_edge)
                        layer_path.lineTo(x, min(layer_bottom_y, pt[1]))
                # Top edge for this layer (interpolate between top_rough points)
                if plateau.get("top_rough"):
                    for tx, ty in plateau["top_rough"]:
                        # Clamp tx for left/right plateau
                        if plateau is self._majestic_plateaus[0]:
                            tx = max(tx, left_edge)
                        else:
                            tx = min(tx, right_edge)
                        # Clamp ty to layer_top_y/layer_bottom_y
                        if ty < layer_top_y:
                            layer_path.lineTo(tx, layer_top_y)
                        elif ty > layer_bottom_y:
                            layer_path.lineTo(tx, layer_bottom_y)
                        else:
                            layer_path.lineTo(tx, ty)
                # Right bulge for this layer
                if plateau.get("bulge_right"):
                    for pt in plateau["bulge_right"]:
                        # Clamp right bulge x for right plateau
                        x = min(pt[0], right_edge)
                        layer_path.lineTo(x, min(layer_bottom_y, pt[1]))
                # End at right/left edge, at layer_bottom_y
                if plateau is self._majestic_plateaus[0]:
                    layer_path.lineTo(left_edge, min(layer_bottom_y, plateau["ground_y"]))
                else:
                    layer_path.lineTo(right_edge, min(layer_bottom_y, plateau["ground_y"]))
                layer_path.closeSubpath()
                painter.drawPath(layer_path)

        # Draw cacti (silhouette, random positions, arms at different heights)
        if not hasattr(self, "_desert_cacti") or self._desert_cacti is None or self.width() != getattr(self, "_desert_cacti_width", None) or self.height() != getattr(self, "_desert_cacti_height", None):
            rng = random.Random(self.width() * 10000 + self.height())
            cacti = []
            n_cacti = rng.randint(7, 12)
            for _ in range(n_cacti):
                cx = rng.randint(10, self.width() - 20)
                base_y = rng.randint(ground_y + 8, self.height() - 12)
                cheight = rng.randint(38, 70)
                cwidth = rng.randint(8, 16)
                # Generate multiple arms at different heights
                n_arms = rng.randint(1, 3)
                arms = []
                for _ in range(n_arms):
                    # Arm vertical position (not too close to top/bottom)
                    arm_y_offset = rng.randint(int(cheight * 0.25), int(cheight * 0.75))
                    arm_y = base_y - arm_y_offset
                    arm_height = rng.randint(14, 22)
                    arm_side = rng.choice([-1, 1])
                    arms.append((arm_y, arm_height, arm_side))
                cacti.append((cx, base_y, cheight, cwidth, arms))
            self._desert_cacti = cacti
            self._desert_cacti_width = self.width()
            self._desert_cacti_height = self.height()
        cactus_color = QColor(5, 9, 5, 255)
        painter.setBrush(cactus_color)
        for cx, base_y, cheight, cwidth, arms in self._desert_cacti:
            # Main trunk
            painter.drawRect(cx, base_y - cheight, cwidth, cheight)
            # Top curve (ellipse)
            painter.drawEllipse(cx, base_y - cheight - 4, cwidth, 8)
            # Arms at different heights
            for arm_y, arm_height, arm_side in arms:
                # Arm base x position (left or right side)
                if arm_side == -1:
                    arm_x = cx - 4
                else:
                    arm_x = cx + cwidth - 1
                # Draw arm vertical part
                painter.drawRect(arm_x, arm_y, 6, arm_height)
                # Arm curve at end
                painter.drawEllipse(arm_x - 2, arm_y + arm_height - 4, 10, 8)

        # Optionally, draw a few rocks (small ellipses)
        if not hasattr(self, "_desert_rocks") or self._desert_rocks is None or self.width() != getattr(self, "_desert_rocks_width", None) or self.height() != getattr(self, "_desert_rocks_height", None):
            rng = random.Random(self.width() * 10000 + self.height())
            rocks = []
            n_rocks = rng.randint(8, 16)
            for _ in range(n_rocks):
                rx = rng.randint(0, self.width())
                ry = ground_y + rng.randint(0, self.height() - ground_y - 10)
                rwidth = rng.randint(10, 22)
                rheight = rng.randint(6, 14)
                rocks.append((rx, ry, rwidth, rheight))
            self._desert_rocks = rocks
            self._desert_rocks_width = self.width()
            self._desert_rocks_height = self.height()
        rock_color = QColor(0, 0, 0, 210)
        painter.setBrush(rock_color)
        for rx, ry, rwidth, rheight in self._desert_rocks:
            painter.drawEllipse(rx, ry, rwidth, rheight)
