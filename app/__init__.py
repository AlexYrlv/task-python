from sanic import Sanic
from sanic_ext import Extend
import os
from app.routes import ServiceRoutes
from app.db import init_db


app = Sanic("ServiceAPI")

Extend(app, openapi_config={
    "title": "Service API",
    "version": "1.0.0",
    "description": "API для управления сервисами",
})

# Абсолютный путь к файлу config.py
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../config.py')
app.config.update_config(config_path)

# Инициализация базы данных
init_db(app.config.MONGODB_URL, app.config.DATABASE_NAME)

# Регистрация маршрутов
ServiceRoutes.register_routes(app)


