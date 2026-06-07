# utils/q_learning.py
import random
import config

class QLearningModel:
    def __init__(self, actions=[(-1, 0), (1, 0), (0, -1), (0, 1)]):
        self.actions = actions
        self.alpha = 0.1   # Tốc độ học (Learning Rate)
        self.gamma = 0.9   # Hệ số giảm tương lai (Discount Factor)
        self.epsilon = 0.2 # Tỷ lệ khám phá (Exploration Rate)
        self.q_table = {}

    def get_q_values(self, state):
        if state not in self.q_table:
            self.q_table[state] = [0.0] * len(self.actions)
        return self.q_table[state]

    def choose_action(self, state):
        q_values = self.get_q_values(state)
        if random.random() < self.epsilon:
            return random.choice(range(len(self.actions)))
        max_q = max(q_values)
        best_actions = [i for i, q in enumerate(q_values) if q == max_q]
        return random.choice(best_actions)

    def learn(self, state, action_idx, reward, next_state):
        current_q = self.get_q_values(state)[action_idx]
        max_next_q = max(self.get_q_values(next_state))
        new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state][action_idx] = new_q