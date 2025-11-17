"""
Módulo para experimentos de escalabilidad del algoritmo genético.
Mide el crecimiento del costo computacional con el tamaño del tablero.
"""
import csv
import json
import os
import statistics
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

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
class ScalabilityResult:
    """Resultado de una ejecución individual."""
    board_size: int
    num_colors: int
    num_cells: int
    ga_success: bool
    ga_time: float
    ga_generations: int
    ga_fitness_evals: int
    ga_generations_to_solution: Optional[int]
    ga_convergence_generation: Optional[int]
    ga_diversity_loss: float
    bt_used: bool
    bt_time: float
    total_time: float
    final_fitness: float


@dataclass
class ScalabilitySummary:
    """Resumen estadístico para un tamaño de tablero."""
    board_size: int
    num_colors: int
    num_cells: int
    num_runs: int
    
    # Métricas GA
    ga_success_rate: float
    ga_avg_time: float
    ga_std_time: float
    ga_avg_generations: float
    ga_avg_fitness_evals: float
    ga_avg_generations_to_solution: Optional[float]
    ga_avg_convergence_gen: Optional[float]
    ga_avg_diversity_loss: float
    
    # Métricas híbridas (GA + BT)
    bt_usage_rate: float
    bt_avg_time: float
    hybrid_avg_time: float
    hybrid_success_rate: float
    
    # Indicadores de eficiencia
    efficiency_score: float  # 0-1, basado en éxito y tiempo
    local_optima_rate: float  # Tasa de estancamiento en óptimos locales


def run_single_experiment(board_size: int, 
                         num_colors: int,
                         pop_size: int = 200,
                         generations: int = 1000,
                         verbose: bool = False) -> ScalabilityResult:
    """Ejecuta un experimento individual con un tablero dado."""
    
    # Generar puzzle
    terminals = generate_random_puzzle(board_size, num_colors)
    num_cells = board_size * board_size
    
    # 🔥 GENERACIONES Y POBLACIÓN ADAPTATIVAS para tableros grandes
    # Configuración mejorada para dar al GA una oportunidad real de encontrar soluciones
    adaptive_generations = generations
    adaptive_pop_size = pop_size
    density = num_colors / num_cells
    
    # Configuración balanceada: suficiente exploración sin explotar el tiempo
    # AJUSTE CRÍTICO: 8×8 necesita MÁS recursos que 7×7 debido al salto en complejidad
    if board_size >= 10:
        adaptive_generations = 300  # 🔥 Suficiente para exploración seria
        adaptive_pop_size = 200     # 🔥 Población razonable
        print(f"   {Fore.CYAN}📊 Tablero 10×10: {adaptive_generations} gens × {adaptive_pop_size} pop (búsqueda intensiva){Style.RESET_ALL}")
    elif board_size >= 9:
        adaptive_generations = 500  # 🔥 Exploración robusta
        adaptive_pop_size = 200     # 🔥 Población amplia
        print(f"   {Fore.CYAN}📊 Tablero 9×9: {adaptive_generations} gens × {adaptive_pop_size} pop (búsqueda robusta){Style.RESET_ALL}")
    elif board_size == 8:
        # 🔥 AJUSTE CRÍTICO: 8×8 es el punto de transición donde crece la complejidad exponencialmente
        # Necesita tantos recursos como 7×7 (o más) para evitar convergencia prematura
        adaptive_generations = 1000  # Aumentado de 800 para evitar óptimos locales
        adaptive_pop_size = 200      # Aumentado de 150 para mayor diversidad
        print(f"   {Fore.YELLOW}⚡ Tablero 8×8 (punto crítico): {adaptive_generations} gens × {adaptive_pop_size} pop = {adaptive_generations*adaptive_pop_size:,} evaluaciones{Style.RESET_ALL}")
    elif board_size >= 7 or density > 0.35:
        adaptive_generations = 1000  # Mantener consistencia con 8×8
        adaptive_pop_size = 150
        print(f"   {Fore.CYAN}� Tablero {board_size}×{board_size}: {adaptive_generations} gens × {adaptive_pop_size} pop{Style.RESET_ALL}")
    
    # Ejecutar GA con parámetros adaptados
    ga_start = time.time()
    sol_ga, metrics = ga_solve_flow(
        board_size, terminals,
        pop_size=adaptive_pop_size,      # 🔥 Población adaptada
        generations=adaptive_generations, # 🔥 Generaciones adaptadas
        mut_rate=0.03,
        elite=0,
        tour_k=3,
        verbose=verbose,
        collect_metrics=True
    )
    ga_time = time.time() - ga_start
    
    # Extraer métricas GA
    summary = metrics.get_summary()
    perf = summary['rendimiento']
    div = summary['diversidad']
    
    ga_success = perf['exito']
    ga_generations = perf['generaciones_ejecutadas']
    ga_fitness_evals = perf['evaluaciones_fitness']
    ga_gen_to_sol = perf['generaciones_hasta_solucion']
    ga_conv_gen = perf['generacion_convergencia']
    ga_diversity_loss = div['perdida_diversidad']
    final_fitness = summary['fitness']['fitness_final']
    
    # Verificar si necesitamos backtracking
    bt_used = False
    bt_time = 0.0
    
    if not ga_success:
        bt_start = time.time()
        sol_bt = solve_flow_bt(board_size, terminals, start_grid=sol_ga)
        bt_time = time.time() - bt_start
        bt_used = True
        
        if sol_bt and is_perfect(sol_bt, terminals):
            ga_success = False  # GA no tuvo éxito, pero BT sí
        else:
            # Esto no debería pasar con nuestro generador
            pass
    
    total_time = ga_time + bt_time
    
    return ScalabilityResult(
        board_size=board_size,
        num_colors=num_colors,
        num_cells=num_cells,
        ga_success=ga_success,
        ga_time=ga_time,
        ga_generations=ga_generations,
        ga_fitness_evals=ga_fitness_evals,
        ga_generations_to_solution=ga_gen_to_sol,
        ga_convergence_generation=ga_conv_gen,
        ga_diversity_loss=ga_diversity_loss,
        bt_used=bt_used,
        bt_time=bt_time,
        total_time=total_time,
        final_fitness=final_fitness
    )


