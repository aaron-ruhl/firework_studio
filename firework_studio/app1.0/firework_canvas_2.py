from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import QTimer
from OpenGL.GL import (
    glClearColor, glPointSize, glEnable, glBlendFunc, glClear, glLoadIdentity,
    glBegin, glColor3f, glVertex2f, glEnd, glViewport, glMatrixMode,
    glOrtho, GL_POINT_SMOOTH, GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
    GL_COLOR_BUFFER_BIT, GL_PROJECTION, GL_MODELVIEW, GL_POINTS, GL_QUADS
)
import random
from firework_2 import Firework  
from PyQt6.QtGui import QColor
import numpy as np

class FireworksCanvas(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.fireworks = []
        self.background_color = (0.05, 0.05, 0.1)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # ~60 FPS
        self.particle_count = 50
        self.background = "night"
        self.fired_times = set()
        self._fireworks_enabled = True
        self.delay = 2.0
        self.pattern = "circle"
        self._custom_bg_texture = None

    def choose_firework_pattern(self, pattern):
        self.pattern = pattern

    def add_firework(self, handle, x=None):

        # Dynamically adjust particle count based on number of fireworks to avoid lag
        if len(self.fireworks) < 5:
            self.particle_count = 80
        elif len(self.fireworks) < 10:
            self.particle_count = 45
        else:
            self.particle_count = 25

        #keep fireworks from going off screen
        margin = 40
        x = random.randint(margin, max(margin, self.width() - margin))

        # create firework
        firework = Firework(
            x, self.height(),
            handle.explosion_color, handle.pattern,
            handle.display_number,
            self.particle_count,
            handle=handle,
            canvas_height=self.height()
        )
        self.fireworks.append(firework)

    def reset_fireworks(self):
        self.fireworks.clear()
        self.fired_times.clear()

    def set_background(self, background, path=None):
        self.background = background
        if background == "custom" and path:
            self._custom_bg_texture = self.load_custom_background(path)
        else:
            self._custom_bg_texture = None
        self.update()

    def reset_firings(self):
        self.fired_times.clear()

    def set_fireworks_enabled(self, enabled: bool):
        self._fireworks_enabled = enabled

    def update_animation(self):
        parent = self.parentWidget()
        preview_widget = None
        current_time = 0
        while parent:
            if parent.__class__.__name__ == "FireworkShowApp":
                preview_widget = getattr(parent, "preview_widget", None)
                break
            parent = parent.parentWidget()
        if preview_widget and hasattr(preview_widget, "current_time"):
            current_time = getattr(preview_widget, "current_time", 0)
        
        # Calculate dynamic fade multiplier based on number of fireworks
        num_fireworks = len(self.fireworks)
        if num_fireworks >= 15:
            fade_multiplier = 3.0  # Very fast fading for many fireworks
        elif num_fireworks >= 10:
            fade_multiplier = 2.5  # Fast fading
        elif num_fireworks >= 5:
            fade_multiplier = 2.0  # Moderate fading
        else:
            fade_multiplier = 1.0  # Normal fading
        
        # Apply fade multiplier to all particles
        for firework in self.fireworks:
            for particle in firework.particles:
                particle.set_dynamic_fade_multiplier(fade_multiplier)
        
        # Vectorized update for fireworks
        self.fireworks = [fw for fw in self.fireworks if fw.update(current_time)]
        # Fire new fireworks if needed (keep detection logic unchanged)
        if preview_widget and getattr(preview_widget, "firework_times", None) is not None and self._fireworks_enabled:
            handles = getattr(preview_widget, "fireworks", [])
            ct = getattr(preview_widget, "current_time", 0)
            to_fire = [
                handle for handle in handles
                if (
                    abs(ct - (handle.firing_time - self.delay)) < 0.017 and
                    (handle.firing_time, 0) not in self.fired_times
                )
            ]
            for handle in to_fire:
                for idx in range(handle.number_firings):
                    # Get pattern and color for this specific shot
                    shot_pattern = handle.pattern_list[idx] if idx < len(handle.pattern_list) else handle.pattern
                    
                    # Handle explosion color list safely
                    if hasattr(handle, 'explosion_color_list') and handle.explosion_color_list and idx < len(handle.explosion_color_list):
                        shot_color = handle.explosion_color_list[idx]
                    else:
                        shot_color = handle.explosion_color
                    
                    # Create a temporary handle-like object for this specific shot
                    # Don't modify the original handle to avoid side effects
                    temp_handle = type('TempHandle', (), {
                        'explosion_color': shot_color,
                        'pattern': shot_pattern,
                        'display_number': handle.display_number,
                        'firing_time': handle.firing_time,
                        'number_firings': 1  # Each shot is individual
                    })()
                    
                    self.add_firework(temp_handle)
                self.fired_times.add((handle.firing_time, 0))
        self.update()

    def initializeGL(self):
        glClearColor(*self.background_color, 1.0)
        glPointSize(3)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        self.draw_background()
        self.draw_fireworks()

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, w, h, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        
        # Don't update existing fireworks - let them maintain their current trajectory
        # Only new fireworks will use the updated canvas dimensions

    def draw_background(self):
        if self.background == "night":
            glBegin(GL_QUADS)
            glColor3f(0.05, 0.05, 0.1)
            glVertex2f(0, 0)
            glVertex2f(self.width(), 0)
            glColor3f(0.0, 0.0, 0.0)
            glVertex2f(self.width(), self.height())
            glVertex2f(0, self.height())
            glEnd()

    def draw_fireworks(self):
        # Draw unexploded fireworks (vectorized)
        unexploded = [fw for fw in self.fireworks if not fw.exploded]
        if unexploded:
            coords = np.array([[fw.x, fw.y] for fw in unexploded], dtype=np.float32)
            colors = []
            for firework in unexploded:
                color = firework.color
                if isinstance(color, QColor):
                    color = color.getRgbF()[:3]
                elif isinstance(color, (tuple, list)) and max(color) > 1.0:
                    color = tuple(c / 255.0 for c in color)
                colors.append(color)
            colors = np.array(colors, dtype=np.float32)
            glBegin(GL_POINTS)
            for i in range(len(coords)):
                glColor3f(*colors[i])
                glVertex2f(*coords[i])
            glEnd()

        # Draw particles (vectorized)
        if self._fireworks_enabled:
            particles = []
            colors = []
            for firework in self.fireworks:
                for particle in firework.particles:
                    particle.resume()
                    px, py = particle.x, particle.y
                    color = particle.get_color()
                    if isinstance(color, QColor):
                        color = color.getRgbF()[:3]
                    elif isinstance(color, (tuple, list)) and max(color) > 1.0:
                        color = tuple(c / 255.0 for c in color)
                    if not isinstance(color, (tuple, list)):
                        color = (1.0, 1.0, 1.0)
                    particles.append((px, py))
                    colors.append(color)
            if particles:
                particles = np.array(particles, dtype=np.float32)
                colors = np.array(colors, dtype=np.float32)
                glBegin(GL_POINTS)
                for i in range(len(particles)):
                    glColor3f(*colors[i])
                    glVertex2f(*particles[i])
                glEnd()
        else:
            particles = []
            colors = []
            for firework in self.fireworks:
                for particle in firework.particles:
                    particle.freeze()
                    px, py = particle.x, particle.y
                    color = particle.get_color()
                    if isinstance(color, QColor):
                        color = color.getRgbF()[:3]
                    elif isinstance(color, (tuple, list)) and max(color) > 1.0:
                        color = tuple(c / 255.0 for c in color)
                    if not isinstance(color, (tuple, list)):
                        color = (1.0, 1.0, 1.0)
                    particles.append((px, py))
                    colors.append(color)
            if particles:
                particles = np.array(particles, dtype=np.float32)
                colors = np.array(colors, dtype=np.float32)
                glBegin(GL_POINTS)
                for i in range(len(particles)):
                    glColor3f(*colors[i])
                    glVertex2f(*particles[i])
                glEnd()

    def load_custom_background(self, path=None):
        return None
