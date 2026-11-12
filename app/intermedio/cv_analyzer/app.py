"""Punto de entrada de Streamlit para el Analizador de Currículums con IA.

Ejecuta main() desde ui.streamlit_ui conforme a la especificación del taller.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Garantizar resolución de paquetes locales (ui, services, models, prompts)
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ui.streamlit_ui import main

if __name__ == "__main__":
    main()

