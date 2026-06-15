import heapq
import config
from agents.base_agent import BaseAgent


class AStarQAgent(BaseAgent):
    def __init__(self, start_pos, goal_pos):
        super().__init__(start_pos, goal_pos, color=(41, 128, 185))
        self.original_hospital_pos = start_pos

        self.calculated_path = []
        self.path_index = 0

        self.search_generator = None
        self.vis_open_set = set()
        self.vis_visited = set()
        self.vis_path = []

    def heuristic(self, pos):
        return abs(pos[0] - self.goal_pos[0]) + abs(pos[1] - self.goal_pos[1])

    def search_path_with_q(self, grid_map, app_instance):
        start, goal = self.start_pos, self.goal_pos
        open_set = []
        heapq.heappush(open_set, (0 + self.heuristic(start), 0, start, [start]))
        visited = set()

        while open_set:
            f, g, current, path = heapq.heappop(open_set)
            if current == goal: return path
            if current in visited: continue
            visited.add(current)

            for action_idx, (dr, dc) in enumerate(app_instance.global_q_brain.actions):
                neighbor = (current[0] + dr, current[1] + dc)
                if grid_map.is_valid_move(neighbor) and neighbor not in visited:
                    base_cost = grid_map.get_cost(neighbor)

                    q_penalty = 0
                    if app_instance.current_mode == getattr(config, 'MODE_ASTAR_Q', 3):
                        q_values = app_instance.global_q_brain.q_table.get(current, [0, 0, 0, 0])
                        raw_q_pen = -q_values[action_idx] if q_values[action_idx] < 0 else 0
                        q_penalty = raw_q_pen * getattr(config, 'Q_WEIGHT', 0.2)

                    new_g = g + base_cost + q_penalty
                    new_f = new_g + self.heuristic(neighbor)
                    heapq.heappush(open_set, (new_f, new_g, neighbor, path + [neighbor]))
        return [start]

    def search_path_generator(self, grid_map, app_instance):
        start, goal = self.start_pos, self.goal_pos
        open_set = []
        heapq.heappush(open_set, (0 + self.heuristic(start), 0, start, [start]))
        visited = set()
        open_set_tracker = {start}

        steps = 0
        while open_set:
            f, g, current, path = heapq.heappop(open_set)
            if current in open_set_tracker: open_set_tracker.remove(current)

            if current == goal:
                yield open_set_tracker, visited, path, True
                return

            if current in visited: continue
            visited.add(current)

            for action_idx, (dr, dc) in enumerate(app_instance.global_q_brain.actions):
                neighbor = (current[0] + dr, current[1] + dc)
                if grid_map.is_valid_move(neighbor) and neighbor not in visited:
                    base_cost = grid_map.get_cost(neighbor)

                    q_penalty = 0
                    if app_instance.current_mode == getattr(config, 'MODE_ASTAR_Q', 3):
                        q_values = app_instance.global_q_brain.q_table.get(current, [0, 0, 0, 0])
                        raw_q_pen = -q_values[action_idx] if q_values[action_idx] < 0 else 0
                        q_penalty = raw_q_pen * getattr(config, 'Q_WEIGHT', 0.2)

                    new_g = g + base_cost + q_penalty
                    new_f = new_g + self.heuristic(neighbor)
                    heapq.heappush(open_set, (new_f, new_g, neighbor, path + [neighbor]))
                    open_set_tracker.add(neighbor)

            steps += 1
            if steps % 4 == 0:
                yield open_set_tracker, visited, path, False

        yield open_set_tracker, visited, [start], True

    def update_astar_return_logic(self, grid_map, app_instance):
        if self.is_finished: return

        # --- NẾU VẪN ĐANG DI CHUYỂN TRÊN LỘ TRÌNH ---
        if self.path_index < len(self.calculated_path) - 1:
            next_step = self.calculated_path[self.path_index + 1]

            if not grid_map.is_valid_move(next_step):
                app_instance.logger.add_log("[RE-PLAN] Đường đi dự kiến bị chặn! Đang tính lại...")
                self.start_pos = self.current_pos
                if app_instance.visualize_search:
                    self.search_generator = self.search_path_generator(grid_map, app_instance)
                else:
                    self.calculated_path = self.search_path_with_q(grid_map, app_instance)
                self.path_index = 0
                return

            self.path_index += 1
            cost = grid_map.get_cost(self.calculated_path[self.path_index])
            self.move_to(self.calculated_path[self.path_index], cost)

        # --- NẾU ĐÃ CHẠM ĐÍCH CỦA GIAI ĐOẠN HIỆN TẠI ---
        else:
            phase = getattr(self, 'mission_phase', 0)

            # Giai đoạn 0 -> 1: Tai nạn -> Tìm bệnh viện tốt nhất
            if phase == 0:
                self.mission_phase = 1
                if self.goal_pos in grid_map.accidents_pool:
                    grid_map.accidents_pool.remove(self.goal_pos)
                    grid_map.grid[self.goal_pos[0]][self.goal_pos[1]] = config.STATE_EMPTY

                self.start_pos = self.current_pos

                # Sức mạnh A*: Cắm cờ quét tất cả bệnh viện để tìm đường tốn ít điểm Cost nhất (né kẹt xe)
                best_h = self.original_hospital_pos
                min_cost = float('inf')

                for h_name, h_info in app_instance.dispatcher.hospitals.items():
                    self.goal_pos = h_info["pos"]
                    test_path = self.search_path_with_q(grid_map, app_instance)
                    if len(test_path) < min_cost:
                        min_cost = len(test_path)
                        best_h = h_info["pos"]

                self.goal_pos = best_h
                self.path = [self.current_pos]

                if app_instance.visualize_search:
                    self.search_generator = self.search_path_generator(grid_map, app_instance)
                else:
                    self.calculated_path = self.search_path_with_q(grid_map, app_instance)
                self.path_index = 0

            # Giai đoạn 1 -> 2: Thả bệnh nhân -> Quay về trạm gốc
            elif phase == 1:
                self.mission_phase = 2
                app_instance.logger.add_log(f"[A*] Đã đưa bệnh nhân đến bệnh viện! Tổng quãng đường: {self.total_distance} ô, Thời gian: {self.total_time} phút.")
                self.start_pos = self.current_pos
                self.goal_pos = self.original_hospital_pos
                self.path = [self.current_pos]

                if app_instance.visualize_search:
                    self.search_generator = self.search_path_generator(grid_map, app_instance)
                else:
                    self.calculated_path = self.search_path_with_q(grid_map, app_instance)
                self.path_index = 0

            # Giai đoạn 2 -> Xong
            elif phase == 2:
                self.is_finished = True
                self.path.clear()
                self.vis_open_set.clear()
                self.vis_visited.clear()
                self.vis_path.clear()

                found_hospital = next((name for name, info in app_instance.dispatcher.hospitals.items() if
                                       info["pos"] == self.original_hospital_pos), None)
                if found_hospital and found_hospital in app_instance.dispatcher.current_cars:
                    app_instance.dispatcher.current_cars[found_hospital] += 1
                    app_instance.logger.add_log(f"[STATION] Xe A* về trạm gốc, phục hồi tại {found_hospital}.")