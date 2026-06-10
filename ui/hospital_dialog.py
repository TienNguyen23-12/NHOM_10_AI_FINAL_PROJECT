# ui/hospital_dialog.py
# Dialog đặt số xe cho bệnh viện mới.
# Enter key → confirm; Escape → cancel; SpinBox validation tự động.

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QPushButton, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QFont, QKeySequence, QShortcut


class HospitalDialog(QDialog):
    """Modal dialog nhập số xe ban đầu cho bệnh viện.

    - SpinBox giới hạn 1–9 (không cần validate thêm)
    - Enter → accept, Escape → reject (Qt default)
    - Tái sử dụng lại QDialogButtonBox thay vì hand-draw buttons
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Setup Hospital")
        self.setFixedSize(300, 180)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 18, 24, 18)

        # ── Title ─────────────────────────────────────────────────
        title = QLabel("INITIAL FLEET COUNT")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2C3E50; padding-bottom: 2px;")
        layout.addWidget(title)

        sub = QLabel("Nhập số xe cứu thương ban đầu cho trạm này:")
        sub.setFont(QFont("Segoe UI", 8))
        sub.setStyleSheet("color: #717D7E;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)
        layout.addWidget(sub)

        # ── SpinBox ────────────────────────────────────────────────
        self.spin = QSpinBox()
        self.spin.setRange(1, 9)
        self.spin.setValue(3)
        self.spin.setFixedHeight(44)
        self.spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        # SpinBox style đã được handle bởi global theme
        layout.addWidget(self.spin)

        # ── Buttons (dùng QDialogButtonBox cho Enter/Esc chuẩn) ───
        box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        box.button(QDialogButtonBox.StandardButton.Ok).setText("CONFIRM")
        box.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        layout.addWidget(box)

        # Auto-focus spinbox để user có thể gõ số ngay
        self.spin.selectAll()
        self.spin.setFocus()

    @property
    def car_count(self) -> int:
        return self.spin.value()
