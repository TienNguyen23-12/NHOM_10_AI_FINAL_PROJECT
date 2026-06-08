# utils/dispatch_center.py
import heapq
import config

class DispatchCenter:
    def __init__(self, q_brain):
        self.q_brain = q_brain
        self.hospitals = {}
        self.current_cars = {}

    def reset_resources(self):
        self.hospitals = config.HOSPITAL_CONFIG.copy()
        self.current_cars = {k: v["max_cars"] for k, v in self.hospitals.items()}

    def evaluate_and_dispatch(self, acc_pos, grid_map):
        best_hospital = None
        best_cost = float('inf')
        best_path = None

        for h_name, h_info in self.hospitals.items():
            if self.current_cars.get(h_name, 0) <= 0: continue
            start = h_info["pos"]
            path, cost = self._calculate_cost(start, acc_pos, grid_map)
            if cost < best_cost:
                best_cost = cost
                best_hospital = h_name
                best_path = path

        if best_hospital:
            self.current_cars[best_hospital] -= 1
            return best_hospital, best_path
        return None, None

    def _calculate_cost(self, start, goal, grid_map):
        open_set = []
        heapq.heappush(open_set, (0, 0, start, [start]))
        visited = set()
        while open_set:
            f, g, current, path = heapq.heappop(open_set)
            if current == goal: return path, g
            if current in visited: continue
            visited.add(current)
            for action_idx, (dr, dc) in enumerate(self.q_brain.actions):
                neighbor = (current[0] + dr, current[1] + dc)
                if grid_map.is_valid_move(neighbor) and neighbor not in visited:
                    base_cost = grid_map.get_cost(neighbor)
                    q_vals = self.q_brain.q_table.get(current, [0, 0, 0, 0])
                    q_pen = -q_vals[action_idx] if q_vals[action_idx] < 0 else 0
                    new_g = g + base_cost + q_pen
                    h_val = abs(neighbor[0] - goal[0]) + abs(neighbor[1] - goal[1])
                    heapq.heappush(open_set, (new_g + h_val, new_g, neighbor, path + [neighbor]))
        return None, float('inf')

    def evaluate_generator(self, acc_pos, grid_map):
        best_hospital = None
        best_cost = float('inf')
        best_path = None
        for h_name, h_info in self.hospitals.items():
            if self.current_cars.get(h_name, 0) <= 0: continue
            start = h_info["pos"]
            open_set = []
            heapq.heappush(open_set, (0, 0, start, [start]))
            visited = set()
            open_set_tracker = {start}
            steps = 0
            while open_set:
                f, g, current, path = heapq.heappop(open_set)
                if current in open_set_tracker: open_set_tracker.remove(current)
                if current == acc_pos:
                    if g < best_cost:
                        best_cost = g
                        best_hospital = h_name
                        best_path = path
                    yield open_set_tracker, visited, path, h_name, False
                    break
                if current in visited: continue
                visited.add(current)
                for action_idx, (dr, dc) in enumerate(self.q_brain.actions):
                    neighbor = (current[0] + dr, current[1] + dc)
                    if grid_map.is_valid_move(neighbor) and neighbor not in visited:
                        base_cost = grid_map.get_cost(neighbor)
                        q_vals = self.q_brain.q_table.get(current, [0, 0, 0, 0])
                        q_pen = -q_vals[action_idx] if q_vals[action_idx] < 0 else 0
                        new_g = g + base_cost + q_pen
                        h_val = abs(neighbor[0] - acc_pos[0]) + abs(neighbor[1] - acc_pos[1])
                        heapq.heappush(open_set, (new_g + h_val, new_g, neighbor, path + [neighbor]))
                        open_set_tracker.add(neighbor)
                steps += 1
                if steps % 3 == 0: yield open_set_tracker, visited, path, h_name, False
        yield set(), set(), best_path, best_hospital, True