def run_scalability_experiments(
    board_sizes: List[int],
    colors_config: Dict[int, int],
    runs_per_size: int = 10,
    pop_size: int = 200,
    generations: int = 1000,
    verbose: bool = False
) -> Dict[int, List[ScalabilityResult]]:
    """
    Ejecuta múltiples experimentos para diferentes tamaños de tablero.
    
    Args:
        board_sizes: Lista de tamaños de tablero a probar (ej: [4, 5, 6, 7])
        colors_config: Diccionario {board_size: num_colors}
        runs_per_size: Número de corridas por tamaño
        pop_size: Tamaño de población del GA
        generations: Generaciones máximas del GA
        verbose: Mostrar progreso detallado
    
    Returns:
        Diccionario con resultados por tamaño de tablero
    """
    results = {}
    
    print("\n" + "="*80)
    print("🔬 EXPERIMENTOS DE ESCALABILIDAD")
    print("="*80)
    print(f"Tamaños de tablero: {board_sizes}")
    print(f"Corridas por tamaño: {runs_per_size}")
    print(f"Población: {pop_size}, Generaciones: {generations}")
    print("="*80 + "\n")
    
    total_configs = len(board_sizes)
    
    try:
        for config_idx, board_size in enumerate(board_sizes, 1):
            num_colors = colors_config.get(board_size, board_size // 2)
            results[board_size] = []
            
            print(f"\n{'='*80}")
            print(f"📐 CONFIGURACIÓN [{config_idx}/{total_configs}]: TABLERO {board_size}x{board_size}")
            print(f"{'='*80}")
            print(f"Celdas: {board_size*board_size} | Colores: {num_colors} | Corridas: {runs_per_size}")
            print(f"{'='*80}")
            
            for run in range(1, runs_per_size + 1):
                # Barra de progreso de corridas
                run_progress = (run / runs_per_size) * 100
                bar_length = 30
                filled = int(bar_length * run / runs_per_size)
                bar = '█' * filled + '░' * (bar_length - filled)
                
                print(f"\n  [{bar}] {run_progress:5.1f}% | Corrida {run}/{runs_per_size}...", end=" ", flush=True)
                
                try:
                    result = run_single_experiment(
                        board_size, num_colors,
                        pop_size, generations,
                        verbose=verbose
                    )
                    results[board_size].append(result)
                    
                    # Mostrar resultado breve
                    status = "✅ GA" if result.ga_success else ("✅ BT" if result.bt_used else "❌")
                    print(f"{status} | {result.ga_time:.2f}s | {result.ga_generations} gen | {result.ga_fitness_evals} evals")
                    
                except Exception as e:
                    print(f"❌ Error: {e}")
                    continue
            
            # Resumen parcial
            if results[board_size]:
                ga_success_rate = sum(1 for r in results[board_size] if r.ga_success) / len(results[board_size])
                avg_time = statistics.mean(r.ga_time for r in results[board_size])
                print(f"\n  📊 Resumen {board_size}x{board_size}:")
                print(f"     • Éxito GA: {ga_success_rate*100:.1f}%")
                print(f"     • Tiempo promedio: {avg_time:.3f}s")
    
    except KeyboardInterrupt:
        print(f"\n\n{'='*80}")
        print(f"⚠️  EXPERIMENTO INTERRUMPIDO (Ctrl+C)")
        print(f"{'='*80}")
        print(f"💾 Guardando resultados parciales...")
        total_completed = sum(len(runs) for runs in results.values())
        print(f"   • Corridas completadas: {total_completed}")
        print(f"   • Tableros analizados: {len([bs for bs, runs in results.items() if runs])}")
        print(f"{'='*80}\n")
        # Filtrar tableros vacíos
        results = {bs: runs for bs, runs in results.items() if runs}
    
    return results


def calculate_summary_statistics(results: Dict[int, List[ScalabilityResult]]) -> Dict[int, ScalabilitySummary]:
    """Calcula estadísticas resumidas para cada tamaño de tablero."""
    summaries = {}
    
    for board_size, runs in results.items():
        if not runs:
            continue
        
        num_runs = len(runs)
        num_colors = runs[0].num_colors
        num_cells = runs[0].num_cells
        
        # Métricas GA
        ga_successes = [r for r in runs if r.ga_success]
        ga_success_rate = len(ga_successes) / num_runs
        
        ga_times = [r.ga_time for r in runs]
        ga_avg_time = statistics.mean(ga_times)
        ga_std_time = statistics.stdev(ga_times) if num_runs > 1 else 0.0
        
        ga_avg_generations = statistics.mean(r.ga_generations for r in runs)
        ga_avg_fitness_evals = statistics.mean(r.ga_fitness_evals for r in runs)
        
        # Generaciones hasta solución (solo éxitos)
        ga_gens_to_sol = [r.ga_generations_to_solution for r in ga_successes if r.ga_generations_to_solution]
        ga_avg_gens_to_sol = statistics.mean(ga_gens_to_sol) if ga_gens_to_sol else None
        
        # Convergencia
        ga_conv_gens = [r.ga_convergence_generation for r in runs if r.ga_convergence_generation]
        ga_avg_conv_gen = statistics.mean(ga_conv_gens) if ga_conv_gens else None
        
        ga_avg_diversity_loss = statistics.mean(r.ga_diversity_loss for r in runs)
        
        # Métricas híbridas
        bt_used_count = sum(1 for r in runs if r.bt_used)
        bt_usage_rate = bt_used_count / num_runs
        
        bt_times = [r.bt_time for r in runs if r.bt_used]
        bt_avg_time = statistics.mean(bt_times) if bt_times else 0.0
        
        hybrid_avg_time = statistics.mean(r.total_time for r in runs)
        
        # Éxito híbrido (GA o BT)
        hybrid_success = sum(1 for r in runs if r.ga_success or r.bt_used)
        hybrid_success_rate = hybrid_success / num_runs
        
        # Indicadores de eficiencia
        # Efficiency score: combina éxito y velocidad
        if ga_success_rate > 0:
            efficiency_score = ga_success_rate * (1.0 / (1.0 + ga_avg_time / 10.0))
        else:
            efficiency_score = 0.0
        
        # Local optima rate: convergencia temprana sin éxito
        early_convergence = sum(
            1 for r in runs 
            if not r.ga_success 
            and r.ga_convergence_generation 
            and r.ga_convergence_generation < r.ga_generations * 0.3
        )
        local_optima_rate = early_convergence / num_runs
        
        summaries[board_size] = ScalabilitySummary(
            board_size=board_size,
            num_colors=num_colors,
            num_cells=num_cells,
            num_runs=num_runs,
            ga_success_rate=ga_success_rate,
            ga_avg_time=ga_avg_time,
            ga_std_time=ga_std_time,
            ga_avg_generations=ga_avg_generations,
            ga_avg_fitness_evals=ga_avg_fitness_evals,
            ga_avg_generations_to_solution=ga_avg_gens_to_sol,
            ga_avg_convergence_gen=ga_avg_conv_gen,
            ga_avg_diversity_loss=ga_avg_diversity_loss,
            bt_usage_rate=bt_usage_rate,
            bt_avg_time=bt_avg_time,
            hybrid_avg_time=hybrid_avg_time,
            hybrid_success_rate=hybrid_success_rate,
            efficiency_score=efficiency_score,
            local_optima_rate=local_optima_rate
        )
    
    return summaries


def export_results_to_csv(results: Dict[int, List[ScalabilityResult]], 
                         filename: str = "scalability_results.csv"):
    """Exporta los resultados detallados a CSV."""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Encabezados
        writer.writerow([
            'board_size', 'num_colors', 'num_cells', 'run_number',
            'ga_success', 'ga_time', 'ga_generations', 'ga_fitness_evals',
            'ga_generations_to_solution', 'ga_convergence_generation',
            'ga_diversity_loss', 'bt_used', 'bt_time', 'total_time',
            'final_fitness'
        ])
        
        # Datos
        for board_size, runs in sorted(results.items()):
            for i, result in enumerate(runs, 1):
                writer.writerow([
                    result.board_size,
                    result.num_colors,
                    result.num_cells,
                    i,
                    result.ga_success,
                    f"{result.ga_time:.4f}",
                    result.ga_generations,
                    result.ga_fitness_evals,
                    result.ga_generations_to_solution or '',
                    result.ga_convergence_generation or '',
                    f"{result.ga_diversity_loss:.4f}",
                    result.bt_used,
                    f"{result.bt_time:.4f}",
                    f"{result.total_time:.4f}",
                    f"{result.final_fitness:.2f}"
                ])
    
    print(f"\n📄 Resultados detallados guardados en: {filename}")


def export_summary_to_json(summaries: Dict[int, ScalabilitySummary],
                          filename: str = "scalability_summary.json"):
    """Exporta el resumen estadístico a JSON."""
    data = {}
    
    for board_size, summary in sorted(summaries.items()):
        data[f"{board_size}x{board_size}"] = {
            'configuracion': {
                'tablero': f"{board_size}x{board_size}",
                'celdas': summary.num_cells,
                'colores': summary.num_colors,
                'corridas': summary.num_runs
            },
            'ga_metricas': {
                'tasa_exito': f"{summary.ga_success_rate*100:.1f}%",
                'tiempo_promedio': f"{summary.ga_avg_time:.3f}s",
                'tiempo_std': f"{summary.ga_std_time:.3f}s",
                'generaciones_promedio': f"{summary.ga_avg_generations:.1f}",
                'evaluaciones_promedio': f"{summary.ga_avg_fitness_evals:.0f}",
                'generaciones_hasta_solucion': f"{summary.ga_avg_generations_to_solution:.1f}" if summary.ga_avg_generations_to_solution else "N/A",
                'generacion_convergencia': f"{summary.ga_avg_convergence_gen:.1f}" if summary.ga_avg_convergence_gen else "N/A",
                'perdida_diversidad': f"{summary.ga_avg_diversity_loss:.3f}"
            },
            'hibrido_metricas': {
                'uso_backtracking': f"{summary.bt_usage_rate*100:.1f}%",
                'tiempo_bt_promedio': f"{summary.bt_avg_time:.3f}s",
                'tiempo_total_promedio': f"{summary.hybrid_avg_time:.3f}s",
                'tasa_exito_total': f"{summary.hybrid_success_rate*100:.1f}%"
            },
            'eficiencia': {
                'score': f"{summary.efficiency_score:.3f}",
                'tasa_optimos_locales': f"{summary.local_optima_rate*100:.1f}%"
            }
        }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"📊 Resumen estadístico guardado en: {filename}")


