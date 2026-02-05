"""
parser.py

Funciones para:
- abrir los archivos HTML guardados de una carpeta de salida
- extraer el campo 'Asunto' del HTML (patrón robusto)
- guardar todos los asuntos en JSON o CSV
"""

from pathlib import Path
from bs4 import BeautifulSoup
import json
import csv
from .utils import ensure_dir
from typing import Optional

def extract_asunto_from_html_text(html_text: str) -> Optional[str]:
    """
    Extrae el valor que sigue a la etiqueta 'Asunto:' dentro del HTML.
    Estrategia:
    - buscar <td> cuyo texto sea 'Asunto:' (case-insensitive)
    - tomar el siguiente <tr> y su <td> y extraer texto limpio
    - fallback: buscar 'Asunto' como label y tomar el siguiente sibling de texto
    """
    soup = BeautifulSoup(html_text, "lxml")

    # buscar td con exacto 'Asunto:'
    for td in soup.find_all("td"):
        text = td.get_text(strip=True)
        if text and text.lower() == "asunto:":
            parent_tr = td.find_parent("tr")
            if parent_tr:
                next_tr = parent_tr.find_next_sibling("tr")
                if next_tr:
                    val_td = next_tr.find("td")
                    if val_td:
                        return val_td.get_text(strip=True)

    # fallback: buscar etiquetas fuertes / b que contengan 'Asunto'
    for strong in soup.find_all(["b", "strong"]):
        t = strong.get_text(strip=True)
        if t and "asunto" in t.lower():
            # puede estar en el siguiente sibling
            ns = strong.find_next(string=True)
            if ns:
                candidate = ns.strip()
                if candidate:
                    return candidate

    # fallback: buscar texto 'Asunto:' en todo el HTML y tomar lo que sigue
    full = soup.get_text(separator="\n")
    idx = full.lower().find("asunto:")
    if idx != -1:
        after = full[idx + len("asunto:"):].strip()
        # tomar la primera línea
        return after.splitlines()[0].strip()

    return None


def parse_folder_htmls(folder_output_dir: Path, out_file: Path, out_format: str = "json"):
    """
    Recorre todos los .html/.txt en folder_output_dir y extrae el asunto.
    Guarda resultados en out_file (json or csv).
    Cada registro contiene: {index_in_folder, identifier, subject_header, extracted_asunto, file_path}
    """
    ensure_dir(out_file.parent)
    records = []

    for p in sorted(folder_output_dir.glob("msg_*")):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            text = ""

        extracted = extract_asunto_from_html_text(text)
        # identifier y index desde filename msg_{idx}_{id}.*
        name = p.stem  # msg_{idx}_{id}
        parts = name.split("_", 2)
        idx = None
        ident = None
        if len(parts) >= 3:
            try:
                idx = int(parts[1])
            except Exception:
                idx = parts[1]
            ident = parts[2]
        record = {
            "file": str(p),
            "index_in_folder": idx,
            "identifier": ident,
            "extracted_asunto": extracted
        }
        records.append(record)

    # guardar
    if out_format.lower() == "json":
        with out_file.open("w", encoding="utf-8") as fh:
            json.dump(records, fh, ensure_ascii=False, indent=2)
    elif out_format.lower() == "csv":
        with out_file.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["file", "index_in_folder", "identifier", "extracted_asunto"])
            writer.writeheader()
            for r in records:
                writer.writerow(r)
    else:
        raise ValueError("Unsupported format: use json or csv")

    return len(records)
