"""Interfaz de usuario Streamlit para el Analizador de Currículums con IA.

Presenta el formulario de carga de CV en PDF y descripción del puesto, ejecuta
la extracción y evaluación semántica mediante LangChain y muestra los resultados
estructurados con doble umbral de clasificación sin emojis.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import streamlit as st

# Asegurar que el directorio del módulo esté en sys.path para resolución de imports
CURRENT_DIR = Path(__file__).resolve().parent.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from models.cv_model import AnalisisCV
from services.cv_evaluator import evaluar_candidato
from services.pdf_processor import extraer_texto_pdf

# -----------------------------------------------------------------------------
# Constantes y Diccionarios de Umbrales del Taller
# -----------------------------------------------------------------------------
COLORES_EVALUACION = {
    "Excelente": "#10B981",  # Esmeralda
    "Bueno": "#3B82F6",      # Azul cielo
    "Regular": "#F59E0B",    # Ámbar
    "Bajo": "#EF4444",       # Carmesí
}

COLORES_RECOMENDACION = {
    "Candidato recomendado": "#10B981",
    "Candidato con potencial": "#3B82F6",
    "Candidato no recomendado": "#EF4444",
}

SVG_ICONS = {
    "document": (
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>'
        '<polyline points="14 2 14 8 20 8"></polyline>'
        '<line x1="16" y1="13" x2="8" y2="13"></line>'
        '<line x1="16" y1="17" x2="8" y2="17"></line>'
        '<polyline points="10 9 9 9 8 9"></polyline>'
        '</svg>'
    ),
    "user_check": (
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>'
        '<circle cx="8.5" cy="7" r="4"></circle>'
        '<polyline points="17 11 19 13 23 9"></polyline>'
        '</svg>'
    ),
    "award": (
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="8" r="7"></circle>'
        '<polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"></polyline>'
        '</svg>'
    ),
    "alert": (
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="10"></circle>'
        '<line x1="12" y1="8" x2="12" y2="12"></line>'
        '<line x1="12" y1="16" x2="12.01" y2="16"></line>'
        '</svg>'
    ),
}


def aplicar_estilos_tecnicos():
    """Inyecta estilos CSS sin emojis y con diseño corporativo estructurado."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        code, pre {
            font-family: 'JetBrains Mono', monospace !important;
        }

        /* Cabecera Técnica */
        .cv-header-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1.2rem 0 0.8rem 0;
            border-bottom: 1px solid rgba(148, 163, 184, 0.15);
            margin-bottom: 1.5rem;
        }

        .cv-header-brand {
            display: flex;
            align-items: center;
            gap: 0.9rem;
        }

        .cv-header-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 44px;
            height: 44px;
            border-radius: 10px;
            background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%);
            color: #ffffff;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25);
        }

        .cv-title {
            font-size: 1.6rem;
            font-weight: 800;
            letter-spacing: -0.025em;
            margin: 0;
            line-height: 1.2;
            color: var(--text-color, #0F172A);
        }

        .cv-subtitle {
            font-size: 0.85rem;
            color: #64748B;
            margin: 0;
            font-weight: 500;
        }

        .cv-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.35rem 0.8rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
            background: rgba(2, 132, 199, 0.1);
            color: #0284C7;
            border: 1px solid rgba(2, 132, 199, 0.25);
        }

        /* Tarjetas de resultados */
        .result-card {
            background: rgba(30, 41, 59, 0.03);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
            padding: 1.2rem;
            margin-bottom: 1rem;
        }

        .score-box {
            text-align: center;
            padding: 1.2rem;
            background: rgba(2, 132, 199, 0.06);
            border: 1px solid rgba(2, 132, 199, 0.2);
            border-radius: 12px;
            margin-bottom: 1.2rem;
        }

        .score-number {
            font-size: 3.2rem;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            line-height: 1;
            margin-bottom: 0.2rem;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.4rem 0.85rem;
            border-radius: 6px;
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 0.03em;
        }

        /* Lista de habilidades en tags */
        .skill-tag {
            display: inline-block;
            padding: 0.3rem 0.65rem;
            margin: 0.2rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
            background: rgba(148, 163, 184, 0.12);
            color: var(--text-color, #1E293B);
            border: 1px solid rgba(148, 163, 184, 0.25);
            font-family: 'JetBrains Mono', monospace;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def obtener_evaluacion_principal(score: int) -> tuple[str, str]:
    """Calcula la evaluación principal según la tabla oficial:

    80–100: Excelente
    60–79: Bueno
    40–59: Regular
    0–39: Bajo
    """
    if score >= 80:
        return "Excelente", COLORES_EVALUACION["Excelente"]
    if score >= 60:
        return "Bueno", COLORES_EVALUACION["Bueno"]
    if score >= 40:
        return "Regular", COLORES_EVALUACION["Regular"]
    return "Bajo", COLORES_EVALUACION["Bajo"]


def obtener_recomendacion_final(score: int) -> tuple[str, str]:
    """Calcula la recomendación final según la tabla oficial:

    70–100: Candidato recomendado
    50–69: Candidato con potencial
    0–49: Candidato no recomendado
    """
    if score >= 70:
        return "Candidato recomendado", COLORES_RECOMENDACION["Candidato recomendado"]
    if score >= 50:
        return "Candidato con potencial", COLORES_RECOMENDACION["Candidato con potencial"]
    return "Candidato no recomendado", COLORES_RECOMENDACION["Candidato no recomendado"]


def main():
    """Función principal de la aplicación Streamlit."""
    st.set_page_config(
        page_title="Analizador de Currículums con IA",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    aplicar_estilos_tecnicos()

    # -------------------------------------------------------------------------
    # Cabecera
    # -------------------------------------------------------------------------
    st.markdown(
        f"""
        <div class="cv-header-container">
            <div class="cv-header-brand">
                <div class="cv-header-icon">
                    {SVG_ICONS['document']}
                </div>
                <div>
                    <h1 class="cv-title">Analizador de Currículums con IA</h1>
                    <p class="cv-subtitle">Evaluación semántica de ajuste a perfiles profesionales con LangChain y modelos estructurados</p>
                </div>
            </div>
            <div>
                <span class="cv-badge">LangChain LCEL &middot; Pydantic v2 &middot; OpenAI / Gemini</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------------------------------------------------
    # Barra Lateral: Configuración del Motor
    # -------------------------------------------------------------------------
    with st.sidebar:
        st.markdown("### Configuración del Motor")
        st.caption("Ajustes de inferencia y credenciales")
        st.divider()

        proveedor_opcion = st.selectbox(
            "Proveedor de IA:",
            options=["OpenAI (Estándar gpt-4o-mini)", "Google Gemini (Alternativa Gratuita)"],
            index=0,
            help="OpenAI es el modelo especificado por el taller. Gemini está disponible como contingencia.",
        )
        es_gemini = "gemini" in proveedor_opcion.lower()

        if es_gemini:
            gemini_key_env = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
            api_key = st.text_input(
                "Gemini API Key:",
                value=gemini_key_env,
                type="password",
                placeholder="Ingresa clave o define GEMINI_API_KEY en .env",
            )
            modelo_activo = "gemini-3.5-flash"
            prov_code = "gemini"
        else:
            openai_key_env = os.getenv("OPENAI_API_KEY") or ""
            api_key = st.text_input(
                "OpenAI API Key:",
                value=openai_key_env if openai_key_env != "tu_clave_de_openai_aqui" else "",
                type="password",
                placeholder="Ingresa clave o define OPENAI_API_KEY en .env",
            )
            modelo_activo = "gpt-4o-mini"
            prov_code = "openai"

        modo_offline = st.checkbox(
            "Modo Demostración (Offline)",
            value=False,
            help="Genera un análisis sintético determinista sin consumir llamadas externas a la API.",
        )

        st.divider()
        st.markdown("**Criterios y Ponderaciones del Taller**")
        st.markdown(
            """
            - **Experiencia Relevante:** 40%
            - **Habilidades Técnicas:** 35%
            - **Formación y Certificaciones:** 15%
            - **Coherencia Profesional:** 10%
            """
        )

    # -------------------------------------------------------------------------
    # Formulario Principal: Entradas (PDF + Descripción del Puesto)
    # -------------------------------------------------------------------------
    col_izq, col_der = st.columns([1, 1], gap="medium")

    with col_izq:
        st.markdown("#### 1. Currículum Vitae (PDF)")
        st.caption("Carga un documento PDF que contenga texto digital seleccionable.")
        archivo_cargado = st.file_uploader(
            "Cargar archivo PDF",
            type=["pdf"],
            help="Se leerá en memoria mediante PyPDF2.",
            label_visibility="collapsed",
        )

        if archivo_cargado is not None:
            st.success(f"Archivo cargado: `{archivo_cargado.name}` ({archivo_cargado.size / 1024:.1f} KB)")

    with col_der:
        st.markdown("#### 2. Descripción y Requisitos de la Vacante")
        st.caption("Detalla el puesto, experiencia mínima, requisitos técnicos y responsabilidades.")

        ejemplo_default = (
            "Puesto: Desarrollador Python Senior\n"
            "Requisitos obligatorios: 3 años de experiencia en desarrollo backend, dominio de Python, diseño de APIs REST y PostgreSQL.\n"
            "Deseables: Docker, pruebas automatizadas (pytest) y experiencia con LangChain o modelos de IA.\n"
            "Responsabilidades: diseñar microservicios robustos, integrar APIs externas y optimizar consultas en base de datos."
        )

        descripcion_puesto = st.text_area(
            "Descripción del puesto:",
            value=ejemplo_default,
            height=140,
            label_visibility="collapsed",
            placeholder="Escribe aquí los requisitos de la vacante...",
        )

    st.markdown("---")

    # -------------------------------------------------------------------------
    # Acciones y Botones
    # -------------------------------------------------------------------------
    b_col1, b_col2, b_col3, _ = st.columns([1.5, 1.2, 1.3, 2.5])

    with b_col1:
        boton_analizar = st.button("Analizar Candidato", type="primary", use_container_width=True)

    with b_col2:
        boton_limpiar = st.button("Limpiar", use_container_width=True)

    with b_col3:
        boton_guardar = st.button("Guardar Análisis", use_container_width=True)

    if boton_limpiar:
        st.rerun()

    if boton_guardar:
        st.info("Funcionalidad en desarrollo. El análisis no se almacena en base de datos.")

    # -------------------------------------------------------------------------
    # Ejecución del Análisis al pulsar "Analizar Candidato"
    # -------------------------------------------------------------------------
    if boton_analizar:
        # Validación 1: Comprobar existencia de ambas entradas
        if archivo_cargado is None:
            st.warning("Debes cargar un archivo PDF con el currículum vitae para continuar.")
            st.stop()

        if not descripcion_puesto or not descripcion_puesto.strip():
            st.warning("Debes ingresar la descripción y requisitos del puesto para continuar.")
            st.stop()

        # Validación 2: Extracción del texto del PDF
        with st.spinner("Extrayendo texto del archivo PDF con PyPDF2..."):
            texto_cv, error_pdf = extraer_texto_pdf(archivo_cargado)

        if error_pdf is not None or not texto_cv:
            st.error(f"Fallo en la lectura del documento PDF:\n\n{error_pdf}")
            st.stop()

        # Validación 3: Inferencia con LangChain + Pydantic
        with st.spinner("Evaluando perfil y contrastando con los requisitos del puesto..."):
            try:
                analisis: AnalisisCV = evaluar_candidato(
                    cv_texto=texto_cv,
                    descripcion_puesto=descripcion_puesto,
                    api_key=api_key or None,
                    model=modelo_activo,
                    proveedor=prov_code,
                    modo_offline=modo_offline,
                )
            except Exception as exc_eval:
                st.error(
                    f"No fue posible completar la evaluación estructurada del candidato:\n\n{exc_eval}\n\n"
                    "Verifica que la clave del proveedor sea válida y tenga cuota activa, o utiliza el Modo Demostración."
                )
                st.stop()

        # ---------------------------------------------------------------------
        # Renderizado de Resultados Estructurados
        # ---------------------------------------------------------------------
        st.markdown("### Resultado del Análisis")

        score = analisis.porcentaje_ajuste
        eval_principal, color_eval = obtener_evaluacion_principal(score)
        rec_final, color_rec = obtener_recomendacion_final(score)

        # Panel de Resumen de Puntuación
        p_col1, p_col2 = st.columns([1, 2], gap="large")

        with p_col1:
            st.markdown(
                f"""
                <div class="score-box">
                    <div style="font-size: 0.85rem; font-weight: 600; color: #64748B; text-transform: uppercase; margin-bottom: 0.4rem;">
                        Porcentaje de Ajuste
                    </div>
                    <div class="score-number" style="color: {color_eval};">
                        {score}%
                    </div>
                    <div style="display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap; margin-top: 0.8rem;">
                        <span class="status-badge" style="background: {color_eval}22; color: {color_eval}; border: 1px solid {color_eval}55;">
                            Evaluación: {eval_principal}
                        </span>
                        <span class="status-badge" style="background: {color_rec}22; color: {color_rec}; border: 1px solid {color_rec}55;">
                            Recomendación: {rec_final}
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with p_col2:
            st.markdown(
                f"""
                <div class="result-card">
                    <h3 style="margin: 0 0 0.5rem 0; font-size: 1.25rem;">{analisis.nombre_candidato}</h3>
                    <p style="margin: 0 0 0.5rem 0; color: #64748B; font-size: 0.9rem;">
                        <strong>Años de Experiencia Relevante:</strong> {analisis.experiencia_años} años &middot; 
                        <strong>Formación:</strong> {analisis.education}
                    </p>
                    <p style="margin: 0; font-size: 0.93rem; line-height: 1.5;">
                        <strong>Trayectoria Relevante:</strong> {analisis.experiencia_relevante}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Secciones Detalladas
        st.markdown("#### Habilidades Clave Identificadas")
        if analisis.habilidades_clave:
            tags_html = "".join([f'<span class="skill-tag">{h}</span>' for h in analisis.habilidades_clave])
            st.markdown(tags_html, unsafe_allow_html=True)
        else:
            st.caption("No se detectaron habilidades específicas.")

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

        d_col1, d_col2 = st.columns(2, gap="medium")

        with d_col1:
            st.markdown("#### Fortalezas Principales")
            for f in analisis.fortalezas:
                st.markdown(f"- {f}")

        with d_col2:
            st.markdown("#### Áreas de Desarrollo y Brechas")
            for a in analisis.areas_mejora:
                st.markdown(f"- {a}")


if __name__ == "__main__":
    main()
