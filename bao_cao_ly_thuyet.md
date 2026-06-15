# BÁO CÁO DỰ ÁN CHI TIẾT: HỆ THỐNG ĐIỀU PHỐI XE CẤP CỨU ĐA TÁC TỬ
## Môn học: Trí tuệ nhân tạo (Artificial Intelligence Course)
## Trường Đại học Sư phạm Kỹ thuật Thành phố Hồ Chí Minh (HCMUTE)

---

# PHẦN 1: MỞ ĐẦU

### 1.1. Giới thiệu đề tài
Đề tài **"Hệ thống Điều phối Xe Cấp cứu Đa Tác tử (Multi-Agent Emergency Dispatch System)"** là một hệ thống giả lập thời gian thực giải quyết bài toán định tuyến xe cứu hộ trong đô thị thông minh. Trong bối cảnh đô thị hóa nhanh chóng, việc tối ưu hóa lộ trình di chuyển của các phương tiện cứu thương đóng vai trò sinh tử. Đề tài tập trung vào việc mô phỏng một trung tâm điều hành thông minh, tự động phân phối xe cấp cứu từ nhiều trạm bệnh viện khác nhau đến các điểm tai nạn bằng cách kết hợp giữa các thuật toán tìm đường heuristic cổ điển và Học tăng cường (Reinforcement Learning).

### 1.2. Lý do chọn đề tài
Trong thực tế, điều kiện giao thông tại các đô thị lớn luôn thay đổi liên tục và khó lường do kẹt xe, tai nạn hoặc công trình xây dựng. Các thuật toán tìm đường truyền thống như A* hay Dijkstra chỉ hoạt động hiệu quả trong môi trường tĩnh. Khi bản đồ thay đổi, chúng phải tính toán lại toàn bộ đồ thị (re-planning), gây tiêu tốn năng lực tính toán và không thể học hỏi từ kinh nghiệm trong quá khứ. 

Để giải quyết vấn đề này, việc kết hợp **Q-Learning** (một thuật toán Học tăng cường) với **A\*** và **LRTA\*** (Learning Real-Time A\*) cho phép hệ thống tận dụng cả hai ưu điểm: khả năng lập kế hoạch có định hướng của heuristic và khả năng thích ứng, tích lũy kinh nghiệm né tránh kẹt xe của học máy. Đây là lý do nhóm lựa chọn đề tài này nhằm hiện thực hóa một giải pháp cứu hộ thông minh, linh hoạt và có tính ứng dụng cao.

### 1.3. Mục tiêu của đề tài
1. **Xây dựng môi trường mô phỏng trực quan**: Phát triển giao diện đồ họa 2D tương tác thời gian thực cho phép tùy biến bản đồ (thêm tường, vẽ vùng kẹt xe, đặt bệnh viện, kích hoạt tai nạn).
2. **Triển khai các thuật toán tìm đường thông minh**:
   - Tích hợp thành công mô hình **A\* kết hợp Q-Learning** (Lập lộ trình tĩnh có phạt kẹt xe).
   - Tích hợp thành công mô hình **LRTA\* kết hợp Q-Learning** (Lập lộ trình động từng bước, tự thích ứng bản đồ).
3. **Phát triển bộ điều phối trung tâm (Smart Dispatch Center)**: Thuật toán tự động tìm kiếm và phân bổ xe từ bệnh viện tối ưu nhất dựa trên ước lượng chi phí thực tế thay vì khoảng cách vật lý thông thường.
4. **Huấn luyện mô hình dùng chung (Shared Brain)**: Thiết lập bảng Q-Table toàn cục để tất cả các tác tử cùng học tập và chia sẻ kinh nghiệm giao thông theo thời gian thực.

### 1.4. Đối tượng sử dụng
- **Các trung tâm quản lý đô thị/cứu hộ y tế**: Sử dụng làm công cụ mô phỏng để đánh giá tính khả thi và kiểm thử các chính sách điều động xe cứu nạn trước khi áp dụng thực tế.
- **Giảng viên và Sinh viên chuyên ngành Công nghệ thông tin/AI**: Làm tài liệu tham khảo trực quan, hỗ trợ giảng dạy các khái niệm tìm kiếm đồ thị, học máy và lập trình game/ứng dụng đồ họa trong Python.

