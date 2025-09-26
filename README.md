# Flow Solver - Versión Modularizada

## Descripción
Este proyecto utiliza Algoritmos Genéticos para resolver puzzles del juego Flow. La versión modularizada organiza el código en módulos especializados para facilitar el mantenimiento y comprensión.

## Estructura del Proyecto

```
Proyecto_simulacion/
├── __init__.py                 # Inicialización del paquete
├── config.py                   # Configuración y constantes
├── utils.py                    # Tipos y utilidades básicas
├── visualization.py            # Funciones de visualización
├── genetic_algorithm.py        # Algoritmo Genético
├── backtracking_solver.py      # Solver con Backtracking
├── puzzle_generator.py         # Generador de puzzles
├── main.py                     # Programa principal ⭐
├── demo_modularizacion.py      # Demostración de uso modular
└── README_modular.md           # Este archivo
```

## Módulos

### 1. `config.py`
- Configuración de colores (colorama)
- Parámetros del fitness
- Constantes globales

### 2. `utils.py`
- Definición de tipos (`Coord`, `Color`)
- Función `neighbors()` para obtener celdas vecinas
- Función `bfs_connected()` para verificar conectividad

### 3. `visualization.py`
- Función `print_grid_color()` para mostrar puzzles con colores
- Manejo de terminales en colorama

### 4. `genetic_algorithm.py`
- Implementación completa del Algoritmo Genético
- Funciones de fitness, selección, cruce y mutación
- Inicialización tipo Voronoi Manhattan

### 5. `backtracking_solver.py`
- Solver exacto usando Backtracking
- Puede usar solución del GA como punto de partida
- Garantiza encontrar solución si existe

### 6. `puzzle_generator.py`
- Genera puzzles aleatorios siempre resolubles
- Método del camino serpenteante
- Transformaciones geométricas (rotación, reflexión)

### 7. `main.py`
- Función principal que coordina todos los módulos
- Lógica de flujo: GA → Backtracking
- Interfaz de usuario

## Uso

### Ejecutar la versión modular:
```bash
python Proyecto_refactorizado.py
```

### Ejecutar la versión original:
```bash
python Proyecto.py
```

## Beneficios de la Modularización

1. **Separación de responsabilidades**: Cada módulo tiene una función específica
2. **Reutilización**: Los módulos pueden ser importados independientemente
3. **Mantenimiento**: Más fácil localizar y modificar funcionalidades específicas
4. **Escalabilidad**: Fácil agregar nuevos algoritmos o características
5. **Testing**: Cada módulo puede ser probado independientemente
6. **Legibilidad**: Código más organizado y comprensible

## Dependencias
- `colorama` (opcional): Para visualización con colores
- Bibliotecas estándar de Python: `typing`, `random`, `collections`

## Configuración
Los parámetros del Algoritmo Genético y fitness pueden ajustarse en `config.py`:
- Tamaño de población
- Número de generaciones  
- Tasa de mutación
- Pesos de la función de fitness

## 🚀 Uso

**Ejecutar el programa:**
```bash
python main.py
```

**Uso modular específico:**
```python
from genetic_algorithm import ga_solve_flow, fitness
from puzzle_generator import generate_random_puzzle
from visualization import print_grid_color
```