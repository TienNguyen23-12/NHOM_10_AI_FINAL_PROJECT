# ui/controls_panel.py
# 3-cột layout: Brush Tools | AI Controls | Monitor + Map.
# Không dùng QScrollArea — tất cả buttons hiển thị cùng lúc trên màn hình.

import qtawesome as qta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QButtonGroup, QSizePolicy, QFrame
)
from PyQt6.QtGui  import QFont
from PyQt6.QtCore import Qt, QSize, pyqtSignal

import config

# ── Constants ─────────────────────────────────────────────────────────
_ICO   = QSize(13, 13)
_H_BTN = 28          # Chiều cao button — compact nhưng vẫn click được
_WHITE = "white"


# ── Helpers ───────────────────────────────────────────────────────────

def _ico(name: str, color: str = _WHITE) -> object:
    return qta.icon(name, color=color, options=[{"scale_factor": 0.8}])


def _col_header(text: str, icon_name: str) -> QWidget:
    """Header đậm nền tối, đặt đầu mỗi cột."""
    row = QHBoxLayout()
    row.setContentsMargins(8, 5, 8, 5)
    row.setSpacing(5)

    pix = QLabel()
    pix.setPixmap(qta.icon(icon_name, color="#AEB6BF").pixmap(QSize(11, 11)))
    row.addWidget(pix)

    lbl = QLabel(text)
    lbl.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
    lbl.setStyleSheet("color: #AEB6BF; letter-spacing: 1px;")
    row.addWidget(lbl, stretch=1)

    w = QWidget()
    w.setLayout(row)
    w.setFixedHeight(26)
    w.setStyleSheet(
        "QWidget { background: #16263F; border-radius: 4px; }")
    return w


def _mini_header(text: str) -> QLabel:
    """Header nhỏ trong lòng cột (không có nền tối)."""
    lbl = QLabel(text)
    lbl.setFont(QFont("Segoe UI", 6, QFont.Weight.Bold))
    lbl.setStyleSheet(
        "color: #7F8C8D; letter-spacing: 1px; "
        "border-top: 1px solid #D5DBDB; padding-top: 4px; margin-top: 2px;")
    return lbl


def _sep_v() -> QFrame:
    """Đường kẻ dọc ngăn cách 2 cột."""
    f = QFrame()
    f.setFrameShape(QFrame.Shape.VLine)
    f.setFixedWidth(1)
    f.setStyleSheet("background: #D5DBDB; border: none;")
    return f


def _btn(text: str, icon_name: str, tip: str = "",
         checkable: bool = False) -> QPushButton:
    b = QPushButton(f" {text}")
    b.setIcon(_ico(icon_name))
    b.setIconSize(_ICO)
    b.setCheckable(checkable)
    b.setFixedHeight(_H_BTN)
    b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    b.setFont(QFont("Segoe UI", 7, QFont.Weight.Medium))
    if tip:
        b.setToolTip(tip)
    return b


def _grid_row(*buttons: QPushButton, spacing: int = 3) -> QWidget:
    """Đặt 2-3 buttons vào một hàng ngang."""
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(spacing)
    for b in buttons:
        h.addWidget(b)
    return w


# ── ControlsPanel ─────────────────────────────────────────────────────

