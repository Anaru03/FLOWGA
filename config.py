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
BACK = {"B": Back.BLUE, "R": Back.RED, "Y": Back.YELLOW, "G": Back.GREEN,
    "O": Back.MAGENTA, "C": Back.CYAN}
# Añadir algunos alias/colores extras (si colorama está presente se usarán)
BACK.update({"P": getattr(Back, 'LIGHTMAGENTA_EX', Back.MAGENTA),
         "W": getattr(Back, 'WHITE', Back.RESET),
         "K": getattr(Back, 'BLACK', Back.RESET),
         "M": getattr(Back, 'LIGHTCYAN_EX', Back.CYAN)})

FORE = {"B": Fore.BLUE, "R": Fore.RED, "Y": Fore.YELLOW, "G": Fore.GREEN,
    "O": Fore.MAGENTA, "C": Fore.CYAN}
FORE.update({"P": getattr(Fore, 'LIGHTMAGENTA_EX', Fore.MAGENTA),
         "W": getattr(Fore, 'WHITE', Fore.RESET),
         "K": getattr(Fore, 'BLACK', Fore.RESET),
         "M": getattr(Fore, 'LIGHTCYAN_EX', Fore.CYAN)})

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