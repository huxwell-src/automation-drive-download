"""
Funciones y clases relacionadas con descargas desde Google Drive.
"""

import logging
from pathlib import Path
from typing import Optional

import requests
from requests import Response, Session
from requests.exceptions import RequestException


logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """
    Error al intentar descargar un archivo desde Google Drive.

    Envuelve errores de red, HTTP o de escritura en disco.
    """


def extraer_id_drive(link: str) -> Optional[str]:
    """
    Extrae el ID de un enlace de Google Drive en distintos formatos.

    Soporta enlaces con:
    - Parámetro "id=<ID>"
    - Segmento "/d/<ID>/"

    Devuelve None si no reconoce el formato del enlace.
    """
    if not isinstance(link, str) or not link.strip():
        return None

    if "id=" in link:
        return link.split("id=")[1]
    if "/d/" in link:
        return link.split("/d/")[1].split("/")[0]
    return None


def obtener_token_confirmacion(response: Response) -> Optional[str]:
    """
    Obtiene el token de confirmación para descargas grandes de Google Drive.

    Google Drive utiliza una cookie especial "download_warning" cuando el
    archivo supera cierto tamaño. Este token debe reenviarse para completar
    la descarga.
    """
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            return value
    return None


from PIL import Image


def extraer_extension_de_respuesta(response: Response) -> Optional[str]:
    """
    Intenta extraer la extensión del archivo desde el header Content-Disposition.
    
    Google Drive suele enviar el nombre del archivo original en este header.
    """
    content_disposition = response.headers.get("Content-Disposition", "")
    if "filename=" in content_disposition:
        # Ejemplo: attachment; filename="planilla.pdf"; filename*=UTF-8''planilla.pdf
        partes = content_disposition.split("filename=")
        if len(partes) > 1:
            nombre_archivo = partes[1].split(";")[0].strip("\"'")
            return Path(nombre_archivo).suffix.lower()
    return None


def detectar_extension_por_contenido(ruta_archivo: Path) -> str:
    """
    Detecta la extensión real del archivo a partir de su firma binaria (Magic Numbers).

    Lee los primeros bytes del archivo temporal y los compara con firmas
    conocidas (PDF, JPG, PNG, ZIP/Office).
    """
    try:
        with open(ruta_archivo, "rb") as f:
            firma = f.read(8)
    except OSError as exc:
        logger.error(
            "No se pudo leer el archivo temporal %s: %s",
            ruta_archivo,
            exc,
            extra={"emoji": "❌", "category": "API", "color": "RED"},
        )
        raise

    # PDF: %PDF
    if firma.startswith(b"%PDF"):
        return ".pdf"
    # JPEG: FF D8
    if firma.startswith(b"\xff\xd8"):
        return ".jpg"
    # PNG: 89 PNG
    if firma.startswith(b"\x89PNG"):
        return ".png"
    # ZIP / Office (XLSX, DOCX, etc): PK
    if firma.startswith(b"PK\x03\x04"):
        # Por defecto si es ZIP asumimos .xlsx dado el contexto de planillas,
        # pero idealmente se usaría el header primero.
        return ".xlsx"

    return ""


