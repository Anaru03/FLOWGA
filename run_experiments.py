"""
Script CLI para ejecutar experimentos de forma sencilla.
Uso:
    python run_experiments.py --mode scalability --board-sizes 4 5 6 --runs 10
    python run_experiments.py --mode tuning --board-size 5 --runs 5
    python run_experiments.py --mode single --board-size 6 --colors 5
"""
import argparse
import os
import sys

try:
    from color_complexity_analysis import run_complete_color_study
    from main import main as run_single
    from parameter_tuning import (export_tuning_results, grid_search,
                                  print_ranking_table, quick_tuning_study,
                                  save_ranking_table_as_image,
                                  summarize_results)
    from scalability_experiments import run_complete_scalability_study
except ImportError:
    print("❌ Error: Asegúrate de estar en el directorio correcto")
    sys.exit(1)


def run_scalability_mode(args):
    """Ejecuta experimentos de escalabilidad."""
    print("\n🔬 MODO: ESCALABILIDAD")
    
    board_sizes = args.board_sizes or [4, 5, 6, 7]
    runs = args.runs or 10
    
    # Configuración de colores por defecto
    colors_config = {}
    if args.colors_config:
        # Formato: "4:3,5:4,6:6"
        for item in args.colors_config.split(','):
            size, colors = map(int, item.split(':'))
            colors_config[size] = colors
    else:
        # Auto configuración
        for size in board_sizes:
            colors_config[size] = max(2, min(size, (size * size) // 3))
    
    output_dir = args.output or "scalability_results"
    
    run_complete_scalability_study(
        board_sizes=board_sizes,
        colors_config=colors_config,
        runs_per_size=runs,
        output_dir=output_dir
    )


def run_tuning_mode(args):
    """Ejecuta experimentos de tuning de parámetros."""
    print("\n🎛️  MODO: TUNING DE PARÁMETROS")
    
    board_size = args.board_size or 5
    num_colors = args.colors or max(2, board_size // 2)
    runs = args.runs or 5
    
    # 🔥 Generar nombre de directorio automáticamente basado en tamaño
    output_dir = args.output or f"tuning_{board_size}x{board_size}"
    
    if args.custom_params:
        # Parámetros personalizados
        print("📝 Usando parámetros personalizados...")
        param_space = parse_custom_params(args.custom_params)
        
        results = grid_search(
            param_space=param_space,
            board_size=board_size,
            num_colors=num_colors,
            runs_per_config=runs,
            verbose=False
        )
        
        summaries = summarize_results(results)
        print_ranking_table(summaries, top_n=10)
        
        # 🔥 Guardar tabla como imagen
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        save_ranking_table_as_image(summaries, board_size, num_colors, 
                                   os.path.join(output_dir, 'ranking_table.png'))
        
        export_tuning_results(results, summaries, output_dir)
        
    else:
        # Tuning rápido con valores por defecto (ya incluye la tabla de imagen)
        quick_tuning_study(
            board_size=board_size,
            num_colors=num_colors,
            runs_per_config=runs,
            output_dir=output_dir
        )


def run_color_complexity_mode(args):
    """Ejecuta análisis de complejidad por número de colores."""
    print("\n🎨 MODO: ANÁLISIS DE COMPLEJIDAD POR COLORES (NP-Completo)")
    
    board_sizes = args.board_sizes or [4, 5, 6]
    runs = args.runs or 10
    output_dir = args.output or "color_complexity_results"
    
    # Configurar rangos de colores
    if args.color_ranges:
        # Formato: "4:3,4,5,6;5:4,5,6,7,8;6:5,6,7,8,9,10"
        color_ranges = {}
        for item in args.color_ranges.split(';'):
            size_part, colors_part = item.split(':')
            size = int(size_part.strip())
            colors = [int(c.strip()) for c in colors_part.split(',')]
            color_ranges[size] = colors
    else:
        # Rangos automáticos inteligentes
        color_ranges = None
    
    run_complete_color_study(
        board_sizes=board_sizes,
        color_ranges=color_ranges,
        runs_per_config=runs,
        output_dir=output_dir,
        pop_size=args.pop_size or 200,
        generations=args.generations or 1000,
        mut_rate=args.mut_rate or 0.03,
        elite=args.elite or 2,
        tour_k=args.tour_k or 3
    )


def run_single_mode(args):
    """Ejecuta un experimento individual."""
    print("\n🎯 MODO: EXPERIMENTO ÚNICO")
    
    # Modificar temporalmente las variables globales de main.py
    # (esto es un hack simple para demo; en producción usaríamos otra estrategia)
    run_single()


def parse_custom_params(param_string):
    """
    Parsea parámetros personalizados.
    Formato: "pop_size:100,200,300;mut_rate:0.01,0.03,0.05"
    """
    param_space = {}
    
    for param_def in param_string.split(';'):
        param_name, values_str = param_def.split(':')
        param_name = param_name.strip()
        
        values = []
        for val_str in values_str.split(','):
            val_str = val_str.strip()
            # Detectar tipo (int vs float)
            if '.' in val_str:
                values.append(float(val_str))
            else:
                values.append(int(val_str))
        
        param_space[param_name] = values
    
    return param_space


def main():
    parser = argparse.ArgumentParser(
        description="🧬 Sistema de Experimentación para Flow GA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  1. Escalabilidad (por defecto):
     python run_experiments.py --mode scalability --board-sizes 4 5 6 --runs 10

  2. Escalabilidad con configuración personalizada:
     python run_experiments.py --mode scalability --board-sizes 4 5 6 --runs 10 \\
         --colors-config "4:3,5:4,6:6" --output my_results

  3. Tuning rápido (valores por defecto):
     python run_experiments.py --mode tuning --board-size 5 --runs 5

  4. Tuning con parámetros personalizados:
     python run_experiments.py --mode tuning --board-size 6 --colors 5 --runs 3 \\
         --custom-params "pop_size:100,200;mut_rate:0.01,0.03,0.05;elite:0,2,5"

  5. Experimento único (interactivo):
     python run_experiments.py --mode single

  6. Comparar diferentes tamaños de población:
     python run_experiments.py --mode tuning --board-size 5 --runs 5 \\
         --custom-params "pop_size:50,100,150,200,250,300;generations:1000;mut_rate:0.03;elite:2;tour_k:3"

  7. Explorar tasas de mutación:
     python run_experiments.py --mode tuning --board-size 6 --runs 5 \\
         --custom-params "pop_size:200;generations:1000;mut_rate:0.005,0.01,0.02,0.03,0.05,0.1;elite:2;tour_k:3"

  8. Análisis de complejidad por colores (NP-Completo):
     python run_experiments.py --mode colors --board-sizes 4 5 6 --runs 10

  9. Análisis de colores con rangos específicos:
     python run_experiments.py --mode colors --board-sizes 4 5 6 --runs 10 \\
         --color-ranges "4:3,4,5,6;5:4,5,6,7,8;6:5,6,7,8,9,10"

  10. Identificar frontera de resolubilidad:
      python run_experiments.py --mode colors --board-sizes 5 6 7 --runs 15 \\
          --output solvability_frontier
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['scalability', 'tuning', 'single', 'colors'],
        default='scalability',
        help='Modo de experimentación (default: scalability)'
    )
    
    # Parámetros para scalability
    parser.add_argument(
        '--board-sizes',
        nargs='+',
        type=int,
        help='Tamaños de tablero a probar (ej: 4 5 6 7)'
    )
    
    parser.add_argument(
        '--colors-config',
        type=str,
        help='Configuración de colores por tamaño: "4:3,5:4,6:6"'
    )
    
    parser.add_argument(
        '--color-ranges',
        type=str,
        help='Rangos de colores para análisis: "4:3,4,5,6;5:4,5,6,7,8"'
    )
    
    # Parámetros para tuning
    parser.add_argument(
        '--board-size',
        type=int,
        help='Tamaño del tablero para tuning'
    )
    
    parser.add_argument(
        '--colors',
        type=int,
        help='Número de colores'
    )
    
    parser.add_argument(
        '--custom-params',
        type=str,
        help='Parámetros personalizados: "param1:val1,val2;param2:val1,val2"'
    )
    
    # Parámetros comunes
    parser.add_argument(
        '--runs',
        type=int,
        help='Número de corridas por configuración'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Directorio de salida para resultados'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Mostrar salida detallada'
    )
    
    # Parámetros GA específicos (para modo colors)
    parser.add_argument('--pop-size', type=int, help='Tamaño de población')
    parser.add_argument('--generations', type=int, help='Número de generaciones')
    parser.add_argument('--mut-rate', type=float, help='Tasa de mutación')
    parser.add_argument('--elite', type=int, help='Elite count')
    parser.add_argument('--tour-k', type=int, help='Tournament size')
    
    args = parser.parse_args()
    
    # Ejecutar el modo seleccionado
    try:
        if args.mode == 'scalability':
            run_scalability_mode(args)
        elif args.mode == 'tuning':
            run_tuning_mode(args)
        elif args.mode == 'colors':
            run_color_complexity_mode(args)
        elif args.mode == 'single':
            run_single_mode(args)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Experimento interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error durante la ejecución: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
