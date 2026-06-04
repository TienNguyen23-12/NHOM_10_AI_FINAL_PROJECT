# utils/q_learning.py

class QLearningModel:
    def __init__(self, alpha=0.1, gamma=0.9):
        self.q_table = {}
        self.actions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Các hành động: Lên, Xuống, Trái, Phải
        self.alpha = alpha  # Learning rate (Hệ số học tập)
        self.gamma = gamma  # Discount factor (Hệ số chiết khấu)

    def get_q_values(self, state):
        """Khởi tạo trạng thái mới với mảng Q-Value [0,0,0,0] nếu ô đó chưa từng được đi qua"""
        if state not in self.q_table:
            self.q_table[state] = [0.0, 0.0, 0.0, 0.0]
        return self.q_table[state]

    def update_q_value(self, state, action_idx, reward, next_state):
        """Áp dụng công thức Bellman để cập nhật trọng số Q-Table sau mỗi bước đi"""
        current_q = self.get_q_values(state)[action_idx]
        max_next_q = max(self.get_q_values(next_state))

        # Phương trình Q-Learning cốt lõi
        new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state][action_idx] = new_q