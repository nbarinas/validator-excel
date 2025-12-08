# Excel Validator Pro

Una herramienta web para validar y cruzar archivos de Excel (R1 vs RF) automáticamente.

## Requisitos
*   Python 3.9+
*   Dependencias: `fastapi`, `uvicorn`, `pandas`, `openpyxl`, `python-multipart`

## Instalación Local

1.  Clona el repositorio.
2.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
3.  Ejecuta el servidor:
    ```bash
    uvicorn backend.main:app --reload
    ```
4.  Abre el navegador en `http://localhost:8000`.

## Despliegue en Internet (GitHub + Render)

GitHub Pages **no** sirve para esta aplicación porque requiere un servidor Python para procesar los Excel. 
La forma más fácil y gratuita es usar **Render**.

### Pasos:

1.  **Sube este código a GitHub**:
    *   Crea un repositorio en GitHub.com.
    *   Sube todos los archivos (asegúrate de incluir `requirements.txt` y `backend/`).

2.  **Crea una cuenta en Render.com** (puedes entrar con tu cuenta de GitHub).

3.  **Nuevo Web Service**:
    *   En Render, haz clic en "New +" -> "Web Service".
    *   Conecta tu repositorio de GitHub.
    
4.  **Configuración en Render**:
    *   **Name**: (El que quieras, ej: `validator-excel`)
    *   **Runtime**: Python 3
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
    
5.  ¡Listo! Render te dará una URL (ej: `https://validator-excel.onrender.com`) que podrás compartir y usar desde cualquier lugar.
