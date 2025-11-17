"""
Módulo para tuning automático de parámetros del algoritmo genético.
Permite ejecutar experimentos con diferentes configuraciones y comparar resultados.
"""
import csv
import itertools
import json
import os
import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np

try:
    from .backtracking_solver import solve_flow_bt
    from .genetic_algorithm import ga_solve_flow, is_perfect
    from .metrics import GAMetrics
    from .puzzle_generator import generate_random_puzzle
except ImportError:
    from backtracking_solver import solve_flow_bt
    from genetic_algorithm import ga_solve_flow, is_perfect
    from metrics import GAMetrics
    from puzzle_generator import generate_random_puzzle


@dataclass
class ParameterConfig:
    """Configuración de parámetros para el GA."""
    pop_size: int
    generations: int
    mut_rate: float
    elite: int
    tour_k: int
    
    def __str__(self):
        return f"pop{self.pop_size}_gen{self.generations}_mut{self.mut_rate}_elite{self.elite}_tour{self.tour_k}"
    
    def to_dict(self):
        return {
            'pop_size': self.pop_size,
            'generations': self.generations,
            'mut_rate': self.mut_rate,
            'elite': self.elite,
            'tour_k': self.tour_k
        }


@dataclass
class ExperimentResult:
    """Resultado de un experimento con una configuración específica."""
    config: ParameterConfig
    board_size: int
    num_colors: int
    run_number: int
    
    # Métricas GA
    ga_success: bool
    ga_time: float
    generations_executed: int
    generations_to_solution: Optional[int]
    fitness_evals: int
    final_fitness: float
    convergence_generation: Optional[int]
    diversity_loss: float
    avg_fitness: float
    fitness_improvement: float
    
    # Métricas híbridas (GA + BT)
    bt_used: bool = False
    bt_time: float = 0.0
    hybrid_success: bool = False
    hybrid_time: float = 0.0


@dataclass
class ConfigurationSummary:
    """Resumen estadístico de una configuración."""
    config: ParameterConfig
    board_size: int
    num_colors: int
    num_runs: int
    
    # Métricas de éxito
    success_rate: float
    avg_time: float
    std_time: float
    
    # Métricas de convergencia
    avg_generations: float
    avg_generations_to_solution: Optional[float]
    avg_fitness_evals: float
    
    # Métricas de calidad
    avg_final_fitness: float
    avg_fitness_improvement: float
    avg_diversity_loss: float
    
    # Score combinado (para ranking)
    score: float = 0.0
    
    def calculate_score(self, time_weight: float = 0.3, 
                       success_weight: float = 0.5, 
                       efficiency_weight: float = 0.2):
        """
        Calcula un score combinado para ranking.
        
        Score = success_weight * success_rate 
              + time_weight * (1 / (1 + norm_time))
              + efficiency_weight * (1 / (1 + norm_evals))
        """
        # Normalizar tiempo (asumiendo 10s como referencia)
        norm_time = self.avg_time / 10.0
        time_score = 1.0 / (1.0 + norm_time)
        
        # Normalizar evaluaciones (asumiendo 100k como referencia)
        norm_evals = self.avg_fitness_evals / 100000.0
        efficiency_score = 1.0 / (1.0 + norm_evals)
        
        self.score = (success_weight * self.success_rate + 
                     time_weight * time_score + 
                     efficiency_weight * efficiency_score)
        
        return self.score


