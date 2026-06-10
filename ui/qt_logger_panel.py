# ui/qt_logger_panel.py
# Logger panel không còn fixed height — nằm trong QSplitter nên user tự kéo.

from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QSizePolicy
from PyQt6.QtGui     import QColor, QFont
from PyQt6.QtCore    import Qt


_LOG_COLORS = {
    "[ALERT]":    QColor(255, 107, 107),
    "[SYSTEM]":   QColor(29,  209, 161),
    "[DISPATCH]": QColor(254, 202, 87),
    "[STATION]":  QColor(72,  219, 251),
    "[TRAFFIC]":  QColor(255, 165,   0),
    "[ERROR]":    QColor(255,  80,  80),
    "[RE-PLAN]":  QColor(200, 150, 255),
}
_DEFAULT_COLOR = QColor(189, 195, 199)

_LOGGER_STYLE = """
    QListWidget {
        background-color: #1C2833;
        border: none;
        padding: 4px;
        font-family: "Consolas", "Courier New", monospace;
        font-size: 8pt;
    }
    QScrollBar:vertical {
        width: 6px;
        background: #1C2833;
    }
    QScrollBar::handle:vertical {
        background: #4A5568;
        border-radius: 3px;
        min-height: 20px;
    }
    QScrollBar::handle:vertical:hover {
        background: #718096;
    }
    QListWidget::item:hover {
        background: transparent;
    }
"""


class QtLoggerPanel(QListWidget):
    """Color-coded event log.

    Không còn setMaximumHeight — kích thước do QSplitter cha quản lý.
    """

    MAX_LOGS = 50   # Tăng lên 50 vì panel có thể được kéo to hơn

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(60)   # Không collapse hoàn toàn
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setFont(QFont("Consolas", 8))
        self.setStyleSheet(_LOGGER_STYLE)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def add_log(self, message: str):
        color = _DEFAULT_COLOR
        for kw, kc in _LOG_COLORS.items():
            if kw in message:
                color = kc
                break

        item = QListWidgetItem(message)
        item.setForeground(color)
        self.addItem(item)

        if self.count() > self.MAX_LOGS:
            self.takeItem(0)

        self.scrollToBottom()
