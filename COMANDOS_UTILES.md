# 🚀 Scripts de Comandos Útiles - FLOWGA

Este archivo contiene comandos listos para copiar y pegar en PowerShell.

---

## 🎨 COMPLEJIDAD POR NÚMERO DE COLORES (NP-COMPLETO) ⭐ NUEVO

### Análisis básico (detecta límites de resolubilidad)
```powershell
python run_experiments.py --mode colors --board-sizes 4 5 6 --runs 10
```

### Análisis extendido con más tamaños
```powershell
python run_experiments.py --mode colors --board-sizes 4 5 6 7 --runs 15 --output frontera_np
```

### Análisis con rangos específicos de colores
```powershell
python run_experiments.py --mode colors --board-sizes 4 5 6 --runs 10 --color-ranges "4:3,4,5,6,7,8;5:4,5,6,7,8,9,10;6:6,8,10,12,14,16"
```

### Análisis profundo (más corridas para mayor precisión)
```powershell
python run_experiments.py --mode colors --board-sizes 5 6 7 --runs 20 --output analisis_profundo
```

### Con parámetros GA personalizados
```powershell
python run_experiments.py --mode colors --board-sizes 5 6 --runs 10 --pop-size 300 --generations 1500 --mut-rate 0.02
```

---

## 📊 ESCALABILIDAD

### Experimento básico (4x4, 5x5, 6x6, 7x7)
```powershell
python run_experiments.py --mode scalability --runs 10
```

### Escalabilidad extendida (hasta 8x8)
```powershell
python run_experiments.py --mode scalability --board-sizes 4 5 6 7 8 --runs 15 --output escalabilidad_completa
```

### Escalabilidad rápida (test)
```powershell
python run_experiments.py --mode scalability --board-sizes 4 5 --runs 3 --output test_escalabilidad
```

### Con configuración personalizada de colores
```powershell
python run_experiments.py --mode scalability --board-sizes 5 6 7 --colors-config "5:4,6:6,7:8" --runs 10
```

---

## 🎛️ TUNING DE PARÁMETROS

### Tuning rápido (valores por defecto)
```powershell
python run_experiments.py --mode tuning --board-size 5 --runs 5
```

### Tuning con tablero 6x6
```powershell
python run_experiments.py --mode tuning --board-size 6 --colors 5 --runs 8 --output tuning_6x6
```

### Explorar tamaños de población
```powershell
python run_experiments.py --mode tuning --board-size 5 --runs 5 --custom-params "pop_size:50,100,150,200,250,300;generations:1000;mut_rate:0.03;elite:2;tour_k:3"
```

### Explorar tasas de mutación
```powershell
python run_experiments.py --mode tuning --board-size 5 --runs 5 --custom-params "pop_size:200;generations:1000;mut_rate:0.005,0.01,0.02,0.03,0.05,0.1;elite:2;tour_k:3"
```

### Explorar elite
```powershell
python run_experiments.py --mode tuning --board-size 5 --runs 5 --custom-params "pop_size:200;generations:1000;mut_rate:0.03;elite:0,1,2,3,5,7,10;tour_k:3"
```

### Explorar tamaño de torneo
```powershell
python run_experiments.py --mode tuning --board-size 5 --runs 5 --custom-params "pop_size:200;generations:1000;mut_rate:0.03;elite:2;tour_k:2,3,5,7,10"
```

### Grid search completo (muchas combinaciones)
```powershell
python run_experiments.py --mode tuning --board-size 6 --runs 10 --custom-params "pop_size:100,200,300;generations:500,1000;mut_rate:0.01,0.03,0.05;elite:0,2,5;tour_k:2,3,5"
```

---

## 🔬 EXPERIMENTOS COMBINADOS

