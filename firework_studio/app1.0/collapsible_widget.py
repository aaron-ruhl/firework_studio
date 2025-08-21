from PyQt6.QtWidgets import QWidget, QToolButton, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QSize


class CollapsibleWidget(QWidget):
    def __init__(self, title, child_widget, parent=None):
        super().__init__(parent)
        self.toggle_btn = QToolButton(text=title)
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(True)
        self.toggle_btn.setArrowType(Qt.ArrowType.DownArrow)
        self.toggle_btn.setStyleSheet("""
            QToolButton {
            background: #23242b;
            color: #ffd700;
            border: 1px solid #444657;
            border-radius: 4px;
            font-size: 13px;
            min-height: 28px;
            padding: 2px 8px;
            }
            QToolButton:checked {
            background: #31323a;
            color: #ffd700;
            }
        """)
        # Set maximum size policy so widget can shrink properly
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.child_widget = child_widget
        self.child_widget.setVisible(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toggle_btn)
        layout.addWidget(self.child_widget)
        self.toggle_btn.toggled.connect(self.toggle_child)
        self.toggle_btn.toggled.connect(self.update_arrow)
        self.update_arrow(self.toggle_btn.isChecked())

    def toggle_child(self, checked):
        self.child_widget.setVisible(checked)
        # Immediately update geometry to trigger layout recalculation
        self.updateGeometry()
        # Force the main window to adjust its layout, but do NOT resize the window
        main_window = self.window()
        if main_window:
            # Only update geometry/layout, do not call resize or setGeometry
            main_window.updateGeometry()
            central_widget = main_window.centralWidget()
            if central_widget:
                layout = central_widget.layout()
            if layout:
                layout.invalidate()
                layout.activate()

    def update_arrow(self, checked):
        self.toggle_btn.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
    
    def sizeHint(self) -> QSize:
        if self.child_widget.isVisible():
            return super().sizeHint()
        else:
            # When collapsed, only account for the button height
            button_height = self.toggle_btn.sizeHint().height()
            return QSize(super().sizeHint().width(), button_height)
    
    def hasHeightForWidth(self) -> bool:
        return False
    
    def heightForWidth(self, width: int) -> int:
        if self.child_widget.isVisible():
            return super().sizeHint().height()
        else:
            return self.toggle_btn.sizeHint().height()

    def minimumSizeHint(self) -> QSize:
        # Expanded: include child_widget minimum size
        if self.toggle_btn.isChecked() and self.child_widget.isVisible():
            btn_min = self.toggle_btn.minimumSizeHint()
            child_min = self.child_widget.minimumSizeHint()
            return QSize(
                max(btn_min.width(), child_min.width()),
                btn_min.height() + child_min.height()
            )
        else:
            # Collapsed: only show button
            btn_min = self.toggle_btn.minimumSizeHint()
            return QSize(btn_min.width(), btn_min.height())
