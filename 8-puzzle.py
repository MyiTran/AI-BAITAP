import pygame, sys, heapq, time, random
from collections import deque
import itertools
import tkinter as tk
from tkinter import messagebox, Toplevel, ttk, Label, Entry, Button
import math

# Tăng giới hạn đệ quy cho IDA*
sys.setrecursionlimit(10000)

# Khởi tạo tkinter
tk_root = tk.Tk()
tk_root.withdraw()

# Cài đặt Pygame
pygame.init()
WIDTH, HEIGHT = 1000, 700  # Tăng chiều cao để chứa thanh trượt
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("8-Puzzle Solver")
clock = pygame.time.Clock()

# Biến toàn cục
start_state = None
goal_state = None
animating = False
full_solution_moves = []
last_move_time = 0
move_interval = 100  # Thời gian chờ giữa các bước (ms)
elapsed_time_str = "00:00:00"
step_count = 0
nodes_explored = 0
solution_path = []
algorithm_running = False
start_time = 0
end_time = 0
elapsed_time = 0
current_state = None
current_step = 0
solution_completed = False
belief_states = None
observable_cells = []  # Khởi tạo rỗng, người dùng phải chọn
comparison_data = []
current_algorithm = None
is_dialog_open = False
selected_group = None
algorithm_buttons = []
interrupt_animation = False  # Biến để ngắt hoạt hình khi restart
dragging_slider = False  # Biến kiểm soát kéo thanh trượt

# Màu sắc
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FRAME_BG = (255, 240, 245)
FRAME_BORDER = (219, 112, 147)
TILE_COLORS = {
    1: (255, 192, 203), 2: (255, 182, 193), 3: (255, 105, 180),
    4: (255, 20, 147), 5: (219, 112, 147), 6: (199, 21, 133),
    7: (255, 0, 127), 8: (255, 105, 180), 0: WHITE
}
BUTTON_COLORS = {
    'normal': (255, 228, 225), 'hover': (255, 192, 203), 'border': (219, 112, 147)
}
HIGHLIGHT_COLOR = (255, 255, 0)
SLIDER_TRACK_COLOR = (200, 200, 200)
SLIDER_THUMB_COLOR = (100, 100, 100)

# Font chữ
PUZZLE_FONT = pygame.font.SysFont("Arial", 36)
SMALL_FONT = pygame.font.SysFont("Arial", 14)
INFO_FONT = pygame.font.SysFont("Arial", 20)
GROUP_FONT = pygame.font.SysFont("Arial", 18, bold=True)

# Kích thước và vị trí
BOARD_X, BOARD_Y = 20, 20
TILE_SIZE = 60
BOARD_WIDTH = TILE_SIZE * 3
BOARD_HEIGHT = TILE_SIZE * 3
GROUP_START_X = BOARD_X + BOARD_WIDTH + 20
GROUP_START_Y = BOARD_Y
GROUP_WIDTH = 200
GROUP_HEIGHT = 50
GROUP_MARGIN = 10
BUTTON_WIDTH = 180
BUTTON_HEIGHT = 25
BUTTON_MARGIN = 5
INFO_X = GROUP_START_X
INFO_Y = GROUP_START_Y + 3 * (GROUP_HEIGHT + GROUP_MARGIN)
INFO_WIDTH = 600
INFO_HEIGHT = 200
SLIDER_X = GROUP_START_X
SLIDER_Y = INFO_Y + INFO_HEIGHT + 90
SLIDER_WIDTH = 300
SLIDER_HEIGHT = 20
SLIDER_THUMB_SIZE = 10

# Lớp Puzzle để quản lý trạng thái bảng
class Puzzle:
    def __init__(self, board, parent=None, move=""):
        self.board = board  # Bảng 3x3
        self.parent = parent  # Trạng thái trước đó
        self.move = move  # Bước di chuyển dẫn đến trạng thái này

    def __eq__(self, other):
        return self.board == other.board

    def __hash__(self):
        return hash(tuple(map(tuple, self.board)))

    # Tìm vị trí ô 0 (ô trống)
    def find_zero(self):
        for i in range(len(self.board)):
            for j in range(len(self.board[i])):
                if self.board[i][j] == 0:
                    return i, j

    # Tạo danh sách các bước di chuyển hợp lệ
    def generate_moves(self):
        i, j = self.find_zero()
        moves = []
        if i > 0: moves.append("UP")
        if i < 2: moves.append("DOWN")
        if j > 0: moves.append("LEFT")
        if j < 2: moves.append("RIGHT")
        return moves

    # Áp dụng một bước di chuyển
    def apply_move(self, move):
        i, j = self.find_zero()
        new_board = [row[:] for row in self.board]
        if move == "UP" and i > 0:
            new_board[i][j], new_board[i - 1][j] = new_board[i - 1][j], new_board[i][j]
        elif move == "DOWN" and i < 2:
            new_board[i][j], new_board[i + 1][j] = new_board[i + 1][j], new_board[i][j]
        elif move == "LEFT" and j > 0:
            new_board[i][j], new_board[i][j - 1] = new_board[i][j - 1], new_board[i][j]
        elif move == "RIGHT" and j < 2:
            new_board[i][j], new_board[i][j + 1] = new_board[i][j + 1], new_board[i][j]
        else:
            return self
        return Puzzle(new_board, self, move)

# Lấy danh sách các bước di chuyển từ trạng thái hiện tại về gốc
def get_solution(state):
    moves = []
    while state and state.parent is not None:
        moves.append(state.move)
        state = state.parent
    return moves[::-1]

# Lấy toàn bộ đường đi (bước di chuyển và trạng thái)
def get_full_path(state):
    path = []
    while state is not None:
        path.append((state.move, state.board))
        state = state.parent
    return path[::-1]

# Hàm heuristic tính khoảng cách Manhattan
def heuristic(board):
    goal_positions = {
        1: (0, 0), 2: (0, 1), 3: (0, 2),
        4: (1, 0), 5: (1, 1), 6: (1, 2),
        7: (2, 0), 8: (2, 1), 0: (2, 2)
    }
    d = 0
    for i in range(3):
        for j in range(3):
            v = board[i][j]
            if v != 0:
                gx, gy = goal_positions[v]
                d += abs(i - gx) + abs(j - gy)
    return d

# Kiểm tra bảng có thể giải được không
def is_solvable(board):
    flat_board = [num for row in board for num in row if num != 0]
    inversions = sum(1 for i in range(len(flat_board)) for j in range(i+1, len(flat_board)) if flat_board[i] > flat_board[j])
    return inversions % 2 == 0

