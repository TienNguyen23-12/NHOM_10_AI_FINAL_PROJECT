# config.py

# Cấu hình kích thước lưới ô vuông đô thị
GRID_SIZE = 20
CELL_SIZE = 25

# Kích thước cửa sổ khởi tạo ban đầu
WIDTH = GRID_SIZE * CELL_SIZE + 300
HEIGHT = GRID_SIZE * CELL_SIZE + 120

# Định nghĩa các trạng thái ô trên bản đồ
STATE_EMPTY = 0
STATE_WALL = 1
STATE_TRAFFIC = 2
STATE_ACCIDENT = 3
STATE_HOSPITAL = 4

# Định nghĩa các chế độ chạy hệ thống
MODE_NONE = 0
MODE_ASTAR_Q = 1
MODE_LRTASTAR_Q = 2

# Hệ thống bảng màu đồ họa RGB
COLOR_EMPTY = (255, 255, 255)      # Trắng - Đường đi tự do
COLOR_WALL = (44, 62, 80)          # Xanh đen - Khối nhà / Rào chắn cố định
COLOR_TRAFFIC = (230, 126, 34)     # Cam - Vùng kẹt xe theo giờ cao điểm
COLOR_ACCIDENT = (231, 76, 60)     # Đỏ - Vị trí điểm xảy ra tai nạn đột xuất
COLOR_HOSPITAL = (155, 89, 182)    # Tím - Vị trí Trạm bệnh viện cứu hộ
COLOR_TEXT = (52, 73, 94)

# Hệ thống điểm thưởng / phạt của bộ não học máy Q-Learning
REWARD_STEP = -1       # Phạt di chuyển thông thường để thúc đẩy đi nhanh
REWARD_TRAFFIC = -10   # Phạt nặng khi lọt vào vùng kẹt xe
REWARD_ACCIDENT = -25  # Phạt cực nặng nếu đâm trúng điểm tai nạn khác

# Cấu hình tài nguyên kho xe (Sẽ được nạp động khi chạy hệ thống)
HOSPITAL_CONFIG = {}