# utils/dispatch_center.py
import config
from agents.astar_q_agent import AStarQAgent


class DispatchCenter:
    def __init__(self, q_model):
        self.hospitals = config.HOSPITAL_CONFIG
        self.q_brain = q_model
        self.current_cars = {}

    def reset_resources(self):
        self.current_cars = {k: v["max_cars"] for k, v in self.hospitals.items()}

    def find_top_3_hospitals(self, accident_pos):
        hospital_distances = []
        for name, info in self.hospitals.items():
            h_pos = info["pos"]
            dist = abs(h_pos[0] - accident_pos[0]) + abs(h_pos[1] - accident_pos[1])
            hospital_distances.append((name, dist))
        hospital_distances.sort(key=lambda x: x[1])
        return [item[0] for item in hospital_distances[:3]]

    def evaluate_and_dispatch(self, accident_pos, grid_map):
        top_3 = self.find_top_3_hospitals(accident_pos)
        state_features = tuple(self.current_cars.get(h_name, 0) > 0 for h_name in top_3)

        candidate_routes = {}
        for h_name in top_3:
            if self.current_cars.get(h_name, 0) > 0:
                h_pos = self.hospitals[h_name]["pos"]
                virtual_agent = AStarQAgent(h_pos, accident_pos)
                path = virtual_agent.search_path_with_q(grid_map)
                path_cost = sum(grid_map.get_cost(node) for node in path)
                candidate_routes[h_name] = (path, path_cost)

        if not candidate_routes:
            print("[CẢNH BÁO] Tất cả các bệnh viện lân cận đều đã HẾT XE cứu hộ!")
            return None, []

        chosen_hospital = min(candidate_routes.keys(), key=lambda h: candidate_routes[h][1])
        self.current_cars[chosen_hospital] -= 1

        print(
            f"-> TỔNG ĐÀI CHỐT: Điều xe từ trạm {chosen_hospital} (Còn rảnh: {self.current_cars[chosen_hospital]} xe)")
        return chosen_hospital, candidate_routes[chosen_hospital][0]