# Vẽ bảng puzzle
def draw_board(board, x, y, tile_size, highlight_cells=None):
    if highlight_cells is None:
        highlight_cells = observable_cells
    for i in range(3):
        for j in range(3):
            rect_x = x + j * tile_size
            rect_y = y + i * tile_size
            pygame.draw.rect(screen, TILE_COLORS[board[i][j]], (rect_x, rect_y, tile_size, tile_size))
            if (i,j) in highlight_cells and current_algorithm == "Partial Observation Search":
                pygame.draw.rect(screen, HIGHLIGHT_COLOR, (rect_x, rect_y, tile_size, tile_size), 4)
            pygame.draw.rect(screen, BLACK, (rect_x, rect_y, tile_size, tile_size), 2)
            if board[i][j] != 0:
                text = PUZZLE_FONT.render(str(board[i][j]), True, BLACK)
                text_rect = text.get_rect(center=(rect_x + tile_size//2, rect_y + tile_size//2))
                screen.blit(text, text_rect)

# Vẽ bảng từ đối tượng Puzzle
def draw_board_with_board(puzzle, x, y, tile_size, highlight_cells=None):
    draw_board(puzzle.board, x, y, tile_size, highlight_cells)

# Vẽ các nút điều khiển
def draw_buttons(buttons):
    mouse_pos = pygame.mouse.get_pos()
    for label, rect in buttons:
        color = BUTTON_COLORS['hover'] if rect.collidepoint(mouse_pos) else BUTTON_COLORS['normal']
        pygame.draw.rect(screen, color, rect, border_radius=5)
        pygame.draw.rect(screen, BUTTON_COLORS['border'], rect, 2, border_radius=5)
        if len(label) > 20:
            label = label[:17] + "..."
        text = SMALL_FONT.render(label, True, BLACK)
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

# Vẽ nhóm thuật toán
def draw_group(title, x, y):
    pygame.draw.rect(screen, FRAME_BG, (x, y, GROUP_WIDTH, GROUP_HEIGHT))
    pygame.draw.rect(screen, FRAME_BORDER, (x, y, GROUP_WIDTH, GROUP_HEIGHT), 2)
    title_text = GROUP_FONT.render(title, True, BLACK)
    screen.blit(title_text, (x + 10, y + GROUP_HEIGHT//2 - 10))

# Vẽ khung thông tin giải pháp
def draw_info(x, y, time_str, steps, nodes, depth, belief_states=None):
    pygame.draw.rect(screen, FRAME_BG, (x, y, INFO_WIDTH, INFO_HEIGHT))
    pygame.draw.rect(screen, FRAME_BORDER, (x, y, INFO_WIDTH, INFO_HEIGHT), 2)
    title_text = GROUP_FONT.render("Thông Tin Giải Pháp", True, BLACK)
    screen.blit(title_text, (x + 10, y + 10))
    y_offset = y + 40
    screen.blit(INFO_FONT.render(f"Thời Gian: {time_str}", True, BLACK), (x + 10, y_offset))
    screen.blit(INFO_FONT.render(f"Số Bước: {steps}", True, BLACK), (x + 10, y_offset + 25))
    screen.blit(INFO_FONT.render(f"Nút Đã Duyệt: {nodes}", True, BLACK), (x + 10, y_offset + 50))
    screen.blit(INFO_FONT.render(f"Độ Sâu: {depth}", True, BLACK), (x + 10, y_offset + 75))
    if belief_states:
        text = SMALL_FONT.render(f"Tập Belief: {len(belief_states)}", True, BLACK)
        screen.blit(text, (x + 10, y_offset + 100))
    if current_algorithm == "Partial Observation Search":
        text = SMALL_FONT.render(f"Ô Quan Sát: {observable_cells}", True, BLACK)
        screen.blit(text, (x + 10, y_offset + 125))

# Vẽ thanh trượt bước
def draw_step_slider(x, y, width, height, current_step, total_steps):
    if total_steps <= 0:
        return
    # Vẽ thanh nền
    pygame.draw.rect(screen, SLIDER_TRACK_COLOR, (x, y, width, height))
    # Tính vị trí nút kéo
    thumb_x = x + (current_step / total_steps) * (width - SLIDER_THUMB_SIZE)
    thumb_y = y + (height - SLIDER_THUMB_SIZE) / 2
    pygame.draw.rect(screen, SLIDER_THUMB_COLOR, (thumb_x, thumb_y, SLIDER_THUMB_SIZE, SLIDER_THUMB_SIZE))
    # Vẽ nhãn bước
    step_text = SMALL_FONT.render(f"Bước: {current_step}/{total_steps}", True, BLACK)
    screen.blit(step_text, (x, y - 20))

# Tạo hoạt hình khi di chuyển ô
def animate_move(puzzle, move, x, y):
    i, j = puzzle.find_zero()
    dx, dy = 0, 0
    if move == "UP":
        dx, dy = 0, -TILE_SIZE
        tile_value = puzzle.board[i-1][j]
    elif move == "DOWN":
        dx, dy = 0, TILE_SIZE
        tile_value = puzzle.board[i+1][j]
    elif move == "LEFT":
        dx, dy = -TILE_SIZE, 0
        tile_value = puzzle.board[i][j-1]
    elif move == "RIGHT":
        dx, dy = TILE_SIZE, 0
        tile_value = puzzle.board[i][j+1]
    else:
        return

    frames = 5
    for frame in range(frames+1):
        screen.fill(WHITE)
        temp_board = [row[:] for row in puzzle.board]
        temp_board[i][j] = tile_value
        if move == "UP":
            temp_board[i-1][j] = 0
        elif move == "DOWN":
            temp_board[i+1][j] = 0
        elif move == "LEFT":
            temp_board[i][j-1] = 0
        elif move == "RIGHT":
            temp_board[i][j+1] = 0
        draw_board(temp_board, x, y, TILE_SIZE, observable_cells)
        
        progress = frame / frames
        temp_x = x + j * TILE_SIZE + dx * progress
        temp_y = y + i * TILE_SIZE + dy * progress
        pygame.draw.rect(screen, TILE_COLORS[tile_value], (temp_x, temp_y, TILE_SIZE, TILE_SIZE))
        pygame.draw.rect(screen, BLACK, (temp_x, temp_y, TILE_SIZE, TILE_SIZE), 2)
        if tile_value != 0:
            text = PUZZLE_FONT.render(str(tile_value), True, BLACK)
            text_rect = text.get_rect(center=(temp_x + TILE_SIZE//2, temp_y + TILE_SIZE//2))
            screen.blit(text, text_rect)
        
        draw_info(INFO_X, INFO_Y, elapsed_time_str, step_count, nodes_explored, len(full_solution_moves), belief_states)
        draw_all_groups()
        draw_step_slider(SLIDER_X, SLIDER_Y, SLIDER_WIDTH, SLIDER_HEIGHT, current_step, len(full_solution_moves))
        pygame.display.flip()
        clock.tick(60)

# Vẽ tất cả nhóm thuật toán và nút điều khiển
def draw_all_groups():
    global algorithm_buttons
    groups = [
        ("Tìm Kiếm Không Thông Tin", [
            "Breadth First Search", "Depth First Search", "Uniform Cost Search", "Iterative Deepening DFS"
        ], 0),
        ("Tìm Kiếm Có Thông Tin", [
            "Greedy Best First Search", "A* Search", "IDA* Search"
        ], 1),
        ("Tìm Kiếm Cục Bộ", [
            "Simple Hill Climbing", "Steepest Ascent Hill Climbing", "Stochastic Hill Climbing", "Beam Search", "Simulated Annealing"
        ], 2),
        ("Môi Trường Phức Tạp", [
            "And-Or Graph Search", "Belief State Search", "Partial Observation Search"
        ], 3),
        ("CSPs", [
            "Backtracking Search", "Forward Checking"
        ], 4),
        ("Học Tăng Cường", [
            "Q-Learning"
        ], 5)
    ]
    group_buttons = []
    for i, (title, algorithms, group_id) in enumerate(groups):
        x = GROUP_START_X + (i % 3) * (GROUP_WIDTH + GROUP_MARGIN)
        y = GROUP_START_Y + (i // 3) * (GROUP_HEIGHT + GROUP_MARGIN)
        draw_group(title, x, y)
        group_buttons.append((title, algorithms, pygame.Rect(x, y, GROUP_WIDTH, GROUP_HEIGHT)))
    
    algorithm_buttons = []
    if selected_group is not None:
        title, algorithms, rect = selected_group
        button_y = rect.y + GROUP_HEIGHT + BUTTON_MARGIN
        for alg in algorithms:
            button_rect = pygame.Rect(rect.x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
            algorithm_buttons.append((alg, button_rect))
            button_y += BUTTON_HEIGHT + BUTTON_MARGIN
        draw_buttons(algorithm_buttons)

    control_buttons = [
        ("Bước Tiếp Theo", pygame.Rect(GROUP_START_X, INFO_Y + INFO_HEIGHT + 10, BUTTON_WIDTH//2, BUTTON_HEIGHT)),
        ("Bước Trước Đó", pygame.Rect(GROUP_START_X + BUTTON_WIDTH//2 + 10, INFO_Y + INFO_HEIGHT + 10, BUTTON_WIDTH//2, BUTTON_HEIGHT)),
        ("Khởi Động Lại", pygame.Rect(GROUP_START_X + BUTTON_WIDTH + 20, INFO_Y + INFO_HEIGHT + 10, BUTTON_WIDTH//2, BUTTON_HEIGHT)),
        ("Đặt Belief States", pygame.Rect(GROUP_START_X, INFO_Y + INFO_HEIGHT + 50, BUTTON_WIDTH, BUTTON_HEIGHT)),
        ("Đặt Ô Quan Sát", pygame.Rect(GROUP_START_X + BUTTON_WIDTH + 10, INFO_Y + INFO_HEIGHT + 50, BUTTON_WIDTH, BUTTON_HEIGHT))
    ]
    draw_buttons(control_buttons)
    return group_buttons, control_buttons

# Thuật toán tìm kiếm không thông tin
def bfs(start, goal):
    # Tìm kiếm theo chiều rộng
    visited = set()
    queue = deque([start])
    nodes_explored = 0
    max_memory = 1
    depth = 0
    while queue:
        current = queue.popleft()
        nodes_explored += 1
        visited.add(current)
        if current.board == goal.board:
            return get_solution(current), nodes_explored, depth, max_memory
        for move in current.generate_moves():
            new_state = current.apply_move(move)
            if new_state not in visited:
                queue.append(new_state)
                max_memory = max(max_memory, len(queue) + len(visited))
        depth += 1
    return None, nodes_explored, 0, max_memory

def dfs(start, goal):
    # Tìm kiếm theo chiều sâu
    visited = set()
    stack = [(start, [], 0)]
    max_depth = 50
    nodes_explored = 0
    max_memory = 1
    while stack:
        current, path, depth = stack.pop()
        nodes_explored += 1
        if depth > max_depth:
            continue
        if current.board == goal.board:
            return path, nodes_explored, depth, max_memory
        state_tuple = tuple(map(tuple, current.board))
        if state_tuple in visited:
            continue
        visited.add(state_tuple)
        moves = current.generate_moves()
        for move in reversed(moves):
            new_state = current.apply_move(move)
            new_tuple = tuple(map(tuple, new_state.board))
            if new_tuple not in visited:
                stack.append((new_state, path + [move], depth + 1))
                max_memory = max(max_memory, len(stack) + len(visited))
    return None, nodes_explored, 0, max_memory

def ucs(start, goal):
    # Tìm kiếm chi phí đồng nhất
    counter = itertools.count()
    pq = [(0, next(counter), start)]
    visited = {}
    nodes_explored = 0
    max_memory = 1
    depth = 0
    while pq:
        cost, _, current = heapq.heappop(pq)
        nodes_explored += 1
        if current.board == goal.board:
            return get_solution(current), nodes_explored, depth, max_memory
        state_tuple = tuple(map(tuple, current.board))
        if state_tuple in visited and visited[state_tuple] <= cost:
            continue
        visited[state_tuple] = cost
        depth = max(depth, cost)
        for move in current.generate_moves():
            new_state = current.apply_move(move)
            new_cost = cost + 1
            heapq.heappush(pq, (new_cost, next(counter), new_state))
            max_memory = max(max_memory, len(pq) + len(visited))
    return None, nodes_explored, 0, max_memory

def dls(state, goal, depth, visited):
    # Tìm kiếm giới hạn độ sâu
    nodes_explored = [0]
    if state.board == goal.board:
        return get_solution(state), nodes_explored[0]
    if depth == 0:
        return None, nodes_explored[0]
    nodes_explored[0] += 1
    visited.add(state)
    for move in state.generate_moves():
        new_state = state.apply_move(move)
        if new_state not in visited:
            result, nodes = dls(new_state, goal, depth - 1, visited)
            nodes_explored[0] += nodes
            if result is not None:
                return result, nodes_explored[0]
    return None, nodes_explored[0]

def iddfs(start, goal, max_depth=30):
    # Tìm kiếm lặp sâu dần
    nodes_explored = 0
    max_memory = 0
    for depth in range(max_depth):
        visited = set()
        result, nodes = dls(start, goal, depth, visited)
        nodes_explored += nodes
        max_memory = max(max_memory, len(visited))
        if result is not None:
            return result, nodes_explored, len(result), max_memory
    return None, nodes_explored, 0, max_memory

# Thuật toán tìm kiếm có thông tin
def greedy(start, goal):
    # Tìm kiếm tham lam theo heuristic
    counter = itertools.count()
    pq = [(heuristic(start.board), next(counter), start)]
    visited = set()
    nodes_explored = 0
    max_memory = 1
    depth = 0
    while pq:
        h, _, current = heapq.heappop(pq)
        nodes_explored += 1
        if current.board == goal.board:
            return get_solution(current), nodes_explored, depth, max_memory
        visited.add(current)
        for move in current.generate_moves():
            new_state = current.apply_move(move)
            if new_state not in visited:
                heapq.heappush(pq, (heuristic(new_state.board), next(counter), new_state))
                max_memory = max(max_memory, len(pq) + len(visited))
        depth += 1
    return None, nodes_explored, 0, max_memory

def astar(start, goal):
    # Tìm kiếm A*
    counter = itertools.count()
    f0 = heuristic(start.board)
    pq = [(f0, 0, next(counter), start)]
    visited = {}
    nodes_explored = 0
    max_memory = 1
    while pq:
        f, g, _, current = heapq.heappop(pq)
        nodes_explored += 1
        state_tuple = tuple(map(tuple, current.board))
        if current.board == goal.board:
            path = []
            while current.parent is not None:
                path.append(current.move)
                current = current.parent
            return path[::-1], nodes_explored, g, max_memory
        if state_tuple in visited and visited[state_tuple] <= g:
            continue
        visited[state_tuple] = g
        for move in current.generate_moves():
            new_state = current.apply_move(move)
            new_g = g + 1
            new_f = new_g + heuristic(new_state.board)
            new_state_tuple = tuple(map(tuple, new_state.board))
            if new_state_tuple not in visited or new_g < visited[new_state_tuple]:
                heapq.heappush(pq, (new_f, new_g, next(counter), new_state))
                max_memory = max(max_memory, len(pq) + len(visited))
    return None, nodes_explored, 0, max_memory

def ida_star(start, goal):
    # Tìm kiếm IDA*
    def search(node, g, bound):
        nodes_explored[0] += 1
        f = g + heuristic(node.board)
        if f > bound:
            return f
        if node.board == goal.board:
            return get_solution(node)
        min_bound = float('inf')
        for move in node.generate_moves():
            new_state = node.apply_move(move)
            result = search(new_state, g + 1, bound)
            if isinstance(result, list):
                return result
            min_bound = min(min_bound, result)
        return min_bound

    nodes_explored = [0]
    bound = heuristic(start.board)
    max_memory = 0
    depth = 0
    while True:
        result = search(start, 0, bound)
        max_memory = max(max_memory, nodes_explored[0])
        if isinstance(result, list):
            return result, nodes_explored[0], len(result), max_memory
        if result == float('inf'):
            return None, nodes_explored[0], 0, max_memory
        bound = result
        depth += 1

# Thuật toán tìm kiếm cục bộ (Thêm cơ chế backup)
def simple_hill_climbing(initial_puzzle, goal):
    # Leo đồi đơn giản
    global start_state, current_state, solution_path
    current = initial_puzzle
    nodes_explored = 0
    visited_states = set()
    depth = 0
    max_memory = 0
    max_iterations = 1000
    while depth < max_iterations:
        nodes_explored += 1
        state_tuple = tuple(map(tuple, current.board))
        if state_tuple in visited_states:
            break
        visited_states.add(state_tuple)
        max_memory = max(max_memory, len(visited_states))
        if current.board == goal.board:
            path = get_solution(current)
            return path, nodes_explored, len(path) if path else 0, max_memory
        best_child = None
        best_h = heuristic(current.board)
        for move in current.generate_moves():
            child = current.apply_move(move)
            h_child = heuristic(child.board)
            if h_child < best_h:
                best_h = h_child
                best_child = child
        if best_child is None:
            break
        current = best_child
        depth += 1
    # Backup: Chuyển sang map dễ hơn
    messagebox.showwarning("Cảnh Báo", "Thuật toán Simple Hill Climbing không tìm được đường đi với map hiện tại. Chuyển sang map dễ hơn để thử lại.")
    start_state = Puzzle([[1, 2, 3], [4, 5, 6], [0, 7, 8]])
    current_state = Puzzle([row[:] for row in start_state.board])
    solution_path = [(None, current_state.board)]
    return simple_hill_climbing(start_state, goal)

def steepest_ascent_hill_climbing(initial_puzzle, goal):
    # Leo đồi dốc nhất
    global start_state, current_state, solution_path
    current = initial_puzzle
    nodes_explored = 0
    visited_states = set()
    depth = 0
    max_memory = 0
    max_iterations = 1000
    while depth < max_iterations:
        nodes_explored += 1
        state_tuple = tuple(map(tuple, current.board))
        if state_tuple in visited_states:
            break
        visited_states.add(state_tuple)
        max_memory = max(max_memory, len(visited_states))
        if current.board == goal.board:
            path = get_solution(current)
            return path, nodes_explored, len(path) if path else 0, max_memory
        best_child = None
        best_h = float('inf')
        for move in current.generate_moves():
            child = current.apply_move(move)
            h_child = heuristic(child.board)
            if h_child < best_h:
                best_h = h_child
                best_child = child
        if best_child is None or best_h >= heuristic(current.board):
            break
        current = best_child
        depth += 1
    # Backup: Chuyển sang map dễ hơn
    messagebox.showwarning("Cảnh Báo", "Thuật toán Steepest Ascent Hill Climbing không tìm được đường đi với map hiện tại. Chuyển sang map dễ hơn để thử lại.")
    start_state = Puzzle([[1, 2, 3], [4, 5, 6], [0, 7, 8]])
    current_state = Puzzle([row[:] for row in start_state.board])
    solution_path = [(None, current_state.board)]
    return steepest_ascent_hill_climbing(start_state, goal)

def randomized_hill_climbing(initial_puzzle, goal):
    # Leo đồi ngẫu nhiên
    global start_state, current_state, solution_path
    current = initial_puzzle
    nodes_explored = 0
    visited_states = set()
    depth = 0
    max_memory = 0
    max_iterations = 1000
    while depth < max_iterations:
        nodes_explored += 1
        state_tuple = tuple(map(tuple, current.board))
        if state_tuple in visited_states:
            break
        visited_states.add(state_tuple)
        max_memory = max(max_memory, len(visited_states))
        if current.board == goal.board:
            path = get_solution(current)
            return path, nodes_explored, len(path) if path else 0, max_memory
        improvements = []
        current_h = heuristic(current.board)
        for move in current.generate_moves():
            child = current.apply_move(move)
            h_child = heuristic(child.board)
            if h_child < current_h:
                improvements.append(child)
        if not improvements:
            break
        current = random.choice(improvements)
        depth += 1
    # Backup: Chuyển sang map dễ hơn
    messagebox.showwarning("Cảnh Báo", "Thuật toán Stochastic Hill Climbing không tìm được đường đi với map hiện tại. Chuyển sang map dễ hơn để thử lại.")
    start_state = Puzzle([[1, 2, 3], [4, 5, 6], [0, 7, 8]])
    current_state = Puzzle([row[:] for row in start_state.board])
    solution_path = [(None, current_state.board)]
    return randomized_hill_climbing(start_state, goal)

def beam_search(start, goal, beam_width=5):
    # Tìm kiếm chùm
    global start_state, current_state, solution_path
    beam = [start]
    visited = set()
    nodes_explored = 0
    max_memory = beam_width
    depth = 0
    while beam and depth < 1000:
        nodes_explored += len(beam)
        for state in beam:
            if state.board == goal.board:
                return get_solution(state), nodes_explored, depth, max_memory
        next_beam = []
        for state in beam:
            for move in state.generate_moves():
                new_state = state.apply_move(move)
                state_id = tuple(tuple(row) for row in new_state.board)
                if state_id not in visited:
                    visited.add(state_id)
                    next_beam.append((new_state, heuristic(new_state.board)))
        next_beam.sort(key=lambda x: x[1])
        beam = [state for state, _ in next_beam[:beam_width]]
        max_memory = max(max_memory, len(visited) + len(next_beam))
        depth += 1
    # Backup: Chuyển sang map dễ hơn
    messagebox.showwarning("Cảnh Báo", "Thuật toán Beam Search không tìm được đường đi với map hiện tại. Chuyển sang map dễ hơn để thử lại.")
    start_state = Puzzle([[1, 2, 3], [4, 5, 6], [0, 7, 8]])
    current_state = Puzzle([row[:] for row in start_state.board])
    solution_path = [(None, current_state.board)]
    return beam_search(start_state, goal)

def simulated_annealing(initial_puzzle, goal, initial_temp=100.0, cooling_rate=0.95):
    # Ủ nhiệt mô phỏng
    global start_state, current_state, solution_path
    current = initial_puzzle
    current_h = heuristic(initial_puzzle.board)
    temperature = initial_temp
    nodes_explored = 0
    depth = 0
    max_memory = 0
    max_iterations = 1000
    while temperature > 0.1 and depth < max_iterations:
        nodes_explored += 1
        if current.board == goal.board:
            path = get_solution(current)
            return path, nodes_explored, len(path) if path else 0, max_memory
        neighbors = [current.apply_move(move) for move in current.generate_moves()]
        if not neighbors:
            break
        next_state = random.choice(neighbors)
        next_h = heuristic(next_state.board)
        delta = next_h - current_h
        if delta < 0 or random.random() < math.exp(-delta / temperature):
            current = next_state
            current_h = next_h
            depth += 1
        temperature *= cooling_rate
        max_memory = max(max_memory, depth)
    # Backup: Chuyển sang map dễ hơn
    messagebox.showwarning("Cảnh Báo", "Thuật toán Simulated Annealing không tìm được đường đi với map hiện tại. Chuyển sang map dễ hơn để thử lại.")
    start_state = Puzzle([[1, 2, 3], [4, 5, 6], [0, 7, 8]])
    current_state = Puzzle([row[:] for row in start_state.board])
    solution_path = [(None, current_state.board)]
    return simulated_annealing(start_state, goal)

# Thuật toán môi trường phức tạp
def state_to_tuple(state):
    # Chuyển trạng thái thành tuple để so sánh
    return tuple(tuple(row) for row in state.board)

def and_or_dfs(state, goal, visited, path, depth=0, max_depth=20):
    # Tìm kiếm đồ thị And-Or
    nodes_explored = [0]
    def dfs(state, depth):
        nodes_explored[0] += 1
        if state.board == goal.board:
            return []
        state_tuple = state_to_tuple(state)
        if state_tuple in visited or depth > max_depth:
            return None
        visited.add(state_tuple)
        possible_moves = state.generate_moves()
        if not possible_moves:
            return None
        for move in possible_moves:
            next_state = state.apply_move(move)
            if next_state is None:
                continue
            if next_state.board == goal.board:
                return [move]
            next_plan = dfs(next_state, depth + 1)
            if next_plan is not None:
                return [move] + next_plan
        return None

    result = dfs(state, depth)
    return result, nodes_explored[0], len(result) if result else 0, len(visited)

# Lớp BeliefState để quản lý tập trạng thái belief
class BeliefState:
    def __init__(self, states, parent=None, move=""):
        self.states = states
        self.parent = parent
        self.move = move

    def __eq__(self, other):
        return frozenset(state_to_tuple(s) for s in self.states) == frozenset(state_to_tuple(s) for s in other.states)

    def __hash__(self):
        return hash(frozenset(state_to_tuple(s) for s in self.states))

# Hàm tính heuristic trung bình cho tập belief
def belief_heuristic(belief_states, goal=None):
    if not belief_states:
        return float('inf')
    return sum(heuristic(state.board) for state in belief_states) / len(belief_states)

# Tìm kiếm trên tập trạng thái belief với hàng đợi ưu tiên
def belief_state_search(start, goal, belief_states=None):
    initial_states = belief_states if belief_states else {start}
    initial_belief = BeliefState(initial_states)
    counter = itertools.count()
    # Sử dụng hàng đợi ưu tiên dựa trên heuristic
    pq = [(belief_heuristic(initial_states, goal), 0, next(counter), initial_belief, [])]
    visited = set()
    nodes_explored = 0
    max_memory = 1
    max_depth = 300
    while pq:
        h, g, _, current_belief, path = heapq.heappop(pq)
        nodes_explored += 1
        # Kiểm tra từng trạng thái trong tập belief
        for state in current_belief.states:
            if state.board == goal.board:
                messagebox.showinfo("Thành Công", f"Đã tìm thấy đường đi với {len(path)} bước!")
                return path, nodes_explored, len(path), max_memory, current_belief.states
        if len(path) > max_depth or not current_belief.states:
            continue
        belief_tuple = frozenset(state_to_tuple(s) for s in current_belief.states)
        if belief_tuple in visited:
            continue
        visited.add(belief_tuple)
        sample_state = next(iter(current_belief.states))
        for move in sample_state.generate_moves():
            new_states = set()
            for state in current_belief.states:
                new_state = state.apply_move(move)
                if new_state.board != state.board and is_solvable(new_state.board):
                    new_states.add(new_state)
            if new_states:
                new_belief = BeliefState(new_states, current_belief, move)
                new_g = g + 1
                new_h = belief_heuristic(new_states, goal)
                heapq.heappush(pq, (new_h + new_g, new_g, next(counter), new_belief, path + [move]))
                max_memory = max(max_memory, len(pq) + len(visited))
    # Thông báo lỗi chi tiết nếu thất bại
    error_msg = "Belief State Search thất bại!\n"
    error_msg += f"Số trạng thái belief cuối: {len(current_belief.states) if current_belief else 0}\n"
    error_msg += f"Số nút đã duyệt: {nodes_explored}\n"
    error_msg += f"Độ sâu cuối: {len(path)}"
    messagebox.showerror("Lỗi", error_msg)
    return None, nodes_explored, 0, max_memory, None

# Tìm kiếm với quan sát
def searching_with_observations(start, goal, observation_function, max_iterations=100):
    current = start
    moves = []
    visited = set()
    nodes_explored = 0
    max_memory = 0
    belief_states = {start}
    depth = 0
    if not observable_cells:
        messagebox.showerror("Lỗi", "Chưa chọn ô quan sát! Vui lòng chọn ít nhất một ô.")
        return None, nodes_explored, 0, len(belief_states), belief_states
    # Thông báo ô quan sát đã chọn
    messagebox.showinfo("Ô Quan Sát", f"Đang sử dụng ô quan sát: {observable_cells}\nCác ô này giúp lọc trạng thái belief dựa trên giá trị thực tế.")
    for _ in range(max_iterations):
        nodes_explored += 1
        observation = observation_function(current)
        # Lọc tập belief dựa trên quan sát
        new_belief_states = {s for s in belief_states if observation_function(s) == observation}
        if new_belief_states:
            belief_states = new_belief_states
        else:
            belief_states.add(current)
        max_memory = max(max_memory, len(belief_states) + len(visited))
        if any(s.board == goal.board for s in belief_states):
            messagebox.showinfo("Kết Quả", f"Đã đến đích với {len(moves)} bước, {len(belief_states)} trạng thái belief cuối cùng!")
            return moves, nodes_explored, len(moves), len(belief_states), belief_states
        state_tuple = tuple(map(tuple, current.board))
        if state_tuple in visited:
            continue
        visited.add(state_tuple)
        possible_moves = current.generate_moves()
        best_move = None
        best_h = float('inf')
        for move in possible_moves:
            next_state = current.apply_move(move)
            if next_state:
                next_tuple = tuple(map(tuple, next_state.board))
                if next_tuple not in visited:
                    # Tính heuristic trung bình trên tập belief giả định
                    temp_belief = {s.apply_move(move) for s in belief_states if s.apply_move(move).board != s.board}
                    if temp_belief:
                        h = belief_heuristic(temp_belief, goal)
                        if h < best_h:
                            best_h = h
                            best_move = move
        if best_move:
            current = current.apply_move(best_move)
            moves.append(best_move)
            depth += 1
        else:
            messagebox.showerror("Lỗi", f"Không tìm thấy bước di chuyển tiếp theo sau {depth} bước, {len(belief_states)} trạng thái belief!")
            return None, nodes_explored, 0, len(belief_states), belief_states
    messagebox.showerror("Lỗi", f"Đã vượt quá giới hạn {max_iterations} bước, {len(belief_states)} trạng thái belief!")
    return None, nodes_explored, 0, len(belief_states), belief_states

# Tạo quan sát từ ô quan sát
def simple_observation(state):
    board = state.board
    obs = [[-1 for _ in range(3)] for _ in range(3)]
    for i, j in observable_cells:
        obs[i][j] = board[i][j]
    return tuple(tuple(row) for row in obs)

# Tìm kiếm quay lui
def backtracking_search(start, goal, max_depth=50):
    nodes_explored = [0]
    visited = set()
    def backtrack(state, depth):
        nodes_explored[0] += 1
        if state.board == goal.board:
            return get_solution(state)
        if depth >= max_depth or not is_solvable(state.board):
            return None
        state_tuple = tuple(map(tuple, state.board))
        if state_tuple in visited:
            return None
        visited.add(state_tuple)
        for move in state.generate_moves():
            new_state = state.apply_move(move)
            result = backtrack(new_state, depth + 1)
            if result:
                return result
        visited.remove(state_tuple)
        return None

    result = backtrack(start, 0)
    return result, nodes_explored[0], len(result) if result else 0, len(visited)

# Tìm kiếm kiểm tra trước
def forward_checking_search(start, goal, max_depth=50):
    nodes_explored = [0]
    visited = set()
    def backtrack(state, depth):
        nodes_explored[0] += 1
        if state.board == goal.board:
            return get_solution(state)
        if depth >= max_depth or not is_solvable(state.board):
            return None
        state_tuple = tuple(map(tuple, state.board))
        if state_tuple in visited:
            return None
        visited.add(state_tuple)
        for move in state.generate_moves():
            new_state = state.apply_move(move)
            result = backtrack(new_state, depth + 1)
            if result:
                return result
        visited.remove(state_tuple)
        return None

    result = backtrack(start, 0)
    return result, nodes_explored[0], len(result) if result else 0, len(visited)

# Thuật toán học tăng cường
class QLearning:
    def __init__(self, learning_rate=0.1, discount_factor=0.9, exploration_rate=0.3):
        self.q_table = {}
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = exploration_rate
    
    def get_state_key(self, state):
        return tuple(tuple(row) for row in state.board)
    
    def get_action(self, state, possible_moves):
        state_key = self.get_state_key(state)
        if state_key not in self.q_table:
            self.q_table[state_key] = {move: 0 for move in possible_moves}
        
        if random.random() < self.epsilon:
            return random.choice(possible_moves)
        else:
            return max(self.q_table[state_key].items(), key=lambda x: x[1])[0]
    
    def update(self, state, action, reward, next_state, next_possible_moves):
        state_key = self.get_state_key(state)
        next_state_key = self.get_state_key(next_state)
        
        if state_key not in self.q_table:
            self.q_table[state_key] = {action: 0}
        if next_state_key not in self.q_table:
            self.q_table[next_state_key] = {move: 0 for move in next_possible_moves}
        
        old_value = self.q_table[state_key][action]
        next_max = max(self.q_table[next_state_key].values()) if next_possible_moves else 0
        new_value = (1 - self.lr) * old_value + self.lr * (reward + self.gamma * next_max)
        self.q_table[state_key][action] = new_value

# Thuật toán Q-Learning
def q_learning(start, goal, episodes=10000, max_steps=2000):
    global current_state, solution_path
    q_agent = QLearning(learning_rate=0.1, discount_factor=0.9, exploration_rate=0.3)
    best_path = None
    min_steps = float('inf')
    nodes_explored = 0
    max_memory = 0
    
    for episode in range(episodes):
        current_state = Puzzle([row[:] for row in start.board])
        path = []
        steps = 0
        visited = set()
        
        while steps < max_steps:
            nodes_explored += 1
            state_key = q_agent.get_state_key(current_state)
            if state_key in visited and steps > 0:
                break
            visited.add(state_key)
            
            if current_state.board == goal.board:
                if steps < min_steps:
                    min_steps = steps
                    best_path = path
                break
            
            possible_moves = current_state.generate_moves()
            if not possible_moves:
                break
            
            action = q_agent.get_action(current_state, possible_moves)
            next_state = current_state.apply_move(action)
            
            h_current = heuristic(current_state.board)
            h_next = heuristic(next_state.board)
            reward = -1
            if next_state.board == goal.board:
                reward = 10000
            elif h_next < h_current:
                reward += 2
            elif h_next > h_current:
                reward -= 3
            
            next_moves = next_state.generate_moves()
            q_agent.update(current_state, action, reward, next_state, next_moves)
            
            current_state = next_state
            path.append(action)
            steps += 1
            max_memory = max(max_memory, len(q_agent.q_table))
        
        q_agent.epsilon = max(0.05, q_agent.epsilon * 0.999)
    
    if best_path is not None:
        current_state = Puzzle([row[:] for row in start.board])
        solution_path = [(None, current_state.board)]
        temp_state = current_state
        for move in best_path:
            temp_state = temp_state.apply_move(move)
            solution_path.append((move, temp_state.board))
        if temp_state.board == goal.board:
            messagebox.showinfo("Kết Quả Q-Learning", f"Tìm được đường đi với {len(best_path)} bước!")
            return best_path, nodes_explored, len(best_path), max_memory
        else:
            messagebox.showerror("Lỗi", "Đường đi Q-Learning không đến đích!")
            return None, nodes_explored, 0, max_memory
    else:
        messagebox.showerror("Lỗi", f"Q-Learning thất bại sau {episodes} tập, {nodes_explored} nút duyệt!")
        return None, nodes_explored, 0, max_memory

# Các tập Belief State (đơn giản hóa, gần đích)
BELIEF_SETS = [
    ([[[1, 2, 3], [4, 5, 6], [7, 8, 0]], [[1, 2, 3], [4, 5, 6], [7, 0, 8]]], "Set 1"),  # 0-1 bước
    ([[[1, 2, 3], [4, 5, 6], [7, 0, 8]], [[1, 2, 3], [4, 5, 0], [7, 8, 6]]], "Set 2"),  # 1-2 bước
    ([[[1, 2, 3], [4, 5, 0], [7, 8, 6]], [[1, 2, 3], [4, 0, 5], [7, 8, 6]]], "Set 3")   # 2 bước
]

# Đặt tập Belief State
def set_belief_states():
    global belief_states, current_state, solution_path, is_dialog_open
    if is_dialog_open:
        return
    is_dialog_open = True

    def select_belief_set():
        global belief_states, current_state, solution_path
        selected_set = combo.get()
        if selected_set == "Custom Input":
            custom_input()
        else:
            for belief_set, name in BELIEF_SETS:
                if name == selected_set:
                    belief_states = {Puzzle(s) for s in belief_set}
                    current_state = Puzzle(belief_set[0])
                    solution_path = [(None, current_state.board)]
                    set_details = f"Belief {name}:\n"
                    for i, state in enumerate(belief_set, 1):
                        set_details += f"Trạng Thái {i}: {state}\n"
                    messagebox.showinfo(f"Đã Chọn Belief {name}", set_details)
                    window.destroy()
                    break

    def custom_input():
        global belief_states, current_state, solution_path
        input_window = Toplevel(tk_root)
        input_window.title("Nhập Belief States Tùy Chỉnh")
        Label(input_window, text="Nhập tập trạng thái (định dạng: [[[1,2,3],[4,5,6],[7,8,0]], ...]):").pack(pady=5)
        entry = Entry(input_window, width=50)
        entry.pack(pady=5)
        def submit():
            global belief_states, current_state, solution_path
            input_str = entry.get()
            try:
                states = eval(input_str)
                if not all(isinstance(s, list) and len(s) == 3 and all(len(row) == 3 for row in s) for s in states):
                    raise ValueError("Định dạng không hợp lệ!")
                belief_states = {Puzzle(s) for s in states}
                current_state = Puzzle(states[0])
                solution_path = [(None, current_state.board)]
                messagebox.showinfo("Thành Công", "Đã cập nhật tập trạng thái tùy chỉnh!")
                input_window.destroy()
                window.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Nhập không hợp lệ: {str(e)}")
        Button(input_window, text="Xác Nhận", command=submit).pack(pady=5)

    window = Toplevel(tk_root)
    window.title("Chọn Belief States")
    Label(window, text="Chọn một tập trạng thái hoặc nhập tùy chỉnh:").pack(pady=5)
    options = ["Custom Input"] + [name for _, name in BELIEF_SETS]
    combo = ttk.Combobox(window, values=options, state="readonly")
    combo.set(options[0])
    combo.pack(pady=5)
    Button(window, text="Chọn", command=select_belief_set).pack(pady=5)
    window.wait_window()
    is_dialog_open = False

# Đặt các ô quan sát
def set_observable_cells():
    global observable_cells, current_state
    messagebox.showinfo("Hướng Dẫn", "Nhấn vào bảng để chọn ô quan sát (giá trị ô sẽ được dùng để lọc trạng thái). Nhấn Enter để xác nhận. Phải chọn ít nhất một ô.")
    selecting = True
    temp_cells = observable_cells.copy()
    while selecting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if BOARD_X <= mx < BOARD_X + BOARD_WIDTH and BOARD_Y <= my < BOARD_Y + BOARD_HEIGHT:
                    j = (mx - BOARD_X) // TILE_SIZE
                    i = (my - BOARD_Y) // TILE_SIZE
                    cell = (i, j)
                    if cell in temp_cells:
                        temp_cells.remove(cell)
                    else:
                        temp_cells.append(cell)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if not temp_cells:
                    messagebox.showerror("Lỗi", "Phải chọn ít nhất một ô quan sát!")
                else:
                    observable_cells = temp_cells[:]
                    selecting = False
        screen.fill(WHITE)
        draw_board_with_board(current_state, BOARD_X, BOARD_Y, TILE_SIZE, temp_cells)
        draw_info(INFO_X, INFO_Y, elapsed_time_str, step_count, nodes_explored, len(full_solution_moves), belief_states)
        draw_all_groups()
        pygame.display.flip()
    messagebox.showinfo("Thành Công", f"Đã đặt ô quan sát: {observable_cells}")

# Khởi động lại trò chơi
def restart():
    global start_state, goal_state, animating, full_solution_moves, solution_path, step_count, elapsed_time_str, algorithm_running, last_move_time, start_time, end_time, elapsed_time, move_interval, current_state, current_step, solution_completed, belief_states, observable_cells, current_algorithm, selected_group, nodes_explored, interrupt_animation
    start_state = Puzzle([[7, 2, 4], [5, 0, 6], [8, 3, 1]])
    goal_state = Puzzle([[1, 2, 3], [4, 5, 6], [7, 8, 0]])
    if not is_solvable(start_state.board):
        start_state = Puzzle([[1, 2, 3], [4, 5, 6], [0, 7, 8]])
    animating = False
    full_solution_moves = []
    solution_path = [(None, start_state.board)]
    step_count = 0
    nodes_explored = 0
    elapsed_time_str = "00:00:00"
    algorithm_running = False
    last_move_time = 0
    start_time = 0
    end_time = 0
    elapsed_time = 0
    move_interval = 100
    current_state = Puzzle([row[:] for row in start_state.board])
    current_step = 0
    solution_completed = False
    belief_states = None
    observable_cells = []
    current_algorithm = None
    selected_group = None
    interrupt_animation = True

# Chạy thuật toán
def run_algorithm(alg):
    global start_state, goal_state, full_solution_moves, animating, start_time, end_time, elapsed_time, elapsed_time_str, step_count, nodes_explored, solution_path, algorithm_running, last_move_time, move_interval, current_state, current_step, solution_completed, current_algorithm, selected_group, belief_states, interrupt_animation
    step_count = 0
    nodes_explored = 0
    full_solution_moves = []
    solution_path = []
    last_move_time = 0
    move_interval = 100
    current_step = 0
    solution_completed = False
    elapsed_time_str = "00:00:00"
    algorithm_running = True
    interrupt_animation = False
    current_algorithm = alg
    selected_group = None
    if alg == "Belief State Search" and belief_states is None:
        messagebox.showerror("Lỗi", "Vui lòng đặt tập trạng thái belief trước!")
        algorithm_running = False
        return
    current_state = Puzzle([row[:] for row in start_state.board])
    solution_path = [(None, current_state.board)]
    start_time = time.perf_counter()
    result = None
    try:
        if alg == "Depth First Search":
            result = dfs(start_state, goal_state)
        elif alg == "Breadth First Search":
            result = bfs(start_state, goal_state)
        elif alg == "Uniform Cost Search":
            result = ucs(start_state, goal_state)
        elif alg == "Iterative Deepening DFS":
            result = iddfs(start_state, goal_state)
        elif alg == "Greedy Best First Search":
            result = greedy(start_state, goal_state)
        elif alg == "A* Search":
            result = astar(start_state, goal_state)
        elif alg == "IDA* Search":
            result = ida_star(start_state, goal_state)
        elif alg == "Simple Hill Climbing":
            result = simple_hill_climbing(start_state, goal_state)
        elif alg == "Steepest Ascent Hill Climbing":
            result = steepest_ascent_hill_climbing(start_state, goal_state)
        elif alg == "Stochastic Hill Climbing":
            result = randomized_hill_climbing(start_state, goal_state)
        elif alg == "Beam Search":
            result = beam_search(start_state, goal_state)
        elif alg == "Simulated Annealing":
            result = simulated_annealing(start_state, goal_state)
        elif alg == "And-Or Graph Search":
            visited = set()
            result = and_or_dfs(start_state, goal_state, visited, [])
        elif alg == "Belief State Search":
            result = belief_state_search(start_state, goal_state, belief_states)
        elif alg == "Partial Observation Search":
            result = searching_with_observations(start_state, goal_state, simple_observation)
        elif alg == "Backtracking Search":
            result = backtracking_search(start_state, goal_state)
        elif alg == "Forward Checking":
            result = forward_checking_search(start_state, goal_state)
        elif alg == "Q-Learning":
            result = q_learning(start_state, goal_state)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Thuật toán {alg} thất bại: {str(e)}")
        algorithm_running = False
        return
    algorithm_running = False
    if result:
        if alg in ["Belief State Search", "Partial Observation Search"]:
            moves, nodes_explored, depth, memory, belief_states = result
        else:
            moves, nodes_explored, depth, memory = result
        if moves:
            full_solution_moves = moves[:]
            step_count = len(moves)
            animating = True
            temp_state = current_state
            solution_path = [(None, temp_state.board)]
            for move in full_solution_moves:
                temp_state = temp_state.apply_move(move)
                solution_path.append((move, temp_state.board))
            if temp_state.board == goal_state.board:
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                elapsed_time_str = f"{elapsed_time:.3f}s"
                comparison_data.append({
                    'algorithm': alg,
                    'time': elapsed_time,
                    'steps': step_count,
                    'nodes_explored': nodes_explored,
                    'depth': depth,
                    'memory': memory
                })
                for i, move in enumerate(full_solution_moves):
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            mx, my = event.pos
                            for label, rect in draw_all_groups()[1]:
                                if rect.collidepoint(mx, my) and label == "Khởi Động Lại":
                                    restart()
                                    return
                    if interrupt_animation:
                        return
                    animate_move(current_state, move, BOARD_X, BOARD_Y)
                    current_state = current_state.apply_move(move)
                    current_step = i + 1
                    pygame.time.wait(move_interval)
                solution_completed = True
            else:
                messagebox.showerror("Lỗi", f"Giải pháp của {alg} không đến đích!")
                animating = False
        else:
            messagebox.showerror("Lỗi", f"Không tìm thấy bước di chuyển với {alg}!")
            animating = False
    else:
        messagebox.showerror("Lỗi", f"Không tìm thấy giải pháp với {alg}!")
        animating = False

# Hàm chính
def main():
    global start_state, goal_state, animating, full_solution_moves, last_move_time, elapsed_time_str, step_count, nodes_explored, solution_path, algorithm_running, start_time, end_time, elapsed_time, move_interval, current_state, current_step, solution_completed, current_algorithm, selected_group, dragging_slider
    start_state = Puzzle([[7, 2, 4], [5, 0, 6], [8, 3, 1]])
    goal_state = Puzzle([[1, 2, 3], [4, 5, 6], [7, 8, 0]])
    if not is_solvable(start_state.board):
        start_state = Puzzle([[1, 2, 3], [4, 5, 6], [0, 7, 8]])
    animating = False
    full_solution_moves = []
    last_move_time = 0
    move_interval = 100
    elapsed_time_str = "00:00:00"
    step_count = 0
    nodes_explored = 0
    solution_path = [(None, start_state.board)]
    algorithm_running = False
    start_time = 0
    end_time = 0
    elapsed_time = 0
    current_state = Puzzle([row[:] for row in start_state.board])
    current_step = 0
    solution_completed = False
    current_algorithm = None
    selected_group = None
    running = True
    while running:
        screen.fill(WHITE)
        draw_board_with_board(current_state, BOARD_X, BOARD_Y, TILE_SIZE, observable_cells)
        draw_info(INFO_X, INFO_Y, elapsed_time_str, step_count, nodes_explored, len(full_solution_moves), belief_states)
        group_buttons, control_buttons = draw_all_groups()
        draw_step_slider(SLIDER_X, SLIDER_Y, SLIDER_WIDTH, SLIDER_HEIGHT, current_step, len(full_solution_moves))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # Kiểm tra kéo thanh trượt
                thumb_x = SLIDER_X + (current_step / max(1, len(full_solution_moves))) * (SLIDER_WIDTH - SLIDER_THUMB_SIZE)
                thumb_rect = pygame.Rect(thumb_x, SLIDER_Y + (SLIDER_HEIGHT - SLIDER_THUMB_SIZE) / 2, SLIDER_THUMB_SIZE, SLIDER_THUMB_SIZE)
                if thumb_rect.collidepoint(mx, my) and full_solution_moves:
                    dragging_slider = True
                # Kiểm tra các nút
                for alg, rect in algorithm_buttons:
                    if rect.collidepoint(mx, my):
                        run_algorithm(alg)
                        break
                for title, algorithms, rect in group_buttons:
                    if rect.collidepoint(mx, my):
                        if selected_group and selected_group[0] == title:
                            selected_group = None
                        else:
                            selected_group = (title, algorithms, rect)
                        break
                for label, rect in control_buttons:
                    if rect.collidepoint(mx, my):
                        if label == "Khởi Động Lại":
                            restart()
                        elif label == "Bước Tiếp Theo" and full_solution_moves and current_step < len(full_solution_moves):
                            move = full_solution_moves[current_step]
                            animate_move(current_state, move, BOARD_X, BOARD_Y)
                            current_state = current_state.apply_move(move)
                            current_step += 1
                            if current_step >= len(full_solution_moves):
                                solution_completed = True
                        elif label == "Bước Trước Đó" and current_step > 0:
                            current_step -= 1
                            current_state = Puzzle(solution_path[current_step][1])
                        elif label == "Đặt Belief States":
                            set_belief_states()
                        elif label == "Đặt Ô Quan Sát":
                            set_observable_cells()
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging_slider = False
            elif event.type == pygame.MOUSEMOTION and dragging_slider and full_solution_moves:
                mx, my = event.pos
                # Tính bước mới dựa trên vị trí chuột
                relative_x = mx - SLIDER_X
                new_step = int((relative_x / (SLIDER_WIDTH - SLIDER_THUMB_SIZE)) * len(full_solution_moves))
                new_step = max(0, min(new_step, len(full_solution_moves)))
                if new_step != current_step:
                    current_step = new_step
                    current_state = Puzzle(solution_path[current_step][1])
        
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()