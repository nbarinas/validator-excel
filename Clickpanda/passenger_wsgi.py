import os
import sys

# Asegurar que el proyecto está en el path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from asgiref.wsgi import WsgiToAsgi
from backend.main import app

asgi_app = WsgiToAsgi(app)
application = asgi_app
