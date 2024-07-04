from mongoengine import connect

def init_db(uri: str, db_name: str):
    connect(db_name, host=uri)
