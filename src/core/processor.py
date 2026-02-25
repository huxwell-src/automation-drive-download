"""
Lógica de alto nivel para procesar el Excel y descargar planillas.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

from src.models.config import ConfigError, DownloadConfig
from src.services.drive_downloader import (
    DownloadError,
    GoogleDriveDownloader,
    extraer_id_drive,
)
from src.utils.log_utils import ProgressBar, timed_operation


logger = logging.getLogger(__name__)


def preparar_carpetas(config: DownloadConfig) -> Tuple[Path, Path]:
    """
    Crea las carpetas de salida y devuelve rutas OSDE y NO OSDE.

    Si no existen, se crean:
    - <output_dir>/OSDE
    - <output_dir>/NO es osde

    Lanza ConfigError si alguna carpeta no se puede crear.
    """
    osde_path = config.output_dir / config.osde_subdir
    no_osde_path = config.output_dir / config.non_osde_subdir

    for carpeta in (osde_path, no_osde_path):
        try:
            carpeta.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.error(
                "No se pudo crear la carpeta %s: %s",
                carpeta,
                exc,
                extra={"emoji": "❌", "category": "DB", "color": "RED"},
            )
            raise ConfigError(f"No se pudo crear la carpeta {carpeta}") from exc

    return osde_path, no_osde_path


def cargar_excel(config: DownloadConfig) -> pd.DataFrame:
    """
    Carga el archivo Excel y valida columnas obligatorias.

    - Verifica que el archivo existe.
    - Intenta leer el Excel con pandas.
    - Comprueba que estén presentes las columnas necesarias.

    Devuelve un DataFrame listo para iterar.
    """
    if not config.excel_path.exists():
        raise ConfigError(f"No se encontró el archivo de Excel: {config.excel_path}")

    with timed_operation(
        logger,
        f"Lectura de Excel {config.excel_path}",
        category="DB",
    ):
        try:
            df = pd.read_excel(config.excel_path)
        except Exception as exc:
            logger.error(
                "Error al leer el Excel %s: %s",
                config.excel_path,
                exc,
                extra={"emoji": "❌", "category": "DB", "color": "RED"},
            )
            raise ConfigError("No se pudo leer el archivo de Excel") from exc

    columnas_obligatorias = {
        config.nombre_col,
        config.categoria_col,
        config.link_col,
    }

    faltantes = columnas_obligatorias.difference(df.columns)
    if faltantes:
        raise ConfigError(f"Faltan columnas obligatorias en el Excel: {', '.join(faltantes)}")

    return df


def seleccionar_carpeta_destino(
    categoria_valor: str,
    osde_path: Path,
    no_osde_path: Path,
) -> Path:
    """
    Selecciona la carpeta de destino según la categoría OSDE.

    Si la categoría contiene "OSDE" y no contiene "NO", se considera OSDE.
    En caso contrario, se usa la carpeta de NO OSDE.
    """
    categoria = str(categoria_valor).upper()
    if "OSDE" in categoria and "NO" not in categoria:
        return osde_path
    return no_osde_path


class PlanillaProcessor:
    """
    Orquesta la lectura del Excel y la descarga de planillas.

    Utiliza la configuración y un objeto descargador para ejecutar el flujo
    completo de negocio de forma controlada y testeable.
    """

    def __init__(self, config: DownloadConfig, downloader: Optional[GoogleDriveDownloader] = None) -> None:
        """
        Inicializa el procesador de planillas.

        Recibe:
        - config: parámetros de entrada/salida y nombres de columnas.
        - downloader: instancia encargada de hablar con Google Drive.
        """
        self._config = config
        self._downloader = downloader or GoogleDriveDownloader()

    def procesar(self) -> None:
        """
        Ejecuta el flujo completo de procesamiento de planillas.

        Pasos:
        1. Prepara las carpetas de salida.
        2. Carga el Excel de entrada.
        3. Recorre cada fila:
           - Extrae nombre, categoría y enlace.
           - Obtiene el ID de Google Drive.
           - Descarga el archivo en la carpeta correspondiente.
        4. Muestra un resumen de éxitos y fallos.
        """
        with timed_operation(
            logger,
            "Procesamiento completo de planillas",
            category="APP",
        ):
            # Crear (si es necesario) las carpetas donde se guardarán los archivos.
            osde_path, no_osde_path = preparar_carpetas(self._config)
            # Leer y validar el archivo Excel de entrada.
            df = cargar_excel(self._config)

            # Contadores para informar al usuario al final del proceso.
            total = len(df)
            exitos = 0
            fallos = 0

            # Barra de progreso visual para el procesamiento.
            bar = ProgressBar(total=total, prefix="Procesando planillas")

            # Iterar fila por fila sobre las planillas definidas en el Excel.
            for _, row in df.iterrows():
                nombre = row[self._config.nombre_col]
                categoria = row[self._config.categoria_col]
                link = row[self._config.link_col]

                # Intentar extraer el ID del enlace de Google Drive.
                file_id = extraer_id_drive(link)
                if not file_id:
                    mensaje = f"No se pudo leer el link de la planilla para: {nombre}"
                    logger.warning(
                        mensaje,
                        extra={"emoji": "⚠️", "category": "API", "color": "YELLOW"},
                    )
                    print(mensaje)
                    fallos += 1
                    bar.update()
                    continue

                # Determinar la carpeta de destino según la categoría.
                carpeta_destino = seleccionar_carpeta_destino(
                    categoria,
                    osde_path,
                    no_osde_path,
                )
                # Construir el nombre base del archivo de salida (sin extensión).
                destino_base = carpeta_destino / f"planilla de asistencia diciembre {nombre}"

                try:
                    archivo_final = self._downloader.descargar(file_id, destino_base)
                except DownloadError as exc:
                    mensaje = f"Error al descargar la planilla para {nombre}: {exc}"
                    logger.error(
                        mensaje,
                        extra={"emoji": "❌", "category": "API", "color": "RED"},
                    )
                    print(mensaje)
                    fallos += 1
                    bar.update()
                    continue

                print(f"✅ Guardado: {archivo_final}")
                logger.info(
                    "Operación de guardado exitosa",
                    extra={
                        "emoji": "✅",
                        "category": "APP",
                        "details": f"archivo={archivo_final}",
                        "color": "GREEN",
                    },
                )
                exitos += 1
                bar.update()

            bar.finish()

            resumen = (
                f"📊 Proceso terminado. Éxitos: {exitos}, Fallos: {fallos}, Total: {total}"
            )
            logger.info(
                resumen,
                extra={
                    "emoji": "📊",
                    "category": "APP",
                    "color": "BLUE",
                },
            )
            print(resumen)