def print_summary_table(summaries: Dict[int, ScalabilitySummary]):
    """Imprime una tabla resumida de los resultados."""
    print("\n" + "="*120)
    print("📋 TABLA RESUMEN DE ESCALABILIDAD")
    print("="*120)
    
    # Encabezados
    print(f"{'Tablero':10} {'Celdas':8} {'Éxito GA':10} {'Tiempo GA':12} {'Evals':12} "
          f"{'Uso BT':10} {'Ópt.Local':12} {'Eficiencia':12}")
    print("-" * 120)
    
    for board_size, summary in sorted(summaries.items()):
        print(f"{board_size}x{board_size:1}     {summary.num_cells:8} "
              f"{summary.ga_success_rate*100:8.1f}%  "
              f"{summary.ga_avg_time:9.3f}s   "
              f"{summary.ga_avg_fitness_evals:10.0f}  "
              f"{summary.bt_usage_rate*100:8.1f}%  "
              f"{summary.local_optima_rate*100:10.1f}%  "
              f"{summary.efficiency_score:10.3f}")
    
    print("="*120)


def identify_inefficiency_threshold(summaries: Dict[int, ScalabilitySummary],
                                   success_threshold: float = 0.5,
                                   efficiency_threshold: float = 0.3) -> Optional[int]:
    """
    Identifica el tamaño de tablero donde el GA deja de ser eficiente.
    
    Criterios:
    - Tasa de éxito < success_threshold
    - Score de eficiencia < efficiency_threshold
    - Alta tasa de óptimos locales (> 30%)
    """
    print("\n" + "="*80)
    print("🎯 ANÁLISIS DE EFICIENCIA DEL ALGORITMO GENÉTICO")
    print("="*80)
    
    inefficient_size = None
    
    for board_size, summary in sorted(summaries.items()):
        is_inefficient = False
        reasons = []
        
        if summary.ga_success_rate < success_threshold:
            is_inefficient = True
            reasons.append(f"Tasa de éxito baja ({summary.ga_success_rate*100:.1f}% < {success_threshold*100}%)")
        
        if summary.efficiency_score < efficiency_threshold:
            is_inefficient = True
            reasons.append(f"Score de eficiencia bajo ({summary.efficiency_score:.3f} < {efficiency_threshold})")
        
        if summary.local_optima_rate > 0.3:
            is_inefficient = True
            reasons.append(f"Alta tasa de óptimos locales ({summary.local_optima_rate*100:.1f}%)")
        
        if is_inefficient and inefficient_size is None:
            inefficient_size = board_size
            print(f"\n⚠️  PUNTO DE INEFICIENCIA DETECTADO: {board_size}x{board_size}")
            print(f"\n   Razones:")
            for reason in reasons:
                print(f"   • {reason}")
        
        # Mostrar estado de cada tamaño
        status = "✅ EFICIENTE" if not is_inefficient else "⚠️  INEFICIENTE"
        print(f"\n{board_size}x{board_size}: {status}")
        print(f"   • Éxito: {summary.ga_success_rate*100:.1f}%")
        print(f"   • Eficiencia: {summary.efficiency_score:.3f}")
        print(f"   • Óptimos locales: {summary.local_optima_rate*100:.1f}%")
        print(f"   • Tiempo promedio: {summary.ga_avg_time:.3f}s")
    
    if inefficient_size:
        print(f"\n{'='*80}")
        print(f"🔴 El GA deja de ser eficiente a partir de tableros {inefficient_size}x{inefficient_size}")
        print(f"{'='*80}")
    else:
        print(f"\n{'='*80}")
        print(f"✅ El GA mantiene buena eficiencia en todos los tamaños probados")
        print(f"{'='*80}")
    
    return inefficient_size


