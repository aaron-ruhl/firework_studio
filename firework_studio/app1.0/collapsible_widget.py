from PyQt6.QtWidgets import QWidget, QToolButton, QVBoxLayout, QSizePolicy, QMainWindow, QApplication
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal


class CollapsibleWidget(QWidget):
    # Signal emitted when the widget's collapsed state changes
    collapsed_changed = pyqtSignal(bool)  # True when collapsed, False when expanded
    
    def __init__(self, title, child_widget, parent=None):
        super().__init__(parent)
        self.toggle_btn = QToolButton()
        self.toggle_btn.setText(title)
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
        
        # Store original size information
        self.child_widget = child_widget
        self.child_widget.setVisible(True)
        self._is_collapsed = False
        
        # Set initial size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toggle_btn)
        layout.addWidget(self.child_widget)
        
        self.toggle_btn.toggled.connect(self.toggle_child)
        self.toggle_btn.toggled.connect(self.update_arrow)
        self.update_arrow(self.toggle_btn.isChecked())

    def toggle_child(self, checked):
        """Toggle the visibility of the child widget with proper layout management"""
        # Store the current main window for reference
        main_window = self.window()
        
        # Toggle the child widget visibility
        self.child_widget.setVisible(checked)
        self._is_collapsed = not checked
        
        # Emit signal about state change
        self.collapsed_changed.emit(self._is_collapsed)
        
        # Update size policy based on state
        if checked:
            # When expanded, use Preferred policy
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        else:
            # When collapsed, use Minimum policy to take only needed space
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        # Force geometry updates from this widget up the hierarchy
        self.updateGeometry()
        
        # Update parent layouts systematically
        current_widget = self.parentWidget()
        while current_widget:
            layout = current_widget.layout()
            if layout:
                layout.invalidate()
                layout.activate()
            current_widget.updateGeometry()
            
            # If we've reached the main window, also update its central widget
            if isinstance(current_widget, QMainWindow):
                central_widget = current_widget.centralWidget()
                if central_widget:
                    central_layout = central_widget.layout()
                    if central_layout:
                        central_layout.invalidate()
                        central_layout.activate()
                    central_widget.updateGeometry()
                break
            
            current_widget = current_widget.parentWidget()
        
        # Schedule a delayed update for final adjustments
        QTimer.singleShot(10, lambda: self._delayed_update(main_window))
    
    def _delayed_update(self, main_window=None):
        """Delayed update to ensure proper layout recalculation"""
        # Force a final geometry update on self and parents
        self.updateGeometry()
        
        # Find the main window if not provided
        if main_window is None:
            main_window = self.window()
            
        if main_window and isinstance(main_window, QMainWindow):
            # Update the main window's geometry calculation
            main_window.updateGeometry()
            
            # Force the central widget to recalculate its layout
            central_widget = main_window.centralWidget()
            if central_widget:
                central_widget.updateGeometry()
                layout = central_widget.layout()
                if layout:
                    layout.invalidate()
                    layout.activate()

    def update_arrow(self, checked):
        self.toggle_btn.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
    
    def sizeHint(self) -> QSize:
        if self.child_widget.isVisible():
            # When expanded, return a reasonable size that won't cause window issues
            btn_hint = self.toggle_btn.sizeHint()
            child_hint = self.child_widget.sizeHint()
            
            # Cap the total height to prevent window sizing issues
            max_total_height = 600  # Reasonable maximum total height
            total_height = btn_hint.height() + child_hint.height()
            capped_height = min(total_height, max_total_height)
            
            return QSize(max(btn_hint.width(), child_hint.width()), capped_height)
        else:
            # When collapsed, only account for the button height
            return self.toggle_btn.sizeHint()
    
    def hasHeightForWidth(self) -> bool:
        return False
    
    def minimumSizeHint(self) -> QSize:
        # Always return a reasonable minimum size to prevent geometry issues
        btn_min = self.toggle_btn.minimumSizeHint()
        
        if self.child_widget.isVisible():
            # When expanded, add some space for child but cap it at reasonable height
            child_min = self.child_widget.minimumSizeHint()
            # Cap the minimum height to prevent excessive window sizing - be more conservative
            max_reasonable_height = 200  # Much more conservative maximum for minimum height
            total_height = btn_min.height() + min(child_min.height(), max_reasonable_height)
            return QSize(max(btn_min.width(), child_min.width()), total_height)
        else:
            # When collapsed, only return the button's minimum size
            return QSize(btn_min.width(), btn_min.height())
        
    def heightForWidth(self, width: int) -> int:
        if self.child_widget.isVisible():
            return super().sizeHint().height()
        else:
            return self.toggle_btn.sizeHint().height()
