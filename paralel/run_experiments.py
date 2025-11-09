#!/usr/bin/env python3
"""
Script de experimentos SEGURO para Flow GA
Parámetros RAZONABLES que realmente funcionan
Compatible con Windows, Linux y macOS
"""

import subprocess
import os
import re
import csv
import time
from datetime import datetime
from pathlib import Path

# Colores ANSI
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def print_colored(text, color):
    print(f"{color}{text}{Colors.NC}")

def detect_executable():
    """Detecta si el ejecutable es .exe o sin extensión"""
    executables = [
        "./flow_ga_parallel.exe",
        "./flow_ga_parallel",
        "./flow_ga.exe",
        "./flow_ga"
    ]
    
    for exe in executables:
        if os.path.exists(exe):
            return exe
    return None

def run_experiment(size, colors, pop, gen, runs, label, exe_path, output_dir, nproc):
    """Ejecuta un experimento completo"""
    
    density = round(colors / (size * size), 3)
    
    print()
    print_colored("=" * 70, Colors.MAGENTA)
    print_colored(f"  {size}x{size} | {colors} colores | Pop: {pop} | Gen: {gen}", Colors.MAGENTA)
    print_colored(f"  Densidad: {density} | {label}", Colors.MAGENTA)
    print_colored("=" * 70, Colors.MAGENTA)
    
    exp_dir = output_dir / f"{size}x{size}_{colors}colors"
    exp_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    total_time = 0.0
    min_time = 999999.0
    max_time = 0.0
    total_fitness = 0.0
    total_gens = 0
    perfect_found = "NO"
    valid_runs = 0
    
    for i in range(1, runs + 1):
        print_colored(f"  Run {i}/{runs}...", Colors.CYAN)
        
        seed = int(time.time() * 1000) % 100000 + i * 13
        output_file = exp_dir / f"run_{i}.txt"
        
        # Construir comando
        cmd = [
            exe_path,
            "--size", str(size),
            "--colors", str(colors),
            "--pop", str(pop),
            "--gen", str(gen),
            "--threads", str(nproc),
            "--seed", str(seed)
        ]
        
        try:
            # Timeout adaptativo según tamaño
            if size <= 5:
                timeout_sec = 120  # 2 minutos
            elif size <= 7:
                timeout_sec = 300  # 5 minutos
            else:
                timeout_sec = 600  # 10 minutos
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                encoding='utf-8',
                errors='replace'
            )
            
            # Guardar output
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
                if result.stderr:
                    f.write("\n=== STDERR ===\n")
                    f.write(result.stderr)
            
            # Analizar códigos de error específicos
            if result.returncode == 3221225477:  # Access Violation Windows
                print_colored(f"    ❌ SEGFAULT (Access Violation)", Colors.RED)
                print_colored(f"       💡 Reducir población o aumentar stack", Colors.YELLOW)
                continue
            elif result.returncode == 139 or result.returncode == -11:  # SIGSEGV Linux
                print_colored(f"    ❌ SEGFAULT", Colors.RED)
                continue
            elif result.returncode != 0:
                print_colored(f"    ❌ Error (código: {result.returncode})", Colors.RED)
                continue
            
            # Extraer métricas
            content = result.stdout
            
            time_match = re.search(r'Elapsed time:\s+([\d.]+)', content)
            perfect_match = re.search(r'Perfect solution:\s+(\w+)', content)
            fitness_match = re.search(r'Best fitness:\s+([-]?[\d.]+)', content)
            gens_match = re.search(r'Generations executed:\s+(\d+)', content)
            
            if not all([time_match, fitness_match, gens_match]):
                print_colored(f"    ⚠️  Error extrayendo métricas", Colors.RED)
                continue
            
            run_time = float(time_match.group(1))
            perfect = perfect_match.group(1) if perfect_match else "NO"
            fitness = float(fitness_match.group(1))
            gens = int(gens_match.group(1))
            
            valid_runs += 1
            
            # Acumular estadísticas
            total_time += run_time
            total_fitness += fitness
            total_gens += gens
            
            min_time = min(min_time, run_time)
            max_time = max(max_time, run_time)
            
            if perfect == "YES":
                success_count += 1
                perfect_found = "YES"
                print_colored(f"    ✅ ÉXITO en {run_time:.2f}s ({gens} gen, fit: {fitness:.0f})", Colors.GREEN)
            else:
                print_colored(f"    ⚠️  No resuelto en {run_time:.2f}s ({gens} gen, fit: {fitness:.0f})", Colors.YELLOW)
        
        except subprocess.TimeoutExpired:
            print_colored(f"    ⏱️  TIMEOUT (>{timeout_sec}s)", Colors.RED)
            continue
        except Exception as e:
            print_colored(f"    ❌ Excepción: {e}", Colors.RED)
            continue
    
    # Calcular promedios
    if valid_runs == 0:
        print_colored("  ❌ No se completó ningún run válido", Colors.RED)
        return [size, colors, density, pop, gen, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, "NO"]
    
    avg_time = round(total_time / valid_runs, 2)
    avg_fitness = round(total_fitness / valid_runs, 0)
    avg_gens = round(total_gens / valid_runs, 0)
    success_rate = round((success_count * 100.0) / valid_runs, 1)
    
    # Mostrar resumen
    print()
    print_colored("  📈 Resumen:", Colors.BLUE)
    print(f"     • Runs válidos: {valid_runs}/{runs}")
    
    color = Colors.GREEN if success_rate >= 70 else Colors.YELLOW if success_rate >= 30 else Colors.RED
    print_colored(f"     • Éxitos: {success_count}/{valid_runs} ({success_rate}%)", color)
    
    print(f"     • Tiempo: {avg_time}s (min: {min_time:.2f}s, max: {max_time:.2f}s)")
    print(f"     • Fitness promedio: {avg_fitness}")
    print(f"     • Generaciones promedio: {int(avg_gens)}")
    
    status = "✅ EXCELENTE" if success_rate >= 90 else "✅ VIABLE" if success_rate >= 70 else "⚠️  MARGINAL" if success_rate >= 30 else "❌ DIFÍCIL"
    print_colored(f"     • Estado: {status}", color)
    
    return [size, colors, density, pop, gen, valid_runs, success_count, success_rate, 
            avg_time, min_time, max_time, avg_fitness, int(avg_gens), perfect_found]

