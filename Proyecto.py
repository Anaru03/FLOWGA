# Genera puzzles aleatorios de Flow (N x N), los imprime en color y los resuelve
# con Algoritmo Genético (GA) o Backtracking.
#
# - Terminales de cada color: letras ("B","R","Y","G","O","C"...).
# - Modo por defecto: GA -> si no resuelve perfecto -> Backtracking.
#
# Requisitos:
#   pip install colorama   (opcional; sin él, imprime sin color)

from typing import Dict, Tuple, List, Optional
from random import random, randint, choice, shuffle
from collections import deque
import argparse

# colorama opcional 
try:
    from colorama import init as colorama_init, Fore, Back, Style
    colorama_init()
    COLOR_ENABLED = True
except Exception:
    class Dummy:
        def __getattr__(self, k): return ""
    Fore = Back = Style = Dummy()
    COLOR_ENABLED = False

Coord = Tuple[int, int]
Color = str

# ====== paleta de colores (añade los que quieras) ======
BACK = {"B": Back.BLUE, "R": Back.RED, "Y": Back.YELLOW, "G": Back.GREEN,
    "O": Back.MAGENTA, "C": Back.CYAN}
# Añadir algunos alias/colores extras (si colorama está presente se usarán)
BACK.update({"P": getattr(Back, 'LIGHTMAGENTA_EX', Back.MAGENTA),
         "W": getattr(Back, 'WHITE', Back.RESET),
         "K": getattr(Back, 'BLACK', Back.RESET),
         "M": getattr(Back, 'LIGHTCYAN_EX', Back.CYAN)})

FORE = {"B": Fore.BLUE, "R": Fore.RED, "Y": Fore.YELLOW, "G": Fore.GREEN,
    "O": Fore.MAGENTA, "C": Fore.CYAN}
FORE.update({"P": getattr(Fore, 'LIGHTMAGENTA_EX', Fore.MAGENTA),
         "W": getattr(Fore, 'WHITE', Fore.RESET),
         "K": getattr(Fore, 'BLACK', Fore.RESET),
         "M": getattr(Fore, 'LIGHTCYAN_EX', Fore.CYAN)})

# Parametrización del fitness (valores por defecto que pueden overridearse por CLI)
FIT_PARAMS = {
    'multi_comp_penalty': 500.0,
    'connect_reward': 3000.0,
    'excess_penalty': 5.0,
    'not_connected_base': 800.0,
    'not_connected_manh_penalty': 60.0,
    'smooth_weight': 0.2,
    'compact_bonus_scale': 2.0,  # se multiplica contra comp_size en el bonus
}


#
# Utilidades de impresión (robusto a celdas '.')
#
def print_grid_color(grid: List[List[str]],
                     terminals: Dict[Color, Tuple[Coord, Coord]],
                     title: str = ""):
    if title:
        print(Style.BRIGHT + title + Style.RESET_ALL)

    N = len(grid)
    endpoints = set()
    for col, (a, b) in terminals.items():
        endpoints.add(a); endpoints.add(b)

    print(Style.DIM + "┌" + "──"*N + "┐" + Style.RESET_ALL)
    for r in range(N):
        row = [Style.DIM + "│" + Style.RESET_ALL]
        for c in range(N):
            ch = grid[r][c]
            pos = (r, c)
            # Si es un endpoint, dibujar el punto sobre el fondo del mismo color
            if pos in endpoints and ch in FORE:
                if COLOR_ENABLED:
                    if ch in BACK:
                        row.append(BACK[ch] + FORE[ch] + Style.BRIGHT + "● " + Style.RESET_ALL)
                    else:
                        row.append(FORE[ch] + Style.BRIGHT + "● " + Style.RESET_ALL)
                else:
                    # Sin color: mostrar letra del terminal para identificarlo
                    row.append(Style.BRIGHT + ch + " " + Style.RESET_ALL)
            else:
                if ch in BACK:
                    if COLOR_ENABLED:
                        row.append(BACK[ch] + "  " + Style.RESET_ALL)
                    else:
                        # Sin color: mostrar la letra del color en la celda
                        row.append(ch + " ")
                else:
                    row.append(Style.DIM + "· " + Style.RESET_ALL)  # celda vacía
        row.append(Style.DIM + "│" + Style.RESET_ALL)
        print("".join(row))
    print(Style.DIM + "└" + "──"*N + "┘" + Style.RESET_ALL)
    print()


