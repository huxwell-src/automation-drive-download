# Automate - Descarga de Planillas

Script automatizado para descargar planillas de asistencia desde Google Drive basándose en un archivo Excel, organizarlas por categorías y convertirlas automáticamente a formato PDF.

## 🚀 Características

- **Organización Automática**: Clasifica las planillas en carpetas separadas (ej. OSDE y No OSDE).
- **Conversión a PDF**: Convierte imágenes (JPG, PNG) a PDF automáticamente al descargar.
- **Logging Visual**: Feedback en tiempo real con colores, emojis y barras de progreso.
- **Robustez**: Manejo de errores detallado y reintentos para archivos grandes de Drive.
- **Modularidad**: Código siguiendo principios SOLID y separado en módulos mantenibles.

## 📋 Requisitos Previos

- Python 3.8+
- Un archivo Excel llamado `planilas.xlsx` en la raíz del proyecto con las siguientes columnas:
  - `NOMBRE Y APELLIDO`: Nombre de la persona.
  - `osde - no osde`: Categoría para organizar (contiene "OSDE" o no).
  - `planilla`: Enlace de Google Drive.

## 🛠️ Instalación

1. Clona el repositorio o descarga los archivos.
2. Crea un entorno virtual (recomendado):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Linux/Mac
   .\.venv\Scripts\activate   # En Windows
   ```
3. Instala las dependencias necesarias:
   ```bash
   pip install pandas requests Pillow openpyxl
   ```

## 💻 Uso

Para iniciar el proceso de descarga:
```bash
python main.py
```

### Opciones de Logging
Puedes configurar el nivel de detalle de los logs:
```bash
python main.py --log-level DEBUG
```

### Limpieza de Logs
Para eliminar archivos de log antiguos (mayores a 7 días):
```bash
python main.py --clean-logs
```

## 📂 Estructura del Proyecto

El proyecto está organizado en carpetas para una mejor mantenibilidad y separación de responsabilidades:

- `main.py`: Punto de entrada y configuración inicial.
- `src/`:
  - `core/`: Lógica principal del negocio (`processor.py`).
  - `services/`: Servicios externos como Google Drive (`drive_downloader.py`).
  - `models/`: Definiciones de datos y configuraciones (`config.py`).
  - `utils/`: Utilidades transversales como el sistema de logging (`log_utils.py`).
- `logs/`: Directorio donde se guardan los logs diarios en formato JSON.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.
