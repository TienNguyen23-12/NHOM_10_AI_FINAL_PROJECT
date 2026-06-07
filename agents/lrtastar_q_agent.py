# agents/lrtastar_q_agent.py
import config
from agents.base_agent import BaseAgent


class LRTALearningAgent(BaseAgent):
    def __init__(self, start_pos, goal_pos):
        super().__init__(start_pos, goal_pos, color=(142, 68, 173))  # Xe màu Tím độc lập
        self.h_table = {}
        self.original_hospital_pos = start_pos  # Lưu giữ tọa độ trạm gốc của thực thể xe này
        self.is_returning = False

    def get_h(self, pos):
        if pos not in self.h_table:
            self.h_table[pos] = abs(pos[0] - self.goal_pos[0]) + abs(pos[1] - self.goal_pos[1])
        return self.h_table[pos]

    def update_route_realtime_with_return(self, grid_map, app_instance):
        if self.is_finished: return

        # GIAI ĐOẠN 1: Khi bẻ lái chạm trúng đích tai nạn mục tiêu
        if self.current_pos == self.goal_pos and not self.is_returning:
            self.is_returning = True
            if self.goal_pos in grid_map.accidents_pool:
                grid_map.accidents_pool.remove(self.goal_pos)
                grid_map.grid[self.goal_pos[0]][self.goal_pos[1]] = config.STATE_EMPTY

            # Dọn sạch vết lộ trình lúc đi để bắt đầu ghi vết mới lúc về
            self.path = [self.current_pos]

            # Thiết lập lại đích đến là vị trí bệnh viện xuất phát ban đầu
            self.goal_pos = self.original_hospital_pos
            self.h_table.clear()  # Dọn bảng Heuristic cũ để học tập đường quay về trạm hiệu quả nhất

        # GIAI ĐOẠN 2: Xe đã học đường chạy về tới viện gốc an toàn
        elif self.current_pos == self.original_hospital_pos and self.is_returning:
            self.is_finished = True
            self.path.clear()  # Xóa sạch hoàn toàn vệt đường đi về trên bản đồ

            # Quét động tìm trạm bệnh viện trùng với tọa độ gốc ban đầu để cộng trả xe
            found_hospital = None
            for h_name, h_info in app_instance.dispatcher.hospitals.items():
                if h_info["pos"] == self.original_hospital_pos:
                    found_hospital = h_name
                    break

            if found_hospital and found_hospital in app_instance.dispatcher.current_cars:
                app_instance.dispatcher.current_cars[found_hospital] += 1
                print(f"[HE THONG] Xe LRTA* da ve tram! {found_hospital} duoc hoi lai 1 xe.")
            return

        # Tính toán bẻ lái di chuyển từng bước thời gian thực (Real-time)
        current = self.current_pos
        best_next = None
        min_f = float('inf')

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            neighbor = (current[0] + dr, current[1] + dc)
            if grid_map.is_valid_move(neighbor):
                # --- TỐI ƯU HÓA: Nếu ô tiếp theo là đích, ép chi phí bằng 1 để xe lao vào đón người ---
                cost = 1 if neighbor == self.goal_pos else grid_map.get_cost(neighbor)

                f_value = cost + self.get_h(neighbor)
                if f_value < min_f:
                    min_f = f_value
                    best_next = neighbor

        if best_next:
            self.h_table[current] = max(self.get_h(current), min_f)
            self.move_to(best_next)