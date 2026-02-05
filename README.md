# PST_EXPLORER2

Proyecto para explorar archivos `.pst`, extraer cuerpos HTML/TXT de mensajes por carpeta y extraer el campo "Asunto" de los HTML guardados.

1. Tener Python 3.12 (o 3.x moderno).
2. Instalar `pypff` (binding de libpff) desde paquetes del sistema:
   ```bash
   sudo apt update
   sudo apt install -y python3-pypff


Crear y activar un entorno virtual con acceso a paquetes del sistema:
    python3 -m venv venv --system-site-packages
    source venv/bin/activate

Instalar dependencias Python:
    pip install -r requirements.txt

Comandos principales

Listar la estructura y conteo:

    python3 -m src.pst_explorer.cli list --pst DatosCorreos/portal.pst


Extraer todos los mensajes (HTML/TXT) de una carpeta (por nombre):

    python3 -m src.pst_explorer.cli extract --pst DatosCorreos/portal.pst --folder "Contacto del portal"



Esto crea output/portal/.../Contacto_del_portal/messages.jsonl y archivos msg_*.html.

Parsear los archivos guardados y extraer todos los "Asuntos":

    python3 -m src.pst_explorer.cli parse --folder-dir output/portal/None/Principio_del_archivo_de_datos_de_Outlook/Contacto_del_portal --format json


Resultado: asuntos.json (por defecto) o asuntos.csv si --format csv

reducir el archivo asuntos.json a asuntos_reducidos.json:

    python3 -m src.pst_explorer.cli reduce --input-json output/portal/None/Principio_del_archivo_de_datos_de_Outlook/Contacto_del_portal/asuntos.json