# agents/base_agent.py
# Đã loại bỏ import pygame — drawing được xử lý bởi GridCanvas (PyQt6).
# Giữ nguyên toàn bộ state và logic di chuyển.

import config


class BaseAgent:
    def __init__(self, start_pos, goal_pos, color):
        self.start_pos   = start_pos
        self.goal_pos    = goal_pos
        self.color       = color        # (R, G, B) tuple — GridCanvas dùng QColor(*color)
        self.current_pos = start_pos
        self.path        = [start_pos]
        self.is_finished = False

    def reset(self):
        self.current_pos = self.start_pos
        self.path        = [self.start_pos]
        self.is_finished = False

    def move_to(self, next_pos):
        self.current_pos = next_pos
        self.path.append(next_pos)
