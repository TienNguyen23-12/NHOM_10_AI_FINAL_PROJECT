# environment/grid_map.py
import random
import config


class GridMap:
    def __init__(self):
        self.grid = [[config.STATE_EMPTY for _ in range(config.GRID_SIZE)] for _ in range(config.GRID_SIZE)]
        self.accidents_pool = []
        self.generate_default_map()

    def generate_default_map(self):
        # Tạo cấu trúc các khối nhà cố định rải rác bản đồ
        for i in range(2, config.GRID_SIZE - 2, 4):
            for j in range(2, config.GRID_SIZE - 2):
                if j % 4 != 0:
                    self.grid[i][j] = config.STATE_WALL

        # Đặt các bệnh viện cố định lên map nếu có cấu hình sẵn
        for h_info in config.HOSPITAL_CONFIG.values():
            r, c = h_info["pos"]
            self.grid[r][c] = config.STATE_HOSPITAL

    def set_traffic_jam(self, hour):
        self.clear_traffic()
        if 17 <= hour <= 18:
            for j in range(2, config.GRID_SIZE - 2):
                if self.grid[8][j] == config.STATE_EMPTY: self.grid[8][j] = config.STATE_TRAFFIC
                if self.grid[12][j] == config.STATE_EMPTY: self.grid[12][j] = config.STATE_TRAFFIC

    def clear_traffic(self):
        for r in range(config.GRID_SIZE):
            for c in range(config.GRID_SIZE):
                if self.grid[r][c] == config.STATE_TRAFFIC:
                    self.grid[r][c] = config.STATE_EMPTY

    def is_valid_move(self, pos):
        r, c = pos
        if 0 <= r < config.GRID_SIZE and 0 <= c < config.GRID_SIZE:
            return self.grid[r][c] != config.STATE_WALL
        return False

    def get_cost(self, pos):
        """HÀM CHI PHÍ ĐỘNG: Trọng số thay đổi rõ rệt giữa giờ bình thường và giờ cao điểm"""
        r, c = pos
        if self.grid[r][c] == config.STATE_TRAFFIC:
            return 5  # Kẹt xe giờ cao điểm: Chi phí tăng gấp 5 lần ô trống bình thường
        if self.grid[r][c] == config.STATE_ACCIDENT:
            return 20  # Vùng tai nạn cục bộ: Chi phí phạt cực cao để ép thuật toán né đường khác
        return 1  # Ô trống bình thường: Chi phí tối thiểu là 1