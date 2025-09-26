# Demostración de la modularización del proyecto Flow
# Este script muestra cómo usar los módulos independientemente

print("=== DEMOSTRACIÓN DE MODULARIZACIÓN ===\n")

# 1. Importar módulos específicos
print("1. Importando módulos específicos...")
from config import FIT_PARAMS
from genetic_algorithm import fitness, random_individual
from puzzle_generator import generate_random_puzzle
from utils import neighbors
from visualization import print_grid_color

print("✓ Módulos importados correctamente\n")

# 2. Mostrar configuración
print("2. Configuración del fitness:")
for key, value in FIT_PARAMS.items():
    print(f"   {key}: {value}")
print()

# 3. Generar un puzzle simple
print("3. Generando puzzle 4x4 con 3 colores...")
terminals = generate_random_puzzle(N=4, n_colors=3)
print(f"✓ Terminales generados: {list(terminals.keys())}\n")

# 4. Mostrar puzzle
puzzle = [["." for _ in range(4)] for _ in range(4)]
for col, (a, b) in terminals.items():
    puzzle[a[0]][a[1]] = col
    puzzle[b[0]][b[1]] = col

print("4. Puzzle generado:")
print_grid_color(puzzle, terminals, "")

# 5. Crear individuo inicial
print("5. Creando individuo inicial con método Voronoi...")
individual = random_individual(4, terminals)
print_grid_color(individual, terminals, "Individuo inicial:")

# 6. Calcular fitness
print("6. Calculando fitness del individuo:")
fit_score = fitness(individual, terminals)
print(f"✓ Fitness score: {fit_score:.2f}\n")

# 7. Mostrar vecinos de una celda
print("7. Demostrando función utilities - vecinos de (1,1):")
neighs = list(neighbors(4, 1, 1))
print(f"   Vecinos: {neighs}\n")

print("=== MODULARIZACIÓN COMPLETADA ===")
print("Cada funcionalidad está ahora en su módulo correspondiente:")
print("• config.py - Configuración y constantes")
print("• utils.py - Utilidades básicas")
print("• puzzle_generator.py - Generación de puzzles")
print("• genetic_algorithm.py - Algoritmo genético")
print("• visualization.py - Visualización")
print("• backtracking_solver.py - Solver exacto")
print("• main.py - Programa principal ⭐")
print("\nEjecuta con: python main.py")