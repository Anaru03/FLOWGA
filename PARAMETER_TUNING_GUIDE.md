# 🎛️ Guía de Tuning de Parámetros para Flow GA

## 📋 Parámetros Disponibles

### 1. **pop_size** (Tamaño de Población)
- **Rango recomendado**: 50-500
- **Efecto**: 
  - ⬆️ Mayor población → Más diversidad, más tiempo
  - ⬇️ Menor población → Más rápido, puede converger prematuramente
- **Valores sugeridos**: [50, 100, 150, 200, 250, 300, 500]

### 2. **generations** (Generaciones)
- **Rango recomendado**: 500-3000
- **Efecto**:
  - ⬆️ Más generaciones → Mayor exploración, más tiempo
  - ⬇️ Menos generaciones → Más rápido, puede no converger
- **Valores sugeridos**: [500, 800, 1000, 1500, 2000, 3000]

### 3. **mut_rate** (Tasa de Mutación)
- **Rango recomendado**: 0.005-0.15
- **Efecto**:
  - ⬆️ Alta mutación → Más exploración, previene convergencia prematura
  - ⬇️ Baja mutación → Más explotación, convergencia rápida
- **Valores sugeridos**: [0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.1, 0.15]

### 4. **elite** (Elitismo)
- **Rango recomendado**: 0-20
- **Efecto**:
  - ⬆️ Más elite → Preserva mejores soluciones, reduce diversidad
  - ⬇️ Sin elite (0) → Más diversidad, puede perder buenas soluciones
- **Valores sugeridos**: [0, 1, 2, 3, 5, 8, 10, 15, 20]

### 5. **tour_k** (Tamaño de Torneo)
- **Rango recomendado**: 1-15
- **Efecto**:
  - ⬆️ Torneo grande → Mayor presión de selección, convergencia rápida
  - ⬇️ Torneo pequeño → Menor presión, más diversidad
- **Valores sugeridos**: [1, 2, 3, 4, 5, 7, 10, 15]

---

## 🎯 Estrategias de Exploración

### A. Exploración Inicial (Grid Amplio)
**Objetivo**: Identificar rangos prometedores
```bash
python parameter_tuning.py --board-size 4 --num-colors 3 --runs 3
```
- Usa el grid por defecto (384 configs)
- 3 corridas por configuración
- ~30-60 minutos

### B. Estudio de Mutación
**Objetivo**: Encontrar la tasa óptima de mutación

Edita `parameter_tuning.py` líneas 805-810 y descomenta OPCIÓN 2:
```python
param_space = {
    'pop_size': [200],
    'generations': [1000],
    'mut_rate': [0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.1, 0.15],
    'elite': [2],
    'tour_k': [3]
}
```
- 8 configuraciones × 3 runs = 24 experimentos
- ~5-10 minutos

### C. Estudio de Población
**Objetivo**: Balance entre velocidad y calidad

Descomenta OPCIÓN 3:
```python
param_space = {
    'pop_size': [50, 100, 150, 200, 250, 300, 400, 500],
    'generations': [1000],
    'mut_rate': [0.03],
    'elite': [2],
    'tour_k': [3]
}
```
- 8 configuraciones × 3 runs = 24 experimentos
- ~5-10 minutos

### D. Estudio de Presión de Selección
**Objetivo**: Optimizar el torneo

Descomenta OPCIÓN 4:
```python
param_space = {
    'pop_size': [200],
    'generations': [1000],
    'mut_rate': [0.03],
    'elite': [2],
    'tour_k': [1, 2, 3, 4, 5, 7, 10, 15]
}
```
- 8 configuraciones × 3 runs = 24 experimentos
- ~5-10 minutos

### E. Estudio de Elitismo
**Objetivo**: Determinar cuántas soluciones preservar

Descomenta OPCIÓN 5:
```python
param_space = {
    'pop_size': [200],
    'generations': [1000],
    'mut_rate': [0.03],
    'elite': [0, 1, 2, 3, 5, 8, 10, 15, 20],
    'tour_k': [3]
}
```
- 9 configuraciones × 3 runs = 27 experimentos
- ~5-10 minutos

### F. Optimización Fina
**Objetivo**: Ajuste fino alrededor de valores prometedores

Descomenta OPCIÓN 6 (después de identificar rangos buenos):
```python
param_space = {
    'pop_size': [150, 175, 200, 225, 250],
    'generations': [800, 1000, 1200],
    'mut_rate': [0.02, 0.025, 0.03, 0.035, 0.04],
    'elite': [1, 2, 3],
    'tour_k': [2, 3, 4]
}
```
- 5×3×5×3×3 = 675 configuraciones
- Para tableros pequeños (4×4)

---

## 📊 Interpretación de Resultados

### Métricas Clave

1. **✅ Tasa de Éxito (Success Rate)**
   - Objetivo: ≥95%
   - Si <90%: Aumentar población o generaciones
   - Si 100%: Puedes reducir parámetros para velocidad

2. **⏱️ Tiempo Promedio**
   - Objetivo: Balance entre velocidad y éxito
   - Si muy alto: Reducir población o generaciones
   - Trade-off con tasa de éxito

