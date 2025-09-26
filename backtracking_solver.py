# Solver usando Backtracking para el juego Flow
from typing import Dict, List, Optional, Tuple

try:
    from .utils import Color, Coord, neighbors
except ImportError:
    from utils import Color, Coord, neighbors


def solve_flow_bt(N: int, terminals: Dict[Color, Tuple[Coord, Coord]], start_grid: Optional[List[List[str]]] = None) -> Optional[List[List[str]]]:
    """Backtracking que puede arrancar desde `start_grid` si se proporciona.
    Las celdas en `start_grid` que ya tienen el mismo color pueden ser reutilizadas
    por el generador de caminos (útil para reparar la salida del GA)."""
    grid = [["." for _ in range(N)] for _ in range(N)]
    if start_grid is not None:
        # copiar start_grid (no confiamos en su exactitud, pero lo usamos como ayuda)
        for r in range(N):
            for c in range(N):
                if start_grid[r][c] != ".":
                    grid[r][c] = start_grid[r][c]
    for col, (a, b) in terminals.items():
        grid[a[0]][a[1]] = col
        grid[b[0]][b[1]] = col

    def manhattan(a: Coord, b: Coord) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    order = sorted(terminals.keys(), key=lambda col: manhattan(*terminals[col]))

    def backtrack(i: int) -> bool:
        if i == len(order):
            return all(cell != "." for row in grid for cell in row)

        col = order[i]
        s, t = terminals[col]

        def gen_paths():
            stack = [(s, [s], {s})]
            while stack:
                cur, path, vis = stack.pop()
                if cur == t:
                    yield path
                    continue
                r, c = cur
                neighs = sorted(neighbors(N, r, c), key=lambda xy: manhattan(xy, t))
                for nr, nc in neighs:
                    if (nr, nc) in vis:
                        continue
                    v = grid[nr][nc]
                    # permitir reutilizar celdas ya pintadas del mismo color
                    if v != "." and v != col and (nr, nc) != t:
                        continue
                    vis2 = set(vis); vis2.add((nr, nc))
                    stack.append(((nr, nc), path + [(nr, nc)], vis2))

        for path in gen_paths():
            painted = []
            for r, c in path[1:]:
                prev = grid[r][c]
                grid[r][c] = col
                painted.append((r, c, prev))
            if backtrack(i + 1):
                return True
            for r, c, prev in painted:
                grid[r][c] = prev
        return False

    return grid if backtrack(0) else None