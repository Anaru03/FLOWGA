"""
Script de prueba para el sistema de timeout adaptativo.

Este script demuestra cómo el sistema detecta automáticamente
problemas intratables y los maneja con timeouts adaptativos.
"""

from colorama import Fore, Style, init

from color_complexity_analysis import run_complete_color_study

init(autoreset=True)

def test_timeout_detection():
    """
    Prueba el sistema de timeout con configuraciones progresivamente más difíciles.
    """
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{'PRUEBA DE SISTEMA DE TIMEOUT ADAPTATIVO':^80}")
    print(f"{'='*80}{Style.RESET_ALL}\n")
    
    print(f"{Fore.YELLOW}Este test ejecutará configuraciones con dificultad creciente:")
    print(f"  1. 5×5 con 7 colores (densidad=0.28) - FÁCIL")
    print(f"  2. 6×6 con 10 colores (densidad=0.28) - MODERADO")
    print(f"  3. 7×7 con 14 colores (densidad=0.29) - DIFÍCIL")
    print(f"\nEl sistema aplicará timeouts adaptativos basados en complejidad.")
    print(f"Si alguna configuración excede 60s consistentemente, se marcará como INTRATABLE.{Style.RESET_ALL}\n")
    
    input(f"{Fore.GREEN}Presiona Enter para comenzar...{Style.RESET_ALL}")
    
    # Configuración de prueba
    color_ranges = {
        5: [7],      # Densidad 0.28
        6: [10],     # Densidad 0.28
        7: [14]      # Densidad 0.29
    }
    
    results, summaries, thresholds = run_complete_color_study(
        board_sizes=[5, 6, 7],
        color_ranges=color_ranges,
        runs_per_config=5,
        output_dir="timeout_test_results"
    )
    
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{'RESULTADOS DEL TEST':^80}")
    print(f"{'='*80}{Style.RESET_ALL}\n")
    
    for summary in summaries:
        status = "✓" if summary.total_success_rate > 0.7 else "⚠️" if summary.total_success_rate > 0.3 else "✗"
        color = Fore.GREEN if summary.total_success_rate > 0.7 else Fore.YELLOW if summary.total_success_rate > 0.3 else Fore.RED
        
        print(f"{color}{status} {summary.board_size}×{summary.board_size} con {summary.num_colors} colores:")
        print(f"   Densidad: {summary.density:.3f}")
        print(f"   Éxito: {summary.total_success_rate:.1%}")
        print(f"   Tiempo promedio: {summary.avg_total_time:.2f}s")
        print(f"   Dificultad: {summary.difficulty_score:.1f}")
        
        if summary.avg_total_time > 60:
            print(f"   {Fore.RED}⚠ PROBLEMA INTRATABLE (tiempo > 60s){Style.RESET_ALL}")
        elif summary.avg_total_time > 30:
            print(f"   {Fore.YELLOW}⚠ Problema difícil (tiempo > 30s){Style.RESET_ALL}")
        else:
            print(f"   {Fore.GREEN}✓ Resoluble en tiempo razonable{Style.RESET_ALL}")
        print()
    
    print(f"\n{Fore.CYAN}Resultados guardados en: timeout_test_results/{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Revisa los archivos CSV y PNG para análisis detallado.{Style.RESET_ALL}\n")


def test_extreme_case():
    """
    Prueba con un caso extremo diseñado para forzar timeout.
    ⚠️ ADVERTENCIA: Esto puede tomar varios minutos.
    """
    print(f"\n{Fore.RED}{'='*80}")
    print(f"{'⚠️  PRUEBA DE CASO EXTREMO  ⚠️':^80}")
    print(f"{'='*80}{Style.RESET_ALL}\n")
    
    print(f"{Fore.YELLOW}Esta prueba intentará resolver un problema muy difícil:")
    print(f"  • 7×7 con 15 colores (densidad=0.31)")
    print(f"  • Límite teórico: ~16 colores")
    print(f"  • Esperado: Múltiples timeouts, early stopping{Style.RESET_ALL}\n")
    
    response = input(f"{Fore.RED}¿Continuar? Puede tomar 5-10 minutos (s/n): {Style.RESET_ALL}").lower()
    
    if response != 's':
        print(f"{Fore.YELLOW}Test cancelado.{Style.RESET_ALL}")
        return
    
    color_ranges = {
        7: [15]  # Cerca del límite, probablemente intratable
    }
    
    results, summaries, thresholds = run_complete_color_study(
        board_sizes=[7],
        color_ranges=color_ranges,
        runs_per_config=5,
        output_dir="extreme_timeout_test"
    )
    
    summary = summaries[0]
    
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{'RESULTADO DEL CASO EXTREMO':^80}")
    print(f"{'='*80}{Style.RESET_ALL}\n")
    
    print(f"Configuración: {summary.board_size}×{summary.board_size} con {summary.num_colors} colores")
    print(f"Densidad: {summary.density:.3f}")
    print(f"Éxito: {summary.total_success_rate:.1%}")
    print(f"Tiempo promedio: {summary.avg_total_time:.2f}s")
    print(f"Dificultad: {summary.difficulty_score:.1f}")
    
    if summary.avg_total_time > 60:
        print(f"\n{Fore.RED}✗ CONFIRMADO: Problema INTRATABLE")
        print(f"   El sistema debería haber aplicado early stopping.{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.GREEN}✓ Problema resuelto en tiempo razonable")
        print(f"   Esta configuración está dentro de la zona resoluble.{Style.RESET_ALL}")


if __name__ == "__main__":
    print(f"{Fore.CYAN}")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                   TEST DE SISTEMA DE TIMEOUT ADAPTATIVO                   ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Style.RESET_ALL}")
    
    print("\nSelecciona un test:")
    print("  1. Test estándar (5-10 minutos)")
    print("  2. Test de caso extremo (puede tomar más tiempo)")
    print("  3. Ambos")
    
    choice = input("\nOpción (1/2/3): ").strip()
    
    if choice == "1":
        test_timeout_detection()
    elif choice == "2":
        test_extreme_case()
    elif choice == "3":
        test_timeout_detection()
        test_extreme_case()
    else:
        print(f"{Fore.RED}Opción inválida.{Style.RESET_ALL}")
