"""
utils.py
Utilidades: sanitizar nombres, crear directorios, logging simple y helpers.
También contiene la función extraer_index_y_asunto que transforma asuntos.json.
"""

from pathlib import Path
import re
import logging
import sys
import json

# Logging básico
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("pst_explorer")


def sanitize_filename(name: str, max_len: int = 200) -> str:
    """
    Crear un nombre de archivo/carpeta seguro a partir de un string arbitrario.
    Reemplaza caracteres problemáticos por '_' y limita longitud.
    """
    if name is None:
        name = "None"
    name = re.sub(r"\s+", " ", name).strip()
    safe = re.sub(r"[^A-Za-z0-9\-\._ ]+", "_", name)
    safe = safe.replace(" ", "_")
    if len(safe) > max_len:
        safe = safe[:max_len]
    return safe


def ensure_dir(path: Path):
    """
    Crea directorio y padres si no existen.
    """
    path.mkdir(parents=True, exist_ok=True)


def iso_or_none(dt):
    """
    Convierte datetime a ISO string o devuelve None.
    pypff entrega datetime para varios campos.
    """
    if dt is None:
        return None
    try:
        return dt.isoformat()
    except Exception:
        return str(dt)


def extraer_index_y_asunto(
    input_json_path: Path,
    output_json_path: Path
) -> None:
    """
    Lee un archivo JSON con resultados de extracción de correos
    (una lista de objetos), y genera un nuevo JSON con solo:
        - index  (desde index_in_folder)
        - asunto  (desde extracted_asunto)

    """

    if not input_json_path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {input_json_path}"
        )

    # Leer JSON
    with input_json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(
            "El archivo JSON debe contener una lista de objetos"
        )

    resultado = []

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            logger.warning(f"Registro {i} ignorado: no es un objeto JSON")
            continue

        index = item.get("index_in_folder")
        asunto = item.get("extracted_asunto")

        if index is None or asunto is None:
            logger.warning(f"Registro {i} incompleto: falta index o asunto")
            continue

        # Asegurar tipos básicos
        try:
            index_val = int(index)
        except Exception:
            index_val = index  # dejar como venga si no es int

        resultado.append({
            "index": index_val,
            "asunto": asunto
        })

    # Guardar resultado
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    with output_json_path.open("w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    logger.info(f"Archivo reducido escrito en: {output_json_path}")
