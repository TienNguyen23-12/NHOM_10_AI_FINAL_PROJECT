# ui/logger_panel.py
import pygame


class LoggerPanel:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.ui_logs = ["[SYSTEM] Ready to initialize application simulation."]

    def add_log(self, text):
        self.ui_logs.append(text)
        if len(self.ui_logs) > 5:  # Giới hạn 5 dòng gọn gàng
            self.ui_logs.pop(0)

    def draw(self, screen, font):
        pygame.draw.rect(screen, (25, 25, 25), (self.x, self.y, self.width, self.height), border_radius=5)
        pygame.draw.rect(screen, (80, 80, 80), (self.x, self.y, self.width, self.height), 1, border_radius=5)

        for idx, log_text in enumerate(self.ui_logs):
            color = (220, 220, 220)
            if "returned" in log_text or "allocation" in log_text or "recovered" in log_text.lower():
                color = (46, 204, 113)
            elif "ALERT" in log_text:
                color = (231, 76, 60)
            elif "DISPATCH" in log_text:
                color = (241, 196, 15)

                # ĐÃ FIX: Bước nhảy dòng là 18px (vượt qua font size 14px) để chữ không bao giờ đè nhau
            y_offset = self.y + 8 + (idx * 18)
            log_surf = font.render(log_text, True, color)
            screen.blit(log_surf, (self.x + 12, y_offset))