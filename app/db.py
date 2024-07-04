from mongoengine import connect
import os

def init_db():
    db_name = os.getenv("DATABASE_NAME", "service_db")
    db_host = os.getenv("MONGODB_URL", "mongodb://localhost:27017/service_db")
    connect(db=db_name, host=db_host)
