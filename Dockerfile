# 1. Usar la imagen oficial de Playwright con Python
# Esta imagen ya incluye Python, Playwright, y todos los navegadores
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# 2. Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Copiar tu script de Python al contenedor
COPY reina.py .

# 4. (Opcional) Si tuvieras MÁS librerías, las instalarías aquí
# COPY requirements.txt .
# RUN pip install -r requirements.txt

# 5. Comando que se ejecutará cuando el contenedor inicie
# Esto es lo mismo que escribir "python reina.py" en tu terminal
CMD ["python", "reina.py"]