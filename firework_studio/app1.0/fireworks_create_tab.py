from PyQt6.QtWidgets import QWidget, QScrollArea, QLabel, QVBoxLayout

class CreateTabHelper:
    def __init__(self, main_window):
        self.main_window = main_window
        self.create_tab_widget = QWidget()
        self.layout = QVBoxLayout(self.create_tab_widget)
        
        self.label = QLabel(
            "<b>Coming in 2.0:</b><br>"
            "This page will enable the user to get detailed information about all of the handles and allow much easier options for customization.<br>"
        )
        self.label.setWordWrap(True)
        self.label.setStyleSheet("font-size: 11px; color: #ffd700; padding: 2px 0;")
        self.layout.addWidget(self.label)

        