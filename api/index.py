import sys
import os

# Añadir el directorio raíz al path para que las importaciones de src funcionen en Vercel
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel Serverless Function entrypoint
handler = app
