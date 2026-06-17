# ui/menu_page.py
# Màn hình Menu: branding xe cấp cứu + 2 nút chọn chế độ bản đồ.
# Style lấy từ global theme (theme.py), chỉ override màu nền tối cục bộ.

import qtawesome as qta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpacerItem, QSizePolicy, QFrame
)
from PyQt6.QtGui  import QFont
from PyQt6.QtCore import Qt, QSize, pyqtSignal


class MenuPage(QWidget):
    """Màn hình khởi động."""

    sandbox_selected = pyqtSignal()
    default_selected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Nền tối — QSS toàn cục đè palette, nên dùng objectName + rule trong theme.py.
        # QWidget subclass cần WA_StyledBackground để QSS background có hiệu lực.
        self.setObjectName("menuPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)

        layout.addSpacerItem(QSpacerItem(
            0, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # ── Logo xe cứu thương ────────────────────────────────────
        logo = QLabel()
        logo.setPixmap(
            qta.icon("fa5s.ambulance", color="#E74C3C").pixmap(QSize(88, 88)))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)
        layout.addSpacing(14)

        # ── Title ─────────────────────────────────────────────────
        title = QLabel("MULTI-AGENT EMERGENCY DISPATCH SYSTEM")
        title.setProperty("title", True)   # theme.py: QLabel[title="true"]
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(8)

        # Vạch đỏ khẩn cấp dưới title
        accent = QFrame()
        accent.setFixedSize(120, 4)
        accent.setStyleSheet(
            "background: #E74C3C; border-radius: 2px; border: none;")
        layout.addWidget(accent, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)

        subtitle = QLabel(
            "HCM-UTE  - Final AI Project  (A* + Q-Learning / LRTA* + Q-Learning)")
        subtitle.setProperty("subtitle", True)
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacerItem(QSpacerItem(
            0, 36, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # ── Buttons ────────────────────────────────────────────────
        for text, icon_name, signal in [
            ("Custom Map Sandbox Layout",    "fa5s.drafting-compass", self.sandbox_selected),
            ("Generate Random Topology Map", "fa5s.random",           self.default_selected),
        ]:
            btn = QPushButton("   " + text)
            btn.setProperty("center", True)   # theme.py: center-aligned style
            btn.setIcon(qta.icon(icon_name, color="white"))
            btn.setIconSize(QSize(20, 20))
            btn.setFont(QFont("Segoe UI", 11))
            btn.setFixedWidth(420)
            btn.setFixedHeight(52)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(signal)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            layout.addSpacing(12)

        layout.addSpacerItem(QSpacerItem(
            0, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Hint
        hint = QLabel("F11 - Fullscreen  |  ESC - Thoát")
        hint.setFont(QFont("Segoe UI", 8))
        hint.setStyleSheet("color: #5D6D7E;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)
        layout.addSpacing(12)