def identify_practical_limits(summaries: Dict[int, ScalabilitySummary],
                              max_time_ga: float = 60.0,
                              max_time_hybrid: float = 120.0,
                              min_success_ga: float = 0.5,
                              min_success_hybrid: float = 0.8) -> Dict[str, Any]:
    """
    Identifica límites prácticos de uso del sistema basado en umbrales configurables.
    
    Args:
        max_time_ga: Tiempo máximo aceptable para GA solo (segundos)
        max_time_hybrid: Tiempo máximo aceptable para modelo híbrido (segundos)
        min_success_ga: Tasa mínima de éxito del GA solo
        min_success_hybrid: Tasa mínima de éxito del modelo híbrido
    
    Returns:
        Diccionario con análisis de límites prácticos
    """
    print("\n" + "="*80)
    print("🎯 IDENTIFICACIÓN DE LÍMITES PRÁCTICOS DE USO")
    print("="*80)
    print(f"Criterios:")
    print(f"  • Tiempo máx GA: {max_time_ga}s")
    print(f"  • Tiempo máx Híbrido: {max_time_hybrid}s")
    print(f"  • Éxito mín GA: {min_success_ga*100}%")
    print(f"  • Éxito mín Híbrido: {min_success_hybrid*100}%")
    print("="*80)
    
    results = {
        'max_size_ga_only': None,
        'max_size_hybrid': None,
        'ga_viable_sizes': [],
        'hybrid_viable_sizes': [],
        'recommendations': []
    }
    
    for board_size, summary in sorted(summaries.items()):
        # Evaluar viabilidad de GA solo
        ga_viable = (summary.ga_success_rate >= min_success_ga and 
                    summary.ga_avg_time <= max_time_ga)
        
        # Evaluar viabilidad del modelo híbrido
        hybrid_viable = (summary.hybrid_success_rate >= min_success_hybrid and 
                        summary.hybrid_avg_time <= max_time_hybrid)
        
        if ga_viable:
            results['ga_viable_sizes'].append(board_size)
            results['max_size_ga_only'] = board_size
        
        if hybrid_viable:
            results['hybrid_viable_sizes'].append(board_size)
            results['max_size_hybrid'] = board_size
        
        # Mostrar evaluación
        print(f"\n📐 Tablero {board_size}x{board_size}:")
        
        # GA Solo
        ga_status = "✅ VIABLE" if ga_viable else "❌ NO VIABLE"
        ga_reasons = []
        if summary.ga_success_rate < min_success_ga:
            ga_reasons.append(f"Éxito bajo ({summary.ga_success_rate*100:.1f}%)")
        if summary.ga_avg_time > max_time_ga:
            ga_reasons.append(f"Tiempo alto ({summary.ga_avg_time:.1f}s)")
        
        print(f"   GA Solo: {ga_status}")
        print(f"      • Éxito: {summary.ga_success_rate*100:.1f}% (req: {min_success_ga*100}%)")
        print(f"      • Tiempo: {summary.ga_avg_time:.2f}s (max: {max_time_ga}s)")
        if ga_reasons:
            print(f"      • Razones: {', '.join(ga_reasons)}")
        
        # Modelo Híbrido
        hybrid_status = "✅ VIABLE" if hybrid_viable else "❌ NO VIABLE"
        hybrid_reasons = []
        if summary.hybrid_success_rate < min_success_hybrid:
            hybrid_reasons.append(f"Éxito bajo ({summary.hybrid_success_rate*100:.1f}%)")
        if summary.hybrid_avg_time > max_time_hybrid:
            hybrid_reasons.append(f"Tiempo alto ({summary.hybrid_avg_time:.1f}s)")
        
        print(f"   Modelo Híbrido: {hybrid_status}")
        print(f"      • Éxito: {summary.hybrid_success_rate*100:.1f}% (req: {min_success_hybrid*100}%)")
        print(f"      • Tiempo: {summary.hybrid_avg_time:.2f}s (max: {max_time_hybrid}s)")
        print(f"      • Uso BT: {summary.bt_usage_rate*100:.1f}%")
        if hybrid_reasons:
            print(f"      • Razones: {', '.join(hybrid_reasons)}")
    
    # Generar recomendaciones
    print(f"\n{'='*80}")
    print("📋 RESUMEN Y RECOMENDACIONES")
    print("="*80)
    
    if results['max_size_ga_only']:
        print(f"\n✅ GA SOLO es viable hasta: {results['max_size_ga_only']}x{results['max_size_ga_only']}")
        results['recommendations'].append(
            f"Usar GA solo para tableros hasta {results['max_size_ga_only']}x{results['max_size_ga_only']}"
        )
    else:
        print(f"\n❌ GA SOLO no cumple criterios en ningún tamaño probado")
        results['recommendations'].append(
            "GA solo requiere ajuste de parámetros o no es viable"
        )
    
    if results['max_size_hybrid']:
        print(f"✅ MODELO HÍBRIDO es viable hasta: {results['max_size_hybrid']}x{results['max_size_hybrid']}")
        results['recommendations'].append(
            f"Usar modelo híbrido GA+BT para tableros hasta {results['max_size_hybrid']}x{results['max_size_hybrid']}"
        )
    else:
        print(f"❌ MODELO HÍBRIDO no cumple criterios en ningún tamaño probado")
        results['recommendations'].append(
            "Modelo híbrido requiere optimización o no es viable"
        )
    
    # Análisis de costo-beneficio
    if results['max_size_ga_only'] and results['max_size_hybrid']:
        if results['max_size_hybrid'] > results['max_size_ga_only']:
            improvement = results['max_size_hybrid'] - results['max_size_ga_only']
            print(f"\n🎯 El modelo híbrido extiende la viabilidad en {improvement} tamaño(s) de tablero")
            results['recommendations'].append(
                f"El backtracking añade {improvement} tamaño(s) de capacidad al sistema"
            )
    
    # Identificar tamaño óptimo (mejor balance éxito/tiempo)
    best_balance = None
    best_score = 0
    for board_size, summary in summaries.items():
        # Score: éxito / tiempo (queremos alto éxito, bajo tiempo)
        balance_score = summary.hybrid_success_rate / (summary.hybrid_avg_time + 1)
        if balance_score > best_score:
            best_score = balance_score
            best_balance = board_size
    
    if best_balance:
        print(f"\n🏆 TAMAÑO ÓPTIMO: {best_balance}x{best_balance}")
        print(f"   (Mejor balance éxito/tiempo: {best_score:.3f})")
        results['optimal_size'] = best_balance
        results['recommendations'].append(
            f"Para uso en producción, recomendamos tableros {best_balance}x{best_balance}"
        )
    
    print(f"\n{'='*80}")
    
    return results



