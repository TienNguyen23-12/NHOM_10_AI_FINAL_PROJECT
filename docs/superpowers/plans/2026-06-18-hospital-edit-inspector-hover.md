# Hospital Edit + Inspector Hover Highlight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add (1) right-click on hospital cell → context menu → edit ambulance count dialog, and (2) hovering over rows in the Live AI Monitor highlights the corresponding cell(s) on the grid with a light overlay.

**Architecture:** Feature 1 intercepts right-click on `STATE_HOSPITAL` cells in `GridCanvas` before the normal pan handler, emits a new signal, and `SimulationPage` opens a modified `HospitalDialog` pre-filled with the current count. Feature 2 restructures the inspector data flow: controller `build_*` methods return `(text, cells)` pairs; `QtInspectorPanel` stores highlight data per row and emits a signal on hover; `GridCanvas` draws a light overlay from that signal.

**Tech Stack:** Python 3.9+, PyQt6, qtawesome

## Global Constraints

- PyQt6 only — no PyQt5 / PySide imports
- No new top-level files unless listed below
- All colors must use `QColor`, not string CSS inside `paintEvent`
- Overlay alpha must be ≤ 90 so existing grid content remains readable

---

## File Map

| File | Change |
|---|---|
| `ui/hospital_dialog.py` | Add `initial_value: int` param to `__init__`, update title dynamically |
| `ui/grid_canvas.py` | Add `hospital_edit_requested` signal; branch right-click on hospital; add `set_inspector_highlight()` + overlay draw |
| `ui/controller.py` | Add `edit_hospital_cars(row, col, new_count)`; change `build_*` methods to return `list[tuple[str, list]]` |
| `ui/qt_inspector_panel.py` | Accept `list[tuple[str, list]]`; store per-row highlight data; emit `highlight_cells_changed` on hover |
| `ui/simulation_page.py` | Wire `hospital_edit_requested`; call `load_items`; connect highlight signal to canvas |

---

## Task 1: HospitalDialog — accept initial value + dynamic title

**Files:**
- Modify: `ui/hospital_dialog.py`

**Interfaces:**
- Produces: `HospitalDialog(parent, initial_value: int = 3, edit_mode: bool = False)` — `car_count` property unchanged

- [ ] **Step 1: Modify `__init__` signature and title logic**

In `ui/hospital_dialog.py`, change the class `__init__` as follows. Find the existing `def __init__(self, parent=None):` line and replace it with the block below. The only changes are: (a) two new params, (b) `setWindowTitle`, (c) `title_lbl` text, (d) `sub_lbl` text, (e) `self.spin.setValue(initial_value)`.

```python
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
```

- [ ] **Step 2: Manual smoke test**

Run `python main.py`, place a hospital, verify dialog still opens with default value 3.

---

## Task 2: Controller — add `edit_hospital_cars` + convert `build_*` to return items

**Files:**
- Modify: `ui/controller.py`

**Interfaces:**
- Produces:
  - `edit_hospital_cars(row: int, col: int, new_count: int) -> None`
  - `build_q_table_items() -> list[tuple[str, list]]`
  - `build_h_table_items() -> list[tuple[str, list]]`
  - `build_paths_items() -> list[tuple[str, list]]`
  - `build_completed_trips_items() -> list[tuple[str, list]]`
  - Old `build_*_lines()` methods are **kept** as thin wrappers returning `[text for text, _ in self.build_*_items()]` so nothing breaks during migration.

- [ ] **Step 1: Add `edit_hospital_cars` method**

Insert this method after `place_hospital` in `ui/controller.py`:

```python
def edit_hospital_cars(self, row: int, col: int, new_count: int):
    key = next(
        (k for k, v in config.HOSPITAL_CONFIG.items() if tuple(v["pos"]) == (row, col)),
        None,
    )
    if key is None:
        return
    config.HOSPITAL_CONFIG[key]["max_cars"] = new_count
    self.dispatcher.current_cars[key] = min(
        new_count, self.dispatcher.current_cars.get(key, new_count)
    )
    self.logger.add_log(
        f"[STATION] Updated {key}: fleet size → {new_count} units "
        f"(available now: {self.dispatcher.current_cars[key]})."
    )
    self.fleet_updated.emit()
```