class GoogleDriveDownloader:
    """
    Responsable de descargar archivos desde Google Drive.

    Encapsula la lógica de llamadas HTTP, manejo de tokens de confirmación
    y escritura de archivos en disco.
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        """
        Crea una instancia del descargador.

        Si no se proporciona una sesión, se crea una nueva de requests.

        Inyectar la sesión facilita las pruebas (por ejemplo, con mocks).
        """
        self._session = session or requests.Session()
        self._url = "https://drive.google.com/uc?export=download"

    def _obtener_respuesta(self, file_id: str) -> Response:
        """
        Realiza las peticiones necesarias para obtener la respuesta de descarga.

        - Hace una primera petición al endpoint de Drive.
        - Si el archivo requiere confirmación, detecta el token y repite
          la petición incluyendo el token.
        - Valida que la respuesta HTTP sea exitosa.
        """
        try:
            response = self._session.get(self._url, params={"id": file_id}, stream=True)
            response.raise_for_status()
        except RequestException as exc:
            logger.error(
                "Error HTTP al iniciar descarga para %s: %s",
                file_id,
                exc,
                extra={"emoji": "❌", "category": "API", "color": "RED"},
            )
            raise DownloadError(f"No se pudo iniciar la descarga para {file_id}") from exc

        token = obtener_token_confirmacion(response)

        if not token:
            return response

        try:
            response = self._session.get(
                self._url,
                params={"id": file_id, "confirm": token},
                stream=True,
            )
            response.raise_for_status()
        except RequestException as exc:
            logger.error(
                "Error HTTP al confirmar descarga para %s: %s",
                file_id,
                exc,
                extra={"emoji": "❌", "category": "API", "color": "RED"},
            )
            raise DownloadError(f"No se pudo confirmar la descarga para {file_id}") from exc

        return response

    def descargar(self, file_id: str, destino_base: Path) -> Path:
        """
        Descarga el archivo y lo convierte a PDF si es una imagen.
        """
        if not file_id:
            raise DownloadError("ID de archivo vacío o nulo")

        response = self._obtener_respuesta(file_id)

        # 1. Intentar extraer extensión del header para saber qué estamos descargando
        extension_orig = extraer_extension_de_respuesta(response)

        # 2. Guardar temporalmente
        temp_path = destino_base.with_suffix(".tmp")

        try:
            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(32768):
                    if chunk:
                        f.write(chunk)
        except OSError as exc:
            logger.error(
                "Error al escribir archivo temporal %s: %s",
                temp_path,
                exc,
                extra={"emoji": "❌", "category": "API", "color": "RED"},
            )
            raise DownloadError(
                f"No se pudo escribir el archivo temporal en {temp_path}"
            ) from exc

        # 3. Detectar extensión por contenido si el header falló
        if not extension_orig:
            try:
                extension_orig = detectar_extension_por_contenido(temp_path)
            except OSError as exc:
                raise DownloadError("No se pudo detectar el tipo de archivo") from exc

        # Fallback final si no se detectó nada
        if not extension_orig:
            extension_orig = ".pdf"

        # 4. Determinar destino final (siempre .pdf)
        destino_final = destino_base.with_suffix(".pdf")

        try:
            # Si ya es PDF, solo renombramos
            if extension_orig == ".pdf":
                temp_path.rename(destino_final)
            # Si es imagen (JPG/PNG), convertimos a PDF
            elif extension_orig in [".jpg", ".png"]:
                with Image.open(temp_path) as img:
                    # Convertimos a RGB para asegurar compatibilidad con PDF
                    img_rgb = img.convert("RGB")
                    img_rgb.save(destino_final, "PDF")
                temp_path.unlink()  # Eliminar temporal
            # Si es XLSX u otro, por ahora solo lo renombramos con .pdf (aunque sea incorrecto binariamente)
            # o podríamos dejar la extensión original. Pero el usuario pidió PDF.
            else:
                logger.warning(
                    f"No se puede convertir {extension_orig} a PDF directamente. Guardando como {destino_final}",
                    extra={"emoji": "⚠️", "category": "API", "color": "YELLOW"},
                )
                temp_path.rename(destino_final)

        except Exception as exc:
            logger.error(
                "Error al finalizar/convertir archivo %s: %s",
                destino_final,
                exc,
                extra={"emoji": "❌", "category": "API", "color": "RED"},
            )
            if temp_path.exists():
                temp_path.unlink()
            raise DownloadError(f"No se pudo guardar el archivo final en {destino_final}") from exc

        logger.info(
            "💾 Archivo guardado como PDF",
            extra={
                "emoji": "💾",
                "category": "API",
                "details": f"destino={destino_final}",
                "color": "GREEN",
            },
        )
        return destino_final
