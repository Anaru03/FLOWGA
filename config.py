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
# 🎨 Paleta BASE con 6 colores sólidos y distintos
BACK = {
    "B": Back.BLUE,      # Azul
    "R": Back.RED,       # Rojo
    "Y": Back.YELLOW,    # Amarillo
    "G": Back.GREEN,     # Verde
    "M": Back.MAGENTA,   # Magenta/Morado
    "C": Back.CYAN       # Cyan/Celeste
}

# 🎨 Colores adicionales SOLO si están disponibles (hasta 15 colores)
# Usamos los LIGHT* variants solo si existen, sino repetimos con Style.BRIGHT
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