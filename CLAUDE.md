# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Real-time ambulance routing simulation using **A* + Q-Learning** and **LRTA* + Q-Learning** on a dynamic 20×20 grid. Built with Python + Pygame as a final AI course project (HCMUTE). Entry point: `main.py`.

## Running the Project

```bash
pip install pygame
python main.py
```

No build step. Python 3.9+ required. The app runs at 30 FPS; agents move one step every ~200ms.

## Architecture

### Module Map

```
main.py                     → Entry point, instantiates SimulationApp
config.py                   → All constants: grid size, costs, rewards, colors, hyperparameters
agents/
  base_agent.py             → Shared state: position, path history, goal, draw()
  astar_q_agent.py          → A* with Q-penalties; pre-computes full path before moving
  lrtastar_q_agent.py       → LRTA*; online planner, updates heuristics as it moves
environment/
  grid_map.py               → 2D grid with 5 cell states; cost lookups; traffic toggle
utils/
  q_learning.py             → Shared Q-table (Bellman updates); save/load to q_brain_memory.json
  dispatch_center.py        → Picks best hospital per accident via A*; manages ambulance fleet
ui/
  simulation_app.py         → Main loop, event handling, rendering (~1000 lines)
  ui_manager.py             → Button groups and layout
  button.py                 → Reusable button widget
  logger_panel.py           → Color-coded event log (max 20 entries, FIFO)
  inspector_panel.py        → Scrollable right panel: Q-table / H-table / route views
```

### Key Data Flow

1. User places an accident cell → appended to `pending_accidents` queue
2. `manage_queue()` calls `dispatcher.evaluate_and_dispatch()` → A* from each hospital to pick lowest-cost route
3. Agent spawned (`AStarQAgent` or `LRTALearningAgent` per current mode)
4. Agent moves one step per tick; on arrival clears accident, sets `is_returning=True`, recomputes path home
5. On reaching home: `is_finished=True`, ambulance returned to hospital fleet

### Algorithm Details

**AStarQAgent** — `f(n) = g(n) + h(n)` where `g` includes Q-penalties to bias away from historically costly directions. Pre-computes the full path; re-plans dynamically if path becomes blocked.

**LRTALearningAgent** — One step at a time. Updates learned heuristic: `H(s) = max(H(s), cost + H(s'))`. Heuristics persist across missions for progressive improvement.

**Q-Learning** — Single shared Q-table across all agents. `Q(s,a) = r + γ * max(Q(s',a'))`. Persisted to `q_brain_memory.json`.

### Tunable Constants (`config.py`)

| Constant | Default | Role |
|---|---|---|
| `GAMMA` | 0.9 | Q-Learning discount factor |
| `LEARNING_RATE` | 0.5 | Q-update step size |
| `COST_EMPTY` | 1 | Movement cost on road |
| `COST_TRAFFIC` | 10 | Movement cost in traffic |
| `COST_ACCIDENT` | 50 | Movement cost through accident cell |
| `REWARD_GOAL` | 100 | Reward on reaching destination |
| `REWARD_STEP` | -1 | Per-step penalty |
| `REWARD_TRAFFIC` | -20 | Traffic penalty |

### Persistent Files

- `q_brain_memory.json` — Q-table saved across sessions (via Save/Load buttons)
- `custom_map_layout.json` — Saved custom map with hospital positions

### Cell States (defined in `config.py`)

`STATE_EMPTY`, `STATE_WALL`, `STATE_TRAFFIC`, `STATE_ACCIDENT`, `STATE_HOSPITAL`

### UI Interaction

- Left-click with brush tool active: place cell type
- Right-click + drag: pan map
- Mouse wheel: scroll inspector panel or zoom
- Rush hour simulation activates traffic on rows 8 & 12 at hour 17
- Grid can be resized 10–100 cells via Expand/Shrink buttons
