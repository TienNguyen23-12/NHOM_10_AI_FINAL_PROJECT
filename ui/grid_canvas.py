# ui/grid_canvas.py
# GridCanvas: render grid với rounded corners, icon trên ô, hover preview,
# agents (xe cứu thương + đèn ưu tiên), overlays và legend.

import qtawesome as qta

from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore    import Qt, QPoint, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui     import (
    QPainter, QColor, QPen, QBrush, QTransform, QCursor,
    QLinearGradient, QPainterPath, QPixmap, QFont
)

import config

# ── Cell colors ───────────────────────────────────────────────────────
_CELL_COLORS = {
    config.STATE_EMPTY:    QColor(252, 253, 255),  # Trắng xanh nhẹ
    config.STATE_WALL:     QColor(44,  62,  80),   # Xanh đen
    config.STATE_TRAFFIC:  QColor(230, 126, 34),   # Cam
    config.STATE_ACCIDENT: QColor(231, 76,  60),   # Đỏ
    config.STATE_HOSPITAL: QColor(22, 160, 133),   # Xanh y tế
}
# Gradient highlight cho mỗi state (màu sáng hơn ở góc trên-trái)
_CELL_HIGHLIGHT = {
    config.STATE_EMPTY:    QColor(255, 255, 255, 180),
    config.STATE_WALL:     QColor(80,  100, 120, 60),
    config.STATE_TRAFFIC:  QColor(255, 180, 100, 100),
    config.STATE_ACCIDENT: QColor(255, 140, 120, 100),
    config.STATE_HOSPITAL: QColor(120, 220, 200, 100),
}

_CANVAS_BG  = QColor(229, 234, 240)   # Nền xám xanh
_GRID_LINE  = QColor(200, 210, 220)   # Đường lưới

# Hover brush preview colors (fill bán trong suốt)
_HOVER_COLORS = {
    'ACCIDENT': QColor(231, 76,  60,  140),
    'HOSPITAL': QColor(22, 160, 133,  140),
    'WALL':     QColor(44,  62,  80,  140),
    'TRAFFIC':  QColor(230, 126, 34,  140),
    'ERASE':    QColor(189, 195, 199, 140),
}

# ── Cell icons (qtawesome, cache pixmap độ phân giải cao) ─────────────
_ICON_SRC_PX = 96   # render 1 lần ở 96px, scale mượt theo zoom

_CELL_ICONS = {
    config.STATE_ACCIDENT: ("fa5s.user-injured", "#FFFFFF"),  # Nạn nhân
    config.STATE_TRAFFIC:  ("fa5s.car-side",     "#FFFFFF"),  # Kẹt xe
    # STATE_HOSPITAL được vẽ riêng trong _draw_cell (số xe + dấu +)
}
# Icon ghost khi hover theo brush đang chọn
_BRUSH_ICONS = {
    'ACCIDENT': ("fa5s.user-injured", "#FFFFFF"),
    'HOSPITAL': ("fa5s.plus",         "#FFFFFF"),
    'TRAFFIC':  ("fa5s.car-side",     "#FFFFFF"),
    'WALL':     ("fa5s.th-large",     "#FFFFFF"),
    'ERASE':    ("fa5s.eraser",       "#FFFFFF"),
}

_PIX_CACHE: dict = {}


