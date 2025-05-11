# ĐỒ ÁN CÁ NHÂN: GAME 8-PUZZLE VỚI 6 NHÓM THUẬT TOÁN CHÍNH

# Mục tiêu và Thành phần chính của bài toán  
- Mục tiêu: Giải bài toán 8 ô chữ từ trạng thái ban đầu [[7,2,4],[5,0,6],[8,3,1]] đến trạng thái đích [[1,2,3],[4,5,6],[7,8,0]] bằng nhiều thuật toán tìm kiếm khác nhau.  
- Thành phần chính: Bảng 3x3, các ô số từ 0-8, các thuật toán tìm kiếm (không thông tin, có thông tin, cục bộ, môi trường phức tạp, CSPs, học tăng cường), giao diện Pygame với hoạt hình và thanh trượt.

# Nội dung

2.1 Tìm kiếm không có thông tin  
Đặc điểm, cách chạy và tính phù hợp:  
- BFS: Tìm đường bằng cách thử hết các khả năng di chuyển ô trống (lên, xuống, trái, phải) theo từng lớp, đảm bảo tìm đường ngắn nhất. Phù hợp với 8-puzzle nếu cần đường ngắn nhưng tốn nhiều bộ nhớ khi bảng phức tạp.  
- DFS: Đi sâu hết một hướng di chuyển ô trống trước rồi quay lại thử hướng khác nếu không được. Không hợp lắm vì dễ đi đường dài, không đảm bảo đường ngắn nhất.  
- UCS: Tìm đường ngắn nhất bằng cách ưu tiên hướng di chuyển ô trống ít bước nhất, giống BFS nhưng tính thêm chi phí. Phù hợp để tìm đường tối ưu nhưng tốn tài nguyên hơn BFS.  
- IDS: Kết hợp BFS và DFS, thử đi sâu từng mức một, tăng dần độ sâu cho đến khi tìm đích. Phù hợp để tiết kiệm bộ nhớ hơn BFS, nhưng chậm hơn.  

Bảng so sánh:

| Thuật Toán | Thời Gian (s) | Số Bước | Nút Duyệt | Độ Sâu |
|------------|---------------|---------|-----------|--------|
| BFS        | 1,262         | 20      | 82,364    | 20     |
| DFS        | 0,466         | 46      | 64,324    | 46     |
| UCS        | 1,588         | 20      | 106,577   | 20     |
| IDS        | 2,613         | 26      | 217,423   | 26     |

Nhận xét: BFS và UCS tìm được đường ngắn nhất với 20 bước, rất phù hợp cho 8-puzzle khi cần đường tối ưu, nhưng cả hai đều tốn nhiều tài nguyên, đặc biệt UCS duyệt tới 106,577 nút và chậm hơn BFS (1,588s so với 1,262s). DFS nhanh nhất (0,466s) và duyệt ít nút hơn (64,324), nhưng đường đi lại dài gấp đôi (46 bước), không hiệu quả khi cần đường ngắn nhất. IDS cân bằng hơn với 26 bước, nhưng tốn thời gian (2,613s) và duyệt quá nhiều nút (217,423), nên không phải lựa chọn tốt nếu cần tốc độ nhanh hoặc ít tài nguyên. Nhóm này cho thấy BFS và UCS đáng tin cậy hơn cho 8-puzzle, nhưng cần cải thiện về tài nguyên và thời gian nếu bảng phức tạp hơn.  


2.2 Tìm kiếm có thông tin  
Đặc điểm, cách chạy và tính phù hợp:  
- Greedy Best-First Search: Chọn hướng di chuyển ô trống sao cho bảng gần đích nhất, dựa vào khoảng cách từ các ô đến vị trí đúng (khoảng cách Manhattan). Ít phù hợp vì dễ đi đường vòng, không đảm bảo đường ngắn nhất.  
- A*: Kết hợp số bước đã đi và khoảng cách Manhattan, chọn hướng di chuyển ô trống tốt nhất để vừa ngắn vừa gần đích. Rất phù hợp với 8-puzzle vì tìm được đường ngắn nhất và hiệu quả cao.  
- IDA*: Giống A* nhưng thử đi sâu từng mức, giới hạn chi phí để tiết kiệm bộ nhớ, sau đó tăng giới hạn nếu không tìm được đích. Phù hợp vì ít tốn bộ nhớ, nhưng chậm hơn A*.  

Bảng so sánh:

| Thuật Toán | Thời Gian (s) | Số Bước | Nút Duyệt | Độ Sâu |
|------------|---------------|---------|-----------|--------|
| Greedy     | 0,011         | 62      | 566       | 62     |
| A*         | 0,006         | 20      | 289       | 20     |
| IDA*       | 0,044         | 20      | 7,399     | 20     |

