"""
Script principal para descargar automáticamente planillas de asistencia desde
enlaces de Google Drive listados en un archivo Excel.

Este módulo solo contiene el punto de entrada y la configuración de logging.
La lógica de negocio está separada en:
- config.py          → configuración y tipos base
- drive_downloader.py → interacción con Google Drive
- processor.py       → procesamiento del Excel y descargas
"""

import argparse
import logging
import os
from pathlib import Path

from src.models.config import ConfigError, DownloadConfig
from src.utils.log_utils import clean_old_logs, setup_logging
from src.core.processor import PlanillaProcessor


# Logger de módulo para registrar información y errores de la aplicación.
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """
    Parsea los argumentos de línea de comandos.

    Opciones:
    - --log-level: nivel de logging (DEBUG, INFO, WARNING, ERROR).
    - --clean-logs: limpia los logs antiguos y termina.
    """
    parser = argparse.ArgumentParser(
        description="Descarga planillas de asistencia desde enlaces de Google Drive."
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        help="Nivel de logging (DEBUG, INFO, WARNING, ERROR)",
    )
    parser.add_argument(
        "--clean-logs",
        action="store_true",
        help="Elimina logs antiguos (mantiene los últimos 7 días) y termina.",
    )
    return parser.parse_args()


def buscar_archivo_excel() -> Path:
    """
    Busca automáticamente el primer archivo .xlsx en la raíz del proyecto.
    
    Excluye archivos temporales que empiezan con ~$ (propios de Excel abierto).
    """
    archivos_excel = [
        f for f in Path(".").glob("*.xlsx") 
        if not f.name.startswith("~$")
    ]
    
    if not archivos_excel:
        raise ConfigError("No se encontró ningún archivo Excel (.xlsx) en la raíz del proyecto.")
    
    # Si hay varios, tomamos el más reciente
    archivo_seleccionado = sorted(archivos_excel, key=lambda x: x.stat().st_mtime, reverse=True)[0]
    
    logger.info(
        f"🔍 Archivo Excel detectado automáticamente",
        extra={
            "emoji": "🔍",
            "category": "DB",
            "details": f"archivo={archivo_seleccionado.name}",
            "color": "BLUE",
        },
    )
    return archivo_seleccionado


def main() -> None:
    """
    Punto de entrada principal del script.

    Configura el logging, construye la configuración de descarga y lanza el
    procesamiento de planillas, gestionando errores de configuración y
    errores inesperados de forma controlada para el usuario.
    """
    args = parse_args()
    setup_logging(level_name=args.log_level)

    if args.clean_logs:
        # Comando especial para limpiar logs antiguos.
        clean_old_logs(logger=logger)
        return

    try:
        # Buscamos el Excel dinámicamente en lugar de usar uno fijo
        excel_path = buscar_archivo_excel()

        # Configuración dinámica:
        # - El Excel se busca automáticamente en la raíz.
        # - Los archivos descargados se almacenarán en "planillas_organizadas".
        config = DownloadConfig(
            excel_path=excel_path,
            output_dir=Path("planillas_organizadas"),
        )

        processor = PlanillaProcessor(config)
        processor.procesar()
    except ConfigError as exc:
        mensaje = f"Error de configuración: {exc}"
        logger.error(mensaje)
        print(mensaje)
    except Exception as exc:  # Protección final ante errores inesperados
        mensaje = f"Ocurrió un error inesperado: {exc}"
        logger.exception(mensaje)
        print(mensaje)


if __name__ == "__main__":
    main()