### Suite completa para reporte (INCLUYE NP-COMPLETO) ⭐
```powershell
# 1. Complejidad por colores (NP-Completo)
python run_experiments.py --mode colors --board-sizes 4 5 6 7 --runs 15 --output reporte_np_completo

# 2. Escalabilidad
python run_experiments.py --mode scalability --board-sizes 4 5 6 7 --runs 15 --output reporte_escalabilidad

# 3. Tuning para cada tamaño
python run_experiments.py --mode tuning --board-size 5 --runs 10 --output reporte_tuning_5x5
python run_experiments.py --mode tuning --board-size 6 --runs 10 --output reporte_tuning_6x6
python run_experiments.py --mode tuning --board-size 7 --runs 10 --output reporte_tuning_7x7
```

### Análisis de sensibilidad (un parámetro a la vez)
```powershell
# Población
python run_experiments.py --mode tuning --board-size 5 --runs 8 --custom-params "pop_size:50,100,150,200,250,300,400,500;generations:1000;mut_rate:0.03;elite:2;tour_k:3" --output sensibilidad_poblacion

# Mutación
python run_experiments.py --mode tuning --board-size 5 --runs 8 --custom-params "pop_size:200;generations:1000;mut_rate:0.001,0.005,0.01,0.02,0.03,0.05,0.07,0.1,0.15;elite:2;tour_k:3" --output sensibilidad_mutacion

# Elite
python run_experiments.py --mode tuning --board-size 5 --runs 8 --custom-params "pop_size:200;generations:1000;mut_rate:0.03;elite:0,1,2,3,5,7,10,15,20;tour_k:3" --output sensibilidad_elite

# Torneo
python run_experiments.py --mode tuning --board-size 5 --runs 8 --custom-params "pop_size:200;generations:1000;mut_rate:0.03;elite:2;tour_k:2,3,4,5,7,10,15,20" --output sensibilidad_torneo
```

---

## 🧪 CASOS ESPECIALES

### Poblaciones muy pequeñas (puede fallar más)
```powershell
python run_experiments.py --mode tuning --board-size 5 --runs 10 --custom-params "pop_size:20,30,40,50,75,100;generations:2000;mut_rate:0.03;elite:0;tour_k:3"
```

### Generaciones muy largas (convergencia garantizada)
```powershell
python run_experiments.py --mode tuning --board-size 6 --runs 5 --custom-params "pop_size:200;generations:2000,3000,5000;mut_rate:0.03;elite:2;tour_k:3"
```

### Sin elite (selección pura)
```powershell
python run_experiments.py --mode tuning --board-size 5 --runs 10 --custom-params "pop_size:100,200,300;generations:1000;mut_rate:0.01,0.03,0.05;elite:0;tour_k:2,3,5"
```

### Elite alto (presión selectiva fuerte)
```powershell
python run_experiments.py --mode tuning --board-size 5 --runs 10 --custom-params "pop_size:200;generations:1000;mut_rate:0.03;elite:10,20,30,40,50;tour_k:3"
```

---

## 🐍 DESDE PYTHON

### Importar y usar directamente

```python
# Complejidad por colores (NP-Completo)
from color_complexity_analysis import run_complete_color_study

results, summaries, thresholds = run_complete_color_study(
    board_sizes=[4, 5, 6],
    runs_per_config=10,
    output_dir="mis_resultados_np"
)

# Ver umbrales detectados
for board_size, threshold in thresholds.items():
    print(f"{board_size}×{board_size}: max {threshold.max_solvable_colors} colores")
```

```python
# Escalabilidad
from scalability_experiments import run_complete_scalability_study

results, summaries, inefficiency = run_complete_scalability_study(
    board_sizes=[4, 5, 6, 7],
    runs_per_size=10,
    output_dir="mis_resultados"
)
```

```python
# Tuning
from parameter_tuning import quick_tuning_study

results, summaries = quick_tuning_study(
    board_size=5,
    num_colors=4,
    runs_per_config=5,
    output_dir="mi_tuning"
)
```

```python
# Grid search personalizado
from parameter_tuning import grid_search, summarize_results, print_ranking_table

param_space = {
    'pop_size': [100, 200, 300],
    'generations': [1000],
    'mut_rate': [0.01, 0.03, 0.05],
    'elite': [0, 2, 5],
    'tour_k': [2, 3, 5]
}

results = grid_search(
    param_space=param_space,
    board_size=5,
    num_colors=4,
    runs_per_config=5
)

summaries = summarize_results(results)
print_ranking_table(summaries, top_n=10)
```

