# Algoritmo Genético para resolver Flow
import statistics
from collections import deque
from random import choice, randint, random
from typing import Dict, List, Optional, Tuple

try:
    from .metrics import (GAMetrics, GenerationMetrics,
                          calculate_convergence_rate, calculate_diversity,
                          count_perfect_solutions)
    from .utils import Color, Coord, bfs_connected, neighbors
except ImportError:
    from metrics import (GAMetrics, GenerationMetrics,
                         calculate_convergence_rate, calculate_diversity,
                         count_perfect_solutions)
    from utils import Color, Coord, bfs_connected, neighbors


def build_fixed_mask(N: int, terminals: Dict[Color, Tuple[Coord, Coord]]) -> List[List[bool]]:
    """Crea una máscara de celdas fijas (terminales)."""
    fixed = [[False]*N for _ in range(N)]
    for col, (a, b) in terminals.items():
        fixed[a[0]][a[1]] = True
        fixed[b[0]][b[1]] = True
    return fixed

def color_list_from_terminals(terminals: Dict[Color, Tuple[Coord, Coord]]) -> List[Color]:
    """Obtiene lista ordenada de colores de los terminales."""
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
    """Verifica si la solución es perfecta (todos los terminales conectados Y cada color forma UN solo componente)."""
    N = len(grid)
    
    # 1. Verificar que cada par de terminales esté conectado
    for col, (a, b) in terminals.items():
        ok, _ = bfs_connected(grid, col, a, b)
        if not ok:
            return False
    
    # 2. CRÍTICO: Verificar que cada color forma EXACTAMENTE UN componente conexo
    #    (no puede haber "islas" de color desconectadas)
    for col in terminals.keys():
        visited = set()
        components = 0
        
        for r in range(N):
            for c in range(N):
                if grid[r][c] == col and (r, c) not in visited:
                    components += 1
                    if components > 1:
                        # Más de un componente detectado = solución inválida
                        return False
                    
                    # BFS para marcar todo el componente
                    from collections import deque
                    q = deque([(r, c)])
                    visited.add((r, c))
                    while q:
                        rr, cc = q.popleft()
                        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                            nr, nc = rr + dr, cc + dc
                            if 0 <= nr < N and 0 <= nc < N and grid[nr][nc] == col and (nr, nc) not in visited:
                                visited.add((nr, nc))
                                q.append((nr, nc))
    
    return True

def tournament_select(pop: List[List[List[str]]], fits: List[float], k: int = 3) -> int:
    """Selección por torneo."""
    best_i, best_f = None, -1e18
    n = len(pop)
    for _ in range(k):
        i = randint(0, n-1)
        if fits[i] > best_f:
            best_f = fits[i]; best_i = i
    return best_i

