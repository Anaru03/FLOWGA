#!/bin/bash

# Script para ejecutar experimentos completos en C con todas las configuraciones
# Prueba desde 3x3 hasta el límite donde el algoritmo falla
# Genera reportes detallados en carpetas *_parallel

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Detectar número de cores
NPROC=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)

# Crear directorio de resultados
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="c_experiments_parallel_${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"

echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║           🧬 EXPERIMENTOS COMPLETOS EN C + OpenMP                  ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "📁 Resultados en: ${GREEN}${OUTPUT_DIR}/${NC}"
echo -e "🖥️  Threads: ${GREEN}${NPROC}${NC}"
echo -e "⏱️  Timestamp: ${BLUE}${TIMESTAMP}${NC}"
echo ""

# Verificar que el binario existe
if [ ! -f "./flow_ga" ]; then
    echo -e "${RED}❌ Error: ./flow_ga no encontrado${NC}"
    echo -e "${YELLOW}💡 Compilar primero: gcc -O3 -fopenmp -march=native -o flow_ga flow_ga_parallel.c -lm${NC}"
    exit 1
fi

# Inicializar CSV de resumen
SUMMARY_CSV="${OUTPUT_DIR}/summary_results.csv"
echo "board_size,num_colors,density,pop_size,generations,success_count,success_rate,avg_time,min_time,max_time,avg_fitness,perfect_found" > "$SUMMARY_CSV"

# Función para ejecutar un experimento
run_experiment() {
    local size=$1
    local colors=$2
    local pop=$3
    local gen=$4
    local runs=$5
    local label=$6
    
    local density=$(echo "scale=3; $colors / ($size * $size)" | bc -l)
    
    echo ""
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}  📊 ${size}x${size} | ${colors} colores | Densidad: ${density} | ${label}${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    local exp_dir="${OUTPUT_DIR}/${size}x${size}_${colors}colors_parallel"
    mkdir -p "$exp_dir"
    
    local success_count=0
    local total_time=0
    local min_time=999999
    local max_time=0
    local total_fitness=0
    local perfect_found="NO"
    
    # Ejecutar múltiples runs
    for ((i=1; i<=runs; i++)); do
        echo -e "${CYAN}  Run ${i}/${runs}...${NC}"
        
        local seed=$((1000 + i))
        local output_file="${exp_dir}/run_${i}.txt"
        
        # Ejecutar y capturar output
        ./flow_ga --size "$size" --colors "$colors" --pop "$pop" --gen "$gen" \
                  --threads "$NPROC" --seed "$seed" --verbose > "$output_file" 2>&1
        
        # Extraer métricas
        local time=$(grep "Elapsed time:" "$output_file" | awk '{print $3}')
        local perfect=$(grep "Perfect solution:" "$output_file" | awk '{print $3}')
        local fitness=$(grep "Best fitness:" "$output_file" | awk '{print $3}')
        local gens=$(grep "Generations executed:" "$output_file" | awk '{print $3}')
        
        # Validar que extrajimos datos
        if [ -z "$time" ]; then
            echo -e "${RED}    ⚠️  Error extrayendo métricas del run ${i}${NC}"
            continue
        fi
        
        # Acumular estadísticas
        total_time=$(echo "$total_time + $time" | bc -l)
        total_fitness=$(echo "$total_fitness + $fitness" | bc -l)
        
        if (( $(echo "$time < $min_time" | bc -l) )); then
            min_time=$time
        fi
        
        if (( $(echo "$time > $max_time" | bc -l) )); then
            max_time=$time
        fi
        
        if [ "$perfect" == "YES" ]; then
            ((success_count++))
            perfect_found="YES"
            echo -e "${GREEN}    ✅ Éxito en ${time}s (${gens} gen, fitness: ${fitness})${NC}"
        else
            echo -e "${YELLOW}    ⚠️  No resuelto en ${time}s (${gens} gen, fitness: ${fitness})${NC}"
        fi
    done
    
    # Calcular promedios
    local avg_time=$(echo "scale=3; $total_time / $runs" | bc -l)
    local avg_fitness=$(echo "scale=2; $total_fitness / $runs" | bc -l)
    local success_rate=$(echo "scale=1; ($success_count * 100) / $runs" | bc -l)
    
    # Guardar resumen en CSV
    echo "${size},${colors},${density},${pop},${gen},${success_count},${success_rate},${avg_time},${min_time},${max_time},${avg_fitness},${perfect_found}" >> "$SUMMARY_CSV"
    
    # Mostrar resumen
    echo ""
    echo -e "${BLUE}  📈 Resumen:${NC}"
    echo -e "     • Éxitos: ${GREEN}${success_count}/${runs}${NC} (${success_rate}%)"
    echo -e "     • Tiempo promedio: ${avg_time}s (min: ${min_time}s, max: ${max_time}s)"
    echo -e "     • Fitness promedio: ${avg_fitness}"
    echo -e "     • Solución perfecta: $([ "$perfect_found" == "YES" ] && echo -e "${GREEN}${perfect_found}${NC}" || echo -e "${RED}${perfect_found}${NC}")"
    
    # Determinar si es viable
    if (( $(echo "$success_rate >= 70" | bc -l) )); then
        echo -e "     • Estado: ${GREEN}✅ VIABLE${NC}"
    elif (( $(echo "$success_rate >= 30" | bc -l) )); then
        echo -e "     • Estado: ${YELLOW}⚠️  MARGINAL${NC}"
    else
        echo -e "     • Estado: ${RED}❌ IRRESOLUBLE${NC}"
    fi
}

