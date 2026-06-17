# Kiến trúc Project — Multi-Agent Emergency Dispatch System

> Mô phỏng điều phối xe cứu thương thời gian thực trên lưới động, dùng **A\* + Q-Learning** và **LRTA\* + Q-Learning**. Đồ án cuối kỳ môn Trí tuệ nhân tạo — HCMUTE.

---

## 1. Công nghệ sử dụng

| Thành phần | Công nghệ | Vai trò |
|---|---|---|
| Ngôn ngữ | **Python 3.9+** | Toàn bộ codebase |
| GUI Framework | **PyQt6** | Cửa sổ, widget, vẽ (QPainter), timer, signal/slot |
| Icon | **qtawesome** (FontAwesome 5) | Icon xe cứu thương, nạn nhân, bệnh viện, brush tools |
| Lưu trữ | **JSON** (thư viện chuẩn) | Lưu Q-table và bản đồ tùy chỉnh |
| Cấu trúc dữ liệu | **heapq** | Hàng đợi ưu tiên cho A\* |

> ⚠️ **Lưu ý về migration:** Project ban đầu viết bằng **Pygame**, sau đó đã được **migrate sang PyQt6** theo mô hình **MVC**. `CLAUDE.md` vẫn mô tả kiến trúc Pygame cũ — phần dưới đây phản ánh **trạng thái thực tế hiện tại**.

### Cài đặt & chạy
```bash
pip install PyQt6 qtawesome
python main.py
```

---

## 2. Mô hình kiến trúc tổng thể (MVC)

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                             │
│              (apply theme → AppWindow → exec)               │
└────────────────────────────┬────────────────────────────────┘
                             │
                ┌────────────▼─────────────┐
                │   ui/app_window.py       │  ← QMainWindow + QStackedWidget
                │   (MenuPage ⇄ SimPage)   │
                └──────┬────────────┬──────┘
                       │            │
          ┌────────────▼──┐    ┌────▼─────────────────┐
          │ ui/menu_page  │    │ ui/simulation_page   │  ← VIEW
          └───────────────┘    │ (lắp ráp các panel)  │
                               └────┬─────────────────┘
                                    │ signal/slot
                       ┌────────────▼────────────┐
                       │   ui/controller.py      │  ← CONTROLLER
                       │  SimulationController   │     (bộ não điều phối)
                       └────────────┬────────────┘
                                    │
        ┌──────────────┬────────────┼─────────────┬──────────────┐
        ▼              ▼            ▼             ▼              ▼
  environment/    agents/      utils/        utils/         config.py
  grid_map.py   *_q_agent.py  q_learning.py dispatch_center.py  ← MODEL
```

**Luồng dữ liệu cốt lõi:**
1. User click ô → `SimulationPage` bắt sự kiện → gọi `controller.place_accident()` → đẩy vào `pending_accidents`.
2. Mỗi tick (`QTimer` 200ms) → `controller.manage_queue()` → `DispatchCenter` chạy A\* từ mọi bệnh viện, chọn route rẻ nhất.
3. Sinh agent (`AStarQAgent` hoặc `LRTALearningAgent` tùy mode).
4. Mỗi tick agent đi 1 bước; tới tai nạn → chuyển `mission_phase` → đưa bệnh nhân tới viện → về trạm gốc.
5. Về trạm: `is_finished=True`, trả xe về fleet, ghi vào `completed_trips`.

---

## 3. Phân cấp folder & chức năng

```
NHOM_10_AI_FINAL_PROJECT/
├── main.py                  → Entry point: khởi tạo QApplication, theme, AppWindow
├── config.py                → TẤT CẢ hằng số: grid, state, màu, mode, hyperparameter AI
│
├── agents/                  → [MODEL] Các tác nhân tìm đường
│   ├── base_agent.py        → BaseAgent: vị trí, path, mission_phase, move_to(), thống kê
│   ├── astar_q_agent.py     → A* (g + h) có Q-penalty, tính trước full path, re-plan động
│   └── lrtastar_q_agent.py  → LRTA*: planner online, cập nhật heuristic khi đi
│
├── environment/             → [MODEL] Thế giới mô phỏng
│   └── grid_map.py          → Lưới 2D, 5 trạng thái ô, hàm cost, kẹt xe giờ cao điểm
│
├── utils/                   → [MODEL] Logic AI dùng chung
│   ├── q_learning.py        → QLearningModel: Q-table chia sẻ, Bellman, dynamic gamma, save/load
│   └── dispatch_center.py   → DispatchCenter: chọn bệnh viện tối ưu qua A*, quản lý đội xe
│
├── ui/                      → [VIEW + CONTROLLER]
│   ├── controller.py        → ⭐ SimulationController — bộ điều phối trung tâm (502 dòng)
│   ├── app_window.py        → QMainWindow, QStackedWidget, F11 fullscreen, xác nhận thoát
│   ├── menu_page.py         → Màn hình menu: branding + 2 nút chọn chế độ bản đồ
│   ├── simulation_page.py   → Màn hình mô phỏng: lắp ráp canvas + controls + inspector + logger
│   ├── grid_canvas.py       → ⭐ Vẽ lưới (QPainter): ô bo góc, icon, hover, xe, zoom/pan (555 dòng)
│   ├── controls_panel.py    → Panel 3 cột: Brush Tools | AI Controls | Monitor & Map
│   ├── qt_inspector_panel.py→ Panel phải: hiển thị Q-table / H-table / route / lịch sử
│   ├── qt_logger_panel.py   → Log sự kiện màu (PyQt6)
│   ├── hospital_dialog.py   → Dialog nhập số xe khi đặt bệnh viện
│   └── theme.py             → QSS global + Fusion palette (theme navy/đỏ cấp cứu)
│
├── q_brain_memory.json      → Q-table lưu giữa các phiên
├── custom_map_layout.json   → Bản đồ tùy chỉnh đã lưu (gồm vị trí bệnh viện)
│
└── ⚠️ FILE LEGACY (Pygame cũ — KHÔNG còn dùng bởi main.py):
    ├── ui/simulation_app.py   (717 dòng, vòng lặp Pygame cũ)
    ├── ui/ui_manager.py
    ├── ui/button.py
    ├── ui/inspector_panel.py
    └── ui/logger_panel.py
