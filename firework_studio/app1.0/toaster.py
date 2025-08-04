from PyQt6.QtCore import Qt, QPropertyAnimation
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel


class ToastDialog(QDialog):
    # ToastDialog: A frameless, styled dialog for displaying temporary toast notifications.
    """
    ToastDialog is a custom QDialog subclass that displays a temporary, styled notification ("toast") 
    in a PyQt application. Toasts are stacked vertically in the bottom-right corner of the parent window 
    and automatically manage their position to avoid overlap.
    Attributes:
        _active_toasts (list): Class-level list tracking currently active ToastDialog instances.
    Args:
        message (str): The message to display in the toast.
        parent (QWidget, optional): The parent widget for the dialog.
    Methods:
        show():
            Displays the toast dialog, stacking it with other visible toasts in the bottom-right 
            corner of the parent window.
        closeEvent(event):
            Handles the dialog close event and removes the toast from the active toasts list.
    """
    _active_toasts = []

    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setStyleSheet("""
            QDialog {
            background-color: rgb(40, 40, 40);
            border-radius: 14px;
            min-width: 320px;
            min-height: 80px;
            }
            QLabel {
            color: #fff;
            padding: 18px 32px;
            font-size: 20px;
            }
        """)
        layout = QVBoxLayout(self)
        label = QLabel(message)
        layout.addWidget(label)
        self.adjustSize()
        ToastDialog._active_toasts.append(self)

    def show(self):
        # Stack toasts vertically so they don't overlap
        parent = self.parentWidget()
        if parent:
            geo = parent.geometry()
            margin = 40
            spacing = 12
            width = self.width()
            height = self.height()
            # Only consider visible toasts
            visible_toasts = [t for t in ToastDialog._active_toasts if t.isVisible()]
            idx = len(visible_toasts)
            x = geo.x() + geo.width() - width - margin
            y = geo.y() + geo.height() - height - margin - (idx * (height + spacing))
            self.move(x, y)
            # Fade out the previous toast if any
            if visible_toasts:
                prev_toast = visible_toasts[-1]
                if prev_toast is not self:
                    # Use QPropertyAnimation for fade out
                    prev_toast.setWindowOpacity(1.0)
                    anim = QPropertyAnimation(prev_toast, b"windowOpacity")
                    anim.setDuration(350)
                    anim.setStartValue(1.0)
                    anim.setEndValue(0.0)
                    # Ensure the toast closes after fade
                    def close_prev():
                        prev_toast.close()
                        anim.deleteLater()
                    anim.finished.connect(close_prev)
                    anim.start()
                    prev_toast._fade_anim = anim  # Prevent garbage collection
        super().show()

    def closeEvent(self, event):
        if self in ToastDialog._active_toasts:
            ToastDialog._active_toasts.remove(self)
        super().closeEvent(event)
