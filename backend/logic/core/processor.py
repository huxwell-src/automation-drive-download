"""
Lógica de alto nivel para procesar el Excel y descargar planillas.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

from logic.models.config import ConfigError, DownloadConfig
from logic.services.drive_downloader import (
    DownloadError,
    GoogleDriveDownloader,
    extraer_id_drive,
)
from logic.utils.log_utils import ProgressBar, timed_operation


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

    def __init__(self, config: DownloadConfig, downloader: Optional[GoogleDriveDownloader] = None, progress_callback: Optional[callable] = None) -> None:
        """
        Inicializa el procesador de planillas.

        Recibe:
        - config: parámetros de entrada/salida y nombres de columnas.
        - downloader: instancia encargada de hablar con Google Drive.
        - progress_callback: función opcional para reportar el progreso (útil para APIs).
          Firma: callback(current, total, item_name, status, error_msg, category_detected)
        """
        self._config = config
        self._downloader = downloader or GoogleDriveDownloader()
        self._progress_callback = progress_callback

    def procesar(self) -> dict:
        """
        Ejecuta el flujo completo de procesamiento de planillas.

        Retorna un diccionario con el resumen de la operación.
        """
        with timed_operation(
            logger,
            "Procesamiento completo de planillas",
            category="APP",
        ):
            osde_path, no_osde_path = preparar_carpetas(self._config)
            df = cargar_excel(self._config)

            total = len(df)
            exitos = 0
            fallos = 0
            detalles = []

            # Solo mostramos barra si no hay callback (CLI)
            bar = None
            if not self._progress_callback:
                bar = ProgressBar(total=total, prefix="Procesando planillas")

            for i, row in df.iterrows():
                nombre = row[self._config.nombre_col]
                categoria_valor = row[self._config.categoria_col]
                link = row[self._config.link_col]

                status = "success"
                error_msg = None
                
                # Determinar categoría para reporte
                carpeta_destino = seleccionar_carpeta_destino(categoria_valor, osde_path, no_osde_path)
                category_label = "OSDE" if carpeta_destino == osde_path else "NO OSDE"

                file_id = extraer_id_drive(link)
                if not file_id:
                    error_msg = f"No se pudo leer el link de la planilla para: {nombre}"
                    logger.warning(error_msg, extra={"emoji": "⚠️", "category": "API", "color": "YELLOW"})
                    status = "error"
                    fallos += 1
                else:
                    destino_base = carpeta_destino / f"planilla de asistencia {self._config.mes} {nombre}"

                    try:
                        archivo_final = self._downloader.descargar(file_id, destino_base)
                        logger.info("Operación de guardado exitosa", extra={"emoji": "✅", "category": "APP", "details": f"archivo={archivo_final}", "color": "GREEN"})
                        exitos += 1
                    except DownloadError as exc:
                        error_msg = str(exc)
                        logger.error(f"Error al descargar la planilla para {nombre}: {exc}", extra={"emoji": "❌", "category": "API", "color": "RED"})
                        status = "error"
                        fallos += 1

                # Reportar progreso si hay callback
                if self._progress_callback:
                    self._progress_callback(i + 1, total, nombre, status, error_msg, category_label)
                
                if bar:
                    bar.update()

            if bar:
                bar.finish()

            resumen_str = f"📊 Proceso terminado. Éxitos: {exitos}, Fallos: {fallos}, Total: {total}"
            logger.info(resumen_str, extra={"emoji": "📊", "category": "APP", "color": "BLUE"})
            
            return {
                "total": total,
                "exitos": exitos,
                "fallos": fallos,
                "resumen": resumen_str
            }

