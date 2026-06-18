# ui/hospital_dialog.py
# Dialog đặt số xe cho bệnh viện mới — modern clean design.
# Enter key → confirm; Escape → cancel; SpinBox validation tự động.

import qtawesome as qta

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QPushButton, QFrame, QWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui  import QFont, QColor


class HospitalDialog(QDialog):
    """Modal dialog nhập số xe ban đầu cho bệnh viện."""

    def __init__(self, parent=None, initial_value: int = 3, edit_mode: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Edit Hospital" if edit_mode else "Setup Hospital")
        self.setFixedSize(380, 310)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint)
        self.setModal(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("QDialog { background: #FFFFFF; border-radius: 12px; }")

        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Header navy ──────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(90)
        header.setStyleSheet(
            "background-color: #16263F;"
            "border-radius: 0px;"
        )
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(20, 14, 20, 14)
        h_layout.setSpacing(4)

        icon_row = QHBoxLayout()
        icon_row.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            qta.icon("fa5s.hospital", color="#E74C3C").pixmap(QSize(26, 26))
        )
        icon_lbl.setStyleSheet("background: transparent;")

        title_text = "EDIT HOSPITAL" if edit_mode else "SETUP HOSPITAL"
        title_lbl = QLabel(title_text)
        title_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #FFFFFF; background: transparent; letter-spacing: 1px;")

        icon_row.addWidget(icon_lbl)
        icon_row.addWidget(title_lbl)
        icon_row.addStretch()
        h_layout.addLayout(icon_row)

        sub_text = "Adjust ambulance fleet size for this station" if edit_mode else "Configure initial ambulance fleet for this station"
        sub_lbl = QLabel(sub_text)
        sub_lbl.setFont(QFont("Segoe UI", 8))
        sub_lbl.setStyleSheet("color: #8FA8C8; background: transparent;")
        h_layout.addWidget(sub_lbl)

        root.addWidget(header)

        # ── Body ─────────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("background: #FFFFFF;")
        body.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(28, 24, 28, 20)
        body_layout.setSpacing(16)

        prompt = QLabel("How many ambulances for this station?")
        prompt.setFont(QFont("Segoe UI", 9))
        prompt.setStyleSheet("color: #2C3E50; background: transparent;")
        prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_layout.addWidget(prompt)

        spin_row = QHBoxLayout()
        spin_row.setSpacing(12)

        self.btn_minus = QPushButton()
        self.btn_minus.setIcon(qta.icon("fa5s.minus", color="#FFFFFF"))
        self.btn_minus.setIconSize(QSize(14, 14))
        self.btn_minus.setFixedSize(44, 44)
        self.btn_minus.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_minus.setStyleSheet(self._stepper_style("#3498DB", "#2980B9"))
        self.btn_minus.setToolTip("Decrease")

        self.spin = QSpinBox()
        self.spin.setRange(1, 9)
        self.spin.setValue(initial_value)
        self.spin.setFixedSize(100, 52)
        self.spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin.setStyleSheet(
            "QSpinBox {"
            "  background: #F4F6F9;"
            "  border: 2px solid #D5DBDB;"
            "  border-radius: 10px;"
            "  color: #16263F;"
            "  padding: 0px;"
            "}"
            "QSpinBox:focus {"
            "  border-color: #3498DB;"
            "  background: #EBF5FB;"
            "}"
        )

        self.btn_plus = QPushButton()
        self.btn_plus.setIcon(qta.icon("fa5s.plus", color="#FFFFFF"))
        self.btn_plus.setIconSize(QSize(14, 14))
        self.btn_plus.setFixedSize(44, 44)
        self.btn_plus.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_plus.setStyleSheet(self._stepper_style("#3498DB", "#2980B9"))
        self.btn_plus.setToolTip("Increase")

        spin_row.addStretch()
        spin_row.addWidget(self.btn_minus)
        spin_row.addWidget(self.spin)
        spin_row.addWidget(self.btn_plus)
        spin_row.addStretch()
        body_layout.addLayout(spin_row)

        range_lbl = QLabel("Range: 1 – 9 vehicles")
        range_lbl.setFont(QFont("Segoe UI", 7))
        range_lbl.setStyleSheet("color: #AEB6BF; background: transparent;")
        range_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_layout.addWidget(range_lbl)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #EAECEE; background: #EAECEE; max-height: 1px;")
        body_layout.addWidget(divider)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_cancel = QPushButton("  Cancel")
        self.btn_cancel.setIcon(qta.icon("fa5s.times", color="#FFFFFF"))
        self.btn_cancel.setIconSize(QSize(13, 13))
        self.btn_cancel.setFixedHeight(40)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setStyleSheet(self._action_style("#6C7A89", "#566573"))

        confirm_text = "  Update" if edit_mode else "  Confirm"
        self.btn_confirm = QPushButton(confirm_text)
        self.btn_confirm.setIcon(qta.icon("fa5s.check", color="#FFFFFF"))
        self.btn_confirm.setIconSize(QSize(13, 13))
        self.btn_confirm.setFixedHeight(40)
        self.btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirm.setStyleSheet(self._action_style("#27AE60", "#1E8449"))

        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_confirm)
        body_layout.addLayout(btn_row)

        root.addWidget(body)

        self.btn_minus.clicked.connect(self._decrement)
        self.btn_plus.clicked.connect(self._increment)
        self.btn_confirm.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        self.spin.selectAll()
        self.spin.setFocus()

    # ── Helpers ───────────────────────────────────────────────────────

    def _stepper_style(self, base: str, pressed: str) -> str:
        return (
            f"QPushButton {{"
            f"  background-color: {base};"
            f"  border: none;"
            f"  border-radius: 22px;"
            f"  padding: 0px;"
            f"  text-align: center;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {pressed};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {pressed};"
            f"}}"
        )

    def _action_style(self, base: str, pressed: str) -> str:
        return (
            f"QPushButton {{"
            f"  background-color: {base};"
            f"  color: #FFFFFF;"
            f"  border: none;"
            f"  border-radius: 8px;"
            f"  padding: 0px 18px;"
            f"  font-size: 9pt;"
            f"  font-weight: 600;"
            f"  text-align: center;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {pressed};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {pressed};"
            f"}}"
        )

    def _increment(self):
        self.spin.setValue(min(self.spin.value() + 1, self.spin.maximum()))

    def _decrement(self):
        self.spin.setValue(max(self.spin.value() - 1, self.spin.minimum()))

    @property
    def car_count(self) -> int:
        return self.spin.value()
