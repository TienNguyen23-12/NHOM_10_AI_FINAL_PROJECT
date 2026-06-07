# utils/q_learning.py
import json
import os


class QLearningModel:
    def __init__(self, gamma=0.9):
        self.q_table = {}
        self.actions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        self.gamma = gamma

    def get_q_values(self, state):
        """Khởi tạo trạng thái s với Q(s,a) = 0 nếu chưa tồn tại"""
        if state not in self.q_table:
            self.q_table[state] = [0.0, 0.0, 0.0, 0.0]
        return self.q_table[state]

    def update_q_value(self, state, action_idx, reward, next_state):
        # --- ĐÃ FIX: Gọi hàm này để đảm bảo 'state' (ô cũ) được khởi tạo mảng [0,0,0,0] ---
        self.get_q_values(state)

        # Phương trình chuẩn: Q(s,a) = r + gamma * max(Q(s',a'))
        max_next_q = max(self.get_q_values(next_state))
        new_q = reward + self.gamma * max_next_q
        self.q_table[state][action_idx] = new_q

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