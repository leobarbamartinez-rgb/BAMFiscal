# 🚀 Guía Rápida para Google Cloud Shell

Sigue estos pasos para ejecutar tu **Fiscal Navigator** en la nube:

## 1. Preparar el entorno
Asegúrate de estar en la carpeta correcta:
```bash
ls
# Debes ver archivos como 'app_ui.py', 'requirements.txt', etc.
```

## 2. Instalar librerías
Si es la primera vez, instala las dependencias:
```bash
pip install -r requirements.txt
```

## 3. Ejecutar la App
Para asegurar que se vea desde fuera, usa esta configuración:
```bash
streamlit run app_ui.py --server.port 8080 --server.address 0.0.0.0 --server.enableCORS false
```

## 4. Visualizar
1. Busca el botón **"Vista previa en la web"** (icono de un ojo o cuadrado en la barra superior del terminal de Cloud Shell).
2. Selecciona **"Vista previa en el puerto 8080"** (Preview on port 8080).
3. ¡Listo! Se abrirá una nueva pestaña con tu aplicación operativa.