### 1.5. Mô tả đề tài
Dự án được xây dựng dưới dạng ứng dụng máy tính trực quan với lưới ô vuông kích thước tùy chọn (mặc định $20 \times 20$). Mỗi ô lưới đại diện cho một trạng thái môi trường:
- **Đường trống**: Chi phí di chuyển bằng 1.
- **Khu vực kẹt xe**: Chi phí di chuyển tăng lên thành 5.
- **Vị trí tai nạn**: Chi phí di chuyển tăng lên thành 20.
- **Vật cản (Tường)**: Xe cứu thương không thể đi qua.
- **Bệnh viện**: Nơi đỗ của đội xe cứu thương.

Hệ thống cung cấp một bảng điều khiển cho phép chuyển đổi giữa chế độ giờ bình thường và giờ cao điểm (tự động tạo kẹt xe diện rộng), theo dõi trực tiếp các thông số kỹ thuật bên trong của AI (Q-Table, Heuristic Table, danh sách lộ trình), và cho phép bật tính năng "Visualizer" để làm chậm quá trình tìm kiếm, giúp hiển thị chi tiết bước lan truyền sóng thuật toán.

---

# PHẦN 2: CƠ SỞ LÝ THUYẾT VÀ KIẾN TRÚC MÃ NGUỒN

## 2.1. Cơ Sở Lý Thuyết Các Thuật Toán Sử Dụng

### 2.1.1. Thuật toán A* (A-Star Search)
A* là một thuật toán tìm kiếm trên đồ thị nhằm tìm đường đi ngắn nhất từ một nút xuất phát đến một nút đích cho trước. Thuật toán sử dụng một hàm đánh giá để xác định thứ tự ưu tiên khám phá các nút:

$$f(n) = g(n) + h(n)$$

Trong đó:
- $g(n)$: Chi phí thực tế tích lũy từ điểm xuất phát đến nút hiện tại $n$.
- $h(n)$: Hàm Heuristic ước lượng khoảng cách từ nút $n$ đến đích. Ở đây ta dùng khoảng cách Manhattan:
  $$h(n) = |r_n - r_{goal}| + |c_n - c_{goal}|$$

A* luôn mở rộng nút có giá trị $f(n)$ nhỏ nhất từ hàng đợi ưu tiên `open_set`. Trong dự án này, thuật toán chạy hoàn toàn **ngoại tuyến (offline)** để tính toán trước đường đi trước khi xe di chuyển.

### 2.1.2. Thuật toán LRTA* (Learning Real-Time A*)
LRTA* là một thuật toán tìm kiếm trực tuyến thích ứng từng bước, lý tưởng cho môi trường động nơi tác tử không biết trước toàn bộ thông tin bản đồ hoặc bản đồ có thể bị thay đổi giữa chừng.

Quy trình ra quyết định của LRTA* tại mỗi chu kỳ thời gian:
1. Xét tất cả các lân cận $neighbor$ hợp lệ của nút hiện tại $current$.
2. Tính giá trị ước lượng cho mỗi lân cận:
   $$f(neighbor) = cost(current, neighbor) + H(neighbor)$$
   Với $cost(current, neighbor)$ là chi phí vật lý để di chuyển sang ô lân cận, và $H(neighbor)$ là giá trị heuristic hiện tại được lưu trong bảng nhớ `h_table` (khởi tạo bằng khoảng cách Manhattan nếu chưa có).
3. Chọn nút lân cận tốt nhất $best\_next$ có giá trị $f$ nhỏ nhất:
   $$min\_f = \min_{neighbor} \big( cost(current, neighbor) + H(neighbor) \Big)$$
4. Cập nhật lại heuristic của nút hiện tại để phản ánh kinh nghiệm thực tế vừa học:
   $$H(current) = \max \big( H(current), min\_f \big)$$
5. Di chuyển tác tử sang ô $best\_next$.

### 2.1.3. Học tăng cường Q-Learning
Q-Learning là thuật toán học tăng cường dựa trên giá trị (value-based) nhằm tìm kiếm một chính sách hành động tối ưu. Tác tử tự học thông qua việc nhận phần thưởng hoặc hình phạt từ môi trường.
Hệ thống sử dụng phương trình cập nhật Bellman để tinh chỉnh giá trị Q cho cặp trạng thái - hành động $(s, a)$ khi tác tử chuyển từ trạng thái $s$ sang $s'$ dưới hành động $a$ và nhận phần thưởng $R$:

