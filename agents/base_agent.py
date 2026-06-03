# agents/base_agent.py
import pygame
import config

class BaseAgent:
    def __init__(self, start_pos, goal_pos, color):
        self.start_pos = start_pos
        self.goal_pos = goal_pos
        self.color = color
        self.current_pos = start_pos
        self.path = [start_pos]
        self.is_finished = False

    def reset(self):
        self.current_pos = self.start_pos
        self.path = [self.start_pos]
        self.is_finished = False

    def move_to(self, next_pos):
        self.current_pos = next_pos
        self.path.append(next_pos)

    def draw(self, screen):
        # Chỉ vẽ lộ trình nếu mảng đường đi có dữ liệu hành trình
        if len(self.path) > 1:
            for i in range(len(self.path) - 1):
                p1, p2 = self.path[i], self.path[i+1]
                center1 = (p1[1] * config.CELL_SIZE + config.CELL_SIZE // 2, p1[0] * config.CELL_SIZE + config.CELL_SIZE // 2)
                center2 = (p2[1] * config.CELL_SIZE + config.CELL_SIZE // 2, p2[0] * config.CELL_SIZE + config.CELL_SIZE // 2)
                pygame.draw.line(screen, self.color, center1, center2, 3)

        r, c = self.current_pos
        center = (c * config.CELL_SIZE + config.CELL_SIZE // 2, r * config.CELL_SIZE + config.CELL_SIZE // 2)
        pygame.draw.circle(screen, self.color, center, config.CELL_SIZE // 3)