```

> **Code chết:** 5 file legacy trên còn import `pygame` và chỉ tham chiếu lẫn nhau, không nằm trong đồ thị phụ thuộc của `main.py`. Có thể xóa an toàn (nên kiểm tra lại trước khi xóa).

---

## 4. Các module quan trọng & code minh họa

### 4.1 `config.py` — Trung tâm cấu hình

```python
# Trạng thái ô
STATE_EMPTY, STATE_WALL, STATE_TRAFFIC, STATE_ACCIDENT, STATE_HOSPITAL = 0,1,2,3,4

# 4 chế độ thuật toán
MODE_ASTAR      = 1   # A* thuần (không Q)
MODE_LRTASTAR   = 2   # LRTA* thuần
MODE_ASTAR_Q    = 3   # A* + Q-Learning  (mặc định)
MODE_LRTASTAR_Q = 4   # LRTA* + Q-Learning

Q_WEIGHT      = 0.2   # Trọng số nhúng Q vào heuristic
GAMMA         = 0.9   # Discount factor
LEARNING_RATE = 0.5

COST_EMPTY, COST_TRAFFIC, COST_ACCIDENT = 1, 10, 50   # Chi phí di chuyển
REWARD_STEP, REWARD_TRAFFIC, REWARD_GOAL = -1, -20, 100  # Phần thưởng Q
```

### 4.2 `controller.py` — Bộ não điều phối (Controller)

Đây là **trái tim** của kiến trúc MVC. Dùng 3 `QTimer` tách biệt và phát `pyqtSignal` để View tự cập nhật (decoupling hoàn toàn khỏi logic).

```python
class SimulationController(QObject):
    # Signals → View lắng nghe để render lại
    log_added     = Signal(str)
    grid_updated  = Signal()
    fleet_updated = Signal()
    status_changed= Signal()

    def __init__(self, parent=None):
        ...
        self._sim_timer    = QTimer(self); self._sim_timer.setInterval(200)   # bước mô phỏng
        self._vis_timer    = QTimer(self); self._vis_timer.setInterval(120)   # animation tìm đường
        self._render_timer = QTimer(self); self._render_timer.setInterval(33) # ~30 FPS vẽ lại
```

**Vòng lặp chính mỗi tick:**
```python
def _on_sim_tick(self):
    if self.is_paused: return
    self.manage_queue()          # gán tai nạn cho xe
    if not self._vis_active:
        self.update_simulation() # di chuyển từng agent 1 bước
