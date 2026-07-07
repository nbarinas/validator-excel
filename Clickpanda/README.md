# Despliegue en ClickPanda

Esta carpeta contiene una copia del proyecto configurada para desplegar en ClickPanda usando Phusion Passenger.

## Requisitos en ClickPanda

- Plan con Application Manager / Passenger habilitado
- Python 3.x disponible
- MySQL activo con la base de datos `zoidusho_az_db`

## Pasos de despliegue

1. Subir esta carpeta `Clickpanda` completa al hosting, por ejemplo a:
   ```
   /home/zoidusho/az-marketing/
   ```

2. Entrar vía SSH o terminal al hosting:
   ```bash
   cd /home/zoidusho/az-marketing
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Asegurarse de que los archivos `passenger_wsgi.py` y `.htaccess` estén en la raíz de la carpeta de la aplicación:
   ```
   /home/zoidusho/az-marketing/passenger_wsgi.py
   /home/zoidusho/az-marketing/.htaccess
   ```

4. Configurar variables de entorno en cPanel → Application Manager:
   - `DATABASE_URL`: `mysql+pymysql://zoidusho_az_user:AzMarketing2025*@localhost/zoidusho_az_db`
   - `SECRET_KEY`: tu clave secreta

5. Registrar la aplicación en cPanel → Application Manager:
   - Application Name: `az-marketing`
   - Deployment Domain: `az-marketing.com.co`
   - Application Path: `az-marketing`
   - Environment: `Production`
   - Click en **Deploy**

6. Abrir en navegador:
   ```
   https://az-marketing.com.co
   ```

## Notas

- `backend/database.py` en esta carpeta está configurado para usar `localhost` por defecto si no se define `DATABASE_URL`, ya que la app y la BD están en el mismo servidor.
- Si necesitas volver a Render, usa la carpeta raíz del repo (`backend/`, `frontend/`) en lugar de esta carpeta.
