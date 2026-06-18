# ui/qt_inspector_panel.py
# AI Monitor panel — QListWidget hiển thị Q-table / H-table / routes.
# Hover trên dòng → emit highlight_cells_changed để GridCanvas tô sáng ô.

from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QSizePolicy
from PyQt6.QtGui     import QColor, QFont
from PyQt6.QtCore    import Qt, pyqtSignal


_HEADER_COLOR = QColor(44, 62, 80)
_NORMAL_COLOR = QColor(86, 101, 115)
_INDENT_COLOR = QColor(127, 140, 141)


class QtInspectorPanel(QListWidget):
    """Hiển thị Q-table / H-table / routes.
    Hover trên dòng phát highlight_cells_changed(cells) để GridCanvas tô sáng.
    """

    highlight_cells_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setFont(QFont("Consolas", 8))
        self.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMouseTracking(True)
        self._highlight_data: list[list] = []
        self._show_welcome()

    def _show_welcome(self):
        self.clear()
        self._highlight_data = []
        for line in [
            "Click any inspection button",
            "above to stream live AI metrics.",
            "",
            "Shortcuts:",
            "  Q  — Q-Table",
            "  H  — H-Table",
            "  Ctrl+R — Routes",
        ]:
            self._add_item(line, [], is_header=line.endswith(":"))

    # ── Public API ────────────────────────────────────────────────

    def load_items(self, items: list[tuple[str, list]]):
        """Load list of (text, cells) pairs. cells is list of (row,col) tuples."""
        self.highlight_cells_changed.emit([])
        self.clear()
        self._highlight_data = []
        for text, cells in items:
            is_header = (text.startswith("---") or
                         text.startswith("[Agent") or
                         text.startswith("Car #") or
                         text.startswith("━━━"))
            self._add_item(text, cells, is_header)

    def load_lines(self, lines: list[str]):
        """Backwards-compat wrapper — no highlight data."""
        self.load_items([(line, []) for line in lines])

    # ── Internal helpers ──────────────────────────────────────────

    def _add_item(self, text: str, cells: list, is_header: bool):
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, cells)
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
        self._highlight_data.append(cells)

    # ── Mouse events ──────────────────────────────────────────────

    def mouseMoveEvent(self, event):
        item = self.itemAt(event.pos())
        if item is not None:
            cells = item.data(Qt.ItemDataRole.UserRole) or []
            self.highlight_cells_changed.emit(cells)
        else:
            self.highlight_cells_changed.emit([])
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.highlight_cells_changed.emit([])
        super().leaveEvent(event)
