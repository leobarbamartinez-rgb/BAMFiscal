# 🌐 Cómo compartir tu aplicación de forma Segura y Temporal

Tienes dos opciones principales desde Google Cloud Shell:

## Opción A: Despliegue Rápido en Google Cloud Run (Recomendada)
Esta es la opción "nativa" de Google. Crea una URL pública segura (HTTPS) que funciona mientras tú quieras.

1.  **Ejecuta este comando en la terminal:**
    ```bash
    gcloud run deploy fiscal-navigator --source . --port 8080 --allow-unauthenticated --region europe-southwest1
    ```
    *(Si te pide activar APIs, di que sí 'y').*

2.  **Espera unos segundos.**
    Google creará un contenedor y te devolverá una URL terminada en `run.app`.

3.  **Comparte esa URL.**
    Es segura (HTTPS) y pública. Tu compañera podrá entrar desde su móvil u ordenador.

4.  **Para "apagarla" (Borrar):**
    Cuando terminéis, ejecuta:
    ```bash
    gcloud run services delete fiscal-navigator --region europe-southwest1
    ```

---

## Opción B: Túnel con Ngrok (Más "temporal")
Crea un túnel directo desde tu Cloud Shell a internet. Si cierras la terminal, se rompe el enlace.

1.  **Regístrate en ngrok.com** (Gratis) y consigue tu *Authtoken*.
2.  **Instala y configura:**
    ```bash
    pip install pyngrok
    ngrok config add-authtoken TU_TOKEN_AQUI
    ```
3.  **Lanza la app (en una terminal):**
    ```bash
    streamlit run app_ui.py --server.port 8080
    ```
4.  **Abre OTRA terminal (botón +) y lanza el túnel:**
    ```bash
    ngrok http 8080
    ```
    Copia el enlace `https://...ngrok-free.app` y envíaselo.

> **Nota de Seguridad:** Ambas opciones generan una URL pública. Si los datos que metes son confidenciales, ten cuidado. Cloud Run es más robusto; Ngrok es más efímero.
