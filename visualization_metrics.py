# Módulo para visualización de métricas del algoritmo genético
import os
from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np

try:
    from .metrics import GAMetrics
except ImportError:
    from metrics import GAMetrics

def plot_fitness_evolution(metrics: GAMetrics, save_path: Optional[str] = None):
    """Gráfica la evolución del fitness a lo largo de las generaciones."""
    plt.figure(figsize=(12, 6))
    
    generations = range(1, len(metrics.fitness_evolution) + 1)
    
    plt.subplot(1, 2, 1)
    plt.plot(generations, metrics.fitness_evolution, 'b-', linewidth=2, label='Mejor Fitness')
    
    # Añadir líneas de referencia importantes
    if metrics.generations_to_solution:
        plt.axvline(x=metrics.generations_to_solution, color='g', linestyle='--', 
                   label=f'Solución (Gen {metrics.generations_to_solution})')
    
    if metrics.convergence_generation:
        plt.axvline(x=metrics.convergence_generation, color='r', linestyle='--', 
                   label=f'Convergencia (Gen {metrics.convergence_generation})')
    
    plt.xlabel('Generación')
    plt.ylabel('Fitness')
    plt.title('Evolución del Fitness')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Gráfica de diversidad
    plt.subplot(1, 2, 2)
    plt.plot(generations, metrics.diversity_evolution, 'r-', linewidth=2, label='Diversidad')
    plt.xlabel('Generación')
    plt.ylabel('Diversidad')
    plt.title('Evolución de la Diversidad')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📈 Gráfica guardada en: {save_path}")
    
    plt.show()

