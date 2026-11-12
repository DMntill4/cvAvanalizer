"""Servicio de evaluación semántica de currículums con LangChain y modelos estructurados.

Configura el modelo de ChatOpenAI (gpt-4o-mini, temperature=0.2) o proveedores
alternativos con salida estructurada conforme al esquema Pydantic AnalisisCV.
Corrige el fallo histórico de campos mal nombrados ('fotalezas' -> 'fortalezas',
'porcetaje_ajuste' -> 'porcentaje_ajuste') en los bloques de contingencia.
"""

from __future__ import annotations

import os
import re
from typing import Any, Optional

from dotenv import load_dotenv

from models.cv_model import AnalisisCV
from prompts.cv_prompts import crear_sistema_prompts

# Cargar variables de entorno locales si existen
load_dotenv()

MODELO_OPENAI_DEFAULT = "gpt-4o-mini"
TEMPERATURA_DEFAULT = 0.2


def crear_evaluador_cv(
    api_key: Optional[str] = None,
    model: str = MODELO_OPENAI_DEFAULT,
    temperature: float = TEMPERATURA_DEFAULT,
    proveedor: str = "openai",
) -> Any:
    """Configura el modelo de chat con salida estructurada forzada mediante AnalisisCV.

    Args:
        api_key: Clave de la API (opcional; si se omite, se lee del entorno).
        model: Nombre del modelo a utilizar (por defecto 'gpt-4o-mini').
        temperature: Temperatura del modelo (por defecto 0.2 para respuestas consistentes).
        proveedor: 'openai' (predeterminado) o 'gemini' (contingencia).

    Returns:
        Modelo con salida estructurada mediante with_structured_output(AnalisisCV).
    """
    prov_clean = proveedor.lower().strip()

    if prov_clean == "gemini":
        key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError(
                "No se encontró la clave de API de Google Gemini (GEMINI_API_KEY). "
                "Por favor defínela en el archivo .env o en la interfaz."
            )
        from langchain_google_genai import ChatGoogleGenerativeAI

        modelo_gemini = model if "gemini" in model else "gemini-3.5-flash"
        chat_llm = ChatGoogleGenerativeAI(
            model=modelo_gemini,
            google_api_key=key,
            temperature=temperature,
            max_retries=2,
        )
        return chat_llm.with_structured_output(AnalisisCV)

    # Proveedor OpenAI estándar
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key or key.strip() == "tu_clave_de_openai_aqui":
        raise ValueError(
            "No se ha configurado una clave de API válida para OpenAI (OPENAI_API_KEY). "
            "Por favor proporciona tu clave en el entorno o en el panel de configuración."
        )

    from langchain_openai import ChatOpenAI

    chat_llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_key=key,
        max_retries=2,
    )
    return chat_llm.with_structured_output(AnalisisCV)


def generar_analisis_offline(cv_texto: str, descripcion_puesto: str) -> AnalisisCV:
    """Generador determinista de análisis para pruebas sin conexión o cuotas agotadas.

    Calcula de manera transparente los componentes clave a partir de coincidencias
    léxicas en el texto del currículum y la vacante para mantener el sistema operativo.
    """
    texto_cv_l = cv_texto.lower()
    desc_l = descripcion_puesto.lower()

    # Extracción aproximada del nombre (primera línea no vacía sin encabezado genérico)
    nombre = "Candidato Evaluado"
    for linea in cv_texto.splitlines():
        l_strip = linea.strip()
        if (
            l_strip
            and not l_strip.lower().startswith("---")
            and len(l_strip.split()) <= 4
            and not any(w in l_strip.lower() for w in ["curriculum", "cv", "resume", "resumen"])
        ):
            nombre = l_strip
            break

    # Estimación de años de experiencia
    patron_años = re.findall(r"(\d+)\s*(?:\+)?\s*(?:años|years|anos)", texto_cv_l)
    años = max([int(a) for a in patron_años if int(a) <= 45], default=3)

    # Detección de habilidades comunes
    habilidades_candidato = []
    stack_conocido = [
        "python", "docker", "sql", "postgresql", "fastapi", "django", "flask",
        "langchain", "react", "git", "aws", "azure", "linux", "rest", "graphql",
        "machine learning", "pandas", "numpy", "scikit-learn", "ci/cd", "kubernetes"
    ]
    for tech in stack_conocido:
        if tech in texto_cv_l:
            habilidades_candidato.append(tech.title())

    if not habilidades_candidato:
        habilidades_candidato = ["Resolución de problemas", "Trabajo en equipo", "Gestión de proyectos"]

    # Detección de educación
    educacion = "Formación Profesional / Licenciatura en Computación o afín"
    if "master" in texto_cv_l or "maestría" in texto_cv_l:
        educacion = "Maestría / Postgrado en área tecnológica"
    elif "ingeniería" in texto_cv_l or "ingeniero" in texto_cv_l or "engineering" in texto_cv_l:
        educacion = "Grado o Ingeniería en Sistemas / Informática"

    # Coincidencia con la descripción para el score
    coincidencias = sum(1 for h in habilidades_candidato if h.lower() in desc_l)
    total_deseadas = max(len([h for h in stack_conocido if h in desc_l]), 1)
    ratio = min(coincidencias / total_deseadas, 1.0)

    score = int(40 + (ratio * 50))
    score = max(0, min(100, score))

    fortalezas = [
        f"Experiencia consolidada estimada en {años} años en áreas tecnológicas.",
        f"Dominio comprobado de herramientas clave: {', '.join(habilidades_candidato[:3])}.",
        "Coherencia en la presentación de responsabilidades y trayectoria laboral.",
    ]

    areas_mejora = [
        "Profundizar en certificaciones formales de la nube o frameworks específicos del puesto.",
        "Detallar métricas cuantitativas de impacto en proyectos anteriores.",
    ]

    resumen_exp = (
        f"El candidato presenta una trayectoria de aproximadamente {años} años orientada "
        f"al desarrollo y tecnologías coincidentes con las necesidades de la vacante."
    )

    return AnalisisCV(
        nombre_candidato=nombre,
        experiencia_años=años,
        habilidades_clave=habilidades_candidato[:8],
        education=educacion,
        experiencia_relevante=resumen_exp,
        fortalezas=fortalezas,
        areas_mejora=areas_mejora,
        porcentaje_ajuste=score,
    )