def run_experiment_with_config(config: ParameterConfig,
                               board_size: int,
                               num_colors: int,
                               run_number: int = 1,
                               use_hybrid: bool = True,
                               verbose: bool = False) -> ExperimentResult:
    """
    Ejecuta un experimento con una configuración específica.
    
    Args:
        config: Configuración de parámetros del GA
        board_size: Tamaño del tablero
        num_colors: Número de colores
        run_number: Número de corrida
        use_hybrid: Si True, usa backtracking cuando GA falla
        verbose: Mostrar progreso detallado
    """
    
    # Generar puzzle
    terminals = generate_random_puzzle(board_size, num_colors)
    
    # Ejecutar GA
    ga_start_time = time.time()
    solution, metrics = ga_solve_flow(
        board_size, terminals,
        pop_size=config.pop_size,
        generations=config.generations,
        mut_rate=config.mut_rate,
        elite=config.elite,
        tour_k=config.tour_k,
        verbose=verbose,
        collect_metrics=True
    )
    ga_elapsed_time = time.time() - ga_start_time
    
    # Extraer métricas GA
    summary = metrics.get_summary()
    perf = summary['rendimiento']
    fitness = summary['fitness']
    div = summary['diversidad']
    
    ga_success = perf['exito']
    
    # Inicializar métricas híbridas
    bt_used = False
    bt_time = 0.0
    hybrid_success = ga_success
    
    # Si GA falló y se permite híbrido, intentar con Backtracking
    if not ga_success and use_hybrid:
        bt_start = time.time()
        solution_bt = solve_flow_bt(board_size, terminals, start_grid=solution)
        bt_time = time.time() - bt_start
        
        if solution_bt and is_perfect(solution_bt, terminals):
            bt_used = True
            hybrid_success = True
            solution = solution_bt  # Actualizar solución
    
    hybrid_time = ga_elapsed_time + bt_time
    
    return ExperimentResult(
        config=config,
        board_size=board_size,
        num_colors=num_colors,
        run_number=run_number,
        ga_success=ga_success,
        ga_time=ga_elapsed_time,
        generations_executed=perf['generaciones_ejecutadas'],
        generations_to_solution=perf['generaciones_hasta_solucion'],
        fitness_evals=perf['evaluaciones_fitness'],
        final_fitness=fitness['fitness_final'],
        convergence_generation=perf['generacion_convergencia'],
        diversity_loss=div['perdida_diversidad'],
        avg_fitness=fitness['fitness_promedio'],
        fitness_improvement=fitness['mejora_total'],
        bt_used=bt_used,
        bt_time=bt_time,
        hybrid_success=hybrid_success,
        hybrid_time=hybrid_time
    )