- [ ] **Step 2: Add `build_q_table_items`**

Add this method alongside `build_q_table_lines` in `ui/controller.py`:

```python
def build_q_table_items(self) -> list[tuple[str, list]]:
    items: list[tuple[str, list]] = [("--- LIVE BACKEND Q-TABLE METRICS ---", [])]
    if not self.global_q_brain.q_table:
        items.append(("No learned Q-weights in memory yet.", []))
        return items
    for state, values in self.global_q_brain.q_table.items():
        items.append((
            f"Cell {state} -> Q:{[round(v, 2) for v in values]}",
            [state],
        ))
    return items
```

Update `build_q_table_lines` to delegate:
```python
def build_q_table_lines(self) -> list[str]:
    return [text for text, _ in self.build_q_table_items()]
```

- [ ] **Step 3: Add `build_h_table_items`**

```python
def build_h_table_items(self) -> list[tuple[str, list]]:
    items: list[tuple[str, list]] = [("--- LIVE LRTA* HEURISTIC FIELDS ---", [])]
    if not self.global_h_table:
        items.append(("No heuristic data has been learned yet.", []))
        return items
    for state, h_val in sorted(self.global_h_table.items()):
        items.append((
            f"  Node {state} -> H: {round(h_val, 1)}",
            [state],
        ))
    return items
```

Update `build_h_table_lines`:
```python
def build_h_table_lines(self) -> list[str]:
    return [text for text, _ in self.build_h_table_items()]
```

- [ ] **Step 4: Add `build_paths_items`**

Each sub-line of a car inherits the full path of that car for highlighting.

```python
def build_paths_items(self) -> list[tuple[str, list]]:
    items: list[tuple[str, list]] = [("--- ACTIVE MISSION PATH ROUTING ---", [])]
    if not self.active_agents:
        items.append(("Fleet is currently stationed at depots.", []))
        return items
    for idx, car in enumerate(self.active_agents):
        from agents.astar_q_agent import AStarQAgent
        kind = "A*" if isinstance(car, AStarQAgent) else "LRTA*"
        car_path = list(car.path)
        planned  = getattr(car, 'calculated_path', None) or []
        all_cells = list(dict.fromkeys(car_path + planned))  # dedupe, preserve order
        items.append((f"Car #{idx + 1} [{kind}]:", all_cells))
        items.append((f"  {car.start_pos} -> {car.goal_pos}", all_cells))
        items.append((f"  Traversed: {len(car.path)} blocks.", all_cells))
    return items
```

Update `build_paths_lines`:
```python
def build_paths_lines(self) -> list[str]:
    return [text for text, _ in self.build_paths_items()]
```

- [ ] **Step 5: Add `build_completed_trips_items`**

```python
def build_completed_trips_items(self) -> list[tuple[str, list]]:
    items: list[tuple[str, list]] = [("--- TRIP HISTORY LOG ---", [])]
    if not self.completed_trips:
        items.append(("Chưa có chuyến xe nào hoàn thành.", []))
        return items
    for t in reversed(self.completed_trips):
        path = t['path']
        items.append((
            f"━━━ Chuyến #{t['num']}  [{t['kind']}]  "
            f"{t['steps']} bước  |  cost={t['cost']}",
            path,
        ))
        items.append((f"    Xuất phát: {t['start']}   Đích: {t['goal']}", path))
        items.append(("    Lộ trình:", path))
        for i in range(0, len(path), 5):
            chunk = path[i:i + 5]
            prefix = f"    [{i:>3}]  "
            cells_str = "  →  ".join(f"({r},{c})" for r, c in chunk)
            items.append((prefix + cells_str, path))
    return items
```

Update `build_completed_trips_lines`:
```python
def build_completed_trips_lines(self) -> list[str]:
    return [text for text, _ in self.build_completed_trips_items()]
```

- [ ] **Step 6: Commit**

```bash
git add ui/controller.py ui/hospital_dialog.py
git commit -m "feat: edit_hospital_cars + build_*_items with highlight data"
```

