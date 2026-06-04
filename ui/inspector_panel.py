# ui/inspector_panel.py
import pygame


class InspectorPanel:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.display_mode = "WELCOME"
        self.inspect_data = []

        # Biến xử lý thanh cuộn
        self.scroll_y = 0
        self.max_scroll = 0

    def handle_event(self, event):
        """Bắt sự kiện lăn chuột (Scroll) khi trỏ vào bảng Monitor"""
        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            if self.x <= mx <= self.x + self.width and self.y <= my <= self.y + self.height:
                self.scroll_y += event.y * 25  # Tốc độ cuộn
                if self.scroll_y > 0: self.scroll_y = 0
                if self.scroll_y < -self.max_scroll: self.scroll_y = -self.max_scroll

    def set_welcome(self):
        self.display_mode = "WELCOME";
        self.scroll_y = 0
        self.inspect_data = ["Click any inspection button above", "to stream live AI internal metrics."]

    def load_q_table(self, q_table):
        self.display_mode = "Q_TABLE";
        self.scroll_y = 0
        self.inspect_data = ["--- LIVE BACKEND Q-TABLE METRICS ---"]
        if not q_table:
            self.inspect_data.append("No learned Q-weights in memory yet.")
            return
        for state, values in q_table.items():
            rounded_v = [round(v, 2) for v in values]
            self.inspect_data.append(f"Cell {state} -> Q:{rounded_v}")

    def load_h_table(self, active_agents):
        self.display_mode = "H_TABLE";
        self.scroll_y = 0
        self.inspect_data = ["--- LIVE LRTA* HEURISTIC FIELDS ---"]
        lrta_cars = [a for a in active_agents if hasattr(a, 'h_table')]
        if not lrta_cars:
            self.inspect_data.append("No active LRTA* agents on map.")
            return
        for idx, car in enumerate(lrta_cars):
            self.inspect_data.append(f"[Agent #{idx + 1}] Memory states:")
            for state, h_val in car.h_table.items():
                self.inspect_data.append(f"  Node {state} -> H: {round(h_val, 1)}")

    def load_paths(self, active_agents):
        self.display_mode = "PATHS";
        self.scroll_y = 0
        self.inspect_data = ["--- ACTIVE MISSION PATH ROUTING ---"]
        if not active_agents:
            self.inspect_data.append("Fleet is currently stationed at depots.")
            return
        for idx, car in enumerate(active_agents):
            type_str = "A*" if hasattr(car, 'calculated_path') else "LRTA*"
            self.inspect_data.append(f"Car #{idx + 1} [{type_str}]:")
            self.inspect_data.append(f"  {car.start_pos} -> {car.goal_pos}")
            self.inspect_data.append(f"  Traversed: {len(car.path)} blocks.")

    def draw(self, screen, font, font_bold):
        pygame.draw.rect(screen, (248, 249, 250), (self.x, self.y, self.width, self.height), border_radius=6)
        pygame.draw.rect(screen, (220, 224, 230), (self.x, self.y, self.width, self.height), 1, border_radius=6)

        # Tạo vùng Clip (Mặt nạ cắt) để chữ cuộn không bị tràn ra ngoài viền bảng
        old_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(self.x, self.y, self.width, self.height))

        y_offset = self.y + 12 + self.scroll_y
        for text in self.inspect_data:
            is_header = text.startswith("---") or text.startswith("[Agent") or text.startswith("Car #")
            current_font = font_bold if is_header else font
            color = (44, 62, 80) if is_header else (79, 93, 117)

            surf = current_font.render(text, True, color)
            screen.blit(surf, (self.x + 12, y_offset))
            y_offset += 20  # Khoảng cách dòng khi cuộn

        screen.set_clip(old_clip)

        # Tính toán độ dài tối đa của thanh cuộn
        total_content_height = len(self.inspect_data) * 20 + 24
        self.max_scroll = max(0, total_content_height - self.height)

        # Vẽ thanh cuộn đồ họa bên mép phải nếu nội dung vượt quá khung hiển thị
        if self.max_scroll > 0:
            bar_height = max(20, self.height * (self.height / total_content_height))
            bar_y = self.y + (-self.scroll_y / self.max_scroll) * (self.height - bar_height)
            pygame.draw.rect(screen, (180, 185, 190), (self.x + self.width - 10, bar_y, 6, bar_height), border_radius=3)