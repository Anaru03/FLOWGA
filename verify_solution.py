# Script para verificar detalladamente si una solución es realmente válida
from typing import Dict, List, Tuple

from genetic_algorithm import is_perfect
from utils import bfs_connected


def verify_solution_detailed(grid: List[List[str]], 
                             terminals: Dict[str, Tuple[Tuple[int, int], Tuple[int, int]]]) -> bool:
    """Verificación detallada de una solución con reporte completo."""
    N = len(grid)
    print(f"\n{'='*60}")
    print(f"🔍 VERIFICACIÓN DETALLADA DE SOLUCIÓN {N}×{N}")
    print(f"{'='*60}")
    
    # 1. Verificar que todos los terminales están correctos
    print(f"\n1️⃣ Verificando terminales...")
    all_terminals_ok = True
    for col, (a, b) in terminals.items():
        if grid[a[0]][a[1]] != col:
            print(f"   ❌ Terminal {col} en {a}: esperado '{col}', encontrado '{grid[a[0]][a[1]]}'")
            all_terminals_ok = False
        if grid[b[0]][b[1]] != col:
            print(f"   ❌ Terminal {col} en {b}: esperado '{col}', encontrado '{grid[b[0]][b[1]]}'")
            all_terminals_ok = False
    
    if all_terminals_ok:
        print(f"   ✅ Todos los terminales están correctos")
    else:
        return False
    
    # 2. Verificar conectividad de cada color
    print(f"\n2️⃣ Verificando conectividad de cada color...")
    all_connected = True
    for col, (a, b) in terminals.items():
        connected, size = bfs_connected(grid, col, a, b)
        if not connected:
            print(f"   ❌ Color {col}: Terminales {a} y {b} NO están conectados")
            all_connected = False
        else:
            print(f"   ✅ Color {col}: Conectado (componente de tamaño {size})")
    
    if not all_connected:
        return False
    
    # 3. Verificar que no hay celdas vacías
    print(f"\n3️⃣ Verificando que no hay celdas vacías...")
    empty_cells = []
    for r in range(N):
        for c in range(N):
            if grid[r][c] == "" or grid[r][c] == ".":
                empty_cells.append((r, c))
    
    if empty_cells:
        print(f"   ❌ Se encontraron {len(empty_cells)} celdas vacías:")
        for pos in empty_cells[:10]:  # Mostrar solo las primeras 10
            print(f"      • {pos}")
        if len(empty_cells) > 10:
            print(f"      ... y {len(empty_cells) - 10} más")
        return False
    else:
        print(f"   ✅ No hay celdas vacías")
    
    # 4. Verificar que cada celda pertenece a exactamente un color
    print(f"\n4️⃣ Verificando asignación única de colores...")
    color_counts = {}
    for r in range(N):
        for c in range(N):
            col = grid[r][c]
            if col not in color_counts:
                color_counts[col] = 0
            color_counts[col] += 1
    
    print(f"   📊 Distribución de colores:")
    for col in sorted(color_counts.keys()):
        print(f"      • {col}: {color_counts[col]} celdas")
    
    # 5. Verificar que cada componente de color es conexo
    print(f"\n5️⃣ Verificando que cada color forma UN solo componente conexo...")
    all_single_component = True
    for col in terminals.keys():
        # Contar cuántos componentes conexos hay de este color
        visited = set()
        components = 0
        
        for r in range(N):
            for c in range(N):
                if grid[r][c] == col and (r, c) not in visited:
                    # Nuevo componente encontrado
                    components += 1
                    # BFS para marcar todo el componente
                    from collections import deque
                    q = deque([(r, c)])
                    visited.add((r, c))
                    while q:
                        rr, cc = q.popleft()
                        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                            nr, nc = rr + dr, cc + dc
                            if 0 <= nr < N and 0 <= nc < N and grid[nr][nc] == col and (nr, nc) not in visited:
                                visited.add((nr, nc))
                                q.append((nr, nc))
        
        if components > 1:
            print(f"   ❌ Color {col}: Tiene {components} componentes conexos (debería tener 1)")
            all_single_component = False
        else:
            print(f"   ✅ Color {col}: Un solo componente conexo")
    
    if not all_single_component:
        return False
    
    # 6. Usar is_perfect como verificación final
    print(f"\n6️⃣ Verificación final con is_perfect()...")
    perfect = is_perfect(grid, terminals)
    if perfect:
        print(f"   ✅ is_perfect() retorna True")
    else:
        print(f"   ❌ is_perfect() retorna False")
    
    print(f"\n{'='*60}")
    if all_terminals_ok and all_connected and not empty_cells and all_single_component and perfect:
        print(f"✅ SOLUCIÓN VÁLIDA: Todos los tests pasaron")
        print(f"{'='*60}\n")
        return True
    else:
        print(f"❌ SOLUCIÓN INVÁLIDA: Algunos tests fallaron")
        print(f"{'='*60}\n")
        return False

if __name__ == "__main__":
    print("Este es un módulo de verificación.")
    print("Úsalo importándolo en otro script.")
