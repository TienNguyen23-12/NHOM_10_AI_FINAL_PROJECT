# ui/theme.py
# Centralized QSS stylesheet cho toàn bộ app.
# Gọi apply(app) một lần từ main.py — không dùng inline stylesheet trong widget.

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui     import QPalette, QColor

# ── Color tokens ─────────────────────────────────────────────────────
C = {
    "bg":           "#F4F6F9",   # Nền app (xám sáng)
    "surface":      "#FFFFFF",   # Panels, cards
    "surface2":     "#F8F9FB",   # Inspector, subtle panels
    "dark":         "#2C3E50",   # Header, sidebar title
    "dark2":        "#34495E",   # Section headers
    "accent":       "#3498DB",   # Hover, active border
    "accent_dk":    "#2980B9",   # Pressed
    "success":      "#27AE60",   # Checked/active button
    "success_dk":   "#1E8449",   # Pressed success
    "warning":      "#F39C12",   # Rush hour active
    "danger":       "#E74C3C",   # Danger / clear / error
    "danger_dk":    "#C0392B",
    "neutral":      "#6C7A89",   # Default button
    "neutral_dk":   "#566573",
    "border":       "#D5DBDB",   # Subtle borders
    "border_focus": "#3498DB",   # Focus ring
    "text":         "#2C3E50",
    "text_muted":   "#717D7E",
    "text_inv":     "#FFFFFF",   # Text on dark bg
    "text_title":   "#F1C40F",   # Yellow title on dark bg
    "log_bg":       "#1C2833",   # Logger background
    "log_border":   "#2E4057",
    "scrollbar":    "#AEB6BF",
    "splitter":     "#D5DBDB",
    "splitter_hov": "#3498DB",
}


# ── Main QSS ─────────────────────────────────────────────────────────

_QSS = """
/* ── Global reset ───────────────────────────────────────────────── */
QWidget {{
    background-color: {bg};
    color: {text};
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 9pt;
}}

/* ── Main Window ─────────────────────────────────────────────────── */
QMainWindow {{
    background-color: {dark};
}}

/* ── Stacked / inner pages ───────────────────────────────────────── */
QStackedWidget > QWidget {{
    background-color: {bg};
}}

/* ── Buttons ─────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {neutral};
    color: {text_inv};
    border: none;
    border-radius: 5px;
    padding: 5px 10px;
    font-weight: 600;
    font-size: 8.5pt;
    text-align: left;
}}
QPushButton:hover {{
    background-color: {accent};
}}
QPushButton:pressed {{
    background-color: {accent_dk};
}}
QPushButton:checked {{
    background-color: {success};
}}
QPushButton:checked:hover {{
    background-color: {success_dk};
}}
QPushButton:disabled {{
    background-color: #B2BEC3;
    color: #DFE6E9;
}}

/* Danger variant — aplicado via setProperty('danger', True) */
QPushButton[danger="true"] {{
    background-color: {danger};
}}
QPushButton[danger="true"]:hover {{
    background-color: {danger_dk};
}}

/* Center-aligned variant (menu buttons) */
QPushButton[center="true"] {{
    text-align: center;
    padding: 10px 20px;
    font-size: 10.5pt;
    border: 2px solid {neutral};
    background-color: {dark2};
}}
QPushButton[center="true"]:hover {{
    background-color: {accent};
    border-color: {accent};
}}

/* ── Labels ──────────────────────────────────────────────────────── */
QLabel {{
    background: transparent;
    color: {text};
}}
QLabel[title="true"] {{
    color: {text_title};
    font-size: 16pt;
    font-weight: bold;
}}
QLabel[subtitle="true"] {{
    color: #AAB7B8;
    font-size: 9pt;
}}
QLabel[section="true"] {{
    color: {dark};
    font-weight: bold;
    font-size: 8.5pt;
    padding-top: 4px;
}}
QLabel[status="true"] {{
    background-color: {dark};
    color: #BDC3C7;
    padding: 4px 10px;
    font-size: 8pt;
}}

/* ── Separators ──────────────────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {border};
    background-color: {border};
    max-height: 1px;
    max-width: 1px;
    border: none;
}}

/* ── QSplitter ───────────────────────────────────────────────────── */
QSplitter::handle {{
    background-color: {splitter};
}}
QSplitter::handle:horizontal {{
    width: 5px;
    background-color: {splitter};
    border-left:  2px solid {bg};
    border-right: 2px solid {bg};
}}
QSplitter::handle:vertical {{
    height: 5px;
    background-color: {splitter};
    border-top:    2px solid {bg};
    border-bottom: 2px solid {bg};
}}
QSplitter::handle:hover, QSplitter::handle:pressed {{
    background-color: {splitter_hov};
}}

/* ── Scroll Bars ─────────────────────────────────────────────────── */
QScrollBar:vertical {{
    width: 8px;
    background: transparent;
    margin: 0;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {scrollbar};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {accent};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    height: 8px;
    background: transparent;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {scrollbar};
    border-radius: 4px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {accent};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ── Scroll Area ─────────────────────────────────────────────────── */
QScrollArea {{
    border: none;
    background: {surface};
}}
QScrollArea > QWidget > QWidget {{
    background: {surface};
}}

/* ── List Widget (Inspector, Logger) ─────────────────────────────── */
QListWidget {{
    background: {surface2};
    border: 1px solid {border};
    border-radius: 5px;
    outline: none;
    padding: 2px;
}}
QListWidget::item {{
    padding: 1px 4px;
    border-radius: 3px;
}}
QListWidget::item:hover {{
    background-color: #EBF5FB;
}}
QListWidget::item:selected {{
    background-color: #D6EAF8;
    color: {text};
}}

/* ── Dialog ──────────────────────────────────────────────────────── */
QDialog {{
    background: {surface};
}}

/* ── SpinBox ─────────────────────────────────────────────────────── */
QSpinBox {{
    background: {surface};
    border: 2px solid {border};
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 13pt;
    font-weight: bold;
    color: {text};
}}
QSpinBox:focus {{
    border-color: {accent};
}}
QSpinBox::up-button, QSpinBox::down-button {{
    width: 22px;
    border: none;
    background: {neutral};
    border-radius: 3px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background: {accent};
}}
QSpinBox::up-arrow {{
    image: none;
}}
QSpinBox::down-arrow {{
    image: none;
}}

/* ── ToolTip ─────────────────────────────────────────────────────── */
QToolTip {{
    background-color: {dark};
    color: {text_inv};
    border: 1px solid {dark2};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 8pt;
}}

/* ── MessageBox ──────────────────────────────────────────────────── */
QMessageBox {{
    background: {surface};
}}
QMessageBox QPushButton {{
    min-width: 70px;
    text-align: center;
    padding: 5px 16px;
}}
""".format(**C)


def apply(app: QApplication) -> None:
    """Áp dụng global stylesheet và Fusion palette cho app."""
    app.setStyle("Fusion")
    app.setStyleSheet(_QSS)

    # Palette supplement — đảm bảo màu consistent trên mọi platform
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(C["bg"]))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(C["text"]))
    palette.setColor(QPalette.ColorRole.Base,            QColor(C["surface"]))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(C["surface2"]))
    palette.setColor(QPalette.ColorRole.Text,            QColor(C["text"]))
    palette.setColor(QPalette.ColorRole.Button,          QColor(C["neutral"]))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(C["text_inv"]))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(C["accent"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(C["text_inv"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase,     QColor(C["dark"]))
    palette.setColor(QPalette.ColorRole.ToolTipText,     QColor(C["text_inv"]))
    app.setPalette(palette)
