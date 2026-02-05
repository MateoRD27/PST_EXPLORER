"""
cli.py

Interfaz de línea de comandos para:
- listar la estructura del PST
- extraer todos los mensajes de una carpeta seleccionada
- parsear los HTML extraídos y guardar los 'Asuntos' en JSON/CSV
- reducir un archivo asuntos.json a un archivo con {index, asunto}

Uso:
    python3 -m src.pst_explorer.cli list --pst DatosCorreos/portal.pst
    python3 -m src.pst_explorer.cli extract --pst DatosCorreos/portal.pst --folder "Contacto del portal"
    python3 -m src.pst_explorer.cli parse --folder-dir output/portal/None/Principio_del_archivo_de_datos_de_Outlook/Contacto_del_portal --format json
    python3 -m src.pst_explorer.cli reduce --input-json output/.../asuntos.json --output-json output/.../asuntos_reducidos.json
"""

import argparse
from pathlib import Path
from .pst_loader import open_pst, list_folders_with_counts, find_folder_by_name
from .extractor import extract_folder_messages
from .parser import parse_folder_htmls
from .utils import sanitize_filename, ensure_dir, extraer_index_y_asunto


def cmd_list(args):
    pst = open_pst(args.pst)
    root = pst.get_root_folder()
    folders = list_folders_with_counts(root)
    print(f"PST abierto: {args.pst}")
    print("Carpeta raíz:", root.name)
    print("\nEstructura de carpetas y conteo:\n")
    for folder, parts in folders:
        name = folder.name if folder.name is not None else "None"
        indent = "  " * (len(parts) - 1)
        print(f"{indent}- {name} (mensajes: {folder.number_of_sub_messages})")


def cmd_extract(args):
    pst = open_pst(args.pst)
    root = pst.get_root_folder()
    # folders = list_folders_with_counts(root)  # no necesitamos la lista completa aquí

    # buscar folder por nombre (case-insensitive)
    target_name = args.folder
    folder_obj, parts = find_folder_by_name(root, target_name)
    if not folder_obj:
        print(f"Carpeta '{target_name}' no encontrada en el PST.")
        return

    # preparar salida
    pst_basename = Path(args.pst).stem
    output_base = Path(args.output or "output") / sanitize_filename(pst_basename)

    ensure_dir(output_base)
    print(f"Extrayendo todos los mensajes de carpeta: {'/'.join(parts)}")
    count = extract_folder_messages(folder_obj, parts, args.pst, output_base)
    print(f"Extraidos {count} mensajes en: {output_base / '/'.join([sanitize_filename(p) for p in parts])}")


def cmd_parse(args):
    folder_dir = Path(args.folder_dir)
    if not folder_dir.exists() or not folder_dir.is_dir():
        print(f"Directorio no existe: {folder_dir}")
        return

    out_format = args.format.lower()
    if out_format not in ("json", "csv"):
        print("Formato inválido: use json o csv")
        return

    out_file = Path(args.out_file) if args.out_file else folder_dir / f"asuntos.{out_format}"
    ensure_dir(out_file.parent)
    n = parse_folder_htmls(folder_dir, out_file, out_format)
    print(f"Procesados {n} archivos. Resultado guardado en {out_file}")


def cmd_reduce(args):
    """
    Nuevo subcomando: reduce
    Lee un JSON (lista) con registros extraídos (asuntos) y produce un JSON reducido
    con solo {'index': ..., 'asunto': ...}.
    """
    input_path = Path(args.input_json)
    if not input_path.exists():
        print(f"Archivo de entrada no encontrado: {input_path}")
        return

    output_path = Path(args.output_json) if args.output_json else input_path.parent / "asuntos_reducidos.json"
    try:
        extraer_index_y_asunto(input_path, output_path)
        print(f"Archivo reducido creado correctamente: {output_path}")
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")


def build_parser():
    ap = argparse.ArgumentParser(prog="pst_explorer", description="Herramientas para explorar PST y extraer HTML/Asuntos")
    sub = ap.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list", help="Listar estructura y conteo de un PST")
    p_list.add_argument("--pst", required=True, help="Ruta al archivo .pst")

    p_extract = sub.add_parser("extract", help="Extraer todos los mensajes HTML/TXT de una carpeta")
    p_extract.add_argument("--pst", required=True, help="Ruta al archivo .pst")
    p_extract.add_argument("--folder", required=True, help="Nombre de la carpeta a extraer (ej: 'Contacto del portal')")
    p_extract.add_argument("--output", help="Directorio base de salida (por defecto ./output)")

    p_parse = sub.add_parser("parse", help="Parsear archivos guardados en una carpeta y extraer asuntos")
    p_parse.add_argument("--folder-dir", required=True, help="Directorio que contiene msg_*.html (ej: output/portal/Root_Folder/Contacto_del_portal)")
    p_parse.add_argument("--format", default="json", help="Formato de salida: json (default) o csv")
    p_parse.add_argument("--out-file", help="Archivo de salida (opcional)")

    p_reduce = sub.add_parser("reduce", help="Reducir un asuntos.json a un JSON con {index, asunto}")
    p_reduce.add_argument("--input-json", required=True, help="Archivo JSON de entrada (lista de objetos, por ejemplo asuntos.json)")
    p_reduce.add_argument("--output-json", help="Archivo JSON de salida (por defecto asuntos_reducidos.json en la misma carpeta)")

    return ap


def main():
    ap = build_parser()
    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        return

    if args.cmd == "list":
        cmd_list(args)
    elif args.cmd == "extract":
        cmd_extract(args)
    elif args.cmd == "parse":
        cmd_parse(args)
    elif args.cmd == "reduce":
        cmd_reduce(args)
    else:
        print("Comando desconocido")


if __name__ == "__main__":
    main()
