# Automate - Drive Batch Processor 🚀

Automate es una herramienta diseñada para descargar, organizar y convertir planillas de asistencia desde Google Drive de forma masiva, utilizando un archivo Excel como fuente de datos.

---

## 🏁 Guía de Inicio Rápido (Getting Started)

Si acabas de descargar el código, sigue estos pasos para ponerlo en marcha sin complicaciones:

### 1. Requisitos Previos
Asegúrate de tener instalado en tu PC:
- **Python 3.10+**
- **Node.js (LTS)**

### 2. Preparación del Excel
Asegúrate de tener un archivo llamado `planilas.xlsx` en la carpeta raíz con las siguientes columnas exactas:
- `NOMBRE Y APELLIDO`: El nombre de la persona.
- `osde - no osde`: La categoría (si contiene "OSDE" se guardará en esa carpeta).
- `planilla`: El enlace directo de Google Drive.
> **Importante:** Los archivos en Drive deben tener el acceso configurado como "Cualquier persona con el enlace".

### 3. Ejecución (El modo fácil)
No necesitas abrir terminales. Simplemente busca el archivo:
👉 **`Instalar_y_Lanzar.vbs`**

Al ejecutarlo por primera vez:
1. Creará un **acceso directo en tu Escritorio** llamado "Automate".
2. Verás una ventana de carga minimalista mientras se instalan las dependencias (Python y Node).
3. Una vez listo, se abrirá automáticamente la aplicación en tu navegador ([http://localhost:4321](http://localhost:4321)).

---

## 🛠️ Características Principales

- **Organización Automática:** Clasifica archivos en carpetas (OSDE / NO OSDE) según el Excel.
- **Conversión a PDF:** Si descargas imágenes (JPG/PNG), se convierten a PDF automáticamente.
- **Mes Opcional:** Puedes elegir si el nombre del archivo descargado debe incluir el mes o no mediante un interruptor en la web.
- **Interfaz Moderna:** UI limpia basada en los principios de diseño de Apple.
- **Ejecución Silenciosa:** Los servidores corren en segundo plano sin ventanas de terminal molestas.

---

## 📂 Estructura del Proyecto

- `backend/`: API construida con FastAPI y lógica de procesamiento.
- `frontend/`: Interfaz web construida con Astro y React.
- `planilas.xlsx`: Archivo Excel de ejemplo/datos.
- `start.bat`: Script maestro de configuración y arranque.
- `Instalar_y_Lanzar.vbs`: Lanzador visual para el usuario final.

---

## 🚀 Versión 2 (Solo Next.js)

Existe una versión experimental en la carpeta `v2/` construida íntegramente con Next.js (sin necesidad de un backend en Python por separado). 

Para probarla:
1. `cd v2`
2. `npm install`
3. `npm run dev`

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.
