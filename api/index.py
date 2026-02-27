import sys
import os
from pathlib import Path

# Determinar la raíz del proyecto de forma absoluta
BASE_DIR = Path(__file__).parent.parent.absolute()
BACKEND_DIR = BASE_DIR / "backend"

# Añadir 'backend' al principio del path para que las importaciones de app.py funcionen
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Importar la instancia de FastAPI
try:
    from app import app
except ImportError as e:
    # Intento alternativo
    sys.path.append(str(BASE_DIR))
    from backend.app import app

# Vercel espera una variable llamada 'app'
app = app