def plot_scalability_loglog(summaries: Dict[int, ScalabilitySummary],
                            save_path: str = "scalability_loglog.png"):
    """Genera gráfico log-log de escalabilidad."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    board_sizes = sorted(summaries.keys())
    num_cells = [summaries[bs].num_cells for bs in board_sizes]
    ga_times = [summaries[bs].ga_avg_time for bs in board_sizes]
    ga_times_std = [summaries[bs].ga_std_time for bs in board_sizes]
    fitness_evals = [summaries[bs].ga_avg_fitness_evals for bs in board_sizes]
    
    # Gráfico 1: Tiempo vs Tamaño (log-log)
    ax1.errorbar(num_cells, ga_times, yerr=ga_times_std, 
                fmt='o-', linewidth=2, markersize=8,
                capsize=5, capthick=2, label='Tiempo GA')
    
    # Añadir línea de referencia (complejidad teórica)
    # Ajuste polinómico para referencia
    if len(num_cells) > 2:
        coeffs = np.polyfit(np.log(num_cells), np.log(ga_times), 1)
        fit_times = np.exp(coeffs[1]) * np.array(num_cells) ** coeffs[0]
        ax1.plot(num_cells, fit_times, '--', alpha=0.5, 
                label=f'Ajuste: O(n^{coeffs[0]:.2f})')
    
    ax1.set_xlabel('Número de celdas (N²)', fontsize=12)
    ax1.set_ylabel('Tiempo promedio (segundos)', fontsize=12)
    ax1.set_title('Escalabilidad del Tiempo de Ejecución', fontsize=14, fontweight='bold')
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    ax1.grid(True, alpha=0.3, which='both')
    ax1.legend(fontsize=10)
    
    # Añadir etiquetas de tamaño
    for bs, nc, t in zip(board_sizes, num_cells, ga_times):
        ax1.annotate(f'{bs}x{bs}', (nc, t), 
                    textcoords="offset points", xytext=(0,10),
                    ha='center', fontsize=8, alpha=0.7)
    
    # Gráfico 2: Evaluaciones vs Tamaño (log-log)
    ax2.plot(num_cells, fitness_evals, 'o-', linewidth=2, markersize=8,
            color='orange', label='Evaluaciones de Fitness')
    
    ax2.set_xlabel('Número de celdas (N²)', fontsize=12)
    ax2.set_ylabel('Evaluaciones de fitness promedio', fontsize=12)
    ax2.set_title('Evaluaciones de Fitness por Tamaño', fontsize=14, fontweight='bold')
    ax2.set_xscale('log')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3, which='both')
    ax2.legend(fontsize=10)
    
    # Añadir etiquetas
    for bs, nc, fe in zip(board_sizes, num_cells, fitness_evals):
        ax2.annotate(f'{bs}x{bs}', (nc, fe), 
                    textcoords="offset points", xytext=(0,10),
                    ha='center', fontsize=8, alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\n📈 Gráfico log-log guardado en: {save_path}")
    plt.show()


def plot_efficiency_metrics(summaries: Dict[int, ScalabilitySummary],
                           save_path: str = "efficiency_metrics.png"):
    """Genera gráficos de métricas de eficiencia."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    board_sizes = sorted(summaries.keys())
    labels = [f"{bs}x{bs}" for bs in board_sizes]
    
    # Gráfico 1: Tasa de éxito
    success_rates = [summaries[bs].ga_success_rate * 100 for bs in board_sizes]
    axes[0, 0].bar(labels, success_rates, color='green', alpha=0.7)
    axes[0, 0].axhline(y=50, color='r', linestyle='--', alpha=0.5, label='Umbral 50%')
    axes[0, 0].set_ylabel('Tasa de éxito GA (%)', fontsize=11)
    axes[0, 0].set_title('Tasa de Éxito del GA', fontsize=12, fontweight='bold')
    axes[0, 0].set_ylim(0, 105)
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3, axis='y')
    
    # Gráfico 2: Uso de Backtracking
    bt_rates = [summaries[bs].bt_usage_rate * 100 for bs in board_sizes]
    axes[0, 1].bar(labels, bt_rates, color='orange', alpha=0.7)
    axes[0, 1].set_ylabel('Uso de Backtracking (%)', fontsize=11)
    axes[0, 1].set_title('Necesidad de Backtracking', fontsize=12, fontweight='bold')
    axes[0, 1].set_ylim(0, 105)
    axes[0, 1].grid(True, alpha=0.3, axis='y')
    
    # Gráfico 3: Tasa de óptimos locales
    local_opt_rates = [summaries[bs].local_optima_rate * 100 for bs in board_sizes]
    axes[1, 0].bar(labels, local_opt_rates, color='red', alpha=0.7)
    axes[1, 0].axhline(y=30, color='darkred', linestyle='--', alpha=0.5, label='Umbral 30%')
    axes[1, 0].set_ylabel('Óptimos locales (%)', fontsize=11)
    axes[1, 0].set_title('Convergencia a Óptimos Locales', fontsize=12, fontweight='bold')
    axes[1, 0].set_ylim(0, 105)
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    
    # Gráfico 4: Score de eficiencia
    efficiency_scores = [summaries[bs].efficiency_score for bs in board_sizes]
    axes[1, 1].bar(labels, efficiency_scores, color='blue', alpha=0.7)
    axes[1, 1].axhline(y=0.3, color='r', linestyle='--', alpha=0.5, label='Umbral 0.3')
    axes[1, 1].set_ylabel('Score de eficiencia', fontsize=11)
    axes[1, 1].set_title('Score de Eficiencia Global', fontsize=12, fontweight='bold')
    axes[1, 1].set_ylim(0, 1.05)
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"📊 Gráficos de eficiencia guardados en: {save_path}")
    plt.show()


