import sys
import os

# Añadir el directorio raíz y el directorio de backend al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from backend.app import app

# Vercel Serverless Function entrypoint
handler = app
