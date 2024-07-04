from motor.motor_asyncio import AsyncIOMotorClient

def initialize_db(app):
    client = AsyncIOMotorClient(app.config.MONGODB_URL, serverSelectionTimeoutMS=50000, socketTimeoutMS=50000)
    app.ctx.db = client[app.config.DATABASE_NAME]
    app.ctx.collection = app.ctx.db[app.config.COLLECTION_NAME]