3. **📊 Evaluaciones de Fitness**
   - Indica cuánto trabajo hace el GA
   - Menor = más eficiente
   - Correlaciona con tiempo

4. **🏅 Score Global (0-1)**
   - Combina éxito, tiempo y eficiencia
   - Más alto = mejor configuración general

5. **🔀 Pérdida de Diversidad**
   - 0.0 = mantiene diversidad total
   - 1.0 = converge a población homogénea
   - Si muy alta: aumentar mutación

### Recomendaciones según Resultados

| Síntoma | Posible Causa | Solución |
|---------|---------------|----------|
| Éxito bajo (<80%) | Convergencia prematura | ⬆️ Mutación, ⬆️ Población |
| Tiempo alto | Demasiadas evaluaciones | ⬇️ Población, ⬇️ Generaciones |
| Diversidad baja | Presión de selección alta | ⬇️ tour_k, ⬆️ Mutación |
| Sin convergencia | Demasiada exploración | ⬇️ Mutación, ⬆️ Elite |
| Elite = 0 falla | Pierde buenas soluciones | Use elite ≥ 1 |

---

## 🚀 Comandos Rápidos

```bash
# Exploración rápida (tablero pequeño)
python parameter_tuning.py --board-size 4 --num-colors 3 --runs 3

# Tablero mediano (más tiempo)
python parameter_tuning.py --board-size 5 --num-colors 4 --runs 5

# Tablero grande (mucho tiempo)
python parameter_tuning.py --board-size 6 --num-colors 5 --runs 5

# Con directorio personalizado
python parameter_tuning.py --board-size 4 --num-colors 3 --runs 3 --output mi_experimento

# Usando run_experiments.py
python run_experiments.py --mode tuning --board-size 4 --colors 3 --runs 3
```

---

## 📁 Archivos Generados

Después de ejecutar, encontrarás en `tuning_4x4/`:

1. **ranking_table.png** - Tabla visual con Top 15
2. **tuning_detailed_results.csv** - Todos los resultados
3. **tuning_summary.json** - Resumen estadístico
4. **impact_*.png** - Gráficos de impacto por parámetro
5. **heatmap_*.png** - Mapas de calor de interacciones

---

## 💡 Consejos Prácticos

### Para Presentación de Clase
1. Usa tablero 4×4 con 3 colores (rápido, claro)
2. Ejecuta OPCIÓN 2 (mutación) para mostrar impacto claro
3. La tabla mejorada se ve profesional en screenshots

### Para Investigación Profunda
1. Comienza con grid amplio (OPCIÓN 1)
2. Identifica parámetros más influyentes
3. Haz estudios enfocados (OPCIONES 2-5)
4. Optimización fina (OPCIÓN 6)

### Para Diferentes Tamaños
- **4×4**: Cualquier configuración funciona bien
- **5×5**: Requiere pop≥200, mut≈0.03
- **6×6**: Requiere pop≥300, gen≥1000
- **7×7+**: Requiere pop≥500, gen≥2000

---

## 🎨 Visualizaciones Disponibles

1. **Tabla de Ranking** (automática)
   - Top 15 configuraciones
   - Emojis para facilidad visual
   - Métricas clave destacadas

2. **Gráficos de Impacto**
   - Cómo cada parámetro afecta métricas
   - Identifica valores óptimos
   - 4 subplots: éxito, tiempo, evaluaciones, score

3. **Heatmaps**
   - Interacción entre 2 parámetros
   - Identifica combinaciones sinérgicas
   - pop_size×mut_rate, elite×tour_k

---

## 🔬 Ejemplo de Flujo Completo

```bash
# Paso 1: Exploración inicial (30 min)
python parameter_tuning.py --board-size 4 --num-colors 3 --runs 3 --output exp1_inicial

# Paso 2: Revisar resultados y identificar mejores rangos
# Ver ranking_table.png y gráficos impact_*.png

# Paso 3: Editar parameter_tuning.py para estudio enfocado
# Descomenta OPCIÓN 2 o 3 según lo que encontraste

# Paso 4: Estudio enfocado (10 min)
python parameter_tuning.py --board-size 4 --num-colors 3 --runs 5 --output exp2_mutacion

# Paso 5: Optimización fina (20 min)
# Descomenta OPCIÓN 6 con rangos ajustados
python parameter_tuning.py --board-size 4 --num-colors 3 --runs 5 --output exp3_fino

# Paso 6: Validar en tablero más grande
python parameter_tuning.py --board-size 5 --num-colors 4 --runs 5 --output exp4_validacion
```

---

## ❓ FAQ

**P: ¿Cuántas corridas por configuración?**
R: 3 es mínimo, 5 es bueno, 10 para papers científicos.

**P: ¿Qué parámetro tiene más impacto?**
R: Típicamente `mut_rate`, seguido de `pop_size`.

**P: ¿Por qué 100% de éxito en 4×4?**
R: Tableros pequeños son fáciles. Prueba 5×5 o 6×6.

**P: ¿Cómo acelerar experimentos?**
R: Reduce corridas a 3, usa grids enfocados (OPCIONES 2-5).

**P: ¿Qué es el "score"?**
R: Métrica combinada: 50% éxito + 30% tiempo + 20% eficiencia.
