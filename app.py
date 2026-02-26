import os
import shutil
import logging
import time
import tempfile
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from src.models.config import ConfigError, DownloadConfig
from src.core.processor import PlanillaProcessor
from src.utils.log_utils import setup_logging

# Cargar variables de entorno
load_dotenv()

# Configuración inicial
setup_logging(level_name="INFO")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Automate API",
    description="API para automatizar la descarga y organización de planillas desde Google Drive",
    version="1.0.0"
)

# Configurar CORS
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorios temporales para la API
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("planillas_organizadas")
ZIP_DIR = Path("exports")

# Asegurar que existan
for d in [UPLOAD_DIR, OUTPUT_DIR, ZIP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Estado global simple para seguimiento de tareas (en producción usar Redis o DB)
tasks_status = {}

class ProcessedItem(BaseModel):
    name: str
    status: str  # success, error
    category: Optional[str] = None  # OSDE o NO OSDE
    error_msg: Optional[str] = None

class TaskProgress(BaseModel):
    task_id: str
    status: str  # pending, running, completed, failed
    total: int = 0
    current: int = 0
    last_item: Optional[str] = None
    processed_items: List[ProcessedItem] = []
    errors: List[str] = []
    result: Optional[dict] = None
    zip_url: Optional[str] = None

def cleanup_old_files():
    """Limpia archivos ZIP y subidas de más de 2 horas."""
    now = time.time()
    for folder in [UPLOAD_DIR, ZIP_DIR]:
        for path in folder.glob("*"):
            if path.is_file() and now - path.stat().st_mtime > 7200:  # 2 horas
                try:
                    path.unlink()
                    logger.info(f"Archivo antiguo eliminado: {path.name}")
                except Exception as e:
                    logger.error(f"Error al eliminar {path.name}: {e}")

def run_processor_task(task_id: str, excel_path: Path, mes: str):
    """Tarea en segundo plano para procesar el Excel y generar el ZIP."""
    cleanup_old_files()  # Limpiar archivos viejos antes de empezar una nueva tarea
    tasks_status[task_id].status = "running"
    
    # Crear carpeta específica para esta tarea para evitar mezclar archivos si hay tareas simultáneas
    task_output_dir = OUTPUT_DIR / task_id
    task_output_dir.mkdir(exist_ok=True)
    
    def progress_callback(current, total, item_name, status, error_msg, category):
        tasks_status[task_id].current = current
        tasks_status[task_id].total = total
        tasks_status[task_id].last_item = item_name
        
        # Añadir a la lista detallada de items con su categoría detectada
        tasks_status[task_id].processed_items.append(
            ProcessedItem(name=item_name, status=status, category=category, error_msg=error_msg)
        )
        
        if status == "error" and error_msg:
            tasks_status[task_id].errors.append(f"{item_name}: {error_msg}")

    try:
        config = DownloadConfig(
            excel_path=excel_path,
            output_dir=task_output_dir,
            mes=mes
        )
        processor = PlanillaProcessor(config, progress_callback=progress_callback)
        result = processor.procesar()
        
        # Generar ZIP de la carpeta de salida específica de la tarea
        zip_filename = f"planillas_{task_id}"
        zip_path = shutil.make_archive(
            str(ZIP_DIR / zip_filename),
            'zip',
            root_dir=str(task_output_dir)
        )
        
        tasks_status[task_id].status = "completed"
        tasks_status[task_id].result = result
        tasks_status[task_id].zip_url = f"/download/{task_id}"
        logger.info(f"Tarea {task_id} completada exitosamente. ZIP generado en {zip_path}")
        
    except Exception as e:
        tasks_status[task_id].status = "failed"
        tasks_status[task_id].errors.append(f"Error crítico: {str(e)}")
        logger.error(f"Error en tarea {task_id}: {str(e)}")
    finally:
        # Limpiar archivo subido y carpeta temporal de salida después de comprimir
        if excel_path.exists():
            excel_path.unlink()
        if task_id in tasks_status and tasks_status[task_id].status == "completed":
            # Si se completó y comprimió, podemos borrar la carpeta de archivos sueltos
            shutil.rmtree(task_output_dir, ignore_errors=True)

@app.get("/")
async def root():
    return {"message": "Bienvenido a Automate API", "docs": "/docs"}

@app.post("/process/", response_model=TaskProgress)
async def create_upload_file(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    mes: str = Form("diciembre")
):
    """Sube un archivo Excel e inicia el procesamiento en segundo plano."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx o .xls)")

    task_id = os.urandom(8).hex()
    file_path = UPLOAD_DIR / f"{task_id}_{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    tasks_status[task_id] = TaskProgress(task_id=task_id, status="pending")
    background_tasks.add_task(run_processor_task, task_id, file_path, mes)
    
    return tasks_status[task_id]

@app.get("/status/{task_id}", response_model=TaskProgress)
async def get_task_status(task_id: str):
    """Consulta el estado de una tarea de procesamiento."""
    if task_id not in tasks_status:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return tasks_status[task_id]

@app.get("/download/{task_id}")
async def download_zip(task_id: str):
    """Descarga el archivo ZIP generado para una tarea."""
    zip_path = ZIP_DIR / f"planillas_{task_id}.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Archivo ZIP no encontrado o tarea aún en proceso")
    
    return FileResponse(
        path=zip_path,
        filename=f"planillas_{task_id}.zip",
        media_type="application/zip"
    )

@app.get("/tasks/", response_model=List[TaskProgress])
async def list_tasks():
    """Lista todas las tareas registradas."""
    return list(tasks_status.values())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
