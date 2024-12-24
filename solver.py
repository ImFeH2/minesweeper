import random
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class Action:
    x: int
    y: int
    is_flag: bool


@dataclass
class Clue:
    pos: Tuple[int, int]  # Position of the clue cell
    unknowns: List[Tuple[int, int]]  # List of unknown neighboring cells
    mines: int  # Number of mines in the unknown neighbors


class MineSolver:
    def __init__(self, mines: List[List[int]]):
        self.width = len(mines)
        self.height = len(mines[0]) if self.width > 0 else 0
        self.mines = mines
        self.actions: List[Action] = []  # Sequence of actions
        self.hints = [
            [sum(mines[nx][ny] for nx, ny in self.get_neighbors(x, y)) for y in range(self.height)]
            for x in range(self.width)]
        # Variable assignments: (x, y) -> 0 (safe) or 1 (mine)
        self.assignments: Dict[Tuple[int, int], int] = {}

    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get the coordinates of all neighboring cells."""
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    neighbors.append((nx, ny))
        return neighbors

    def get_unknown_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get neighboring cells that are still unknown."""
        return [(nx, ny) for nx, ny in self.get_neighbors(x, y) if (nx, ny) not in self.assignments]

    def get_clues(self) -> List[Clue]:
        """Build initial constraints based on the current known cells."""
        clues = []
        for x in range(self.width):
            for y in range(self.height):
                if (x, y) in self.assignments and self.assignments[(x, y)] == 0:
                    unknown_neighbors = self.get_unknown_neighbors(x, y)
                    if not unknown_neighbors: continue
                    mine_count = self.hints[x][y] - sum(1 for nx, ny in self.get_neighbors(x, y) if
                                                        self.assignments.get((nx, ny)) == 1)
                    clues.append(Clue((x, y), unknown_neighbors, mine_count))
        return clues

    def solve(self, start_x: int, start_y: int) -> List[Action]:
        """Solve the Minesweeper puzzle using a custom CDCL-inspired solver."""
        # Initialize by marking the starting cell as safe
        self.assignments[(start_x, start_y)] = 0  # 0 represents safe
        self.actions.append(Action(start_x, start_y, False))

        # Iteratively apply constraint propagation
        while self.propagate_constraints():
            pass

        return self.actions

    def propagate_constraints(self) -> bool:
        """Propagate constraints and deduce new safe cells or mines."""
        progress = False
        constraints = self.get_clues()

        for eq in constraints:
            unknowns = eq.unknowns
            mines_left = eq.mines

            # If no unknowns left, skip
            if not unknowns:
                continue

            # If the number of mines left equals the number of unknowns, all unknowns are mines
            if mines_left == len(unknowns):
                for pos in unknowns:
                    if self.assignments.get(pos) != 1:
                        self.assignments[pos] = 1
                        self.actions.append(Action(pos[0], pos[1], True))
                        progress = True
                continue

            # If no mines left, all unknowns are safe
            if mines_left == 0:
                for pos in unknowns:
                    if self.assignments.get(pos) != 0:
                        self.assignments[pos] = 0
                        self.actions.append(Action(pos[0], pos[1], False))
                        progress = True
                continue

            # Advanced inference: subset checking
            for other_eq in constraints:
                if other_eq is eq:
                    continue
                if set(other_eq.unknowns).issubset(set(eq.unknowns)):
                    subset = set(other_eq.unknowns)
                    superset = set(eq.unknowns)
                    difference = superset - subset
                    mine_difference = eq.mines - other_eq.mines

                    if mine_difference == len(difference):
                        for pos in difference:
                            if self.assignments.get(pos) != 1:
                                self.assignments[pos] = 1
                                self.actions.append(Action(pos[0], pos[1], True))
                                progress = True

                    elif mine_difference == 0:
                        for pos in difference:
                            if self.assignments.get(pos) != 0:
                                self.assignments[pos] = 0
                                self.actions.append(Action(pos[0], pos[1], False))
                                progress = True

        return progress

def generate_safe_mines(mines_count, width, height, first_x, first_y):
    def random_mines():
        mines = [[0] * height for _ in range(width)]
        # 不在第一次点击的周围生成雷, 有雷的地方标记为1，随机
        for _ in range(mines_count):
            x, y = random.randint(0, width - 1), random.randint(0, height - 1)
            if abs(x - first_x) <= 1 and abs(y - first_y) <= 1 or mines[x][y]:
                continue
            mines[x][y] = 1
        return mines

    while True:
        mines = random_mines()
        solver = MineSolver(mines)
        actions = solver.solve(first_x, first_y)
        if len(actions) == width * height:
            break

    return mines