class ControlsPanel(QWidget):
    """3-cột controls panel — không scroll, hiển thị hết buttons trên màn hình.

    Cấu trúc:
      [Brush Tools] | [AI Controls] | [AI Monitor + Map Controls]
    """

    # Signals
    brush_changed      = pyqtSignal(str)
    mode_changed       = pyqtSignal(int)
    pause_clicked      = pyqtSignal()
    clear_map_clicked  = pyqtSignal()
    rush_hour_clicked  = pyqtSignal()
    visualizer_clicked = pyqtSignal()
    view_qtable        = pyqtSignal()
    view_htable        = pyqtSignal()
    view_routes        = pyqtSignal()
    save_model         = pyqtSignal()
    load_model         = pyqtSignal()
    save_map           = pyqtSignal()
    load_map           = pyqtSignal()
    expand_map         = pyqtSignal()
    shrink_map         = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed)   # Chiều cao = sizeHint, không co giãn dọc

        outer = QHBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(0)

        # Ba cột, mỗi cột có stretch=1 để chia đều
        col1 = self._build_col_brush()
        col2 = self._build_col_ai()
        col3 = self._build_col_monitor_map()

        outer.addWidget(col1, stretch=3)
        outer.addWidget(_sep_v())
        outer.addWidget(col2, stretch=4)
        outer.addWidget(_sep_v())
        outer.addWidget(col3, stretch=4)

    # ------------------------------------------------------------------ #
    #  Cột 1 — Brush Tools                                                #
    # ------------------------------------------------------------------ #

    def _build_col_brush(self) -> QWidget:
        col = QWidget()
        v   = QVBoxLayout(col)
        v.setContentsMargins(4, 0, 4, 0)
        v.setSpacing(3)
        v.setAlignment(Qt.AlignmentFlag.AlignTop)

        v.addWidget(_col_header("BRUSH TOOLS", "fa5s.paint-brush"))

        self._brush_group = QButtonGroup(self)
        self._brush_group.setExclusive(True)
        self._brushes: dict[str, QPushButton] = {}

        # Brush buttons trong grid 2 cột
        brush_defs = [
            ('ACCIDENT', "Accident",  "fa5s.car-crash",     "Tai nạn [1]",   0, 0),
            ('HOSPITAL', "Hospital",  "fa5s.hospital",      "Bệnh viện [2]", 0, 1),
            ('WALL',     "Wall",      "fa5s.cube",          "Tường [3]",     1, 0),
            ('TRAFFIC',  "Traffic",   "fa5s.traffic-light", "Kẹt xe [4]",    1, 1),
            ('ERASE',    "Eraser",    "fa5s.eraser",        "Xóa ô [5]",     2, 0),
        ]
        grid = QGridLayout()
        grid.setSpacing(3)
        grid.setContentsMargins(0, 0, 0, 0)

        for key, text, ico, tip, row, col_idx in brush_defs:
            b = _btn(text, ico, tip, checkable=True)
            self._brush_group.addButton(b)
            b.clicked.connect(lambda _, k=key: self.brush_changed.emit(k))
            grid.addWidget(b, row, col_idx)
            self._brushes[key] = b

        self._brushes['ACCIDENT'].setChecked(True)
        v.addLayout(grid)
        v.addStretch()
        return col

    # ------------------------------------------------------------------ #
    #  Cột 2 — AI Controls                                                #
    # ------------------------------------------------------------------ #

    def _build_col_ai(self) -> QWidget:
        col = QWidget()
        v   = QVBoxLayout(col)
        v.setContentsMargins(4, 0, 4, 0)
        v.setSpacing(3)
        v.setAlignment(Qt.AlignmentFlag.AlignTop)

        v.addWidget(_col_header("AI CONTROLS", "fa5s.brain"))

        # Dòng 1 + 2: Algorithm mode (exclusive group với 4 nút)
        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)

        self._btn_astar = _btn("A* Thuần", "fa5s.star", checkable=True)
        self._btn_lrta = _btn("LRTA* Thuần", "fa5s.route", checkable=True)
        self._btn_astar_q = _btn("A* + Q", "fa5s.brain", checkable=True)
        self._btn_lrta_q = _btn("LRTA* + Q", "fa5s.microchip", checkable=True)

        # Mặc định chọn A* + Q
        self._btn_astar_q.setChecked(True)

        self._mode_group.addButton(self._btn_astar)
        self._mode_group.addButton(self._btn_lrta)
        self._mode_group.addButton(self._btn_astar_q)
        self._mode_group.addButton(self._btn_lrta_q)

        self._btn_astar.clicked.connect(lambda: self.mode_changed.emit(config.MODE_ASTAR))
        self._btn_lrta.clicked.connect(lambda: self.mode_changed.emit(config.MODE_LRTASTAR))
        self._btn_astar_q.clicked.connect(lambda: self.mode_changed.emit(config.MODE_ASTAR_Q))
        self._btn_lrta_q.clicked.connect(lambda: self.mode_changed.emit(config.MODE_LRTASTAR_Q))

        # Xếp thành 2 dòng
        v.addWidget(_grid_row(self._btn_astar, self._btn_lrta))
        v.addWidget(_grid_row(self._btn_astar_q, self._btn_lrta_q))

        # Dòng 2: Rush Hour + Stop/Resume
        self._btn_rush  = _btn("Rush Hour", "fa5s.clock", "Giờ cao điểm [Ctrl+H]", checkable=True)
        self._btn_pause = _btn("Stop/Resume","fa5s.pause", "Dừng/tiếp tục [Space]", checkable=True)
        v.addWidget(_grid_row(self._btn_rush, self._btn_pause))

        self._btn_rush.clicked.connect(self.rush_hour_clicked)
        self._btn_pause.clicked.connect(self.pause_clicked)

        # Dòng 3: Clear Map (toàn chiều rộng — nút nguy hiểm)
        self._btn_clear = _btn("Clear Map", "fa5s.trash", "Xóa bản đồ, về Menu [Ctrl+W]")
        self._btn_clear.setProperty("danger", "true")
        self._btn_clear.clicked.connect(self.clear_map_clicked)
        v.addWidget(self._btn_clear)

        # Dòng 4: Visualizer (toàn chiều rộng)
        self._btn_vis = _btn("Visualizer: OFF", "fa5s.eye",
                             "Hiện quá trình tìm đường [V]", checkable=True)
        self._btn_vis.clicked.connect(self.visualizer_clicked)
        v.addWidget(self._btn_vis)

        v.addStretch()
        return col

    # ------------------------------------------------------------------ #
    #  Cột 3 — AI Monitor + Map Controls                                  #
    # ------------------------------------------------------------------ #

    def _build_col_monitor_map(self) -> QWidget:
        col = QWidget()
        v   = QVBoxLayout(col)
        v.setContentsMargins(4, 0, 4, 0)
        v.setSpacing(3)
        v.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── AI Monitor sub-section ──────────────────────────────
        v.addWidget(_col_header("AI MONITOR", "fa5s.search"))

        # Dòng 1: Q-Table | H-Table | Routes
        btn_q  = _btn("Q-Table", "fa5s.table",     "Xem Q-table [Q]")
        btn_h  = _btn("H-Table", "fa5s.chart-bar", "Xem H-table [H]")
        btn_rt = _btn("Routes",  "fa5s.map-signs",  "Xem routes [Ctrl+R]")
        btn_q.clicked.connect(self.view_qtable)
        btn_h.clicked.connect(self.view_htable)
        btn_rt.clicked.connect(self.view_routes)
        v.addWidget(_grid_row(btn_q, btn_h, btn_rt))

        # Dòng 2: Save Model | Load Model
        btn_sm = _btn("Save AI", "fa5s.save",  "Lưu Q-brain [Ctrl+Shift+S]")
        btn_lm = _btn("Load AI", "fa5s.brain", "Tải Q-brain [Ctrl+Shift+O]")
        btn_sm.clicked.connect(self.save_model)
        btn_lm.clicked.connect(self.load_model)
        v.addWidget(_grid_row(btn_sm, btn_lm))

        # ── Map Controls sub-section ────────────────────────────
        v.addWidget(_mini_header("MAP CONTROLS"))

        # Dòng 3: Save Map | Load Map
        btn_sv = _btn("Save Map", "fa5s.save",        "Lưu bản đồ [Ctrl+S]")
        btn_ld = _btn("Load Map", "fa5s.folder-open", "Tải bản đồ [Ctrl+O]")
        btn_sv.clicked.connect(self.save_map)
        btn_ld.clicked.connect(self.load_map)
        v.addWidget(_grid_row(btn_sv, btn_ld))

        # Dòng 4: Expand | Shrink
        btn_ex = _btn("Expand +5", "fa5s.expand",   "Tăng kích thước [+]")
        btn_sh = _btn("Shrink -5", "fa5s.compress", "Giảm kích thước [-]")
        btn_ex.clicked.connect(self.expand_map)
        btn_sh.clicked.connect(self.shrink_map)
        v.addWidget(_grid_row(btn_ex, btn_sh))

        v.addStretch()
        return col

    # ------------------------------------------------------------------ #
    #  State setters                                                       #
    # ------------------------------------------------------------------ #

    def set_brush(self, mode: str):
        if mode in self._brushes:
            self._brushes[mode].setChecked(True)

    def set_mode(self, mode: int):
        (self._btn_astar if mode == config.MODE_ASTAR_Q else self._btn_lrta).setChecked(True)

    def set_paused(self, paused: bool):
        self._btn_pause.setChecked(paused)
        self._btn_pause.setIcon(_ico("fa5s.play" if paused else "fa5s.pause"))
        self._btn_pause.setText(" STOPPED  ⏸" if paused else " Stop/Resume")

    def set_rush_hour(self, hour: int):
        is_rush = (hour == 17)
        self._btn_rush.setChecked(is_rush)
        self._btn_rush.setText(" Standard 12h" if is_rush else " Rush Hour")

    def set_visualizer(self, active: bool):
        self._btn_vis.setChecked(active)
        self._btn_vis.setIcon(_ico("fa5s.eye", color="#F1C40F" if active else _WHITE))
        self._btn_vis.setText(" Visualizer: ON  ●" if active else " Visualizer: OFF")