```

### 4.3 `astar_q_agent.py` — A\* lai Q-Learning

Điểm cốt lõi: hàm `g(n)` được cộng thêm **Q-penalty** để né hướng từng bị phạt trong quá khứ.

```python
new_g = g + base_cost + q_penalty   # q_penalty = -Q(s,a) * Q_WEIGHT  nếu Q<0
new_f = new_g + self.heuristic(neighbor)   # f = g + h (Manhattan)
```

**Máy trạng thái nhiệm vụ (mission_phase)** — đặc trưng thiết kế quan trọng:
```python
# phase 0: tới tai nạn → phase 1: tìm bệnh viện rẻ nhất (quét A* tới mọi viện)
# phase 1: thả bệnh nhân → phase 2: quay về trạm gốc
# phase 2: về tới nơi → is_finished=True, trả xe về fleet
```

A\* còn có 2 phiên bản tìm đường:
- `search_path_with_q()` — tính 1 lần ra full path.
- `search_path_generator()` — phiên bản **generator** `yield` từng bước để animation trực quan hóa quá trình mở rộng node.

### 4.4 `lrtastar_q_agent.py` — LRTA\* online

Khác A\*: chỉ nhìn 4 ô lân cận, đi từng bước, **cập nhật heuristic học được** ngay khi di chuyển:

```python
f_value = base_cost + q_pen + self.get_h(neighbor)   # chọn neighbor có f nhỏ nhất
...
self.h_table[current] = max(self.get_h(current), min_f)   # quy tắc cập nhật LRTA*
```
H-table **bền vững qua các nhiệm vụ** → xe ngày càng "khôn" hơn.

### 4.5 `q_learning.py` — Q-table chia sẻ + Dynamic Gamma

Một Q-table duy nhất dùng chung cho mọi agent. Điểm sáng tạo: **gamma tăng dần theo tuổi đời AI** (nhìn ngắn lúc đầu → nhìn xa khi trưởng thành).

```python
def update_q_value(self, state, action_idx, reward, next_state):
    self.total_steps += 1
    self.gamma = min(self.gamma_max, self.gamma_init + self.growth_rate * self.total_steps)
    best_next_q = max(self.q_table[next_state])
    self.q_table[state][action_idx] = reward + (self.gamma * best_next_q)  # Bellman, alpha=1
```

### 4.6 `dispatch_center.py` — Điều phối đội xe

Khi có tai nạn, chạy A\* từ **mọi bệnh viện còn xe** và chọn nơi có chi phí thấp nhất:

```python
def evaluate_and_dispatch(self, acc_pos, grid_map):
    for h_name, h_info in self.hospitals.items():
        if self.current_cars.get(h_name, 0) <= 0: continue
        path, cost = self._calculate_cost(h_info["pos"], acc_pos, grid_map)
        if cost < best_cost: best_hospital, best_path = h_name, path
    self.current_cars[best_hospital] -= 1   # trừ 1 xe khỏi trạm
    return best_hospital, best_path
```

### 4.7 `grid_map.py` — Môi trường lưới

```python
def get_cost(self, pos):       # Hàm chi phí động
    if self.grid[r][c] == STATE_TRAFFIC:  return COST_TRAFFIC   # 10
    if self.grid[r][c] == STATE_ACCIDENT: return COST_ACCIDENT  # 50
    return COST_EMPTY                                            # 1

def set_traffic_jam(self, hour):   # Giờ cao điểm 17-18h → kẹt xe hàng 8 & 12
    if 17 <= hour <= 18: ...
```

### 4.8 `grid_canvas.py` — Lớp render (QPainter thuần)

Vẽ toàn bộ lưới bằng `QPainter`: ô bo góc + gradient, icon qtawesome cache theo pixmap, hover preview, xe cứu thương với đèn ưu tiên, hỗ trợ **zoom (0.12–14×) và pan**. Phát signal `cell_clicked`, `hospital_requested`, `hover_changed` lên `SimulationPage`.

---

## 5. Tương tác người dùng

| Thao tác | Chức năng |
|---|---|
| Left-click (brush active) | Đặt tai nạn / bệnh viện / tường / kẹt xe / xóa |
| Phím `1`–`5` | Chọn brush (Accident/Hospital/Wall/Traffic/Erase) |
| `A` / `L` | Chuyển mode A\*+Q / LRTA\*+Q |
| `Space` | Pause/Resume |
| `V` | Bật/tắt trực quan hóa quá trình tìm đường |
| `Ctrl+H` | Bật/tắt giờ cao điểm (kẹt xe) |
| `Q`/`H`/`Ctrl+R`/`Ctrl+T` | Xem Q-table / H-table / routes / lịch sử chuyến |
| `Ctrl+S/O` | Lưu/tải bản đồ · `Ctrl+Shift+S/O` lưu/tải Q-brain |
| `+`/`-` | Phóng to/thu nhỏ lưới (10–100 ô) · `0` reset view |
| `F11` | Fullscreen |

---

## 6. File lưu trữ bền vững

- **`q_brain_memory.json`** — Q-table (key = vị trí ô, value = [Q lên, xuống, trái, phải]).
- **`custom_map_layout.json`** — kích thước lưới + grid + cấu hình bệnh viện.

---

*Tài liệu sinh tự động từ phân tích codebase — phản ánh nhánh `NhanNguyen` tại thời điểm tổng hợp.*
