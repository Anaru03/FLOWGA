# Ejemplo de demostración con puzzle más complejo para mostrar métricas detalladas
import os
import sys

# Agregar el directorio actual al path para importaciones
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from genetic_algorithm import ga_solve_flow
    from metrics import GAMetrics
    from puzzle_generator import generate_random_puzzle
    from visualization import print_grid_color
    from visualization_metrics import (analyze_convergence_patterns,
                                       create_metrics_dashboard,
                                       plot_fitness_evolution,
                                       plot_generation_metrics,
                                       recommend_parameter_adjustments)
    HAS_VISUALIZATION = True
except ImportError as e:
    print(f"Error importing modules: {e}")
    HAS_VISUALIZATION = False

def demo_completo():
    """Demostración completa del sistema con puzzle más desafiante."""
    print("🧬 DEMOSTRACIÓN COMPLETA - SISTEMA DE MÉTRICAS GA")
    print("="*60)
    
    # Configuración para puzzle más desafiante
    N = 7           # Tablero más grande
    n_colors = 6    # Más colores para mayor complejidad
    
    print(f"📋 Configuración:")
    print(f"   • Tablero: {N}x{N}")
    print(f"   • Colores: {n_colors}")
    print(f"   • Complejidad: ALTA")
    
    # Generar puzzle
    print(f"\n🎲 Generando puzzle complejo...")
    colors_and_terminals = generate_random_puzzle(N, n_colors)
    
    # Crear tablero vacío y extraer información
    puzzle = [[None for _ in range(N)] for _ in range(N)]
    colors = list(colors_and_terminals.keys())
    terminals = {}
    
    # Colocar terminales en el tablero
    for color, (start, end) in colors_and_terminals.items():
        puzzle[start[0]][start[1]] = color
        puzzle[end[0]][end[1]] = color
        terminals[color] = (start, end)
    
    print(f"\n📋 Puzzle generado:")
    print_grid_color(puzzle, terminals)
    
    # Resolver con GA
    print(f"\n🧬 Resolviendo con Algoritmo Genético...")
    print("   (Esto puede tomar un momento para puzzles complejos)")
    
    try:
        solution, metrics = ga_solve_flow(N, terminals, collect_metrics=True)
        
        # Mostrar resultado
        if solution:
            print(f"\n✅ ¡Solución encontrada!")
            print_grid_color(solution, terminals)
        else:
            print(f"\n❌ No se encontró solución en el límite de generaciones")
        
        # Mostrar métricas detalladas
        print("\n" + "="*60)
        print("📊 ANÁLISIS COMPLETO DE MÉTRICAS")
        print("="*60)
        
        summary = metrics.get_summary()
        
        # Métricas de rendimiento
        perf = summary['rendimiento']
        print(f"\n⚡ RENDIMIENTO:")
        print(f"   • Éxito: {'✅' if perf['exito'] else '❌'}")
        print(f"   • Tiempo total: {perf['tiempo_total']:.3f} segundos")
        print(f"   • Generaciones ejecutadas: {perf['generaciones_ejecutadas']}")
        if perf['generaciones_hasta_solucion']:
            print(f"   • Solución encontrada en: generación {perf['generaciones_hasta_solucion']}")
        if perf['generacion_convergencia']:
            print(f"   • Convergencia en: generación {perf['generacion_convergencia']}")
        
        # Métricas de fitness
        fit = summary['fitness']
        print(f"\n🎯 EVOLUCIÓN DEL FITNESS:")
        print(f"   • Fitness final: {fit['fitness_final']:.2f}")
        print(f"   • Mejor fitness alcanzado: {fit['mejor_fitness']:.2f}")
        print(f"   • Fitness promedio: {fit['fitness_promedio']:.2f}")
        print(f"   • Mejora total: +{fit['mejora_total']:.2f}")
        
        # Métricas de diversidad
        div = summary['diversidad']
        print(f"\n🌍 DIVERSIDAD POBLACIONAL:")
        print(f"   • Diversidad inicial: {div['diversidad_inicial']:.3f}")
        print(f"   • Diversidad final: {div['diversidad_final']:.3f}")
        print(f"   • Máxima diversidad: {div['diversidad_maxima']:.3f}")
        print(f"   • Pérdida de diversidad: {div['perdida_diversidad']:.1%}")
        
        # Análisis de fases
        fases = summary['fases']
        print(f"\n🔄 ANÁLISIS DE FASES:")
        print(f"   • Fases de exploración: {fases['exploracion']}")
        print(f"   • Fases de explotación: {fases['explotacion']}")
        print(f"   • Períodos de estancamiento: {fases['estancamiento']}")
        
        # Análisis avanzado
        if HAS_VISUALIZATION:
            print(f"\n🔍 ANÁLISIS AVANZADO:")
            analyze_convergence_patterns(metrics)
            
            print(f"\n💡 RECOMENDACIONES:")
            recommend_parameter_adjustments(metrics)
            
            # Generar visualizaciones
            print(f"\n📈 GENERANDO VISUALIZACIONES...")
            
            # Dashboard completo
            dashboard_dir = create_metrics_dashboard(metrics, "demo_results")
            print(f"✅ Dashboard completo guardado en: {dashboard_dir}")
            
            # Mostrar gráficas individuales
            print(f"\n📊 Mostrando gráficas interactivas...")
            plot_fitness_evolution(metrics)
            plot_generation_metrics(metrics)
            
        else:
            print(f"\n⚠️  Para visualizaciones completas, instale matplotlib:")
            print(f"   pip install matplotlib")
        
        # Guardar métricas
        json_file = f"demo_metrics_{N}x{N}_{n_colors}c.json"
        metrics.export_to_json(json_file)
        print(f"\n📁 Métricas detalladas guardadas en: {json_file}")
        
        return metrics
        
    except Exception as e:
        print(f"❌ Error durante la ejecución: {e}")
        return None