Nhận xét: A* là lựa chọn tốt nhất cho 8-puzzle, tìm đường ngắn nhất chỉ 20 bước, nhanh nhất (0,006s) và duyệt ít nút nhất (289), phù hợp khi cần hiệu quả cao và tối ưu. Greedy tuy nhanh (0,011s) và duyệt không nhiều (566 nút), nhưng đi đường vòng tới 62 bước, không hiệu quả khi cần đường ngắn nhất. IDA* cũng tìm được đường 20 bước như A*, nhưng tốn nhiều nút hơn (7,399) và chậm hơn (0,044s), dù ưu điểm là tiết kiệm bộ nhớ. Nhóm này cho thấy A* vượt trội nhất về mọi mặt, rất đáng dùng cho 8-puzzle, trong khi Greedy cần cải thiện để tránh đường vòng và IDA* cần tối ưu tốc độ.  


2.3 Tìm kiếm cục bộ  
Đặc điểm, cách chạy và tính phù hợp:  
- Simple Hill Climbing: Chọn hướng di chuyển ô trống làm bảng gần đích hơn (dựa vào khoảng cách Manhattan), nhưng dễ bị kẹt nếu không tìm được đích. Ít phù hợp vì map chính không giải được, phải dùng map dễ hơn.  
- Steepest Ascent Hill Climbing: Tương tự Simple nhưng thử hết hướng, chọn hướng tốt nhất làm bảng gần đích nhất. Cũng ít phù hợp vì dễ kẹt, cần map dễ hơn để hoạt động tốt.  
- Stochastic Hill Climbing: Chọn ngẫu nhiên hướng làm bảng gần đích, tránh kẹt tốt hơn Simple/Steepest. Hợp hơn một chút nhưng vẫn cần map dễ để hiệu quả.  
- Beam Search: Giữ 5 trạng thái bảng tốt nhất, thử di chuyển ô trống từ đó, chọn hướng tốt nhất. Phù hợp vì hiệu quả trên map chính, ít tốn tài nguyên.  
- Simulated Annealing: Chấp nhận hướng di chuyển không tốt với xác suất giảm dần, tránh kẹt cục bộ. Phù hợp hơn Hill Climbing nhưng vẫn cần map dễ để hiệu quả.  

Bảng so sánh:

| Thuật Toán        | Map         | Thời Gian (s) | Số Bước | Nút Duyệt | Độ Sâu |
|-------------------|-------------|---------------|---------|-----------|--------|
| Simple Hill       | Dễ hơn      | 0             | 2       | 3         | 2      |
| Steepest Ascent   | Dễ hơn      | 0             | 2       | 3         | 2      |
| Stochastic Hill   | Dễ hơn      | 0             | 2       | 3         | 2      |
| Beam Search       | Chính       | 0,002         | 20      | 99        | 20     |
| Simulated Annealing | Dễ hơn    | 1,095         | 2       | 3         | 2      |

Nhận xét: Map chính không giải được nên Simple, Steepest, Stochastic và Simulated phải chuyển sang map dễ hơn, lúc này cả 4 thuật toán đều hiệu quả, chỉ cần 2 bước và 3 nút, rất nhanh (0s), trừ Simulated Annealing chậm hơn (1,095s) do cơ chế xác suất. Beam Search nổi bật khi hoạt động tốt trên map chính, tìm đường 20 bước, nhanh (0,002s) và chỉ duyệt 99 nút, rất phù hợp với 8-puzzle khi map giải được. Nhóm này cho thấy Beam Search đáng tin cậy nhất trên map chính, nhưng các thuật toán Hill Climbing và Simulated cần map khả thi để phát huy hiệu quả, nếu không dễ bị kẹt hoặc tốn thời gian không cần thiết.  


2.4 Tìm kiếm trong môi trường phức tạp  
Đặc điểm, cách chạy và tính phù hợp:  
- And-Or Graph Search: Xử lý trường hợp không chắc chắn, chọn hướng di chuyển ô trống dựa trên các nhánh logic, thử nhiều khả năng cùng lúc. Không phù hợp vì map chính không giải được, không tìm ra đường đi.  
- Belief State Search: Làm việc với nhiều trạng thái bảng có thể xảy ra (belief), di chuyển ô trống đồng thời trên các trạng thái, dựa vào khoảng cách trung bình đến đích. Không hợp vì map không giải được, các trạng thái belief không dẫn đến đích.  
- Partial Observation Search: Lọc trạng thái belief bằng cách nhìn giá trị ở vài ô cố định, chọn hướng di chuyển ô trống dựa trên khoảng cách trung bình. Không hợp vì map không giải được, nhìn vài ô không đủ để tìm đường.  

