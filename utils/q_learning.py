# utils/q_learning.py
import json
import os


class QLearningModel:
    def __init__(self, gamma=0.9):
        self.q_table = {}
        self.actions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        self.gamma = gamma

        # --- THÊM CÁC BIẾN CHO DYNAMIC GAMMA VÀ DYNAMIC Q_WEIGHT ---
        self.gamma_init = 0.4  # Ban đầu nhìn ngắn
        self.gamma_max = 0.95  # Sau này nhìn xa
        self.growth_rate = 0.001  # Tốc độ trưởng thành
        self.total_steps = 0  # Đếm tuổi đời AI
        self.gamma = self.gamma_init

    def get_dynamic_q_weight(self):
        import config
        # Tỉ số cân bằng: AI càng già, nó càng tin tưởng vào kinh nghiệm (Q-Table)
        # Giới hạn tối đa là config.Q_WEIGHT
        max_w = getattr(config, 'Q_WEIGHT', 0.8)
        min_w = 0.1
        # Cùng tốc độ trưởng thành với gamma
        current_w = min_w + (self.growth_rate * self.total_steps * 5)
        return min(max_w, current_w)

    def get_q_values(self, state):
        """Khởi tạo trạng thái s với Q(s,a) = 0 nếu chưa tồn tại"""
        if state not in self.q_table:
            self.q_table[state] = [0.0, 0.0, 0.0, 0.0]
        return self.q_table[state]

    def update_q_value(self, state, action_idx, reward, next_state):
        # 1. AI già đi 1 tuổi, Gamma lớn lên 1 chút
        self.total_steps += 1
        self.gamma = min(self.gamma_max, self.gamma_init + (self.growth_rate * self.total_steps))

        if state not in self.q_table:
            self.q_table[state] = [0.0, 0.0, 0.0, 0.0]
        if next_state not in self.q_table:
            self.q_table[next_state] = [0.0, 0.0, 0.0, 0.0]

        # 2. Sử dụng Gamma hiện tại (đã tăng) để tính toán
        best_next_q = max(self.q_table[next_state])

        # Phương trình Bellman với Alpha = 1.0
        self.q_table[state][action_idx] = reward + (self.gamma * best_next_q)
        print(f"[Q-TABLE UPDATE] State: {state}, Action: {self.actions[action_idx]}, Reward: {reward}, New Q: {self.q_table[state][action_idx]}")

    def save_brain(self, filepath="q_brain_memory.json"):
        json_friendly_table = {str(k): v for k, v in self.q_table.items()}
        try:
            with open(filepath, 'w') as f:
                json.dump(json_friendly_table, f)
            print(f"[AI] Saved Q-Table to {filepath}")
        except Exception as e:
            print(f"[ERROR] Failed to save AI brain: {e}")

    def load_brain(self, filepath="q_brain_memory.json"):
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                self.q_table = {eval(k): v for k, v in data.items()}
                print(f"[AI] Loaded Q-Table from {filepath}")
            except Exception as e:
                print(f"[ERROR] Failed to load AI brain: {e}")
        else:
            print("[AI] No previous memory found. Starting fresh.")