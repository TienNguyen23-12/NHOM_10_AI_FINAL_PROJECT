# 🚑 Multi-Agent Emergency Dispatch System

> **Final Project — Artificial Intelligence Course**
> Ho Chi Minh City University of Technology and Education (HCMUTE)

A real-time ambulance routing simulation that uses **A\* + Q-Learning** and **LRTA\* + Q-Learning** to find optimal paths from hospital depots to accident scenes across a dynamic urban grid map.

---

## Overview

This system simulates a city emergency dispatch center that automatically:

- Detects accident events on a 20×20 grid map
- Selects the nearest available hospital with spare ambulances
- Dispatches an ambulance using one of two AI pathfinding algorithms
- Navigates around walls, traffic jams, and other obstacles in real time
- Returns the ambulance to its home depot after reaching the accident scene

The simulation runs in an interactive **Pygame** dashboard where you can paint the map, trigger accidents, and watch the agents navigate live.

---

## Features

- **Dual AI Solver Engines** — switch between A\* + Q-Learning and LRTA\* + Q-Learning mid-simulation
- **Dynamic Cost Map** — traffic jam zones raise movement cost; accident cells carry extreme penalties
- **Q-Learning Brain** — a shared Q-table accumulates movement rewards across all agents, penalising slow or congested routes
- **Smart Dispatch Center** — evaluates the top-3 nearest hospitals by Manhattan distance, then picks the one with the lowest actual path cost
- **Return-to-Depot Logic** — after clearing an accident, each agent re-plans a fresh route home using the current map state
- **Rush Hour Simulation** — toggle between standard hours (12h) and peak hour (17h), which floods two horizontal corridors with traffic
- **Live AI Monitor Panel** — inspect the Q-table weights, LRTA\* heuristic memory, and active agent routes in real time
- **Fully Editable Map** — draw walls, hospitals, traffic zones, and accidents with brush tools; resize the window freely

---

## Algorithms

### A\* + Q-Learning (`AStarQAgent`)

A standard A\* search augmented with Q-value penalties. For each neighbour during expansion, the algorithm adds a Q-penalty to the movement cost when the learned Q-value for that action is negative. This biases the search away from historically costly directions without fully blocking them.

```
f(n) = g(n) + h(n)
g(n) = base_cost(n) + max(0, -Q(state, action))
h(n) = Manhattan distance to goal
```

The full path is pre-computed before the agent moves. On the return trip, a new path is computed from the accident scene back to the home depot.

### LRTA\* + Q-Learning (`LRTALearningAgent`)

Learning Real-Time A\* operates as a **one-step-at-a-time** online planner. At each tick the agent:

1. Evaluates all valid neighbours using `f = cost + H(neighbour)`
2. Updates the heuristic of the current cell: `H(current) = max(H(current), min_f)`
3. Moves to the best neighbour immediately

This means LRTA\* adapts to map changes (new walls, traffic shifts) in real time without re-running a full search. The heuristic table grows as the agent explores, making it progressively smarter across multiple missions.

---

## Project Structure

```
.
├── main.py                        # Entry point
├── config.py                      # Grid constants, colours, reward values
├── agents/
│   ├── base_agent.py              # Shared movement and drawing logic
│   ├── astar_q_agent.py           # A* + Q-Learning agent
│   └── lrtastar_q_agent.py        # LRTA* + Q-Learning agent
├── environment/
│   └── grid_map.py                # Grid state, cost function, traffic/accident management
├── ui/
│   ├── simulation_app.py          # Main app loop, event handling, rendering
│   ├── ui_manager.py              # Button layout and state management
│   ├── button.py                  # Reusable button widget
│   ├── logger_panel.py            # Bottom event log strip
│   └── inspector_panel.py        # Scrollable live AI monitor panel
└── utils/
    ├── q_learning.py              # Bellman-equation Q-table model
    └── dispatch_center.py         # Hospital selection and car allocation logic
```

---

## Installation

**Requirements:** Python 3.9+, Pygame

```bash
# Clone the repository
git clone <repo-url>
cd <repo-folder>

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
pip install pygame
```

---

## Running the Simulation

```bash
python main.py
```

---

## How to Use

### 1. Choose a Map Mode

| Option | Description |
|---|---|
| Custom Map Sandbox | Blank canvas — place everything manually |
| Generate Random Topology | Pre-built map with 3 hospitals and wall blocks |

### 2. Paint the Map (Brush Tools)

| Brush | Effect |
|---|---|
| Accident | Places an accident; immediately triggers dispatch |
| Hospital | Places a hospital depot (set fleet size in popup) |
| Block Wall | Impassable obstacle |
| Traffic Jam | High-cost zone (cost ×5) |
| Eraser | Removes any cell |

### 3. Control the Simulation

| Button | Action |
|---|---|
| System: A\* + Q | Use A\* with Q-penalties for all new dispatches |
| System: LRTA\* + Q | Use real-time LRTA\* for all new dispatches |
| Rush Hour (17h) | Toggle peak-hour traffic on rows 8 and 12 |
| Clear Map & Reset | Wipe the board and return to the main menu |

### 4. Inspect AI Internals

| Button | Shows |
|---|---|
| View Live Q-Table | Q-values per grid cell and direction |
| View Live H-Table | Heuristic memory of active LRTA\* agents |
| View Active Routes | Current start → goal and steps traversed |

**Scroll** the monitor panel with the mouse wheel. **Right-click drag** to pan the map.

---

## Configuration

All tunable constants live in `config.py`:

| Constant | Default | Description |
|---|---|---|
| `GRID_SIZE` | 20 | Grid dimensions (N×N) |
| `CELL_SIZE` | 25 | Pixel size of each cell |
| `REWARD_STEP` | -1 | Q penalty per normal move |
| `REWARD_TRAFFIC` | -10 | Q penalty for traffic cell |
| `REWARD_ACCIDENT` | -25 | Q penalty for accident cell |

Q-Learning hyperparameters are set in `utils/q_learning.py`:

| Parameter | Default | Description |
|---|---|---|
| `alpha` | 0.1 | Learning rate |
| `gamma` | 0.9 | Discount factor |

---

## Cell Cost Reference

| Cell Type | Movement Cost |
|---|---|
| Empty road | 1 |
| Traffic jam | 5 |
| Accident zone | 20 |
| Wall | Impassable |

---

## License

This project was developed for academic purposes as a final assignment for the Artificial Intelligence course at HCMUTE.
