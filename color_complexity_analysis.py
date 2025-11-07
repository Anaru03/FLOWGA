"""
Análisis de complejidad basado en el número de colores.
Explora el espacio (tamaño_tablero × num_colores) para identificar límites de resolubilidad.
"""
import csv
import json
import os
import statistics
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np

try:
    from .backtracking_solver import solve_flow_bt
    from .config import Fore, Style
    from .genetic_algorithm import ga_solve_flow, is_perfect
    from .metrics import GAMetrics
    from .puzzle_generator import generate_random_puzzle
    from .utils import Color, Coord
except ImportError:
    from backtracking_solver import solve_flow_bt
    from config import Fore, Style
    from genetic_algorithm import ga_solve_flow, is_perfect
    from metrics import GAMetrics
    from puzzle_generator import generate_random_puzzle
    from utils import Color, Coord


@dataclass
class ColorComplexityResult:
    """Resultado de un experimento (board_size × num_colors)."""
    board_size: int
    num_colors: int
    density: float  # num_colors / (board_size * board_size)
    run_id: int
    
    # Resultados GA
    ga_success: bool
    ga_time: float
    ga_generations: int
    ga_fitness_evals: int
    ga_generations_to_solution: Optional[int]
    final_fitness: float
    
    # Resultados BT
    bt_used: bool
    bt_time: float
    bt_success: bool
    
    # Totales
    total_time: float
    solved: bool


@dataclass
class ColorComplexitySummary:
    """Resumen estadístico para una configuración (board_size × num_colors)."""
    board_size: int
    num_colors: int
    density: float
    total_runs: int
    
    # Tasa de éxito
    ga_success_rate: float
    bt_success_rate: float
    total_success_rate: float
    
    # Tiempos promedio
    avg_ga_time: float
    avg_bt_time: float
    avg_total_time: float
    
    # Fitness
    avg_fitness: float
    avg_fitness_evals: int
    
    # Generaciones
    avg_generations: int
    avg_generations_to_solution: Optional[float]
    
    # Resolubilidad
    is_solvable: bool  # True si success_rate >= umbral
    difficulty_score: float  # Métrica compuesta de dificultad
    
    def __str__(self):
        return (f"[{self.board_size}×{self.board_size}, {self.num_colors} colores] "
                f"Éxito: {self.total_success_rate:.1%}, "
                f"Tiempo: {self.avg_total_time:.3f}s, "
                f"Dificultad: {self.difficulty_score:.2f}")


@dataclass
class SolvabilityThreshold:
    """Umbral de resolubilidad detectado."""
    board_size: int
    max_solvable_colors: int
    max_density: float
    success_rate_at_threshold: float
    avg_time_at_threshold: float
    reason: str  # Por qué se considera umbral


