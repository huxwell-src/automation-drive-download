"""
Configuración y tipos base para el procesamiento de planillas.
"""

from dataclasses import dataclass
from pathlib import Path


class ConfigError(Exception):
    """
    Error relacionado con la configuración de entrada o rutas.

    Se utiliza cuando faltan archivos, carpetas o columnas necesarias en
    el archivo Excel.
    """


@dataclass
class DownloadConfig:
    """
    Configuración principal de la descarga de planillas.

    Define las rutas de entrada/salida y los nombres de columnas que se
    esperan en el archivo Excel.
    """

    excel_path: Path
    output_dir: Path
    osde_subdir: str = "OSDE"
    non_osde_subdir: str = "NO es osde"
    nombre_col: str = "NOMBRE Y APELLIDO"
    categoria_col: str = "osde - no osde"
    link_col: str = "planilla"

