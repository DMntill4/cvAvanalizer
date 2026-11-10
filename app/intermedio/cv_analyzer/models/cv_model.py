"""Esquema de datos Pydantic para el análisis estructurado de currículums.

Define la estructura de salida que el modelo de lenguaje debe generar
obligatoriamente mediante la técnica with_structured_output de LangChain.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalisisCV(BaseModel):
    """Modelo estructurado que contiene el análisis exhaustivo de un candidato."""

    nombre_candidato: str = Field(
        ...,
        description="Nombre completo del candidato extraído fielmente del currículum vitae.",
    )
    experiencia_años: int = Field(
        ...,
        description="Número total de años de experiencia laboral relevante identificados en el CV.",
        ge=0,
    )
    habilidades_clave: list[str] = Field(
        ...,
        description="Lista de habilidades técnicas, herramientas y competencias clave del candidato pertinentes al puesto.",
    )
    education: str = Field(
        ...,
        description="Nivel educativo máximo, titulación académica y especializaciones principales alcanzadas.",
    )
    experiencia_relevante: str = Field(
        ...,
        description="Síntesis narrativa de la trayectoria profesional directamente aplicable a las responsabilidades de la vacante.",
    )
    fortalezas: list[str] = Field(
        ...,
        description="Puntos fuertes, ventajas competitivas y logros sobresalientes del candidato frente al perfil solicitado.",
    )
    areas_mejora: list[str] = Field(
        ...,
        description="Áreas de desarrollo, conocimientos ausentes o brechas técnicas identificadas en relación con los requisitos.",
    )
    porcentaje_ajuste: int = Field(
        ...,
        description="Puntuación numérica estimada de adecuación al puesto, evaluada holísticamente entre 0 y 100.",
        ge=0,
        le=100,
    )

    def clasificar_evaluacion_principal(self) -> str:
        """Determina la categoría de evaluación principal según los umbrales del taller:

        80–100: Excelente
        60–79: Bueno
        40–59: Regular
        0–39: Bajo
        """
        score = self.porcentaje_ajuste
        if score >= 80:
            return "Excelente"
        if score >= 60:
            return "Bueno"
        if score >= 40:
            return "Regular"
        return "Bajo"

    def clasificar_recomendacion_final(self) -> str:
        """Determina la recomendación de contratación según los umbrales del taller:

        70–100: Candidato recomendado
        50–69: Candidato con potencial
        0–49: Candidato no recomendado
        """
        score = self.porcentaje_ajuste
        if score >= 70:
            return "Candidato recomendado"
        if score >= 50:
            return "Candidato con potencial"
        return "Candidato no recomendado"
