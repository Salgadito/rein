# 1. Usar la imagen oficial de Playwright con Python
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# 2. Establecer el directorio de trabajo
WORKDIR /app

# 3. --- LÍNEAS NUEVAS ---
# Instalar la librería de Python y el navegador
RUN pip install playwright
RUN playwright install chromium

# 4. Copiar tu script
COPY reina.py .

# 5. Comando que se ejecutará al iniciar
CMD ["python", "reina.py"]