def grid_search(param_space: Dict[str, List[Any]],
               board_size: int,
               num_colors: int,
               runs_per_config: int = 5,
               verbose: bool = False) -> List[ExperimentResult]:
    """
    Ejecuta grid search sobre el espacio de parámetros.
    
    Args:
        param_space: Diccionario con listas de valores para cada parámetro
                    Ejemplo: {
                        'pop_size': [100, 200, 300],
                        'generations': [500, 1000],
                        'mut_rate': [0.01, 0.03, 0.05],
                        'elite': [0, 2, 5],
                        'tour_k': [2, 3, 5]
                    }
        board_size: Tamaño del tablero
        num_colors: Número de colores
        runs_per_config: Corridas por configuración para promediar
        verbose: Mostrar progreso detallado
    
    Returns:
        Lista con todos los resultados de experimentos
    """
    
    # Generar todas las combinaciones
    keys = sorted(param_space.keys())
    values = [param_space[k] for k in keys]
    combinations = list(itertools.product(*values))
    
    total_experiments = len(combinations) * runs_per_config
    
    print("\n" + "="*80)
    print("🔍 GRID SEARCH DE PARÁMETROS")
    print("="*80)
    print(f"Tablero: {board_size}x{board_size}, Colores: {num_colors}")
    print(f"Configuraciones a probar: {len(combinations)}")
    print(f"Corridas por configuración: {runs_per_config}")
    print(f"Total de experimentos: {total_experiments}")
    print("="*80 + "\n")
    
    results = []
    experiment_count = 0
    
    for combo_idx, combo in enumerate(combinations, 1):
        # Crear configuración
        param_dict = dict(zip(keys, combo))
        config = ParameterConfig(**param_dict)
        
        # Calcular progreso global
        global_progress = ((combo_idx - 1) / len(combinations)) * 100
        bar_length = 50
        filled = int(bar_length * (combo_idx - 1) / len(combinations))
        global_bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\n{'='*80}")
        print(f"[{global_bar}] {global_progress:5.1f}%")
        print(f"CONFIGURACIÓN [{combo_idx}/{len(combinations)}]")
        print(f"{'='*80}")
        print(f"Pop: {config.pop_size} | Gen: {config.generations} | Mut: {config.mut_rate} | "
              f"Elite: {config.elite} | Tour: {config.tour_k}")
        print(f"{'='*80}")
        
        for run in range(1, runs_per_config + 1):
            experiment_count += 1
            
            # Progreso dentro de la configuración
            run_progress = (run / runs_per_config) * 100
            run_bar_length = 20
            run_filled = int(run_bar_length * run / runs_per_config)
            run_bar = '█' * run_filled + '░' * (run_bar_length - run_filled)
            
            print(f"  [{run_bar}] Run {run}/{runs_per_config} ({run_progress:4.0f}%)...", end=" ", flush=True)
            
            try:
                result = run_experiment_with_config(
                    config, board_size, num_colors, run, verbose
                )
                results.append(result)
                
                # Mostrar resultado breve
                status = "✅" if result.ga_success else "❌"
                print(f"{status} | {result.ga_time:.2f}s | {result.generations_executed} gen | "
                      f"fitness: {result.final_fitness:.1f}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
        
        # Resumen parcial de esta configuración
        config_results = [r for r in results if r.config == config]
        if config_results:
            success_rate = sum(1 for r in config_results if r.ga_success) / len(config_results)
            avg_time = statistics.mean(r.ga_time for r in config_results)
            avg_gens = statistics.mean(r.generations_executed for r in config_results)
            
            # Determinar estado visual
            if success_rate >= 0.8:
                status_icon = "✅ EXCELENTE"
                status_color = ""
            elif success_rate >= 0.5:
                status_icon = "✔️  BUENO"
                status_color = ""
            elif success_rate >= 0.3:
                status_icon = "⚠️  REGULAR"
                status_color = ""
            else:
                status_icon = "❌ POBRE"
                status_color = ""
            
            print(f"\n  {'─'*76}")
            print(f"  📊 RESUMEN CONFIGURACIÓN: {status_icon}")
            print(f"  {'─'*76}")
            print(f"  • Tasa de éxito: {success_rate*100:5.1f}%")
            print(f"  • Tiempo promedio: {avg_time:6.3f}s")
            print(f"  • Generaciones promedio: {avg_gens:6.1f}")
            print(f"  {'─'*76}")
    
    return results


def summarize_results(results: List[ExperimentResult]) -> Dict[str, ConfigurationSummary]:
    """Agrupa y resume resultados por configuración."""
    
    # Agrupar por configuración
    grouped = {}
    for result in results:
        config_str = str(result.config)
        if config_str not in grouped:
            grouped[config_str] = []
        grouped[config_str].append(result)
    
    # Calcular estadísticas por configuración
    summaries = {}
    
    for config_str, config_results in grouped.items():
        config = config_results[0].config
        board_size = config_results[0].board_size
        num_colors = config_results[0].num_colors
        num_runs = len(config_results)
        
        # Métricas de éxito
        successes = [r for r in config_results if r.ga_success]
        success_rate = len(successes) / num_runs
        
        times = [r.ga_time for r in config_results]
        avg_time = statistics.mean(times)
        std_time = statistics.stdev(times) if num_runs > 1 else 0.0
        
        # Métricas de convergencia
        avg_generations = statistics.mean(r.generations_executed for r in config_results)
        
        gens_to_sol = [r.generations_to_solution for r in successes if r.generations_to_solution]
        avg_gens_to_sol = statistics.mean(gens_to_sol) if gens_to_sol else None
        
        avg_fitness_evals = statistics.mean(r.fitness_evals for r in config_results)
        
        # Métricas de calidad
        avg_final_fitness = statistics.mean(r.final_fitness for r in config_results)
        avg_fitness_improvement = statistics.mean(r.fitness_improvement for r in config_results)
        avg_diversity_loss = statistics.mean(r.diversity_loss for r in config_results)
        
        summary = ConfigurationSummary(
            config=config,
            board_size=board_size,
            num_colors=num_colors,
            num_runs=num_runs,
            success_rate=success_rate,
            avg_time=avg_time,
            std_time=std_time,
            avg_generations=avg_generations,
            avg_generations_to_solution=avg_gens_to_sol,
            avg_fitness_evals=avg_fitness_evals,
            avg_final_fitness=avg_final_fitness,
            avg_fitness_improvement=avg_fitness_improvement,
            avg_diversity_loss=avg_diversity_loss
        )
        
        summary.calculate_score()
        summaries[config_str] = summary
    
    return summaries


def print_ranking_table(summaries: Dict[str, ConfigurationSummary], top_n: int = 10):
    """Imprime una tabla con las mejores configuraciones."""
    
    # Ordenar por score
    ranked = sorted(summaries.values(), key=lambda s: s.score, reverse=True)
    
    print("\n" + "="*150)
    print(f"{'🏆 RANKING DE CONFIGURACIONES':^150}")
    print(f"{'Top ' + str(min(top_n, len(ranked))) + ' mejores configuraciones':^150}")
    print("="*150)
    
    # Encabezados más claros con emojis
    print(f"{'':^5} {'👥':^6} {'🔄':^7} {'🎲':^10} {'⭐':^7} {'🎯':^7} "
          f"{'✅ Éxito':^12} {'⏱️ Tiempo':^12} {'📊 Evals':^12} {'🏅 Score':^10}")
    print(f"{'Rank':^5} {'Pop':^6} {'Gen':^7} {'MutRate':^10} {'Elite':^7} {'TourK':^7} "
          f"{'(%)':^12} {'(seg)':^12} {'(miles)':^12} {'(0-1)':^10}")
    print("-" * 150)
    
    for rank, summary in enumerate(ranked[:top_n], 1):
        config = summary.config
        
        # Determinar medalla/emoji según ranking
        if rank == 1:
            medal = "🥇"
        elif rank == 2:
            medal = "🥈"
        elif rank == 3:
            medal = "🥉"
        elif rank <= 5:
            medal = "⭐"
        else:
            medal = "  "
        
        # Color de fondo según tasa de éxito
        if summary.success_rate >= 0.95:
            status = "✅"
        elif summary.success_rate >= 0.80:
            status = "✔️ "
        elif summary.success_rate >= 0.50:
            status = "⚠️ "
        else:
            status = "❌"
        
        # Formatear evaluaciones en miles
        evals_k = summary.avg_fitness_evals / 1000
        
        print(f"{medal}{rank:3} {config.pop_size:6} {config.generations:7} "
              f"{config.mut_rate:10.4f} {config.elite:7} {config.tour_k:7} "
              f"{status} {summary.success_rate*100:7.1f}% {summary.avg_time:9.3f}s "
              f"{evals_k:10.1f}k {summary.score:10.4f}")
    
    print("="*150)
    
    # Mostrar mejor configuración con más detalles
    if ranked:
        best = ranked[0]
        print(f"\n{'🎯 MEJOR CONFIGURACIÓN ENCONTRADA':^150}")
        print("="*150)
        print(f"  {'Parámetros':30} {'Valor':20} {'Métrica Adicional':30} {'Valor':20}")
        print("-"*150)
        print(f"  {'👥 Tamaño de Población':30} {best.config.pop_size:20} {'📈 Fitness Final':30} {best.avg_final_fitness:20.2f}")
        print(f"  {'🔄 Generaciones':30} {best.config.generations:20} {'📊 Mejora Fitness':30} {best.avg_fitness_improvement:20.2f}")
        print(f"  {'🎲 Tasa de Mutación':30} {best.config.mut_rate:20.4f} {'🔀 Pérdida Diversidad':30} {best.avg_diversity_loss:20.4f}")
        print(f"  {'⭐ Elitismo':30} {best.config.elite:20} {'🎯 Generaciones usadas':30} {best.avg_generations:20.1f}")
        print(f"  {'🎯 Tamaño Torneo':30} {best.config.tour_k:20} {'⚡ Evaluaciones Totales':30} {int(best.avg_fitness_evals):20,}")
        print("-"*150)
        print(f"  {'✅ Tasa de Éxito':30} {best.success_rate*100:19.1f}% {'⏱️  Tiempo Promedio':30} {best.avg_time:19.3f}s")
        print(f"  {'🏅 Score Global':30} {best.score:20.4f} {'📊 Desviación Tiempo':30} {best.std_time:19.3f}s")
        print("="*150)
        
        # Recomendaciones basadas en los resultados
        print(f"\n💡 RECOMENDACIONES:")
        if best.success_rate < 0.9:
            print(f"  • ⚠️  Tasa de éxito baja ({best.success_rate*100:.1f}%). Considera aumentar población o generaciones")
        if best.avg_time > 1.0:
            print(f"  • ⏱️  Tiempo alto ({best.avg_time:.2f}s). Considera reducir evaluaciones o población")
        if best.avg_diversity_loss > 0.8:
            print(f"  • 🔀 Alta pérdida de diversidad ({best.avg_diversity_loss:.2f}). Aumenta mutación o reduce elite")
        if best.config.elite == 0:
            print(f"  • ⭐ Sin elitismo. Considera usar elite=1 o 2 para preservar mejores soluciones")
        if best.success_rate >= 0.95 and best.avg_time < 0.5:
            print(f"  • 🎉 ¡Excelente configuración! Balance óptimo entre éxito y velocidad")
        print()


def save_ranking_table_as_image(summaries: Dict[str, ConfigurationSummary], 
                                board_size: int,
                                num_colors: int,
                                save_path: str,
                                top_n: int = 15):
    """
    Guarda la tabla de ranking como una imagen PNG.
    
    Args:
        summaries: Diccionario de resúmenes de configuraciones
        board_size: Tamaño del tablero
        num_colors: Número de colores
        save_path: Ruta donde guardar la imagen
        top_n: Número de configuraciones a mostrar
    """
    
    # Crear directorio si no existe
    import os
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # Ordenar por score
    ranked = sorted(summaries.values(), key=lambda s: s.score, reverse=True)
    ranked = ranked[:top_n]
    
    # Preparar datos para la tabla (SIN EMOJIS para evitar problemas de fuentes)
    table_data = []
    for rank, summary in enumerate(ranked, 1):
        config = summary.config
        
        row = [
            f"#{rank}",  # Sin emojis, solo números
            config.pop_size,
            config.generations,
            f"{config.mut_rate:.3f}",
            config.elite,
            config.tour_k,
            f"{summary.success_rate*100:.1f}%",
            f"{summary.avg_time:.3f}s",
            f"{int(summary.avg_fitness_evals)}",
            f"{summary.score:.3f}"
        ]
        table_data.append(row)
    
    # Crear figura
    fig = plt.figure(figsize=(16, max(8, len(table_data) * 0.4 + 2)))
    ax = fig.add_subplot(111)
    ax.axis('tight')
    ax.axis('off')
    
    # Título (sin emojis)
    title = f"RANKING DE CONFIGURACIONES (Top {len(ranked)})\n"
    title += f"Tablero: {board_size}x{board_size} | Colores: {num_colors}"
    ax.text(0.5, 0.98, title, 
            ha='center', va='top', 
            fontsize=16, fontweight='bold',
            transform=ax.transAxes)
    
    # Encabezados
    col_labels = ['Rank', 'Pop', 'Gen', 'MutRate', 'Elite', 'TourK', 
                  'Exito%', 'Tiempo', 'FitEvals', 'Score']
    
    # Crear tabla
    table = ax.table(cellText=table_data,
                    colLabels=col_labels,
                    cellLoc='center',
                    loc='center',
                    bbox=[0.05, 0.05, 0.9, 0.88])
    
    # Estilizar tabla
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.8)
    
    # Estilizar encabezados
    for j in range(len(col_labels)):
        cell = table[(0, j)]
        cell.set_facecolor('#4CAF50')
        cell.set_text_props(weight='bold', color='white', fontsize=10)
    
    # Estilizar filas (alternar colores)
    for i in range(1, len(table_data) + 1):
        for j in range(len(col_labels)):
            cell = table[(i, j)]
            if i <= 3:  # Top 3
                cell.set_facecolor('#FFD700')  # Dorado para top 3
                cell.set_text_props(weight='bold')
            elif i % 2 == 0:
                cell.set_facecolor('#F5F5F5')  # Gris claro
            else:
                cell.set_facecolor('white')
    
    # Guardar con manejo de errores
    try:
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        print(f"📊 Tabla de ranking guardada en: {save_path}")
    except Exception as e:
        print(f"⚠️  Error al guardar tabla de ranking: {e}")
        plt.close(fig)


