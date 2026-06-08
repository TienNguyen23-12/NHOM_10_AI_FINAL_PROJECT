import pygame


class LoggerPanel:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.logs = []
        self.max_logs = 20  # Lưu tối đa 20 dòng để nhẹ máy

    def add_log(self, message):
        self.logs.append(message)
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)

    def draw(self, screen, font):
        # 1. Vẽ background bo góc xịn sò (Màu Than chì đậm)
        pygame.draw.rect(screen, (34, 47, 62), (self.x, self.y, self.width, self.height), border_radius=6)
        # 2. Vẽ viền xám nhạt
        pygame.draw.rect(screen, (87, 101, 116), (self.x, self.y, self.width, self.height), 2, border_radius=6)

        # 3. CẮT VIỀN (Clipping): Đảm bảo chữ không bao giờ bị tràn ra ngoài khung
        old_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(self.x, self.y, self.width, self.height))

        # 4. Vẽ text từ dưới lên trên
        padding_x = 10
        padding_y = 10
        line_spacing = 18

        current_y = self.y + self.height - padding_y - line_spacing

        for log in reversed(self.logs):
            if current_y < self.y: break  # Nếu vượt quá mép trên thì ngưng vẽ

            # Tô màu text tự động dựa vào keyword
            color = (200, 214, 229)  # Xám trắng mặc định
            if "[ALERT]" in log:
                color = (255, 107, 107)  # Đỏ
            elif "[SYSTEM]" in log:
                color = (29, 209, 161)  # Xanh mint
            elif "[DISPATCH]" in log:
                color = (254, 202, 87)  # Vàng cam
            elif "[STATION]" in log:
                color = (72, 219, 251)  # Xanh dương nhạt

            text_surf = font.render(log, True, color)
            screen.blit(text_surf, (self.x + padding_x, current_y))
            current_y -= line_spacing

        # Trả lại quyền vẽ toàn màn hình
        screen.set_clip(old_clip)