def evaluar_candidato(
    cv_texto: str,
    descripcion_puesto: str,
    api_key: Optional[str] = None,
    model: str = MODELO_OPENAI_DEFAULT,
    temperature: float = TEMPERATURA_DEFAULT,
    proveedor: str = "openai",
    modo_offline: bool = False,
) -> AnalisisCV:
    """Ejecuta el pipeline de evaluación: prompt | modelo_estructurado.

    Args:
        cv_texto: Texto extraído íntegramente del CV.
        descripcion_puesto: Requisitos y responsabilidades del puesto.
        api_key: Clave del proveedor de LLM.
        model: Nombre del modelo a invocar.
        temperature: Parámetro de temperatura.
        proveedor: 'openai' o 'gemini'.
        modo_offline: Si es True, utiliza el motor de evaluación determinista local.

    Returns:
        Instancia validada de AnalisisCV con todos sus campos obligatorios.

    Raises:
        ValueError: Si los textos de entrada están vacíos o incompletos.
        Exception: Si la llamada al modelo estructurado falla y no se autoriza contingencia.
    """
    if not cv_texto or not cv_texto.strip():
        raise ValueError("El texto extraído del currículum vitae no puede estar vacío.")

    if not descripcion_puesto or not descripcion_puesto.strip():
        raise ValueError("La descripción del puesto de trabajo no puede estar vacía.")

    if modo_offline:
        return generar_analisis_offline(cv_texto, descripcion_puesto)

    try:
        # 1. Crear el modelo estructurado
        modelo_estructurado = crear_evaluador_cv(
            api_key=api_key,
            model=model,
            temperature=temperature,
            proveedor=proveedor,
        )

        # 2. Crear la plantilla de prompts
        chat_prompt = crear_sistema_prompts()

        # 3. Compilar la cadena LCEL con el operador tubería (|)
        cadena = chat_prompt | modelo_estructurado

        # 4. Invocar con las variables esperadas
        resultado = cadena.invoke({
            "descripcion_puesto": descripcion_puesto.strip(),
            "cv_texto": cv_texto.strip(),
        })

        if isinstance(resultado, dict):
            resultado = AnalisisCV(**resultado)
        elif not isinstance(resultado, AnalisisCV):
            raise TypeError(
                f"El modelo estructurado retornó un tipo inesperado: {type(resultado)}"
            )

        return resultado

    except Exception as exc:
        # Manejo riguroso del error: corrección del bug original donde se intentaba
        # instanciar AnalisisCV con 'fotalezas' y 'porcetaje_ajuste'.
        error_msg = str(exc)

        # Si el error es de cuota o clave ausente, permitir fallback automático si se solicita
        if "429" in error_msg or "quota" in error_msg.lower() or "RESOURCE_EXHAUSTED" in error_msg:
            # Fallback seguro con nombres corregidos: fortalezas y porcentaje_ajuste
            analisis_contingencia = generar_analisis_offline(cv_texto, descripcion_puesto)
            analisis_contingencia.areas_mejora.append(
                "Nota técnica del sistema: Inferencia completada con motor de contingencia local "
                "debido a agotamiento de cuota en la API externa."
            )
            return analisis_contingencia

        # Re-lanzar para que la interfaz muestre el mensaje de error explícito y exacto
        raise RuntimeError(
            f"Fallo en la inferencia del modelo estructurado ({type(exc).__name__}): {error_msg}"
        ) from exc

