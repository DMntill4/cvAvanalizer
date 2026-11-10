"""Suite de pruebas unitarias y de validación para el Analizador de Currículums con IA.

Verifica:
1. Contratos y validaciones del modelo Pydantic AnalisisCV.
2. Cumplimiento de la doble escala de umbrales del taller.
3. Extracción de texto con PyPDF2 (casos válidos, vacíos y dañados).
4. Estructura y compilación de ChatPromptTemplate con los 4 pesos solicitados.
5. Invocación determinista y mitigación de fallos históricos de nombres de atributos.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

# Añadir directorio raíz del módulo a sys.path
TEST_DIR = Path(__file__).resolve().parent
MODULE_DIR = TEST_DIR.parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from models.cv_model import AnalisisCV
from prompts.cv_prompts import PROMPT_SISTEMA_RECLUTADOR, crear_sistema_prompts
from services.cv_evaluator import evaluar_candidato, generar_analisis_offline
from services.pdf_processor import extraer_texto_pdf


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture
def analisis_valido_dict() -> dict:
    return {
        "nombre_candidato": "Carlos Mendoza",
        "experiencia_años": 5,
        "habilidades_clave": ["Python", "FastAPI", "Docker", "PostgreSQL"],
        "education": "Ingeniero de Sistemas - Universidad Nacional",
        "experiencia_relevante": "5 años diseñando servicios backend y arquitecturas de microservicios.",
        "fortalezas": [
            "Dominio avanzado del ecosistema Python y patrones de diseño.",
            "Experiencia práctica con contenedores e integración continua.",
        ],
        "areas_mejora": [
            "Ampliar experiencia en arquitecturas de eventos con Kafka.",
        ],
        "porcentaje_ajuste": 85,
    }


@pytest.fixture
def pdf_bytes_valido() -> bytes:
    """Retorna bytes de un PDF con texto digital seleccionable."""
    return b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length 44 >> stream
BT /F1 12 Tf 100 700 Td (Carlos Mendoza - Python Dev) Tj ET
endstream endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000338 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
417
%%EOF"""


# -----------------------------------------------------------------------------
# 1. Pruebas del Modelo Pydantic (AnalisisCV)
# -----------------------------------------------------------------------------
def test_modelo_cv_creacion_valida(analisis_valido_dict):
    """Verifica que un diccionario con todos los campos obligatorios cree AnalisisCV sin errores."""
    analisis = AnalisisCV(**analisis_valido_dict)
    assert analisis.nombre_candidato == "Carlos Mendoza"
    assert analisis.experiencia_años == 5
    assert len(analisis.habilidades_clave) == 4
    assert analisis.porcentaje_ajuste == 85


def test_modelo_cv_campos_obligatorios():
    """Verifica que omitir cualquier campo obligatorio dispare ValidationError."""
    datos_incompletos = {
        "nombre_candidato": "Laura Gómez",
        # Falta experiencia_años
        "habilidades_clave": ["Python"],
        "education": "Licenciada",
        "experiencia_relevante": "Desarrollo web",
        "fortalezas": ["Puntualidad"],
        "areas_mejora": ["Cloud"],
        "porcentaje_ajuste": 75,
    }
    with pytest.raises(ValidationError):
        AnalisisCV(**datos_incompletos)


def test_modelo_cv_validacion_rango_porcentaje(analisis_valido_dict):
    """Verifica que porcentaje_ajuste deba estar estrictamente en el rango [0, 100]."""
    # Menor a 0
    analisis_valido_dict["porcentaje_ajuste"] = -5
    with pytest.raises(ValidationError):
        AnalisisCV(**analisis_valido_dict)

    # Mayor a 100
    analisis_valido_dict["porcentaje_ajuste"] = 105
    with pytest.raises(ValidationError):
        AnalisisCV(**analisis_valido_dict)

    # Límite 0
    analisis_valido_dict["porcentaje_ajuste"] = 0
    obj_cero = AnalisisCV(**analisis_valido_dict)
    assert obj_cero.porcentaje_ajuste == 0

    # Límite 100
    analisis_valido_dict["porcentaje_ajuste"] = 100
    obj_cien = AnalisisCV(**analisis_valido_dict)
    assert obj_cien.porcentaje_ajuste == 100


