# Generador de puzzles aleatorios para Flow
from random import choice, randint, shuffle
from typing import Dict, List, Tuple

try:
    from .backtracking_solver import solve_flow_bt
    from .utils import Color, Coord
except ImportError:
    from backtracking_solver import solve_flow_bt
    from utils import Color, Coord


def serpentine_path(N: int) -> List[Coord]:
    """Genera un camino serpenteante que recorre todo el tablero."""
    path = []
    for r in range(N):
        cols = range(N) if r % 2 == 0 else range(N-1, -1, -1)
        for c in cols:
            path.append((r, c))
    return path

def random_splits(total: int, k: int, min_len: int = 2) -> List[int]:
    """Divide un total en k segmentos aleatorios con longitud mínima."""
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
    """Rota una coordenada k veces en sentido horario."""
    r, c = rc
    for _ in range(k % 4):
        r, c = c, N - 1 - r
    return r, c

def flip_coord(N: int, rc: Coord, horizontal: bool) -> Coord:
    """Refleja una coordenada horizontal o verticalmente."""
    r, c = rc
    return (r, N - 1 - c) if horizontal else (N - 1 - r, c)

def generate_random_puzzle(N: int = 5, n_colors: int = 4,
                           palette: List[Color] = None) -> Dict[Color, Tuple[Coord, Coord]]:
    """Crea una solución "snake", la divide en segmentos y usa extremos como terminales."""
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