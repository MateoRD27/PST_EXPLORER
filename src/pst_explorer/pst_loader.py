"""
pst_loader.py

Funciones para:
- abrir un PST
- obtener la carpeta raíz
- listar carpetas (recursivo) con conteo de mensajes
- buscar carpeta por nombre
"""

from pathlib import Path
import pypff
from typing import List, Tuple
from .utils import sanitize_filename

def open_pst(path: str) -> pypff.file:
    """
    Abre un archivo PST y devuelve el objeto pypff.file.
    Lanza excepción si no existe o no se puede abrir.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"PST file not found: {path}")
    pst = pypff.file()
    pst.open(str(p))
    return pst


def list_folders_with_counts(root_folder) -> List[Tuple[object, List[str]]]:
    """
    Recorre recursivamente las carpetas e imprime el conteo.
    Devuelve lista de tuplas (folder_obj, path_parts) donde path_parts es la ruta de nombres.
    """
    results = []

    def _rec(folder, path_parts):
        name = folder.name if folder.name is not None else "None"
        results.append((folder, path_parts + [name]))
        for i in range(folder.number_of_sub_folders):
            _rec(folder.get_sub_folder(i), path_parts + [name])

    _rec(root_folder, [])
    return results


def find_folder_by_name(root_folder, target_name: str):
    """
    Busca la primera carpeta que tenga exactamente el nombre target_name (case-sensitive).
    Devuelve el objeto folder o None.
    """
    for folder, parts in list_folders_with_counts(root_folder):
        if (folder.name == target_name) or (folder.name is not None and folder.name.lower() == target_name.lower()):
            return folder, parts
    return None, None