---

## Task 3: GridCanvas — `hospital_edit_requested` signal + inspector highlight overlay

**Files:**
- Modify: `ui/grid_canvas.py`

**Interfaces:**
- Produces:
  - `hospital_edit_requested = pyqtSignal(int, int)` — emitted with `(row, col)` on right-click over hospital cell
  - `set_inspector_highlight(cells: list) -> None` — stores cells, triggers repaint
- Consumes: existing `_draw_overlay`, `_to_grid`, `config.STATE_HOSPITAL`

- [ ] **Step 1: Add `hospital_edit_requested` signal and `_inspector_highlight` attribute**

In `ui/grid_canvas.py`, locate the three existing `pyqtSignal` lines and add the new signal:

```python
cell_clicked          = pyqtSignal(int, int)
hospital_requested    = pyqtSignal(int, int)
hospital_edit_requested = pyqtSignal(int, int)   # <-- new
hover_changed         = pyqtSignal(object)
```

In `__init__`, after `self._hover_cell = None`, add:

```python
self._inspector_highlight: list = []
```

- [ ] **Step 2: Branch right-click in `mousePressEvent`**

Replace the existing `mousePressEvent` with:

```python
def mousePressEvent(self, event):
    self.setFocus()
    if event.button() == Qt.MouseButton.RightButton:
        row, col = self._to_grid(event.pos())
        if (row is not None and
                self._ctrl.env.grid[row][col] == config.STATE_HOSPITAL):
            self.hospital_edit_requested.emit(row, col)
            return
        self._panning    = True
        self._last_mouse = event.pos()
        self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
    elif event.button() == Qt.MouseButton.LeftButton:
        row, col = self._to_grid(event.pos())
        if row is None:
            return
        if self._ctrl.brush_mode == 'HOSPITAL':
            self.hospital_requested.emit(row, col)
        else:
            self.cell_clicked.emit(row, col)
```

- [ ] **Step 3: Add `set_inspector_highlight` method**

Append this method anywhere in the class (e.g., after `reset_view`):

```python
def set_inspector_highlight(self, cells: list):
    self._inspector_highlight = cells
    self.update()
```

- [ ] **Step 4: Draw inspector overlay in `paintEvent`**

In `paintEvent`, locate the comment `# ── 4. Visualizer overlays` block. After all the existing overlay drawing (but before section 5 agents), add the inspector highlight:

```python
# ── 4b. Inspector hover highlight ─────────────────────────
if self._inspector_highlight:
    self._draw_overlay(
        painter,
        self._inspector_highlight,
        QColor(100, 200, 255, 75),
        cs, gap, r_abs,
    )
```

- [ ] **Step 5: Manual test**

Run `python main.py`, set default map, right-click an empty cell → should still pan. Right-click a hospital cell → should NOT start panning (dialog not wired yet, but no pan is the observable behavior).

- [ ] **Step 6: Commit**

```bash
git add ui/grid_canvas.py
git commit -m "feat: hospital_edit_requested signal + inspector highlight overlay"
```

---

## Task 4: QtInspectorPanel — hover → emit highlight signal

**Files:**
- Modify: `ui/qt_inspector_panel.py`

**Interfaces:**
- Produces:
  - `highlight_cells_changed = pyqtSignal(list)` — emitted with `list[tuple]` of `(row, col)` pairs
  - `load_items(items: list[tuple[str, list]]) -> None` — replaces `load_lines`; `load_lines` kept as wrapper
- Consumes: nothing new from earlier tasks

- [ ] **Step 1: Replace class body**

Rewrite `ui/qt_inspector_panel.py` in full:

```python
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
```

- [ ] **Step 2: Manual smoke test**

Run `python main.py`, open Q-Table view. Hover over rows in the inspector — no crash. (Highlight wiring comes in Task 5.)

- [ ] **Step 3: Commit**

```bash
git add ui/qt_inspector_panel.py
git commit -m "feat: inspector hover emits highlight_cells_changed signal"
```

---

## Task 5: SimulationPage — wire everything together

**Files:**
- Modify: `ui/simulation_page.py`

