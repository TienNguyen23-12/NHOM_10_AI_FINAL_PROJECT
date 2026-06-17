# config.py

# --- 1. CẤU HÌNH BẢN ĐỒ (GRID CONFIG) ---
GRID_SIZE = 20
CELL_SIZE = 25
# Giới hạn kích thước để đảm bảo hiệu năng
MIN_GRID = 10
MAX_GRID = 100

# --- 2. TRẠNG THÁI Ô (GRID STATES) ---
STATE_EMPTY = 0
STATE_WALL = 1
STATE_TRAFFIC = 2
STATE_ACCIDENT = 3
STATE_HOSPITAL = 4

# --- 3. BẢNG MÀU ĐỒ HỌA (THEME CONFIG) ---
THEME = {
    "EMPTY": (255, 255, 255),
    "WALL": (44, 62, 80),
    "TRAFFIC": (230, 126, 34),
    "ACCIDENT": (231, 76, 60),
    "HOSPITAL": (155, 89, 182),
    "TEXT": (52, 73, 94)
}

# Ánh xạ màu cho GridMap sử dụng
COLOR_EMPTY = THEME["EMPTY"]
COLOR_WALL = THEME["WALL"]
COLOR_TRAFFIC = THEME["TRAFFIC"]
COLOR_ACCIDENT = THEME["ACCIDENT"]
COLOR_HOSPITAL = THEME["HOSPITAL"]
COLOR_TEXT = THEME["TEXT"]

# --- 4. CẤU HÌNH AI & THUẬT TOÁN (AI HYPERPARAMETERS) ---
# Chế độ thuật toán
MODE_ASTAR = 1           # A* Thuần (Không não)
MODE_LRTASTAR = 2        # LRTA* Thuần (Không não)
MODE_ASTAR_Q = 3         # A* + Q-Learning
MODE_LRTASTAR_Q = 4      # LRTA* + Q-Learning

# Hệ số đồng bộ đơn vị Q-Table vào hàm Heuristic (Từ 0.1 đến 1.0)
Q_WEIGHT = 0.2

# Hệ số Q-Learning (Ảnh hưởng đến độ "nhớ" của xe)
GAMMA = 0.9  # Tầm nhìn xa của AI (Discount Factor)
LEARNING_RATE = 0.5 # Tốc độ cập nhật kinh nghiệm mới (Nếu thầy cô hỏi, bảo em để 0.5 để cân bằng giữa cũ và mới)

# Chi phí di chuyển (Cost) - Dùng trong hàm tính toán tổng chi phí của A* và LRTA*
COST_EMPTY = 1
COST_TRAFFIC = 5    # Càng cao xe càng sợ đường kẹt
COST_ACCIDENT = 50   # Phạt cực nặng khi đâm vào vùng nguy hiểm

# --- 5. ĐỊNH NGHĨA PHẦN THƯỞNG (Q-LEARNING REWARDS) ---
REWARD_STEP = -1       # Chi phí mỗi bước di chuyển
REWARD_TRAFFIC = -20   # Phạt kẹt xe (Cần thấp hơn COST_TRAFFIC để AI học nhanh hơn)
REWARD_GOAL = 100      # Phần thưởng khi về đích thành công

# --- 6. CẤU HÌNH HỆ THỐNG ---
HOSPITAL_CONFIG = {}
DEFAULT_FLEET_SIZE = 3 # Số xe mặc định khi tạo trạm mới