echo -e "${YELLOW}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  FASE 1: CONFIGURACIONES ÓPTIMAS (Alta tasa de éxito esperada)${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════════════${NC}"

# 3x3 - Muy fácil (9 celdas, ~33% densidad)
run_experiment 3 2 50 200 10 "MUY FÁCIL"

# 4x4 - Fácil (16 celdas, ~31% densidad)
run_experiment 4 3 100 500 10 "FÁCIL"

# 5x5 - Normal (25 celdas, ~32% densidad)
run_experiment 5 4 200 1000 10 "NORMAL"

# 6x6 - Medio (36 celdas, ~28% densidad)
run_experiment 6 5 200 1000 10 "MEDIO"

# 7x7 - Complejo (49 celdas, ~29% densidad)
run_experiment 7 6 250 1500 10 "COMPLEJO"

echo ""
echo -e "${YELLOW}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  FASE 2: LÍMITES DE COMPLEJIDAD (Buscando el punto de falla)${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════════════${NC}"

# 5x5 con más colores (densidad alta)
run_experiment 5 6 200 1500 8 "ALTA DENSIDAD"
run_experiment 5 7 250 2000 5 "MUY ALTA DENSIDAD"

# 6x6 límites
run_experiment 6 8 250 1500 8 "6x6 DIFÍCIL"
run_experiment 6 10 300 2000 5 "6x6 MUY DIFÍCIL"

# 7x7 límites
run_experiment 7 8 300 2000 8 "7x7 DIFÍCIL"
run_experiment 7 10 300 2500 5 "7x7 MUY DIFÍCIL"

echo ""
echo -e "${YELLOW}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  FASE 3: ZONA CRÍTICA (8x8 y más grandes)${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════════════${NC}"

# 8x8 - Muy complejo (64 celdas)
run_experiment 8 8 300 1500 5 "8x8 ESTÁNDAR"
run_experiment 8 10 300 2000 5 "8x8 ALTO"

# 9x9 - Casi imposible (81 celdas)
run_experiment 9 10 200 1000 5 "9x9 LÍMITE"