$$Q(s, a) = R + \gamma \max_{a'} Q(s', a')$$

Trong đó:
- $\gamma = 0.9$: Hệ số chiết khấu (Discount Factor) quyết định mức độ ưu tiên của các phần thưởng tương lai.
- Phần thưởng $R$: Được thiết lập bằng giá trị âm của chi phí di chuyển thực tế nhằm phạt các bước đi dài hoặc đi vào khu vực giao thông xấu:
  - Đi vào ô trống thông thường: $R = -1$
  - Đi vào ô kẹt xe: $R = -5$
  - Đi vào ô tai nạn: $R = -20$

### 2.1.4. Cơ chế kết hợp (Fusion: Search + Q-Learning)
Để thuật toán tìm kiếm tĩnh kế thừa kinh nghiệm từ học tăng cường, ta điều chỉnh chi phí thực tế $g(neighbor)$ trong A* bằng cách cộng thêm hình phạt **Q-penalty**:

$$g(neighbor) = g(current) + base\_cost(neighbor) + q\_penalty(current, action\_idx)$$

Với hình phạt được xác định từ các giá trị Q âm trong bảng Q-Table:

$$q\_penalty(current, action\_idx) = \begin{cases} -Q(current, action\_idx) & \text{nếu } Q(current, action\_idx) < 0 \\ 0 & \text{ngược lại} \end{cases}$$

Sự kết hợp này giúp thuật toán tìm kiếm chủ động định tuyến tránh xa các khu vực có giá trị Q cực thấp (do đã từng bị kẹt xe/tai nạn trong quá khứ).

---

## 2.2. Mô Tả Chi Tiết Các Class (Lớp Đối Tượng)

Dự án được thiết kế theo mô hình hướng đối tượng rõ ràng, tách biệt giữa môi trường logic, các tác tử thông minh, và giao diện người dùng đồ họa.

### 2.2.1. Lớp `QLearningModel` (File: [q_learning.py](file:///d:/Study/KY2_NAM2_DOT2/AI/NHOM_10_FINAL_PROJECT/utils/q_learning.py))
- **Mục đích**: Đại diện cho mô hình trí tuệ nhân tạo Q-Learning toàn cục (Shared Brain).
- **Thuộc tính**:
  - `q_table` (dict): Bảng lưu trữ giá trị $Q(s, a)$. Key là tuple tọa độ trạng thái `(r, c)`, value là list 4 phần tử kiểu float đại diện cho Q-value của 4 hành động.
  - `actions` (list): Danh sách các bước di chuyển tương ứng `[(-1, 0), (1, 0), (0, -1), (0, 1)]` (Lên, Xuống, Trái, Phải).
  - `gamma` (float): Hệ số chiết khấu (mặc định 0.9).

### 2.2.2. Lớp `GridMap` (File: [grid_map.py](file:///d:/Study/KY2_NAM2_DOT2/AI/NHOM_10_FINAL_PROJECT/environment/grid_map.py))
- **Mục đích**: Quản lý trạng thái logic của bản đồ dạng lưới đô thị.
- **Thuộc tính**:
  - `grid` (list 2D): Ma trận kích thước $N \times N$ lưu trữ trạng thái của từng ô lưới.
  - `accidents_pool` (list): Danh sách chứa tọa độ các vụ tai nạn đang diễn ra.

### 2.2.3. Lớp `BaseAgent` (File: [base_agent.py](file:///d:/Study/KY2_NAM2_DOT2/AI/NHOM_10_FINAL_PROJECT/agents/base_agent.py))
- **Mục đích**: Lớp cha trừu tượng định nghĩa các hành vi di chuyển và hiển thị cơ bản của xe cấp cứu.
- **Thuộc tính**:
  - `start_pos` / `goal_pos` (tuple): Tọa độ điểm bắt đầu và điểm đích.
  - `current_pos` (tuple): Vị trí hiện tại của tác tử trên bản đồ.
  - `path` (list): Danh sách tọa độ lưu hành trình thực tế tác tử đã đi qua.
  - `color` (tuple): Màu sắc hiển thị riêng của tác tử trên đồ họa.
  - `is_finished` (bool): Đánh dấu tác tử đã hoàn thành nhiệm vụ và trở về trạm gốc hay chưa.

### 2.2.4. Lớp `AStarQAgent` (File: [astar_q_agent.py](file:///d:/Study/KY2_NAM2_DOT2/AI/NHOM_10_FINAL_PROJECT/agents/astar_q_agent.py))
- **Mục đích**: Xe cứu thương sử dụng thuật toán hoạch định đường đi ngoại tuyến A* kết hợp phạt Q-learning. Kế thừa từ `BaseAgent`.
- **Thuộc tính**:
  - `original_hospital_pos` (tuple): Lưu trữ tọa độ trạm bệnh viện gốc để quay về sau khi hoàn tất cứu hộ.
  - `q_brain` (QLearningModel): Tham chiếu tới mô hình Q-Learning dùng chung.
  - `calculated_path` (list): Đường đi tĩnh đã tính toán trước từ thuật toán A*.
  - `path_index` (int): Chỉ số bước hiện tại của tác tử trên đường đi đã tính toán.
  - `is_returning` (bool): Trạng thái xe đang đi cứu nạn (False) hay đang quay về trạm (True).
  - `search_generator` (generator): Bộ sinh trạng thái tìm đường dùng cho việc vẽ trực quan hóa từng bước khám phá.

### 2.2.5. Lớp `LRTALearningAgent` (File: [lrtastar_q_agent.py](file:///d:/Study/KY2_NAM2_DOT2/AI/NHOM_10_FINAL_PROJECT/agents/lrtastar_q_agent.py))
- **Mục đích**: Xe cứu thương sử dụng thuật toán tìm kiếm thích ứng thời gian thực trực tuyến LRTA*. Kế thừa từ `BaseAgent`.
- **Thuộc tính**:
  - `h_table` (dict): Bảng nhớ giá trị heuristic cục bộ của riêng tác tử này.
  - `original_hospital_pos` (tuple): Tọa độ bệnh viện gốc.
  - `is_returning` (bool): Đánh dấu trạng thái đi cứu nạn hoặc quay về trạm.

### 2.2.6. Lớp `DispatchCenter` (File: [dispatch_center.py](file:///d:/Study/KY2_NAM2_DOT2/AI/NHOM_10_FINAL_PROJECT/utils/dispatch_center.py))
- **Mục đích**: Đóng vai trò là trung tâm điều phối tài nguyên và quản lý đội xe của tất cả các bệnh viện.
- **Thuộc tính**:
  - `q_brain` (QLearningModel): Mô hình Q-Learning chung để ước lượng chi phí đường đi.
  - `hospitals` (dict): Cấu hình các trạm bệnh viện (tọa độ và số lượng xe tối đa).
  - `current_cars` (dict): Quản lý số lượng xe cứu hộ rảnh rỗi hiện có tại từng trạm cứu hộ.

### 2.2.7. Các Lớp Giao Diện Người Dùng (UI Components)
- **`Button`** (File: [button.py](file:///d:/Study/KY2_NAM2_DOT2/AI/NHOM_10_FINAL_PROJECT/ui/button.py)): Định nghĩa các nút bấm đồ họa có khả năng bắt tương tác nhấp chuột và đổi màu sắc động (Hover/Active).
- **`LoggerPanel`** (File: [logger_panel.py](file:///d:/Study/KY2_NAM2_DOT2/AI/NHOM_10_FINAL_PROJECT/ui/logger_panel.py)): Khung nhật ký hoạt động dưới chân màn hình, tự động tô màu chữ dựa theo nhãn nội dung (`[ALERT]`, `[SYSTEM]`, `[DISPATCH]`, `[STATION]`).
- **`InspectorPanel`** (File: [inspector_panel.py](file:///d:/Study/KY2_NAM2_DOT2/AI/NHOM_10_FINAL_PROJECT/ui/inspector_panel.py)): Bảng giám sát chỉ số AI thời gian thực ở mép phải màn hình, hỗ trợ thanh cuộn và hiển thị chi tiết các bảng dữ liệu nội bộ.
- **`UIManager`** (File: [ui_manager.py](file:///d:/Study/KY2_NAM2_DOT2/AI/NHOM_10_FINAL_PROJECT/ui/ui_manager.py)): Bộ quản lý vị trí, trạng thái kích hoạt và vẽ toàn bộ các nút điều khiển.
- **`SimulationApp`** (File: [simulation_app.py](file:///d:/Study/KY2_NAM2_DOT2/AI/NHOM_10_FINAL_PROJECT/ui/simulation_app.py)): Trái tim của ứng dụng đồ họa, quản lý vòng lặp chính của Pygame, tiếp nhận sự kiện chuột/bàn phím và liên kết hoạt động của tất cả các lớp phía trên.

---

## 2.3. Mô Tả Chi Tiết Các Function (Hàm Chức Năng Cốt Lõi)

Dưới đây là mô tả chi tiết các hàm chức năng xử lý nghiệp vụ AI và thuật toán trong hệ thống:

### 2.3.1. Các hàm trong Lớp `QLearningModel`
- **`get_q_values(self, state)`**:
  - Input: `state` (tuple) - tọa độ của một ô lưới.
  - Output: `list` - mảng 4 giá trị Q tương ứng 4 hướng.
  - Chức năng: Trả về danh sách Q-values. Nếu trạng thái này chưa từng được khám phá, hàm tự động khởi tạo giá trị mặc định là `[0.0, 0.0, 0.0, 0.0]`.
- **`update_q_value(self, state, action_idx, reward, next_state)`**:
  - Input: `state` (tọa độ cũ), `action_idx` (chỉ số hành động), `reward` (phần thưởng nhận được), `next_state` (tọa độ mới).
  - Chức năng: Áp dụng công thức Bellman để tính toán và cập nhật giá trị Q mới cho hành động tại trạng thái cũ.
- **`save_brain(self, filepath)` / `load_brain(self, filepath)`**:
  - Chức năng: Đọc/ghi cấu trúc bảng Q-Table dưới dạng JSON từ/xuống tệp lưu trữ trên ổ cứng để bảo toàn kết quả huấn luyện.

### 2.3.2. Các hàm trong Lớp `GridMap`
- **`generate_default_map(self)`**:
  - Chức năng: Tạo cấu trúc các khối tường nhà cố định và định vị các trạm bệnh viện lên bản đồ lưới ban đầu.
- **`set_traffic_jam(self, hour)`**:
  - Input: `hour` (int) - giờ giả lập hệ thống.
  - Chức năng: Nếu là giờ cao điểm ($17 \le hour \le 18$), tự động vẽ 2 làn đường kẹt xe nằm ngang trên dòng thứ 8 và dòng thứ 12 của lưới.
- **`get_cost(self, pos)`**:
  - Input: `pos` (tuple) - tọa độ ô lưới cần kiểm tra.
  - Output: `int` - chi phí di chuyển.
  - Chức năng: Trả về chi phí động của ô (Đường trống = 1, Kẹt xe = 5, Vùng tai nạn = 20).

### 2.3.3. Các hàm trong Lớp `AStarQAgent`
- **`heuristic(self, pos)`**:
  - Chức năng: Tính khoảng cách Manhattan hỗ trợ ước lượng chi phí tìm đường.
- **`search_path_with_q(self, grid_map)`**:
  - Input: `grid_map` (GridMap) - đối tượng bản đồ lưới.
  - Output: `list` - danh sách tọa độ tạo thành lộ trình đi ngắn nhất từ xuất phát đến đích.
  - Chức năng: Thực thi thuật toán tìm kiếm A* có tích hợp giá trị phạt Q-value âm từ bảng Q-Table dùng chung làm trọng số phụ để né các khu vực kẹt xe tĩnh/động.
- **`search_path_generator(self, grid_map)`**:
  - Chức năng: Tương tự như hàm tìm đường trên nhưng viết dưới dạng generator (sử dụng từ khóa `yield`) giúp giao diện vẽ chậm lại quá trình duyệt nút phục vụ mục đích trực quan hóa hoạt động của thuật toán.
- **`update_astar_return_logic(self, grid_map, app_instance)`**:
  - Chức năng: Cập nhật di chuyển từng bước của xe A* theo lộ trình. Khi xe đến điểm tai nạn, hàm tự động dọn dẹp tai nạn trên bản đồ, chuyển hướng điểm đích về bệnh viện gốc, tính toán một lộ trình quay lại mới và cập nhật trạng thái hoạt động của xe.

### 2.3.4. Các hàm trong Lớp `LRTALearningAgent`
- **`get_h(self, pos)`**:
  - Chức năng: Lấy giá trị heuristic hiện tại của ô từ bảng nhớ `h_table`. Khởi tạo bằng khoảng cách Manhattan nếu ô đó chưa từng được duyệt.
- **`update_route_realtime_with_return(self, grid_map, app_instance)`**:
  - Chức năng: Triển khai toàn bộ quy trình 5 bước của thuật toán LRTA* để tìm bước đi tối ưu tiếp theo thời gian thực và di chuyển tác tử. Đồng thời xử lý chuyển đổi đích đến về lại bệnh viện gốc khi cứu hộ xong.

### 2.3.5. Các hàm trong Lớp `DispatchCenter`
- **`reset_resources(self)`**:
  - Chức năng: Cài đặt lại trạng thái số lượng xe cứu thương hiện có tại mỗi bệnh viện về mức ban đầu.
- **`evaluate_and_dispatch(self, acc_pos, grid_map)`**:
  - Input: `acc_pos` (tọa độ tai nạn), `grid_map` (GridMap).
  - Output: `tuple` - (Tên bệnh viện tốt nhất, Lộ trình tìm được).
  - Chức năng: Duyệt qua toàn bộ các bệnh viện còn xe cứu thương rảnh, thực hiện chạy thử thuật toán tìm đường để tính toán tổng chi phí thực tế nhỏ nhất (có cộng phạt Q-penalty) từ bệnh viện đó đến điểm tai nạn. Từ đó lựa chọn bệnh viện tối ưu nhất để xuất xe.
- **`evaluate_generator(self, acc_pos, grid_map)`**:
  - Chức năng: Generator mô phỏng quá trình quét thầu đa bệnh viện trên giao diện (Visualizer thầu).

### 2.3.6. Các hàm trong Lớp `SimulationApp`
- **`run(self)`**:
  - Chức năng: Vòng lặp ứng dụng, đồng bộ tần số quét màn hình (FPS = 30), điều khiển cập nhật tác tử và vẽ khung hình.
- **`manage_queue(self)`**:
  - Chức năng: Tự động chạy ngầm để quét hàng chờ tai nạn (`pending_accidents`) và gọi trung tâm điều phối cử xe ngay khi phát hiện có xe cứu thương vừa quay về trạm rảnh rỗi.
- **`update_simulation(self)`**:
  - Chức năng: Di chuyển các xe hoạt động trên lưới đồng thời tính toán phần thưởng thực tế và huấn luyện bảng Q-Table toàn cục dựa trên hành trình di chuyển thực tế của các xe cứu thương.

---

## 2.4. Mô Tả Các Thư Viện Sử Dụng

Dự án sử dụng các thư viện Python chuẩn và thư viện đồ họa mở rộng sau:

1. **`pygame`**:
   - *Mục đích*: Thư viện cốt lõi dùng để xây dựng giao diện đồ họa (GUI). Nó cung cấp các công cụ vẽ lưới ô vuông, tác tử, đường nối lộ trình, xử lý phông chữ hiển thị, điều khiển vòng lặp chính của ứng dụng và bắt các sự kiện tương tác chuột/bàn phím từ người dùng.
2. **`heapq`**:
   - *Mục đích*: Thư viện chuẩn hỗ trợ cấu trúc dữ liệu hàng đợi ưu tiên (Priority Queue) dưới dạng Min-Heap. Thư viện này cực kỳ quan trọng giúp tối ưu hóa thuật toán A* và bộ tính toán chi phí cứu hộ của Dispatch Center khi liên tục phải lấy ra nút có chi phí $f(n)$ nhỏ nhất với độ phức tạp thời gian chỉ là $O(\log n)$.
3. **`json`**:
   - *Mục đích*: Thư viện xử lý dữ liệu định dạng JSON. Được sử dụng để chuyển đổi bảng Q-Table (dữ liệu học tập của AI) và bố cục bản đồ tùy biến của người dùng thành chuỗi ký tự để ghi xuống đĩa cứng, giúp lưu trữ và khôi phục mô hình làm việc tiện lợi.
4. **`os`**:
   - *Mục đích*: Thư viện tương tác với hệ thống tập tin của hệ điều hành, được dùng để kiểm tra sự tồn tại của tệp tin lưu trữ (`custom_map_layout.json`, `q_brain_memory.json`) trước khi thực hiện các thao tác tải dữ liệu lên nhằm tránh gây lỗi dừng chương trình đột ngột.
5. **`random`**:
   - *Mục đích*: Thư viện sinh số ngẫu nhiên, hỗ trợ một số thiết lập bố cục tường và vật cản ngẫu nhiên khi người dùng lựa chọn chế độ tạo bản đồ ngẫu nhiên từ menu chính.
