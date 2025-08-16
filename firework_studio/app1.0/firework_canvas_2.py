from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt, QTimer
from OpenGL.GL import (
    glClearColor, glPointSize, glEnable, glBlendFunc, glClear, glLoadIdentity,
    glBegin, glColor3f, glVertex2f, glEnd, glViewport, glMatrixMode,
    glOrtho, GL_POINT_SMOOTH, GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
    GL_COLOR_BUFFER_BIT, GL_PROJECTION, GL_MODELVIEW, GL_POINTS, GL_QUADS
)
import random
from firework_2 import Firework  
from PyQt6.QtGui import QColor
class FireworksCanvas(QOpenGLWidget):

    def __init__(self):
        super().__init__()
        self.fireworks = []
        self.background_color = (0.05, 0.05, 0.1)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # ~60 FPS
        self.particle_count = 50
        self.firework_color = (1.0, 0.0, 0.0)
        self.background = "night"
        self.fired_times = set()
        self._fireworks_enabled = True
        self.delay = 2.0
        self.pattern = "circle"
        self._custom_bg_texture = None

    def choose_firework_pattern(self, pattern):
        self.pattern = pattern

    def add_firework(self, handle, x=None):
        margin = 40
        if len(self.fireworks) >= 20:
            self.particle_count = 5
        elif len(self.fireworks) >= 10:
            self.particle_count = 15
        else:
            self.particle_count = 50
        x = random.randint(margin, max(margin, self.width() - margin))
        color = getattr(handle, "firing_color", None)
        if isinstance(color, (tuple, list)) and len(color) == 3:
            # Use float RGB tuple (0.0-1.0) for explosion color
            explosion_color = QColor.fromRgbF(
                max(0.0, min(1.0, color[0])),
                max(0.0, min(1.0, color[1])),
                max(0.0, min(1.0, color[2]))
            )
        else:
            # Fallback to a random QColor for variety
            explosion_color = QColor.fromRgbF(
                random.uniform(0.0, 1.0),
                random.uniform(0.0, 1.0),
                random.uniform(0.0, 1.0)
            )
        firework = Firework(
            x, self.height(),
            explosion_color, handle.pattern,
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
        # Find preview_widget and current_time
        while parent:
            if parent.__class__.__name__ == "FireworkShowApp":
                preview_widget = getattr(parent, "preview_widget", None)
                break
            parent = parent.parentWidget()
        if preview_widget and hasattr(preview_widget, "current_time"):
            current_time = getattr(preview_widget, "current_time", 0)
        # Update fireworks
        self.fireworks = [fw for fw in self.fireworks if fw.update(current_time)]
        # Fire new fireworks if needed
        if preview_widget and getattr(preview_widget, "firework_times", None) is not None and self._fireworks_enabled:
            handles = getattr(preview_widget, "fireworks", [])
            ct = getattr(preview_widget, "current_time", 0)
            # Use exact handle.firing_time comparison to avoid zoom/scale issues
            to_fire = [
                handle for handle in handles
                if (
                    abs(ct - (handle.firing_time - self.delay)) < 0.017 and
                    (handle.firing_time, 0) not in self.fired_times
                )
            ]
            for handle in to_fire:
                for _ in range(handle.number_firings):
                    self.add_firework(handle)
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
        # Draw unexploded fireworks
        unexploded = [
            fw for fw in self.fireworks if not fw.exploded
        ]
        if unexploded:
            glBegin(GL_POINTS)
            for firework in unexploded:
                color = firework.color
                if isinstance(color, QColor):
                    color = color.getRgbF()[:3]
                elif isinstance(color, (tuple, list)) and max(color) > 1.0:
                    color = tuple(c / 255.0 for c in color)
                glColor3f(*color)
                glVertex2f(firework.x, firework.y)
            glEnd()

        # Draw particles (vectorized where possible)
        if self._fireworks_enabled:
            glBegin(GL_POINTS)
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
                    glColor3f(*color)
                    glVertex2f(px, py)
            glEnd()
        else:
            glBegin(GL_POINTS)
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
                    glColor3f(*color)
                    glVertex2f(px, py)
            glEnd()

    def load_custom_background(self, path=None):
        return None