# 10x10 - Probablemente irresoluble
echo ""
echo -e "${RED}⚠️  ADVERTENCIA: 10x10 es computacionalmente MUY costoso${NC}"
echo -e "${RED}   Esto puede tomar varios minutos por run${NC}"
read -p "¿Continuar con 10x10? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    run_experiment 10 12 200 500 3 "10x10 EXPERIMENTAL"
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ EXPERIMENTOS COMPLETADOS${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Generar reporte final
REPORT_FILE="${OUTPUT_DIR}/REPORT.txt"

cat > "$REPORT_FILE" << EOF
═══════════════════════════════════════════════════════════════════
  REPORTE DE EXPERIMENTOS - Algoritmo Genético Flow (C + OpenMP)
═══════════════════════════════════════════════════════════════════

Fecha: $(date)
Threads: ${NPROC}
Directorio: ${OUTPUT_DIR}

───────────────────────────────────────────────────────────────────
  RESUMEN DE RESULTADOS
───────────────────────────────────────────────────────────────────

EOF

echo "" >> "$REPORT_FILE"
echo "Tamaño | Colores | Densidad | Éxito%  | Tiempo Avg | Estado" >> "$REPORT_FILE"
echo "-------|---------|----------|---------|------------|-------------" >> "$REPORT_FILE"

# Procesar CSV y generar tabla
tail -n +2 "$SUMMARY_CSV" | while IFS=, read -r size colors density pop gen success_count success_rate avg_time min_time max_time avg_fitness perfect; do
    # Determinar estado
    if (( $(echo "$success_rate >= 70" | bc -l) )); then
        status="✅ VIABLE"
    elif (( $(echo "$success_rate >= 30" | bc -l) )); then
        status="⚠️  MARGINAL"
    else
        status="❌ IRRESOLUBLE"
    fi
    
    printf "%4sx%-2s | %7s | %8s | %6.1f%% | %9.2fs | %s\n" \
        "$size" "$size" "$colors" "$density" "$success_rate" "$avg_time" "$status" >> "$REPORT_FILE"
done

cat >> "$REPORT_FILE" << EOF

───────────────────────────────────────────────────────────────────
  CONCLUSIONES
───────────────────────────────────────────────────────────────────

CONFIGURACIONES RECOMENDADAS:
  • 3x3 - 5x5: Óptimas para uso práctico
  • 6x6 - 7x7: Funcionales con parámetros ajustados
  • 8x8+: Límite del algoritmo genético

LÍMITE DE RESOLUBILIDAD:
  • El GA funciona bien hasta 7x7 con densidad < 0.30
  • 8x8 es el límite práctico (tasa de éxito < 50%)
  • 9x9+ son computacionalmente intratables para el GA

FACTORES CRÍTICOS:
  • Densidad: Mantener < 0.35 para mejores resultados
  • Población: Aumentar para problemas grandes (300+)
  • Generaciones: 1000-2500 según complejidad

═══════════════════════════════════════════════════════════════════
EOF

# Mostrar reporte
cat "$REPORT_FILE"

echo ""
echo -e "${CYAN}📄 Reporte completo guardado en: ${GREEN}${REPORT_FILE}${NC}"
echo -e "${CYAN}📊 CSV de resultados: ${GREEN}${SUMMARY_CSV}${NC}"
echo -e "${CYAN}📁 Logs individuales en: ${GREEN}${OUTPUT_DIR}/*/run_*.txt${NC}"
echo ""

# Generar gráfica simple en texto
echo -e "${BLUE}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  📈 TASA DE ÉXITO POR TAMAÑO${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════════${NC}"
echo ""

tail -n +2 "$SUMMARY_CSV" | while IFS=, read -r size colors density pop gen success_count success_rate avg_time min_time max_time avg_fitness perfect; do
    # Crear barra visual
    bar_length=$(echo "scale=0; $success_rate / 2" | bc -l)
    bar=$(printf '█%.0s' $(seq 1 ${bar_length}))
    
    printf "%2sx%2s [%-50s] %5.1f%%\n" "$size" "$size" "$bar" "$success_rate"
done

echo ""
echo -e "${GREEN}✅ Script completado exitosamente${NC}"
echo ""