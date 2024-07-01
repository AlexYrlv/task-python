from sanic import Sanic
from motor.motor_asyncio import AsyncIOMotorClient
from .exceptions import NotFound, ServerError, bad_request
from loguru import logger
import os
from sanic_ext import Extend

app = Sanic("ServiceAPI")


# Абсолютный путь к файлу config.py
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../config.py')
app.config.update_config(config_path)

client = AsyncIOMotorClient(app.config.MONGODB_URL)
database = client[app.config.DATABASE_NAME]
collection = database[app.config.COLLECTION_NAME]

app.error_handler.add(NotFound, bad_request)
app.error_handler.add(ServerError, bad_request)

# Добавление Sanic Extensions
Extend(app)

app.config.API_VERSION = '1.0.0'
app.config.API_TITLE = 'Service API'
app.config.API_DESCRIPTION = 'API for managing services'
app.config.API_TERMS_OF_SERVICE = 'https://your-terms-of-service.url'
app.config.API_CONTACT_EMAIL = 'your-email@example.com'

from . import routes


# инициализирует приложение Sanic, подключает базу данных MongoDB

