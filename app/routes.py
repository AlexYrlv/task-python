from sanic import response
from sanic.request import Request
from bson import ObjectId
from pydantic import ValidationError
from datetime import datetime, timedelta
from . import app, collection
from .models import Service
from .serializers import ServiceSerializer
from .exceptions import NotFound, ServerError
from loguru import logger
from sanic_ext import openapi

@app.post("/service")
@openapi.summary("Add a new service")
@openapi.description("Add a new service with name, state, and description")
@openapi.body({"application/json": ServiceSerializer.schema()})
@openapi.response(201, {"application/json": ServiceSerializer.schema()})
async def add_service(request: Request):
    try:
        data = request.json
        logger.info(f"Received data: {data}")
        # Завершить предыдущую запись для этого сервиса, если она существует
        update_result = await collection.update_many(
            {"name": data["name"], "timestamp_end": None},
            {"$set": {"timestamp_end": datetime.utcnow()}}
        )
        logger.info(f"Updated previous records: {update_result.modified_count}")
        service = Service(**data)
        result = await collection.insert_one(service.dict(exclude={"id"}))
        logger.info(f"Inserted new service with id: {result.inserted_id}")
        service.id = str(result.inserted_id)
        service_serialized = ServiceSerializer(**service.dict())
        return response.json(service_serialized.dict(), status=201)
    except ValidationError as e:
        logger.error(f"Validation error: {e.errors()}")
        return response.json(e.errors(), status=400)
    except Exception as e:
        logger.exception("Failed to add service")
        raise ServerError("Failed to add service")

@app.get("/services")
@openapi.summary("Get all services")
@openapi.description("Retrieve a list of all services")
@openapi.response(200, {"application/json": {"services": list}})
async def get_services(request: Request):
    services = []
    try:
        async for service in collection.find():
            service["_id"] = str(service["_id"])
            service_obj = Service(**service)
            service_serialized = ServiceSerializer(**service_obj.dict())
            services.append(service_serialized.dict())
        return response.json({"services": services})
    except Exception:
        logger.exception("Failed to fetch services")
        raise ServerError("Failed to fetch services")

@app.get("/service/<name>")
@openapi.summary("Get service history")
@openapi.description("Get the history of a specific service by name")
@openapi.response(200, {"application/json": {"history": list}})
async def get_service_history(request: Request, name: str):
    services = []
    try:
        async for service in collection.find({"name": name}):
            service["_id"] = str(service["_id"])
            service_obj = Service(**service)
            service_serialized = ServiceSerializer(**service_obj.dict())
            services.append(service_serialized.dict())
        if not services:
            raise NotFound(f"No service found with name {name}")
        return response.json({"history": services})
    except NotFound as e:
        raise e
    except Exception:
        logger.exception(f"Failed to fetch service history for {name}")
        raise ServerError("Failed to fetch service history for {name}")

@app.get("/sla/<name>")
@openapi.summary("Get SLA for a service")
@openapi.description("Calculate the SLA for a service over a given interval")
@openapi.parameter("interval", str, location="query", required=True, description="Time interval (e.g., '24h' or '7d')")
@openapi.response(200, {"application/json": {"sla": float}})
async def get_service_sla(request: Request, name: str):
    interval = request.args.get("interval")  # Получаем интервал из запроса
    try:
        # Вычисление интервала в секундах
        if interval.endswith("h"):
            interval_seconds = int(interval[:-1]) * 3600
        elif interval.endswith("d"):
            interval_seconds = int(interval[:-1]) * 86400
        else:
            return response.json({"error": 'Invalid interval format. Use "h" for hours or "d" for days.'}, status=400)

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(seconds=interval_seconds)

        total_time = interval_seconds
        downtime = 0

        async for service in collection.find({"name": name, "timestamp": {"$gte": start_time}}):
            service_end_time = service.get("timestamp_end", end_time)
            if service["state"] != "работает":
                downtime += (service_end_time - service["timestamp"]).total_seconds()

        uptime = total_time - downtime
        sla = (uptime / total_time) * 100

        return response.json({"sla": round(sla, 3)})
    except Exception:
        logger.exception(f"Failed to calculate SLA for {name}")
        raise ServerError("Failed to calculate SLA for {name}")


# Этот файл содержит маршруты API, которые обрабатывают HTTP-запросы.
# Каждый маршрут представляет собой асинхронную функцию, которая принимает запрос, обрабатывает его и возвращает ответ.