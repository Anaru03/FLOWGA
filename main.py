# Programa principal - Resuelve puzzles Flow con AG y Backtracking
from typing import Dict, List, Tuple

try:
    # Importaciones relativas (cuando se usa como paquete)
    from .backtracking_solver import solve_flow_bt
    from .config import Fore, Style
    from .genetic_algorithm import ga_solve_flow, is_perfect
    from .metrics import GAMetrics
    from .puzzle_generator import generate_random_puzzle
    from .utils import Color, Coord
    from .visualization import print_grid_color
    from .visualization_metrics import (analyze_convergence_patterns,
                                        create_metrics_dashboard,
                                        plot_fitness_evolution,
                                        plot_generation_metrics,
                                        recommend_parameter_adjustments)
    HAS_VISUALIZATION = True
except ImportError:
    # Importaciones absolutas (cuando se ejecuta directamente)
    from backtracking_solver import solve_flow_bt
    from config import Fore, Style
    from genetic_algorithm import ga_solve_flow, is_perfect
    from metrics import GAMetrics
    from puzzle_generator import generate_random_puzzle
    from utils import Color, Coord
    from visualization import print_grid_color
    try:
        from visualization_metrics import (analyze_convergence_patterns,
                                           create_metrics_dashboard,
                                           plot_fitness_evolution,
                                           plot_generation_metrics,
                                           recommend_parameter_adjustments)
        HAS_VISUALIZATION = True
    except ImportError:
        print("⚠️  Módulo de visualización no disponible (matplotlib requerido)")
        HAS_VISUALIZATION = False


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
        # Ejecutar GA con métricas
        sol_ga, metrics = ga_solve_flow(N, terminals,
                                       pop_size=220,
                                       generations=2000,
                                       mut_rate=0.03,
                                       elite=4,
                                       tour_k=4,
                                       verbose=True,
                                       collect_metrics=True)
        
        if sol_ga and is_perfect(sol_ga, terminals):
            solution = sol_ga
            print_grid_color(solution, terminals, "¡Solución (GA)!")
            
            # Mostrar métricas del algoritmo
            if metrics:
                print_metrics_summary(metrics)
                
        elif solver_mode == "GA":
            print(Style.BRIGHT + Fore.YELLOW + "GA no llegó a solución perfecta; mostrando mejor individuo." + Style.RESET_ALL)
            if sol_ga:
                print_grid_color(sol_ga, terminals, "Mejor individuo (GA):")
            if metrics:
                print_metrics_summary(metrics)

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

