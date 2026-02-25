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
from pathlib import Path

from config import ConfigError, DownloadConfig
from log_utils import clean_old_logs, setup_logging
from processor import PlanillaProcessor


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

    # Configuración por defecto para el proceso principal:
    # - El Excel "planilas.xlsx" debe estar junto a este script.
    # - Los archivos descargados se almacenarán en "planillas_organizadas".
    config = DownloadConfig(
        excel_path=Path("planilas.xlsx"),
        output_dir=Path("planillas_organizadas"),
    )

    try:
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