def _pix(name: str, color: str) -> QPixmap:
    """Pixmap cache cho icon qtawesome (key = name+color)."""
    key = (name, color)
    pm = _PIX_CACHE.get(key)
    if pm is None:
        pm = qta.icon(name, color=color).pixmap(_ICON_SRC_PX, _ICON_SRC_PX)
        _PIX_CACHE[key] = pm
    return pm

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

    cell_clicked            = pyqtSignal(int, int)
    hospital_requested      = pyqtSignal(int, int)
    hospital_edit_requested = pyqtSignal(int, int)
    hover_changed           = pyqtSignal(object)   # (row, col) hoặc None

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._ctrl = controller

        self._zoom  = 1.0
        self._pan_x = 20.0
        self._pan_y = 20.0
        self._panning    = False
        self._last_mouse = QPoint()
        self._hover_cell = None      # (row, col) ô đang hover
        self._inspector_highlight: list = []

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
                # Icon ghost theo brush đang chọn
                icon_def = _BRUSH_ICONS.get(self._ctrl.brush_mode)
                if icon_def:
                    pm = _pix(*icon_def)
                    s  = w * 0.6
                    painter.setOpacity(0.75)
                    painter.drawPixmap(
                        QRectF(x + (w - s) / 2, y + (w - s) / 2, s, s),
                        pm, QRectF(pm.rect()))
                    painter.setOpacity(1.0)

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

        # ── 4b. Inspector hover highlight ─────────────────────────
        if self._inspector_highlight:
            self._draw_overlay(
                painter,
                self._inspector_highlight,
                QColor(100, 200, 255, 75),
                cs, gap, r_abs,
            )

        # ── 5. Agent trails + positions ───────────────────────────
        for agent in self._ctrl.active_agents:
            self._draw_agent(painter, agent, cs)

        # ── 6. Rulers + Legend (không theo zoom/pan) ─────────────
        painter.setTransform(QTransform())
        self._draw_rulers(painter)
        self._draw_legend(painter)

        painter.end()

    # ── Legend renderer ───────────────────────────────────────────

    _LEGEND_ITEMS = [
        (QColor(231, 76,  60), "fa5s.user-injured", "Tai nạn"),
        (QColor(22, 160, 133), "fa5s.plus",         "Bệnh viện"),
        (QColor(230, 126, 34), "fa5s.car-side",     "Kẹt xe"),
        (QColor(44,  62,  80), "mdi.wall",           "Tường"),
        (QColor(52, 152, 219), "fa5s.ambulance",    "Xe cứu thương"),
    ]

    def _draw_legend(self, painter: QPainter):
        font = QFont("Segoe UI", 8)
        painter.setFont(font)
        fm = painter.fontMetrics()

        badge, gap_i, gap_g, pad = 18, 5, 14, 10
        width = pad * 2 + sum(
            badge + gap_i + fm.horizontalAdvance(label) + gap_g
            for _, _, label in self._LEGEND_ITEMS) - gap_g
        height = 30
        x0 = 10
        y0 = self.height() - height - 10
        if width + 20 > self.width():     # Canvas quá hẹp — ẩn legend
            return

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(22, 38, 63, 215)))
        painter.drawRoundedRect(QRectF(x0, y0, width, height), 8, 8)

        x = x0 + pad
        cy = y0 + height / 2
        for color, icon, label in self._LEGEND_ITEMS:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(
                QRectF(x, cy - badge / 2, badge, badge), 4, 4)
            pm = _pix(icon, "#FFFFFF")
            s  = badge * 0.66
            painter.drawPixmap(
                QRectF(x + (badge - s) / 2, cy - s / 2, s, s),
                pm, QRectF(pm.rect()))
            x += badge + gap_i
            painter.setPen(QColor(236, 240, 245))
            painter.drawText(
                QRectF(x, y0, fm.horizontalAdvance(label) + 2, height),
                Qt.AlignmentFlag.AlignVCenter, label)
            x += fm.horizontalAdvance(label) + gap_g

    # ── Ruler renderer (số cột/dòng bên ngoài grid) ─────────────

    def _draw_rulers(self, painter: QPainter):
        cs      = config.CELL_SIZE
        gs      = config.GRID_SIZE
        cell_px = cs * self._zoom

        if cell_px < 8:   # Quá nhỏ — ẩn ruler
            return

        font_px = max(7, min(11, int(cell_px * 0.30)))
        font = QFont("Consolas", -1)
        font.setPixelSize(font_px)
        font.setBold(True)
        painter.setFont(font)
        fm = painter.fontMetrics()
        painter.setPen(QColor(70, 95, 130, 200))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        th = fm.height()
        for c in range(gs):
            cx = self._pan_x + c * cell_px + cell_px / 2
            if cx < 0 or cx > self.width():
                continue
            label = str(c)
            tw = fm.horizontalAdvance(label)
            painter.drawText(
                QRectF(cx - tw / 2 - 1, 2, tw + 2, th),
                Qt.AlignmentFlag.AlignCenter, label)

        for r in range(gs):
            ry = self._pan_y + r * cell_px + cell_px / 2
            if ry < 0 or ry > self.height():
                continue
            label = str(r)
            tw = fm.horizontalAdvance(label)
            painter.drawText(
                QRectF(2, ry - th / 2, tw + 2, th),
                Qt.AlignmentFlag.AlignVCenter, label)

    # ── Hospital car count helper ─────────────────────────────────

    def _get_hospital_cars(self, r: int, c: int):
        for k, v in config.HOSPITAL_CONFIG.items():
            if tuple(v["pos"]) == (r, c):
                return self._ctrl.dispatcher.current_cars.get(k)
        return None

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

            # Icon / hoa văn theo loại ô
            if state == config.STATE_WALL:
                self._draw_brick_pattern(painter, rect, radius)
            elif state == config.STATE_HOSPITAL:
                # Số xe lớn ở giữa-dưới ô (thay thế dấu +)
                painter.save()
                cars = self._get_hospital_cars(r, c)
                label = str(cars) if cars is not None else "?"
                f = QFont("Segoe UI", -1, QFont.Weight.Bold)
                f.setPixelSize(max(5, int(w * 0.50)))
                painter.setFont(f)
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(
                    QRectF(x, y + w * 0.22, w, w * 0.78),
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                    label)
                painter.restore()
                # Dấu + nhỏ ở góc trên-trái biểu thị bệnh viện
                pm_plus = _pix("fa5s.plus", "#FFFFFF")
                icon_s = max(4.0, w * 0.30)
                painter.setOpacity(0.90)
                painter.drawPixmap(
                    QRectF(x + w * 0.06, y + w * 0.05, icon_s, icon_s),
                    pm_plus, QRectF(pm_plus.rect()))
                painter.setOpacity(1.0)
            else:
                icon_def = _CELL_ICONS.get(state)
                if icon_def:
                    pm = _pix(*icon_def)
                    s  = w * 0.62
                    tgt = QRectF(x + (w - s) / 2, y + (w - s) / 2, s, s)
                    painter.drawPixmap(tgt, pm, QRectF(pm.rect()))

            # --- VẼ H-TABLE (LRTA*) ---
            if hasattr(self._ctrl, 'global_h_table') and (r, c) in self._ctrl.global_h_table:
                h_val = self._ctrl.global_h_table[(r, c)]
                painter.save()
                f = QFont("Segoe UI", -1, QFont.Weight.Bold)
                f.setPixelSize(max(6, int(w * 0.25)))
                painter.setFont(f)
                painter.setPen(QColor(255, 215, 0, 220)) # Vàng cam (Gold)
                painter.drawText(
                    QRectF(x, y + 2, w - 4, w),
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
                    f"{h_val:.1f}"
                )
                painter.restore()

    @staticmethod
    def _draw_brick_pattern(painter: QPainter, rect: QRectF, radius: float):
        """Hoa văn gạch (mạch vữa sáng) trên ô tường."""
        painter.save()
        clip = QPainterPath()
        clip.addRoundedRect(rect, radius, radius)
        painter.setClipPath(clip)

        x, y, w = rect.x(), rect.y(), rect.width()
        painter.setPen(QPen(QColor(255, 255, 255, 38), max(0.8, w * 0.05)))
        y1, y2 = y + w / 3, y + 2 * w / 3
        painter.drawLine(QPointF(x, y1), QPointF(x + w, y1))
        painter.drawLine(QPointF(x, y2), QPointF(x + w, y2))
        # Mạch dọc so le như tường gạch thật
        painter.drawLine(QPointF(x + w * 0.50, y),  QPointF(x + w * 0.50, y1))
        painter.drawLine(QPointF(x + w * 0.25, y1), QPointF(x + w * 0.25, y2))
        painter.drawLine(QPointF(x + w * 0.75, y1), QPointF(x + w * 0.75, y2))
        painter.drawLine(QPointF(x + w * 0.50, y2), QPointF(x + w * 0.50, y + w))
        painter.restore()

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
        color = QColor(*agent.color)

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

        # Badge xe cứu thương (rounded rect màu agent + icon ambulance)
        row, col = agent.current_pos
        pad  = cs * 0.10
        rect = QRectF(col * cs + pad, row * cs + pad, cs - pad * 2, cs - pad * 2)
        rad  = cs * 0.22

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 70)))           # Drop shadow
        painter.drawRoundedRect(rect.translated(1, 2), rad, rad)

        painter.setBrush(QBrush(color))
        painter.drawRoundedRect(rect, rad, rad)
        painter.setPen(QPen(QColor(255, 255, 255, 200), max(0.8, cs * 0.04)))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, rad, rad)

        pm = _pix("fa5s.ambulance", "#FFFFFF")
        s  = rect.width() * 0.74
        painter.drawPixmap(
            QRectF(rect.center().x() - s / 2,
                   rect.center().y() - s / 2 + cs * 0.02, s, s),
            pm, QRectF(pm.rect()))

        # Đèn ưu tiên nhấp nháy — đổi màu đỏ/xanh theo mỗi bước di chuyển
        blink  = len(agent.path) % 2 == 0
        red    = QColor(231, 76, 60)
        blue   = QColor(52, 152, 219)
        r      = cs * 0.09
        painter.setPen(QPen(QColor(255, 255, 255, 180), max(0.6, cs * 0.02)))
        painter.setBrush(QBrush(red if blink else blue))
        painter.drawEllipse(QPointF(rect.left() + rect.width() * 0.30,
                                    rect.top() + r * 0.2), r, r)
        painter.setBrush(QBrush(blue if blink else red))
        painter.drawEllipse(QPointF(rect.left() + rect.width() * 0.70,
                                    rect.top() + r * 0.2), r, r)

    # ------------------------------------------------------------------ #
    #  Mouse                                                               #
    # ------------------------------------------------------------------ #

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
                self.hover_changed.emit(new_hover)
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._panning = False
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

    def leaveEvent(self, event):
        self._hover_cell = None
        self.hover_changed.emit(None)
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

    def set_inspector_highlight(self, cells: list):
        self._inspector_highlight = cells
        self.update()
