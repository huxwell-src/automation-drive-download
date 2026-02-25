from app import app

# Este archivo es el punto de entrada para Vercel Serverless Functions
# Vercel buscará una variable llamada 'app' o 'handler'
handler = app