def run_complete_scalability_study(
    board_sizes: List[int] = [4, 5, 6, 7],
    colors_config: Optional[Dict[int, int]] = None,
    runs_per_size: int = 10,
    output_dir: str = "scalability_results"
):
    """Ejecuta el estudio completo de escalabilidad."""
    
    if colors_config is None:
        # Configuración por defecto basada en reglas prácticas
        colors_config = {
            4: 3,  # 4x4 = 16 celdas, 3 colores
            5: 4,  # 5x5 = 25 celdas, 4 colores
            6: 6,  # 6x6 = 36 celdas, 6 colores
            7: 8,  # 7x7 = 49 celdas, 8 colores
            8: 10, # 8x8 = 64 celdas, 10 colores (opcional)
        }
    
    # Crear directorio de salida
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Ejecutar experimentos
    results = run_scalability_experiments(
        board_sizes=board_sizes,
        colors_config=colors_config,
        runs_per_size=runs_per_size,
        verbose=False
    )
    
    # Calcular estadísticas
    summaries = calculate_summary_statistics(results)
    
    # Mostrar tabla resumen
    print_summary_table(summaries)
    
    # Identificar umbral de ineficiencia
    inefficiency_point = identify_inefficiency_threshold(summaries)
    
    # Identificar límites prácticos de uso
    practical_limits = identify_practical_limits(
        summaries,
        max_time_ga=60.0,
        max_time_hybrid=120.0,
        min_success_ga=0.5,
        min_success_hybrid=0.8
    )
    
    # Exportar resultados
    csv_path = os.path.join(output_dir, "scalability_results.csv")
    json_path = os.path.join(output_dir, "scalability_summary.json")
    
    export_results_to_csv(results, csv_path)
    export_summary_to_json(summaries, json_path)
    
    # Generar visualizaciones
    loglog_path = os.path.join(output_dir, "scalability_loglog.png")
    efficiency_path = os.path.join(output_dir, "efficiency_metrics.png")
    
    plot_scalability_loglog(summaries, loglog_path)
    plot_efficiency_metrics(summaries, efficiency_path)
    
    # Resumen final
    print("\n" + "="*80)
    print("✅ ESTUDIO DE ESCALABILIDAD COMPLETADO")
    print("="*80)
    print(f"📁 Resultados guardados en: {output_dir}/")
    print(f"   • {csv_path}")
    print(f"   • {json_path}")
    print(f"   • {loglog_path}")
    print(f"   • {efficiency_path}")
    
    if inefficiency_point:
        print(f"\n⚠️  Punto crítico detectado en tableros {inefficiency_point}x{inefficiency_point}")
    
    # Guardar reporte de límites prácticos
    limits_path = os.path.join(output_dir, "practical_limits.json")
    with open(limits_path, 'w', encoding='utf-8') as f:
        json.dump(practical_limits, f, indent=2, ensure_ascii=False)
    print(f"\n📋 Análisis de límites prácticos guardado en: {limits_path}")
    
    return results, summaries, inefficiency_point, practical_limits


if __name__ == "__main__":
    # Estudio completo con configuración por defecto
    run_complete_scalability_study(
        board_sizes=[4, 5, 6, 7],
        runs_per_size=10,
        output_dir="scalability_results"
    )