def crossover_uniform(p1: List[List[str]], p2: List[List[str]],
                      fixed: List[List[bool]]) -> List[List[str]]:
    """Cruce uniforme entre dos padres."""
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
    """Mutación: una celda toma el color de un vecino aleatorio."""
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
                  verbose: bool = True,
                  collect_metrics: bool = False) -> tuple[Optional[List[List[str]]], Optional[GAMetrics]]:
    """Resuelve Flow usando Algoritmo Genético con métricas opcionales."""
    
    # Inicializar métricas si se solicita
    metrics = None
    if collect_metrics:
        metrics = GAMetrics(
            pop_size=pop_size,
            generations=generations,
            mut_rate=mut_rate,
            elite_size=elite,
            tournament_k=tour_k,
            board_size=N,
            num_colors=len(terminals)
        )
        metrics.start_timing()
    
    fixed = build_fixed_mask(N, terminals)
    pop = [random_individual(N, terminals) for _ in range(pop_size)]

    best, best_fit = None, -1e18
    fitness_history = []
    
    # 🔥 DETECCIÓN DE ESTANCAMIENTO: Detener si no hay mejora en N generaciones
    # Esto es crítico para tableros grandes donde el GA puede quedarse atascado
    # 💡 AJUSTE: Para tableros grandes, ser más paciente antes de declarar estancamiento
    if N >= 10:
        stagnation_limit = max(generations // 2, 100)  # Más generoso para tableros grandes
    elif N >= 8:
        stagnation_limit = generations // 2  # 8×8 y 9×9: también necesitan paciencia
    else:
        stagnation_limit = min(200, generations // 3)  # Original para tableros pequeños
    
    generations_without_improvement = 0
    last_improvement_fitness = -1e18
    
    # 🔥 BARRA DE PROGRESO VISUAL
    if verbose:
        print(f"\n{'='*80}")
        print(f"🧬 INICIANDO EVOLUCIÓN GENÉTICA")
        print(f"{'='*80}")
        print(f"Población: {pop_size} | Generaciones máx: {generations}")
        print(f"Mutación: {mut_rate} | Elite: {elite} | Torneo: {tour_k}")
        print(f"{'='*80}\n")
    
    for gen in range(1, generations+1):
        fits = [fitness(ind, terminals) for ind in pop]
        
        # Contar evaluaciones de fitness
        if collect_metrics and metrics:
            metrics.total_fitness_evaluations += len(fits)
        
        i_best = max(range(pop_size), key=lambda i: fits[i])
        
        if fits[i_best] > best_fit:
            best_fit = fits[i_best]
            best = [row[:] for row in pop[i_best]]
            
            # 🔥 Resetear contador de estancamiento si hay mejora significativa
            if fits[i_best] > last_improvement_fitness + 10.0:  # Mejora significativa
                last_improvement_fitness = fits[i_best]
                generations_without_improvement = 0
            else:
                generations_without_improvement += 1
        else:
            generations_without_improvement += 1
        
        fitness_history.append(best_fit)
        
        # 🔥 DETECCIÓN TEMPRANA: Si estancado por mucho tiempo, detener
        if generations_without_improvement >= stagnation_limit:
            if verbose:
                print(f"\n{'='*80}")
                print(f"⚠️  ESTANCAMIENTO DETECTADO")
                print(f"{'='*80}")
                print(f"Generación: {gen}/{generations}")
                print(f"Generaciones sin mejora: {generations_without_improvement}/{stagnation_limit}")
                print(f"Fitness final: {best_fit:.2f}")
                print(f"{'='*80}")
            break
        
        # Calcular métricas de esta generación
        if collect_metrics and metrics:
            diversity = calculate_diversity(pop, N)
            convergence = calculate_convergence_rate(fitness_history)
            perfect_count = count_perfect_solutions(pop, terminals)
            
            gen_metric = GenerationMetrics(
                generation=gen,
                best_fitness=best_fit,
                avg_fitness=sum(fits) / len(fits),
                worst_fitness=min(fits),
                std_fitness=statistics.stdev(fits) if len(fits) > 1 else 0.0,
                diversity_score=diversity,
                convergence_rate=convergence,
                perfect_solutions=perfect_count
            )
            metrics.add_generation_metric(gen_metric)
        
        # 🔥 REPORTE DE PROGRESO MEJORADO
        if verbose and gen % 50 == 0:
            progress_pct = (gen / generations) * 100
            bar_length = 40
            filled_length = int(bar_length * gen / generations)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            
            print(f"\r[{bar}] {progress_pct:5.1f}% | Gen {gen:4d}/{generations} | "
                  f"Fitness: {best_fit:8.2f} | ", end='')
            
            if collect_metrics and metrics:
                last_metric = metrics.generation_metrics[-1]
                print(f"Div: {last_metric.diversity_score:.3f} | "
                      f"Perfect: {last_metric.perfect_solutions:2d} | "
                      f"Sin mejora: {generations_without_improvement:3d}", end='')
            else:
                print(f"Sin mejora: {generations_without_improvement:3d}", end='')
            
            # Añadir salto de línea cada 10 reportes para no saturar
            if gen % 500 == 0:
                print()  # Nueva línea
        
        if is_perfect(best, terminals):
            if verbose:
                print(f"\n\n{'='*80}")
                print(f"✅ ¡SOLUCIÓN PERFECTA ENCONTRADA!")
                print(f"{'='*80}")
                print(f"Generación: {gen}/{generations}")
                print(f"Fitness final: {best_fit:.2f}")
                print(f"{'='*80}\n")
            if collect_metrics and metrics:
                metrics.generations_to_solution = gen
            break

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
    
    # Finalizar métricas
    if collect_metrics and metrics:
        solution_found = best is not None and is_perfect(best, terminals)
        metrics.finalize_metrics(solution_found, best_fit)
    
    if collect_metrics:
        return best, metrics
    else:
        return best, None