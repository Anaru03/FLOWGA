# 🧬 Guía de Experimentación - FLOWGA

Esta guía te muestra cómo usar el sistema de experimentación automática para analizar el rendimiento del algoritmo genético con diferentes configuraciones.

## 📋 Contenido

1. [Instalación](#instalación)
2. [Experimentos de Escalabilidad](#experimentos-de-escalabilidad)
3. [Tuning de Parámetros](#tuning-de-parámetros)
4. [Casos de Uso Comunes](#casos-de-uso-comunes)
5. [Interpretación de Resultados](#interpretación-de-resultados)

---

## 🔧 Instalación

```powershell
# Instalar dependencias (si no están instaladas)
pip install matplotlib numpy
```

---

## 📊 Experimentos de Escalabilidad

### Objetivo
Medir cómo escala el costo computacional (tiempo y evaluaciones de fitness) con el tamaño del tablero.

### Uso Básico

```powershell
# Escalabilidad estándar (4x4, 5x5, 6x6, 7x7)
python run_experiments.py --mode scalability --runs 10

# Personalizar tamaños de tablero
python run_experiments.py --mode scalability --board-sizes 4 5 6 7 8 --runs 10

# Con configuración de colores específica
python run_experiments.py --mode scalability --board-sizes 4 5 6 --colors-config "4:3,5:4,6:6" --runs 10
```

### Uso desde Python

```python
from scalability_experiments import run_complete_scalability_study

# Estudio completo
results, summaries, inefficiency_point = run_complete_scalability_study(
    board_sizes=[4, 5, 6, 7],
    colors_config={4: 3, 5: 4, 6: 6, 7: 8},
    runs_per_size=10,
    output_dir="my_scalability_results"
)
```

### Resultados Generados

- **CSV**: `scalability_results.csv` - Datos detallados de cada corrida
- **JSON**: `scalability_summary.json` - Estadísticas resumidas
- **Gráfico Log-Log**: `scalability_loglog.png` - Tiempo y evaluaciones vs tamaño
- **Métricas de Eficiencia**: `efficiency_metrics.png` - Tasas de éxito, uso de BT, etc.

---

## 🎛️ Tuning de Parámetros

### Objetivo
Encontrar la mejor combinación de parámetros del GA para un tamaño de tablero específico.

### Parámetros del GA

- **pop_size**: Tamaño de la población (ej: 100, 200, 300)
- **generations**: Número máximo de generaciones (ej: 500, 1000, 1500)
- **mut_rate**: Tasa de mutación (ej: 0.01, 0.03, 0.05)
- **elite**: Número de individuos élite (ej: 0, 2, 5)
- **tour_k**: Tamaño del torneo para selección (ej: 2, 3, 5)

### Uso Básico

```powershell
# Tuning rápido con valores por defecto
python run_experiments.py --mode tuning --board-size 5 --runs 5

# Personalizar tablero y colores
python run_experiments.py --mode tuning --board-size 6 --colors 5 --runs 5
```

### Tuning Personalizado

```powershell
# Explorar diferentes tamaños de población
python run_experiments.py --mode tuning --board-size 5 --runs 5 \
    --custom-params "pop_size:50,100,150,200,250,300;generations:1000;mut_rate:0.03;elite:2;tour_k:3"

# Explorar tasas de mutación
python run_experiments.py --mode tuning --board-size 5 --runs 5 \
    --custom-params "pop_size:200;generations:1000;mut_rate:0.005,0.01,0.02,0.03,0.05,0.1;elite:2;tour_k:3"

# Explorar elite vs torneo
python run_experiments.py --mode tuning --board-size 6 --runs 5 \
    --custom-params "pop_size:200;generations:1000;mut_rate:0.03;elite:0,2,5,10;tour_k:2,3,5,7"
```

### Uso desde Python

```python
from parameter_tuning import grid_search, summarize_results, print_ranking_table

# Definir espacio de parámetros
param_space = {
    'pop_size': [100, 200, 300],
    'generations': [500, 1000],
    'mut_rate': [0.01, 0.03, 0.05],
    'elite': [0, 2, 5],
    'tour_k': [2, 3, 5]
}

# Ejecutar grid search
results = grid_search(
    param_space=param_space,
    board_size=5,
    num_colors=4,
    runs_per_config=5
)

# Analizar resultados
summaries = summarize_results(results)
print_ranking_table(summaries, top_n=10)
```

### Resultados Generados

- **CSV**: `tuning_detailed_results.csv` - Todos los experimentos
- **JSON**: `tuning_summary.json` - Ranking de configuraciones
- **Gráficos de Impacto**: `impact_*.png` - Impacto de cada parámetro
- **Heatmaps**: `heatmap_*.png` - Interacciones entre parámetros

---

## 🎯 Casos de Uso Comunes

### Caso 1: Encontrar Configuración Óptima para 5x5

```powershell
python run_experiments.py --mode tuning --board-size 5 --colors 4 --runs 10
```

**Interpretación**: Busca entre 108 configuraciones diferentes (3×2×3×3×3) y ejecuta 10 corridas de cada una. Genera un ranking con las mejores configuraciones.

### Caso 2: Comparar Poblaciones Pequeñas vs Grandes

```python
from parameter_tuning import grid_search, plot_parameter_impact

param_space = {
    'pop_size': [50, 100, 150, 200, 250, 300, 400, 500],
    'generations': [1000],
    'mut_rate': [0.03],
    'elite': [2],
    'tour_k': [3]
}

results = grid_search(param_space, board_size=6, num_colors=5, runs_per_config=10)
summaries = summarize_results(results)

# Visualizar impacto
plot_parameter_impact(summaries, 'pop_size', 'impact_population.png')
```

### Caso 3: Estudio de Escalabilidad Completo

```python
from scalability_experiments import run_complete_scalability_study

# Desde 4x4 hasta 8x8
results, summaries, inefficiency = run_complete_scalability_study(
    board_sizes=[4, 5, 6, 7, 8],
    runs_per_size=20,  # 20 corridas para mejor estadística
    output_dir="full_scalability"
)

# El sistema automáticamente:
# - Identifica el punto donde el GA pierde eficiencia
# - Genera gráficos log-log
# - Calcula tasas de uso de backtracking
# - Exporta todo a CSV y JSON
```

### Caso 4: Análisis de Sensibilidad de Mutación

```powershell
# Probar mutaciones desde muy bajas hasta muy altas
python run_experiments.py --mode tuning --board-size 5 --runs 8 \
    --custom-params "pop_size:200;generations:1000;mut_rate:0.001,0.005,0.01,0.02,0.03,0.05,0.07,0.1,0.15;elite:2;tour_k:3"
```

### Caso 5: Comparación Elite vs No-Elite

```python
from parameter_tuning import grid_search, plot_comparative_heatmap

param_space = {
    'pop_size': [150, 200, 250],
    'generations': [1000],
    'mut_rate': [0.03],
    'elite': [0, 1, 2, 3, 5, 7, 10],
    'tour_k': [2, 3, 5]
}

results = grid_search(param_space, board_size=5, num_colors=4, runs_per_config=5)
summaries = summarize_results(results)

# Heatmap: elite vs tour_k
plot_comparative_heatmap(summaries, 'elite', 'tour_k', 'success_rate', 'elite_vs_tournament.png')
```

---

## 📈 Interpretación de Resultados

### Métricas Clave

#### Escalabilidad

- **Tiempo promedio**: Tiempo de ejecución del GA
- **Evaluaciones de fitness**: Total de evaluaciones realizadas
- **Tasa de éxito GA**: % de veces que el GA encuentra solución sin BT
- **Uso de backtracking**: % de veces que se necesitó BT
- **Tasa de óptimos locales**: % de convergencia temprana sin éxito

#### Tuning

- **Success Rate**: Tasa de éxito (más alto = mejor)
- **Avg Time**: Tiempo promedio (más bajo = mejor)
- **Fitness Evals**: Evaluaciones de fitness (indica esfuerzo computacional)
- **Score**: Métrica combinada que balancea éxito, tiempo y eficiencia

### Identificar el Mejor Parámetro

**Score combinado**:
```
Score = 0.5 × success_rate + 0.3 × (1 / (1 + norm_time)) + 0.2 × (1 / (1 + norm_evals))
```

- **Score > 0.7**: Configuración excelente
- **Score 0.5-0.7**: Configuración buena
- **Score < 0.5**: Configuración subóptima

### Punto de Ineficiencia del GA

El sistema identifica automáticamente cuándo el GA deja de ser eficiente:

- ✅ **Eficiente**: Success rate > 50%, óptimos locales < 30%
- ⚠️ **Ineficiente**: Success rate < 50% o alta tasa de óptimos locales

---

## 🔬 Experimentos Sugeridos

### Para el Reporte (Punto 7 de la tabla)

**Objetivo**: Identificar punto de ineficiencia y complejidad

```powershell
# 1. Escalabilidad (múltiples tamaños)
python run_experiments.py --mode scalability --board-sizes 4 5 6 7 8 --runs 15 --output escalabilidad_completa

# 2. Tuning para cada tamaño
python run_experiments.py --mode tuning --board-size 5 --runs 10 --output tuning_5x5
python run_experiments.py --mode tuning --board-size 6 --runs 10 --output tuning_6x6
python run_experiments.py --mode tuning --board-size 7 --runs 10 --output tuning_7x7
```

### Para Análisis Estadístico

```python
from scalability_experiments import run_scalability_experiments, calculate_summary_statistics

# 50 corridas para estadísticas robustas
results = run_scalability_experiments(
    board_sizes=[5, 6, 7],
    colors_config={5: 4, 6: 6, 7: 8},
    runs_per_size=50,
    pop_size=200,
    generations=1000
)

summaries = calculate_summary_statistics(results)

# Analizar desviaciones estándar, intervalos de confianza, etc.
for size, summary in summaries.items():
    print(f"{size}x{size}: {summary.ga_avg_time:.3f} ± {summary.ga_std_time:.3f}s")
```

---

## 💡 Consejos

### Optimización de Tiempo

1. **Empezar con pocas corridas** (3-5) para probar
2. **Aumentar a 10-20** para resultados finales
3. **Usar tableros pequeños** (4x4, 5x5) para tuning inicial
4. **Paralelizar** corridas independientes (futura mejora)

### Elección de Parámetros

- **Tableros pequeños (4x4, 5x5)**: Pop=100-200, Gen=500-1000
- **Tableros medianos (6x6, 7x7)**: Pop=200-300, Gen=1000-1500
- **Tableros grandes (8x8+)**: Pop=300-500, Gen=1500-2000

### Análisis de Resultados

1. **Revisar el ranking** de configuraciones
2. **Observar los gráficos de impacto** individual
3. **Analizar heatmaps** para interacciones
4. **Comparar con métricas baseline** (config por defecto)

---

## 📁 Estructura de Resultados

```
scalability_results/
├── scalability_results.csv         # Datos crudos
├── scalability_summary.json        # Resumen estadístico
├── scalability_loglog.png          # Gráfico log-log
└── efficiency_metrics.png          # Métricas de eficiencia

tuning_results/
├── tuning_detailed_results.csv     # Todos los experimentos
├── tuning_summary.json             # Ranking de configs
├── impact_pop_size.png             # Impacto de población
├── impact_mut_rate.png             # Impacto de mutación
├── impact_elite.png                # Impacto de elite
├── impact_tour_k.png               # Impacto de torneo
├── heatmap_pop_mut.png            # Interacción pop × mutación
└── heatmap_elite_tour.png         # Interacción elite × torneo
```

---

## 🚀 Próximos Pasos

1. Ejecutar experimentos básicos para familiarizarse
2. Modificar parámetros según necesidades
3. Analizar gráficos y tablas generadas
4. Documentar hallazgos en el reporte
5. Considerar implementar optimizaciones basadas en resultados

---

## ❓ Troubleshooting

**Error: `ModuleNotFoundError: No module named 'matplotlib'`**
```powershell
pip install matplotlib numpy
```

**Error: Puzzle inválido (demasiados colores)**
- Reducir número de colores o aumentar tamaño de tablero
- Regla: colores ≤ (N × N) ÷ 3

**Experimentos muy lentos**
- Reducir `runs_per_config`
- Usar tableros más pequeños
- Limitar el espacio de parámetros

---

## 📚 Referencias

- `scalability_experiments.py`: Experimentos de escalabilidad
- `parameter_tuning.py`: Tuning automático de parámetros
- `run_experiments.py`: Interfaz CLI unificada
- `metrics.py`: Sistema de métricas del GA

---

**¡Buena suerte con los experimentos! 🧬🔬**
