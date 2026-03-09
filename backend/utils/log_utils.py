"""
Utilidades de logging enriquecido para la aplicación de planillas.

Características:
- Colores y emojis por nivel de severidad.
- Formato estructurado con timestamp de alta precisión.
- Salida a consola y archivo JSON diario.
- Medición de tiempos de operaciones.
- Barra de progreso con animación para procesos largos.
- Limpieza automática de logs antiguos.
"""

import json
import logging
import os
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from time import perf_counter
from typing import Generator, Optional


LOG_DIR = Path("logs")


# Códigos ANSI de color para la consola.
COLOR_CODES = {
    "RESET": "\033[0m",
    "GREEN": "\033[32m",
    "BLUE": "\033[34m",
    "YELLOW": "\033[33m",
    "RED": "\033[31m",
}


LEVEL_EMOJIS = {
    logging.DEBUG: "🔍",
    logging.INFO: "ℹ️",
    logging.WARNING: "⚠️",
    logging.ERROR: "❌",
    logging.CRITICAL: "❌",
}


class ColoredFormatter(logging.Formatter):
    """
    Formateador de logs para consola con colores, emojis y estructura fija.

    Formato:
    [TIMESTAMP] [EMOJI] [COLOR] [CATEGORIA] MENSAJE - DETALLES
    """

    def format(self, record: logging.LogRecord) -> str:
        # Timestamp con milisegundos.
        ts = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        timestamp = f"{ts}.{int(record.msecs):03d}"

        emoji = getattr(record, "emoji", None) or LEVEL_EMOJIS.get(record.levelno, "ℹ️")
        color_name = getattr(record, "color", None)

        if not color_name:
            if record.levelno >= logging.ERROR:
                color_name = "RED"
            elif record.levelno >= logging.WARNING:
                color_name = "YELLOW"
            else:
                color_name = "BLUE"

        color_code = COLOR_CODES.get(color_name, "")
        reset_code = COLOR_CODES["RESET"]

        category = getattr(record, "category", "")
        category_prefix = f"[{category}] " if category else ""

        message = record.getMessage()
        details = getattr(record, "details", "")
        details_suffix = f" - {details}" if details else ""

        base = f"[{timestamp}] [{emoji}] [{color_name}]{reset_code} {category_prefix}{message}{details_suffix}"
        return f"{color_code}{base}{reset_code}"


class JsonFormatter(logging.Formatter):
    """
    Formateador para archivo de log en formato JSON por línea.
    """

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        timestamp = f"{ts}.{int(record.msecs):03d}"

        payload = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "category": getattr(record, "category", None),
            "emoji": getattr(record, "emoji", None),
            "details": getattr(record, "details", None),
            "module": record.module,
            "funcName": record.funcName,
            "lineNo": record.lineno,
        }
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level_name: Optional[str] = None) -> None:
    """
    Configura el sistema de logging global.
    """
    # Detectar si estamos en Vercel para evitar escritura en disco
    is_vercel = os.getenv("VERCEL") == "1"

    if not is_vercel:
        LOG_DIR.mkdir(parents=True, exist_ok=True)

    selected_level = (level_name or "INFO").upper()
    level = getattr(logging, selected_level, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Eliminar handlers previos para evitar duplicados.
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # Consola con colores (Siempre habilitada).
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredFormatter())
    root_logger.addHandler(console_handler)

    # Archivo JSON rotado diariamente (Solo si NO estamos en Vercel).
    if not is_vercel:
        try:
            file_handler = TimedRotatingFileHandler(
                LOG_DIR / "app.log.jsonl",
                when="midnight",
                interval=1,
                backupCount=7,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(JsonFormatter())
            root_logger.addHandler(file_handler)
        except Exception:
            # Si falla la creación del archivo de log local, continuamos con consola
            pass


@contextmanager
def timed_operation(
    logger: logging.Logger,
    description: str,
    category: Optional[str] = None,
) -> Generator[None, None, None]:
    """
    Context manager para medir el tiempo de una operación importante.

    Al finalizar, registra un log con el tiempo empleado.
    """
    start = perf_counter()
    try:
        yield
    finally:
        elapsed = perf_counter() - start
        logger.info(
            f"⏱️ {description} completada",
            extra={
                "emoji": "⏱️",
                "category": category,
                "details": f"duración={elapsed:.3f}s",
                "color": "BLUE",
            },
        )


class ProgressBar:
    """
    Barra de progreso simple con animación para operaciones largas.

    Uso:
        bar = ProgressBar(total, prefix="🔄 Procesando")
        for item in items:
            ...
            bar.update()
        bar.finish()
    """

    def __init__(self, total: int, prefix: str = "", length: int = 30) -> None:
        self.total = max(total, 1)
        self.prefix = prefix
        self.length = length
        self.start_time = perf_counter()
        self.current = 0
        self._spinner_frames = ["🔄", "⏳", "🔄"]
        self._spinner_index = 0

    def _format_bar(self) -> str:
        progress = self.current / self.total
        filled_length = int(self.length * progress)
        bar = "█" * filled_length + "-" * (self.length - filled_length)

        elapsed = perf_counter() - self.start_time
        if self.current > 0:
            est_total = elapsed / progress
            remaining = max(est_total - elapsed, 0.0)
        else:
            remaining = 0.0

        spinner = self._spinner_frames[self._spinner_index]
        self._spinner_index = (self._spinner_index + 1) % len(self._spinner_frames)

        percent = progress * 100
        return (
            f"{spinner} {self.prefix} |{bar}| "
            f"{percent:6.2f}% "
            f"⏱️ restante ~ {remaining:5.1f}s"
        )

    def update(self, step: int = 1) -> None:
        """
        Incrementa el progreso y redibuja la barra en consola.
        """
        self.current = min(self.current + step, self.total)
        line = self._format_bar()
        sys.stdout.write("\r" + line)
        sys.stdout.flush()

    def finish(self) -> None:
        """
        Marca la barra como completada y deja la línea cerrada.
        """
        self.current = self.total
        line = self._format_bar()
        sys.stdout.write("\r" + line + "\n")
        sys.stdout.flush()


def clean_old_logs(days: int = 7, logger: Optional[logging.Logger] = None) -> None:
    """
    Elimina archivos de log con más de `days` días de antigüedad.

    Mantiene por defecto los últimos 7 días.
    """
    log = logger or logging.getLogger(__name__)
    if not LOG_DIR.exists():
        return

    cutoff = datetime.now() - timedelta(days=days)

    removed = 0
    for path in LOG_DIR.glob("*.log.jsonl"):
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
        except OSError:
            continue
        if mtime < cutoff:
            try:
                path.unlink()
                removed += 1
            except OSError:
                continue

    log.info(
        "📊 Limpieza de logs completada",
        extra={
            "emoji": "📊",
            "category": "LOG",
            "details": f"archivos_eliminados={removed}, dias_retenidos={days}",
            "color": "GREEN",
        },
    )

