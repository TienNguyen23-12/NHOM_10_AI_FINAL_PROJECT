import config
from agents.base_agent import BaseAgent


class LRTALearningAgent(BaseAgent):
    def __init__(self, start_pos, goal_pos):
        super().__init__(start_pos, goal_pos, color=(142, 68, 173))
        self.h_table = {}
        self.original_hospital_pos = start_pos
        self.is_returning = False

        self.vis_open_set = set()
        self.vis_visited = set()
        self.vis_path = []

    def get_h(self, pos):
        if pos not in self.h_table:
            self.h_table[pos] = abs(pos[0] - self.goal_pos[0]) + abs(pos[1] - self.goal_pos[1])
        return self.h_table[pos]

    def update_route_realtime_with_return(self, grid_map, app_instance):
        if self.is_finished: return

        if self.current_pos == self.goal_pos and not self.is_returning:
            self.is_returning = True
            if self.goal_pos in grid_map.accidents_pool:
                grid_map.accidents_pool.remove(self.goal_pos)
                grid_map.grid[self.goal_pos[0]][self.goal_pos[1]] = config.STATE_EMPTY

            self.path = [self.current_pos]
            self.goal_pos = self.original_hospital_pos
            self.h_table.clear()

        elif self.current_pos == self.original_hospital_pos and self.is_returning:
            self.is_finished = True
            self.path.clear();
            self.vis_open_set.clear()
            self.vis_visited.clear();
            self.vis_path.clear()

            found_hospital = next((name for name, info in app_instance.dispatcher.hospitals.items() if
                                   info["pos"] == self.original_hospital_pos), None)
            if found_hospital and found_hospital in app_instance.dispatcher.current_cars:
                app_instance.dispatcher.current_cars[found_hospital] += 1
                app_instance.logger.add_log(f"[STATION] Xe LRTA* returned, fleet recovered at {found_hospital}.")
            return

        current = self.current_pos
        best_next = None
        min_f = float('inf')
        radar_scanned_cells = set()

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (current[0] + dr, current[1] + dc)
            if grid_map.is_valid_move(neighbor):
                radar_scanned_cells.add(neighbor)
                cost = 1 if neighbor == self.goal_pos else grid_map.get_cost(neighbor)
                f_value = cost + self.get_h(neighbor)
                if f_value < min_f:
                    min_f = f_value;
                    best_next = neighbor

        if hasattr(app_instance, 'visualize_search') and app_instance.visualize_search:
            self.vis_open_set = radar_scanned_cells
            self.vis_visited = {current}
            self.vis_path = [current, best_next] if best_next else [current]
        else:
            self.vis_open_set.clear()
            self.vis_visited.clear()
            self.vis_path.clear()

        if best_next:
            self.h_table[current] = max(self.get_h(current), min_f)
            self.move_to(best_next)