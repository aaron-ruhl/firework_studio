from PyQt6.QtWidgets import QWidget, QScrollArea,

class CreateTabHelper:
    def __init__(self, main_window):
        self.main_window = main_window
        self.create_tab_widget = QWidget()

        # Create a scroll area for the tab content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QWidget {
            background-color: #23242b;
            color: #ffd700;
            font-size: 15px;
            font-family: 'Segoe UI', 'Arial', sans-serif;
            }
            QGroupBox {
            background-color: #181a20;
            border: 2px solid #ffd700;
            border-radius: 8px;
            color: #ffd700;
            font-size: 16px;
            font-weight: bold;
            margin-top: 12px;
            margin-bottom: 12px;
            padding: 8px 12px;
            }
            QGroupBox:title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            color: #ffd700;
            font-size: 16px;
            font-weight: bold;
            }
            QLabel {
            color: #ffd700;
            font-size: 15px;
            font-weight: 500;
            padding: 4px 0;
            }
            QComboBox, QSpinBox {
            background-color: #23242b;
            color: #ffd700;
            border: 2px solid #ffd700;
            border-radius: 6px;
            font-size: 15px;
            font-weight: bold;
            min-width: 60px;
            min-height: 32px;
            padding: 4px 12px;
            margin: 4px 0;
            }
            QPushButton {
            background-color: #ffd700;
            color: #23242b;
            border: 2px solid #ffd700;
            border-radius: 6px;
            font-size: 15px;
            font-weight: bold;
            min-width: 80px;
            min-height: 32px;
            margin: 6px 0;
            }
            QPushButton:hover {
            background-color: #fffbe6;
            color: #23242b;
            border: 2px solid #ffd700;
            }
            QMenu {
            background-color: #23242b;
            color: #ffd700;
            border: 2px solid #ffd700;
            border-radius: 8px;
            font-size: 15px;
            padding: 8px 0px;
            }
            QTabWidget::pane {
            border: 2px solid #ffd700;
            background: #23242b;
            }
            QTabBar::tab {
            background: #181a20;
            color: #ffd700;
            border: 2px solid #ffd700;
            border-radius: 6px;
            min-width: 140px;
            min-height: 36px;
            font-size: 15px;
            font-weight: bold;
            margin: 4px;
            }
            QTabBar::tab:selected {
            background: #ffd700;
            color: #23242b;
            border: 2px solid #ffd700;
            }
            QTabBar::tab:hover {
            background-color: #fffbe6;
            color: #23242b;
            }
        """)

        