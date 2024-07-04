# app/__init__.py

from sanic import Sanic
from sanic_ext import Extend
from .db import initialize_db
from .routes import ServiceRoutes
import os

app = Sanic("ServiceAPI")

# Настройка Sanic Extensions и OpenAPI с использованием Swagger UI
Extend(app, openapi_config={
    "title": "Service API",
    "version": "1.0.0",
    "description": "API для управления сервисами",
})

# Абсолютный путь к файлу config.py
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../config.py')
app.config.update_config(config_path)

initialize_db(app)

ServiceRoutes.register_routes(app, app.ctx.collection)