Nhận xét: Cả ba thuật toán đều không hiệu quả với 8-puzzle trong trường hợp này vì map chính không giải được, dẫn đến không tìm được đường đi. And-Or không có lời giải do không xử lý được trạng thái không khả thi. Belief State Search và Partial Observation Search cần map có thể giải và tập trạng thái belief hợp lý, nếu không sẽ thất bại. Nhóm này chỉ hợp với 8-puzzle khi map giải được và có thêm yếu tố không chắc chắn (như không biết hết trạng thái bảng), nhưng với map cố định như hiện tại thì không phát huy được hiệu quả, cần cải thiện map hoặc cách thiết lập bài toán.  

2.5 CSPs  
Đặc điểm, cách chạy và tính phù hợp:  
- Backtracking Search: Thử từng hướng di chuyển ô trống, nếu không hợp thì quay lại thử hướng khác, kiểm tra bảng có hợp lệ không. Ít phù hợp vì map không giải được, dẫn đến tìm đường dài và tốn tài nguyên.  
- Forward Checking: Tương tự Backtracking nhưng kiểm tra trước các ràng buộc sau mỗi bước di chuyển ô trống để giảm khả năng sai. Cũng ít phù hợp vì map không giải được, hiệu quả không khác Backtracking.  

Bảng so sánh:

| Thuật Toán        | Thời Gian (s) | Số Bước | Nút Duyệt | Độ Sâu |
|-------------------|---------------|---------|-----------|--------|
| Backtracking      | 0,607         | 50      | 94,681    | 50     |
| Forward Checking  | 0,614         | 50      | 94,681    | 50     |

Nhận xét: Cả hai thuật toán đều không hiệu quả với 8-puzzle trong trường hợp này, tìm đường dài (50 bước) và tốn rất nhiều tài nguyên (94,681 nút), do map chính không giải được. Backtracking và Forward Checking có hiệu suất gần giống nhau (0,607s và 0,614s), nhưng Forward Checking không cải thiện đáng kể vì map không khả thi, không tận dụng được lợi thế kiểm tra trước. Nhóm này chỉ phù hợp với 8-puzzle khi map giải được và cần kiểm tra ràng buộc chặt chẽ, nhưng với map hiện tại thì không phát huy hiệu quả, nên cân nhắc dùng các thuật toán khác như A* hoặc Beam Search để thay thế.  


2.6 Học tăng cường  
Đặc điểm, cách chạy và tính phù hợp:  
- Q-Learning: Học cách di chuyển ô trống qua thử sai, dựa vào phần thưởng (khoảng cách đến đích và khi đạt đích), sau nhiều lần thử sẽ chọn hướng tốt nhất. Phù hợp với 8-puzzle vì có thể tìm đường tối ưu, nhưng cần thời gian học lâu.  

Bảng so sánh:

| Thuật Toán | Thời Gian (s) | Số Bước | Nút Duyệt | Độ Sâu |
|------------|---------------|---------|-----------|--------|
| Q-Learning | 4,181         | 20      | 152,551   | 20     |

Nhận xét: Q-Learning tìm được đường tối ưu (20 bước), rất phù hợp với 8-puzzle khi cần đường ngắn nhất mà không biết trước cách giải, nhưng nhược điểm lớn là quá chậm (4,181s) và tốn nhiều tài nguyên (152,551 nút) do phải thử sai qua nhiều lần. So với các thuật toán khác như A* (0,006s, 289 nút), Q-Learning không hiệu quả về tốc độ và tài nguyên, nhưng lợi thế là có thể học và cải thiện nếu áp dụng lâu dài hoặc với các map thay đổi. Nếu cần giải nhanh 8-puzzle, nên dùng A* hoặc Beam Search, nhưng nếu cần thuật toán học hỏi và linh hoạt, Q-Learning là lựa chọn tốt, chỉ cần tối ưu thời gian học.  

# Kết luận:
Dựa trên hiệu suất và tính phù hợp, nên dùng A* hoặc Beam Search để giải 8-puzzle. A* là lựa chọn tốt nhất khi cần đường ngắn nhất, nhanh (0,006s), ít tốn tài nguyên (289 nút), và luôn đảm bảo tối ưu (20 bước), rất phù hợp với bài toán cố định như 8-puzzle. Beam Search cũng là một lựa chọn tốt, đặc biệt trên map chính, với 20 bước, nhanh (0,002s) và chỉ 99 nút, phù hợp khi cần hiệu quả mà không tốn quá nhiều tài nguyên. Các thuật toán khác như BFS, UCS hay Q-Learning tuy tìm được đường tối ưu nhưng tốn tài nguyên và thời gian, không hiệu quả bằng. 
Nhóm Hill Climbing, Simulated Annealing không giải được, còn Belief State, Partial Observation và CSPs không hợp với map cố định không giải được, nên tránh dùng trong trường hợp này.
