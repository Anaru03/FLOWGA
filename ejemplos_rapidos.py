"""
Ejemplos rápidos para empezar a experimentar.
Ejecuta este archivo para ver demos de cada funcionalidad.
"""

def ejemplo_0_complejidad_colores():
    """Ejemplo 0: Análisis de complejidad por número de colores (NP-Completo)."""
    print("\n" + "="*80)
    print("EJEMPLO 0: Complejidad por Número de Colores (NP-Completo)")
    print("="*80)
    print("Explora diferentes cantidades de colores para identificar límites de resolubilidad")
    print("Tableros 4x4, 5x5, y 6x6")
    print("Detecta automáticamente dónde el problema se vuelve intratable")
    print()
    
    from color_complexity_analysis import run_complete_color_study

    # Rangos inteligentes: desde 50% hasta 100% de densidad
    color_ranges = {
        4: [3, 4, 5, 6, 7, 8],      # 4x4 = 16 celdas
        5: [4, 5, 6, 7, 8, 9, 10],  # 5x5 = 25 celdas
        6: [6, 8, 10, 12, 14, 16]   # 6x6 = 36 celdas
    }
    
    results, summaries, thresholds = run_complete_color_study(
        board_sizes=[4, 5, 6],
        color_ranges=color_ranges,
        runs_per_config=5,
        output_dir="ejemplo_complejidad_colores"
    )
    
    print("\n" + "="*80)
    print("FRONTERA DE RESOLUBILIDAD DETECTADA:")
    print("="*80)
    for board_size, threshold in sorted(thresholds.items()):
        print(f"  {board_size}×{board_size}: Máximo {threshold.max_solvable_colors} colores "
              f"(densidad {threshold.max_density:.3f}, éxito {threshold.success_rate_at_threshold:.1%})")
    print("\n✓ Revisa la carpeta 'ejemplo_complejidad_colores' para ver las visualizaciones!")


def ejemplo_1_tuning_rapido():
    """Ejemplo 1: Tuning rápido con pocos parámetros."""
    print("\n" + "="*80)
    print("EJEMPLO 1: Tuning Rápido")
    print("="*80)
    print("Compara 3 tamaños de población con 3 tasas de mutación")
    print("Tablero 5x5, 4 colores, 3 corridas por configuración")
    print()
    
    from parameter_tuning import (grid_search, print_ranking_table,
                                  summarize_results)
    
    param_space = {
        'pop_size': [100, 200, 300],
        'generations': [1000],
        'mut_rate': [0.01, 0.03, 0.05],
        'elite': [2],
        'tour_k': [3]
    }
    
    results = grid_search(
        param_space=param_space,
        board_size=5,
        num_colors=4,
        runs_per_config=3,
        verbose=False
    )
    
    summaries = summarize_results(results)
    print_ranking_table(summaries, top_n=5)


def ejemplo_2_escalabilidad_simple():
    """Ejemplo 2: Escalabilidad con 2 tamaños."""
    print("\n" + "="*80)
    print("EJEMPLO 2: Escalabilidad Simple")
    print("="*80)
    print("Compara rendimiento en tableros 4x4 y 5x5")
    print("5 corridas por tamaño")
    print()
    
    from scalability_experiments import run_complete_scalability_study
    
    run_complete_scalability_study(
        board_sizes=[4, 5],
        runs_per_size=5,
        output_dir="ejemplo_escalabilidad"
    )


def ejemplo_3_impacto_poblacion():
    """Ejemplo 3: Estudiar impacto del tamaño de población."""
    print("\n" + "="*80)
    print("EJEMPLO 3: Impacto del Tamaño de Población")
    print("="*80)
    print("Prueba poblaciones de 50 a 400 individuos")
    print("Tablero 5x5, parámetros fijos, 5 corridas cada uno")
    print()
    
    from parameter_tuning import (grid_search, plot_parameter_impact,
                                  summarize_results)
    
    param_space = {
        'pop_size': [50, 100, 150, 200, 250, 300, 400],
        'generations': [1000],
        'mut_rate': [0.03],
        'elite': [2],
        'tour_k': [3]
    }
    
    results = grid_search(
        param_space=param_space,
        board_size=5,
        num_colors=4,
        runs_per_config=5,
        verbose=False
    )
    
    summaries = summarize_results(results)
    
    # Visualizar impacto
    plot_parameter_impact(summaries, 'pop_size', 'impacto_poblacion.png')
    
    print("\n✅ Gráfico guardado: impacto_poblacion.png")


