import os

MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://mongo:27017')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'service_db')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'services')

# Файл конфигурации для хранения настроек приложения, таких как URL базы данных.