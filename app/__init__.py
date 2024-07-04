from sanic import Sanic
from sanic_ext import Extend
from .db import init_db

app = Sanic("ServiceAPI")

# Настройка Sanic Extensions и OpenAPI с использованием Swagger UI
Extend(app, openapi_config={
    "title": "Service API",
    "version": "1.0.0",
    "description": "API для управления сервисами",
})

init_db()

from .routes import ServiceRoutes

ServiceRoutes.register_routes(app)
