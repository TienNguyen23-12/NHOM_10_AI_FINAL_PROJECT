# ui/button.py
import pygame


class Button:
    def __init__(self, x, y, w, h, text, mode_id=0):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.mode_id = mode_id
        self.is_active = False

    def draw(self, screen, font):
        mouse_pos = pygame.mouse.get_pos()

        # Hiệu ứng đổi màu thông minh khi tương tác chuột
        if self.is_active:
            base_color = (46, 204, 113)  # Xanh lá khi nút đang được kích hoạt
        elif self.rect.collidepoint(mouse_pos):
            base_color = (52, 152, 219)  # Xanh dương sáng khi di chuột qua (Hover effect)
        else:
            base_color = (127, 140, 141)  # Xám trang nhã ở trạng thái tĩnh bình thường

        pygame.draw.rect(screen, base_color, self.rect, border_radius=5)

        # --- ĐÃ FIX: Chuyển độ dày viền từ 1.5 về số nguyên 1 để tránh lỗi TypeError ---
        pygame.draw.rect(screen, (44, 62, 80), self.rect, 1, border_radius=5)

        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)