# Configuración y constantes del proyecto Flow
from typing import Dict

# colorama opcional 
try:
    from colorama import Back, Fore, Style
    from colorama import init as colorama_init
    colorama_init()
    COLOR_ENABLED = True
except Exception:
    class Dummy:
        def __getattr__(self, k): return ""
    Fore = Back = Style = Dummy()
    COLOR_ENABLED = False

# ====== paleta de colores (añade los que quieras) ======
# 🎨 Paleta EXTENDIDA - Hasta 30+ colores usando códigos ANSI 256-color
# Los primeros 15 usan colorama estándar, los demás usan códigos ANSI directos

# Función auxiliar para crear códigos ANSI de fondo con 256 colores
def _ansi_bg(code: int) -> str:
    """Genera código ANSI de fondo para 256 colores."""
    return f'\033[48;5;{code}m' if COLOR_ENABLED else ''

def _ansi_fg(code: int) -> str:
    """Genera código ANSI de texto para 256 colores."""
    return f'\033[38;5;{code}m' if COLOR_ENABLED else ''

# 🎨 Paleta BASE con 6 colores sólidos y distintos
BACK = {
    "B": Back.BLUE,      # Azul
    "R": Back.RED,       # Rojo
    "Y": Back.YELLOW,    # Amarillo
    "G": Back.GREEN,     # Verde
    "M": Back.MAGENTA,   # Magenta/Morado
    "C": Back.CYAN       # Cyan/Celeste
}

# 🎨 Colores adicionales SOLO si están disponibles (hasta 15 colores con colorama)
try:
    BACK.update({
        "W": Back.WHITE,                                    # Blanco (7)
        "K": getattr(Back, 'LIGHTBLACK_EX', Back.BLACK),   # Gris (8)
        "L": getattr(Back, 'LIGHTBLUE_EX', None),          # Azul claro (9)
        "N": getattr(Back, 'LIGHTGREEN_EX', None),         # Verde claro (10)
        "T": getattr(Back, 'LIGHTYELLOW_EX', None),        # Amarillo claro (11)
        "V": getattr(Back, 'LIGHTRED_EX', None),           # Rojo claro (12)
        "P": getattr(Back, 'LIGHTMAGENTA_EX', None),       # Magenta claro (13)
        "X": getattr(Back, 'LIGHTCYAN_EX', None),          # Cyan claro (14)
        "O": getattr(Back, 'LIGHTWHITE_EX', None),         # Blanco brillante (15)
    })
    # Limpiar los None (colores no disponibles)
    BACK = {k: v for k, v in BACK.items() if v is not None}
except Exception:
    pass  # Mantener solo los 6 colores base

# 🌈 COLORES EXTENDIDOS usando paleta ANSI 256 (colores 16-30)
# Estos son códigos ANSI directos que funcionan en terminales modernos
BACK.update({
    # Naranjas y marrones (16-18)
    "1": _ansi_bg(208),  # Naranja brillante
    "2": _ansi_bg(130),  # Marrón/naranja oscuro
    "3": _ansi_bg(94),   # Púrpura oscuro
    
    # Verdes y azules especiales (19-21)
    "4": _ansi_bg(28),   # Verde bosque
    "5": _ansi_bg(33),   # Azul cielo
    "6": _ansi_bg(63),   # Púrpura/violeta
    
    # Rosas y rojos especiales (22-24)
    "7": _ansi_bg(197),  # Rosa fuerte
    "8": _ansi_bg(161),  # Rosa/magenta
    "9": _ansi_bg(124),  # Rojo vino
    
    # Amarillos y verdes especiales (25-27)
    "a": _ansi_bg(220),  # Amarillo dorado
    "b": _ansi_bg(34),   # Verde agua
    "c": _ansi_bg(118),  # Verde lima
    
    # Azules y grises especiales (28-30)
    "d": _ansi_bg(25),   # Azul marino
    "e": _ansi_bg(240),  # Gris oscuro
    "f": _ansi_bg(250),  # Gris claro
})

# ⚠️ NOTA: Si quieres AÚN MÁS colores (30+), añade más letras o símbolos:
# "A", "D", "E", "F", "H", "I", "J", "Q", "S", "U", "Z", etc.
# Códigos ANSI 256 disponibles: 16-255 (pero algunos son muy similares)

FORE = {
    "B": Fore.BLUE,
    "R": Fore.RED,
    "Y": Fore.YELLOW,
    "G": Fore.GREEN,
    "M": Fore.MAGENTA,
    "C": Fore.CYAN
}

try:
    FORE.update({
        "W": Fore.WHITE,
        "K": getattr(Fore, 'LIGHTBLACK_EX', Fore.BLACK),
        "L": getattr(Fore, 'LIGHTBLUE_EX', None),
        "N": getattr(Fore, 'LIGHTGREEN_EX', None),
        "T": getattr(Fore, 'LIGHTYELLOW_EX', None),
        "V": getattr(Fore, 'LIGHTRED_EX', None),
        "P": getattr(Fore, 'LIGHTMAGENTA_EX', None),
        "X": getattr(Fore, 'LIGHTCYAN_EX', None),
        "O": getattr(Fore, 'LIGHTWHITE_EX', None),
    })
    FORE = {k: v for k, v in FORE.items() if v is not None}
except Exception:
    pass

# Añadir colores FORE correspondientes para los nuevos colores ANSI
FORE.update({
    "1": _ansi_fg(208), "2": _ansi_fg(130), "3": _ansi_fg(94),
    "4": _ansi_fg(28),  "5": _ansi_fg(33),  "6": _ansi_fg(63),
    "7": _ansi_fg(197), "8": _ansi_fg(161), "9": _ansi_fg(124),
    "a": _ansi_fg(220), "b": _ansi_fg(34),  "c": _ansi_fg(118),
    "d": _ansi_fg(25),  "e": _ansi_fg(240), "f": _ansi_fg(250),
})

# Parametrización del fitness (valores por defecto que pueden overridearse por CLI)
FIT_PARAMS = {
    'multi_comp_penalty': 500.0,
    'connect_reward': 3000.0,
    'excess_penalty': 5.0,
    'not_connected_base': 800.0,
    'not_connected_manh_penalty': 60.0,
    'smooth_weight': 0.2,
    'compact_bonus_scale': 2.0,  # se multiplica contra comp_size en el bonus
}