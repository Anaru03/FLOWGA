# Módulo de visualización para el juego Flow
from typing import Dict, List, Tuple

try:
    from .config import BACK, COLOR_ENABLED, FORE, Style
    from .utils import Color, Coord
except ImportError:
    from config import BACK, COLOR_ENABLED, FORE, Style
    from utils import Color, Coord


def print_grid_color(grid: List[List[str]],
                     terminals: Dict[Color, Tuple[Coord, Coord]],
                     title: str = ""):
    """Imprime el grid del juego Flow con colores y formato."""
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