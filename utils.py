# Tipos y utilidades básicas para el juego Flow
from collections import deque
from typing import Dict, List, Tuple

Coord = Tuple[int, int]
Color = str

def neighbors(N: int, r: int, c: int):
    """Genera las coordenadas de los vecinos válidos de una celda."""
    for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < N and 0 <= cc < N:
            yield rr, cc

def bfs_connected(grid: List[List[str]], color: Color, a: Coord, b: Coord) -> Tuple[bool, int]:
    """BFS sobre el color; retorna (conectados?, tamaño del componente que contiene 'a')."""
    N = len(grid)
    if grid[a[0]][a[1]] != color or grid[b[0]][b[1]] != color:
        return False, 0
    q = deque([a])
    vis = {a}
    size = 0
    while q:
        r, c = q.popleft()
        size += 1
        if (r, c) == b:
            return True, size
        for rr, cc in neighbors(N, r, c):
            if (rr, cc) not in vis and grid[rr][cc] == color:
                vis.add((rr, cc)); q.append((rr, cc))
    return False, size