**Interfaces:**
- Consumes:
  - `GridCanvas.hospital_edit_requested(int, int)`
  - `QtInspectorPanel.highlight_cells_changed(list)`
  - `GridCanvas.set_inspector_highlight(list)`
  - `SimulationController.edit_hospital_cars(int, int, int)`
  - `SimulationController.build_*_items() -> list[tuple[str, list]]`
  - `HospitalDialog(parent, initial_value, edit_mode)`

- [ ] **Step 1: Connect `hospital_edit_requested` in `_connect_signals`**

In `_connect_signals`, after the line `self._canvas.hospital_requested.connect(self._on_hospital_requested)`, add:

```python
self._canvas.hospital_edit_requested.connect(self._on_hospital_edit_requested)
```

After the line `self._canvas.hover_changed.connect(self._on_hover_changed)`, add:

```python
self._inspector.highlight_cells_changed.connect(
    self._canvas.set_inspector_highlight)
```

- [ ] **Step 2: Add `_on_hospital_edit_requested` slot**

Add this method near `_on_hospital_requested` in `simulation_page.py`:

```python
def _on_hospital_edit_requested(self, row: int, col: int):
    key = next(
        (k for k, v in config.HOSPITAL_CONFIG.items()
         if tuple(v["pos"]) == (row, col)),
        None,
    )
    if key is None:
        return
    current = self._ctrl.dispatcher.current_cars.get(key, 1)
    dlg = HospitalDialog(self, initial_value=current, edit_mode=True)
    if dlg.exec():
        self._ctrl.edit_hospital_cars(row, col, dlg.car_count)
```

- [ ] **Step 3: Switch `_auto_refresh_inspector` to use `load_items`**

Replace the entire `_auto_refresh_inspector` method:

```python
def _auto_refresh_inspector(self):
    view = getattr(self, '_current_inspector_view', None)
    if view == 'Q':
        self._inspector.load_items(self._ctrl.build_q_table_items())
    elif view == 'H':
        self._inspector.load_items(self._ctrl.build_h_table_items())
    elif view == 'R':
        self._inspector.load_items(self._ctrl.build_paths_items())
    elif view == 'T':
        self._inspector.load_items(self._ctrl.build_completed_trips_items())
```

- [ ] **Step 4: Full end-to-end test**

Run `python main.py`:

1. Load default map → right-click hospital cell → dialog opens with current car count pre-filled, title says "EDIT HOSPITAL" → change value → click Update → status bar shows updated fleet count.
2. Place accident → wait for car to dispatch → press Q to open Q-Table → hover over a `Cell (r,c)` row → that cell lights up on the grid in light blue.
3. Press Ctrl+R (Routes) → hover over `Car #1 [A*]` row → planned path highlights on grid.
4. After a trip completes, press Ctrl+T (History) → hover over `━━━ Chuyến #1` row → route highlights.
5. Right-click an empty cell → panning still works normally.
6. Mouse leaves inspector → highlight clears.

- [ ] **Step 5: Commit**

```bash
git add ui/simulation_page.py
git commit -m "feat: wire hospital edit + inspector hover highlight to grid"
```

---

## Self-Review

**Spec coverage:**
- ✅ Edit ambulance count for hospital: Tasks 1, 2, 3, 5
- ✅ Right-click hospital → context menu path (direct dialog, no separate QMenu needed since there's only one action)
- ✅ Inspector hover → highlight node (Q/H tables): Tasks 2, 4, 5
- ✅ Inspector hover → highlight path (Routes/History): Tasks 2, 4, 5
- ✅ Light color overlay (alpha 75 ≤ 90 limit): Task 3

**Type consistency:**
- `build_*_items()` returns `list[tuple[str, list]]` consistently across Tasks 2, 4, 5 ✅
- `load_items` accepts `list[tuple[str, list]]` ✅
- `set_inspector_highlight(cells: list)` matches `highlight_cells_changed = pyqtSignal(list)` ✅
- `edit_hospital_cars(row, col, new_count)` matches call site in Task 5 ✅

**No placeholders:** All steps contain complete code. ✅
