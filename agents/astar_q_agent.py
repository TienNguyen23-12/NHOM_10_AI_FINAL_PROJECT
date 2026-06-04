# agents/astar_q_agent.py
import heapq
import config
from agents.base_agent import BaseAgent
from utils.q_learning import QLearningModel


class AStarQAgent(BaseAgent):
    def __init__(self, start_pos, goal_pos):
        super().__init__(start_pos, goal_pos, color=(41, 128, 185))  # Xe màu Xanh Dương
        self.original_hospital_pos = start_pos  # --- FIX: Ghi nhớ vĩnh viễn tọa độ trạm gốc ---
        self.q_brain = QLearningModel()
        self.calculated_path = []
        self.path_index = 0
        self.is_returning = False

    def heuristic(self, pos):
        return abs(pos[0] - self.goal_pos[0]) + abs(pos[1] - self.goal_pos[1])

    def search_path_with_q(self, grid_map):
        """Hàm tìm đường A* quét lại toàn bộ bản đồ tại thời điểm gọi"""
        start, goal = self.start_pos, self.goal_pos
        open_set = []
        heapq.heappush(open_set, (0 + self.heuristic(start), 0, start, [start]))
        visited = set()

        while open_set:
            f, g, current, path = heapq.heappop(open_set)
            if current == goal: return path
            if current in visited: continue
            visited.add(current)

            for action_idx, (dr, dc) in enumerate(self.q_brain.actions):
                neighbor = (current[0] + dr, current[1] + dc)
                if grid_map.is_valid_move(neighbor) and neighbor not in visited:
                    base_cost = grid_map.get_cost(neighbor)
                    q_values = self.q_brain.get_q_values(current)
                    q_penalty = -q_values[action_idx] if q_values[action_idx] < 0 else 0

                    new_g = g + base_cost + q_penalty
                    new_f = new_g + self.heuristic(neighbor)
                    heapq.heappush(open_set, (new_f, new_g, neighbor, path + [neighbor]))
        return [start]  # Trả về vị trí đứng im nếu bị kẹt cứng mọi đường

    def update_astar_return_logic(self, grid_map, app_instance):
        if self.is_finished: return

        if self.path_index < len(self.calculated_path) - 1:
            self.path_index += 1
            self.move_to(self.calculated_path[self.path_index])
        else:
            # GIAI ĐOẠN 1: Tới hiện trường tai nạn
            if not self.is_returning:
                self.is_returning = True
                if self.goal_pos in grid_map.accidents_pool:
                    grid_map.accidents_pool.remove(self.goal_pos)
                    grid_map.grid[self.goal_pos[0]][self.goal_pos[1]] = config.STATE_EMPTY

                # Dọn vết xe đi
                self.path = [self.current_pos]

                # --- ĐÃ FIX LOGIC: KHÔNG CHẠY NGƯỢC MẢNG LƯỜI BIẾNG NỮA ---
                # Đổi vai trò: Điểm đứng hiện tại thành Điểm xuất phát, Trạm gốc thành Đích đến
                self.start_pos = self.current_pos
                self.goal_pos = self.original_hospital_pos

                # Gọi hệ thống quét radar bản đồ lại từ đầu để tìm đường về an toàn nhất (né tường/kẹt xe mới)
                self.calculated_path = self.search_path_with_q(grid_map)
                self.path_index = 0

            else:
                # GIAI ĐOẠN 2: Về tới bệnh viện
                self.is_finished = True
                self.path.clear()

                found_hospital = None
                for h_name, h_info in app_instance.dispatcher.hospitals.items():
                    if h_info["pos"] == self.original_hospital_pos:
                        found_hospital = h_name
                        break

                if found_hospital and found_hospital in app_instance.dispatcher.current_cars:
                    app_instance.dispatcher.current_cars[found_hospital] += 1
                    app_instance.logger.add_log(f"[STATION] Xe A* returned, fleet recovered at {found_hospital}.")