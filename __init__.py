# Paquete Flow Solver - Algoritmo Genético para resolver puzzles Flow
"""
Este paquete contiene módulos para generar y resolver puzzles del juego Flow
usando Algoritmos Genéticos y Backtracking como respaldo.

Módulos:
- config: Configuración y constantes del proyecto
- utils: Tipos y utilidades básicas
- visualization: Funciones para visualizar los puzzles
- genetic_algorithm: Implementación del Algoritmo Genético
- backtracking_solver: Solver usando Backtracking
- puzzle_generator: Generador de puzzles aleatorios
- main: Programa principal

Uso:
    python main.py
"""

__version__ = "1.0.0"
__author__ = "Flow Solver Team"

from .backtracking_solver import solve_flow_bt
# Exportar las funciones más importantes para uso modular
from .genetic_algorithm import fitness, ga_solve_flow, is_perfect
# Importar función principal para facilitar el uso como paquete
from .main import main
from .puzzle_generator import generate_random_puzzle
from .visualization import print_grid_color

__all__ = [
    'main',
    'ga_solve_flow',
    'fitness', 
    'is_perfect',
    'generate_random_puzzle',
    'print_grid_color',
    'solve_flow_bt'
]