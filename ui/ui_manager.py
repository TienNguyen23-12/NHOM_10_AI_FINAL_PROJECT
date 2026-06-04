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

        # --- ĐÃ FIX CƠ CHẾ RESPONSIVE: Neo vị trí vào mép phải màn hình ---
        btn_x = self.window_width - 590
        btn_w = 155

        self.brush_buttons = [
            Button(btn_x, 35, btn_w, 32, "Brush: Accident"),
            Button(btn_x, 75, btn_w, 32, "Brush: Hospital"),
            Button(btn_x, 115, btn_w, 32, "Brush: Block Wall"),
            Button(btn_x, 155, btn_w, 32, "Brush: Traffic Jam"),
            Button(btn_x, 195, btn_w, 32, "Eraser: Clear Cell")
        ]

        self.inspect_buttons = [
            Button(btn_x, 260, btn_w, 32, "View Live Q-Table"),
            Button(btn_x, 300, btn_w, 32, "View Live H-Table"),
            Button(btn_x, 340, btn_w, 32, "View Active Routes")
        ]

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

    def draw_all(self, screen, font):
        for btn in self.sim_buttons: btn.draw(screen, font)
        for btn in self.brush_buttons: btn.draw(screen, font)
        for btn in self.inspect_buttons: btn.draw(screen, font)