# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Real-time ambulance routing simulation using **A* + Q-Learning** and **LRTA* + Q-Learning** on a dynamic 20×20 grid. Built with **Python + PyQt6** (migrated from Pygame) as a final AI course project (HCMUTE). Entry point: `main.py`.

## Running the Project

```bash
pip install PyQt6 qtawesome
python main.py
```

No build step. Python 3.9+ required. Simulation ticks every 200ms via QTimer.

## Architecture

### Module Map

```
main.py                        → Entry point: QApplication, AppWindow, theme.apply()
config.py                      → All constants: grid size, costs, rewards, colors, hyperparameters
agents/
  base_agent.py                → Shared state: position, path history, goal (no pygame drawing)
  astar_q_agent.py             → A* with Q-penalties; pre-computes full path before moving
  lrtastar_q_agent.py          → LRTA*; online planner, updates heuristics as it moves
environment/
  grid_map.py                  → 2D grid with 5 cell states; cost lookups; traffic toggle
utils/
  q_learning.py                → Shared Q-table (Bellman updates); save/load to q_brain_memory.json
  dispatch_center.py           → Picks best hospital per accident via A*; manages ambulance fleet
ui/
  app_window.py                → QMainWindow + QStackedWidget (MENU / SIMULATION screens)
  menu_page.py                 → MenuPage QWidget; logo ambulance đỏ + WA_StyledBackground
  simulation_page.py           → SimulationPage: connects Controller ↔ all views
  controller.py                → SimulationController (QObject); toàn bộ logic + 2 QTimer
  grid_canvas.py               → QPainter rendering; qtawesome icons; legend góc dưới-trái
  controls_panel.py            → QScrollArea chứa button groups bên trái
  qt_inspector_panel.py        → QListWidget hiển thị Q-table / H-table / route info
  qt_logger_panel.py           → QListWidget màu sắc, tối đa 20 dòng, FIFO
  hospital_dialog.py           → QDialog thêm/xóa bệnh viện
  theme.py                     → Dark navy (#16263F) + Fusion palette; hover đỏ khẩn cấp
```

### Key Data Flow

1. User places an accident cell → appended to `pending_accidents` queue in `SimulationController`
2. `_sim_timer` (200ms) triggers `_on_sim_tick()` → `manage_queue()` → `dispatcher.evaluate_and_dispatch()`
3. Agent spawned (`AStarQAgent` or `LRTALearningAgent` per `current_mode`)
4. Agent moves one step per tick; on arrival clears accident, sets `is_returning=True`, recomputes path home
5. On reaching home: `is_finished=True`, ambulance returned to hospital fleet
6. Controller emits `grid_updated` / `log_added` / `fleet_updated` signals → views re-render

### Algorithm Details

**AStarQAgent** — `f(n) = g(n) + h(n)` where `g` includes Q-penalties (`Q_WEIGHT = 0.2`) to bias away from historically costly directions. Pre-computes the full path; re-plans dynamically if path becomes blocked.

**LRTALearningAgent** — One step at a time. Updates learned heuristic: `H(s) = max(H(s), cost + H(s'))`. Heuristics persist across missions for progressive improvement via `global_h_table` in controller.

**Q-Learning** — Single shared Q-table across all agents. `Q(s,a) = r + γ * max(Q(s',a'))`. Persisted to `q_brain_memory.json`.

**Algorithm modes** (defined in `config.py`):
- `MODE_ASTAR = 1` — Pure A* (no Q-Learning)
- `MODE_LRTASTAR = 2` — Pure LRTA* (no Q-Learning)
- `MODE_ASTAR_Q = 3` — A* + Q-Learning (default)
- `MODE_LRTASTAR_Q = 4` — LRTA* + Q-Learning

### Tunable Constants (`config.py`)

| Constant | Default | Role |
|---|---|---|
| `GAMMA` | 0.9 | Q-Learning discount factor |
| `LEARNING_RATE` | 0.5 | Q-update step size |
| `Q_WEIGHT` | 0.2 | Q-penalty weight in A* heuristic |
| `COST_EMPTY` | 1 | Movement cost on road |
| `COST_TRAFFIC` | 5 | Movement cost in traffic |
| `COST_ACCIDENT` | 50 | Movement cost through accident cell |
| `REWARD_GOAL` | 100 | Reward on reaching destination |
| `REWARD_STEP` | -1 | Per-step penalty |
| `REWARD_TRAFFIC` | -20 | Traffic penalty |
| `DEFAULT_FLEET_SIZE` | 3 | Ambulances per hospital on creation |

### Persistent Files

- `q_brain_memory.json` — Q-table saved across sessions (via Save/Load buttons)
- `custom_map_layout.json` — Saved custom map with hospital positions

### Cell States (defined in `config.py`)

`STATE_EMPTY (0)`, `STATE_WALL (1)`, `STATE_TRAFFIC (2)`, `STATE_ACCIDENT (3)`, `STATE_HOSPITAL (4)`

### UI & Rendering Notes

- `grid_canvas.py` uses **qtawesome** icons: `fa5s.user-injured` (nạn nhân), `fa5s.plus` (bệnh viện), `fa5s.car-side` (traffic), `fa5s.ambulance` (agent). Module-level `_PIX_CACHE` caches pixmaps at 96px.
- Hospital color trong GridCanvas: teal `(22, 160, 133)` — **không** dùng `config.THEME` (vẫn giữ màu tím cũ chỉ cho legacy code).
- `menu_page.py` phải set `setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)` để QSS background hoạt động trên QWidget subclass.
- `SimulationController` có 2 timer: `_sim_timer` (200ms, logic tick) và `_vis_timer` (120ms, search visualization).

### UI Interaction

- Left-click với brush tool: đặt loại ô (accident, wall, traffic, hospital, erase)
- Right-click + drag: pan map
- Mouse wheel: scroll inspector hoặc zoom
- Rush hour: tự động bật traffic giờ cao điểm
- Grid có thể resize 10–100 ô qua Expand/Shrink