```python
# Visualizaciones
from parameter_tuning import plot_parameter_impact, plot_comparative_heatmap

# Impacto individual
plot_parameter_impact(summaries, 'pop_size', 'impacto_poblacion.png')

# Heatmap de interacción
plot_comparative_heatmap(summaries, 'elite', 'tour_k', 'success_rate', 'heatmap.png')
```

---

## 📋 EJEMPLOS RÁPIDOS

### Script de ejemplos interactivo
```powershell
python ejemplos_rapidos.py
```

### Ejemplo individual desde Python
```python
from ejemplos_rapidos import ejemplo_0_complejidad_colores
ejemplo_0_complejidad_colores()
```

---

## 🧪 ANÁLISIS DE FRONTERA NP-COMPLETO

### Explorar densidad crítica (colores vs celdas)
```powershell
# Tablero 5x5 (25 celdas): probar desde 50% hasta 100% de densidad
python run_experiments.py --mode colors --board-sizes 5 --runs 15 --color-ranges "5:8,10,12,14,16,18,20,22,25"
```

### Identificar transición de fase (donde éxito cae dramáticamente)
```powershell
python run_experiments.py --mode colors --board-sizes 6 --runs 20 --color-ranges "6:12,15,18,21,24,27,30,33,36"
```

### Comparar diferentes tamaños con misma densidad
```powershell
# Densidad ~0.5: 4x4→8col, 5x5→12col, 6x6→18col, 7x7→24col
python run_experiments.py --mode colors --board-sizes 4 5 6 7 --runs 15 --color-ranges "4:8;5:12,13;6:18;7:24,25"
```

---

## 🔧 UTILIDADES

### Verificar instalación
```powershell
python -c "import matplotlib, numpy; print('✅ Dependencias OK')"
```

### Limpiar resultados anteriores
```powershell
Remove-Item -Recurse -Force test_*
Remove-Item -Recurse -Force scalability_results
Remove-Item -Recurse -Force tuning_results
```

### Ver ayuda del CLI
```powershell
python run_experiments.py --help
```

---

## ⏱️ TIEMPOS ESTIMADOS

- **Experimento único** (5x5, 1 config, 1 color): ~1-5 segundos
- **Análisis de colores** (1 tamaño, 5 colores, 10 runs): ~5-8 minutos
- **Tuning rápido** (9 configs, 3 runs): ~2-3 minutos
- **Tuning medio** (27 configs, 5 runs): ~8-10 minutos
- **Tuning completo** (108 configs, 10 runs): ~40-60 minutos
- **Escalabilidad** (4 tamaños, 10 runs): ~15-20 minutos
- **Complejidad NP** (3 tamaños, 6 colores c/u, 10 runs): ~30-45 minutos
- **Suite completa** para reporte: ~3-4 horas

---

## 💡 RECOMENDACIONES

1. **Empezar simple**: Pocas corridas (3-5) para probar
2. **Incrementar**: 10-20 corridas para resultados finales
3. **Guardar todo**: Usar `--output` para organizar resultados
4. **Revisar gráficos**: Los PNG generados son muy informativos
5. **Usar CSV/JSON**: Para análisis posterior en Excel, R, etc.
6. **Análisis NP-Completo**: Usa el modo `colors` para identificar límites de resolubilidad ⭐
7. **Frontera de resolubilidad**: Los heatmaps y gráficos de frontera muestran dónde el problema se vuelve intratable

---

## 📈 RESULTADOS CLAVE

### Qué buscar en análisis de colores:
- **Tasa de éxito < 30%**: Problema probablemente intratable con configuración actual
- **Heatmap verde → rojo**: Transición de fase donde complejidad explota
- **Frontera de resolubilidad**: Línea que separa región resoluble de intratable
- **Puntuación de dificultad > 70**: Configuración muy difícil para el GA
- **Uso de backtracking > 80%**: GA ineficiente, dominado por búsqueda exhaustiva

---

**¡Feliz experimentación! 🧬**
