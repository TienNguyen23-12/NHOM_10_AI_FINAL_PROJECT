# ui/qt_inspector_panel.py
# AI Monitor panel — QListWidget hiển thị Q-table / H-table / routes.
# Style từ global theme (light surface).

from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QSizePolicy
from PyQt6.QtGui     import QColor, QFont
from PyQt6.QtCore    import Qt


_HEADER_COLOR = QColor(44, 62, 80)
_NORMAL_COLOR = QColor(86, 101, 115)
_INDENT_COLOR = QColor(127, 140, 141)


class QtInspectorPanel(QListWidget):
    """Hiển thị Q-table / H-table / routes với font mono cho data alignment."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setFont(QFont("Consolas", 8))
        self.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._show_welcome()

    def _show_welcome(self):
        self.clear()
        for line in [
            "Click any inspection button",
            "above to stream live AI metrics.",
            "",
            "Shortcuts:",
            "  Q  — Q-Table",
            "  H  — H-Table",
            "  Ctrl+R — Routes",
        ]:
            self._add_line(line, is_header=line.endswith(":"))

    def load_lines(self, lines: list[str]):
        self.clear()
        for line in lines:
            is_header = (line.startswith("---") or
                         line.startswith("[Agent") or
                         line.startswith("Car #"))
            self._add_line(line, is_header)

    def _add_line(self, text: str, is_header: bool):
        item = QListWidgetItem(text)
        if is_header:
            item.setForeground(_HEADER_COLOR)
            f = self.font()
            f.setBold(True)
            item.setFont(f)
        elif text.startswith("  "):
            item.setForeground(_INDENT_COLOR)
        else:
            item.setForeground(_NORMAL_COLOR)
        self.addItem(item)
