# ui/simulation_page.py
# Layout: outer_split (dọc) chứa main_split (ngang) + logger.
# Panel phải: QVBoxLayout với controls (cố định chiều cao) + inspector (mở rộng).
# ControlsPanel không còn scroll — 3 cột hiển thị hết trên màn hình.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame,
    QLabel, QSizePolicy, QMessageBox
)
from PyQt6.QtGui  import QFont, QKeySequence, QShortcut
from PyQt6.QtCore import Qt, pyqtSignal

import config
from ui.controller          import SimulationController
from ui.grid_canvas         import GridCanvas
from ui.controls_panel      import ControlsPanel
from ui.qt_inspector_panel  import QtInspectorPanel
from ui.qt_logger_panel     import QtLoggerPanel
from ui.hospital_dialog     import HospitalDialog


def _hline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet("background: #D5DBDB; border: none;")
    return f


class SimulationPage(QWidget):
    """Màn hình Simulation.

    Cấu trúc:
      outer_split (dọc)
        ├─ main_split (ngang)        [kéo trái-phải]
        │    ├─ GridCanvas
        │    └─ right_widget (QVBoxLayout)
        │         ├─ ControlsPanel   [3 cột, chiều cao cố định — không scroll]
        │         ├─ separator
        │         └─ InspectorPanel  [chiếm phần còn lại]
        └─ LoggerPanel               [kéo lên-xuống]
    """

    go_to_menu = pyqtSignal()

    def __init__(self, controller: SimulationController, parent=None):
        super().__init__(parent)
        self._ctrl = controller
        self._build_ui()
        self._connect_signals()
        self._register_shortcuts()

    # ------------------------------------------------------------------ #
    #  Build layout                                                        #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── outer_split: [main content] / [logger] ────────────────
        outer_split = QSplitter(Qt.Orientation.Vertical)
        outer_split.setChildrenCollapsible(False)
        outer_split.setHandleWidth(5)

        # ── main_split: [grid] / [right widget] ───────────────────
        main_split = QSplitter(Qt.Orientation.Horizontal)
        main_split.setChildrenCollapsible(False)
        main_split.setHandleWidth(5)

        self._canvas = GridCanvas(self._ctrl)
        self._canvas.setMinimumWidth(300)
        main_split.addWidget(self._canvas)

        # ── right_widget: controls (cố định) + inspector (flex) ───
        right_widget = QWidget()
        right_widget.setMinimumWidth(460)
        right_v = QVBoxLayout(right_widget)
        right_v.setSpacing(0)
        right_v.setContentsMargins(0, 0, 0, 0)

        self._controls = ControlsPanel()
        right_v.addWidget(self._controls, stretch=0)   # không co giãn dọc

        right_v.addWidget(_hline())

        inspector_wrap = self._build_inspector_wrap()
        right_v.addWidget(inspector_wrap, stretch=1)   # chiếm phần còn lại

        main_split.addWidget(right_widget)
        main_split.setSizes([720, 540])
        main_split.setStretchFactor(0, 1)
        main_split.setStretchFactor(1, 0)
        self._main_split = main_split

        outer_split.addWidget(main_split)

        # ── Logger trong splitter (kéo được lên-xuống) ────────────
        self._logger_widget = QtLoggerPanel()
        outer_split.addWidget(self._logger_widget)
        outer_split.setSizes([580, 130])
        outer_split.setStretchFactor(0, 1)
        outer_split.setStretchFactor(1, 0)

        root.addWidget(outer_split, stretch=1)

        # ── Status bar cố định ở đáy ──────────────────────────────
        self._status_label = QLabel()
        self._status_label.setProperty("status", True)
        self._status_label.setFont(QFont("Segoe UI", 8))
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._status_label.setFixedHeight(22)
        root.addWidget(self._status_label)

        self._update_status()

    def _build_inspector_wrap(self) -> QWidget:
        wrap = QWidget()
        wrap.setMinimumWidth(220)
        layout = QVBoxLayout(wrap)
        layout.setSpacing(2)
        layout.setContentsMargins(6, 4, 6, 6)

        header = QLabel("  LIVE AI MONITOR")
        header.setProperty("section", True)
        header.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        layout.addWidget(header)

        self._inspector = QtInspectorPanel()
        layout.addWidget(self._inspector)
        return wrap

    # ------------------------------------------------------------------ #
    #  Signals ↔ Slots                                                     #
    # ------------------------------------------------------------------ #

    def _connect_signals(self):
        ctrl = self._ctrl
        ctrl.log_added.connect(self._logger_widget.add_log)
        ctrl.fleet_updated.connect(self._update_status)
        ctrl.status_changed.connect(self._update_status)

        self._canvas.cell_clicked.connect(self._on_cell_clicked)
        self._canvas.hospital_requested.connect(self._on_hospital_requested)

        cp = self._controls
        cp.brush_changed.connect(self._on_brush_changed)
        cp.mode_changed.connect(self._on_mode_changed)
        cp.pause_clicked.connect(self._on_pause)
        cp.clear_map_clicked.connect(self._on_clear_map)
        cp.rush_hour_clicked.connect(self._on_rush_hour)
        cp.visualizer_clicked.connect(self._on_visualizer)
        cp.view_qtable.connect(self._on_view_qtable)
        cp.view_htable.connect(self._on_view_htable)
        cp.view_routes.connect(self._on_view_routes)
        cp.save_model.connect(ctrl.save_q_brain)
        cp.load_model.connect(ctrl.load_q_brain)
        cp.save_map.connect(ctrl.save_map)
        cp.load_map.connect(ctrl.load_map)
        cp.expand_map.connect(lambda: ctrl.resize_map(5))
        cp.shrink_map.connect(lambda: ctrl.resize_map(-5))

    # ------------------------------------------------------------------ #
    #  Keyboard shortcuts                                                  #
    # ------------------------------------------------------------------ #

    def _register_shortcuts(self):
        def sc(key, slot):
            QShortcut(QKeySequence(key), self).activated.connect(slot)

        sc("1", lambda: self._set_brush_kb('ACCIDENT'))
        sc("2", lambda: self._set_brush_kb('HOSPITAL'))
        sc("3", lambda: self._set_brush_kb('WALL'))
        sc("4", lambda: self._set_brush_kb('TRAFFIC'))
        sc("5", lambda: self._set_brush_kb('ERASE'))

        sc("A",      lambda: self._set_mode_kb(config.MODE_ASTAR_Q))
        sc("L",      lambda: self._set_mode_kb(config.MODE_LRTASTAR_Q))
        sc("Space",  self._on_pause)
        sc("V",      self._on_visualizer)
        sc("Ctrl+H", self._on_rush_hour)

        sc("Q",       self._on_view_qtable)
        sc("H",       self._on_view_htable)
        sc("Ctrl+R",  self._on_view_routes)

        sc("Ctrl+S",       self._ctrl.save_map)
        sc("Ctrl+O",       self._ctrl.load_map)
        sc("Ctrl+Shift+S", self._ctrl.save_q_brain)
        sc("Ctrl+Shift+O", self._ctrl.load_q_brain)

        sc("+",      lambda: self._ctrl.resize_map(5))
        sc("=",      lambda: self._ctrl.resize_map(5))
        sc("-",      lambda: self._ctrl.resize_map(-5))
        sc("0",      self._canvas.reset_view)
        sc("Ctrl+W", self._on_clear_map)
        sc("Escape", self._on_escape)

    def _set_brush_kb(self, mode: str):
        self._ctrl.set_brush(mode)
        self._controls.set_brush(mode)

    def _set_mode_kb(self, mode: int):
        self._ctrl.set_mode(mode)
        self._controls.set_mode(mode)
        self._update_status()

    def _on_escape(self):
        if self._ctrl.active_agents or self._ctrl.pending_accidents:
            reply = QMessageBox.question(
                self, "Về Menu",
                "Simulation đang chạy. Về Menu không?\n"
                "(Tiến trình hiện tại sẽ bị hủy.)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self._on_clear_map()

    # ------------------------------------------------------------------ #
    #  Slots                                                               #
    # ------------------------------------------------------------------ #

    def _on_cell_clicked(self, row: int, col: int):
        mode = self._ctrl.brush_mode
        if   mode == 'ERASE':    self._ctrl.erase_cell(row, col)
        elif mode == 'WALL':     self._ctrl.place_wall(row, col)
        elif mode == 'TRAFFIC':  self._ctrl.place_traffic(row, col)
        elif mode == 'ACCIDENT': self._ctrl.place_accident(row, col)

    def _on_hospital_requested(self, row: int, col: int):
        if self._ctrl.env.grid[row][col] not in (config.STATE_EMPTY, config.STATE_WALL):
            self._ctrl.logger.add_log(
                f"[ERROR] Ô ({row},{col}) đã có vật thể — không thể đặt bệnh viện.")
            return
        dlg = HospitalDialog(self)
        if dlg.exec():
            self._ctrl.place_hospital(row, col, dlg.car_count)

    def _on_brush_changed(self, mode: str):
        self._ctrl.set_brush(mode)

    def _on_mode_changed(self, mode: int):
        self._ctrl.set_mode(mode)
        self._update_status()

    def _on_pause(self):
        self._controls.set_paused(self._ctrl.toggle_pause())

    def _on_clear_map(self):
        self._ctrl.clear_map()
        self._canvas.reset_view()
        self.go_to_menu.emit()

    def _on_rush_hour(self):
        self._controls.set_rush_hour(self._ctrl.toggle_rush_hour())

    def _on_visualizer(self):
        self._controls.set_visualizer(self._ctrl.toggle_visualizer())

    def _on_view_qtable(self):
        self._inspector.load_lines(self._ctrl.build_q_table_lines())

    def _on_view_htable(self):
        self._inspector.load_lines(self._ctrl.build_h_table_lines())

    def _on_view_routes(self):
        self._inspector.load_lines(self._ctrl.build_paths_lines())

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    def on_enter(self):
        self._ctrl.start_timers()
        self._canvas.reset_view()
        self._update_status()

    def on_leave(self):
        self._ctrl.stop_timers()

    def _update_status(self):
        self._status_label.setText(
            "  " + self._ctrl.get_status_text() +
            "    ·    F11 Fullscreen   Space Pause   0 Reset View")