def export_tuning_results(results: List[ExperimentResult],
                         summaries: Dict[str, ConfigurationSummary],
                         output_dir: str = "tuning_results"):
    """Exporta resultados del tuning a archivos."""
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Exportar resultados detallados a CSV
    csv_path = os.path.join(output_dir, "tuning_detailed_results.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'config_id', 'pop_size', 'generations', 'mut_rate', 'elite', 'tour_k',
            'board_size', 'num_colors', 'run_number', 'success', 'time',
            'generations_executed', 'generations_to_solution', 'fitness_evals',
            'final_fitness', 'fitness_improvement', 'diversity_loss'
        ])
        
        for result in results:
            writer.writerow([
                str(result.config),
                result.config.pop_size,
                result.config.generations,
                f"{result.config.mut_rate:.4f}",
                result.config.elite,
                result.config.tour_k,
                result.board_size,
                result.num_colors,
                result.run_number,
                result.ga_success,
                f"{result.ga_time:.4f}",
                result.generations_executed,
                result.generations_to_solution or '',
                result.fitness_evals,
                f"{result.final_fitness:.2f}",
                f"{result.fitness_improvement:.2f}",
                f"{result.diversity_loss:.4f}"
            ])
    
    print(f"\n📄 Resultados detallados guardados en: {csv_path}")
    
    # Exportar resumen a JSON
    json_path = os.path.join(output_dir, "tuning_summary.json")
    summary_data = {}
    
    # Ordenar por score
    ranked = sorted(summaries.values(), key=lambda s: s.score, reverse=True)
    
    for rank, summary in enumerate(ranked, 1):
        config_id = str(summary.config)
        summary_data[config_id] = {
            'rank': rank,
            'config': summary.config.to_dict(),
            'board_size': f"{summary.board_size}x{summary.board_size}",
            'num_colors': summary.num_colors,
            'num_runs': summary.num_runs,
            'success_rate': f"{summary.success_rate*100:.1f}%",
            'avg_time': f"{summary.avg_time:.3f}s",
            'std_time': f"{summary.std_time:.3f}s",
            'avg_generations': f"{summary.avg_generations:.1f}",
            'avg_generations_to_solution': f"{summary.avg_generations_to_solution:.1f}" if summary.avg_generations_to_solution else "N/A",
            'avg_fitness_evals': f"{summary.avg_fitness_evals:.0f}",
            'avg_final_fitness': f"{summary.avg_final_fitness:.2f}",
            'avg_fitness_improvement': f"{summary.avg_fitness_improvement:.2f}",
            'avg_diversity_loss': f"{summary.avg_diversity_loss:.3f}",
            'score': f"{summary.score:.3f}"
        }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    print(f"📊 Resumen guardado en: {json_path}")


