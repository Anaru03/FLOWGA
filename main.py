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
    from .verify_solution import verify_solution_detailed
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
    from verify_solution import verify_solution_detailed
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
    N = 15        # tamaño del tablero (p. ej., 5, 6, 7, 8, 10)
    n_colors = 8   # número de colores (MÁXIMO: 30+ con paleta extendida ANSI)
    # 💡 REGLA DE ORO PARA TABLEROS GRANDES:
    #    • 10×10: usar 15+ colores (deja ~70 celdas libres)
    #    • Paleta disponible: 30+ colores (15 colorama + 15 ANSI 256)
    #    • Para MÁS colores: añadir más letras en config.py (A,D,E,F,H,I,J,Q,S,U,Z...)
    #    • 8×8:  usar 10-13 colores
    #    • 7×7:  usar 7-10 colores
    #    • Más colores = problema más fácil para el GA
    
    # 🔧 CONFIGURACIÓN DE MÉTRICAS
    # Cambia a False si NO quieres generar archivos JSON de métricas
    GUARDAR_METRICAS = True  # True = genera JSON + gráficas, False = solo solución

    #  ADVERTENCIA PARA TABLEROS GRANDES
    if N >= 10:
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"📋 TABLERO GRANDE DETECTADO: {N}×{N}")
        print(f"{'='*70}{Style.RESET_ALL}")
        
        # Calcular métricas del problema
        total_cells = N * N
        terminal_cells = n_colors * 2
        free_cells = total_cells - terminal_cells
        optimal_colors = N * N // 5  # Regla: 20% del tablero en colores
        
        print(f"📊 Análisis de complejidad:")
        print(f"   • Celdas totales: {total_cells}")
        print(f"   • Celdas ocupadas por terminales: {terminal_cells}")
        print(f"   • Celdas libres a conectar: {free_cells}")
        print(f"   • Complejidad estimada: ~10^{free_cells//4}")
        
        # Advertencias según el número de colores
        if n_colors < 15:
            print(f"\n{Fore.RED}⚠️  ADVERTENCIA: Pocos colores para este tamaño{Style.RESET_ALL}")
            print(f"   • Colores actuales: {n_colors}")
            print(f"   • Colores disponibles en paleta: 30+")
            print(f"   • Colores óptimos (teóricos): {optimal_colors}")
            print(f"   • Problema: {free_cells} celdas libres es DIFÍCIL para el GA")
            print(f"\n{Fore.YELLOW}💡 Sugerencia: Usar 15-30 colores (más disponibles){Style.RESET_ALL}")
        else:
            print(f"\n{Fore.GREEN}✅ Buena configuración de colores{Style.RESET_ALL}")
            print(f"   • Colores: {n_colors}")
            print(f"   • Paleta extendida disponible hasta 30+ colores")
        
        print(f"\n{Fore.YELLOW}  Tiempo estimado de ejecución:{Style.RESET_ALL}")
        if n_colors >= 12:
            print(f"   • Con GA: 60-180 segundos (búsqueda intensiva)")
            print(f"   • Con Backtracking: 10-120 segundos (reparación desde GA)")
        else:
            print(f"   • Con GA: 3-15 minutos (MUY difícil encontrar solución)")
            print(f"   • Con Backtracking: 1-10 minutos (si el puzzle es válido)")
        
        response = input(f"\n¿Continuar con esta configuración? (s/n): ").strip().lower()
        if response not in ['s', 'si', 'sí', 'y', 'yes']:
            print("Operación cancelada.")
            return
        print()

    # ---- Generar puzzle aleatorio ----
    try:
        terminals = generate_random_puzzle(N=N, n_colors=n_colors)
    except ValueError as e:
        print(f"\n{e}")
        print(f"\n🔧 Regla práctica para puzzles válidos:")
        print(f"   Máximo de colores ≤ (N × N) ÷ 3")
        print(f"   Para tablero {N}x{N}: máximo {(N*N)//3} colores recomendados")
        
        print(f"\n📋 CONFIGURACIONES RECOMENDADAS:")
        configs = [(4, 3), (5, 4), (6, 6), (7, 8), (8, 10)]
        for size, colors in configs:
            print(f"   • {size}x{size} tablero: hasta {colors} colores")
        
        return  # Salir de la función main

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
        # 🔥 PARÁMETROS ADAPTATIVOS según tamaño del tablero
        if N >= 12:
            # Tableros muy grandes: recursos moderados (puede ser lento)
            pop_size, generations = 100, 300
            print(f"{Fore.YELLOW}⚠️  Tablero {N}×{N}: usando {pop_size} pop × {generations} gen (exploración moderada){Style.RESET_ALL}")
        elif N >= 10:
            # 💡 MEJORADO: MUCHO más recursos para 10×10
            pop_size, generations = 300, 1000  # 2× población, 2× generaciones
            print(f"{Fore.YELLOW}🔥 Tablero {N}×{N}: usando {pop_size} pop × {generations} gen (búsqueda INTENSIVA){Style.RESET_ALL}")
            print(f"{Fore.CYAN}   💡 Recomendación: usar al menos {N*N//5} colores para mejorar convergencia{Style.RESET_ALL}")
        elif N >= 8:
            pop_size, generations = 150, 800
            print(f"{Fore.CYAN}📉 Tablero {N}×{N}: usando {pop_size} pop × {generations} gen (búsqueda reforzada){Style.RESET_ALL}")
        elif N >= 7:
            pop_size, generations = 150, 1000
        else:
            pop_size, generations = 200, 2000
        
        # Ejecutar GA con métricas (si está habilitado)
        sol_ga, metrics = ga_solve_flow(N, terminals,
                                       pop_size=pop_size,
                                       generations=generations,
                                       mut_rate=0.05,  # Más mutación para explorar mejor
                                       elite=5,        # Mantener mejores soluciones
                                       tour_k=3,       # Torneo más selectivo
                                       verbose=True,
                                       collect_metrics=GUARDAR_METRICAS)  # Solo si está activado
        
        if sol_ga and is_perfect(sol_ga, terminals):
            solution = sol_ga
            print_grid_color(solution, terminals, "¡Solución (GA)!")
            
            # 🔍 VERIFICACIÓN DETALLADA de la solución
            print(f"\n{Fore.CYAN}{'='*60}")
            print(f"🔬 VERIFICACIÓN EXHAUSTIVA DE LA SOLUCIÓN")
            print(f"{'='*60}{Style.RESET_ALL}")
            is_valid = verify_solution_detailed(solution, terminals)
            
            if not is_valid:
                print(f"\n{Fore.RED}⚠️  ALERTA: La solución reportada como 'perfecta' tiene problemas!{Style.RESET_ALL}")
                print(f"Esto indica un bug en is_perfect() o en el algoritmo.")
                solution = None  # Invalidar la solución
            else:
                print(f"\n{Fore.GREEN}✅ Solución verificada correctamente{Style.RESET_ALL}")
            
            # Mostrar métricas del algoritmo (solo si se recolectaron)
            if metrics and GUARDAR_METRICAS:
                print_metrics_summary(metrics, save_to_file=True)
            elif not GUARDAR_METRICAS:
                print(f"\n{Fore.CYAN}💡 Métricas desactivadas. Para ver estadísticas detalladas, cambiar GUARDAR_METRICAS=True en main.py{Style.RESET_ALL}")
                
        elif solver_mode == "GA":
            print(Style.BRIGHT + Fore.YELLOW + "GA no llegó a solución perfecta; mostrando mejor individuo." + Style.RESET_ALL)
            if sol_ga:
                print_grid_color(sol_ga, terminals, "Mejor individuo (GA):")
            if metrics and GUARDAR_METRICAS:
                print_metrics_summary(metrics, save_to_file=True)

    if solution is None and solver_mode in ("BT", "GA_THEN_BT"):
        print(f"\n{Fore.YELLOW}🔄 Intentando resolver con Backtracking...{Style.RESET_ALL}")
        
        # Si hay una solución del GA, úsala como punto de partida para el Backtracking
        if 'sol_ga' in locals() and sol_ga is not None:
            print(f"   💡 Usando mejor solución del GA como punto de partida")
            sol_bt = solve_flow_bt(N, terminals, start_grid=sol_ga)
        else:
            sol_bt = solve_flow_bt(N, terminals)
        
        if sol_bt:
            solution = sol_bt
            print_grid_color(solution, terminals, "¡Solución (Backtracking)!")
            
            # Verificar la solución
            print(f"\n{Fore.CYAN}{'='*60}")
            print(f"🔬 VERIFICACIÓN DE LA SOLUCIÓN")
            print(f"{'='*60}{Style.RESET_ALL}")
            is_valid = verify_solution_detailed(solution, terminals)
            
            if is_valid:
                print(f"\n{Fore.GREEN}✅ Solución verificada correctamente{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.RED}⚠️  La solución tiene problemas{Style.RESET_ALL}")
        else:
            print(f"\n{Style.BRIGHT}{Fore.RED}{'='*60}")
            print(f"❌ NO SE ENCONTRÓ SOLUCIÓN")
            print(f"{'='*60}{Style.RESET_ALL}")
            print(f"Posibles causas:")
            print(f"  1️⃣  El puzzle generado NO tiene solución válida")
            print(f"  2️⃣  El backtracking alcanzó el límite de caminos explorados")
            print(f"  3️⃣  El problema es demasiado complejo")
            print(f"\n{Fore.YELLOW}💡 Soluciones sugeridas:{Style.RESET_ALL}")
            print(f"  • Volver a ejecutar (genera un nuevo puzzle)")
            print(f"  • Reducir el tamaño del tablero (usar {N-2}×{N-2})")
            print(f"  • Aumentar el número de colores (usar {n_colors + 5} colores)")
            print(f"  • Para tableros grandes, el GA suele funcionar mejor que backtracking")

def print_metrics_summary(metrics: GAMetrics, save_to_file: bool = True):
    """Imprime un resumen de las métricas del algoritmo genético.
    
    Args:
        metrics: Objeto GAMetrics con los datos recolectados
        save_to_file: Si True, guarda el JSON. Si False, solo muestra en pantalla
    """
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
    print(f"   • Evaluaciones de fitness: {perf['evaluaciones_fitness']}")
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
    
    # Guardar métricas en archivo JSON (solo si está habilitado)
    if save_to_file:
        filename = f"metricas_flow_{config['tablero']}_{config['colores']}c.json"
        metrics.export_to_json(filename)
        print(f"📁 Métricas guardadas en: {filename}")
    else:
        print(f"💡 Archivo JSON NO guardado (save_to_file=False)")
    
    # Análisis avanzado y visualizaciones (solo si se guardan métricas)
    if HAS_VISUALIZATION and save_to_file:
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