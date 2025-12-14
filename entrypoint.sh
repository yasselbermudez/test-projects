#!/bin/bash

#El script entrypoint.sh expande la variable $PORT 
#correctamente antes de ejecutar uvicorn. 

# Si la variable PORT no está definida, usa 8000 por defecto
PORT=${PORT:-8000}

# Ejecuta uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT