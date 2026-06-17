# main.py
import sys
import ctypes
import qtawesome as qta  # Import thư viện vẽ icon xe cấp cứu
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from ui.app_window import AppWindow
from ui import theme


def main():
    try:
        # --- BƯỚC 1: KHAI BÁO ID ỨNG DỤNG ĐỂ TASKBAR NHẬN DIỆN ---
        myappid = 'hcm-ute.ai.ambulance.group.10'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)

    # --- BƯỚC 2: LẤY LOGO XE CẤP CỨU MÀU ĐỎ GẮN LÀM ICON ---
    app.setWindowIcon(qta.icon("fa5s.ambulance", color="#E74C3C"))

    # Áp dụng global QSS theme + Fusion palette
    theme.apply(app)

    # Font mặc định toàn app
    app.setFont(QFont("Segoe UI", 9))

    window = AppWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()