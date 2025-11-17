# 🚀 FLOWGA - Inicio Rápido

**Solucionador Híbrido de Flow Free con Algoritmo Genético + Backtracking**

---

## ⚡ Setup en 5 Minutos

### 1. Prerrequisitos
- Python 3.10+ 
- WSL2/Ubuntu (recomendado) o Linux/macOS

### 2. Instalación

```bash
# Clonar/navegar al directorio
cd /mnt/d/UVG/Modsim/FLOWGA  # Ajustar ruta

# Crear entorno virtual
python3 -m venv .venv

# Activar entorno
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Verificar Instalación

```bash
# Test rápido
python main.py
# Debe generar y resolver un puzzle 10×10 en ~30-60s
```

---

## 🎮 Uso Básico

### Resolver un Puzzle Aleatorio

```python
from genetic_algorithm import ga_solve_flow
from puzzle_generator import generate_random_puzzle

# Generar puzzle 6×6 con 6 colores
terminals = generate_random_puzzle(6, 6)

# Resolver con GA
solution, metrics = ga_solve_flow(
    N=6, 
    terminals=terminals,
    pop_size=200,
    generations=1000,
    mut_rate=0.03,
    elite=3,
    tour_k=3,
    verbose=True
)

if solution:
    print("✅ Solución encontrada!")
else:
    print("❌ GA no encontró solución")
```

### Resolver con Modelo Híbrido

```python
from genetic_algorithm import ga_solve_flow
from backtracking_solver import solve_flow_bt
from puzzle_generator import generate_random_puzzle
from verify_solution import is_perfect

N = 7
terminals = generate_random_puzzle(N, 7)

# Intentar con GA primero
solution, _ = ga_solve_flow(N, terminals, verbose=True)

# Si falla, usar BT con hint del GA
if not solution or not is_perfect(solution, terminals):
    print("🔄 GA falló, intentando con backtracking...")
    solution = solve_flow_bt(N, terminals, start_grid=solution)

if solution and is_perfect(solution, terminals):
    print("✅ Solución encontrada con modelo híbrido!")
```

---

## 🔬 Ejecutar Experimentos

### Experimento de Escalabilidad

```bash
# Tableros 4×4 a 8×8, 10 runs cada uno
python run_experiments.py --mode scalability \
    --board-sizes 4 5 6 7 8 \
    --runs 10 \
    --output escalabilidad_test