def plot_generation_metrics(metrics: GAMetrics, save_path: Optional[str] = None):
    """Gráfica métricas detalladas por generación."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    generations = range(1, len(metrics.generation_metrics) + 1)
    
    # Fitness estadísticas
    best_fitness = [gm.best_fitness for gm in metrics.generation_metrics]
    avg_fitness = [gm.avg_fitness for gm in metrics.generation_metrics]
    worst_fitness = [gm.worst_fitness for gm in metrics.generation_metrics]
    
    axes[0, 0].plot(generations, best_fitness, 'g-', label='Mejor', linewidth=2)
    axes[0, 0].plot(generations, avg_fitness, 'b-', label='Promedio', linewidth=2)
    axes[0, 0].plot(generations, worst_fitness, 'r-', label='Peor', linewidth=2)
    axes[0, 0].set_xlabel('Generación')
    axes[0, 0].set_ylabel('Fitness')
    axes[0, 0].set_title('Estadísticas de Fitness por Generación')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Diversidad y convergencia
    diversity = [gm.diversity_score for gm in metrics.generation_metrics]
    convergence = [gm.convergence_rate for gm in metrics.generation_metrics]
    
    axes[0, 1].plot(generations, diversity, 'purple', label='Diversidad', linewidth=2)
    axes[0, 1].set_xlabel('Generación')
    axes[0, 1].set_ylabel('Diversidad')
    axes[0, 1].set_title('Diversidad de la Población')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Tasa de convergencia
    axes[1, 0].plot(generations, convergence, 'orange', label='Convergencia', linewidth=2)
    axes[1, 0].set_xlabel('Generación')
    axes[1, 0].set_ylabel('Tasa de Convergencia')
    axes[1, 0].set_title('Tasa de Convergencia')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Soluciones perfectas
    perfect_solutions = [gm.perfect_solutions for gm in metrics.generation_metrics]
    axes[1, 1].plot(generations, perfect_solutions, 'brown', label='Perfectas', linewidth=2)
    axes[1, 1].set_xlabel('Generación')
    axes[1, 1].set_ylabel('Número de Soluciones Perfectas')
    axes[1, 1].set_title('Soluciones Perfectas en la Población')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 Gráfica detallada guardada en: {save_path}")
    
    plt.show()

def create_metrics_dashboard(metrics: GAMetrics, save_dir: str = "metrics_output"):
    """Crea un dashboard completo con todas las visualizaciones."""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    config = metrics.get_summary()['configuracion']
    base_name = f"flow_{config['tablero']}_{config['colores']}c"
    
    # Gráfica de evolución
    evolution_path = os.path.join(save_dir, f"{base_name}_evolution.png")
    plot_fitness_evolution(metrics, evolution_path)
    
    # Gráfica detallada
    detailed_path = os.path.join(save_dir, f"{base_name}_detailed.png")
    plot_generation_metrics(metrics, detailed_path)
    
    # Guardar métricas en JSON
    json_path = os.path.join(save_dir, f"{base_name}_metrics.json")
    metrics.export_to_json(json_path)
    
    print(f"\n📁 Dashboard completo guardado en: {save_dir}/")
    return save_dir

def print_comparative_table(metrics_list: List[GAMetrics], labels: List[str]):
    """Imprime una tabla comparativa de múltiples ejecuciones."""
    print("\n" + "="*100)
    print("📋 TABLA COMPARATIVA DE EJECUCIONES")
    print("="*100)
    
    # Encabezados
    print(f"{'Experimento':15} {'Éxito':8} {'Tiempo (s)':12} {'Generaciones':13} {'Fitness Final':15} {'Diversidad':15}")
    print("-" * 100)
    
    for i, (metrics, label) in enumerate(zip(metrics_list, labels)):
        summary = metrics.get_summary()
        perf = summary['rendimiento']
        div = summary['diversidad']
        
        success_icon = "✅" if perf['exito'] else "❌"
        
        print(f"{label:15} {success_icon:8} {perf['tiempo_total']:12.3f} "
              f"{perf['generaciones_ejecutadas']:13} {summary['fitness']['fitness_final']:15.2f} "
              f"{div['diversidad_final']:15.3f}")
    
    print("="*100)
    
    # Estadísticas generales
    total_success = sum(1 for metrics in metrics_list if metrics.get_summary()['rendimiento']['exito'])
    avg_time = sum(metrics.get_summary()['rendimiento']['tiempo_total'] for metrics in metrics_list) / len(metrics_list)
    avg_generations = sum(metrics.get_summary()['rendimiento']['generaciones_ejecutadas'] for metrics in metrics_list) / len(metrics_list)
    
    print(f"\n📊 ESTADÍSTICAS GENERALES:")
    print(f"   • Tasa de éxito: {total_success}/{len(metrics_list)} ({100*total_success/len(metrics_list):.1f}%)")
    print(f"   • Tiempo promedio: {avg_time:.3f} segundos")
    print(f"   • Generaciones promedio: {avg_generations:.1f}")

# Funciones para análisis estadístico
def analyze_convergence_patterns(metrics: GAMetrics):
    """Analiza patrones de convergencia del algoritmo."""
    print("\n🔍 ANÁLISIS DE CONVERGENCIA:")
    
    fitness_evolution = metrics.fitness_evolution
    if len(fitness_evolution) < 10:
        print("   ⚠️  Datos insuficientes para análisis")
        return
    
    # Calcular velocidad de convergencia
    improvements = []
    for i in range(1, len(fitness_evolution)):
        if fitness_evolution[i] > fitness_evolution[i-1]:
            improvements.append(i)
    
    if improvements:
        avg_improvement_gap = sum(improvements[i] - improvements[i-1] 
                                for i in range(1, len(improvements))) / max(1, len(improvements)-1)
        print(f"   • Mejoras cada {avg_improvement_gap:.1f} generaciones en promedio")
        print(f"   • Total de mejoras: {len(improvements)}")
        print(f"   • Última mejora en generación: {max(improvements)}")
    
    # Detectar estancamiento
    stagnation_threshold = max(1, len(fitness_evolution) // 4)
    last_improvement = len(fitness_evolution)
    
    for i in range(len(fitness_evolution)-1, 0, -1):
        if fitness_evolution[i] > fitness_evolution[i-1]:
            last_improvement = i
            break
    
    stagnation_period = len(fitness_evolution) - last_improvement
    if stagnation_period > stagnation_threshold:
        print(f"   ⚠️  Estancamiento detectado: {stagnation_period} generaciones sin mejora")
    else:
        print(f"   ✅ Algoritmo activo hasta el final")

def recommend_parameter_adjustments(metrics: GAMetrics):
    """Recomienda ajustes de parámetros basado en las métricas."""
    print("\n💡 RECOMENDACIONES:")
    
    summary = metrics.get_summary()
    perf = summary['rendimiento']
    div = summary['diversidad']
    
    # Analizar éxito
    if not perf['exito']:
        print("   🔧 Para mejorar el éxito:")
        print("      • Aumentar el número de generaciones")
        print("      • Aumentar el tamaño de la población")
        print("      • Ajustar la tasa de mutación")
    
    # Analizar diversidad
    if div['diversidad_final'] < 0.1:
        print("   🌍 Para mantener más diversidad:")
        print("      • Reducir el tamaño de la elite")
        print("      • Aumentar la tasa de mutación")
        print("      • Considerar esquemas de selección menos agresivos")
    
    # Analizar tiempo
    if perf['tiempo_total'] > 10:
        print("   ⚡ Para mejorar el rendimiento:")
        print("      • Reducir el tamaño de la población")
        print("      • Implementar criterios de parada temprana")
        print("      • Optimizar la función de fitness")
    
    # Analizar convergencia
    if perf['generacion_convergencia'] and perf['generacion_convergencia'] < perf['generaciones_ejecutadas'] * 0.3:
        print("   🎯 Convergencia muy temprana detectada:")
        print("      • Aumentar la diversidad inicial")
        print("      • Reducir la presión selectiva")
        print("      • Implementar reinicio de diversidad")