# ui/button.py
import pygame


class Button:
    def __init__(self, x, y, w, h, text, mode_id=0):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.mode_id = mode_id
        self.is_active = False

    def draw(self, screen, font):
        if self.is_active:
            base_color = (46, 204, 113)  # Xanh lá khi nút kích hoạt
        else:
            base_color = (149, 165, 166)  # Xám nhạt khi tắt nút

        pygame.draw.rect(screen, base_color, self.rect, border_radius=4)
        pygame.draw.rect(screen, (127, 140, 141), self.rect, 1, border_radius=4)

        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)