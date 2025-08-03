import sys
from PyQt6.QtWidgets import QApplication
from firework_show_app import FireworkShowApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FireworkShowApp()
    window.show()
    sys.exit(app.exec())