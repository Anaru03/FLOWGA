# Programa principal - Resuelve puzzles Flow con AG y Backtracking
from typing import Dict, List, Tuple

try:
    # Importaciones relativas (cuando se usa como paquete)
    from .backtracking_solver import solve_flow_bt
    from .config import Fore, Style
    from .genetic_algorithm import ga_solve_flow, is_perfect
    from .puzzle_generator import generate_random_puzzle
    from .utils import Color, Coord
    from .visualization import print_grid_color
except ImportError:
    # Importaciones absolutas (cuando se ejecuta directamente)
    from backtracking_solver import solve_flow_bt
    from config import Fore, Style
    from genetic_algorithm import ga_solve_flow, is_perfect
    from puzzle_generator import generate_random_puzzle
    from utils import Color, Coord
    from visualization import print_grid_color


def main():
    """Función principal del programa."""
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

if __name__ == "__main__":
    main()