```

**Salidas:**
- `escalabilidad_test/scalability_results.csv` - Datos completos
- `escalabilidad_test/scalability_summary.json` - Resumen estadístico
- `escalabilidad_test/practical_limits.json` - Límites prácticos
- `escalabilidad_test/*.png` - Gráficas de análisis

**Tiempo estimado:** ~1-2 horas

---

### Tuning de Hiperparámetros

```bash
# Buscar configuración óptima para 6×6
python run_experiments.py --mode tuning \
    --board-size 6 \
    --colors 6 \
    --runs 5 \
    --output tuning_6x6_test
```

**Salidas:**
- `tuning_6x6_test/tuning_detailed_results.csv`
- `tuning_6x6_test/tuning_summary.json` - 🏆 Top configuraciones
- `tuning_6x6_test/ranking_table.png` - Top-15 visual
- `tuning_6x6_test/impact_*.png` - Impacto de cada parámetro
- `tuning_6x6_test/heatmap_*.png` - Interacciones

**Tiempo estimado:** ~2-4 horas (5,292 configuraciones)

**Búsqueda rápida (parámetros reducidos):**
```bash
python run_experiments.py --mode tuning \
    --board-size 6 \
    --colors 6 \
    --runs 3 \
    --custom-params "pop_size:100,200,300;generations:500,1000;mut_rate:0.03,0.05;elite:2,5;tour_k:3" \
    --output tuning_6x6_rapido
```
**Tiempo estimado:** ~30-45 minutos (72 configuraciones)

---

### Análisis de Complejidad por Colores

```bash
# Demostrar NP-completitud
python run_experiments.py --mode colors \
    --board-sizes 4 5 6 \
    --runs 15 \
    --output complejidad_colores
```

**Salidas:**
- `complejidad_colores/color_complexity_detailed.csv`
- `complejidad_colores/color_complexity_summary.csv`
- `complejidad_colores/solvability_thresholds.json`

**Tiempo estimado:** ~1-2 horas

---

## 📊 Ver Resultados

### Resumen de Escalabilidad

```bash
# Ver resumen JSON
cat escalabilidad_test/scalability_summary.json | python -m json.tool

# Ver límites prácticos
cat escalabilidad_test/practical_limits.json | python -m json.tool
```

### Top Configuraciones de Tuning

```bash
# Ver ranking
cat tuning_6x6_test/tuning_summary.json | python -m json.tool

# Mostrar Top-3
python -c "
import json
with open('tuning_6x6_test/tuning_summary.json') as f:
    data = json.load(f)
    for i, config in enumerate(data['top_configurations'][:3], 1):
        print(f'{i}. Score: {config[\"score\"]:.3f}')
        print(f'   pop={config[\"pop_size\"]}, gens={config[\"generations\"]}, mut={config[\"mut_rate\"]}, elite={config[\"elite\"]}, tour_k={config[\"tour_k\"]}')
        print(f'   Éxito: {config[\"success_rate\"]*100:.1f}%, Tiempo: {config[\"avg_time\"]:.2f}s')
        print()
"
```

### Abrir Gráficas

```bash
# Linux/WSL
xdg-open escalabilidad_test/scalability_loglog.png
xdg-open tuning_6x6_test/ranking_table.png

# macOS
open escalabilidad_test/scalability_loglog.png
```

---

## 🎯 Casos de Uso Comunes

### 1. Resolver Puzzle Específico

```python
# puzzle_custom.py
from genetic_algorithm import ga_solve_flow

# Definir terminales manualmente
# Formato: [(fila1, col1), (fila2, col2)]
terminals = {
    1: [(0, 0), (4, 4)],  # Color 1: esquinas opuestas
    2: [(0, 4), (4, 0)],  # Color 2: otras esquinas
    3: [(2, 1), (2, 3)]   # Color 3: centro
}

solution, metrics = ga_solve_flow(
    N=5,
    terminals=terminals,
    pop_size=200,
    generations=1000,
    verbose=True
)

# Visualizar
from visualization import print_solution
print_solution(solution, terminals)
```

---

### 2. Benchmark de Configuraciones

```python
# benchmark.py
from genetic_algorithm import ga_solve_flow
from puzzle_generator import generate_random_puzzle
import time

configs = [
    {'pop_size': 100, 'generations': 500},
    {'pop_size': 200, 'generations': 1000},
    {'pop_size': 300, 'generations': 1500}
]

N = 6
runs = 10

for config in configs:
    successes = 0
    total_time = 0
    
    for _ in range(runs):
        terminals = generate_random_puzzle(N, 6)
        start = time.time()
        sol, _ = ga_solve_flow(N, terminals, **config, verbose=False)
        elapsed = time.time() - start
        total_time += elapsed
        if sol:
            successes += 1
    
    print(f"Config {config}:")
    print(f"  Éxito: {successes}/{runs} ({successes/runs*100:.1f}%)")
    print(f"  Tiempo promedio: {total_time/runs:.2f}s")
    print()
```

---

### 3. Validar Solución

```python
from verify_solution import verify_solution_detailed, is_perfect

# Verificar solución
is_valid, errors = verify_solution_detailed(solution, terminals)

if is_valid:
    print("✅ Solución válida")
else:
    print("❌ Solución inválida:")
    for error in errors:
        print(f"  - {error}")

# Check rápido
if is_perfect(solution, terminals):
    print("✅ Solución perfecta!")
```

---

## 📚 Documentación Completa

- **[GUIA_COMPLETA_EXPERIMENTOS.md](GUIA_COMPLETA_EXPERIMENTOS.md)** - Todo sobre experimentos
  - Fundamento teórico completo
  - Plan de pruebas detallado
  - Interpretación de resultados
  - Troubleshooting
  
- **[PLAN_PRESENTACION_RESULTADOS.md](PLAN_PRESENTACION_RESULTADOS.md)** - Cómo presentar
  - Estructura de presentación
  - Plantillas de slides
  - Análisis de visualizaciones
  - Backup slides para preguntas

- **[EXPERIMENTS_GUIDE.md](EXPERIMENTS_GUIDE.md)** - Guía original de experimentos

- **[README.md](README.md)** - Información general del proyecto

---

## 🔧 Troubleshooting Rápido

### Error: "externally-managed-environment"
```bash
# Usar entorno virtual
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Experimento muy lento
```bash
# Reducir parámetros
python run_experiments.py --mode scalability \
    --board-sizes 4 5 \
    --runs 3  # En vez de 10
```

### Out of Memory
```python
# En genetic_algorithm.py o main.py
pop_size = 200  # Reducir de 300-500
collect_metrics = False  # Desactivar métricas
```

### Ver progreso en tiempo real
```bash
# Ejecutar con verbose
python main.py  # Muestra barras de progreso

# O guardar logs
python run_experiments.py ... 2>&1 | tee experimento.log
```

---

## 🎓 Parámetros Recomendados por Tamaño

Basado en experimentos de tuning:

| Tamaño | pop_size | generations | mut_rate | elite | tour_k |
|--------|----------|-------------|----------|-------|--------|
| 4×4    | 100      | 300         | 0.03     | 2     | 3      |
| 5×5    | 150      | 500         | 0.03     | 3     | 3      |
| 6×6    | 200      | 800         | 0.03     | 3     | 3      |
| 7×7    | 250      | 1000        | 0.05     | 2     | 3      |
| 8×8    | 300      | 1500        | 0.05     | 2     | 3      |
| 9×9+   | Usar modelo híbrido (GA + BT)                |

**Nota:** Ejecutar tuning para tu hardware específico puede dar mejores resultados.

---

## 🚀 Flujo de Trabajo Recomendado

### Para Investigación/Tarea:

1. **Setup inicial (5 min)**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python main.py  # Verificar
   ```

2. **Experimento de validación (30 min)**
   ```bash
   python run_experiments.py --mode scalability \
       --board-sizes 4 5 6 \
       --runs 5 \
       --output validacion
   ```

3. **Escalabilidad completa (3-5 horas - dejar corriendo)**
   ```bash
   # En screen/tmux o de noche
   python run_experiments.py --mode scalability \
       --board-sizes 4 5 6 7 8 9 10 \
       --runs 10 \
       --output escalabilidad_completa
   ```

4. **Tuning por tamaño (2-4 horas cada uno)**
   ```bash
   # Ejecutar para 2-3 tamaños clave
   python run_experiments.py --mode tuning \
       --board-size 6 --runs 5 --output tuning_6x6
   
   python run_experiments.py --mode tuning \
       --board-size 7 --runs 5 --output tuning_7x7
   ```

5. **Análisis de resultados (1 hora)**
   ```bash
   # Ver JSONs, gráficas, llenar plantillas del PLAN_PRESENTACION
   ```

6. **Preparar presentación (2-3 horas)**
   ```bash
   # Usar PLAN_PRESENTACION_RESULTADOS.md como guía
   # Crear slides, insertar gráficas, practicar
   ```

---

## 📧 Contacto y Soporte

- **Repositorio:** `github.com/Anaru03/FLOWGA` (si existe)
- **Issues:** Reportar en GitHub Issues
- **Documentación:** Ver carpeta `/docs` o archivos `.md` en raíz

---

## 📌 Comandos Más Usados

```bash
# Activar entorno
source .venv/bin/activate

# Test rápido
python main.py

# Escalabilidad
python run_experiments.py --mode scalability --board-sizes 4 5 6 --runs 5

# Tuning
python run_experiments.py --mode tuning --board-size 6 --runs 5

# Ver resultados
cat */scalability_summary.json | python -m json.tool
cat */practical_limits.json | python -m json.tool

# Abrir gráficas (Linux/WSL)
xdg-open */scalability_loglog.png
xdg-open */ranking_table.png
```

---

**¡Listo para empezar! 🎉**

Para información detallada, ver [GUIA_COMPLETA_EXPERIMENTOS.md](GUIA_COMPLETA_EXPERIMENTOS.md)

