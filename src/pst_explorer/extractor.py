"""
extractor.py

Funciones para extraer TODOS los mensajes (HTML o texto) de una carpeta pypff.folder.
Guarda cada mensaje como archivo y crea messages.jsonl con metadatos.
"""

from pathlib import Path
import json
import datetime
from .utils import ensure_dir, sanitize_filename, iso_or_none
import typing

def extract_folder_messages(folder_obj, folder_path_parts: typing.List[str], pst_path: str, output_base: Path) -> int:
    """
    Extrae todos los mensajes de 'folder_obj'.
    - folder_path_parts: lista con nombres de la ruta (ej: ["Root", "Inbox"])
    - pst_path: ruta original del PST (para metadata)
    - output_base: Path base donde crear la salida
    Retorna el número de mensajes extraídos.
    """
    sanitized_parts = [sanitize_filename(p) for p in folder_path_parts]
    folder_out_dir = output_base.joinpath(*sanitized_parts)
    ensure_dir(folder_out_dir)

    jsonl_path = folder_out_dir / "messages.jsonl"
    total = getattr(folder_obj, "number_of_sub_messages", 0)
    if total == 0:
        return 0

    with jsonl_path.open("w", encoding="utf-8") as jf:
        for idx in range(total):
            try:
                msg = folder_obj.get_sub_message(idx)
            except Exception as e:
                # registrar y saltar
                print(f"[WARN] No se pudo obtener mensaje idx={idx}: {e}")
                continue

            # id seguro
            identifier = getattr(msg, "identifier", None)
            idstr = str(identifier) if identifier is not None else f"idx{idx}"

            meta = {
                "file": pst_path,
                "folder_path": "/".join(folder_path_parts),
                "folder_sanitized": "/".join(sanitized_parts),
                "index_in_folder": idx,
                "identifier": idstr,
                "subject": getattr(msg, "subject", None),
                "sender_name": getattr(msg, "sender_name", None),
                "creation_time": iso_or_none(getattr(msg, "creation_time", None)),
                "delivery_time": iso_or_none(getattr(msg, "delivery_time", None)),
                "has_html_body": bool(getattr(msg, "html_body", None)),
                "has_plain_text_body": bool(getattr(msg, "plain_text_body", None)),
                "number_of_attachments": getattr(msg, "number_of_attachments", 0),
                "extracted_body_path": None,
                "extraction_time": datetime.datetime.utcnow().isoformat() + "Z"
            }

            # guardar body
            html_bytes = getattr(msg, "html_body", None)
            plain_text = getattr(msg, "plain_text_body", None)

            try:
                if html_bytes:
                    try:
                        html_text = html_bytes.decode("utf-8", errors="replace")
                    except Exception:
                        html_text = html_bytes.decode("latin-1", errors="replace")
                    fname = f"msg_{idx}_{idstr}.html"
                    fpath = folder_out_dir / fname
                    fpath.write_text(html_text, encoding="utf-8", errors="replace")
                    meta["extracted_body_path"] = str(fpath.relative_to(output_base))
                elif plain_text:
                    fname = f"msg_{idx}_{idstr}.txt"
                    fpath = folder_out_dir / fname
                    fpath.write_text(str(plain_text), encoding="utf-8", errors="replace")
                    meta["extracted_body_path"] = str(fpath.relative_to(output_base))
                else:
                    fname = f"msg_{idx}_{idstr}.txt"
                    fpath = folder_out_dir / fname
                    fpath.write_text("", encoding="utf-8")
                    meta["extracted_body_path"] = str(fpath.relative_to(output_base))
            except Exception as e:
                print(f"[ERROR] Guardando body idx={idx}: {e}")

            # escribir meta por línea (JSONL)
            jf.write(json.dumps(meta, ensure_ascii=False) + "\n")

            if (idx + 1) % 50 == 0 or (idx + 1) == total:
                print(f"  procesados {idx + 1}/{total}")

    return total
