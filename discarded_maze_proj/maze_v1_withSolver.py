import pygame
import random
#https://gemini.google.com/app/84290c8c3aca1a7f?hl=zh-TW
# Basic Settings
WIDTH, HEIGHT = 800, 600
CELL_SIZE = 20
COLS, ROWS = WIDTH // CELL_SIZE, HEIGHT // CELL_SIZE

class Cell:
    def __init__(self, r, c):
        self.r, self.c = r, c
        self.visited = False
        self.walls = {'top': True, 'right': True, 'bottom': True, 'left': True}

    def draw(self, sc):
        x, y = self.c * CELL_SIZE, self.r * CELL_SIZE
        if self.visited:
            pygame.draw.rect(sc, (240, 240, 240), (x, y, CELL_SIZE, CELL_SIZE))
        
        # Walls
        color = (0, 0, 0)
        if self.walls['top']: pygame.draw.line(sc, color, (x, y), (x + CELL_SIZE, y), 2)
        if self.walls['right']: pygame.draw.line(sc, color, (x + CELL_SIZE, y), (x + CELL_SIZE, y + CELL_SIZE), 2)
        if self.walls['bottom']: pygame.draw.line(sc, color, (x, y + CELL_SIZE), (x + CELL_SIZE, y + CELL_SIZE), 2)
        if self.walls['left']: pygame.draw.line(sc, color, (x, y), (x, y + CELL_SIZE), 2)

def remove_walls(current, next_node):
    dx = current.c - next_node.c
    if dx == 1:
        current.walls['left'] = False
        next_node.walls['right'] = False
    elif dx == -1:
        current.walls['right'] = False
        next_node.walls['left'] = False
    dy = current.r - next_node.r
    if dy == 1:
        current.walls['top'] = False
        next_node.walls['bottom'] = False
    elif dy == -1:
        current.walls['bottom'] = False
        next_node.walls['top'] = False

def get_neighbors(cell, grid):
    neighbors = []
    directions = [(0, 1, 'right'), (0, -1, 'left'), (1, 0, 'bottom'), (-1, 0, 'top')]
    for dr, dc, wall in directions:
        nr, nc = cell.r + dr, cell.c + dc
        if 0 <= nr < ROWS and 0 <= nc < COLS and not grid[nr][nc].visited:
            neighbors.append(grid[nr][nc])
    return neighbors

# --- Algorithms ---

def generate_binary_tree(grid):
    """Bias: Always looks Top or Right. Very fast, very structured."""
    for r in range(ROWS):
        for c in range(COLS):
            grid[r][c].visited = True
            choices = []
            if r > 0: choices.append(grid[r-1][c])
            if c < COLS - 1: choices.append(grid[r][c+1])
            if choices:
                remove_walls(grid[r][c], random.choice(choices))

def generate_backtracker(grid):
    """DFS: Creates long, winding paths. Great for classic mazes."""
    stack = []
    current = grid[0][0]
    current.visited = True
    
    while True:
        neighbors = get_neighbors(current, grid)
        if neighbors:
            next_node = random.choice(neighbors)
            stack.append(current)
            remove_walls(current, next_node)
            current = next_node
            current.visited = True
        elif stack:
            current = stack.pop()
        else:
            break
def generate_prims(grid):
    """Randomized Prim's Algorithm: Grows the maze from a central point."""
    walls_list = []
    
    # 1. Start at a random cell
    start_r, start_c = random.randint(0, ROWS-1), random.randint(0, COLS-1)
    start_cell = grid[start_r][start_c]
    start_cell.visited = True
    
    # 2. Add neighbors of start cell to the wall list
    def add_walls(cell):
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dr, dc in directions:
            nr, nc = cell.r + dr, cell.c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS and not grid[nr][nc].visited:
                # We store (current_cell, next_neighbor_cell)
                walls_list.append((cell, grid[nr][nc]))

    add_walls(start_cell)

    while walls_list:
        # 3. Pick a random "wall" (edge) from the list
        current, next_node = random.choice(walls_list)
        walls_list.remove((current, next_node))

        # 4. If the neighbor hasn't been visited, connect them
        if not next_node.visited:
            remove_walls(current, next_node)
            next_node.visited = True
            # 5. Add new potential walls to the list
            add_walls(next_node)
def main():
    pygame.init()
    sc = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Maze Algorithms - NTU IM DSAP")
    grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
    
    print("Commands: [1] Backtracker (DFS) | [2] Binary Tree | [3] Prim's | [ESC] Reset")
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
                if event.key == pygame.K_1:
                    grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
                    generate_backtracker(grid)
                if event.key == pygame.K_2:
                    grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
                    generate_binary_tree(grid)
                if event.key == pygame.K_3:
                    grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
                    generate_prims(grid)
        sc.fill((100, 100, 100))
        for row in grid:
            for cell in row:
                cell.draw(sc)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
