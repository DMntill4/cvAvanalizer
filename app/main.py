"""Punto de entrada principal del repositorio compartido.

Permite acceder a los diferentes módulos de la aplicación o redirigir
directamente al analizador de currículums en app/intermedio/cv_analyzer.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import streamlit as st

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent
CV_ANALYZER_DIR = BASE_DIR / "intermedio" / "cv_analyzer"

st.set_page_config(
    page_title="Portal de Aplicaciones IA | Docker Base",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Portal de Aplicaciones IA y LangChain")
st.caption("Entorno de desarrollo compartido con Docker y Streamlit")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Analizador de Currículums con IA")
    st.write(
        "Módulo de evaluación y comparación de CVs en formato PDF frente a perfiles "
        "de puesto utilizando modelos estructurados con LangChain y Pydantic."
    )
    if st.button("Iniciar Analizador de CV", use_container_width=True, type="primary"):
        # Importar y ejecutar la interfaz del analizador de CV
        if str(CV_ANALYZER_DIR) not in sys.path:
            sys.path.insert(0, str(CV_ANALYZER_DIR))
        from ui.streamlit_ui import main as cv_main
        cv_main()
        st.stop()

with col2:
    st.subheader("Información del Entorno")
    st.markdown(
        """
        - **Python:** 3.12
        - **Framework:** Streamlit + LangChain
        - **Módulo Activo:** `app/intermedio/cv_analyzer/app.py`
        - **Modelos Compatibles:** OpenAI (gpt-4o-mini) y Google Gemini
        """
    )
