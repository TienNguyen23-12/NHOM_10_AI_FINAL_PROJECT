import config
from agents.base_agent import BaseAgent


class LRTALearningAgent(BaseAgent):
    def __init__(self, start_pos, goal_pos):
        super().__init__(start_pos, goal_pos, color=(142, 68, 173))
        self.h_table = {}
        self.original_hospital_pos = start_pos

        self.vis_open_set = set()
        self.vis_visited = set()
        self.vis_path = []

    def get_h(self, pos):
        if pos not in self.h_table:
            self.h_table[pos] = abs(pos[0] - self.goal_pos[0]) + abs(pos[1] - self.goal_pos[1])
        return self.h_table[pos]

    def update_route_realtime_with_return(self, grid_map, app_instance):
        if self.is_finished: return

        # --- STATE MACHINE: KIỂM TRA CHUYỂN GIAI ĐOẠN ---
        if self.current_pos == self.goal_pos:
            phase = getattr(self, 'mission_phase', 0)

            # Giai đoạn 0 -> 1: Tai nạn -> Bệnh viện gần nhất
            if phase == 0:
                self.mission_phase = 1
                if self.goal_pos in grid_map.accidents_pool:
                    grid_map.accidents_pool.remove(self.goal_pos)
                    grid_map.grid[self.goal_pos[0]][self.goal_pos[1]] = config.STATE_EMPTY

                # LRTA* thực chiến: Chọn viện gần nhất dựa trên khoảng cách Manhattan ngay tại chỗ
                best_h = self.original_hospital_pos
                min_dist = float('inf')
                for h_name, h_info in app_instance.dispatcher.hospitals.items():
                    target_pos = h_info["pos"]
                    dist = abs(self.current_pos[0] - target_pos[0]) + abs(self.current_pos[1] - target_pos[1])
                    if dist < min_dist:
                        min_dist = dist
                        best_h = target_pos

                self.goal_pos = best_h
                self.path = [self.current_pos]
                self.h_table.clear()
                return  # Đứng yên 1 nhịp để đưa nạn nhân lên xe

            # Giai đoạn 1 -> 2: Thả bệnh nhân -> Quay về trạm gốc
            elif phase == 1:
                self.mission_phase = 2
                app_instance.logger.add_log(f"[LRTA*] Đã đưa bệnh nhân đến bệnh viện! Tổng quãng đường: {self.total_distance} ô, Thời gian: {self.total_time} phút.")
                self.goal_pos = self.original_hospital_pos
                self.path = [self.current_pos]
                self.h_table.clear()
                return  # Đứng yên 1 nhịp để thả bệnh nhân

            # Giai đoạn 2 -> Xong: Về tới trạm gốc, phục hồi xe
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
                    app_instance.logger.add_log(f"[STATION] Xe LRTA* về trạm gốc, phục hồi tại {found_hospital}.")
                return

        # --- TÌM ĐƯỜNG LRTA* TRONG THỰC CHIẾN ---
        current = self.current_pos
        best_next = None
        min_f = float('inf')
        radar_scanned_cells = set()
        best_action_idx = -1

        for action_idx, (dr, dc) in enumerate(app_instance.global_q_brain.actions):
            neighbor = (current[0] + dr, current[1] + dc)

            if grid_map.is_valid_move(neighbor):
                radar_scanned_cells.add(neighbor)

                base_cost = 1 if neighbor == self.goal_pos else grid_map.get_cost(neighbor)

                q_pen = 0
                if app_instance.current_mode == getattr(config, 'MODE_LRTASTAR_Q', 4):
                    q_vals = app_instance.global_q_brain.q_table.get(current, [0, 0, 0, 0])
                    raw_q_pen = -q_vals[action_idx] if q_vals[action_idx] < 0 else 0
                    q_pen = raw_q_pen * getattr(config, 'Q_WEIGHT', 0.2)

                f_value = base_cost + q_pen + self.get_h(neighbor)

                if f_value < min_f:
                    min_f = f_value
                    best_next = neighbor
                    best_action_idx = action_idx

        if hasattr(app_instance, 'visualize_search') and app_instance.visualize_search:
            self.vis_open_set = radar_scanned_cells
            self.vis_visited = {current}
            self.vis_path = [current, best_next] if best_next else [current]
        else:
            self.vis_open_set.clear()
            self.vis_visited.clear()
            self.vis_path.clear()

        if best_next:
            old_pos = self.current_pos
            self.h_table[current] = max(self.get_h(current), min_f)
            cost = grid_map.get_cost(best_next)
            self.move_to(best_next, cost)

            if app_instance.current_mode == getattr(config, 'MODE_LRTASTAR_Q', 4):
                reward = -grid_map.get_cost(self.current_pos)
                if self.current_pos == self.goal_pos:
                    reward = getattr(config, 'REWARD_GOAL', 100)
                app_instance.global_q_brain.update_q_value(old_pos, best_action_idx, reward, self.current_pos)