def print_metrics_summary(metrics: GAMetrics):
    """Imprime un resumen de las métricas del algoritmo genético."""
    summary = metrics.get_summary()
    
    print("\n" + "="*60)
    print("📊 MÉTRICAS DEL ALGORITMO GENÉTICO")
    print("="*60)
    
    # Configuración
    config = summary['configuracion']
    print(f"🔧 CONFIGURACIÓN:")
    print(f"   • Población: {config['poblacion']}")
    print(f"   • Generaciones máx: {config['generaciones']}")
    print(f"   • Tasa mutación: {config['tasa_mutacion']}")
    print(f"   • Elite: {config['elite']}")
    print(f"   • Torneo K: {config['torneo_k']}")
    print(f"   • Tablero: {config['tablero']}")
    print(f"   • Colores: {config['colores']}")
    
    # Rendimiento
    perf = summary['rendimiento']
    print(f"\n⚡ RENDIMIENTO:")
    print(f"   • Éxito: {'✅ SÍ' if perf['exito'] else '❌ NO'}")
    print(f"   • Tiempo total: {perf['tiempo_total']:.3f} segundos")
    print(f"   • Tiempo por generación: {perf['tiempo_por_generacion']:.4f} segundos")
    print(f"   • Generaciones ejecutadas: {perf['generaciones_ejecutadas']}")
    if perf['generaciones_hasta_solucion']:
        print(f"   • Generaciones hasta solución: {perf['generaciones_hasta_solucion']}")
    if perf['generacion_convergencia']:
        print(f"   • Generación de convergencia: {perf['generacion_convergencia']}")
    
    # Fitness
    fit = summary['fitness']
    print(f"\n🎯 FITNESS:")
    print(f"   • Fitness final: {fit['fitness_final']}")
    print(f"   • Mejor fitness: {fit['mejor_fitness']}")
    print(f"   • Fitness promedio: {fit['fitness_promedio']}")
    print(f"   • Mejora total: {fit['mejora_total']}")
    
    # Diversidad
    div = summary['diversidad']
    print(f"\n🌍 DIVERSIDAD:")
    print(f"   • Diversidad inicial: {div['diversidad_inicial']}")
    print(f"   • Diversidad final: {div['diversidad_final']}")
    print(f"   • Diversidad máxima: {div['diversidad_maxima']}")
    print(f"   • Pérdida de diversidad: {div['perdida_diversidad']}")
    
    # Fases
    fases = summary['fases']
    print(f"\n🔄 FASES DEL ALGORITMO:")
    print(f"   • Exploración: {fases['exploracion']} fases")
    print(f"   • Explotación: {fases['explotacion']} fases")
    print(f"   • Estancamiento: {fases['estancamiento']} períodos")
    
    print("="*60)
    
    # Guardar métricas en archivo JSON
    filename = f"metricas_flow_{config['tablero']}_{config['colores']}c.json"
    metrics.export_to_json(filename)
    print(f"📁 Métricas guardadas en: {filename}")
    
    # Análisis avanzado y visualizaciones
    if HAS_VISUALIZATION:
        print("\n" + "="*60)
        print("📊 ANÁLISIS AVANZADO Y VISUALIZACIONES")
        print("="*60)
        
        # Análisis de convergencia
        analyze_convergence_patterns(metrics)
        
        # Recomendaciones
        recommend_parameter_adjustments(metrics)
        
        # Preguntar si mostrar gráficas
        print("\n¿Desea generar visualizaciones? (s/n): ", end="")
        try:
            response = input().strip().lower()
            if response in ['s', 'si', 'sí', 'y', 'yes']:
                print("\n📈 Generando visualizaciones...")
                
                # Gráfica de evolución del fitness
                plot_fitness_evolution(metrics)
                
                # Gráficas detalladas
                plot_generation_metrics(metrics)
                
                # Dashboard completo
                dashboard_dir = create_metrics_dashboard(metrics)
                print(f"✅ Dashboard completo disponible en: {dashboard_dir}")
                
        except (KeyboardInterrupt, EOFError):
            print("\nVisualizaciones omitidas.")
    else:
        print("\n📊 Para visualizaciones avanzadas, instale matplotlib:")
        print("   pip install matplotlib")

def run_multiple_experiments(n_experiments: int = 5):
    """Ejecuta múltiples experimentos para análisis estadístico."""
    print(f"\n🔬 EJECUTANDO {n_experiments} EXPERIMENTOS...")
    
    results = []
    labels = []
    
    # Configuraciones variadas para hacer más interesante el análisis
    configs = [
        (5, 3, "Fácil"),
        (5, 4, "Medio"),
        (6, 4, "Difícil"),
        (6, 5, "Muy Difícil"),
        (7, 4, "Complejo")
    ]
    
    for i in range(n_experiments):
        print(f"\n--- Experimento {i+1}/{n_experiments} ---")
        
        # Rotar entre diferentes configuraciones
        config_idx = i % len(configs)
        N, n_colors, difficulty = configs[config_idx]
        
        print(f"   Configuración: {N}x{N} tablero, {n_colors} colores ({difficulty})")
        
        terminals = generate_random_puzzle(N, n_colors)
        solution, metrics = ga_solve_flow(N, terminals, collect_metrics=True)
        
        results.append(metrics)
        labels.append(f"{difficulty}")
        
        # Mostrar resultado breve
        summary = metrics.get_summary()
        perf = summary['rendimiento']
        print(f"   Resultado: {'✅' if perf['exito'] else '❌'} - "
              f"{perf['generaciones_ejecutadas']} gen - "
              f"{perf['tiempo_total']:.2f}s")
    
    # Análisis comparativo
    if HAS_VISUALIZATION:
        from visualization_metrics import print_comparative_table
        print_comparative_table(results, labels)
    
    return results

if __name__ == "__main__":
    print("🧬 SIMULADOR DE ALGORITMOS GENÉTICOS PARA FLOW PUZZLE")
    print("="*60)
    print("Opciones:")
    print("1. Ejecutar experimento único")
    print("2. Ejecutar múltiples experimentos")
    print("3. Salir")
    
    try:
        choice = input("\nSeleccione una opción (1-3): ").strip()
        
        if choice == "1":
            main()
        elif choice == "2":
            n_exp = input("Número de experimentos (default: 5): ").strip()
            n_exp = int(n_exp) if n_exp.isdigit() else 5
            run_multiple_experiments(n_exp)
        elif choice == "3":
            print("👋 ¡Hasta luego!")
        else:
            print("❌ Opción no válida. Ejecutando experimento único...")
            main()
    except (KeyboardInterrupt, EOFError):
        print("\n👋 Programa interrumpido.")