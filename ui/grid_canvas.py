# ui/grid_canvas.py
# GridCanvas: render grid với rounded corners, hover preview, agents, overlays.

from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore    import Qt, QPoint, QRectF, pyqtSignal
from PyQt6.QtGui     import (
    QPainter, QColor, QPen, QBrush, QTransform, QCursor,
    QLinearGradient, QPainterPath
)

import config

# ── Cell colors ───────────────────────────────────────────────────────
_CELL_COLORS = {
    config.STATE_EMPTY:    QColor(252, 253, 255),  # Trắng xanh nhẹ
    config.STATE_WALL:     QColor(44,  62,  80),   # Xanh đen
    config.STATE_TRAFFIC:  QColor(230, 126, 34),   # Cam
    config.STATE_ACCIDENT: QColor(231, 76,  60),   # Đỏ
    config.STATE_HOSPITAL: QColor(142, 68, 173),   # Tím
}
# Gradient highlight cho mỗi state (màu sáng hơn ở góc trên-trái)
_CELL_HIGHLIGHT = {
    config.STATE_EMPTY:    QColor(255, 255, 255, 180),
    config.STATE_WALL:     QColor(80,  100, 120, 60),
    config.STATE_TRAFFIC:  QColor(255, 180, 100, 100),
    config.STATE_ACCIDENT: QColor(255, 140, 120, 100),
    config.STATE_HOSPITAL: QColor(200, 130, 240, 100),
}

_CANVAS_BG  = QColor(229, 234, 240)   # Nền xám xanh
_GRID_LINE  = QColor(200, 210, 220)   # Đường lưới

# Hover brush preview colors (fill bán trong suốt)
_HOVER_COLORS = {
    'ACCIDENT': QColor(231, 76,  60,  140),
    'HOSPITAL': QColor(142, 68, 173,  140),
    'WALL':     QColor(44,  62,  80,  140),
    'TRAFFIC':  QColor(230, 126, 34,  140),
    'ERASE':    QColor(189, 195, 199, 140),
}

_ZOOM_MIN = 0.12
_ZOOM_MAX = 14.0

# Bán kính bo góc tính theo tỉ lệ cell size
_CORNER_RATIO = 0.22   # 22% của CELL_SIZE


