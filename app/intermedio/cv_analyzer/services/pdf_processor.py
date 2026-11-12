"""Procesamiento y extracción de texto de documentos PDF con PyPDF2.

Lee el archivo en memoria, concatena las páginas con separadores legibles
y valida que contenga texto extraíble antes de enviarlo al modelo de lenguaje.
"""

from __future__ import annotations

import io
from typing import BinaryIO, Union
import PyPDF2


def extraer_texto_pdf(archivo_pdf: Union[BinaryIO, bytes, io.BytesIO]) -> tuple[str | None, str | None]:
    """Extrae el contenido de texto de un archivo PDF en memoria.

    Recorre todas las páginas del documento y las concatena agregando separadores
    de página estandarizados.

    Args:
        archivo_pdf: Objeto de archivo en memoria (UploadedFile de Streamlit, BytesIO o bytes).

    Returns:
        Tupla (texto_extraido, mensaje_error):
        - Si la extracción es exitosa: (texto_concatenado, None)
        - Si ocurre un fallo o no hay texto: (None, mensaje_explicativo)
    """
    if archivo_pdf is None:
        return None, "No se proporcionó ningún archivo para procesar."

    try:
        # Normalizar a stream de bytes si se pasó bytes crudos
        if isinstance(archivo_pdf, bytes):
            stream = io.BytesIO(archivo_pdf)
        elif hasattr(archivo_pdf, "read"):
            # Streamlit UploadedFile o BytesIO
            archivo_pdf.seek(0)
            stream = io.BytesIO(archivo_pdf.read())
            # Restaurar cursor si tiene seek
            archivo_pdf.seek(0)
        else:
            return None, "Tipo de archivo o buffer no soportado."

        reader = PyPDF2.PdfReader(stream)

        if reader.is_encrypted:
            try:
                # Intentar desencriptar con clave vacía
                reader.decrypt("")
            except Exception:
                return (
                    None,
                    "El archivo PDF está protegido con contraseña o encriptado. "
                    "Por favor proporciona un documento sin restricciones de acceso.",
                )

        num_paginas = len(reader.pages)
        if num_paginas == 0:
            return None, "El documento PDF no contiene páginas legibles."

        paginas_texto: list[str] = []

        for idx, pagina in enumerate(reader.pages, start=1):
            try:
                texto_pagina = pagina.extract_text() or ""
                texto_limpio = texto_pagina.strip()
                if texto_limpio:
                    paginas_texto.append(f"--- Página {idx} ---\n{texto_limpio}")
            except Exception as e_page:
                # Continuar con las demás páginas si una sola falla
                continue

        texto_completo = "\n\n".join(paginas_texto).strip()

        if not texto_completo:
            return (
                None,
                "No se encontró texto seleccionable en el PDF. Es posible que el "
                "documento sea un escaneo o una imagen. Este analizador requiere "
                "PDFs con texto digital seleccionable (sin OCR).",
            )

        return texto_completo, None

    except PyPDF2.errors.PdfReadError as pdf_err:
        return (
            None,
            f"El archivo PDF está dañado o tiene un formato no válido: {pdf_err}",
        )
    except Exception as exc:
        return (
            None,
            f"Ocurrió un error inesperado al leer el archivo PDF: {exc}",
        )

