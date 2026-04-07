import pygame
import random
from collections import deque
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

    def draw(self, sc, color=(240, 240, 240)):
        x, y = self.c * CELL_SIZE, self.r * CELL_SIZE
        if self.visited:
            pygame.draw.rect(sc, color, (x, y, CELL_SIZE, CELL_SIZE))
        
        line_color = (0, 0, 0)
        if self.walls['top']: pygame.draw.line(sc, line_color, (x, y), (x + CELL_SIZE, y), 2)
        if self.walls['right']: pygame.draw.line(sc, line_color, (x + CELL_SIZE, y), (x + CELL_SIZE, y + CELL_SIZE), 2)
        if self.walls['bottom']: pygame.draw.line(sc, line_color, (x, y + CELL_SIZE), (x + CELL_SIZE, y + CELL_SIZE), 2)
        if self.walls['left']: pygame.draw.line(sc, line_color, (x, y), (x, y + CELL_SIZE), 2)

def remove_walls(current, next_node):
    dx, dy = current.c - next_node.c, current.r - next_node.r
    if dx == 1: current.walls['left'] = next_node.walls['right'] = False
    elif dx == -1: current.walls['right'] = next_node.walls['left'] = False
    if dy == 1: current.walls['top'] = next_node.walls['bottom'] = False
    elif dy == -1: current.walls['bottom'] = next_node.walls['top'] = False

# --- Generators ---

def binary_tree_gen(grid):
    for r in range(ROWS):
        for c in range(COLS):
            grid[r][c].visited = True
            choices = []
            if r > 0: choices.append(grid[r-1][c])
            if c < COLS - 1: choices.append(grid[r][c+1])
            if choices: remove_walls(grid[r][c], random.choice(choices))
            yield grid[r][c]

def prims_gen(grid):
    walls_list = []
    start = grid[random.randint(0, ROWS-1)][random.randint(0, COLS-1)]
    start.visited = True
    def get_f(cell):
        return [(cell, grid[cell.r+dr][cell.c+dc]) for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)] 
                if 0<=cell.r+dr<ROWS and 0<=cell.c+dc<COLS and not grid[cell.r+dr][cell.c+dc].visited]
    walls_list.extend(get_f(start))
    while walls_list:
        curr, nxt = random.choice(walls_list)
        walls_list.remove((curr, nxt))
        if not nxt.visited:
            remove_walls(curr, nxt); nxt.visited = True
            walls_list.extend(get_f(nxt)); yield nxt

def backtracker_gen(grid):
    stack, curr = [], grid[0][0]
    curr.visited = True
    while True:
        ns = [grid[curr.r+dr][curr.c+dc] for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]
              if 0<=curr.r+dr<ROWS and 0<=curr.c+dc<COLS and not grid[curr.r+dr][curr.c+dc].visited]
        if ns:
            nxt = random.choice(ns); stack.append(curr)
            remove_walls(curr, nxt); curr = nxt; curr.visited = True; yield curr
        elif stack: curr = stack.pop(); yield curr
        else: break

# --- Solvers ---

class MazeSolver:
    def __init__(self, grid, mode="BFS"):
        self.grid, self.mode = grid, mode
        self.container = deque([grid[0][0]]) if mode == "BFS" else [grid[0][0]]
        self.visited, self.parent, self.path, self.found = {grid[0][0]}, {}, [], False
        self.curr = grid[0][0]

    def step(self):
        if not self.container or self.found: return
        self.curr = self.container.popleft() if self.mode == "BFS" else self.container.pop()
        if self.curr == self.grid[ROWS-1][COLS-1]:
            self.found = True
            c = self.curr
            while c in self.parent: self.path.append(c); c = self.parent[c]
            return
        r, c = self.curr.r, self.curr.c
        for dr, dc, w in [(-1,0,'top'),(1,0,'bottom'),(0,-1,'left'),(0,1,'right')]:
            nr, nc = r+dr, c+dc
            if 0<=nr<ROWS and 0<=nc<COLS:
                n = self.grid[nr][nc]
                if not self.curr.walls[w] and n not in self.visited:
                    self.visited.add(n); self.parent[n] = self.curr
                    self.container.append(n)

def main():
    pygame.init()
    sc = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
    gen, solver = None, None
    
    print("GEN: 1-Binary | 2-Prims | 3-DFS")
    print("SOLVE: B-BFS | D-DFS | ESC-Reset")
    
    while True:
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT: return
            if e.type == pygame.KEYDOWN:
                if e.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_ESCAPE]:
                    grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
                    gen, solver = None, None
                if e.key == pygame.K_1: gen = binary_tree_gen(grid)
                if e.key == pygame.K_2: gen = prims_gen(grid)
                if e.key == pygame.K_3: gen = backtracker_gen(grid)
                if e.key == pygame.K_b and not gen: solver = MazeSolver(grid, "BFS")
                if e.key == pygame.K_d and not gen: solver = MazeSolver(grid, "DFS")

        if gen:
            try: [next(gen) for _ in range(20)]
            except StopIteration: gen = None
        if solver: solver.step()

        sc.fill((80, 80, 80))
        for row in grid: [cell.draw(sc) for cell in row]
        if solver:
            for n in solver.visited: pygame.draw.circle(sc, (150, 150, 255), (n.c*20+10, n.r*20+10), 3)
            for n in solver.path: pygame.draw.rect(sc, (255, 50, 50), (n.c*20+6, n.r*20+6, 8, 8))
            pygame.draw.rect(sc, (0, 255, 0), (solver.curr.c*20+4, solver.curr.r*20+4, 12, 12))
        pygame.display.flip()

if __name__ == "__main__": main()