# Motor/Utilidades Flow

def neighbors(N: int, r: int, c: int):
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



# Solver Backtracking 

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


 
# Algoritmo Genético (Selección, Cruce, Mutación)

def build_fixed_mask(N: int, terminals: Dict[Color, Tuple[Coord, Coord]]) -> List[List[bool]]:
    fixed = [[False]*N for _ in range(N)]
    for col, (a, b) in terminals.items():
        fixed[a[0]][a[1]] = True
        fixed[b[0]][b[1]] = True
    return fixed

def color_list_from_terminals(terminals: Dict[Color, Tuple[Coord, Coord]]) -> List[Color]:
    cols = list(terminals.keys())
    cols.sort()
    return cols

def random_individual(N: int, terminals: Dict[Color, Tuple[Coord, Coord]]) -> List[List[str]]:
    """Inicialización tipo Voronoi Manhattan (cada celda toma color del terminal más cercano)."""
    grid = [["" for _ in range(N)] for _ in range(N)]
    for col, (a, b) in terminals.items():
        grid[a[0]][a[1]] = col
        grid[b[0]][b[1]] = col
    for r in range(N):
        for c in range(N):
            if grid[r][c] != "":
                continue
            best_col, best_d = None, 10**9
            for col, (a, b) in terminals.items():
                d = min(abs(r-a[0]) + abs(c-a[1]), abs(r-b[0]) + abs(c-b[1]))
                if d < best_d:
                    best_d = d; best_col = col
            grid[r][c] = best_col
    return grid

def fitness(grid: List[List[str]], terminals: Dict[Color, Tuple[Coord, Coord]]) -> float:
    """Versión reforzada de fitness:
    - Gran recompensa por conectar ambos terminales de un color.
    - Penaliza múltiples componentes del mismo color (discontinuidades).
    - Penaliza no estar conectado según distancia Manhattan.
    - Penaliza componentes demasiado grandes (overfilling).
    - Añade término de suavidad (vecinos del mismo color).
    """
    score = 0.0
    N = len(grid)

    # Helper: obtener todos los componentes de un color
    def components_of_color(col: Color):
        vis = set()
        comps = []  # lista de sets
        for r in range(N):
            for c in range(N):
                if (r, c) in vis:
                    continue
                if grid[r][c] != col:
                    continue
                # BFS/DFS para componente
                q = deque([(r, c)])
                comp = set([(r, c)])
                vis.add((r, c))
                while q:
                    rr, cc = q.popleft()
                    for nr, nc in neighbors(N, rr, cc):
                        if (nr, nc) not in vis and grid[nr][nc] == col:
                            vis.add((nr, nc))
                            comp.add((nr, nc))
                            q.append((nr, nc))
                comps.append(comp)
        return comps

    for col, (a, b) in terminals.items():
        comps = components_of_color(col)
        # penalizar número de componentes (ideal: 1)
        if len(comps) > 1:
            score -= 500.0 * (len(comps) - 1)

        # comprobar si a y b están en la misma componente
        in_same = False
        comp_size = 0
        for comp in comps:
            if a in comp:
                comp_size = len(comp)
                if b in comp:
                    in_same = True
                break

        if in_same:
            # recompensa fuerte por conectar, penaliza compacidad grande
            score += 3000.0
            # componente preferiblemente cercana a la distancia manhattan
            manh = abs(a[0]-b[0]) + abs(a[1]-b[1])
            # si el tamaño es mucho mayor que la distancia, penalizar
            excess = max(0, comp_size - (manh + 2))
            score -= 5.0 * excess
            # pequeña bonificación por ser compacto
            score += max(0.0, 200.0 - 2.0 * comp_size)
        else:
            # no conectados -> penalizar según Manhattan y tamaño de la mayor componente
            manh = abs(a[0]-b[0]) + abs(a[1]-b[1])
            score -= 800.0 + 60.0 * manh
            if comps:
                # si hay una gran componente, penalizar (ocupa espacio)
                max_comp = max(len(c) for c in comps)
                score -= 2.0 * max_comp

    # suavidad (vecinos del mismo color)
    smooth = 0
    for r in range(N):
        for c in range(N):
            for rr, cc in neighbors(N, r, c):
                if grid[r][c] == grid[rr][cc]:
                    smooth += 1
    score += 0.2 * smooth
    return score

