# 🚀 Despliegue en GitHub y Streamlit Community Cloud

Para compartir tu proyecto con el mundo de forma permanente, vamos a usar dos herramientas gratuitas y estándar: **GitHub** (para guardar el código) y **Streamlit Cloud** (para ejecutar la app).

## Paso 1: Subir a GitHub

Como estoy trabajando en tu máquina local (virtual), ya he inicializado el repositorio Git por ti. Solo necesitas "empujarlo" a tu cuenta.

1.  **Crea un repositorio en GitHub:**
    *   Entra en [github.com/new](https://github.com/new)
    *   Nombre: `fiscal-navigator-spain` (o lo que quieras).
    *   Público.
    *   **NO** marques "Add a README", ni .gitignore, ni license (ya los tenemos).
    *   Dale a "Create repository".

2.  **Sube tu código:**
    En la página siguiente te saldrán comandos. Copia y pega estos comandos en tu terminal de Cloud Shell (uno a uno):

    ```bash
    git remote add origin https://github.com/TU_USUARIO/fiscal-navigator-spain.git
    git branch -M main
    git push -u origin main
    ```
    *(Te pedirá tu usuario y un "Personal Access Token" como contraseña. Si no tienes token, es más fácil usar la opción de "GitHub Desktop" o autenticarte vía web si Cloud Shell te lo permite, pero el token es lo estándar en terminal).*

---

### Opción Alternativa: Subida Manual (Sin Comandos)

Si prefieres hacerlo "visual" desde la web:

1.  **Descarga el código:**
    *   En tu explorador de archivos (izquierda), busca `fiscal_project_v4_full.zip`.
    *   Haz click derecho -> "Download".
    *   Descomprímelo en tu ordenador.

2.  **Sube a GitHub:**
    *   Crea el repositorio en GitHub (Paso 1 anterior).
    *   En la pantalla principal del repo vacío, pulsa el enlace **"uploading an existing file"**.
    *   Arrastra todos tus archivos descomprimidos ahí.
    *   Dale al botón verde "Commit changes".

---

## Paso 2: Conectar con Streamlit Cloud

1.  Ve a [share.streamlit.io](https://share.streamlit.io/).
2.  Haz login con tu cuenta de GitHub.
3.  Dale a **"New app"**.
4.  Selecciona "Use existing repo".
5.  Elige tu repositorio: `TU_USUARIO/fiscal-navigator-spain`.
6.  Branch: `main`.
7.  Main file path: `app_ui.py`.
8.  Dale a **"Deploy!"**.

## 💡 ¡Listo!
En unos minutos tendrás una URL tipo `https://fiscal-navigator-spain.streamlit.app` que funcionará para siempre (mientras no la borres) y se actualizará automáticamente cada vez que hagas cambios en el código y hagas `git push`.
