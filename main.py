# main.py
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui     import QFont
from ui.app_window   import AppWindow
from ui              import theme

def main():
    app = QApplication(sys.argv)

    # Áp dụng global QSS theme + Fusion palette
    theme.apply(app)

    # Font mặc định toàn app
    app.setFont(QFont("Segoe UI", 9))

    window = AppWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()