def is_perfect(grid: List[List[str]], terminals: Dict[Color, Tuple[Coord, Coord]]) -> bool:
    for col, (a, b) in terminals.items():
        ok, _ = bfs_connected(grid, col, a, b)
        if not ok:
            return False
    return True

def tournament_select(pop: List[List[List[str]]], fits: List[float], k: int = 3) -> int:
    best_i, best_f = None, -1e18
    n = len(pop)
    for _ in range(k):
        i = randint(0, n-1)
        if fits[i] > best_f:
            best_f = fits[i]; best_i = i
    return best_i

def crossover_uniform(p1: List[List[str]], p2: List[List[str]],
                      fixed: List[List[bool]]) -> List[List[str]]:
    N = len(p1)
    child = [[p1[r][c] for c in range(N)] for r in range(N)]
    for r in range(N):
        for c in range(N):
            if fixed[r][c]:
                continue
            child[r][c] = p1[r][c] if random() < 0.5 else p2[r][c]
    return child

def mutate_neighbor_color(ind: List[List[str]],
                          fixed: List[List[bool]],
                          mut_rate: float = 0.02):
    N = len(ind)
    for r in range(N):
        for c in range(N):
            if fixed[r][c]:
                continue
            if random() < mut_rate:
                rr, cc = choice(list(neighbors(N, r, c)))
                ind[r][c] = ind[rr][cc]

def ga_solve_flow(N: int,
                  terminals: Dict[Color, Tuple[Coord, Coord]],
                  pop_size: int = 200,
                  generations: int = 1500,
                  mut_rate: float = 0.03,
                  elite: int = 3,
                  tour_k: int = 3,
                  verbose: bool = True) -> Optional[List[List[str]]]:

    fixed = build_fixed_mask(N, terminals)
    pop = [random_individual(N, terminals) for _ in range(pop_size)]

    best, best_fit = None, -1e18
    for gen in range(1, generations+1):
        fits = [fitness(ind, terminals) for ind in pop]
        i_best = max(range(pop_size), key=lambda i: fits[i])
        if fits[i_best] > best_fit:
            best_fit = fits[i_best]; best = [row[:] for row in pop[i_best]]
        if verbose and gen % 50 == 0:
            print(f"[GA] Gen {gen:4d} | best fitness = {best_fit:.2f}")
        if is_perfect(best, terminals):
            if verbose:
                print(f"[GA] Solución perfecta en gen {gen}.")
            return best

        # Nueva población con elitismo
        new_pop: List[List[List[str]]] = []
        elite_idx = sorted(range(pop_size), key=lambda i: -fits[i])[:elite]
        for i in elite_idx:
            new_pop.append([row[:] for row in pop[i]])
        while len(new_pop) < pop_size:
            i1 = tournament_select(pop, fits, tour_k)
            i2 = tournament_select(pop, fits, tour_k)
            child = crossover_uniform(pop[i1], pop[i2], fixed)
            mutate_neighbor_color(child, fixed, mut_rate)
            new_pop.append(child)
        pop = new_pop

    return best  # tal vez no perfecto


# =========================================================
# Generador de puzzles aleatorios (siempre resolubles)
# =========================================================
def serpentine_path(N: int) -> List[Coord]:
    path = []
    for r in range(N):
        cols = range(N) if r % 2 == 0 else range(N-1, -1, -1)
        for c in cols:
            path.append((r, c))
    return path

def random_splits(total: int, k: int, min_len: int = 2) -> List[int]:
    cuts = []
    start = 0
    for j in range(k - 1):
        lo = start + min_len
        hi = total - (k - j - 1) * min_len
        cut = randint(lo, hi - 1)
        cuts.append(cut)
        start = cut
    return cuts