def ejemplo_4_comparar_mutaciones():
    """Ejemplo 4: Comparar diferentes tasas de mutación."""
    print("\n" + "="*80)
    print("EJEMPLO 4: Comparación de Tasas de Mutación")
    print("="*80)
    print("Prueba 7 tasas de mutación diferentes")
    print("Desde muy baja (0.001) hasta alta (0.1)")
    print()
    
    from parameter_tuning import (grid_search, plot_parameter_impact,
                                  print_ranking_table, summarize_results)
    
    param_space = {
        'pop_size': [200],
        'generations': [1000],
        'mut_rate': [0.001, 0.005, 0.01, 0.03, 0.05, 0.07, 0.1],
        'elite': [2],
        'tour_k': [3]
    }
    
    results = grid_search(
        param_space=param_space,
        board_size=5,
        num_colors=4,
        runs_per_config=5,
        verbose=False
    )
    
    summaries = summarize_results(results)
    print_ranking_table(summaries, top_n=7)
    
    # Visualizar
    plot_parameter_impact(summaries, 'mut_rate', 'impacto_mutacion.png')
    
    print("\n✅ Gráfico guardado: impacto_mutacion.png")


def ejemplo_5_heatmap_interaccion():
    """Ejemplo 5: Heatmap de interacción elite vs torneo."""
    print("\n" + "="*80)
    print("EJEMPLO 5: Interacción Elite vs Torneo")
    print("="*80)
    print("Explora cómo interactúan elite y tamaño de torneo")
    print()
    
    from parameter_tuning import (grid_search, plot_comparative_heatmap,
                                  summarize_results)
    
    param_space = {
        'pop_size': [200],
        'generations': [1000],
        'mut_rate': [0.03],
        'elite': [0, 2, 5, 10],
        'tour_k': [2, 3, 5, 7]
    }
    
    results = grid_search(
        param_space=param_space,
        board_size=5,
        num_colors=4,
        runs_per_config=5,
        verbose=False
    )
    
    summaries = summarize_results(results)
    
    # Heatmap
    plot_comparative_heatmap(
        summaries, 
        'elite', 
        'tour_k', 
        'success_rate',
        'heatmap_elite_tour.png'
    )
    
    print("\n✅ Heatmap guardado: heatmap_elite_tour.png")


def menu_interactivo():
    """Menú interactivo para elegir ejemplos."""
    print("\n" + "="*80)
    print("🧬 EJEMPLOS DE EXPERIMENTACIÓN - FLOWGA")
    print("="*80)
    print("\nElige un ejemplo para ejecutar:\n")
    print("0. 🎨 Complejidad por Colores (NP-Completo) [~5 min] ⭐ NUEVO")
    print("1. Tuning rápido (3 poblaciones × 3 mutaciones) [~2 min]")
    print("2. Escalabilidad simple (4x4 y 5x5) [~3 min]")
    print("3. Impacto del tamaño de población [~5 min]")
    print("4. Comparación de tasas de mutación [~5 min]")
    print("5. Heatmap de interacción elite vs torneo [~6 min]")
    print("6. Ejecutar todos los ejemplos [~25 min]")
    print("9. Salir")
    print()
    
    try:
        opcion = input("Selecciona una opción (0-6, 9): ").strip()
        
        if opcion == "0":
            ejemplo_0_complejidad_colores()
        elif opcion == "1":
            ejemplo_1_tuning_rapido()
        elif opcion == "2":
            ejemplo_2_escalabilidad_simple()
        elif opcion == "3":
            ejemplo_3_impacto_poblacion()
        elif opcion == "4":
            ejemplo_4_comparar_mutaciones()
        elif opcion == "5":
            ejemplo_5_heatmap_interaccion()
        elif opcion == "6":
            print("\n🚀 Ejecutando todos los ejemplos...\n")
            ejemplo_0_complejidad_colores()
            ejemplo_1_tuning_rapido()
            ejemplo_2_escalabilidad_simple()
            ejemplo_3_impacto_poblacion()
            ejemplo_4_comparar_mutaciones()
            ejemplo_5_heatmap_interaccion()
            print("\n✅ Todos los ejemplos completados!")
        elif opcion == "9":
            print("👋 ¡Hasta luego!")
            return
        else:
            print("❌ Opción no válida")
            return
        
        print("\n" + "="*80)
        print("✅ EJEMPLO COMPLETADO")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    menu_interactivo()
