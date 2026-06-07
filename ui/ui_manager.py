# ui/ui_manager.py
import pygame
import config
from ui.button import Button


class UIManager:
    def __init__(self, window_width, window_height):
        self.window_width = window_width
        self.window_height = window_height
        self.menu_buttons = []
        self.sim_buttons = []
        self.brush_buttons = []
        self.inspect_buttons = []
        self.map_buttons = []

        # Biến lưu trữ độ lệch của thanh cuộn cột giữa
        self.controls_scroll_y = 0

        self.reposition_buttons()

    def reposition_buttons(self):
        self.menu_buttons = [
            Button(self.window_width // 2 - 180, self.window_height // 2 - 40, 360, 45, "1. Custom Map Sandbox Layout"),
            Button(self.window_width // 2 - 180, self.window_height // 2 + 30, 360, 45,
                   "2. Generate Random Topology Map")
        ]

        ui_y = self.window_height - 145
        self.sim_buttons = [
            Button(15, ui_y, 140, 35, "System: A* + Q", config.MODE_ASTAR_Q),
            Button(165, ui_y, 140, 35, "System: LRTA* + Q", config.MODE_LRTASTAR_Q),
            Button(315, ui_y, 130, 35, "Rush Hour (17h)"),
            Button(455, ui_y, 120, 35, "Clear Map & Reset")
        ]

        # Khởi tạo các nút điều khiển lần đầu
        btn_x = self.window_width - 590
        btn_w = 155

        # Tạo placeholder, tọa độ Y thực tế sẽ do update_controls_layout lo
        self.brush_buttons = [Button(btn_x, 0, btn_w, 32, t) for t in
                              ["Brush: Accident", "Brush: Hospital", "Brush: Block Wall", "Brush: Traffic Jam",
                               "Eraser: Clear Cell"]]
        self.inspect_buttons = [Button(btn_x, 0, btn_w, 32, t) for t in
                                ["View Live Q-Table", "View Live H-Table", "View Active Routes", "Save Model (JSON)",
                                 "Load Model (JSON)", "Visualizer: OFF"]]
        self.map_buttons = [Button(btn_x, 0, btn_w, 32, t) for t in
                            ["Save Map (JSON)", "Load Map (JSON)", "Expand Map (+5)", "Shrink Map (-5)"]]

        self.update_controls_layout()

    def update_controls_layout(self):
        """Cập nhật lại tọa độ Y của tất cả các nút dựa vào thao tác cuộn chuột"""
        sy = self.controls_scroll_y

        # ĐÃ FIX: Giãn cách các nhóm nút ra cho dễ nhìn
        brush_y = 40
        ai_y = brush_y + (5 * 40) + 30  # Nhóm AI cách nhóm Brush 30px
        map_y = ai_y + (6 * 40) + 30  # Nhóm Map cách nhóm AI 30px

        for i, btn in enumerate(self.brush_buttons):
            btn.y = brush_y + i * 40 + sy
            if hasattr(btn, 'rect'): btn.rect.y = btn.y

        for i, btn in enumerate(self.inspect_buttons):
            btn.y = ai_y + i * 40 + sy
            if hasattr(btn, 'rect'): btn.rect.y = btn.y

        for i, btn in enumerate(self.map_buttons):
            btn.y = map_y + i * 40 + sy
            if hasattr(btn, 'rect'): btn.rect.y = btn.y

    def update_button_states(self, current_mode, brush_mode):
        for btn in self.sim_buttons:
            if btn.mode_id != 0: btn.is_active = (btn.mode_id == current_mode)

        for btn in self.brush_buttons:
            if "Accident" in btn.text and brush_mode == 'ACCIDENT':
                btn.is_active = True
            elif "Hospital" in btn.text and brush_mode == 'HOSPITAL':
                btn.is_active = True
            elif "Block Wall" in btn.text and brush_mode == 'WALL':
                btn.is_active = True
            elif "Traffic" in btn.text and brush_mode == 'TRAFFIC':
                btn.is_active = True
            elif "Clear" in btn.text and brush_mode == 'ERASE':
                btn.is_active = True
            else:
                btn.is_active = False

    def draw_controls(self, screen, font):
        """Chỉ vẽ cột điều khiển (Để SimulationApp dùng Clipping cắt viền)"""
        for btn in self.brush_buttons: btn.draw(screen, font)
        for btn in self.inspect_buttons: btn.draw(screen, font)
        for btn in self.map_buttons: btn.draw(screen, font)

    def draw_sim_buttons(self, screen, font):
        for btn in self.sim_buttons: btn.draw(screen, font)