def rotate_coord(N: int, rc: Coord, k: int) -> Coord:
    r, c = rc
    for _ in range(k % 4):
        r, c = c, N - 1 - r
    return r, c

def flip_coord(N: int, rc: Coord, horizontal: bool) -> Coord:
    r, c = rc
    return (r, N - 1 - c) if horizontal else (N - 1 - r, c)

def generate_random_puzzle(N: int = 5, n_colors: int = 4,
                           palette: List[Color] = None) -> Dict[Color, Tuple[Coord, Coord]]:
    """Crea una solución “snake”, la divide en segmentos y usa extremos como terminales."""
    if palette is None:
        palette = ["B", "R", "Y", "G", "O", "C"]
    colors = palette[:]
    shuffle(colors)
    colors = colors[:n_colors]

    path = serpentine_path(N)
    cuts = random_splits(len(path), n_colors, min_len=max(2, N//2))
    segments = []
    prev = 0
    for cut in cuts + [len(path)]:
        segments.append(path[prev:cut])
        prev = cut
    shuffle(colors)

    terminals: Dict[Color, Tuple[Coord, Coord]] = {}
    for col, seg in zip(colors, segments):
        terminals[col] = (seg[0], seg[-1])

    # aleatorizar orientación
    rot_k = randint(0, 3)
    hflip = choice([False, True])
    new_terms = {}
    for col, (a, b) in terminals.items():
        aa = rotate_coord(N, a, rot_k)
        bb = rotate_coord(N, b, rot_k)
        if hflip:
            aa = flip_coord(N, aa, True)
            bb = flip_coord(N, bb, True)
        new_terms[col] = (aa, bb)

    # verificación rápida: backtracking debe poder resolver
    if solve_flow_bt(N, new_terms) is None:
        return generate_random_puzzle(N, n_colors, palette)
    return new_terms


# =========================================================
# DEMO / MAIN
# =========================================================
if __name__ == "__main__":
    # ---- Parámetros del tablero ----
    N = 5           # tamaño del tablero (p. ej., 5, 6, 7)
    n_colors = 4    # número de colores

    # ---- Generar puzzle aleatorio ----
    terminals = generate_random_puzzle(N=N, n_colors=n_colors)

    # Construir el tablero con sólo terminales para mostrar
    puzzle = [["." for _ in range(N)] for _ in range(N)]
    for col, (a, b) in terminals.items():
        puzzle[a[0]][a[1]] = col
        puzzle[b[0]][b[1]] = col

    print_grid_color(puzzle, terminals, "Terminales (puzzle aleatorio):")

    #Resolver: primero GA (rápido/heurístico), si no, Backtracking (fiable) 
    solver_mode = "GA_THEN_BT"   # "GA", "BT" o "GA_THEN_BT"

    solution = None

    if solver_mode in ("GA", "GA_THEN_BT"):
        sol_ga = ga_solve_flow(N, terminals,
                               pop_size=220,
                               generations=2000,
                               mut_rate=0.03,
                               elite=4,
                               tour_k=4,
                               verbose=True)
        if sol_ga and is_perfect(sol_ga, terminals):
            solution = sol_ga
            print_grid_color(solution, terminals, "¡Solución (GA)!")
        elif solver_mode == "GA":
            print(Style.BRIGHT + Fore.YELLOW + "GA no llegó a solución perfecta; mostrando mejor individuo." + Style.RESET_ALL)
            if sol_ga:
                print_grid_color(sol_ga, terminals, "Mejor individuo (GA):")

    if solution is None and solver_mode in ("BT", "GA_THEN_BT"):
        # Si hay una solución del GA, úsala como punto de partida para el Backtracking
        if 'sol_ga' in locals() and sol_ga is not None:
            sol_bt = solve_flow_bt(N, terminals, start_grid=sol_ga)
        else:
            sol_bt = solve_flow_bt(N, terminals)
        if sol_bt:
            solution = sol_bt
            print_grid_color(solution, terminals, "¡Solución (Backtracking)!")
        else:
            print(Style.BRIGHT + Fore.RED + "Backtracking no encontró solución (no debería ocurrir con este generador)." + Style.RESET_ALL)
