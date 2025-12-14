FROM python:3.13-slim

# 1. Instala los certificados CA del sistema y las herramientas de compilación
RUN apt-get update && apt-get install -y \
    ca-certificates \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 2. Establece el directorio de trabajo
WORKDIR /app

# 3. Copia el archivo de dependencias
COPY requirements.txt .

# 4. Instala las dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copia el resto del código de la aplicación
COPY . .

# 6. Comando para ejecutar la aplicación

# 6.1-Copia el script de entrada
COPY entrypoint.sh /entrypoint.sh 

# 6.2-Hazlo ejecutable
RUN chmod +x /entrypoint.sh

# 6.3-Usa ENTRYPOINT para ejecutarlo
ENTRYPOINT ["/entrypoint.sh"]

