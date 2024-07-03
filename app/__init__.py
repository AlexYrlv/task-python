# # app/__init__.py
# from loguru import logger
# from sanic import Sanic
# from motor.motor_asyncio import AsyncIOMotorClient
# from .exceptions import NotFound, ServerError, bad_request
# import os
# from sanic_ext import Extend
#
# app = Sanic("ServiceAPI")
#
# config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../config.py')
# app.config.update_config(config_path)
#
# logger.info("Connecting to MongoDB at {}", app.config.MONGODB_URL)
#
# client = AsyncIOMotorClient(app.config.MONGODB_URL, serverSelectionTimeoutMS=50000, socketTimeoutMS=50000)
# database = client[app.config.DATABASE_NAME]
# collection = database[app.config.COLLECTION_NAME]
#
# logger.info("Successfully connected to MongoDB")
#
# app.error_handler.add(NotFound, bad_request)
# app.error_handler.add(ServerError, bad_request)
#
# Extend(app)
#
# app.config.API_VERSION = '1.0.0'
# app.config.API_TITLE = 'Service API'
# app.config.API_DESCRIPTION = 'API for managing services'
#
#
# from . import routes
#
from sanic import Sanic
from motor.motor_asyncio import AsyncIOMotorClient
from .exceptions import NotFound, ServerError, bad_request
import os
from sanic_ext import Extend

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

client = AsyncIOMotorClient(app.config.MONGODB_URL, serverSelectionTimeoutMS=50000, socketTimeoutMS=50000)
database = client[app.config.DATABASE_NAME]
collection = database[app.config.COLLECTION_NAME]

app.error_handler.add(NotFound, bad_request)
app.error_handler.add(ServerError, bad_request)

from . import routes
