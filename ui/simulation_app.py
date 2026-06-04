# ui/simulation_app.py
import pygame
import config
from environment.grid_map import GridMap
from ui.ui_manager import UIManager
from ui.logger_panel import LoggerPanel
from ui.inspector_panel import InspectorPanel
from utils.q_learning import QLearningModel
from utils.dispatch_center import DispatchCenter
from agents.astar_q_agent import AStarQAgent
from agents.lrtastar_q_agent import LRTALearningAgent


class SimulationApp:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.window_width = 1180
        self.window_height = config.GRID_SIZE * config.CELL_SIZE + 180
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        pygame.display.set_caption("Multi-Agent Intelligence Rescue Dashboard - HCMUTE")

        self.font = pygame.font.SysFont("Segoe UI", 14)
        self.font_bold = pygame.font.SysFont("Segoe UI", 14, bold=True)
        self.font_large = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.clock = pygame.time.Clock()

        self.app_state = 'MENU'
        self.env = GridMap()
        self.env.grid = [[config.STATE_EMPTY for _ in range(config.GRID_SIZE)] for _ in range(config.GRID_SIZE)]
        config.HOSPITAL_CONFIG.clear()

        self.ui_mgr = UIManager(self.window_width, self.window_height)
        self.logger = LoggerPanel(15, self.window_height - 105, 560, 100)

        monitor_x = self.window_width - 415
        self.monitor = InspectorPanel(monitor_x, 35, 400, self.window_height - 200)
        self.monitor.set_welcome()

        self.global_q_brain = QLearningModel()
        self.dispatcher = DispatchCenter(self.global_q_brain)
        self.dispatcher.reset_resources()

        self.active_agents = []
        self.current_mode = config.MODE_ASTAR_Q
        self.current_hour = 12
        self.brush_mode = 'ACCIDENT'

        self.show_popup = False
        self.popup_target_pos = None
        self.popup_car_count = 3
        self.zoom_scale = 1.0
        self.pan_offset_x = 20
        self.pan_offset_y = 20
        self.is_panning = False
        self.last_mouse_pos = (0, 0)

        # --- Biến quản lý thanh cuộn ngang của bảng Fleet ---
        self.fleet_scroll_x = 0
        self.max_fleet_scroll = 0

        self.ui_mgr.update_button_states(self.current_mode, self.brush_mode)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.VIDEORESIZE:
                self.window_width, self.window_height = event.w, event.h
                self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
                self.ui_mgr.window_width, self.ui_mgr.window_height = event.w, event.h
                self.ui_mgr.reposition_buttons()

                self.logger.y = self.window_height - 105
                self.monitor.x = self.window_width - 415
                self.monitor.height = self.window_height - 200
                continue

            # --- ĐÃ FIX LOGIC SỰ KIỆN: Chia vùng cuộn chuột cho Fleet và Monitor ---
            elif event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                brush_x = self.window_width - 590
                fleet_rect = pygame.Rect(brush_x, self.window_height - 145, self.window_width - brush_x - 15, 40)

                # Nếu chuột đang trỏ vào thanh Fleet -> Cuộn ngang
                if fleet_rect.collidepoint((mx, my)):
                    # Hỗ trợ cả Trackpad (cuộn x) và Chuột thường (cuộn y)
                    scroll_val = event.x if event.x != 0 else event.y
                    self.fleet_scroll_x += scroll_val * 40
                    if self.fleet_scroll_x > 0: self.fleet_scroll_x = 0
                    if self.fleet_scroll_x < -self.max_fleet_scroll: self.fleet_scroll_x = -self.max_fleet_scroll
                else:
                    # Nếu không, chuyền sự kiện cuộn dọc cho Monitor Panel
                    self.monitor.handle_event(event)

            mouse_pos = pygame.mouse.get_pos()

            if self.app_state == 'SIMULATION' and self.show_popup:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_popup_click(mouse_pos)
                continue

            if self.app_state == 'MENU':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for btn in self.ui_mgr.menu_buttons:
                        if btn.is_clicked(mouse_pos):
                            if "Custom Map" in btn.text:
                                self.env.grid = [[config.STATE_EMPTY for _ in range(config.GRID_SIZE)] for _ in
                                                 range(config.GRID_SIZE)]
                                config.HOSPITAL_CONFIG.clear()
                                self.dispatcher.reset_resources()
                                self.logger.add_log("[SYSTEM] Switched to customizable sandbox canvas mode.")
                            else:
                                self.env.grid = [[config.STATE_EMPTY for _ in range(config.GRID_SIZE)] for _ in
                                                 range(config.GRID_SIZE)]
                                config.HOSPITAL_CONFIG = {"HOSPITAL_1": {"pos": (2, 2), "max_cars": 2},
                                                          "HOSPITAL_2": {"pos": (2, 17), "max_cars": 3},
                                                          "HOSPITAL_3": {"pos": (17, 9), "max_cars": 2}}
                                self.env.generate_default_map()
                                self.dispatcher.hospitals = config.HOSPITAL_CONFIG
                                self.dispatcher.reset_resources()
                                self.logger.add_log("[SYSTEM] Random node network topology generated successfully.")
                            self.app_state = 'SIMULATION'

            elif self.app_state == 'SIMULATION':
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 3:
                        self.is_panning = True
                        self.last_mouse_pos = pygame.mouse.get_pos()
                    elif event.button == 1:
                        brush_x = self.window_width - 590
                        if mouse_pos[1] > self.window_height - 160:
                            self.process_sim_button_clicks(mouse_pos)
                        elif mouse_pos[0] >= brush_x:
                            self.process_inspect_button_clicks(mouse_pos)
                            self.process_brush_button_clicks(mouse_pos)
                        else:
                            self.handle_grid_click(mouse_pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                    self.is_panning = False
                elif event.type == pygame.MOUSEMOTION and self.is_panning:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    self.pan_offset_x += mouse_x - self.last_mouse_pos[0]
                    self.pan_offset_y += mouse_y - self.last_mouse_pos[1]
                    self.last_mouse_pos = (mouse_x, mouse_y)
        return True

    def process_brush_button_clicks(self, mouse_pos):
        for btn in self.ui_mgr.brush_buttons:
            if btn.is_clicked(mouse_pos):
                if "Accident" in btn.text:
                    self.brush_mode = 'ACCIDENT'
                elif "Hospital" in btn.text:
                    self.brush_mode = 'HOSPITAL'
                elif "Wall" in btn.text:
                    self.brush_mode = 'WALL'
                elif "Traffic" in btn.text:
                    self.brush_mode = 'TRAFFIC'
                elif "Clear" in btn.text:
                    self.brush_mode = 'ERASE'
                self.ui_mgr.update_button_states(self.current_mode, self.brush_mode)

    def process_inspect_button_clicks(self, mouse_pos):
        for btn in self.ui_mgr.inspect_buttons:
            if btn.is_clicked(mouse_pos):
                if "Q-Table" in btn.text:
                    self.monitor.load_q_table(self.global_q_brain.q_table)
                elif "H-Table" in btn.text:
                    self.monitor.load_h_table(self.active_agents)
                elif "Routes" in btn.text:
                    self.monitor.load_paths(self.active_agents)

    def handle_grid_click(self, mouse_pos):
        adj_x = (mouse_pos[0] - self.pan_offset_x) / self.zoom_scale
        adj_y = (mouse_pos[1] - self.pan_offset_y) / self.zoom_scale
        col, row = int(adj_x // config.CELL_SIZE), int(adj_y // config.CELL_SIZE)

        if 0 <= row < config.GRID_SIZE and 0 <= col < config.GRID_SIZE:
            if self.brush_mode == 'ERASE':
                curr = self.env.grid[row][col]
                if curr == config.STATE_HOSPITAL:
                    key = next((k for k, v in config.HOSPITAL_CONFIG.items() if v["pos"] == (row, col)), None)
                    if key: config.HOSPITAL_CONFIG.pop(key); self.dispatcher.current_cars.pop(key)
                elif curr == config.STATE_ACCIDENT and (row, col) in self.env.accidents_pool:
                    self.env.accidents_pool.remove((row, col))
                self.env.grid[row][col] = config.STATE_EMPTY
            elif self.brush_mode == 'HOSPITAL' and self.env.grid[row][col] in [config.STATE_EMPTY, config.STATE_WALL]:
                self.show_popup, self.popup_target_pos, self.popup_car_count = True, (row, col), 3
            elif self.brush_mode == 'WALL' and self.env.grid[row][col] == config.STATE_EMPTY:
                self.env.grid[row][col] = config.STATE_WALL
            elif self.brush_mode == 'TRAFFIC' and self.env.grid[row][col] == config.STATE_EMPTY:
                self.env.grid[row][col] = config.STATE_TRAFFIC
            elif self.brush_mode == 'ACCIDENT' and self.env.grid[row][col] == config.STATE_EMPTY:
                acc_pos = (row, col)
                self.env.grid[row][col] = config.STATE_ACCIDENT
                self.env.accidents_pool.append(acc_pos)
                self.logger.add_log(f"[ALERT] New emergency incident logged at area ({row}, {col})!")
                h_name, path = self.dispatcher.evaluate_and_dispatch(acc_pos, self.env)
                if h_name and path:
                    agent = AStarQAgent(config.HOSPITAL_CONFIG[h_name]["pos"],
                                        acc_pos) if self.current_mode == config.MODE_ASTAR_Q else LRTALearningAgent(
                        config.HOSPITAL_CONFIG[h_name]["pos"], acc_pos)
                    if self.current_mode == config.MODE_ASTAR_Q: agent.calculated_path = path
                    self.active_agents.append(agent)
                    self.logger.add_log(f"-> [DISPATCH] Ambulance deploying from depot {h_name}.")

    def handle_popup_click(self, mouse_pos):
        px, py = self.window_width // 2 - 120, self.window_height // 2 - 60
        if pygame.Rect(px + 40, py + 40, 30, 25).collidepoint(mouse_pos):
            self.popup_car_count = max(1, self.popup_car_count - 1)
        elif pygame.Rect(px + 140, py + 40, 30, 25).collidepoint(mouse_pos):
            self.popup_car_count = min(9, self.popup_car_count + 1)
        elif pygame.Rect(px + 60, py + 80, 100, 30).collidepoint(mouse_pos):
            r, c = self.popup_target_pos
            name = f"HOSPITAL_{r}_{c}"
            config.HOSPITAL_CONFIG[name] = {"pos": (r, c), "max_cars": self.popup_car_count}
            self.dispatcher.hospitals = config.HOSPITAL_CONFIG
            self.dispatcher.current_cars[name] = self.popup_car_count
            self.env.grid[r][c] = config.STATE_HOSPITAL
            self.logger.add_log(f"[STATION] Setup hospital {name} with fleet allocation: {self.popup_car_count} cars.")
            self.show_popup = False

    def draw_popup(self):
        w, h = 240, 130
        px, py = self.window_width // 2 - w // 2, self.window_height // 2 - h // 2
        pygame.draw.rect(self.screen, (255, 255, 255), (px, py, w, h), border_radius=8)
        pygame.draw.rect(self.screen, (44, 62, 80), (px, py, w, h), 2, border_radius=8)
        self.screen.blit(self.font_bold.render("INITIAL FLEET COUNT:", True, (44, 62, 80)), (px + 35, py + 15))
        pygame.draw.rect(self.screen, (192, 57, 43), (px + 40, py + 40, 30, 25), border_radius=3)
        self.screen.blit(self.font_large.render("-", True, (255, 255, 255)), (px + 51, py + 38))
        self.screen.blit(self.font_large.render(str(self.popup_car_count), True, (44, 62, 80)), (px + 108, py + 38))
        pygame.draw.rect(self.screen, (46, 204, 113), (px + 140, py + 40, 30, 25), border_radius=3)
        self.screen.blit(self.font_large.render("+", True, (255, 255, 255)), (px + 147, py + 38))
        pygame.draw.rect(self.screen, (41, 128, 185), (px + 60, py + 80, 100, 30), border_radius=4)
        self.screen.blit(self.font_bold.render("CONFIRM", True, (255, 255, 255)), (px + 82, py + 86))

    def process_sim_button_clicks(self, mouse_pos):
        for btn in self.ui_mgr.sim_buttons:
            if btn.is_clicked(mouse_pos):
                if btn.mode_id in [config.MODE_ASTAR_Q, config.MODE_LRTASTAR_Q]:
                    self.current_mode = btn.mode_id
                    self.ui_mgr.update_button_states(self.current_mode, self.brush_mode)
                    self.logger.add_log(
                        f"[SYSTEM] Switched execution to: {'A* + Q' if self.current_mode == config.MODE_ASTAR_Q else 'LRTA* + Q'}")
                elif "Hour" in btn.text:
                    self.current_hour = 17 if self.current_hour == 12 else 12
                    btn.text = "Standard Hour (12h)" if self.current_hour == 17 else "Rush Hour (17h)"
                    btn.is_active = (self.current_hour == 17)
                    self.env.set_traffic_jam(self.current_hour)
                    self.logger.add_log(f"[TRAFFIC] Timetable altered to {self.current_hour}h00.")
                elif "Clear Map" in btn.text:
                    self.active_agents.clear();
                    self.env.accidents_pool.clear();
                    config.HOSPITAL_CONFIG.clear()
                    self.dispatcher.reset_resources();
                    self.env.grid = [[config.STATE_EMPTY for _ in range(config.GRID_SIZE)] for _ in
                                     range(config.GRID_SIZE)]
                    self.app_state = 'MENU';
                    self.ui_mgr.reposition_buttons();
                    self.monitor.set_welcome()
                    self.fleet_scroll_x = 0  # Reset cuộn xe

    def update_simulation(self):
        if self.show_popup: return
        for agent in self.active_agents:
            if not agent.is_finished:
                old_pos = agent.current_pos
                if isinstance(agent, LRTALearningAgent):
                    agent.update_route_realtime_with_return(self.env, self)
                else:
                    agent.update_astar_return_logic(self.env, self)

                if agent.current_pos != old_pos:
                    dr = agent.current_pos[0] - old_pos[0]
                    dc = agent.current_pos[1] - old_pos[1]
                    if (dr, dc) in self.global_q_brain.actions:
                        action_idx = self.global_q_brain.actions.index((dr, dc))
                        reward = -self.env.get_cost(agent.current_pos)
                        self.global_q_brain.update_q_value(old_pos, action_idx, reward, agent.current_pos)
                        if self.monitor.display_mode == "Q_TABLE":
                            self.monitor.load_q_table(self.global_q_brain.q_table)

    def draw_simulation(self):
        self.screen.fill((240, 244, 248))
        base_w, base_h = config.GRID_SIZE * config.CELL_SIZE, config.GRID_SIZE * config.CELL_SIZE
        s_w, s_h = int(base_w * self.zoom_scale), int(base_h * self.zoom_scale)
        if s_w <= 0 or s_h <= 0: return

        map_surface = pygame.Surface((base_w, base_h))
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
                pygame.draw.rect(map_surface, color,
                                 pygame.Rect(c * config.CELL_SIZE, r * config.CELL_SIZE, config.CELL_SIZE,
                                             config.CELL_SIZE))
                pygame.draw.rect(map_surface, (235, 240, 245),
                                 pygame.Rect(c * config.CELL_SIZE, r * config.CELL_SIZE, config.CELL_SIZE,
                                             config.CELL_SIZE), 1)

        for agent in self.active_agents: agent.draw(map_surface)
        self.screen.blit(pygame.transform.smoothscale(map_surface, (s_w, s_h)), (self.pan_offset_x, self.pan_offset_y))

        brush_x = self.window_width - 590
        inspect_x = self.window_width - 415

        pygame.draw.rect(self.screen, (255, 255, 255), (0, self.window_height - 165, self.window_width, 165))
        pygame.draw.line(self.screen, (189, 195, 199), (0, self.window_height - 165),
                         (self.window_width, self.window_height - 165), 2)
        pygame.draw.rect(self.screen, (255, 255, 255),
                         (brush_x - 10, 0, self.window_width - (brush_x - 10), self.window_height - 165))
        pygame.draw.line(self.screen, (189, 195, 199), (brush_x - 10, 0), (brush_x - 10, self.window_height - 165), 2)
        pygame.draw.line(self.screen, (189, 195, 199), (inspect_x - 10, 0), (inspect_x - 10, self.window_height - 165),
                         1)

        self.screen.blit(self.font_bold.render("BRUSH TOOLS:", True, (44, 62, 80)), (brush_x, 15))
        self.screen.blit(self.font_bold.render("AI CONTROLS:", True, (44, 62, 80)), (brush_x, 240))
        self.screen.blit(self.font_bold.render("LIVE AI MONITOR:", True, (44, 62, 80)), (inspect_x, 15))

        self.ui_mgr.draw_all(self.screen, self.font)
        self.logger.draw(self.screen, self.font)
        self.monitor.draw(self.screen, self.font, self.font_bold)

        # --- ĐÃ FIX BẢNG FLEET: THÊM CƠ CHẾ CUỘN NGANG VÀ CHUẨN HÓA TÊN H(x,y) ---
        fleet_rect = pygame.Rect(brush_x, self.window_height - 145, self.window_width - brush_x - 15, 40)
        pygame.draw.rect(self.screen, (241, 242, 246), fleet_rect, border_radius=5)

        title_surf = self.font_bold.render("AVAILABLE FLEET:", True, (44, 62, 80))
        self.screen.blit(title_surf, (brush_x + 10, self.window_height - 133))

        # Thiết lập vùng hiển thị chữ và khung mặt nạ
        content_x_start = brush_x + title_surf.get_width() + 20
        content_width = fleet_rect.width - title_surf.get_width() - 20
        content_rect = pygame.Rect(content_x_start, fleet_rect.y, content_width, fleet_rect.height)

        if not self.dispatcher.current_cars:
            car_status_surf = self.font_bold.render("No active hospitals deployed", True, (192, 57, 43))
            self.screen.blit(car_status_surf, (content_x_start, self.window_height - 133))
            self.max_fleet_scroll = 0
        else:
            status_list = []
            for k, v in self.dispatcher.current_cars.items():
                # Lấy tọa độ chuẩn tuyệt đối từ bộ nhớ Dispatcher
                if k in self.dispatcher.hospitals:
                    pos = self.dispatcher.hospitals[k]["pos"]
                    short_name = f"H({pos[0]},{pos[1]})"
                else:
                    short_name = k
                status_list.append(f"{short_name}: {v} cars")

            cars_str = "   |   ".join(status_list)
            car_status_surf = self.font_bold.render(cars_str, True, (192, 57, 43))

            # Tính giới hạn cuộn
            self.max_fleet_scroll = max(0, car_status_surf.get_width() - content_width + 15)
            if self.fleet_scroll_x < -self.max_fleet_scroll: self.fleet_scroll_x = -self.max_fleet_scroll

            # Áp dụng Clipping Mask (Chỉ vẽ chữ nằm gọn trong khung xám)
            old_clip = self.screen.get_clip()
            self.screen.set_clip(content_rect)
            self.screen.blit(car_status_surf, (content_x_start + self.fleet_scroll_x, self.window_height - 133))
            self.screen.set_clip(old_clip)

            # Vẽ thêm cái vạch thanh cuộn mỏng ở đáy hộp nếu danh sách bị dài quá
            if self.max_fleet_scroll > 0:
                bar_width = max(30, content_width * (content_width / (car_status_surf.get_width() + 20)))
                bar_x = content_x_start + (-self.fleet_scroll_x / self.max_fleet_scroll) * (content_width - bar_width)
                pygame.draw.rect(self.screen, (180, 185, 190), (bar_x, fleet_rect.bottom - 5, bar_width, 3),
                                 border_radius=2)

        status_str = f"Timetable: {self.current_hour}h00  |  Solver Engine: {'A* + Q-Learning' if self.current_mode == config.MODE_ASTAR_Q else 'LRTA* + Q-Learning'}  |  Scale: {int(self.zoom_scale * 100)}%"
        self.screen.blit(self.font.render(status_str, True, config.COLOR_TEXT), (15, self.window_height - 25))
        if self.show_popup: self.draw_popup()

    def run(self):
        while self.handle_events():
            if self.app_state == 'MENU':
                self.screen.fill((44, 62, 80))
                self.screen.blit(self.font_large.render("MULTI-AGENT EMERGENCY DISPATCH SYSTEM", True, (241, 196, 15)),
                                 (self.window_width // 2 - 250, self.window_height // 2 - 80))
                for btn in self.ui_mgr.menu_buttons: btn.draw(self.screen, self.font)
            elif self.app_state == 'SIMULATION':
                self.update_simulation();
                self.draw_simulation()
            pygame.display.flip();
            self.clock.tick(5)
        pygame.quit()