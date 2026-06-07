# main.py
import pygame
import config
from environment.grid_map import GridMap
from ui.button import Button
from utils.q_learning import QLearningModel
from utils.dispatch_center import DispatchCenter
from agents.astar_q_agent import AStarQAgent
from agents.lrtastar_q_agent import LRTALearningAgent


class SimulationApp:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        # Mở rộng kích thước cửa sổ chuẩn hóa không gian
        self.window_width = 980
        self.window_height = config.GRID_SIZE * config.CELL_SIZE + 140

        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        pygame.display.set_caption("Dashboard Dieu Phoi Cuu Ho Da Tac Tu - HCMUTE")

        self.font = pygame.font.SysFont(None, 18)
        self.font_large = pygame.font.SysFont(None, 26)
        self.clock = pygame.time.Clock()

        self.app_state = 'MENU'
        self.env = GridMap()

        # Khởi tạo ma trận trống trơn ban đầu
        self.env.grid = [[config.STATE_EMPTY for _ in range(config.GRID_SIZE)] for _ in range(config.GRID_SIZE)]
        config.HOSPITAL_CONFIG.clear()

        self.global_q_brain = QLearningModel()
        self.dispatcher = DispatchCenter(self.global_q_brain)
        self.dispatcher.reset_resources()

        self.active_agents = []
        self.current_mode = config.MODE_ASTAR_Q
        self.current_hour = 12

        # Các chế độ cọ vẽ chuột: 'ACCIDENT', 'HOSPITAL', 'WALL', 'TRAFFIC', 'ERASE'
        self.brush_mode = 'ACCIDENT'

        # Quản lý hộp thoại Popup chọn số xe
        self.show_popup = False
        self.popup_target_pos = None
        self.popup_car_count = 3

        self.zoom_scale = 1.0
        self.pan_offset_x = 20
        self.pan_offset_y = 20
        self.is_panning = False
        self.last_mouse_pos = (0, 0)

        self.reposition_buttons()

    def reposition_buttons(self):
        # Căn giữa các nút bấm Start Menu
        self.menu_buttons = [
            Button(self.window_width // 2 - 160, self.window_height // 2 - 40, 320, 45, "1. Tu tao ban do tu dau"),
            Button(self.window_width // 2 - 160, self.window_height // 2 + 30, 320, 45, "2. Sinh ngau nhien do thi")
        ]

        # Thanh UI điều khiển dưới đáy
        ui_y = self.window_height - 95
        self.sim_buttons = [
            Button(15, ui_y, 140, 35, "He thong: A* + Q", config.MODE_ASTAR_Q),
            Button(165, ui_y, 140, 35, "He thong: LRTA* + Q", config.MODE_LRTASTAR_Q),
            Button(315, ui_y, 130, 35, "Gio cao diem (17h)"),
            Button(455, ui_y, 120, 35, "Reset sach map")
        ]

        # Tọa độ X của thanh công cụ Brush bên phải
        brush_x = 600
        self.brush_buttons = [
            Button(brush_x, 35, 150, 32, "Chon: Dat tai nan"),
            Button(brush_x, 75, 150, 32, "Chon: Dat benh vien"),
            Button(brush_x, 115, 150, 32, "Chon: Ve tuong nha"),
            Button(brush_x, 155, 150, 32, "Chon: Ve vung ket xe"),
            Button(brush_x, 195, 150, 32, "Chon: Xoa o tren map")
        ]
        self.update_active_button_states()

    def update_active_button_states(self):
        for btn in self.sim_buttons:
            if btn.mode_id == self.current_mode:
                btn.is_active = True
            elif btn.mode_id != 0:
                btn.is_active = False

        for btn in self.brush_buttons:
            if "Dat tai nan" in btn.text and self.brush_mode == 'ACCIDENT':
                btn.is_active = True
            elif "Dat benh vien" in btn.text and self.brush_mode == 'HOSPITAL':
                btn.is_active = True
            elif "Ve tuong nha" in btn.text and self.brush_mode == 'WALL':
                btn.is_active = True
            elif "Ve vung ket xe" in btn.text and self.brush_mode == 'TRAFFIC':
                btn.is_active = True
            elif "Xoa o tren map" in btn.text and self.brush_mode == 'ERASE':
                btn.is_active = True
            else:
                btn.is_active = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.VIDEORESIZE:
                self.window_width, self.window_height = event.w, event.h
                self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
                self.reposition_buttons()
                continue

            mouse_pos = pygame.mouse.get_pos()

            if self.app_state == 'SIMULATION' and self.show_popup:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_popup_click(mouse_pos)
                continue

            # --- MÀN HÌNH MENU ---
            if self.app_state == 'MENU':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for btn in self.menu_buttons:
                        if btn.is_clicked(mouse_pos):
                            if "Tu tao ban do" in btn.text:
                                self.env.grid = [[config.STATE_EMPTY for _ in range(config.GRID_SIZE)] for _ in
                                                 range(config.GRID_SIZE)]
                                config.HOSPITAL_CONFIG.clear()
                                self.dispatcher.reset_resources()
                            else:
                                self.env.grid = [[config.STATE_EMPTY for _ in range(config.GRID_SIZE)] for _ in
                                                 range(config.GRID_SIZE)]
                                config.HOSPITAL_CONFIG = {
                                    "HOSPITAL_1": {"pos": (2, 2), "max_cars": 2},
                                    "HOSPITAL_2": {"pos": (2, 17), "max_cars": 3},
                                    "HOSPITAL_3": {"pos": (17, 9), "max_cars": 2}
                                }
                                self.env.generate_default_map()
                                self.dispatcher.hospitals = config.HOSPITAL_CONFIG
                                self.dispatcher.reset_resources()
                            self.app_state = 'SIMULATION'

            # --- MÀN HÌNH MÔ PHỎNG CHÍNH ---
            elif self.app_state == 'SIMULATION':
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:
                        self.zoom_scale = min(3.0, self.zoom_scale + 0.1)
                    elif event.button == 5:
                        self.zoom_scale = max(0.5, self.zoom_scale - 0.1)
                    elif event.button == 3:
                        self.is_panning = True
                        self.last_mouse_pos = pygame.mouse.get_pos()
                    elif event.button == 1:
                        if mouse_pos[1] > self.window_height - 110:
                            self.process_sim_button_clicks(mouse_pos)
                        elif mouse_pos[0] >= 590:
                            self.process_brush_button_clicks(mouse_pos)
                        else:
                            self.handle_grid_click(mouse_pos)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 3:
                        self.is_panning = False

                elif event.type == pygame.MOUSEMOTION:
                    if self.is_panning:
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        self.pan_offset_x += mouse_x - self.last_mouse_pos[0]
                        self.pan_offset_y += mouse_y - self.last_mouse_pos[1]
                        self.last_mouse_pos = (mouse_x, mouse_y)
        return True

    def process_brush_button_clicks(self, mouse_pos):
        for btn in self.brush_buttons:
            if btn.is_clicked(mouse_pos):
                if "Dat tai nan" in btn.text:
                    self.brush_mode = 'ACCIDENT'
                elif "Dat benh vien" in btn.text:
                    self.brush_mode = 'HOSPITAL'
                elif "Ve tuong nha" in btn.text:
                    self.brush_mode = 'WALL'
                elif "Ve vung ket xe" in btn.text:
                    self.brush_mode = 'TRAFFIC'
                elif "Xoa o tren map" in btn.text:
                    self.brush_mode = 'ERASE'
                self.update_active_button_states()

    def handle_grid_click(self, mouse_pos):
        adjusted_x = (mouse_pos[0] - self.pan_offset_x) / self.zoom_scale
        adjusted_y = (mouse_pos[1] - self.pan_offset_y) / self.zoom_scale
        col = int(adjusted_x // config.CELL_SIZE)
        row = int(adjusted_y // config.CELL_SIZE)

        if 0 <= row < config.GRID_SIZE and 0 <= col < config.GRID_SIZE:

            # 1. CHẾ ĐỘ TẨY XÓA O
            if self.brush_mode == 'ERASE':
                current_state = self.env.grid[row][col]
                if current_state == config.STATE_HOSPITAL:
                    target_key = None
                    for h_name, h_info in config.HOSPITAL_CONFIG.items():
                        if h_info["pos"] == (row, col):
                            target_key = h_name
                            break
                    if target_key:
                        config.HOSPITAL_CONFIG.pop(target_key, None)
                        self.dispatcher.current_cars.pop(target_key, None)
                elif current_state == config.STATE_ACCIDENT:
                    if (row, col) in self.env.accidents_pool:
                        self.env.accidents_pool.remove((row, col))
                self.env.grid[row][col] = config.STATE_EMPTY

            # 2. CHẾ ĐỘ ĐẶT BỆNH VIỆN
            elif self.brush_mode == 'HOSPITAL':
                if self.env.grid[row][col] in [config.STATE_EMPTY, config.STATE_WALL]:
                    self.show_popup = True
                    self.popup_target_pos = (row, col)
                    self.popup_car_count = 3

            # 3. CHẾ ĐỘ VẼ TƯỜNG CẢN (Đã sửa lỗi thụt đầu dòng logic)
            elif self.brush_mode == 'WALL':
                if self.env.grid[row][col] == config.STATE_EMPTY:
                    self.env.grid[row][col] = config.STATE_WALL

            # 4. CHẾ ĐỘ VẼ ĐƯỜNG KẸT XE
            elif self.brush_mode == 'TRAFFIC':
                if self.env.grid[row][col] == config.STATE_EMPTY:
                    self.env.grid[row][col] = config.STATE_TRAFFIC

            # 5. CHẾ ĐỘ BÁO TAI NẠN XUẤT XE
            elif self.brush_mode == 'ACCIDENT':
                if self.env.grid[row][col] == config.STATE_EMPTY:
                    accident_pos = (row, col)
                    self.env.grid[row][col] = config.STATE_ACCIDENT
                    self.env.accidents_pool.append(accident_pos)

                    chosen_hospital, optimal_path = self.dispatcher.evaluate_and_dispatch(accident_pos, self.env)
                    if chosen_hospital and optimal_path:
                        h_pos = config.HOSPITAL_CONFIG[chosen_hospital]["pos"]
                        if self.current_mode == config.MODE_ASTAR_Q:
                            new_ambulance = AStarQAgent(h_pos, accident_pos)
                            new_ambulance.calculated_path = optimal_path
                        else:
                            new_ambulance = LRTALearningAgent(h_pos, accident_pos)
                        self.active_agents.append(new_ambulance)

    def handle_popup_click(self, mouse_pos):
        px = self.window_width // 2 - 120
        py = self.window_height // 2 - 60
        btn_minus = pygame.Rect(px + 40, py + 40, 30, 25)
        btn_plus = pygame.Rect(px + 140, py + 40, 30, 25)
        btn_confirm = pygame.Rect(px + 60, py + 80, 100, 30)

        if btn_minus.collidepoint(mouse_pos):
            self.popup_car_count = max(1, self.popup_car_count - 1)
        elif btn_plus.collidepoint(mouse_pos):
            self.popup_car_count = min(9, self.popup_car_count + 1)
        elif btn_confirm.collidepoint(mouse_pos):
            row, col = self.popup_target_pos
            h_name = f"HOSPITAL_{row}_{col}"
            config.HOSPITAL_CONFIG[h_name] = {"pos": (row, col), "max_cars": self.popup_car_count}
            self.dispatcher.hospitals = config.HOSPITAL_CONFIG
            self.dispatcher.current_cars[h_name] = self.popup_car_count
            self.env.grid[row][col] = config.STATE_HOSPITAL
            self.show_popup = False
            self.popup_target_pos = None

    def draw_popup(self):
        w, h = 240, 130
        px = self.window_width // 2 - w // 2
        py = self.window_height // 2 - h // 2

        pygame.draw.rect(self.screen, (255, 255, 255), (px, py, w, h), border_radius=8)
        pygame.draw.rect(self.screen, (44, 62, 80), (px, py, w, h), 2, border_radius=8)

        txt_title = self.font.render("SO XE CAP CUU BAN DAU:", True, (44, 62, 80))
        self.screen.blit(txt_title, (px + 35, py + 15))

        pygame.draw.rect(self.screen, (192, 57, 43), (px + 40, py + 40, 30, 25), border_radius=3)
        txt_minus = self.font_large.render("-", True, (255, 255, 255))
        self.screen.blit(txt_minus, (px + 51, py + 42))

        txt_num = self.font_large.render(str(self.popup_car_count), True, (44, 62, 80))
        self.screen.blit(txt_num, (px + 108, py + 43))

        pygame.draw.rect(self.screen, (46, 204, 113), (px + 140, py + 40, 30, 25), border_radius=3)
        txt_plus = self.font_large.render("+", True, (255, 255, 255))
        self.screen.blit(txt_plus, (px + 149, py + 42))

        pygame.draw.rect(self.screen, (41, 128, 185), (px + 60, py + 80, 100, 30), border_radius=4)
        txt_cf = self.font.render("XAC NHAN", True, (255, 255, 255))
        self.screen.blit(txt_cf, (px + 80, py + 88))

    def process_sim_button_clicks(self, mouse_pos):
        for btn in self.sim_buttons:
            if btn.is_clicked(mouse_pos):
                if btn.mode_id in [config.MODE_ASTAR_Q, config.MODE_LRTASTAR_Q]:
                    self.current_mode = btn.mode_id
                    self.update_active_button_states()
                elif btn.text in ["Gio cao diem (17h)", "Gio binh thuong (12h)"]:
                    if self.current_hour == 12:
                        self.current_hour = 17
                        btn.text = "Gio binh thuong (12h)"
                        btn.is_active = True
                    else:
                        self.current_hour = 12
                        btn.text = "Gio cao diem (17h)"
                        btn.is_active = False
                    self.env.set_traffic_jam(self.current_hour)
                elif btn.text == "Reset sach map":
                    self.active_agents.clear()
                    self.env.accidents_pool.clear()
                    config.HOSPITAL_CONFIG.clear()
                    self.dispatcher.reset_resources()
                    self.env.grid = [[config.STATE_EMPTY for _ in range(config.GRID_SIZE)] for _ in
                                     range(config.GRID_SIZE)]
                    self.app_state = 'MENU'
                    self.reposition_buttons()

    # --- ĐÃ BỔ SUNG LẠI HÀM UPDATE_SIMULATION BỊ THIẾU TẠI ĐÂY ---
    def update_simulation(self):
        if self.show_popup: return
        for agent in self.active_agents:
            if not agent.is_finished:
                if isinstance(agent, LRTALearningAgent):
                    agent.update_route_realtime_with_return(self.env, self)
                else:
                    agent.update_astar_return_logic(self.env, self)

    def draw_menu(self):
        self.screen.fill((44, 62, 80))
        title_surf = self.font_large.render("HE THONG DIEU PHOI CUU HO THONG MINH", True, (241, 196, 15))
        title_rect = title_surf.get_rect(center=(self.window_width // 2, self.window_height // 2 - 120))
        self.screen.blit(title_surf, title_rect)
        for btn in self.menu_buttons: btn.draw(self.screen, self.font)

    def draw_simulation(self):
        self.screen.fill((240, 244, 248))

        base_map_w = config.GRID_SIZE * config.CELL_SIZE
        base_map_h = config.GRID_SIZE * config.CELL_SIZE
        scaled_w = int(base_map_w * self.zoom_scale)
        scaled_h = int(base_map_h * self.zoom_scale)

        if scaled_w <= 0 or scaled_h <= 0: return

        map_surface = pygame.Surface((base_map_w, base_map_h))
        map_surface.fill((255, 255, 255))

        for r in range(config.GRID_SIZE):
            for c in range(config.GRID_SIZE):
                state = self.env.grid[r][c]
                color = config.COLOR_EMPTY
                if state == config.STATE_WALL:
                    color = config.COLOR_WALL
                elif state == config.STATE_TRAFFIC:
                    color = config.COLOR_TRAFFIC
                elif state == config.STATE_ACCIDENT:
                    color = config.COLOR_ACCIDENT
                elif state == config.STATE_HOSPITAL:
                    color = config.COLOR_HOSPITAL

                rect = pygame.Rect(c * config.CELL_SIZE, r * config.CELL_SIZE, config.CELL_SIZE, config.CELL_SIZE)
                pygame.draw.rect(map_surface, color, rect)
                pygame.draw.rect(map_surface, (235, 240, 245), rect, 1)

        for agent in self.active_agents: agent.draw(map_surface)

        scaled_map = pygame.transform.smoothscale(map_surface, (scaled_w, scaled_h))
        self.screen.blit(scaled_map, (self.pan_offset_x, self.pan_offset_y))

        # Khóa dải UI đáy
        pygame.draw.rect(self.screen, (255, 255, 255), (0, self.window_height - 110, self.window_width, 110))
        pygame.draw.line(self.screen, (189, 195, 199), (0, self.window_height - 110),
                         (self.window_width, self.window_height - 110), 2)

        # Khóa bảng Brush bên phải
        pygame.draw.rect(self.screen, (255, 255, 255), (590, 0, self.window_width - 590, self.window_height - 110))
        pygame.draw.line(self.screen, (189, 195, 199), (590, 0), (590, self.window_height - 110), 2)

        txt_brush = self.font.render("CONG CU VE CHUOT:", True, (44, 62, 80))
        self.screen.blit(txt_brush, (610, 12))

        for btn in self.sim_buttons: btn.draw(self.screen, self.font)
        for btn in self.brush_buttons: btn.draw(self.screen, self.font)

        # Định vị bảng kho xe động co giãn
        start_x = 600
        start_y = self.window_height - 95
        pygame.draw.rect(self.screen, (241, 242, 246),
                         (start_x - 10, start_y - 5, self.window_width - start_x - 10, 55), border_radius=5)

        title_surf = self.font.render("KHO XE CAP CUU KHA DUNG HIEN TAI:", True, (44, 62, 80))
        self.screen.blit(title_surf, (start_x, start_y))

        status_list = [f"Vien({k[-5:]}):{v}xe" for k, v in self.dispatcher.current_cars.items()]
        car_status_str = " | ".join(status_list) if status_list else "Chua co benh vien nao"
        car_status_surf = self.font.render(car_status_str, True, (192, 57, 43))
        self.screen.blit(car_status_surf, (start_x, start_y + 20))

        mode_text = "A* + Q-Learning" if self.current_mode == config.MODE_ASTAR_Q else "LRTA* + Q-Learning"
        status_str = f"Khung gio: {self.current_hour}h00  |  He thong: {mode_text}  |  Zoom Map: {int(self.zoom_scale * 100)}%"
        status_surf = self.font.render(status_str, True, config.COLOR_TEXT)
        self.screen.blit(status_surf, (15, self.window_height - 35))

        if self.show_popup:
            self.draw_popup()

    def run(self):
        while self.handle_events():
            if self.app_state == 'MENU':
                self.draw_menu()
            elif self.app_state == 'SIMULATION':
                self.update_simulation()
                self.draw_simulation()
            pygame.display.flip()
            self.clock.tick(5)
        pygame.quit()


if __name__ == "__main__":
    SimulationApp().run()