# -----------------------------------------------------------------------------
# 2. Pruebas de Doble Umbral (Evaluación Principal vs Recomendación Final)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "score,evaluacion_esperada,recomendacion_esperada",
    [
        (100, "Excelente", "Candidato recomendado"),
        (85, "Excelente", "Candidato recomendado"),
        (80, "Excelente", "Candidato recomendado"),
        (75, "Bueno", "Candidato recomendado"),
        (70, "Bueno", "Candidato recomendado"),
        (65, "Bueno", "Candidato con potencial"),  # Ejemplo explícito del taller
        (60, "Bueno", "Candidato con potencial"),
        (55, "Regular", "Candidato con potencial"),
        (50, "Regular", "Candidato con potencial"),
        (45, "Regular", "Candidato no recomendado"),
        (40, "Regular", "Candidato no recomendado"),
        (35, "Bajo", "Candidato no recomendado"),
        (0, "Bajo", "Candidato no recomendado"),
    ],
)
def test_doble_escala_umbrales(analisis_valido_dict, score, evaluacion_esperada, recomendacion_esperada):
    """Verifica la coherencia de la doble escala de umbrales según el documento oficial."""
    analisis_valido_dict["porcentaje_ajuste"] = score
    analisis = AnalisisCV(**analisis_valido_dict)

    assert analisis.clasificar_evaluacion_principal() == evaluacion_esperada
    assert analisis.clasificar_recomendacion_final() == recomendacion_esperada


# -----------------------------------------------------------------------------
# 3. Pruebas del Extractor de PDF (pdf_processor)
# -----------------------------------------------------------------------------
def test_extraer_texto_pdf_valido(pdf_bytes_valido):
    """Verifica la extracción exitosa y la presencia de separadores de página."""
    texto, error = extraer_texto_pdf(pdf_bytes_valido)
    assert error is None
    assert texto is not None
    assert "Carlos Mendoza - Python Dev" in texto
    assert "--- Página 1 ---" in texto


def test_extraer_texto_pdf_vacio():
    """Verifica el manejo de archivos vacíos o None."""
    texto, error = extraer_texto_pdf(b"")
    assert texto is None
    assert error is not None

    texto_none, error_none = extraer_texto_pdf(None)
    assert texto_none is None
    assert "No se proporcionó" in error_none


def test_extraer_texto_pdf_danado():
    """Verifica que un archivo binario corrupto sea interceptado sin colapsar."""
    bytes_danados = b"%PDF-1.4\nContenido binario totalmente corrupto..."
    texto, error = extraer_texto_pdf(bytes_danados)
    assert texto is None
    assert error is not None
    assert "dañado" in error.lower() or "error" in error.lower()


# -----------------------------------------------------------------------------
# 4. Pruebas de Prompts y Criterios Ponderados (cv_prompts)
# -----------------------------------------------------------------------------
def test_prompt_contiene_pesos_solicitados():
    """Verifica que el prompt del sistema contemple explícitamente los 4 pesos solicitados."""
    prompt_str = PROMPT_SISTEMA_RECLUTADOR
    assert "40%" in prompt_str  # Experiencia relevante
    assert "35%" in prompt_str  # Habilidades técnicas
    assert "15%" in prompt_str  # Formación y certificaciones
    assert "10%" in prompt_str  # Coherencia profesional


def test_crear_sistema_prompts_variables_de_entrada():
    """Verifica que la plantilla ChatPromptTemplate reciba las dos entradas requeridas."""
    chat_prompt = crear_sistema_prompts()
    variables = chat_prompt.input_variables
    assert "descripcion_puesto" in variables
    assert "cv_texto" in variables


# -----------------------------------------------------------------------------
# 5. Pruebas de Inferencia Offline y Contingencia de Atributos (cv_evaluator)
# -----------------------------------------------------------------------------
def test_generar_analisis_offline_determinista():
    """Verifica que el motor offline genere un AnalisisCV completamente válido."""
    cv = """
    Alejandro Martínez
    Ingeniero de Software con 4 años de experiencia en desarrollo backend con Python, Django y PostgreSQL.
    Manejo de Docker, Git y despliegue de microservicios.
    """
    puesto = "Se busca Desarrollador Python con 3 años de experiencia, Docker y PostgreSQL."

    resultado = generar_analisis_offline(cv, puesto)
    assert isinstance(resultado, AnalisisCV)
    assert resultado.experiencia_años >= 3
    assert "Python" in resultado.habilidades_clave
    assert 0 <= resultado.porcentaje_ajuste <= 100
    assert len(resultado.fortalezas) >= 1
    assert len(resultado.areas_mejora) >= 1
    # Asegurar que se usaron los nombres de campo correctos (no fotalezas ni porcetaje_ajuste)
    assert hasattr(resultado, "fortalezas")
    assert hasattr(resultado, "porcentaje_ajuste")


def test_evaluar_candidato_valida_entradas_vacias():
    """Verifica que no se permita evaluar si alguna de las entradas está vacía."""
    with pytest.raises(ValueError, match="currículum"):
        evaluar_candidato(cv_texto="", descripcion_puesto="Puesto válido")

    with pytest.raises(ValueError, match="descripción"):
        evaluar_candidato(cv_texto="Texto válido de CV", descripcion_puesto="")