def run_color_experiment(
    board_size: int,
    num_colors: int,
    run_id: int = 0,
    pop_size: int = 200,
    generations: int = 1000,
    mut_rate: float = 0.03,
    elite: int = 2,
    tour_k: int = 3,
    verbose: bool = False,
    max_time: float = None
) -> ColorComplexityResult:
    """
    Ejecuta un experimento individual con un tablero específico.
    
    Args:
        board_size: Tamaño del tablero (N×N)
        num_colors: Número de colores/flujos
        run_id: ID de la corrida (para múltiples repeticiones)
        pop_size, generations, mut_rate, elite, tour_k: Parámetros del GA
        verbose: Si True, imprime información detallada
        max_time: Tiempo máximo en segundos (None = calculado automáticamente)
    
    Returns:
        ColorComplexityResult con métricas del experimento
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"Experimento: {board_size}×{board_size}, {num_colors} colores, Run #{run_id}")
        print(f"{'='*60}")
    
    # Validar configuración antes de generar puzzle
    total_cells = board_size * board_size
    min_segment_length = max(2, board_size // 2)
    max_possible_colors = total_cells // min_segment_length
    
    if num_colors > max_possible_colors:
        if verbose:
            print(f"{Fore.RED}✗ CONFIGURACIÓN INVÁLIDA: {num_colors} colores excede el máximo de {max_possible_colors} para tablero {board_size}×{board_size}{Style.RESET_ALL}")
        
        # Retornar resultado de fallo inmediato
        density = num_colors / total_cells
        return ColorComplexityResult(
            board_size=board_size,
            num_colors=num_colors,
            density=density,
            run_id=run_id,
            ga_success=False,
            ga_time=0.0,
            ga_generations=0,
            ga_fitness_evals=0,
            ga_generations_to_solution=None,
            final_fitness=0.0,
            bt_used=False,
            bt_time=0.0,
            bt_success=False,
            total_time=0.0,
            solved=False
        )
    
    # Generar puzzle
    try:
        terminals = generate_random_puzzle(board_size, num_colors)
    except (ValueError, Exception) as e:
        if verbose:
            print(f"{Fore.RED}✗ Error al generar puzzle: {e}{Style.RESET_ALL}")
        
        density = num_colors / total_cells
        return ColorComplexityResult(
            board_size=board_size,
            num_colors=num_colors,
            density=density,
            run_id=run_id,
            ga_success=False,
            ga_time=0.0,
            ga_generations=0,
            ga_fitness_evals=0,
            ga_generations_to_solution=None,
            final_fitness=0.0,
            bt_used=False,
            bt_time=0.0,
            bt_success=False,
            total_time=0.0,
            solved=False
        )
    
    density = num_colors / (board_size * board_size)
    
    # Calcular timeout y generaciones adaptativas basado en complejidad
    if max_time is None:
        # Heurística: tiempo base * factor de escala exponencial
        # Base: 5s para problemas pequeños
        # Escala: crece exponencialmente con tamaño y densidad
        complexity_factor = (board_size ** 2) * (density ** 2)
        max_time = min(120.0, 5.0 * (1 + complexity_factor / 10))
        
        if verbose:
            print(f"{Fore.CYAN}⏱ Timeout adaptativo: {max_time:.1f}s (complejidad={complexity_factor:.2f}){Style.RESET_ALL}")
    
    # Ajustar generaciones basado en complejidad
    # Para problemas más complejos, usamos menos generaciones pero con early stopping
    adaptive_generations = generations
    
    # Estrategia escalonada basada en tamaño de tablero
    if board_size >= 10:
        # 10×10 o mayor: Prácticamente intratable con GA
        adaptive_generations = 50
        if verbose:
            print(f"{Fore.RED}⚠️ Tablero {board_size}×{board_size} es EXTREMADAMENTE grande")
            print(f"   Generaciones reducidas a {adaptive_generations} (exploración mínima){Style.RESET_ALL}")
    elif board_size >= 9:
        # 9×9: Muy difícil, exploración superficial
        adaptive_generations = 100
        if verbose:
            print(f"{Fore.YELLOW}⚠️ Tablero {board_size}×{board_size} cerca del límite práctico")
            print(f"   Generaciones reducidas a {adaptive_generations}{Style.RESET_ALL}")
    elif board_size >= 8:
        # 8×8: Difícil, reducción significativa
        adaptive_generations = 200
        if verbose:
            print(f"{Fore.YELLOW}📉 Tablero {board_size}×{board_size} requiere reducción")
            print(f"   Generaciones reducidas a {adaptive_generations}{Style.RESET_ALL}")
    elif board_size >= 7 or density > 0.35:
        # 7×7 o densidad alta: Reducción moderada
        adaptive_generations = min(500, generations)
        if verbose:
            print(f"{Fore.CYAN}📉 Generaciones reducidas a {adaptive_generations} para problema complejo{Style.RESET_ALL}")
    
    # Ejecutar GA con timeout
    start_time = time.time()
    timeout_reached = False
    
    solution_ga, metrics_dict = ga_solve_flow(
        board_size,
        terminals,
        pop_size=pop_size,
        generations=adaptive_generations,
        mut_rate=mut_rate,
        elite=elite,
        tour_k=tour_k,
        verbose=False,
        collect_metrics=True
    )
    
    ga_time = time.time() - start_time
    
    # Verificar si excedimos el timeout
    if ga_time > max_time:
        timeout_reached = True
        if verbose:
            print(f"{Fore.YELLOW}⚠ Timeout alcanzado: {ga_time:.1f}s > {max_time:.1f}s{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}   El problema puede ser computacionalmente intratable{Style.RESET_ALL}")
    
    ga_success = solution_ga is not None and is_perfect(solution_ga, terminals)
    
    # Extraer métricas GA
    summary = metrics_dict.get_summary()
    perf = summary['rendimiento']
    
    final_fitness = summary['fitness']['fitness_final']
    ga_generations = perf['generaciones_ejecutadas']
    ga_fitness_evals = perf['evaluaciones_fitness']
    ga_generations_to_solution = perf['generaciones_hasta_solucion']
    
    # Intentar backtracking si GA falló
    bt_used = False
    bt_time = 0.0
    bt_success = False
    solved = ga_success
    
    if not ga_success:
        if verbose:
            print(f"{Fore.YELLOW}GA no encontró solución. Intentando backtracking...{Style.RESET_ALL}")
        
        bt_start = time.time()
        solution_bt = solve_flow_bt(board_size, terminals, start_grid=solution_ga)
        bt_time = time.time() - bt_start
        bt_used = True
        
        if solution_bt is not None and is_perfect(solution_bt, terminals):
            bt_success = True
            solved = True
            if verbose:
                print(f"{Fore.GREEN}✓ Backtracking encontró solución{Style.RESET_ALL}")
        else:
            if verbose:
                print(f"{Fore.RED}✗ Backtracking también falló{Style.RESET_ALL}")
    
    total_time = ga_time + bt_time
    
    if verbose:
        print(f"\n{'Resultados':^60}")
        print(f"{'-'*60}")
        print(f"  GA Success:    {ga_success}")
        print(f"  GA Time:       {ga_time:.3f}s")
        print(f"  BT Used:       {bt_used}")
        print(f"  BT Time:       {bt_time:.3f}s")
        print(f"  Total Time:    {total_time:.3f}s")
        print(f"  Solved:        {solved}")
        print(f"  Density:       {density:.3f}")
        print(f"{'='*60}\n")
    
    return ColorComplexityResult(
        board_size=board_size,
        num_colors=num_colors,
        density=density,
        run_id=run_id,
        ga_success=ga_success,
        ga_time=ga_time,
        ga_generations=ga_generations,
        ga_fitness_evals=ga_fitness_evals,
        ga_generations_to_solution=ga_generations_to_solution,
        final_fitness=final_fitness,
        bt_used=bt_used,
        bt_time=bt_time,
        bt_success=bt_success,
        total_time=total_time,
        solved=solved
    )


def run_color_complexity_study(
    board_sizes: List[int],
    color_ranges: Dict[int, List[int]],
    runs_per_config: int = 10,
    pop_size: int = 200,
    generations: int = 1000,
    mut_rate: float = 0.03,
    elite: int = 2,
    tour_k: int = 3,
    verbose: bool = True
) -> List[ColorComplexityResult]:
    """
    Ejecuta un estudio completo de complejidad por colores.
    
    Args:
        board_sizes: Lista de tamaños de tablero [4, 5, 6, ...]
        color_ranges: Dict {board_size: [list of num_colors]}
                      Ej: {4: [3, 4, 5, 6], 5: [4, 5, 6, 7, 8]}
        runs_per_config: Número de corridas por configuración
        pop_size, generations, mut_rate, elite, tour_k: Parámetros del GA
        verbose: Si True, muestra progreso
    
    Returns:
        Lista de ColorComplexityResult con todos los experimentos
    """
    results = []
    total_configs = sum(len(color_ranges.get(bs, [])) for bs in board_sizes)
    total_experiments = total_configs * runs_per_config
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"{'ESTUDIO DE COMPLEJIDAD POR NÚMERO DE COLORES':^70}")
        print(f"{'='*70}")
        print(f"  Tamaños de tablero: {board_sizes}")
        print(f"  Configuraciones totales: {total_configs}")
        print(f"  Corridas por configuración: {runs_per_config}")
        print(f"  Total de experimentos: {total_experiments}")
        print(f"{'='*70}\n")
    
    experiment_count = 0
    
    for board_size in board_sizes:
        colors_list = color_ranges.get(board_size, [])
        
        if not colors_list:
            if verbose:
                print(f"{Fore.YELLOW}⚠ Sin colores definidos para tablero {board_size}×{board_size}{Style.RESET_ALL}")
            continue
        
        if verbose:
            print(f"\n{Fore.CYAN}{'─'*70}")
            print(f"Tablero {board_size}×{board_size}: Probando {len(colors_list)} cantidades de colores")
            print(f"{'─'*70}{Style.RESET_ALL}")
        
        for num_colors in colors_list:
            density = num_colors / (board_size * board_size)
            
            if verbose:
                print(f"\n  {Fore.BLUE}[{board_size}×{board_size}, {num_colors} colores, densidad={density:.3f}]{Style.RESET_ALL}")
            
            # Variables para detectar problemas intratables
            consecutive_timeouts = 0
            timeout_threshold = 3  # Si 3 runs consecutivos exceden timeout, saltar resto
            
            for run_id in range(runs_per_config):
                experiment_count += 1
                
                if verbose:
                    print(f"    Run {run_id+1}/{runs_per_config} ", end="", flush=True)
                
                result = run_color_experiment(
                    board_size=board_size,
                    num_colors=num_colors,
                    run_id=run_id,
                    pop_size=pop_size,
                    generations=generations,
                    mut_rate=mut_rate,
                    elite=elite,
                    tour_k=tour_k,
                    verbose=False
                )
                
                results.append(result)
                
                if verbose:
                    status = f"{Fore.GREEN}✓" if result.solved else f"{Fore.RED}✗"
                    print(f"{status} {result.total_time:.2f}s{Style.RESET_ALL}")
                
                # Detectar si el problema es intratable
                # Si toma más de 60s consideramos que es un timeout
                if result.total_time > 60.0:
                    consecutive_timeouts += 1
                    if consecutive_timeouts >= timeout_threshold:
                        if verbose:
                            print(f"    {Fore.YELLOW}⚠ Problema detectado como INTRATABLE (3+ timeouts consecutivos){Style.RESET_ALL}")
                            print(f"    {Fore.YELLOW}   Saltando {runs_per_config - run_id - 1} runs restantes de esta configuración{Style.RESET_ALL}")
                        # Marcar runs restantes como fallidos por timeout
                        for skip_run in range(run_id + 1, runs_per_config):
                            skip_result = ColorComplexityResult(
                                board_size=board_size,
                                num_colors=num_colors,
                                density=density,
                                run_id=skip_run,
                                ga_success=False,
                                ga_time=0.0,
                                ga_generations=0,
                                ga_fitness_evals=0,
                                ga_generations_to_solution=None,
                                final_fitness=0.0,
                                bt_used=False,
                                bt_time=0.0,
                                bt_success=False,
                                total_time=0.0,
                                solved=False
                            )
                            results.append(skip_result)
                            experiment_count += 1
                        break
                else:
                    consecutive_timeouts = 0  # Reiniciar contador si el run fue rápido
            
            # Mini-resumen por configuración
            config_results = [r for r in results if r.board_size == board_size and r.num_colors == num_colors]
            success_rate = sum(1 for r in config_results if r.solved) / len(config_results)
            avg_time = statistics.mean(r.total_time for r in config_results)
            
            if verbose:
                print(f"    → Éxito: {success_rate:.1%}, Tiempo promedio: {avg_time:.3f}s")
        
        if verbose:
            print(f"{Fore.CYAN}{'─'*70}{Style.RESET_ALL}")
    
    if verbose:
        print(f"\n{Fore.GREEN}✓ Estudio completado: {experiment_count} experimentos ejecutados{Style.RESET_ALL}\n")
    
    return results


def calculate_color_summaries(results: List[ColorComplexityResult]) -> List[ColorComplexitySummary]:
    """
    Calcula resúmenes estadísticos agrupados por (board_size, num_colors).
    
    Args:
        results: Lista de resultados individuales
    
    Returns:
        Lista de ColorComplexitySummary ordenada por board_size y num_colors
    """
    # Agrupar por (board_size, num_colors)
    groups = {}
    for r in results:
        key = (r.board_size, r.num_colors)
        if key not in groups:
            groups[key] = []
        groups[key].append(r)
    
    summaries = []
    
    for (board_size, num_colors), group in sorted(groups.items()):
        total_runs = len(group)
        
        # Tasas de éxito
        ga_success_rate = sum(1 for r in group if r.ga_success) / total_runs
        bt_success_rate = sum(1 for r in group if r.bt_success) / total_runs
        total_success_rate = sum(1 for r in group if r.solved) / total_runs
        
        # Tiempos promedio
        avg_ga_time = statistics.mean(r.ga_time for r in group)
        avg_bt_time = statistics.mean(r.bt_time for r in group)
        avg_total_time = statistics.mean(r.total_time for r in group)
        
        # Fitness
        avg_fitness = statistics.mean(r.final_fitness for r in group)
        avg_fitness_evals = int(statistics.mean(r.ga_fitness_evals for r in group))
        
        # Generaciones
        avg_generations = int(statistics.mean(r.ga_generations for r in group))
        
        solved_gens = [r.ga_generations_to_solution for r in group if r.ga_generations_to_solution is not None]
        avg_generations_to_solution = statistics.mean(solved_gens) if solved_gens else None
        
        # Resolubilidad (umbral: 30% de éxito)
        is_solvable = total_success_rate >= 0.3
        
        # Puntuación de dificultad (0-100, más alto = más difícil)
        # Factores: tasa de fracaso, tiempo, evaluaciones, uso de BT
        fail_rate = 1.0 - total_success_rate
        normalized_time = min(avg_total_time / 10.0, 1.0)  # normalizar a 10s
        normalized_evals = min(avg_fitness_evals / 200000, 1.0)  # normalizar a 200k
        bt_usage_rate = sum(1 for r in group if r.bt_used) / total_runs
        
        difficulty_score = (
            fail_rate * 40 +           # 40% peso al fracaso
            normalized_time * 25 +     # 25% peso al tiempo
            normalized_evals * 20 +    # 20% peso a evaluaciones
            bt_usage_rate * 15         # 15% peso al uso de BT
        ) * 100
        
        density = num_colors / (board_size * board_size)
        
        summary = ColorComplexitySummary(
            board_size=board_size,
            num_colors=num_colors,
            density=density,
            total_runs=total_runs,
            ga_success_rate=ga_success_rate,
            bt_success_rate=bt_success_rate,
            total_success_rate=total_success_rate,
            avg_ga_time=avg_ga_time,
            avg_bt_time=avg_bt_time,
            avg_total_time=avg_total_time,
            avg_fitness=avg_fitness,
            avg_fitness_evals=avg_fitness_evals,
            avg_generations=avg_generations,
            avg_generations_to_solution=avg_generations_to_solution,
            is_solvable=is_solvable,
            difficulty_score=difficulty_score
        )
        
        summaries.append(summary)
    
    return summaries


def identify_solvability_thresholds(
    summaries: List[ColorComplexitySummary],
    success_threshold: float = 0.3
) -> Dict[int, SolvabilityThreshold]:
    """
    Identifica el umbral de resolubilidad para cada tamaño de tablero.
    El umbral es la máxima cantidad de colores donde success_rate >= threshold.
    
    Args:
        summaries: Lista de resúmenes calculados
        success_threshold: Umbral mínimo de éxito (default: 30%)
    
    Returns:
        Dict {board_size: SolvabilityThreshold}
    """
    thresholds = {}
    
    # Agrupar por board_size
    by_board = {}
    for s in summaries:
        if s.board_size not in by_board:
            by_board[s.board_size] = []
        by_board[s.board_size].append(s)
    
    for board_size, board_summaries in sorted(by_board.items()):
        # Ordenar por num_colors
        board_summaries.sort(key=lambda x: x.num_colors)
        
        # Buscar el máximo num_colors con éxito >= threshold
        max_solvable = None
        for s in board_summaries:
            if s.total_success_rate >= success_threshold:
                max_solvable = s
            else:
                # Una vez que fallamos, no seguir (asumimos monotonicidad)
                break
        
        if max_solvable:
            # Determinar razón
            if max_solvable.total_success_rate >= 0.9:
                reason = "Alta tasa de éxito mantenida"
            elif max_solvable.total_success_rate >= 0.7:
                reason = "Tasa de éxito aceptable"
            else:
                reason = "Límite de resolubilidad marginal"
            
            threshold = SolvabilityThreshold(
                board_size=board_size,
                max_solvable_colors=max_solvable.num_colors,
                max_density=max_solvable.density,
                success_rate_at_threshold=max_solvable.total_success_rate,
                avg_time_at_threshold=max_solvable.avg_total_time,
                reason=reason
            )
            thresholds[board_size] = threshold
    
    return thresholds


def plot_color_complexity_heatmap(
    summaries: List[ColorComplexitySummary],
    metric: str = 'success_rate',
    output_path: Optional[str] = None
):
    """
    Genera un heatmap de (board_size × num_colors) para una métrica específica.
    
    Args:
        summaries: Lista de resúmenes
        metric: 'success_rate', 'avg_time', 'difficulty', 'avg_fitness'
        output_path: Si se proporciona, guarda la figura
    """
    # Crear matriz
    board_sizes = sorted(set(s.board_size for s in summaries))
    
    # Obtener todos los num_colors únicos
    all_colors = sorted(set(s.num_colors for s in summaries))
    
    # Crear matriz con NaN por defecto
    matrix = np.full((len(all_colors), len(board_sizes)), np.nan)
    
    # Mapeos
    board_to_idx = {bs: i for i, bs in enumerate(board_sizes)}
    color_to_idx = {nc: i for i, nc in enumerate(all_colors)}
    
    # Llenar matriz
    for s in summaries:
        row = color_to_idx[s.num_colors]
        col = board_to_idx[s.board_size]
        
        if metric == 'success_rate':
            matrix[row, col] = s.total_success_rate * 100
        elif metric == 'avg_time':
            matrix[row, col] = s.avg_total_time
        elif metric == 'difficulty':
            matrix[row, col] = s.difficulty_score
        elif metric == 'avg_fitness':
            matrix[row, col] = s.avg_fitness
    
    # Plotear
    fig, ax = plt.subplots(figsize=(10, 8))
    
    if metric == 'success_rate':
        cmap = 'RdYlGn'
        vmin, vmax = 0, 100
        label = 'Tasa de Éxito (%)'
        fmt = '.1f'
    elif metric == 'avg_time':
        cmap = 'YlOrRd'
        vmin, vmax = None, None
        label = 'Tiempo Promedio (s)'
        fmt = '.2f'
    elif metric == 'difficulty':
        cmap = 'YlOrRd'
        vmin, vmax = 0, 100
        label = 'Puntuación de Dificultad'
        fmt = '.1f'
    elif metric == 'avg_fitness':
        cmap = 'RdYlGn'
        vmin, vmax = None, None
        label = 'Fitness Promedio'
        fmt = '.3f'
    else:
        cmap = 'viridis'
        vmin, vmax = None, None
        label = metric
        fmt = '.2f'
    
    im = ax.imshow(matrix, aspect='auto', cmap=cmap, vmin=vmin, vmax=vmax)
    
    # Etiquetas
    ax.set_xticks(range(len(board_sizes)))
    ax.set_xticklabels([f'{bs}×{bs}' for bs in board_sizes])
    ax.set_yticks(range(len(all_colors)))
    ax.set_yticklabels(all_colors)
    
    ax.set_xlabel('Tamaño del Tablero', fontsize=12, fontweight='bold')
    ax.set_ylabel('Número de Colores', fontsize=12, fontweight='bold')
    ax.set_title(f'Complejidad por Colores: {label}', fontsize=14, fontweight='bold')
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label(label, fontsize=11)
    
    # Anotar valores
    for i in range(len(all_colors)):
        for j in range(len(board_sizes)):
            if not np.isnan(matrix[i, j]):
                text_color = 'white' if matrix[i, j] < (vmax or matrix.max()) / 2 else 'black'
                ax.text(j, i, format(matrix[i, j], fmt), ha='center', va='center',
                       color=text_color, fontsize=9)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Heatmap guardado: {output_path}")
    else:
        plt.show()
    
    plt.close()


def plot_solvability_frontier(
    summaries: List[ColorComplexitySummary],
    thresholds: Dict[int, SolvabilityThreshold],
    output_path: Optional[str] = None
):
    """
    Visualiza la frontera de resolubilidad en el espacio (board_size, num_colors).
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Gráfico 1: Tasa de éxito vs num_colors por board_size
    board_sizes = sorted(set(s.board_size for s in summaries))
    
    for bs in board_sizes:
        bs_summaries = [s for s in summaries if s.board_size == bs]
        bs_summaries.sort(key=lambda x: x.num_colors)
        
        colors = [s.num_colors for s in bs_summaries]
        success_rates = [s.total_success_rate * 100 for s in bs_summaries]
        
        ax1.plot(colors, success_rates, marker='o', label=f'{bs}×{bs}', linewidth=2)
        
        # Marcar threshold
        if bs in thresholds:
            th = thresholds[bs]
            ax1.axvline(th.max_solvable_colors, color='gray', linestyle='--', alpha=0.5)
            ax1.plot(th.max_solvable_colors, th.success_rate_at_threshold * 100,
                    'r*', markersize=15, markeredgecolor='black', markeredgewidth=1)
    
    ax1.axhline(30, color='red', linestyle=':', alpha=0.7, label='Umbral 30%')
    ax1.set_xlabel('Número de Colores', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Tasa de Éxito (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Tasa de Éxito vs Número de Colores', fontsize=13, fontweight='bold')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 105)
    
    # Gráfico 2: Frontera en espacio 2D
    for bs in board_sizes:
        bs_summaries = [s for s in summaries if s.board_size == bs]
        bs_summaries.sort(key=lambda x: x.num_colors)
        
        colors = [s.num_colors for s in bs_summaries]
        sizes = [s.board_size for s in bs_summaries]
        success_rates = [s.total_success_rate for s in bs_summaries]
        
        # Color por success_rate
        scatter = ax2.scatter(sizes, colors, c=success_rates, s=100, cmap='RdYlGn',
                            vmin=0, vmax=1, edgecolors='black', linewidth=0.5, alpha=0.8)
    
    # Línea de frontera
    if thresholds:
        frontier_x = sorted(thresholds.keys())
        frontier_y = [thresholds[bs].max_solvable_colors for bs in frontier_x]
        ax2.plot(frontier_x, frontier_y, 'r-', linewidth=3, label='Frontera de Resolubilidad', zorder=10)
        ax2.fill_between(frontier_x, 0, frontier_y, alpha=0.2, color='green', label='Región Resoluble')
    
    ax2.set_xlabel('Tamaño del Tablero (N)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Número de Colores', fontsize=12, fontweight='bold')
    ax2.set_title('Frontera de Resolubilidad (NP-Completo)', fontsize=13, fontweight='bold')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    
    cbar = plt.colorbar(scatter, ax=ax2)
    cbar.set_label('Tasa de Éxito', fontsize=11)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Frontera de resolubilidad guardada: {output_path}")
    else:
        plt.show()
    
    plt.close()


def export_color_study_results(
    results: List[ColorComplexityResult],
    summaries: List[ColorComplexitySummary],
    thresholds: Dict[int, SolvabilityThreshold],
    output_dir: str = "color_complexity_results"
):
    """Exporta resultados a CSV y JSON."""
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. CSV detallado
    csv_path = os.path.join(output_dir, "color_complexity_detailed.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'board_size', 'num_colors', 'density', 'run_id',
            'ga_success', 'ga_time', 'ga_generations', 'ga_fitness_evals',
            'ga_generations_to_solution', 'final_fitness',
            'bt_used', 'bt_time', 'bt_success',
            'total_time', 'solved'
        ])
        
        for r in results:
            writer.writerow([
                r.board_size, r.num_colors, f"{r.density:.4f}", r.run_id,
                r.ga_success, f"{r.ga_time:.4f}", r.ga_generations, r.ga_fitness_evals,
                r.ga_generations_to_solution if r.ga_generations_to_solution else '',
                f"{r.final_fitness:.4f}",
                r.bt_used, f"{r.bt_time:.4f}", r.bt_success,
                f"{r.total_time:.4f}", r.solved
            ])
    
    print(f"✓ CSV detallado: {csv_path}")
    
    # 2. CSV resumen
    summary_csv_path = os.path.join(output_dir, "color_complexity_summary.csv")
    with open(summary_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'board_size', 'num_colors', 'density', 'total_runs',
            'ga_success_rate', 'bt_success_rate', 'total_success_rate',
            'avg_ga_time', 'avg_bt_time', 'avg_total_time',
            'avg_fitness', 'avg_fitness_evals', 'avg_generations',
            'avg_generations_to_solution', 'is_solvable', 'difficulty_score'
        ])
        
        for s in summaries:
            writer.writerow([
                s.board_size, s.num_colors, f"{s.density:.4f}", s.total_runs,
                f"{s.ga_success_rate:.4f}", f"{s.bt_success_rate:.4f}", f"{s.total_success_rate:.4f}",
                f"{s.avg_ga_time:.4f}", f"{s.avg_bt_time:.4f}", f"{s.avg_total_time:.4f}",
                f"{s.avg_fitness:.4f}", s.avg_fitness_evals, s.avg_generations,
                f"{s.avg_generations_to_solution:.2f}" if s.avg_generations_to_solution else '',
                s.is_solvable, f"{s.difficulty_score:.2f}"
            ])
    
    print(f"✓ CSV resumen: {summary_csv_path}")
    
    # 3. JSON con umbrales
    json_path = os.path.join(output_dir, "solvability_thresholds.json")
    thresholds_dict = {
        bs: {
            'max_solvable_colors': th.max_solvable_colors,
            'max_density': round(th.max_density, 4),
            'success_rate': round(th.success_rate_at_threshold, 4),
            'avg_time': round(th.avg_time_at_threshold, 4),
            'reason': th.reason
        }
        for bs, th in thresholds.items()
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(thresholds_dict, f, indent=2)
    
    print(f"✓ JSON umbrales: {json_path}")


def print_solvability_report(
    summaries: List[ColorComplexitySummary],
    thresholds: Dict[int, SolvabilityThreshold]
):
    """Imprime un reporte legible de los umbrales de resolubilidad."""
    print(f"\n{'='*80}")
    print(f"{'REPORTE DE RESOLUBILIDAD (NP-COMPLETO)':^80}")
    print(f"{'='*80}\n")
    
    if not thresholds:
        print(f"{Fore.RED}⚠ No se encontraron umbrales de resolubilidad{Style.RESET_ALL}\n")
        return
    
    print(f"{'Tamaño':<12} {'Max Colores':<15} {'Densidad':<12} {'Éxito':<12} {'Tiempo':<12} {'Razón':<30}")
    print(f"{'-'*80}")
    
    for bs in sorted(thresholds.keys()):
        th = thresholds[bs]
        print(f"{bs}×{bs:<9} {th.max_solvable_colors:<15} {th.max_density:<12.3f} "
              f"{th.success_rate_at_threshold*100:<11.1f}% {th.avg_time_at_threshold:<11.3f}s {th.reason:<30}")
    
    print(f"{'-'*80}\n")
    
    # Estadísticas generales
    print(f"{'ANÁLISIS DE COMPLEJIDAD':^80}")
    print(f"{'-'*80}")
    
    for bs in sorted(set(s.board_size for s in summaries)):
        bs_summaries = [s for s in summaries if s.board_size == bs]
        bs_summaries.sort(key=lambda x: x.num_colors)
        
        print(f"\n{Fore.CYAN}Tablero {bs}×{bs}:{Style.RESET_ALL}")
        print(f"  {'Colores':<10} {'Densidad':<12} {'Éxito':<12} {'Tiempo':<12} {'Dificultad':<12} {'Estado'}")
        print(f"  {'-'*75}")
        
        for s in bs_summaries:
            status = f"{Fore.GREEN}✓ Resoluble" if s.is_solvable else f"{Fore.RED}✗ Irresoluble"
            print(f"  {s.num_colors:<10} {s.density:<12.3f} {s.total_success_rate*100:<11.1f}% "
                  f"{s.avg_total_time:<11.3f}s {s.difficulty_score:<11.1f} {status}{Style.RESET_ALL}")
    
    print(f"\n{'='*80}\n")


def run_complete_color_study(
    board_sizes: List[int] = [4, 5, 6],
    color_ranges: Optional[Dict[int, List[int]]] = None,
    runs_per_config: int = 10,
    output_dir: str = "color_complexity_results",
    pop_size: int = 200,
    generations: int = 1000,
    mut_rate: float = 0.03,
    elite: int = 2,
    tour_k: int = 3
) -> Tuple[List[ColorComplexityResult], List[ColorComplexitySummary], Dict[int, SolvabilityThreshold]]:
    """
    Ejecuta un estudio completo de complejidad por colores con visualizaciones.
    
    Args:
        board_sizes: Lista de tamaños de tablero
        color_ranges: Dict {board_size: [num_colors_list]}
                      Si None, usa rangos inteligentes basados en board_size
        runs_per_config: Corridas por configuración
        output_dir: Directorio para resultados
        pop_size, generations, mut_rate, elite, tour_k: Parámetros GA
    
    Returns:
        (results, summaries, thresholds)
    """
    # Generar rangos automáticos si no se proporcionan
    if color_ranges is None:
        color_ranges = {}
        for bs in board_sizes:
            # Calcular máximo de colores viable
            total_cells = bs * bs
            min_segment_length = max(2, bs // 2)
            max_possible_colors = total_cells // min_segment_length
            
            # Para tableros grandes (8×8+), usar rangos MUY conservadores
            # porque el espacio de búsqueda crece exponencialmente
            if bs >= 8:
                # Solo probar densidades BAJAS (10%-30%)
                start = max(3, int(total_cells * 0.10))
                end = max(start, int(total_cells * 0.30))
                # Limitar número de experimentos a 3-4 puntos
                step = max(1, (end - start) // 3)
                print(f"⚠️  {bs}×{bs} tablero GRANDE: usando rango conservador ({start}-{end} colores)")
            else:
                # Tableros pequeños/medianos: rango normal
                # Rango seguro: desde ~30% de densidad hasta ~80% del máximo posible
                start = max(3, int(total_cells * 0.30))
                # Usar 80% del máximo teórico para evitar límites físicos imposibles
                end = max(start, int(max_possible_colors * 0.80))
                # Limitar a máximo 8 valores para no hacer experimentos muy largos
                step = max(1, (end - start) // 7)
            
            # Asegurar que end no exceda el máximo
            end = min(end, max_possible_colors)
            
            color_ranges[bs] = list(range(start, end + 1, step))
            
            # Filtro final: asegurar que no excedemos el límite
            color_ranges[bs] = [c for c in color_ranges[bs] if c <= max_possible_colors]
            
            # Si el rango quedó vacío, usar valores conservadores
            if not color_ranges[bs]:
                # Usar 50%-70% del máximo
                mid = max(3, int(max_possible_colors * 0.60))
                color_ranges[bs] = [mid]
    
    # Mostrar rangos generados
    print(f"\n{Fore.CYAN}Rangos de colores generados (automáticos):{Style.RESET_ALL}")
    for bs in sorted(color_ranges.keys()):
        total_cells = bs * bs
        min_seg = max(2, bs // 2)
        max_colors = total_cells // min_seg
        print(f"  {bs}×{bs} ({total_cells} celdas, max={max_colors}): {color_ranges[bs]}")
    print()
    
    # Ejecutar experimentos
    results = run_color_complexity_study(
        board_sizes=board_sizes,
        color_ranges=color_ranges,
        runs_per_config=runs_per_config,
        pop_size=pop_size,
        generations=generations,
        mut_rate=mut_rate,
        elite=elite,
        tour_k=tour_k,
        verbose=True
    )
    
    # Calcular resúmenes
    summaries = calculate_color_summaries(results)
    
    # Identificar umbrales
    thresholds = identify_solvability_thresholds(summaries)
    
    # Exportar resultados
    export_color_study_results(results, summaries, thresholds, output_dir)
    
    # Generar visualizaciones
    plot_color_complexity_heatmap(summaries, 'success_rate', 
                                   os.path.join(output_dir, 'heatmap_success_rate.png'))
    plot_color_complexity_heatmap(summaries, 'avg_time',
                                   os.path.join(output_dir, 'heatmap_avg_time.png'))
    plot_color_complexity_heatmap(summaries, 'difficulty',
                                   os.path.join(output_dir, 'heatmap_difficulty.png'))
    plot_solvability_frontier(summaries, thresholds,
                              os.path.join(output_dir, 'solvability_frontier.png'))
    
    # Imprimir reporte
    print_solvability_report(summaries, thresholds)
    
    return results, summaries, thresholds


if __name__ == "__main__":
    # Ejemplo de uso
    print("Ejecutando estudio de complejidad por colores...")
    
    results, summaries, thresholds = run_complete_color_study(
        board_sizes=[4, 5, 6],
        runs_per_config=5,
        output_dir="color_complexity_test"
    )
    
    print("\n✓ Estudio completado. Revisa la carpeta 'color_complexity_test' para los resultados.")
