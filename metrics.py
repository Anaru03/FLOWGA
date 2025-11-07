# Módulo de métricas para el Algoritmo Genético
import json
import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    from .utils import Color, Coord
except ImportError:
    from utils import Color, Coord

@dataclass
class GenerationMetrics:
    """Métricas de una generación específica."""
    generation: int
    best_fitness: float
    avg_fitness: float
    worst_fitness: float
    std_fitness: float
    diversity_score: float
    convergence_rate: float
    perfect_solutions: int

@dataclass
class GAMetrics:
    """Métricas completas del Algoritmo Genético."""
    # Parámetros de configuración
    pop_size: int
    generations: int
    mut_rate: float
    elite_size: int
    tournament_k: int
    board_size: int
    num_colors: int
    
    # Métricas de tiempo
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    total_time: float = 0.0
    avg_generation_time: float = 0.0
    
    # Métricas de convergencia
    generations_to_solution: Optional[int] = None
    convergence_generation: Optional[int] = None
    final_best_fitness: float = 0.0
    success: bool = False
    
    # Métricas de evaluaciones
    total_fitness_evaluations: int = 0
    
    # Métricas de rendimiento por generación
    generation_metrics: List[GenerationMetrics] = field(default_factory=list)
    
    # Estadísticas de fitness
    fitness_evolution: List[float] = field(default_factory=list)
    diversity_evolution: List[float] = field(default_factory=list)
    convergence_evolution: List[float] = field(default_factory=list)
    
    # Métricas de población
    initial_diversity: float = 0.0
    final_diversity: float = 0.0
    max_diversity: float = 0.0
    min_diversity: float = float('inf')
    
    # Métricas de exploración/explotación
    exploration_phases: int = 0
    exploitation_phases: int = 0
    stagnation_periods: int = 0
    
    def start_timing(self):
        """Inicia el cronómetro."""
        self.start_time = time.time()
    
    def end_timing(self):
        """Termina el cronómetro y calcula métricas de tiempo."""
        self.end_time = time.time()
        self.total_time = self.end_time - self.start_time
        if self.generation_metrics:
            self.avg_generation_time = self.total_time / len(self.generation_metrics)
    
    def add_generation_metric(self, metric: GenerationMetrics):
        """Añade métricas de una generación."""
        self.generation_metrics.append(metric)
        self.fitness_evolution.append(metric.best_fitness)
        self.diversity_evolution.append(metric.diversity_score)
        self.convergence_evolution.append(metric.convergence_rate)
        
        # Actualizar métricas de diversidad
        if metric.diversity_score > self.max_diversity:
            self.max_diversity = metric.diversity_score
        if metric.diversity_score < self.min_diversity:
            self.min_diversity = metric.diversity_score
            
        # Detectar convergencia (cuando la mejora es mínima)
        if (self.convergence_generation is None and 
            len(self.fitness_evolution) > 10 and
            metric.convergence_rate < 0.01):
            self.convergence_generation = metric.generation
    
    def finalize_metrics(self, solution_found: bool, final_fitness: float):
        """Finaliza las métricas del algoritmo."""
        self.end_timing()
        self.success = solution_found
        self.final_best_fitness = final_fitness
        
        if solution_found and self.generations_to_solution is None:
            self.generations_to_solution = len(self.generation_metrics)
        
        # Calcular métricas finales de diversidad
        if self.generation_metrics:
            self.initial_diversity = self.generation_metrics[0].diversity_score
            self.final_diversity = self.generation_metrics[-1].diversity_score
        
        # Analizar fases de exploración/explotación
        self._analyze_phases()
    
    def _analyze_phases(self):
        """Analiza las fases de exploración y explotación."""
        if len(self.diversity_evolution) < 5:
            return
            
        exploration_threshold = statistics.mean(self.diversity_evolution) * 1.1
        stagnation_threshold = 0.01
        
        current_phase = None
        stagnation_count = 0
        
        for i, (diversity, convergence) in enumerate(zip(self.diversity_evolution, self.convergence_evolution)):
            if diversity > exploration_threshold:
                if current_phase != 'exploration':
                    self.exploration_phases += 1
                    current_phase = 'exploration'
            elif convergence < stagnation_threshold:
                stagnation_count += 1
                if stagnation_count > 5:
                    if current_phase != 'stagnation':
                        self.stagnation_periods += 1
                        current_phase = 'stagnation'
            else:
                if current_phase != 'exploitation':
                    self.exploitation_phases += 1
                    current_phase = 'exploitation'
                stagnation_count = 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen de las métricas."""
        return {
            'configuracion': {
                'poblacion': self.pop_size,
                'generaciones': self.generations,
                'tasa_mutacion': self.mut_rate,
                'elite': self.elite_size,
                'torneo_k': self.tournament_k,
                'tablero': f"{self.board_size}x{self.board_size}",
                'colores': self.num_colors
            },
            'rendimiento': {
                'exito': self.success,
                'tiempo_total': round(self.total_time, 3),
                'tiempo_por_generacion': round(self.avg_generation_time, 4),
                'generaciones_ejecutadas': len(self.generation_metrics),
                'generaciones_hasta_solucion': self.generations_to_solution,
                'generacion_convergencia': self.convergence_generation,
                'evaluaciones_fitness': self.total_fitness_evaluations
            },
            'fitness': {
                'fitness_final': round(self.final_best_fitness, 2),
                'mejor_fitness': round(max(self.fitness_evolution) if self.fitness_evolution else 0, 2),
                'fitness_promedio': round(statistics.mean(self.fitness_evolution) if self.fitness_evolution else 0, 2),
                'mejora_total': round(max(self.fitness_evolution) - min(self.fitness_evolution) if len(self.fitness_evolution) > 1 else 0, 2)
            },
            'diversidad': {
                'diversidad_inicial': round(self.initial_diversity, 3),
                'diversidad_final': round(self.final_diversity, 3),
                'diversidad_maxima': round(self.max_diversity, 3),
                'diversidad_minima': round(self.min_diversity, 3),
                'perdida_diversidad': round(self.initial_diversity - self.final_diversity, 3)
            },
            'fases': {
                'exploracion': self.exploration_phases,
                'explotacion': self.exploitation_phases,
                'estancamiento': self.stagnation_periods
            }
        }
    
    def export_to_json(self, filename: str):
        """Exporta las métricas a un archivo JSON."""
        data = {
            'resumen': self.get_summary(),
            'evolucion_fitness': self.fitness_evolution,
            'evolucion_diversidad': self.diversity_evolution,
            'evolucion_convergencia': self.convergence_evolution,
            'metricas_por_generacion': [
                {
                    'generacion': gm.generation,
                    'mejor_fitness': gm.best_fitness,
                    'fitness_promedio': gm.avg_fitness,
                    'peor_fitness': gm.worst_fitness,
                    'desviacion_fitness': gm.std_fitness,
                    'diversidad': gm.diversity_score,
                    'convergencia': gm.convergence_rate,
                    'soluciones_perfectas': gm.perfect_solutions
                } for gm in self.generation_metrics
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

def calculate_diversity(population: List[List[List[str]]], board_size: int) -> float:
    """Calcula la diversidad de la población usando distancia de Hamming normalizada."""
    if len(population) < 2:
        return 0.0
    
    total_distance = 0
    comparisons = 0
    
    for i in range(len(population)):
        for j in range(i + 1, len(population)):
            distance = hamming_distance(population[i], population[j], board_size)
            total_distance += distance
            comparisons += 1
    
    # Normalizar por el número de comparaciones y el máximo posible
    max_possible_distance = board_size * board_size
    return (total_distance / comparisons) / max_possible_distance if comparisons > 0 else 0.0

def hamming_distance(grid1: List[List[str]], grid2: List[List[str]], board_size: int) -> int:
    """Calcula la distancia de Hamming entre dos grids."""
    distance = 0
    for r in range(board_size):
        for c in range(board_size):
            if grid1[r][c] != grid2[r][c]:
                distance += 1
    return distance

def calculate_convergence_rate(fitness_history: List[float], window_size: int = 5) -> float:
    """Calcula la tasa de convergencia basada en la mejora reciente."""
    if len(fitness_history) < window_size:
        return 1.0
    
    recent_fitness = fitness_history[-window_size:]
    if len(set(recent_fitness)) == 1:  # Todos iguales
        return 0.0
    
    improvement = (max(recent_fitness) - min(recent_fitness)) / abs(max(recent_fitness)) if max(recent_fitness) != 0 else 0.0
    return min(improvement, 1.0)

def count_perfect_solutions(population: List[List[List[str]]], terminals: Dict[Color, Tuple[Coord, Coord]]) -> int:
    """Cuenta cuántas soluciones perfectas hay en la población."""
    try:
        from .genetic_algorithm import is_perfect
    except ImportError:
        from genetic_algorithm import is_perfect
    
    count = 0
    for individual in population:
        if is_perfect(individual, terminals):
            count += 1
    return count