def main():
    # Detectar ejecutable
    exe_path = detect_executable()
    if not exe_path:
        print_colored("❌ Error: No se encontró el ejecutable", Colors.RED)
        print_colored("\n💡 Compilar primero:", Colors.YELLOW)
        print()
        print("  Windows (MinGW con stack aumentado):")
        print("    gcc -O3 -fopenmp -march=native -Wl,--stack,16777216 -o flow_ga_parallel.exe flow_ga_parallel.c -lm")
        print()
        print("  Linux:")
        print("    gcc -O3 -fopenmp -march=native -o flow_ga_parallel flow_ga_parallel.c -lm")
        print()
        print("  macOS:")
        print("    gcc-13 -O3 -Xpreprocessor -fopenmp -march=native -o flow_ga_parallel flow_ga_parallel.c -lomp -lm")
        return 1
    
    # Detectar número de cores
    try:
        nproc = os.cpu_count() or 4
    except:
        nproc = 4
    
    # Crear directorio de resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"experiments_safe_{timestamp}")
    output_dir.mkdir(exist_ok=True)
    
    print_colored("=" * 70, Colors.CYAN)
    print_colored("  🧬 EXPERIMENTOS CON PARÁMETROS RAZONABLES", Colors.CYAN)
    print_colored("=" * 70, Colors.CYAN)
    print()
    print_colored(f"📁 Resultados en: {output_dir}/", Colors.GREEN)
    print_colored(f"🖥️  Threads: {nproc}", Colors.GREEN)
    print_colored(f"⚙️  Ejecutable: {exe_path}", Colors.GREEN)
    print()
    print_colored("✅ Parámetros optimizados para estabilidad y velocidad", Colors.GREEN)
    print()
    
    # CSV de resultados
    csv_file = output_dir / "summary_results.csv"
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "board_size", "num_colors", "density", "pop_size", "generations",
            "runs_total", "success_count", "success_rate", "avg_time", "min_time",
            "max_time", "avg_fitness", "avg_gens", "perfect_found"
        ])
    
    # ========================================================================
    # PARÁMETROS RAZONABLES Y PROBADOS
    # ========================================================================
    
    print_colored("=" * 70, Colors.YELLOW)
    print_colored("  FASE 1: CONFIGURACIONES BÁSICAS (Alta Tasa de Éxito)", Colors.YELLOW)
    print_colored("=" * 70, Colors.YELLOW)
    
    phase1_experiments = [
        # (size, colors, pop, gen, runs, label)
        (3, 2, 100, 500, 100, "MUY FÁCIL - Sanity Check"),
        (4, 3, 150, 1000, 100, "FÁCIL - 4x4 Estándar"),
        (5, 4, 200, 1500, 100, "NORMAL - 5x5 Estándar"),
        (5, 5, 250, 2000, 100, "MEDIO - 5x5 Alta Densidad"),
        (6, 5, 300, 2500, 100, "MEDIO-ALTO - 6x6 Estándar"),
    ]
    
    results = []
    
    for size, colors, pop, gen, runs, label in phase1_experiments:
        result = run_experiment(size, colors, pop, gen, runs, label, exe_path, output_dir, nproc)
        results.append(result)
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(result)
    
    print()
    print_colored("=" * 70, Colors.YELLOW)
    print_colored("  FASE 2: CONFIGURACIONES DESAFIANTES", Colors.YELLOW)
    print_colored("=" * 70, Colors.YELLOW)
    
    phase2_experiments = [
        (6, 6, 350, 3000, 100, "DESAFIANTE - 6x6 Alta Densidad"),
        (7, 6, 400, 3500, 100, "COMPLEJO - 7x7 Estándar"),
        (7, 7, 500, 4500, 100, "MUY COMPLEJO - 7x7 Alta Densidad"),
        (8, 8, 600, 5000, 100, "EXTREMO - 8x8 Límite Práctico"),
    ]
    
    for size, colors, pop, gen, runs, label in phase2_experiments:
        result = run_experiment(size, colors, pop, gen, runs, label, exe_path, output_dir, nproc)
        results.append(result)
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(result)
    
    print()
    print_colored("=" * 70, Colors.YELLOW)
    print_colored("  FASE 3: LÍMITE EXPERIMENTAL (Opcional)", Colors.YELLOW)
    print_colored("=" * 70, Colors.YELLOW)
    
    print_colored("⚠️  Estas configuraciones pueden fallar o tomar mucho tiempo", Colors.YELLOW)
    response = input("¿Ejecutar Fase 3? (s/N): ").strip().lower()
    
    if response == 's':
        phase3_experiments = [
            (6, 8, 450, 4000, 100, "EXTREMO - 6x6 Muy Alta Densidad"),
            (7, 8, 600, 5000, 100, "EXTREMO - 7x7 Muy Alta Densidad"),
            (8, 10, 800, 6000, 100, "LÍMITE - 8x8 Máxima Densidad"),
        ]
        
        for size, colors, pop, gen, runs, label in phase3_experiments:
            result = run_experiment(size, colors, pop, gen, runs, label, exe_path, output_dir, nproc)
            results.append(result)
            
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(result)
    else:
        print_colored("  Saltando Fase 3", Colors.CYAN)
    
    # Generar reporte final
    print()
    print_colored("=" * 70, Colors.GREEN)
    print_colored("  ✅ EXPERIMENTOS COMPLETADOS", Colors.GREEN)
    print_colored("=" * 70, Colors.GREEN)
    print()
    
    # Calcular estadísticas globales
    total_configs = len(results)
    excellent = sum(1 for r in results if r[7] >= 90)
    viable = sum(1 for r in results if r[7] >= 70)
    total_runs = sum(r[5] for r in results)
    total_success = sum(r[6] for r in results)
    global_success_rate = round((total_success * 100) / total_runs, 1) if total_runs > 0 else 0
    
    print_colored(f"📊 Resultados guardados en: {csv_file}", Colors.CYAN)
    print()
    print_colored("RESUMEN GLOBAL:", Colors.BLUE)
    print(f"  • Total configuraciones: {total_configs}")
    print(f"  • Excelentes (≥90%): {excellent}")
    print(f"  • Viables (≥70%): {viable}")
    print(f"  • Total runs ejecutados: {total_runs}")
    print(f"  • Total éxitos: {total_success}")
    
    color = Colors.GREEN if global_success_rate >= 70 else Colors.YELLOW if global_success_rate >= 50 else Colors.RED
    print_colored(f"  • Tasa global de éxito: {global_success_rate}%", color)
    
    # Mejores configuraciones
    print()
    print_colored("🏆 TOP 5 CONFIGURACIONES:", Colors.GREEN)
    sorted_results = sorted(results, key=lambda x: x[7], reverse=True)[:5]
    
    for i, r in enumerate(sorted_results, 1):
        size, colors, density, pop, gen, _, _, success_rate, avg_time, _, _, _, _, _ = r
        print(f"  {i}. {size}x{size} | {colors} colores | {success_rate}% éxito | {avg_time}s | Pop:{pop} Gen:{gen}")
    
    print()
    print_colored("=" * 70, Colors.GREEN)
    print_colored("✅ Script completado exitosamente", Colors.GREEN)
    print_colored("=" * 70, Colors.GREEN)
    
    return 0

if __name__ == "__main__":
    exit(main())    