def plot_parameter_impact(summaries: Dict[str, ConfigurationSummary],
                         param_name: str,
                         save_path: Optional[str] = None):
    """
    Genera gráficos del impacto de un parámetro específico.
    
    Args:
        summaries: Diccionario de resúmenes
        param_name: Nombre del parámetro ('pop_size', 'mut_rate', etc.)
        save_path: Ruta para guardar la imagen
    """
    
    # Agrupar por valor del parámetro
    param_values = {}
    
    for summary in summaries.values():
        param_val = getattr(summary.config, param_name)
        if param_val not in param_values:
            param_values[param_val] = []
        param_values[param_val].append(summary)
    
    # Calcular promedios por valor
    sorted_values = sorted(param_values.keys())
    success_rates = []
    avg_times = []
    avg_evals = []
    scores = []
    
    for val in sorted_values:
        summaries_list = param_values[val]
        success_rates.append(statistics.mean(s.success_rate for s in summaries_list))
        avg_times.append(statistics.mean(s.avg_time for s in summaries_list))
        avg_evals.append(statistics.mean(s.avg_fitness_evals for s in summaries_list))
        scores.append(statistics.mean(s.score for s in summaries_list))
    
    # Crear gráficos
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Tasa de éxito
    axes[0, 0].plot(sorted_values, [sr * 100 for sr in success_rates], 
                   'o-', linewidth=2, markersize=8, color='green')
    axes[0, 0].set_xlabel(param_name, fontsize=11)
    axes[0, 0].set_ylabel('Tasa de éxito (%)', fontsize=11)
    axes[0, 0].set_title(f'Impacto de {param_name} en Tasa de Éxito', 
                        fontsize=12, fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].set_ylim(0, 105)
    
    # Tiempo promedio
    axes[0, 1].plot(sorted_values, avg_times, 
                   'o-', linewidth=2, markersize=8, color='blue')
    axes[0, 1].set_xlabel(param_name, fontsize=11)
    axes[0, 1].set_ylabel('Tiempo promedio (s)', fontsize=11)
    axes[0, 1].set_title(f'Impacto de {param_name} en Tiempo de Ejecución', 
                        fontsize=12, fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Evaluaciones de fitness
    axes[1, 0].plot(sorted_values, avg_evals, 
                   'o-', linewidth=2, markersize=8, color='orange')
    axes[1, 0].set_xlabel(param_name, fontsize=11)
    axes[1, 0].set_ylabel('Evaluaciones de fitness', fontsize=11)
    axes[1, 0].set_title(f'Impacto de {param_name} en Evaluaciones', 
                        fontsize=12, fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Score combinado
    axes[1, 1].plot(sorted_values, scores, 
                   'o-', linewidth=2, markersize=8, color='purple')
    axes[1, 1].set_xlabel(param_name, fontsize=11)
    axes[1, 1].set_ylabel('Score', fontsize=11)
    axes[1, 1].set_title(f'Impacto de {param_name} en Score Global', 
                        fontsize=12, fontweight='bold')
    axes[1, 1].grid(True, alpha=0.3)
    
    # Marcar el mejor valor
    best_idx = scores.index(max(scores))
    best_val = sorted_values[best_idx]
    for ax in axes.flat:
        ax.axvline(x=best_val, color='red', linestyle='--', 
                  alpha=0.5, label=f'Mejor: {best_val}')
        ax.legend()
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 Gráfico de impacto guardado en: {save_path}")
    
    plt.show()


def plot_comparative_heatmap(summaries: Dict[str, ConfigurationSummary],
                            param1: str, param2: str,
                            metric: str = 'success_rate',
                            save_path: Optional[str] = None):
    """
    Genera un heatmap comparando dos parámetros.
    
    Args:
        summaries: Diccionario de resúmenes
        param1: Primer parámetro (eje X)
        param2: Segundo parámetro (eje Y)
        metric: Métrica a visualizar ('success_rate', 'avg_time', 'score')
        save_path: Ruta para guardar
    """
    
    # Recopilar datos
    data_dict = {}
    
    for summary in summaries.values():
        val1 = getattr(summary.config, param1)
        val2 = getattr(summary.config, param2)
        metric_val = getattr(summary, metric)
        
        if metric == 'success_rate':
            metric_val *= 100  # Convertir a porcentaje
        
        if val1 not in data_dict:
            data_dict[val1] = {}
        
        if val2 not in data_dict[val1]:
            data_dict[val1][val2] = []
        
        data_dict[val1][val2].append(metric_val)
    
    # Promediar si hay múltiples valores
    for val1 in data_dict:
        for val2 in data_dict[val1]:
            data_dict[val1][val2] = statistics.mean(data_dict[val1][val2])
    
    # Crear matriz para heatmap
    values1 = sorted(data_dict.keys())
    all_values2 = set()
    for val1 in values1:
        all_values2.update(data_dict[val1].keys())
    values2 = sorted(all_values2)
    
    matrix = np.zeros((len(values2), len(values1)))
    
    for i, val1 in enumerate(values1):
        for j, val2 in enumerate(values2):
            if val2 in data_dict[val1]:
                matrix[j, i] = data_dict[val1][val2]
            else:
                matrix[j, i] = np.nan
    
    # Crear heatmap
    plt.figure(figsize=(12, 8))
    
    im = plt.imshow(matrix, aspect='auto', cmap='RdYlGn', interpolation='nearest')
    
    plt.colorbar(im, label=metric.replace('_', ' ').title())
    plt.xticks(range(len(values1)), values1)
    plt.yticks(range(len(values2)), values2)
    plt.xlabel(param1, fontsize=12)
    plt.ylabel(param2, fontsize=12)
    plt.title(f'Heatmap: {param1} vs {param2} ({metric})', 
             fontsize=14, fontweight='bold')
    
    # Añadir valores en las celdas
    for i in range(len(values2)):
        for j in range(len(values1)):
            if not np.isnan(matrix[i, j]):
                text = plt.text(j, i, f'{matrix[i, j]:.1f}',
                              ha="center", va="center", color="black", fontsize=9)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"🔥 Heatmap guardado en: {save_path}")
    
    plt.show()


def quick_tuning_study(board_size: int = 5,
                      num_colors: int = 4,
                      runs_per_config: int = 5,
                      output_dir: str = None):
    """
    Ejecuta un estudio rápido de tuning con configuraciones comunes.
    """
    
    # 🔥 Generar nombre de directorio automáticamente basado en tamaño del tablero
    if output_dir is None:
        output_dir = f"tuning_{board_size}x{board_size}"
    
    print(f"\n📁 Resultados se guardarán en: {output_dir}/")
    
    # 🎯 Espacio de parámetros AMPLIADO para exploración profunda
    # Puedes comentar/descomentar líneas para diferentes estudios
    
    # OPCIÓN 1: Grid RÁPIDO (actual) - 4×2×4×3×4 = 384 configs
    param_space = {
        'pop_size': [150, 175, 200, 225, 250],
        'generations': [800, 1000, 1200],
        'mut_rate': [0.02, 0.025, 0.03, 0.035, 0.04],
        'elite': [1, 2, 3],
        'tour_k': [2, 3, 4]
    }
    
    # OPCIÓN 2: Exploración de MUTACIÓN (descomenta para usar)
    # param_space = {
    #     'pop_size': [200],
    #     'generations': [1000],
    #     'mut_rate': [0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.1, 0.15],  # Más valores
    #     'elite': [2],
    #     'tour_k': [3]
    # }
    
    # OPCIÓN 3: Exploración de POBLACIÓN (descomenta para usar)
    # param_space = {
    #     'pop_size': [50, 100, 150, 200, 250, 300, 400, 500],  # Más valores
    #     'generations': [1000],
    #     'mut_rate': [0.03],
    #     'elite': [2],
    #     'tour_k': [3]
    # }
    
    # OPCIÓN 4: Exploración de SELECCIÓN (descomenta para usar)
    # param_space = {
    #     'pop_size': [200],
    #     'generations': [1000],
    #     'mut_rate': [0.03],
    #     'elite': [2],
    #     'tour_k': [1, 2, 3, 4, 5, 7, 10, 15]  # Presión de selección
    # }
    
    # OPCIÓN 5: Exploración de ELITISMO (descomenta para usar)
    # param_space = {
    #     'pop_size': [200],
    #     'generations': [1000],
    #     'mut_rate': [0.03],
    #     'elite': [0, 1, 2, 3, 5, 8, 10, 15, 20],  # Diferentes niveles
    #     'tour_k': [3]
    # }
    
    # OPCIÓN 6: Grid FINO para optimización (descomenta para usar)
    # param_space = {
    #     'pop_size': [150, 175, 200, 225, 250],
    #     'generations': [800, 1000, 1200],
    #     'mut_rate': [0.02, 0.025, 0.03, 0.035, 0.04],
    #     'elite': [1, 2, 3],
    #     'tour_k': [2, 3, 4]
    # }
    
    # Ejecutar grid search
    results = grid_search(
        param_space=param_space,
        board_size=board_size,
        num_colors=num_colors,
        runs_per_config=runs_per_config,
        verbose=False
    )
    
    # Resumir
    summaries = summarize_results(results)
    
    # Mostrar ranking
    print_ranking_table(summaries, top_n=15)
    
    # 🔥 Guardar tabla de ranking como imagen
    save_ranking_table_as_image(summaries, board_size, num_colors, 
                                os.path.join(output_dir, 'ranking_table.png'))
    
    # Exportar
    export_tuning_results(results, summaries, output_dir)
    
    # Visualizaciones
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Impacto de cada parámetro
    for param in ['pop_size', 'mut_rate', 'elite', 'tour_k']:
        save_path = os.path.join(output_dir, f"impact_{param}.png")
        plot_parameter_impact(summaries, param, save_path)
    
    # Heatmaps de interacciones
    plot_comparative_heatmap(summaries, 'pop_size', 'mut_rate', 'success_rate',
                           os.path.join(output_dir, 'heatmap_pop_mut.png'))
    
    plot_comparative_heatmap(summaries, 'elite', 'tour_k', 'score',
                           os.path.join(output_dir, 'heatmap_elite_tour.png'))
    
    print(f"\n✅ Estudio de tuning completado. Resultados en: {output_dir}/")
    
    return results, summaries


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="🎛️  Sistema de Tuning Automático de Parámetros para Flow GA"
    )
    
    parser.add_argument('--board-size', type=int, default=4,
                       help='Tamaño del tablero (default: 4)')
    parser.add_argument('--num-colors', type=int, default=3,
                       help='Número de colores (default: 3)')
    parser.add_argument('--runs', type=int, default=3,
                       help='Corridas por configuración (default: 3)')
    parser.add_argument('--output', type=str, default=None,
                       help='Directorio de salida (default: tuning_NxN)')
    
    args = parser.parse_args()
    
    print("🎛️  SISTEMA DE TUNING AUTOMÁTICO DE PARÁMETROS")
    print("="*80)
    
    quick_tuning_study(
        board_size=args.board_size,
        num_colors=args.num_colors,
        runs_per_config=args.runs,
        output_dir=args.output
    )
