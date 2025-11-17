/*
 * flow_ga_improved.c
 * 
 * Algoritmo Genético MEJORADO para Flow Puzzle con:
 * - Fitness más inteligente con análisis de distancias
 * - Mutación path-aware
 * - Operador de reparación local
 * - Búsqueda A* para inicialización
 * 
 * Compilar: gcc -O3 -fopenmp -march=native -o flow_ga_improved flow_ga_improved.c -lm
 * Ejecutar: ./flow_ga_improved --size 7 --colors 6 --pop 300 --gen 2000 --threads 8
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <omp.h>
#include <stdbool.h>
#include <getopt.h>
#include <stdint.h>

// ==================== RANDOM THREAD-SAFE ====================

typedef struct {
    uint64_t state;
    uint64_t inc;
} pcg32_random_t;

static inline uint32_t pcg32_random(pcg32_random_t* rng) {
    uint64_t oldstate = rng->state;
    rng->state = oldstate * 6364136223846793005ULL + rng->inc;
    uint32_t xorshifted = ((oldstate >> 18u) ^ oldstate) >> 27u;
    uint32_t rot = oldstate >> 59u;
    return (xorshifted >> rot) | (xorshifted << ((-rot) & 31));
}

static inline void pcg32_init(pcg32_random_t* rng, uint64_t seed) {
    rng->state = 0;
    rng->inc = (seed << 1u) | 1u;
    pcg32_random(rng);
    rng->state += seed;
    pcg32_random(rng);
}

static inline int rand_range(pcg32_random_t* rng, int max) {
    return pcg32_random(rng) % max;
}

static inline double rand_double(pcg32_random_t* rng) {
    return (double)pcg32_random(rng) / UINT32_MAX;
}

// ==================== ESTRUCTURAS ====================

typedef struct {
    int r, c;
} Coord;

typedef struct {
    char color;
    Coord a, b;
} ColorPair;

typedef struct {
    int N;
    int num_colors;
    ColorPair *colors;
    char **grid;
} Individual;

typedef struct {
    int pop_size;
    int generations;
    double mut_rate;
    int elite_size;
    int tournament_k;
    int num_threads;
} GAParams;

typedef struct {
    double best_fitness;
    double avg_fitness;
    int generation;
    bool perfect_found;
    double elapsed_time;
} GAMetrics;

// ==================== GLOBALS ====================
static const char COLOR_CHARS[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
static pcg32_random_t *THREAD_RNGS;

// ==================== UTILIDADES ====================

char** alloc_grid(int N) {
    char **grid = malloc(N * sizeof(char*));
    for (int i = 0; i < N; i++) {
        grid[i] = malloc(N * sizeof(char));
        memset(grid[i], '.', N);
    }
    return grid;
}

void free_grid(char **grid, int N) {
    for (int i = 0; i < N; i++) free(grid[i]);
    free(grid);
}

void copy_grid(char **dest, char **src, int N) {
    for (int i = 0; i < N; i++)
        memcpy(dest[i], src[i], N);
}

// ==================== PRIORITY QUEUE (A*) ====================

typedef struct {
    Coord pos;
    int f_score;
} PQNode;

typedef struct {
    PQNode *data;
    int size;
    int capacity;
} PriorityQueue;

PriorityQueue* pq_create(int capacity) {
    PriorityQueue *pq = malloc(sizeof(PriorityQueue));
    pq->data = malloc(capacity * sizeof(PQNode));
    pq->size = 0;
    pq->capacity = capacity;
    return pq;
}

void pq_free(PriorityQueue *pq) {
    free(pq->data);
    free(pq);
}

void pq_push(PriorityQueue *pq, Coord pos, int f_score) {
    if (pq->size >= pq->capacity) return;
    
    int i = pq->size++;
    while (i > 0) {
        int parent = (i - 1) / 2;
        if (pq->data[parent].f_score <= f_score) break;
        pq->data[i] = pq->data[parent];
        i = parent;
    }
    pq->data[i] = (PQNode){pos, f_score};
}

Coord pq_pop(PriorityQueue *pq) {
    Coord result = pq->data[0].pos;
    PQNode last = pq->data[--pq->size];
    
    int i = 0;
    while (true) {
        int left = 2 * i + 1;
        int right = 2 * i + 2;
        int smallest = i;
        
        if (left < pq->size && pq->data[left].f_score < pq->data[smallest].f_score)
            smallest = left;
        if (right < pq->size && pq->data[right].f_score < pq->data[smallest].f_score)
            smallest = right;
        
        if (smallest == i) break;
        
        pq->data[i] = pq->data[smallest];
        i = smallest;
    }
    
    if (pq->size > 0) pq->data[i] = last;
    return result;
}

// ==================== A* PATH FINDING ====================

bool find_path_astar(char **grid, int N, Coord start, Coord goal, char color, bool **used_by_others) {
    // Validación de entrada
    if (!grid || N <= 0) return false;
    if (start.r < 0 || start.r >= N || start.c < 0 || start.c >= N) return false;
    if (goal.r < 0 || goal.r >= N || goal.c < 0 || goal.c >= N) return false;
    
    static const int dr[] = {-1, 1, 0, 0};
    static const int dc[] = {0, 0, -1, 1};
    
    int **g_score = malloc(N * sizeof(int*));
    bool **visited = malloc(N * sizeof(bool*));
    Coord **came_from = malloc(N * sizeof(Coord*));
    
    if (!g_score || !visited || !came_from) {
        if (g_score) free(g_score);
        if (visited) free(visited);
        if (came_from) free(came_from);
        return false;
    }
    
    for (int i = 0; i < N; i++) {
        g_score[i] = malloc(N * sizeof(int));
        visited[i] = calloc(N, sizeof(bool));
        came_from[i] = malloc(N * sizeof(Coord));
        
        if (!g_score[i] || !visited[i] || !came_from[i]) {
            for (int j = 0; j <= i; j++) {
                if (g_score[j]) free(g_score[j]);
                if (visited[j]) free(visited[j]);
                if (came_from[j]) free(came_from[j]);
            }
            free(g_score);
            free(visited);
            free(came_from);
            return false;
        }
        
        for (int j = 0; j < N; j++) {
            g_score[i][j] = N * N * 10;
        }
    }
    
    PriorityQueue *pq = pq_create(N * N);
    
    g_score[start.r][start.c] = 0;
    int h_start = abs(start.r - goal.r) + abs(start.c - goal.c);
    pq_push(pq, start, h_start);
    
    bool found = false;
    
    while (pq->size > 0) {
        Coord curr = pq_pop(pq);
        
        if (visited[curr.r][curr.c]) continue;
        visited[curr.r][curr.c] = true;
        
        if (curr.r == goal.r && curr.c == goal.c) {
            found = true;
            break;
        }
        
        for (int i = 0; i < 4; i++) {
            int nr = curr.r + dr[i];
            int nc = curr.c + dc[i];
            
            if (nr < 0 || nr >= N || nc < 0 || nc >= N) continue;
            if (visited[nr][nc]) continue;
            
            // No puede usar celdas de otros colores
            if (grid[nr][nc] != '.' && grid[nr][nc] != color) continue;
            if (used_by_others && used_by_others[nr][nc]) continue;
            
            int tentative_g = g_score[curr.r][curr.c] + 1;
            
            if (tentative_g < g_score[nr][nc]) {
                came_from[nr][nc] = curr;
                g_score[nr][nc] = tentative_g;
                int h = abs(nr - goal.r) + abs(nc - goal.c);
                pq_push(pq, (Coord){nr, nc}, tentative_g + h);
            }
        }
    }
    
    // Trazar el camino
    if (found) {
        Coord curr = goal;
        while (curr.r != start.r || curr.c != start.c) {
            grid[curr.r][curr.c] = color;
            curr = came_from[curr.r][curr.c];
        }
        grid[start.r][start.c] = color;
    }
    
    for (int i = 0; i < N; i++) {
        free(g_score[i]);
        free(visited[i]);
        free(came_from[i]);
    }
    free(g_score);
    free(visited);
    free(came_from);
    pq_free(pq);
    
    return found;
}

// ==================== BFS MEJORADO ====================

typedef struct {
    Coord *data;
    int front, rear, size;
} Queue;

Queue* queue_create(int capacity) {
    Queue *q = malloc(sizeof(Queue));
    q->data = malloc(capacity * sizeof(Coord));
    q->front = q->rear = 0;
    q->size = capacity;
    return q;
}

void queue_free(Queue *q) {
    free(q->data);
    free(q);
}

static inline void queue_push(Queue *q, Coord c) {
    q->data[q->rear++] = c;
}

static inline Coord queue_pop(Queue *q) {
    return q->data[q->front++];
}

static inline bool queue_empty(Queue *q) {
    return q->front == q->rear;
}

bool bfs_connected(char **grid, int N, char color, Coord start, Coord end, int *component_size) {
    // Validación de entrada
    if (!grid || N <= 0 || !component_size) return false;
    if (start.r < 0 || start.r >= N || start.c < 0 || start.c >= N) return false;
    if (end.r < 0 || end.r >= N || end.c < 0 || end.c >= N) return false;
    
    static const int dr[] = {-1, 1, 0, 0};
    static const int dc[] = {0, 0, -1, 1};
    
    bool **visited = malloc(N * sizeof(bool*));
    if (!visited) return false;
    
    for (int i = 0; i < N; i++) {
        visited[i] = calloc(N, sizeof(bool));
        if (!visited[i]) {
            for (int j = 0; j < i; j++) free(visited[j]);
            free(visited);
            return false;
        }
    }
    
    Queue *q = queue_create(N * N);
    queue_push(q, start);
    visited[start.r][start.c] = true;
    
    int size = 0;
    bool found = false;
    
    while (!queue_empty(q)) {
        Coord curr = queue_pop(q);
        size++;
        
        if (curr.r == end.r && curr.c == end.c) {
            found = true;
        }
        
        for (int i = 0; i < 4; i++) {
            int nr = curr.r + dr[i];
            int nc = curr.c + dc[i];
            
            if (nr >= 0 && nr < N && nc >= 0 && nc < N &&
                !visited[nr][nc] && grid[nr][nc] == color) {
                visited[nr][nc] = true;
                queue_push(q, (Coord){nr, nc});
            }
        }
    }
    
    *component_size = size;
    
    for (int i = 0; i < N; i++) free(visited[i]);
    free(visited);
    queue_free(q);
    
    return found;
}

int count_components(char **grid, int N, char color) {
    if (!grid || N <= 0) return 0;
    
    bool **visited = malloc(N * sizeof(bool*));
    if (!visited) return 0;
    
    for (int i = 0; i < N; i++) {
        visited[i] = calloc(N, sizeof(bool));
        if (!visited[i]) {
            for (int j = 0; j < i; j++) free(visited[j]);
            free(visited);
            return 0;
        }
    }
    
    int components = 0;
    Queue *q = queue_create(N * N);
    
    for (int r = 0; r < N; r++) {
        for (int c = 0; c < N; c++) {
            if (grid[r][c] == color && !visited[r][c]) {
                components++;
                
                q->front = q->rear = 0;
                queue_push(q, (Coord){r, c});
                visited[r][c] = true;
                
                while (!queue_empty(q)) {
                    Coord curr = queue_pop(q);
                    
                    static const int dr[] = {-1, 1, 0, 0};
                    static const int dc[] = {0, 0, -1, 1};
                    
                    for (int i = 0; i < 4; i++) {
                        int nr = curr.r + dr[i];
                        int nc = curr.c + dc[i];
                        
                        if (nr >= 0 && nr < N && nc >= 0 && nc < N &&
                            !visited[nr][nc] && grid[nr][nc] == color) {
                            visited[nr][nc] = true;
                            queue_push(q, (Coord){nr, nc});
                        }
                    }
                }
            }
        }
    }
    
    for (int i = 0; i < N; i++) free(visited[i]);
    free(visited);
    queue_free(q);
    
    return components;
}

// ==================== FITNESS MEJORADO ====================

double calculate_fitness(Individual *ind) {
    if (!ind || !ind->grid || !ind->colors) return -999999.0;
    
    double score = 0.0;
    int N = ind->N;
    char **grid = ind->grid;
    
    int total_cells = N * N;
    int covered_cells = 0;
    
    // Contar celdas vacías
    for (int r = 0; r < N; r++) {
        for (int c = 0; c < N; c++) {
            if (grid[r][c] != '.') covered_cells++;
        }
    }
    
    // Bonus por cobertura total
    if (covered_cells == total_cells) {
        score += 5000.0;
    } else {
        score -= 300.0 * (total_cells - covered_cells);
    }
    
    int total_connected = 0;
    
    // Evaluar cada color
    for (int i = 0; i < ind->num_colors; i++) {
        ColorPair cp = ind->colors[i];
        char color = cp.color;
        
        // Validar coordenadas
        if (cp.a.r < 0 || cp.a.r >= N || cp.a.c < 0 || cp.a.c >= N) continue;
        if (cp.b.r < 0 || cp.b.r >= N || cp.b.c < 0 || cp.b.c >= N) continue;
        
        int num_comps = count_components(grid, N, color);
        
        // Penalización FUERTE por múltiples componentes
        if (num_comps > 1) {
            score -= 1000.0 * (num_comps - 1);
        }
        
        int comp_size = 0;
        bool connected = bfs_connected(grid, N, color, cp.a, cp.b, &comp_size);
        
        if (connected) {
            total_connected++;
            score += 4000.0;  // Bonus grande por conectar
            
            int manhattan = abs(cp.a.r - cp.b.r) + abs(cp.a.c - cp.b.c);
            int ideal_length = manhattan + 2;  // +2 por las terminales
            
            // Penalizar caminos con exceso
            int excess = comp_size - ideal_length;
            if (excess > 0) {
                score -= 8.0 * excess;
            } else if (excess == 0) {
                score += 200.0;  // Bonus por camino óptimo
            }
        } else {
            // Penalización progresiva por no conectar
            int manhattan = abs(cp.a.r - cp.b.r) + abs(cp.a.c - cp.b.c);
            score -= 1200.0 + 80.0 * manhattan;
        }
    }
    
    // Bonus extra por tener todos conectados
    if (total_connected == ind->num_colors) {
        score += 3000.0;
    }
    
    // Término de suavidad (caminos continuos)
    int smooth_count = 0;
    for (int r = 0; r < N; r++) {
        for (int c = 0; c < N; c++) {
            char curr = grid[r][c];
            if (curr == '.') continue;
            
            if (c + 1 < N && grid[r][c+1] == curr) smooth_count++;
            if (r + 1 < N && grid[r+1][c] == curr) smooth_count++;
        }
    }
    score += 0.5 * smooth_count;
    
    return score;
}

bool is_perfect(Individual *ind) {
    // Verificar que todas las celdas estén llenas
    for (int r = 0; r < ind->N; r++) {
        for (int c = 0; c < ind->N; c++) {
            if (ind->grid[r][c] == '.') return false;
        }
    }
    
    // Verificar conectividad y componentes únicos
    for (int i = 0; i < ind->num_colors; i++) {
        ColorPair cp = ind->colors[i];
        int size;
        if (!bfs_connected(ind->grid, ind->N, cp.color, cp.a, cp.b, &size)) {
            return false;
        }
        if (count_components(ind->grid, ind->N, cp.color) != 1) {
            return false;
        }
    }
    return true;
}

// ==================== INICIALIZACIÓN MEJORADA (A*) ====================

void init_astar_greedy(Individual *ind, pcg32_random_t *rng) {
    if (!ind || !ind->grid || !ind->colors) return;
    
    int N = ind->N;
    
    // Limpiar grid
    for (int r = 0; r < N; r++) {
        for (int c = 0; c < N; c++) {
            ind->grid[r][c] = '.';
        }
    }
    
    // Validar número de colores razonable
    if (ind->num_colors <= 0 || ind->num_colors > 26) return;
    
    // Crear orden aleatorio de colores
    int *order = malloc(ind->num_colors * sizeof(int));
    if (!order) return;
    
    for (int i = 0; i < ind->num_colors; i++) order[i] = i;
    
    // Shuffle
    for (int i = ind->num_colors - 1; i > 0; i--) {
        int j = rand_range(rng, i + 1);
        int temp = order[i];
        order[i] = order[j];
        order[j] = temp;
    }
    
    // Trazar caminos con A*
    for (int i = 0; i < ind->num_colors; i++) {
        int color_idx = order[i];
        
        // Validar índice
        if (color_idx < 0 || color_idx >= ind->num_colors) continue;
        
        ColorPair cp = ind->colors[color_idx];
        
        // Validar coordenadas
        if (cp.a.r < 0 || cp.a.r >= N || cp.a.c < 0 || cp.a.c >= N) continue;
        if (cp.b.r < 0 || cp.b.r >= N || cp.b.c < 0 || cp.b.c >= N) continue;
        
        // Marcar terminales
        ind->grid[cp.a.r][cp.a.c] = cp.color;
        ind->grid[cp.b.r][cp.b.c] = cp.color;
        
        // Intentar encontrar camino
        find_path_astar(ind->grid, N, cp.a, cp.b, cp.color, NULL);
    }
    
    // Llenar vacíos con Voronoi
    for (int r = 0; r < N; r++) {
        for (int c = 0; c < N; c++) {
            if (ind->grid[r][c] != '.') continue;
            
            int min_dist = N * N;
            char best_color = ind->colors[0].color;
            
            for (int i = 0; i < ind->num_colors; i++) {
                ColorPair cp = ind->colors[i];
                int d1 = abs(r - cp.a.r) + abs(c - cp.a.c);
                int d2 = abs(r - cp.b.r) + abs(c - cp.b.c);
                int dist = (d1 < d2) ? d1 : d2;
                
                if (dist < min_dist) {
                    min_dist = dist;
                    best_color = cp.color;
                }
            }
            
            ind->grid[r][c] = best_color;
        }
    }
    
    free(order);
}

// ==================== OPERADOR DE REPARACIÓN LOCAL ====================

void repair_local(Individual *ind, pcg32_random_t *rng) {
    if (!ind || !ind->grid || !ind->colors) return;
    
    int N = ind->N;
    
    // Por cada color desconectado, intentar reparar
    for (int i = 0; i < ind->num_colors; i++) {
        ColorPair cp = ind->colors[i];
        
        // Validar coordenadas
        if (cp.a.r < 0 || cp.a.r >= N || cp.a.c < 0 || cp.a.c >= N) continue;
        if (cp.b.r < 0 || cp.b.r >= N || cp.b.c < 0 || cp.b.c >= N) continue;
        
        int size = 0;
        
        if (!bfs_connected(ind->grid, N, cp.color, cp.a, cp.b, &size)) {
            // Intentar crear un puente
            // Buscar el punto más cercano a la otra terminal
            
            int best_r = -1, best_c = -1;
            int min_dist = N * N;
            
            for (int r = 0; r < N; r++) {
                for (int c = 0; c < N; c++) {
                    if (ind->grid[r][c] == cp.color) continue;
                    
                    int dist_to_a = abs(r - cp.a.r) + abs(c - cp.a.c);
                    int dist_to_b = abs(r - cp.b.r) + abs(c - cp.b.c);
                    int total_dist = dist_to_a + dist_to_b;
                    
                    if (total_dist < min_dist) {
                        min_dist = total_dist;
                        best_r = r;
                        best_c = c;
                    }
                }
            }
            
            if (best_r != -1) {
                ind->grid[best_r][best_c] = cp.color;
            }
        }
    }
}

// ==================== OPERADORES GENÉTICOS MEJORADOS ====================

int tournament_select(double *fitness, int pop_size, int k, pcg32_random_t *rng) {
    int best_idx = rand_range(rng, pop_size);
    double best_fit = fitness[best_idx];
    
    for (int i = 1; i < k; i++) {
        int idx = rand_range(rng, pop_size);
        if (fitness[idx] > best_fit) {
            best_fit = fitness[idx];
            best_idx = idx;
        }
    }
    
    return best_idx;
}

void crossover_uniform(Individual *child, Individual *p1, Individual *p2, pcg32_random_t *rng) {
    if (!child || !p1 || !p2 || !child->grid || !p1->grid || !p2->grid) return;
    
    int N = child->N;
    
    bool **fixed = malloc(N * sizeof(bool*));
    if (!fixed) return;
    
    for (int i = 0; i < N; i++) {
        fixed[i] = calloc(N, sizeof(bool));
        if (!fixed[i]) {
            for (int j = 0; j < i; j++) free(fixed[j]);
            free(fixed);
            return;
        }
    }
    
    for (int i = 0; i < child->num_colors; i++) {
        ColorPair cp = child->colors[i];
        fixed[cp.a.r][cp.a.c] = true;
        fixed[cp.b.r][cp.b.c] = true;
    }
    
    for (int r = 0; r < N; r++) {
        for (int c = 0; c < N; c++) {
            if (!fixed[r][c]) {
                child->grid[r][c] = (rand_double(rng) < 0.5) ? 
                                    p1->grid[r][c] : p2->grid[r][c];
            }
        }
    }
    
    for (int i = 0; i < N; i++) free(fixed[i]);
    free(fixed);
}

// MUTACIÓN MEJORADA: Path-aware
void mutate_path_aware(Individual *ind, double mut_rate, pcg32_random_t *rng) {
    if (!ind || !ind->grid || !ind->colors) return;
    
    int N = ind->N;
    
    bool **fixed = malloc(N * sizeof(bool*));
    if (!fixed) return;
    
    for (int i = 0; i < N; i++) {
        fixed[i] = calloc(N, sizeof(bool));
        if (!fixed[i]) {
            for (int j = 0; j < i; j++) free(fixed[j]);
            free(fixed);
            return;
        }
    }
    
    for (int i = 0; i < ind->num_colors; i++) {
        ColorPair cp = ind->colors[i];
        fixed[cp.a.r][cp.a.c] = true;
        fixed[cp.b.r][cp.b.c] = true;
    }
    
    static const int dr[] = {-1, 1, 0, 0};
    static const int dc[] = {0, 0, -1, 1};
    
    for (int r = 0; r < N; r++) {
        for (int c = 0; c < N; c++) {
            if (fixed[r][c]) continue;
            
            if (rand_double(rng) < mut_rate) {
                // Contar vecinos de cada color
                int color_count[26] = {0};
                int valid_neighbors = 0;
                
                for (int i = 0; i < 4; i++) {
                    int nr = r + dr[i];
                    int nc = c + dc[i];
                    if (nr >= 0 && nr < N && nc >= 0 && nc < N) {
                        char neighbor_color = ind->grid[nr][nc];
                        if (neighbor_color != '.') {
                            int idx = neighbor_color - 'A';
                            color_count[idx]++;
                            valid_neighbors++;
                        }
                    }
                }
                
                // Elegir el color más común (fomenta continuidad)
                if (valid_neighbors > 0) {
                    int max_count = 0;
                    char best_color = ind->grid[r][c];
                    
                    for (int i = 0; i < ind->num_colors; i++) {
                        int idx = ind->colors[i].color - 'A';
                        if (color_count[idx] > max_count) {
                            max_count = color_count[idx];
                            best_color = ind->colors[i].color;
                        }
                    }
                    
                    ind->grid[r][c] = best_color;
                }
            }
        }
    }
    
    for (int i = 0; i < N; i++) free(fixed[i]);
    free(fixed);
}

// ==================== GA PARALELO MEJORADO ====================

GAMetrics run_ga_parallel(Individual **population, GAParams params, bool verbose) {
    GAMetrics metrics = {0};
    int pop_size = params.pop_size;
    int N = population[0]->N;
    
    double start_time = omp_get_wtime();
    
    double *fitness = malloc(pop_size * sizeof(double));
    
    Individual **new_pop = malloc(pop_size * sizeof(Individual*));
    for (int i = 0; i < pop_size; i++) {
        new_pop[i] = malloc(sizeof(Individual));
        new_pop[i]->N = N;
        new_pop[i]->num_colors = population[i]->num_colors;
        new_pop[i]->colors = population[i]->colors;
        new_pop[i]->grid = alloc_grid(N);
    }
    
    double best_fitness = -1e18;
    int best_idx = 0;
    int gens_without_improvement = 0;
    int stagnation_limit = params.generations / 3;
    
    // Mutation rate adaptativa
    double current_mut_rate = params.mut_rate;
    
    omp_set_num_threads(params.num_threads);
    
    for (int gen = 0; gen < params.generations; gen++) {
        // Evaluación paralela CON MANEJO DE ERRORES
        #pragma omp parallel for schedule(dynamic, 8)
        for (int i = 0; i < pop_size; i++) {
            // Validar individuo antes de evaluar
            if (population[i] && population[i]->grid && population[i]->colors) {
                fitness[i] = calculate_fitness(population[i]);
            } else {
                fitness[i] = -999999.0;  // Penalización por individuo inválido
            }
        }
        
        // Encontrar mejor
        int gen_best_idx = 0;
        double gen_best_fit = fitness[0];
        for (int i = 1; i < pop_size; i++) {
            if (fitness[i] > gen_best_fit) {
                gen_best_fit = fitness[i];
                gen_best_idx = i;
            }
        }
        
        if (gen_best_fit > best_fitness) {
            best_fitness = gen_best_fit;
            best_idx = gen_best_idx;
            gens_without_improvement = 0;
            
            // Reducir mutation rate cuando mejora
            current_mut_rate = params.mut_rate * 0.9;
        } else {
            gens_without_improvement++;
            
            // Aumentar mutation rate si se estanca
            if (gens_without_improvement > 50) {
                current_mut_rate = fmin(0.15, params.mut_rate * 1.5);
            }
        }
        
        if (verbose && gen % 50 == 0) {
            double avg_fit = 0.0;
            for (int i = 0; i < pop_size; i++) avg_fit += fitness[i];
            avg_fit /= pop_size;
            
            printf("[Gen %4d] Best: %.2f | Avg: %.2f | MutRate: %.4f | Perfect: %s\n", 
                   gen, best_fitness, avg_fit, current_mut_rate,
                   is_perfect(population[best_idx]) ? "YES" : "NO");
        }
        
        if (is_perfect(population[best_idx])) {
            metrics.perfect_found = true;
            metrics.generation = gen;
            break;
        }
        
        if (gens_without_improvement >= stagnation_limit) {
            if (verbose) {
                printf("[Gen %d] Stagnation detected. Stopping.\n", gen);
            }
            metrics.generation = gen;
            break;
        }
        
        // Elitismo
        for (int e = 0; e < params.elite_size; e++) {
            int best = 0;
            double best_fit = -1e18;
            for (int i = 0; i < pop_size; i++) {
                bool already_selected = false;
                for (int j = 0; j < e; j++) {
                    if (i == j) {
                        already_selected = true;
                        break;
                    }
                }
                if (!already_selected && fitness[i] > best_fit) {
                    best_fit = fitness[i];
                    best = i;
                }
            }
            copy_grid(new_pop[e]->grid, population[best]->grid, N);
        }
        
        // Generación paralela con reparación local
        #pragma omp parallel
        {
            int thread_id = omp_get_thread_num();
            pcg32_random_t *rng = &THREAD_RNGS[thread_id];
            
            #pragma omp for schedule(dynamic, 4)
            for (int i = params.elite_size; i < pop_size; i++) {
                int p1_idx = tournament_select(fitness, pop_size, params.tournament_k, rng);
                int p2_idx = tournament_select(fitness, pop_size, params.tournament_k, rng);
                
                crossover_uniform(new_pop[i], population[p1_idx], population[p2_idx], rng);
                mutate_path_aware(new_pop[i], current_mut_rate, rng);
                
                // Aplicar reparación local con cierta probabilidad
                if (rand_double(rng) < 0.1) {
                    repair_local(new_pop[i], rng);
                }
            }
        }
        
        Individual **temp = population;
        population = new_pop;
        new_pop = temp;
        
        metrics.generation = gen;
    }
    
    metrics.best_fitness = best_fitness;
    metrics.elapsed_time = omp_get_wtime() - start_time;
    
    double total_fit = 0.0;
    for (int i = 0; i < pop_size; i++) {
        total_fit += fitness[i];
    }
    metrics.avg_fitness = total_fit / pop_size;
    
    free(fitness);
    for (int i = 0; i < pop_size; i++) {
        free_grid(new_pop[i]->grid, N);
        free(new_pop[i]);
    }
    free(new_pop);
    
    return metrics;
}

// ==================== PUZZLE ====================

void generate_random_puzzle(ColorPair *colors, int num_colors, int N, uint64_t seed) {
    pcg32_random_t rng;
    pcg32_init(&rng, seed);
    
    bool **used = malloc(N * sizeof(bool*));
    for (int i = 0; i < N; i++) {
        used[i] = calloc(N, sizeof(bool));
    }
    
    for (int i = 0; i < num_colors; i++) {
        colors[i].color = COLOR_CHARS[i];
        
        int r1, c1, r2, c2;
        do {
            r1 = rand_range(&rng, N);
            c1 = rand_range(&rng, N);
        } while (used[r1][c1]);
        used[r1][c1] = true;
        
        do {
            r2 = rand_range(&rng, N);
            c2 = rand_range(&rng, N);
        } while (used[r2][c2]);
        used[r2][c2] = true;
        
        colors[i].a = (Coord){r1, c1};
        colors[i].b = (Coord){r2, c2};
    }
    
    for (int i = 0; i < N; i++) free(used[i]);
    free(used);
}

// ==================== VISUALIZACIÓN ====================

void print_grid(Individual *ind) {
    int N = ind->N;
    printf("┌");
    for (int i = 0; i < N; i++) printf("──");
    printf("┐\n");
    
    for (int r = 0; r < N; r++) {
        printf("│");
        for (int c = 0; c < N; c++) {
            printf("%c ", ind->grid[r][c]);
        }
        printf("│\n");
    }
    
    printf("└");
    for (int i = 0; i < N; i++) printf("──");
    printf("┘\n");
}

// ==================== MAIN ====================

void print_usage(const char *prog) {
    printf("Usage: %s [options]\n", prog);
    printf("Options:\n");
    printf("  --size N        Board size (default: 5)\n");
    printf("  --colors C      Number of colors (default: 4)\n");
    printf("  --pop P         Population size (default: 300)\n");
    printf("  --gen G         Generations (default: 2000)\n");
    printf("  --mut M         Mutation rate (default: 0.05)\n");
    printf("  --elite E       Elite size (default: 3)\n");
    printf("  --tour K        Tournament size (default: 4)\n");
    printf("  --threads T     Number of threads (default: auto)\n");
    printf("  --seed S        Random seed (default: time)\n");
    printf("  --verbose       Enable verbose output\n");
    printf("  --help          Show this help\n");
}

int main(int argc, char *argv[]) {
    int N = 5;
    int num_colors = 4;
    GAParams params = {
        .pop_size = 300,
        .generations = 2000,
        .mut_rate = 0.05,
        .elite_size = 3,
        .tournament_k = 4,
        .num_threads = omp_get_max_threads()
    };
    uint64_t seed = time(NULL);
    bool verbose = false;
    
    static struct option long_options[] = {
        {"size",    required_argument, 0, 's'},
        {"colors",  required_argument, 0, 'c'},
        {"pop",     required_argument, 0, 'p'},
        {"gen",     required_argument, 0, 'g'},
        {"mut",     required_argument, 0, 'm'},
        {"elite",   required_argument, 0, 'e'},
        {"tour",    required_argument, 0, 'k'},
        {"threads", required_argument, 0, 't'},
        {"seed",    required_argument, 0, 'r'},
        {"verbose", no_argument,       0, 'v'},
        {"help",    no_argument,       0, 'h'},
        {0, 0, 0, 0}
    };
    
    int opt;
    while ((opt = getopt_long(argc, argv, "s:c:p:g:m:e:k:t:r:vh", long_options, NULL)) != -1) {
        switch (opt) {
            case 's': N = atoi(optarg); break;
            case 'c': num_colors = atoi(optarg); break;
            case 'p': params.pop_size = atoi(optarg); break;
            case 'g': params.generations = atoi(optarg); break;
            case 'm': params.mut_rate = atof(optarg); break;
            case 'e': params.elite_size = atoi(optarg); break;
            case 'k': params.tournament_k = atoi(optarg); break;
            case 't': params.num_threads = atoi(optarg); break;
            case 'r': seed = (uint64_t)atoll(optarg); break;
            case 'v': verbose = true; break;
            case 'h': print_usage(argv[0]); return 0;
            default: print_usage(argv[0]); return 1;
        }
    }
    
    if (num_colors > N * N / 3) {
        fprintf(stderr, "Error: Too many colors for board size\n");
        return 1;
    }
    
    // Validación adicional de parámetros
    if (N < 3 || N > 20) {
        fprintf(stderr, "Error: Board size must be between 3 and 20\n");
        return 1;
    }
    
    if (num_colors < 1 || num_colors > 26) {
        fprintf(stderr, "Error: Number of colors must be between 1 and 26\n");
        return 1;
    }
    
    if (params.pop_size < 10 || params.pop_size > 100000) {
        fprintf(stderr, "Error: Population size must be between 10 and 100000\n");
        return 1;
    }
    
    if (params.generations < 1) {
        fprintf(stderr, "Error: Generations must be at least 1\n");
        return 1;
    }
    
    // Inicializar RNGs por thread
    THREAD_RNGS = malloc(params.num_threads * sizeof(pcg32_random_t));
    for (int i = 0; i < params.num_threads; i++) {
        pcg32_init(&THREAD_RNGS[i], seed + i);
    }
    
    printf("=================================================================\n");
    printf("  FLOW GENETIC ALGORITHM - IMPROVED VERSION\n");
    printf("  Features: A* Init, Path-aware Mutation, Local Repair\n");
    printf("=================================================================\n");
    printf("Configuration:\n");
    printf("  Board size:      %dx%d (%d cells)\n", N, N, N*N);
    printf("  Colors:          %d\n", num_colors);
    printf("  Population:      %d\n", params.pop_size);
    printf("  Generations:     %d\n", params.generations);
    printf("  Mutation rate:   %.3f\n", params.mut_rate);
    printf("  Elite size:      %d\n", params.elite_size);
    printf("  Tournament K:    %d\n", params.tournament_k);
    printf("  Threads:         %d\n", params.num_threads);
    printf("  Random seed:     %lu\n", seed);
    printf("=================================================================\n\n");
    
    // Generar puzzle
    ColorPair *colors = malloc(num_colors * sizeof(ColorPair));
    generate_random_puzzle(colors, num_colors, N, seed);
    
    printf("Generated puzzle with %d colors\n", num_colors);
    printf("Terminals:\n");
    for (int i = 0; i < num_colors; i++) {
        printf("  %c: (%d,%d) -> (%d,%d)\n", 
               colors[i].color,
               colors[i].a.r, colors[i].a.c,
               colors[i].b.r, colors[i].b.c);
    }
    printf("\n");
    
    // Inicializar población con A*
    Individual **population = malloc(params.pop_size * sizeof(Individual*));
    
    printf("Initializing population with A* pathfinding...\n");
    
    #pragma omp parallel for
    for (int i = 0; i < params.pop_size; i++) {
        population[i] = malloc(sizeof(Individual));
        population[i]->N = N;
        population[i]->num_colors = num_colors;
        population[i]->colors = colors;
        population[i]->grid = alloc_grid(N);
        
        int thread_id = omp_get_thread_num();
        init_astar_greedy(population[i], &THREAD_RNGS[thread_id]);
    }
    
    printf("Population initialized. Starting evolution...\n\n");
    
    // Ejecutar GA
    GAMetrics metrics = run_ga_parallel(population, params, verbose);
    
    // Resultados
    printf("\n=================================================================\n");
    printf("  RESULTS\n");
    printf("=================================================================\n");
    printf("Generations executed: %d\n", metrics.generation + 1);
    printf("Best fitness:         %.2f\n", metrics.best_fitness);
    printf("Average fitness:      %.2f\n", metrics.avg_fitness);
    printf("Perfect solution:     %s\n", metrics.perfect_found ? "YES ✓" : "NO ✗");
    printf("Elapsed time:         %.3f seconds\n", metrics.elapsed_time);
    
    if (metrics.perfect_found) {
        printf("\n🎉 SUCCESS! Perfect solution found!\n");
    } else {
        printf("\n⚠️  No perfect solution found. Try increasing --pop or --gen\n");
    }
    
    printf("=================================================================\n\n");
    
    // Mostrar mejor solución
    int best_idx = 0;
    double best_fit = calculate_fitness(population[0]);
    for (int i = 1; i < params.pop_size; i++) {
        double fit = calculate_fitness(population[i]);
        if (fit > best_fit) {
            best_fit = fit;
            best_idx = i;
        }
    }
    
    printf("Best solution found:\n");
    print_grid(population[best_idx]);
    
    // Estadísticas detalladas
    printf("\nDetailed analysis:\n");
    int total_connected = 0;
    for (int i = 0; i < num_colors; i++) {
        ColorPair cp = colors[i];
        int size;
        bool conn = bfs_connected(population[best_idx]->grid, N, cp.color, cp.a, cp.b, &size);
        int comps = count_components(population[best_idx]->grid, N, cp.color);
        
        printf("  Color %c: %s | Size: %d | Components: %d\n",
               cp.color,
               conn ? "Connected" : "NOT connected",
               size, comps);
        
        if (conn) total_connected++;
    }
    
    printf("\nConnected colors: %d/%d\n", total_connected, num_colors);
    
    // Cleanup
    for (int i = 0; i < params.pop_size; i++) {
        free_grid(population[i]->grid, N);
        free(population[i]);
    }
    free(population);
    free(colors);
    free(THREAD_RNGS);
    
    return metrics.perfect_found ? 0 : 1;
}