class GridCanvas(QWidget):
    """Render lưới bản đồ với:
    - Rounded corners trên mỗi ô (QPainterPath)
    - Hover preview khi di chuột
    - Agent trails + position circles
    - Visualizer overlays (semi-transparent)
    - Zoom (scroll wheel / Ctrl+±) và pan (chuột phải / WASD)
    """

    cell_clicked       = pyqtSignal(int, int)
    hospital_requested = pyqtSignal(int, int)

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._ctrl = controller

        self._zoom  = 1.0
        self._pan_x = 20.0
        self._pan_y = 20.0
        self._panning    = False
        self._last_mouse = QPoint()
        self._hover_cell = None      # (row, col) ô đang hover

        self.setMinimumSize(300, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        self._ctrl.grid_updated.connect(self.update)

    # ------------------------------------------------------------------ #
    #  Paint                                                               #
    # ------------------------------------------------------------------ #

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        # Nền canvas (ngoài grid)
        painter.fillRect(self.rect(), _CANVAS_BG)

        transform = QTransform()
        transform.translate(self._pan_x, self._pan_y)
        transform.scale(self._zoom, self._zoom)
        painter.setTransform(transform)

        cs    = config.CELL_SIZE
        gs    = config.GRID_SIZE
        r_abs = max(2.0, cs * _CORNER_RATIO)   # Bán kính bo góc (pixel trong grid space)
        gap   = 1.5                              # Khoảng trống giữa các ô

        # ── 1. Background tổng thể của grid (shadow-like border) ──
        total = gs * cs
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(180, 195, 210)))
        painter.drawRoundedRect(
            QRectF(-4, -4, total + 8, total + 8), r_abs + 3, r_abs + 3)

        # ── 2. Các ô grid với rounded corners ─────────────────────
        for r in range(gs):
            for c in range(gs):
                state = self._ctrl.env.grid[r][c]
                self._draw_cell(painter, r, c, cs, r_abs, gap, state)

        # ── 3. Hover preview ──────────────────────────────────────
        if self._hover_cell:
            hr, hc = self._hover_cell
            hover_color = _HOVER_COLORS.get(
                self._ctrl.brush_mode, QColor(200, 200, 200, 130))
            x = hc * cs + gap
            y = hr * cs + gap
            w = cs - gap * 2
            # Bỏ brush preview nếu ô đã là Hospital (không overwrite)
            current = self._ctrl.env.grid[hr][hc]
            if not (self._ctrl.brush_mode == 'ACCIDENT' and
                    current != config.STATE_EMPTY):
                painter.setPen(QPen(hover_color.darker(130), 1.5))
                painter.setBrush(QBrush(hover_color))
                painter.drawRoundedRect(QRectF(x, y, w, w), r_abs, r_abs)

        # ── 4. Visualizer overlays ─────────────────────────────────
        if self._ctrl.dispatch_vis_data:
            open_s, visited, path, _ = self._ctrl.dispatch_vis_data
            self._draw_overlay(painter, visited, QColor(241, 196, 15, 70),  cs, gap, r_abs)
            self._draw_overlay(painter, open_s,  QColor(230, 126, 34, 110), cs, gap, r_abs)
            if path:
                self._draw_overlay(painter, path, QColor(155, 89, 182, 130), cs, gap, r_abs)

        for agent in self._ctrl.active_agents:
            vis_v = getattr(agent, 'vis_visited',  None)
            vis_o = getattr(agent, 'vis_open_set', None)
            vis_p = getattr(agent, 'vis_path',     None)
            if vis_v: self._draw_overlay(painter, vis_v, QColor(231, 76, 60, 90),   cs, gap, r_abs)
            if vis_o: self._draw_overlay(painter, vis_o, QColor(46, 204, 113, 110), cs, gap, r_abs)
            if vis_p: self._draw_overlay(painter, vis_p, QColor(52, 152, 219, 130), cs, gap, r_abs)

        # ── 5. Agent trails + positions ───────────────────────────
        for agent in self._ctrl.active_agents:
            self._draw_agent(painter, agent, cs)

        painter.end()

    # ── Cell renderer ─────────────────────────────────────────────

    def _draw_cell(self, painter: QPainter,
                   r: int, c: int, cs: int,
                   radius: float, gap: float, state: int):
        x = c * cs + gap
        y = r * cs + gap
        w = cs - gap * 2
        rect = QRectF(x, y, w, w)

        base_color = _CELL_COLORS.get(state, QColor(240, 240, 240))
        painter.setPen(Qt.PenStyle.NoPen)

        if state == config.STATE_EMPTY:
            # Ô trống: màu đơn giản, không cần gradient
            painter.setBrush(QBrush(base_color))
            painter.drawRoundedRect(rect, radius, radius)
        else:
            # Ô có nội dung: thêm gradient nhẹ để trông có chiều sâu
            grad = QLinearGradient(x, y, x + w * 0.6, y + w * 0.6)
            highlight = _CELL_HIGHLIGHT.get(state, QColor(255, 255, 255, 60))
            grad.setColorAt(0.0, highlight)
            grad.setColorAt(1.0, QColor(0, 0, 0, 0))

            painter.setBrush(QBrush(base_color))
            painter.drawRoundedRect(rect, radius, radius)

            # Gradient overlay
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(rect, radius, radius)

            # Viền nhẹ
            border = base_color.darker(130)
            border.setAlpha(80)
            painter.setPen(QPen(border, 0.8))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, radius, radius)

    # ── Overlay renderer ──────────────────────────────────────────

    def _draw_overlay(self, painter: QPainter, cells,
                      color: QColor, cs: int, gap: float, radius: float):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        for row, col in cells:
            x = col * cs + gap
            y = row * cs + gap
            w = cs - gap * 2
            painter.drawRoundedRect(QRectF(x, y, w, w), radius, radius)

    # ── Agent renderer ────────────────────────────────────────────

    def _draw_agent(self, painter: QPainter, agent, cs: int):
        color  = QColor(*agent.color)
        shadow = QColor(0, 0, 0, 60)

        # Trail lines
        if len(agent.path) > 1:
            pen = QPen(color, 2.5)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            for i in range(len(agent.path) - 1):
                r1, c1 = agent.path[i]
                r2, c2 = agent.path[i + 1]
                painter.drawLine(
                    c1 * cs + cs // 2, r1 * cs + cs // 2,
                    c2 * cs + cs // 2, r2 * cs + cs // 2,
                )

        # Agent circle với shadow
        row, col = agent.current_pos
        cx  = col * cs + cs // 2
        cy  = row * cs + cs // 2
        rad = cs // 3

        # Drop shadow
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(shadow))
        painter.drawEllipse(cx - rad + 1, cy - rad + 2, rad * 2, rad * 2)

        # Main circle
        painter.setBrush(QBrush(color))
        painter.drawEllipse(cx - rad, cy - rad, rad * 2, rad * 2)

        # Highlight spot
        hi = QColor(255, 255, 255, 100)
        painter.setBrush(QBrush(hi))
        painter.drawEllipse(cx - rad // 2, cy - rad, rad, rad)

    # ------------------------------------------------------------------ #
    #  Mouse                                                               #
    # ------------------------------------------------------------------ #

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.MouseButton.RightButton:
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

    def mouseMoveEvent(self, event):
        if self._panning:
            delta        = event.pos() - self._last_mouse
            self._pan_x += delta.x()
            self._pan_y += delta.y()
            self._last_mouse = event.pos()
            self.update()
        else:
            row, col  = self._to_grid(event.pos())
            new_hover = (row, col) if row is not None else None
            if new_hover != self._hover_cell:
                self._hover_cell = new_hover
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._panning = False
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

    def leaveEvent(self, event):
        self._hover_cell = None
        self.update()

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        mx = event.position().x()
        my = event.position().y()
        self._pan_x = mx - factor * (mx - self._pan_x)
        self._pan_y = my - factor * (my - self._pan_y)
        self._zoom  = max(_ZOOM_MIN, min(self._zoom * factor, _ZOOM_MAX))
        self.update()

    # ------------------------------------------------------------------ #
    #  Keyboard (pan & zoom khi widget có focus)                          #
    # ------------------------------------------------------------------ #

    def keyPressEvent(self, event):
        key = event.key()
        mod = event.modifiers()
        step = 30

        if   key in (Qt.Key.Key_Left,  Qt.Key.Key_A): self._pan_x += step; self.update()
        elif key in (Qt.Key.Key_Right, Qt.Key.Key_D): self._pan_x -= step; self.update()
        elif key in (Qt.Key.Key_Up,    Qt.Key.Key_W): self._pan_y += step; self.update()
        elif key in (Qt.Key.Key_Down,  Qt.Key.Key_S): self._pan_y -= step; self.update()
        elif (key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal) and
              mod & Qt.KeyboardModifier.ControlModifier):
            self._zoom_center(1.2)
        elif (key == Qt.Key.Key_Minus and
              mod & Qt.KeyboardModifier.ControlModifier):
            self._zoom_center(1 / 1.2)
        else:
            super().keyPressEvent(event)

    def _zoom_center(self, factor: float):
        cx = self.width()  / 2
        cy = self.height() / 2
        self._pan_x = cx - factor * (cx - self._pan_x)
        self._pan_y = cy - factor * (cy - self._pan_y)
        self._zoom  = max(_ZOOM_MIN, min(self._zoom * factor, _ZOOM_MAX))
        self.update()

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _to_grid(self, pos: QPoint):
        adj_x = (pos.x() - self._pan_x) / self._zoom
        adj_y = (pos.y() - self._pan_y) / self._zoom
        col   = int(adj_x // config.CELL_SIZE)
        row   = int(adj_y // config.CELL_SIZE)
        if 0 <= row < config.GRID_SIZE and 0 <= col < config.GRID_SIZE:
            return row, col
        return None, None

    def reset_view(self):
        self._zoom  = 1.0
        self._pan_x = 20.0
        self._pan_y = 20.0
        self.update()
