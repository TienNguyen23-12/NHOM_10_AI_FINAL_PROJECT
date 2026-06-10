# ui/menu_page.py
# Màn hình Menu: title + 2 nút chọn chế độ bản đồ.
# Style lấy từ global theme (theme.py), không dùng inline stylesheet.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
)
from PyQt6.QtGui  import QFont, QColor, QPalette
from PyQt6.QtCore import Qt, pyqtSignal


class MenuPage(QWidget):
    """Màn hình khởi động."""

    sandbox_selected = pyqtSignal()
    default_selected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Nền tối — override palette cục bộ cho page này
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#2C3E50"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)

        layout.addSpacerItem(QSpacerItem(
            0, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # ── Title ─────────────────────────────────────────────────
        title = QLabel("MULTI-AGENT EMERGENCY DISPATCH SYSTEM")
        title.setProperty("title", True)   # theme.py: QLabel[title="true"]
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("HCMUTE  —  Final AI Project  (A* + Q-Learning / LRTA* + Q-Learning)")
        subtitle.setProperty("subtitle", True)
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacerItem(QSpacerItem(
            0, 36, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # ── Buttons ────────────────────────────────────────────────
        for text, signal in [
            ("1.   Custom Map Sandbox Layout",        self.sandbox_selected),
            ("2.   Generate Random Topology Map",     self.default_selected),
        ]:
            btn = QPushButton(text)
            btn.setProperty("center", True)   # theme.py: center-aligned style
            btn.setFont(QFont("Segoe UI", 11))
            btn.setFixedWidth(420)
            btn.setFixedHeight(52)
            btn.clicked.connect(signal)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            layout.addSpacing(12)

        layout.addSpacerItem(QSpacerItem(
            0, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Hint
        hint = QLabel("F11 — Fullscreen  |  ESC — Thoát")
        hint.setFont(QFont("Segoe UI", 8))
        hint.setStyleSheet("color: #5D6D7E;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)
        layout.addSpacing(12)
