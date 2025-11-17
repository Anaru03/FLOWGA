# 🧬 GUÍA COMPLETA DE EXPERIMENTACIÓN - FLOW GA

**Sistema Híbrido de Algoritmo Genético y Backtracking para Resolución del Juego Flow Free**

---

## 📋 TABLA DE CONTENIDOS

1. [Fundamento Teórico](#1-fundamento-teórico)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Configuración del Entorno](#3-configuración-del-entorno)
4. [Tipos de Experimentos](#4-tipos-de-experimentos)
5. [Plan de Pruebas Completo](#5-plan-de-pruebas-completo)
6. [Interpretación de Resultados](#6-interpretación-de-resultados)
7. [Análisis Estadístico](#7-análisis-estadístico)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. FUNDAMENTO TEÓRICO

### 1.1. El Problema: Flow Free

**Definición Formal:**
- **Entrada:** Tablero N×N con k pares de terminales de colores
- **Objetivo:** Conectar cada par de terminales con un camino del mismo color
- **Restricciones:**
  - Cada celda debe estar ocupada por exactamente un camino
  - Los caminos no pueden cruzarse
  - Los caminos solo pueden moverse horizontal o verticalmente

**Complejidad Computacional:**
- **Clase:** NP-Completo
- **Espacio de búsqueda:** Aproximadamente O(4^(N²-2k)) para backtracking naive
- **Implicación:** No existe algoritmo de tiempo polinomial conocido

### 1.2. Modelo Híbrido GA + Backtracking

#### 1.2.1. Algoritmo Genético (GA)

**Características:**
- **Tipo:** Algoritmo metaheurístico evolutivo
- **Fortaleza:** Exploración eficiente del espacio de soluciones
- **Debilidad:** No garantiza encontrar el óptimo global

**Componentes:**

1. **Representación (Codificación)**
   ```
   Individuo = Tablero N×N donde cada celda contiene un color
   Inicialización: Voronoi Manhattan (cada celda toma el color del terminal más cercano)
   ```

2. **Función de Fitness**
   ```
   fitness(individuo) = Σ penalties
   
   Penalizaciones:
   - Desconexión: +10,000 por terminal desconectado
   - Fragmentación: +100 por cada componente conexa extra del mismo color
   - Vacíos: +500 por celda vacía
   - Celdas ocupadas: -(número de celdas ocupadas)
   
   Óptimo: fitness = 0 (solución perfecta)
   ```

3. **Operadores Genéticos**
   
   **Selección por Torneo (Tournament Selection)**
   ```
   - Seleccionar K individuos aleatorios
   - Elegir el de mejor fitness
   - Parámetro tour_k: controla presión selectiva
     * tour_k = 1: selección aleatoria (baja presión)
     * tour_k = 3: estándar (presión moderada)
     * tour_k = 5+: alta presión selectiva
   ```

   **Crossover (Cruce)**
   ```
   - Tipo: Cruce uniforme por celda
   - Cada celda del hijo toma el color del padre1 o padre2 con 50% prob.
   - Terminales siempre se preservan
   ```

   **Mutación**
   ```
   - Para cada celda no-terminal:
     * Con probabilidad mut_rate, cambiar a un color aleatorio
   - Propósito: mantener diversidad genética
   - Parámetro crítico: afecta balance exploración/explotación
   ```

   **Elitismo**
   ```
   - Los mejores 'elite' individuos pasan intactos a la siguiente generación
   - Previene pérdida de buenas soluciones
   - Elite = 0: sin elitismo (máxima diversidad)
   - Elite = 2-5: estándar
   - Elite > 10: riesgo de convergencia prematura
   ```

4. **Criterios de Parada**
   ```
   - Solución perfecta encontrada (fitness == 0)
   - Máximo de generaciones alcanzado
   - Estancamiento: sin mejora por 50 generaciones
   ```

#### 1.2.2. Backtracking (BT)

**Características:**
- **Tipo:** Búsqueda completa con poda
- **Fortaleza:** Garantiza encontrar solución si existe
- **Debilidad:** Costo exponencial en el peor caso

**Estrategia:**
```
1. Ordenar colores por distancia Manhattan (heurística)
2. Para cada color:
   - Generar todos los caminos posibles entre terminales
   - Probar recursivamente con cada camino
   - Backtrack si no hay solución
3. Límite adaptativo de caminos según tamaño:
   - 4×4 a 7×7: 10,000 caminos por color
   - 8×8: 2,000 caminos
   - 9×9: 500 caminos
   - 10×10+: 100 caminos
```

**Optimización con GA:**
```
- Usar solución parcial del GA como punto de partida
- Reutilizar celdas que ya tienen el color correcto
- Reduce drásticamente el espacio de búsqueda
```

#### 1.2.3. Modelo Híbrido

**Flujo de Ejecución:**
```
1. Ejecutar GA(N, terminales, params)
   ├─ Si encuentra solución perfecta → ÉXITO (devolver solución)
   └─ Si no converge → Continuar a paso 2

2. Ejecutar BT(N, terminales, start_grid=solución_GA)
   ├─ Si encuentra solución → ÉXITO (devolver solución)
   └─ Si falla → FALLA (puzzle posiblemente imposible)
```

**Ventajas del Modelo Híbrido:**
- ✅ **Velocidad:** GA encuentra soluciones en ~10-60s (vs 1-10min de BT puro)
- ✅ **Robustez:** BT garantiza solución si GA falla
- ✅ **Sinergia:** Solución parcial de GA reduce espacio de búsqueda de BT en ~80-90%
- ✅ **Escalabilidad:** Permite abordar tableros 10×10+ donde BT solo es inviable

---

## 2. ARQUITECTURA DEL SISTEMA

### 2.1. Módulos Principales

```
FLOWGA/
├── genetic_algorithm.py      # Implementación del GA
│   ├── ga_solve_flow()      # Función principal
│   ├── fitness()            # Evaluación de individuos
│   ├── mutate()             # Operador de mutación
│   └── crossover()          # Operador de cruce
│
├── backtracking_solver.py    # Solver por backtracking
│   └── solve_flow_bt()      # Búsqueda exhaustiva con poda
│
├── puzzle_generator.py       # Generación de puzzles aleatorios
│   └── generate_random_puzzle()
│
├── metrics.py                # Recolección de métricas
│   ├── GAMetrics            # Clase para métricas del GA
│   └── GenerationMetrics    # Métricas por generación
│
├── scalability_experiments.py   # 🔬 Experimentos de escalabilidad
│   ├── run_scalability_experiments()
│   ├── identify_inefficiency_threshold()
│   └── identify_practical_limits()    # 🆕 Análisis de viabilidad
│
├── parameter_tuning.py       # 🎛️ Ajuste de hiperparámetros
│   ├── grid_search()
│   ├── summarize_results()
│   └── quick_tuning_study()
│
├── color_complexity_analysis.py  # Análisis NP-completitud
│   └── run_complete_color_study()
│
└── run_experiments.py        # 🚀 CLI unificada
    └── Interfaz de línea de comandos
```

### 2.2. Flujo de Datos

```
┌─────────────────┐
│  Generación de  │
│     Puzzle      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  Algoritmo      │─────▶│   Métricas   │
│   Genético      │      │   (fitness,  │
└────────┬────────┘      │  diversidad) │
         │               └──────────────┘
         │ (si falla)
         ▼
┌─────────────────┐
│  Backtracking   │
│  (con hint GA)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Solución     │
│    + Análisis   │
└─────────────────┘
```

---

## 3. CONFIGURACIÓN DEL ENTORNO

### 3.1. Requisitos del Sistema

**Sistema Operativo:**
- ✅ Linux/Ubuntu (recomendado para experimentos largos)
- ✅ Windows 10/11 con WSL2
- ✅ macOS

**Hardware Recomendado:**
- **CPU:** 4+ cores (experimentos se pueden paralelizar manualmente)
- **RAM:** 8GB mínimo, 16GB recomendado para tableros 10×10+
- **Almacenamiento:** 500MB para código + resultados

### 3.2. Instalación

#### Opción 1: WSL2 (Windows - Recomendado)

```bash
# 1. Abrir terminal WSL (Ubuntu)
cd /mnt/d/UVG/Modsim/FLOWGA  # Ajustar ruta según tu caso

# 2. Crear entorno virtual
python3 -m venv .venv

# 3. Activar entorno
source .venv/bin/activate

# 4. Actualizar pip
pip install --upgrade pip

# 5. Instalar dependencias
pip install -r requirements.txt

# 6. Verificar instalación
python -c "import matplotlib, numpy; print('✅ Dependencias OK')"
```

#### Opción 2: Linux/macOS Nativo

```bash
# Mismo proceso que WSL2
cd /ruta/a/FLOWGA
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### Opción 3: Windows PowerShell (No recomendado para experimentos largos)

```powershell
cd D:\UVG\Modsim\FLOWGA
python -m venv venv
.\venv\Scripts\Activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3. Verificación de Instalación

```bash
# Test rápido
python main.py
# Debe generar un puzzle 10×10 y resolverlo

# Test de experimentos
python run_experiments.py --mode single
```

---

## 4. TIPOS DE EXPERIMENTOS

### 4.1. Experimento de Escalabilidad

**Objetivo:** Medir cómo crece el costo computacional con el tamaño del tablero

**Comando:**
```bash
python run_experiments.py --mode scalability \
    --board-sizes 4 5 6 7 8 9 10 \
    --runs 10 \
    --output scalability_results
```

**Parámetros:**
- `--board-sizes`: Lista de tamaños a probar (ej: 4, 5, 6, 7, 8, 9, 10)
- `--runs`: Número de ejecuciones por tamaño (mínimo 10 para validez estadística)
- `--output`: Directorio donde guardar resultados
- `--colors-config`: (Opcional) Configuración manual de colores por tamaño

**Configuración de Colores (Auto):**
```
4×4 → 3 colores  (16 celdas, 6 terminales, 10 libres)
5×5 → 4 colores  (25 celdas, 8 terminales, 17 libres)
6×6 → 6 colores  (36 celdas, 12 terminales, 24 libres)
7×7 → 8 colores  (49 celdas, 16 terminales, 33 libres)
8×8 → 10 colores (64 celdas, 20 terminales, 44 libres)
9×9 → 12 colores (81 celdas, 24 terminales, 57 libres)
10×10 → 15 colores (100 celdas, 30 terminales, 70 libres)
```

**Métricas Capturadas:**
- ✅ Tiempo de ejecución GA
- ✅ Tiempo de ejecución BT (si se usa)
- ✅ Tiempo total (híbrido)
- ✅ Tasa de éxito del GA
- ✅ Tasa de uso del BT
- ✅ Número de evaluaciones de fitness
- ✅ Generaciones ejecutadas
- ✅ Pérdida de diversidad genética
- ✅ Tasa de convergencia a óptimos locales

**Salidas Generadas:**
```
scalability_results/
├── scalability_results.csv         # Datos completos por ejecución
├── scalability_summary.json        # Resumen estadístico
├── practical_limits.json           # 🆕 Análisis de viabilidad
├── scalability_loglog.png          # Curvas log-log de complejidad
└── efficiency_metrics.png          # Gráficas de eficiencia
```

**Análisis Automáticos:**
1. **Identificación de Punto de Ineficiencia:**
   - Detecta el tamaño donde GA deja de ser eficiente
   - Criterios: éxito <50%, eficiencia <0.3, óptimos locales >30%

2. **Límites Prácticos de Uso:** (🆕)
   - Identifica tamaño máximo viable según umbrales
   - Recomienda configuración óptima
   - Analiza costo-beneficio del modelo híbrido

**Tiempo Estimado:**
```
Configuración estándar (4-10, 10 runs):
- Con tableros pequeños (4-6): ~20-30 minutos
- Con tableros medianos (4-8): ~1-2 horas
- Con tableros grandes (4-10): ~3-5 horas
```

---

### 4.2. Experimento de Tuning de Hiperparámetros

**Objetivo:** Encontrar la configuración óptima de parámetros del GA

**Comando Básico:**
```bash
python run_experiments.py --mode tuning \
    --board-size 6 \
    --colors 6 \
    --runs 5 \
    --output tuning_6x6
```

**Comando con Parámetros Personalizados:**
```bash
python run_experiments.py --mode tuning \
    --board-size 6 \
    --colors 6 \
    --runs 5 \
    --custom-params "pop_size:100,200,300;mut_rate:0.01,0.03,0.05;elite:0,2,5;tour_k:2,3,5"
```

**Espacio de Hiperparámetros (Expandido 🆕):**

| Parámetro | Valores | Descripción | Recomendación |
|-----------|---------|-------------|---------------|
| `pop_size` | 50, 100, 150, 200, 300, 500 | Tamaño de población | 200-300 para tableros grandes |
| `generations` | 300, 500, 800, 1000, 1500 | Generaciones máximas | 1000+ para convergencia garantizada |
| `mut_rate` | 0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.1 | Tasa de mutación | 0.03-0.05 balance óptimo |
| `elite` | 0, 1, 2, 3, 5, 8, 10 | Individuos elitistas | 2-5 estándar |
| `tour_k` | 1, 2, 3, 4, 5, 7 | Tamaño de torneo | 3 presión moderada |

**Estrategias de Exploración:**

1. **Grid Search Completo** (exhaustivo)
   ```bash
   # Explora TODAS las combinaciones
   # Tiempo: ~2-8 horas para espacio completo
   python run_experiments.py --mode tuning --board-size 5 --runs 5
   ```

2. **Búsqueda Dirigida** (enfocada)
   ```bash
   # Explora rangos específicos
   # Ejemplo: optimizar población
   python run_experiments.py --mode tuning --board-size 6 --runs 5 \
       --custom-params "pop_size:100,150,200,250,300;generations:1000;mut_rate:0.03;elite:2;tour_k:3"
   ```

3. **Análisis de Interacciones** (avanzado)
   ```bash
   # Explorar interacciones entre 2 parámetros
   # Ejemplo: mutación vs elitismo
   python run_experiments.py --mode tuning --board-size 5 --runs 5 \
       --custom-params "pop_size:200;generations:1000;mut_rate:0.01,0.03,0.05,0.1;elite:0,2,5,10;tour_k:3"
   ```

**Métricas de Evaluación:**

**Score Combinado (Ranking):**
```
score = 0.5 × tasa_éxito + 0.3 × score_tiempo + 0.2 × score_eficiencia

donde:
  score_tiempo = 1 / (1 + tiempo/10)
  score_eficiencia = 1 / (1 + evals/100k)
```

**Salidas Generadas:**
```
tuning_6x6/
├── tuning_detailed_results.csv     # Resultados de cada ejecución
├── tuning_summary.json             # Ranking de configuraciones
├── ranking_table.png               # Tabla visual Top-15
├── impact_pop_size.png             # Impacto de población
├── impact_mut_rate.png             # Impacto de mutación
├── impact_elite.png                # Impacto de elitismo
├── impact_tour_k.png               # Impacto de torneo
├── heatmap_pop_mut.png             # Interacción población-mutación
└── heatmap_elite_tour.png          # Interacción elitismo-torneo
```

**Interpretación de Resultados:**

🏆 **Top Configuración:**
- Aparece en ranking_table.png y tuning_summary.json
- Usar estos parámetros para experimentos finales

📊 **Gráficas de Impacto:**
- Identifican sensibilidad a cada parámetro
- Curvas con pico → óptimo claro
- Curvas planas → parámetro poco relevante

🔥 **Heatmaps de Interacción:**
- Revelan sinergias entre parámetros
- Buscar "puntos calientes" (verde intenso)
- Evitar combinaciones malas (rojo)

---

### 4.3. Experimento de Complejidad por Colores

**Objetivo:** Demostrar la naturaleza NP-Completa analizando el impacto del número de colores

**Comando:**
```bash
python run_experiments.py --mode colors \
    --board-sizes 4 5 6 7 \
    --runs 15 \
    --output color_complexity_results
```

**Con Rangos Personalizados:**
```bash
python run_experiments.py --mode colors \
    --board-sizes 4 5 6 \
    --color-ranges "4:2,3,4,5,6;5:3,4,5,6,7,8;6:4,5,6,7,8,9,10" \
    --runs 15
```

**Hipótesis a Validar:**
1. **Más colores** → **problema más fácil** (más espacio libre)
2. Existe un **umbral de resolubilidad** donde el problema se vuelve imposible/muy difícil
3. La dificultad NO crece linealmente con el número de colores

**Métricas Capturadas:**
- Tasa de éxito por configuración (tamaño, colores)
- Tiempo promedio por número de colores
- Identificación de "frontera de resolubilidad"

**Salidas:**
```
color_complexity_results/
├── color_complexity_detailed.csv
├── color_complexity_summary.csv
└── solvability_thresholds.json
```

---

### 4.4. Experimento Individual

**Objetivo:** Probar una configuración específica con salida detallada

**Comando:**
```bash
python run_experiments.py --mode single
```

**Uso:** 
- Depuración
- Demostración interactiva
- Validación de cambios en el código

---

## 5. PLAN DE PRUEBAS COMPLETO

### 5.1. Fase 1: Validación Básica (30 min)

**Objetivo:** Verificar que todo funcione correctamente

```bash
# Test 1: Puzzle pequeño
python main.py
# Esperar: Solución en <10s

# Test 2: Experimento rápido de escalabilidad
python run_experiments.py --mode scalability \
    --board-sizes 4 5 \
    --runs 3 \
    --output test_scalability

# Test 3: Tuning rápido
python run_experiments.py --mode tuning \
    --board-size 4 \
    --colors 3 \
    --runs 2 \
    --output test_tuning
```

**Criterios de Éxito:**
- ✅ Todos los comandos terminan sin errores
- ✅ Se generan archivos CSV y JSON
- ✅ Las gráficas se crean correctamente

---

### 5.2. Fase 2: Escalabilidad Completa (3-5 horas)

**Objetivo:** Determinar límites prácticos del sistema

```bash
# Configuración recomendada
python run_experiments.py --mode scalability \
    --board-sizes 4 5 6 7 8 9 10 \
    --runs 10 \
    --output escalabilidad_completa
```

**Configuración para Tableros Grandes (10×10):**
```
🔥 Optimización aplicada automáticamente:
- Población: 200 (suficiente exploración)
- Generaciones: 300 (balance tiempo/calidad)
- Esto permite al GA tener ~60,000 evaluaciones
```

**Análisis Esperado:**

1. **Curvas Log-Log:** 
   - Verificar si el crecimiento es polinomial, exponencial o peor
   - Comparar con complejidad teórica O(4^N²)

2. **Punto de Ineficiencia:**
   - Esperar que aparezca entre 7×7 y 9×9
   - Si aparece en 6×6 → parámetros muy conservadores
   - Si no aparece hasta 10×10 → excelente configuración

3. **Límites Prácticos:** (🆕)
   - GA solo viable hasta: esperado 6×6 o 7×7
   - Modelo híbrido viable hasta: esperado 8×8 o 9×9
   - Tamaño óptimo: esperado 5×5 o 6×6

**Guardar Resultados:**
```bash
# Copiar resultados a carpeta de reportes
cp -r escalabilidad_completa/ reporte_escalabilidad/
```

---

### 5.3. Fase 3: Tuning Intensivo (Por Tamaño)

**Objetivo:** Encontrar configuración óptima para cada tamaño de tablero

#### 5.3.1. Tableros Pequeños (4×4, 5×5) - 2 horas

```bash
# 4x4 - Exploración exhaustiva
python run_experiments.py --mode tuning \
    --board-size 4 \
    --colors 3 \
    --runs 5 \
    --output tuning_4x4_final

# 5x5 - Exploración exhaustiva
python run_experiments.py --mode tuning \
    --board-size 5 \
    --colors 4 \
    --runs 5 \
    --output tuning_5x5_final
```

**Análisis:** 
- Identificar tendencias generales
- Estos tamaños convergen rápido → buenos para validar hipótesis

#### 5.3.2. Tableros Medianos (6×6, 7×7) - 4 horas

```bash
# 6x6
python run_experiments.py --mode tuning \
    --board-size 6 \
    --colors 6 \
    --runs 5 \
    --output tuning_6x6_final

# 7x7
python run_experiments.py --mode tuning \
    --board-size 7 \
    --colors 8 \
    --runs 5 \
    --output tuning_7x7_final
```

**Enfoque:**
- Usar resultados de 4×4 y 5×5 para guiar exploración
- Reducir espacio de búsqueda a rangos prometedores

#### 5.3.3. Tableros Grandes (8×8, 9×9) - 6-8 horas

```bash
# 8x8 - Búsqueda dirigida
python run_experiments.py --mode tuning \
    --board-size 8 \
    --colors 10 \
    --runs 3 \
    --custom-params "pop_size:200,300,500;generations:800,1000,1500;mut_rate:0.03,0.05;elite:2,3,5;tour_k:3,4,5" \
    --output tuning_8x8_final
```

**Nota:** 
- Reducir runs a 3 para ahorrar tiempo
- Enfocarse en población grande y muchas generaciones

---

### 5.4. Fase 4: Análisis de Complejidad NP (2-3 horas)

**Objetivo:** Demostrar relación entre colores y dificultad

```bash
python run_experiments.py --mode colors \
    --board-sizes 4 5 6 7 \
    --runs 15 \
    --output complejidad_np_final
```

**Análisis:**
1. Graficar tasa de éxito vs número de colores
2. Identificar "punto de quiebre" donde el problema se vuelve intratable
3. Validar hipótesis de NP-completitud

---

### 5.5. Fase 5: Validación Final (1 hora)

**Objetivo:** Confirmar resultados con configuración óptima encontrada

```bash
# Usar MEJOR configuración encontrada en tuning
# Ejemplo (ajustar según resultados):
python -c "
from genetic_algorithm import ga_solve_flow
from puzzle_generator import generate_random_puzzle
import time

# Parámetros óptimos (EJEMPLO - ajustar según tuning)
OPTIMAL = {
    'pop_size': 250,
    'generations': 1000,
    'mut_rate': 0.03,
    'elite': 3,
    'tour_k': 3
}

# Probar 20 veces en tablero 6x6
success = 0
total_time = 0

for i in range(20):
    terminals = generate_random_puzzle(6, 6)
    start = time.time()
    sol, _ = ga_solve_flow(6, terminals, **OPTIMAL, verbose=False, collect_metrics=False)
    elapsed = time.time() - start
    total_time += elapsed
    if sol and fitness(sol, terminals) == 0:
        success += 1
    print(f'Run {i+1}/20: {\"✅\" if sol else \"❌\"} ({elapsed:.2f}s)')

print(f'\n📊 Resumen:')
print(f'   Tasa de éxito: {success}/20 ({success*5}%)')
print(f'   Tiempo promedio: {total_time/20:.2f}s')
"
```

---

## 6. INTERPRETACIÓN DE RESULTADOS

### 6.1. Métricas Clave

#### 6.1.1. Tasa de Éxito del GA

**Definición:** Porcentaje de ejecuciones donde el GA encuentra una solución perfecta

**Interpretación:**
```
≥ 80%: Excelente - Configuración óptima para este tamaño
60-79%: Bueno - Configuración funcional pero mejorable
30-59%: Regular - Requiere ajuste de parámetros
< 30%: Pobre - Configuración inadecuada o problema muy difícil
```

**Factores que la afectan:**
- 📊 Tamaño del tablero (↑ tamaño → ↓ éxito)
- 🎨 Número de colores (↑ colores → ↑ éxito)
- 👥 Tamaño de población (↑ población → ↑ éxito, pero ↑ tiempo)
- 🔄 Número de generaciones (↑ generaciones → ↑ éxito, pero ↑ tiempo)

#### 6.1.2. Tiempo de Ejecución

**GA Solo:**
```
< 10s:   Muy rápido - Ideal para uso interactivo
10-60s:  Rápido - Aceptable para experimentos
60-300s: Lento - Viable pero no óptimo
> 300s:  Muy lento - Considerar reducir tamaño/parámetros
```

**Modelo Híbrido (GA + BT):**
```
< 30s:   Excelente
30-120s: Bueno
> 120s:  Límite de viabilidad práctica
```

#### 6.1.3. Evaluaciones de Fitness

**Interpretación:**
- Evaluaciones = pop_size × generations_executed
- Cada evaluación requiere BFS por cada color
- Costo por evaluación: O(N² × k) donde k = número de colores

**Ejemplo:**
```
Tablero 6×6, 6 colores:
- Población: 200
- Generaciones: 800
- Evaluaciones: 200 × 800 = 160,000
- Costo por evaluación: ~36 × 6 = 216 operaciones BFS
- Costo total: ~34.5 millones de operaciones
```

#### 6.1.4. Diversidad Genética

**Definición:** Medida de variabilidad entre individuos de la población

**Valores:**
```
0.8-1.0: Alta diversidad (exploración activa)
0.4-0.7: Diversidad moderada (convergiendo)
0.1-0.3: Baja diversidad (cerca de convergencia)
< 0.1:   Convergencia prematura (posible óptimo local)
```

**Pérdida de Diversidad:**
```
< 20%: Excelente mantenimiento de diversidad
20-40%: Normal (convergencia controlada)
40-60%: Alta pérdida (riesgo de óptimos locales)
> 60%: Pérdida excesiva (revisar mutación y elite)
```

#### 6.1.5. Uso de Backtracking

**Tasa de Uso BT:**
```
0-20%:   Excelente - GA resuelve la mayoría
20-50%:  Bueno - Modelo híbrido efectivo
50-80%:  Regular - GA poco efectivo
> 80%:   Pobre - GA falla sistemáticamente
```

**Interpretación por tamaño:**
- **4×4 a 6×6:** Esperar 0-10% uso BT
- **7×7 a 8×8:** Esperar 20-50% uso BT
- **9×9 a 10×10:** Esperar 50-90% uso BT

---

### 6.2. Análisis de Curvas

#### 6.2.1. Evolución del Fitness

**Gráfica:** fitness vs generación

**Patrones Esperados:**

1. **Convergencia Rápida:**
   ```
   Fitness inicial: ~5000-10000
   Generación 100: ~100-500
   Generación 300: ~0-50
   Generación 500: 0 (solución)
   ```
   - ✅ Configuración bien ajustada
   - ✅ Problema abordable

2. **Convergencia Lenta:**
   ```
   Fitness inicial: ~5000-10000
   Generación 100: ~2000-4000
   Generación 500: ~500-1000
   Generación 1000: ~100-300
   ```
   - ⚠️ Necesita más generaciones o mejor configuración
   - ⚠️ Problema difícil

3. **Estancamiento:**
   ```
   Fitness inicial: ~5000
   Generación 100: ~1000
   Generación 200-1000: ~950-1050 (sin mejora)
   ```
   - ❌ Óptimo local
   - ❌ Necesita más mutación o diversidad

#### 6.2.2. Curva Log-Log (Escalabilidad)

**Ejes:** log(tamaño) vs log(tiempo)

**Interpretación de Pendiente:**
```
Pendiente 1-2: Crecimiento lineal/cuadrático (EXCELENTE)
Pendiente 2-3: Crecimiento polinomial bajo (BUENO)
Pendiente 3-4: Crecimiento polinomial alto (REGULAR)
Pendiente > 4: Crecimiento cuasi-exponencial (POBRE)
```

**Ejemplo de Análisis:**
```
Si ajuste da: tiempo = 0.5 × N^2.3

Interpretación:
- Complejidad práctica: O(N^2.3)
- Para N=10: ~0.5 × 10^2.3 ≈ 100s
- Para N=20: ~0.5 × 20^2.3 ≈ 870s (¡14.5 min!)
- Conclusión: Viable hasta ~N=12
```

---

### 6.3. Identificación de Problemas

#### 6.3.1. GA con Baja Tasa de Éxito

**Síntomas:**
- Éxito < 30%
- Alta tasa de uso de BT
- Convergencia a óptimos locales

**Causas Posibles:**
1. **Población insuficiente:** Probar duplicar pop_size
2. **Pocas generaciones:** Aumentar a 1500-2000
3. **Baja mutación:** Aumentar mut_rate a 0.05-0.08
4. **Alto elitismo:** Reducir elite a 0-2
5. **Problema muy difícil:** Aumentar número de colores

**Solución:**
```bash
# Re-ejecutar con parámetros más agresivos
python run_experiments.py --mode tuning \
    --board-size X \
    --runs 5 \
    --custom-params "pop_size:300,500;generations:1500,2000;mut_rate:0.05,0.08,0.1;elite:0,1,2;tour_k:2,3"
```

#### 6.3.2. Tiempo de Ejecución Excesivo

**Síntomas:**
- Tiempo > 5 minutos para tableros medianos
- Muchas evaluaciones sin mejora

**Causas:**
1. **Parámetros demasiado grandes:** pop_size × generations muy alto
2. **Tablero demasiado grande:** 10×10+ con pocos colores
3. **Fitness costoso:** Muchos colores aumentan costo BFS

**Solución:**
- Reducir población o generaciones
- Aumentar número de colores
- Implementar criterio de parada temprana más agresivo

#### 6.3.3. Convergencia Prematura

**Síntomas:**
- Pérdida de diversidad > 60%
- Estancamiento en fitness alto (~100-500)
- Elite alto con mutación baja

**Solución:**
- Aumentar mut_rate (0.05-0.1)
- Reducir elite (0-2)
- Reducir tour_k (2-3)

---

## 7. ANÁLISIS ESTADÍSTICO

### 7.1. Validez Estadística

**Mínimo de Ejecuciones:**
- **Experimentos de tuning:** 5 runs por configuración
- **Experimentos de escalabilidad:** 10 runs por tamaño
- **Análisis de complejidad:** 15 runs por configuración

**Justificación:**
- Puzzles aleatorios → variabilidad inherente
- GA estocástico → diferentes resultados por run
- Necesario para calcular media, desviación y IC

### 7.2. Métricas Estadísticas

**Media (μ):** Tendencia central
```python
μ = Σ valores / n
```

**Desviación Estándar (σ):** Dispersión
```python
σ = √(Σ(valor - μ)² / (n-1))
```

**Intervalo de Confianza 95%:**
```python
IC = μ ± (1.96 × σ / √n)
```

**Coeficiente de Variación:**
```python
CV = (σ / μ) × 100%

Interpretación:
< 10%:  Baja variabilidad (resultados consistentes)
10-25%: Variabilidad moderada (aceptable)
> 25%:  Alta variabilidad (resultados poco predecibles)
```

### 7.3. Pruebas de Hipótesis

#### Hipótesis 1: "El GA es más eficiente que BT solo"

**Test:** Comparar tiempos GA vs BT en 20 puzzles idénticos

**Estadístico:** Prueba t de Student pareada

**Python:**
```python
from scipy import stats

# tiempos_ga = [t1, t2, ..., t20]
# tiempos_bt = [t1, t2, ..., t20]

t_stat, p_value = stats.ttest_rel(tiempos_ga, tiempos_bt)

if p_value < 0.05:
    print("✅ GA es significativamente más rápido")
else:
    print("❌ No hay diferencia significativa")
```

#### Hipótesis 2: "Más colores → mayor tasa de éxito"

**Test:** Correlación de Pearson

```python
# colores = [3, 4, 5, 6, 7, 8, 9, 10]
# tasas_exito = [0.4, 0.6, 0.75, 0.85, 0.9, 0.95, 0.98, 0.99]

r, p_value = stats.pearsonr(colores, tasas_exito)

print(f"Correlación: {r:.3f}")
if p_value < 0.05 and r > 0.7:
    print("✅ Fuerte correlación positiva significativa")
```

#### Hipótesis 3: "El modelo híbrido extiende la viabilidad"

**Test:** Comparar tamaño máximo viable GA vs Híbrido

**Criterio:** Tasa de éxito ≥ 70%, Tiempo ≤ 120s

---

## 8. TROUBLESHOOTING

### 8.1. Problemas Comunes

#### Error: "externally-managed-environment"

**Síntoma:**
```
error: externally-managed-environment
```

**Causa:** Python sistema protegido (PEP 668)

**Solución:**
```bash
# Crear y usar entorno virtual
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

#### Error: "No module named 'matplotlib'"

**Causa:** Dependencias no instaladas

**Solución:**
```bash
pip install matplotlib numpy
# o
pip install -r requirements.txt
```

---

#### Warning: "Cognitive Complexity"

**Síntoma:** Warnings de linter sobre complejidad

**Causa:** Funciones grandes (común en código experimental)

**Solución:** ⚠️ Son solo warnings, **no afectan la ejecución**

---

#### Experimento muy lento

**Síntomas:**
- Un solo run tarda >10 minutos
- Memoria creciendo constantemente

**Diagnóstico:**
```bash
# Ejecutar con verbose para ver progreso
python main.py  # Observar barras de progreso
```

**Soluciones:**
1. **Reducir parámetros:**
   ```python
   # En main.py o experimentos
   pop_size = 100  # en vez de 300
   generations = 500  # en vez de 1000
   ```

2. **Verificar que no haya loops infinitos:**
   - GA tiene límite de generaciones ✅
   - BT tiene límite de caminos ✅

3. **Usar tableros más pequeños para tests:**
   ```bash
   python run_experiments.py --mode scalability --board-sizes 4 5 --runs 3
   ```

---

#### Out of Memory

**Síntomas:**
- Programa crash con "MemoryError"
- Sistema se congela

**Causas:**
- Población muy grande (>1000)
- Tableros muy grandes (>12×12)
- Métricas acumulando datos sin límite

**Soluciones:**
```python
# Opción 1: Reducir población
pop_size = 200  # máximo recomendado

# Opción 2: Desactivar métricas
collect_metrics = False

# Opción 3: Límite en generaciones
generations = 500  # no exceder 2000
```

---

### 8.2. Validación de Resultados

#### ¿Cómo sé si mis resultados son correctos?

**Checklist de Validación:**

✅ **Soluciones verificadas:**
```python
# Cada solución debe pasar verify_solution_detailed()
from verify_solution import verify_solution_detailed
is_valid = verify_solution_detailed(solution, terminals)
```

✅ **Consistencia estadística:**
- Desviación estándar razonable (CV < 30%)
- Tendencias coherentes (más tamaño → más tiempo)

✅ **Archivos generados:**
- CSV con datos completos
- JSON con resumen
- Gráficas PNG

✅ **Valores dentro de rangos esperados:**
```
Tiempo GA 5×5: 5-30s
Tiempo GA 8×8: 30-180s
Éxito 5×5: 70-95%
Éxito 8×8: 30-70%
```

---

### 8.3. Optimización de Rendimiento

#### Para experimentos largos:

1. **Usar screen/tmux (Linux/WSL):**
   ```bash
   # Crear sesión persistente
   screen -S experimentos
   
   # Ejecutar experimento
   python run_experiments.py --mode scalability ...
   
   # Detach: Ctrl+A, luego D
   # Reattach: screen -r experimentos
   ```

2. **Guardar logs:**
   ```bash
   python run_experiments.py ... 2>&1 | tee experimento.log
   ```

3. **Monitorear recursos:**
   ```bash
   # Terminal adicional
   htop  # Linux/WSL
   # o
   top
   ```

4. **Ejecutar de noche:**
   ```bash
   # Iniciar a medianoche
   echo "cd /path/to/FLOWGA && source .venv/bin/activate && python run_experiments.py ..." | at 00:00
   ```

---

## 9. CHECKLIST DE ENTREGA

Antes de finalizar el proyecto, asegurar que tienes:

### Experimentos Ejecutados:
- [ ] Escalabilidad completa (4-10, 10 runs)
- [ ] Tuning por tamaño (al menos 3 tamaños)
- [ ] Análisis de complejidad por colores
- [ ] Validación con configuración óptima

### Archivos de Resultados:
- [ ] `scalability_results/` con todos los CSVs y gráficas
- [ ] `tuning_*/` para cada tamaño analizado
- [ ] `color_complexity_results/`
- [ ] `practical_limits.json` 🆕

### Análisis Completo:
- [ ] Curvas log-log interpretadas
- [ ] Punto de ineficiencia identificado
- [ ] Límites prácticos documentados 🆕
- [ ] Configuración óptima por tamaño
- [ ] Heatmaps de interacciones de parámetros

### Documentación:
- [ ] README.md actualizado
- [ ] Esta guía completa (GUIA_COMPLETA_EXPERIMENTOS.md)
- [ ] Guía de presentación (PLAN_PRESENTACION_RESULTADOS.md)

### Validación:
- [ ] Todas las soluciones verificadas
- [ ] Métricas estadísticas calculadas
- [ ] Pruebas de hipótesis ejecutadas

---

## 10. REFERENCIAS Y RECURSOS

### Papers Relacionados:
- **"The Complexity of the Puzzles of Final Fantasy XIII-2"** - Viglietta (2015)
  - Demuestra que variantes de Flow son NP-Completos

- **"Genetic Algorithms for Combinatorial Optimization"** - Holland (1975)
  - Fundamentos teóricos de algoritmos genéticos

### Recursos en Línea:
- [Flow Free (juego original)](https://www.bigduckgames.com/flowfree)
- [Documentación Matplotlib](https://matplotlib.org/stable/contents.html)
- [SciPy Stats](https://docs.scipy.org/doc/scipy/reference/stats.html)

### Contacto y Soporte:
- **Repositorio:** `github.com/Anaru03/FLOWGA`
- **Issues:** Reportar bugs en GitHub Issues
- **Documentación adicional:** Ver `/docs` en el repo

---

**Última actualización:** Noviembre 11, 2025  
**Versión:** 2.0 (con mejoras de escalabilidad y análisis de límites prácticos)

