# ui/controller.py
# MVC Controller layer: chứa toàn bộ logic nghiệp vụ của simulation.
# Thay thế SimulationApp (Pygame) bằng QObject thuần, không import pygame.
# Views (GridCanvas, LoggerPanel...) kết nối qua Qt Signals.

import json
import os
from PyQt6.QtCore import QObject, pyqtSignal as Signal, QTimer

import config
from environment.grid_map import GridMap
from utils.q_learning import QLearningModel
from utils.dispatch_center import DispatchCenter
from agents.astar_q_agent import AStarQAgent
from agents.lrtastar_q_agent import LRTALearningAgent


class _LoggerProxy:
    """Proxy nhận add_log() từ agents và forward lên Qt signal.
    Giữ nguyên interface cũ (app_instance.logger.add_log) để không sửa agent code."""
    def __init__(self, signal: Signal):
        self._signal = signal

    def add_log(self, message: str):
        self._signal.emit(message)


class SimulationController(QObject):
    """Controller giữ toàn bộ trạng thái và logic simulation.

    Agents tiếp tục gọi self.logger.add_log(), self.dispatcher,
    self.global_q_brain, self.visualize_search — giống interface cũ của
    SimulationApp — nên agent code không cần thay đổi.
    """

    # --- Signals cho View đăng ký ---
    log_added      = Signal(str)   # LoggerPanel listen
    grid_updated   = Signal()      # GridCanvas.update() trigger repaint
    fleet_updated  = Signal()      # Fleet status label
    status_changed = Signal()      # Status bar text

    def __init__(self, parent=None):
        super().__init__(parent)

        # Proxy logger — agents gọi self.logger.add_log() như cũ
        self.logger = _LoggerProxy(self.log_added)

        # --- Model layer ---
        self.env = GridMap()
        self.env.grid = [[config.STATE_EMPTY] * config.GRID_SIZE
                         for _ in range(config.GRID_SIZE)]
        config.HOSPITAL_CONFIG.clear()

        self.global_q_brain = QLearningModel()
        self.dispatcher = DispatchCenter(self.global_q_brain)
        self.dispatcher.reset_resources()

        self.active_agents: list = []
        self.pending_accidents: list = []

        # --- Trạng thái simulation ---
        self.is_paused        = False
        self.current_mode     = config.MODE_ASTAR_Q
        self.current_hour     = 12
        self.brush_mode       = 'ACCIDENT'
        self.visualize_search = False

        # Dữ liệu visualizer (dùng bởi GridCanvas khi vẽ overlay)
        self.dispatch_generator  = None
        self.dispatch_vis_data   = None   # (open_set, visited, path, h_name)
        self._vis_active         = False  # True khi đang animate

        # --- Qt Timers (thay game loop của Pygame) ---
        # Mỗi 200ms: bước logic simulation (agent di chuyển)
        self._sim_timer = QTimer(self)
        self._sim_timer.setInterval(200)
        self._sim_timer.timeout.connect(self._on_sim_tick)

        # Mỗi 120ms: step visualizer frame (A* search animation)
        self._vis_timer = QTimer(self)
        self._vis_timer.setInterval(120)
        self._vis_timer.timeout.connect(self._on_vis_tick)

        # Mỗi 33ms (~30 FPS): trigger repaint của GridCanvas
        self._render_timer = QTimer(self)
        self._render_timer.setInterval(33)
        self._render_timer.timeout.connect(self.grid_updated)

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    def start_timers(self):
        self._sim_timer.start()
        self._vis_timer.start()
        self._render_timer.start()

    def stop_timers(self):
        self._sim_timer.stop()
        self._vis_timer.stop()
        self._render_timer.stop()

    # ------------------------------------------------------------------ #
    #  Timer callbacks                                                     #
    # ------------------------------------------------------------------ #

    def _on_sim_tick(self):
        """Chạy mỗi 200ms: quản lý hàng chờ và bước logic agents."""
        if self.is_paused:
            return
        self.manage_queue()
        # Không chạy simulation khi đang visualize để không bỏ qua animation
        if not self._vis_active:
            self.update_simulation()

    def _on_vis_tick(self):
        """Chạy mỗi 120ms: step một frame của search visualizer."""
        if self.is_paused:
            return
        self._vis_active = self.update_visualizer()

    # ------------------------------------------------------------------ #
    #  Core simulation logic (giữ nguyên so với SimulationApp cũ)         #
    # ------------------------------------------------------------------ #

    def manage_queue(self):
        if self.dispatch_generator is not None:
            return
        if not self.pending_accidents:
            return
        if sum(self.dispatcher.current_cars.values()) <= 0:
            return

        acc_pos = self.pending_accidents[0]

        if self.visualize_search:
            self.logger.add_log(f"[DISPATCH] Đang quét thầu cho tai nạn tại {acc_pos}...")
            self.dispatch_generator = self.dispatcher.evaluate_generator(acc_pos, self.env)
        else:
            h_name, path = self.dispatcher.evaluate_and_dispatch(acc_pos, self.env)
            if h_name and path:
                agent = self._create_agent(config.HOSPITAL_CONFIG[h_name]["pos"], acc_pos)
                agent.calculated_path = path
                self.active_agents.append(agent)
                self.pending_accidents.pop(0)
                self.logger.add_log(
                    f"-> [DISPATCH] Đã chốt xe từ trạm {h_name}. "
                    f"Còn {len(self.pending_accidents)} ca chờ.")
                self.fleet_updated.emit()
            else:
                self.pending_accidents.pop(0)
                self.logger.add_log(
                    f"[DISPATCH] TỪ CHỐI: Lỗi chặn đường đến {acc_pos}! Đã hủy ca.")

    def update_visualizer(self) -> bool:
        """Step một frame animation. Trả về True nếu vẫn còn đang animate."""
        # --- Dispatch visualizer (quét từng bệnh viện) ---
        if self.dispatch_generator:
            try:
                open_set, visited, current_path, h_name, is_done = next(self.dispatch_generator)
                self.dispatch_vis_data = (open_set, visited, current_path, h_name)

                if is_done:
                    self.dispatch_generator = None
                    self.dispatch_vis_data  = None
                    if h_name and current_path:
                        agent = self._create_agent(
                            config.HOSPITAL_CONFIG[h_name]["pos"], current_path[-1])
                        if self.visualize_search and self.current_mode == config.MODE_ASTAR_Q:
                            agent.search_generator = agent.search_path_generator(self.env)
                        else:
                            agent.calculated_path = current_path
                        self.active_agents.append(agent)
                        self.dispatcher.current_cars[h_name] -= 1
                        if self.pending_accidents:
                            self.pending_accidents.pop(0)
                        self.logger.add_log(
                            f"-> [DISPATCH] Đã chốt xe từ trạm {h_name}. "
                            f"Còn {len(self.pending_accidents)} ca chờ.")
                        self.fleet_updated.emit()
                    else:
                        if self.pending_accidents:
                            self.pending_accidents.pop(0)
                        self.logger.add_log(
                            "[DISPATCH] TỪ CHỐI: Các trạm đã hết xe hoặc kẹt đường!")
            except StopIteration:
                self.dispatch_generator = None
            return True

        # --- Agent search visualizer (A* path animation) ---
        for agent in self.active_agents:
            if hasattr(agent, 'search_generator') and agent.search_generator:
                try:
                    open_set, visited, current_path, is_done = next(agent.search_generator)
                    agent.vis_open_set = open_set
                    agent.vis_visited  = visited
                    agent.vis_path     = current_path
                    if is_done:
                        agent.calculated_path  = current_path
                        agent.search_generator = None
                except StopIteration:
                    agent.search_generator = None
                return True

        return False

    def update_simulation(self):
        """Bước logic: di chuyển tất cả agent một ô, cập nhật Q-table."""
        for agent in self.active_agents:
            if agent.is_finished:
                continue
            old_pos = agent.current_pos

            if isinstance(agent, LRTALearningAgent):
                agent.update_route_realtime_with_return(self.env, self)
            else:
                agent.update_astar_return_logic(self.env, self)

            if agent.current_pos != old_pos and isinstance(agent, AStarQAgent):
                dr = agent.current_pos[0] - old_pos[0]
                dc = agent.current_pos[1] - old_pos[1]
                if (dr, dc) in self.global_q_brain.actions:
                    action_idx = self.global_q_brain.actions.index((dr, dc))
                    reward = -self.env.get_cost(agent.current_pos)
                    if agent.current_pos == agent.goal_pos:
                        reward = config.REWARD_GOAL
                    self.global_q_brain.update_q_value(old_pos, action_idx, reward, agent.current_pos)

        # Dọn agent đã hoàn thành (không xóa trong loop để tránh lỗi index)
        self.active_agents = [a for a in self.active_agents if not a.is_finished]
        self.fleet_updated.emit()

    # ------------------------------------------------------------------ #
    #  Map setup                                                           #
    # ------------------------------------------------------------------ #

    def setup_default_map(self):
        config.GRID_SIZE = 20
        self.env.grid = [[config.STATE_EMPTY] * config.GRID_SIZE
                         for _ in range(config.GRID_SIZE)]
        config.HOSPITAL_CONFIG.clear()
        config.HOSPITAL_CONFIG.update({
            "HOSPITAL_1": {"pos": (2, 2),   "max_cars": 2},
            "HOSPITAL_2": {"pos": (2, 17),  "max_cars": 3},
            "HOSPITAL_3": {"pos": (17, 9),  "max_cars": 2},
        })
        self.env.generate_default_map()
        self.dispatcher.hospitals = config.HOSPITAL_CONFIG
        self.dispatcher.reset_resources()
        self.active_agents.clear()
        self.pending_accidents.clear()
        self.logger.add_log("[SYSTEM] Random node network generated.")
        self.fleet_updated.emit()
        self.grid_updated.emit()

    def setup_sandbox_map(self):
        config.GRID_SIZE = 20
        self.env.grid = [[config.STATE_EMPTY] * config.GRID_SIZE
                         for _ in range(config.GRID_SIZE)]
        config.HOSPITAL_CONFIG.clear()
        self.dispatcher.reset_resources()
        self.active_agents.clear()
        self.pending_accidents.clear()
        self.logger.add_log("[SYSTEM] Đã kích hoạt chế độ Sandbox Map.")
        self.fleet_updated.emit()
        self.grid_updated.emit()

    def clear_map(self):
        self.active_agents.clear()
        self.env.accidents_pool.clear()
        self.pending_accidents.clear()
        config.HOSPITAL_CONFIG.clear()
        self.dispatcher.reset_resources()
        self.env.grid = [[config.STATE_EMPTY] * config.GRID_SIZE
                         for _ in range(config.GRID_SIZE)]
        self.fleet_updated.emit()
        self.grid_updated.emit()

    # ------------------------------------------------------------------ #
    #  Cell interaction (từ GridCanvas mouse events)                       #
    # ------------------------------------------------------------------ #

    def place_accident(self, row: int, col: int) -> bool:
        if self.env.grid[row][col] != config.STATE_EMPTY:
            return False
        pos = (row, col)
        self.env.grid[row][col] = config.STATE_ACCIDENT
        self.env.accidents_pool.append(pos)
        self.pending_accidents.append(pos)
        self.logger.add_log(
            f"[ALERT] Tai nạn tại {pos} đã được đưa vào HÀNG CHỜ ({len(self.pending_accidents)}).")
        return True

    def place_wall(self, row: int, col: int) -> bool:
        if self.env.grid[row][col] != config.STATE_EMPTY:
            return False
        self.env.grid[row][col] = config.STATE_WALL
        return True

    def place_traffic(self, row: int, col: int) -> bool:
        if self.env.grid[row][col] != config.STATE_EMPTY:
            return False
        self.env.grid[row][col] = config.STATE_TRAFFIC
        return True

    def erase_cell(self, row: int, col: int):
        curr = self.env.grid[row][col]
        if curr == config.STATE_HOSPITAL:
            key = next((k for k, v in config.HOSPITAL_CONFIG.items()
                        if v["pos"] == (row, col)), None)
            if key:
                config.HOSPITAL_CONFIG.pop(key)
                self.dispatcher.current_cars.pop(key, None)
        elif curr == config.STATE_ACCIDENT and (row, col) in self.env.accidents_pool:
            self.env.accidents_pool.remove((row, col))
            if (row, col) in self.pending_accidents:
                self.pending_accidents.remove((row, col))
        self.env.grid[row][col] = config.STATE_EMPTY
        self.fleet_updated.emit()

    def place_hospital(self, row: int, col: int, car_count: int):
        name = f"HOSPITAL_{row}_{col}"
        config.HOSPITAL_CONFIG[name] = {"pos": (row, col), "max_cars": car_count}
        self.dispatcher.hospitals = config.HOSPITAL_CONFIG
        self.dispatcher.current_cars[name] = car_count
        self.env.grid[row][col] = config.STATE_HOSPITAL
        self.logger.add_log(f"[STATION] Setup depot {name} with: {car_count} units.")
        self.fleet_updated.emit()

    # ------------------------------------------------------------------ #
    #  Action toggles (từ ControlsPanel buttons)                          #
    # ------------------------------------------------------------------ #

    def set_mode(self, mode: int):
        self.current_mode = mode
        label = 'A* + Q' if mode == config.MODE_ASTAR_Q else 'LRTA* + Q'
        self.logger.add_log(f"[SYSTEM] Switched execution to: {label}")
        self.status_changed.emit()

    def set_brush(self, mode: str):
        self.brush_mode = mode

    def toggle_pause(self) -> bool:
        self.is_paused = not self.is_paused
        self.logger.add_log(
            f"[SYSTEM] Simulation {'PAUSED' if self.is_paused else 'RESUMED'}.")
        return self.is_paused

    def toggle_rush_hour(self) -> int:
        self.current_hour = 17 if self.current_hour == 12 else 12
        self.env.set_traffic_jam(self.current_hour)
        self.logger.add_log(f"[TRAFFIC] Timetable altered to {self.current_hour}h00.")
        self.status_changed.emit()
        return self.current_hour

    def toggle_visualizer(self) -> bool:
        self.visualize_search = not self.visualize_search
        if not self.visualize_search:
            self._flush_visualizer()
        return self.visualize_search

    def _flush_visualizer(self):
        """Drain generators ngay khi visualizer bị tắt (không để lag)."""
        if self.dispatch_generator:
            try:
                while True:
                    _, _, path, h_name, is_done = next(self.dispatch_generator)
                    if is_done:
                        if h_name and path:
                            agent = self._create_agent(
                                config.HOSPITAL_CONFIG[h_name]["pos"], path[-1])
                            agent.calculated_path = path
                            self.active_agents.append(agent)
                            self.dispatcher.current_cars[h_name] -= 1
                            if self.pending_accidents:
                                self.pending_accidents.pop(0)
                            self.logger.add_log(
                                f"-> [DISPATCH] Xả đệm: Đã chốt xe từ trạm {h_name}.")
                        else:
                            if self.pending_accidents:
                                self.pending_accidents.pop(0)
                        break
            except StopIteration:
                pass
            self.dispatch_generator = None
            self.dispatch_vis_data   = None

        for agent in self.active_agents:
            if hasattr(agent, 'search_generator') and agent.search_generator:
                try:
                    while True:
                        _, _, path, is_done = next(agent.search_generator)
                        if is_done:
                            agent.calculated_path = path
                            break
                except StopIteration:
                    pass
                agent.search_generator = None

    # ------------------------------------------------------------------ #
    #  Map I/O & resize                                                    #
    # ------------------------------------------------------------------ #

    def resize_map(self, delta: int) -> bool:
        new_size = config.GRID_SIZE + delta
        if new_size < config.MIN_GRID or new_size > config.MAX_GRID:
            self.logger.add_log("[ERROR] Kích thước bản đồ đạt giới hạn an toàn (10-100).")
            return False

        new_grid = [[config.STATE_EMPTY] * new_size for _ in range(new_size)]
        min_s = min(config.GRID_SIZE, new_size)
        for r in range(min_s):
            for c in range(min_s):
                new_grid[r][c] = self.env.grid[r][c]

        self.env.accidents_pool = [
            p for p in self.env.accidents_pool if p[0] < new_size and p[1] < new_size]
        self.pending_accidents = [
            p for p in self.pending_accidents if p[0] < new_size and p[1] < new_size]

        for h in [n for n, i in config.HOSPITAL_CONFIG.items()
                  if i["pos"][0] >= new_size or i["pos"][1] >= new_size]:
            config.HOSPITAL_CONFIG.pop(h)
            self.dispatcher.current_cars.pop(h, None)

        # Xóa agents đang ở vị trí ngoài bản đồ mới — tránh IndexError tick tiếp theo
        removed = [a for a in self.active_agents
                   if a.current_pos[0] >= new_size or a.current_pos[1] >= new_size]
        if removed:
            self.logger.add_log(
                f"[SYSTEM] Đã hủy {len(removed)} agent ngoài vùng bản đồ mới.")
        self.active_agents = [a for a in self.active_agents
                              if a not in removed]

        self.env.grid    = new_grid
        config.GRID_SIZE = new_size
        self.logger.add_log(
            f"[SYSTEM] Kích thước lưới bản đồ được điều chỉnh thành {new_size}x{new_size}.")
        self.fleet_updated.emit()
        self.grid_updated.emit()
        return True

    def save_map(self, filepath: str = "custom_map_layout.json"):
        data = {
            "grid_size": config.GRID_SIZE,
            "grid":      self.env.grid,
            "hospitals": config.HOSPITAL_CONFIG,
        }
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f)
            self.logger.add_log(f"[SYSTEM] Đã lưu bản đồ thiết kế xuống file: {filepath}.")
        except Exception as e:
            self.logger.add_log(f"[ERROR] Lỗi lưu bản đồ: {e}")

    def load_map(self, filepath: str = "custom_map_layout.json"):
        if not os.path.exists(filepath):
            self.logger.add_log(f"[ERROR] Không tìm thấy file bản đồ {filepath}.")
            return
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.active_agents.clear()
            self.env.accidents_pool.clear()
            self.pending_accidents.clear()
            config.GRID_SIZE = data["grid_size"]
            self.env.grid    = data["grid"]
            config.HOSPITAL_CONFIG.clear()
            for k, v in data["hospitals"].items():
                config.HOSPITAL_CONFIG[k] = {"pos": tuple(v["pos"]), "max_cars": v["max_cars"]}
            for r in range(config.GRID_SIZE):
                for c in range(config.GRID_SIZE):
                    if self.env.grid[r][c] == config.STATE_ACCIDENT:
                        self.env.accidents_pool.append((r, c))
                        self.pending_accidents.append((r, c))
            self.dispatcher.hospitals = config.HOSPITAL_CONFIG
            self.dispatcher.reset_resources()
            self.logger.add_log(f"[SYSTEM] Đã tải thành công bản đồ từ {filepath}.")
            self.fleet_updated.emit()
            self.grid_updated.emit()
        except Exception as e:
            self.logger.add_log(f"[ERROR] Lỗi tải bản đồ: {e}")

    def save_q_brain(self):
        self.global_q_brain.save_brain()
        self.logger.add_log("[SYSTEM] AI Brain saved to JSON.")

    def load_q_brain(self):
        self.global_q_brain.load_brain()
        self.logger.add_log("[SYSTEM] Restored AI Brain from JSON.")

    # ------------------------------------------------------------------ #
    #  Helpers cho View                                                    #
    # ------------------------------------------------------------------ #

    def get_status_text(self) -> str:
        mode = ('A* + Q-Learning' if self.current_mode == config.MODE_ASTAR_Q
                else 'LRTA* + Q-Learning')
        return (f"Timetable: {self.current_hour}h00  |  "
                f"Solver Engine: {mode}  |  "
                f"Queue: {len(self.pending_accidents)} waiting")

    def get_fleet_text(self) -> str | None:
        if not self.dispatcher.current_cars:
            return None
        parts = []
        for k, v in self.dispatcher.current_cars.items():
            pos = self.dispatcher.hospitals.get(k, {}).get("pos")
            label = f"H({pos[0]},{pos[1]})" if pos else k
            parts.append(f"{label}: {v} units")
        return "   |   ".join(parts)

    # ------------------------------------------------------------------ #
    #  Inspector data builders                                             #
    # ------------------------------------------------------------------ #

    def build_q_table_lines(self) -> list[str]:
        lines = ["--- LIVE BACKEND Q-TABLE METRICS ---"]
        if not self.global_q_brain.q_table:
            lines.append("No learned Q-weights in memory yet.")
            return lines
        for state, values in self.global_q_brain.q_table.items():
            lines.append(f"Cell {state} -> Q:{[round(v, 2) for v in values]}")
        return lines

    def build_h_table_lines(self) -> list[str]:
        lines = ["--- LIVE LRTA* HEURISTIC FIELDS ---"]
        lrta_agents = [a for a in self.active_agents if hasattr(a, 'h_table')]
        if not lrta_agents:
            lines.append("No active LRTA* agents on map.")
            return lines
        for idx, car in enumerate(lrta_agents):
            lines.append(f"[Agent #{idx + 1}] Memory states:")
            for state, h_val in car.h_table.items():
                lines.append(f"  Node {state} -> H: {round(h_val, 1)}")
        return lines

    def build_paths_lines(self) -> list[str]:
        lines = ["--- ACTIVE MISSION PATH ROUTING ---"]
        if not self.active_agents:
            lines.append("Fleet is currently stationed at depots.")
            return lines
        for idx, car in enumerate(self.active_agents):
            kind = "A*" if isinstance(car, AStarQAgent) else "LRTA*"
            lines.append(f"Car #{idx + 1} [{kind}]:")
            lines.append(f"  {car.start_pos} -> {car.goal_pos}")
            lines.append(f"  Traversed: {len(car.path)} blocks.")
        return lines

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _create_agent(self, start, goal):
        if self.current_mode == config.MODE_ASTAR_Q:
            return AStarQAgent(start, goal)
        return LRTALearningAgent(start, goal)