def demo_comparativo():
    """Ejecuta múltiples experimentos para análisis comparativo."""
    print("\n" + "="*60)
    print("🔬 ANÁLISIS COMPARATIVO - MÚLTIPLES EJECUCIONES")
    print("="*60)
    
    # Diferentes configuraciones para comparar
    configs = [
        (5, 3, "Fácil"),
        (5, 4, "Medio"),
        (6, 4, "Difícil"),
        (6, 5, "Muy Difícil")
    ]
    
    results = []
    
    for i, (N, n_colors, difficulty) in enumerate(configs):
        print(f"\n--- Experimento {i+1}: {difficulty} ({N}x{N}, {n_colors} colores) ---")
        
        try:
            colors_and_terminals = generate_random_puzzle(N, n_colors)
            terminals = colors_and_terminals
            _, metrics = ga_solve_flow(N, terminals, collect_metrics=True)
            
            summary = metrics.get_summary()
            perf = summary['rendimiento']
            
            results.append({
                'config': f"{N}x{N}-{n_colors}c",
                'difficulty': difficulty,
                'success': perf['exito'],
                'time': perf['tiempo_total'],
                'generations': perf['generaciones_ejecutadas'],
                'fitness': summary['fitness']['fitness_final'],
                'metrics': metrics
            })
            
            print(f"   Resultado: {'✅' if perf['exito'] else '❌'} - "
                  f"{perf['generaciones_ejecutadas']} gen - "
                  f"{perf['tiempo_total']:.2f}s")
                  
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Mostrar tabla comparativa
    if results:
        print(f"\n📋 TABLA COMPARATIVA:")
        print(f"{'Config':12} {'Dificultad':12} {'Éxito':8} {'Tiempo':8} {'Gen':6} {'Fitness':10}")
        print("-" * 70)
        
        for r in results:
            success_icon = "✅" if r['success'] else "❌"
            print(f"{r['config']:12} {r['difficulty']:12} {success_icon:8} "
                  f"{r['time']:8.2f} {r['generations']:6} {r['fitness']:10.1f}")
    
    return results

if __name__ == "__main__":
    print("🎯 SELECTOR DE DEMOSTRACIONES")
    print("="*40)
    print("1. Demostración completa (puzzle complejo)")
    print("2. Análisis comparativo (múltiples puzzles)")
    print("3. Ambas demostraciones")
    
    try:
        choice = input("\nSeleccione una opción (1-3): ").strip()
        
        if choice == "1":
            demo_completo()
        elif choice == "2":
            demo_comparativo()
        elif choice == "3":
            demo_completo()
            demo_comparativo()
        else:
            print("Ejecutando demostración completa...")
            demo_completo()
            
    except (KeyboardInterrupt, EOFError):
        print("\n👋 Demostración interrumpida.")
    
    print(f"\n🎉 ¡Demostración completada!")
    print(f"   Revise los archivos generados para análisis detallado.")