from mongoengine import ValidationError
from sanic import Blueprint, response
from sanic.request import Request
from .exceptions import NotFound, ServerError
from sanic_ext import openapi
from typing import Optional
from .models import Service
from .loggers import logging

logger = logging.getLogger(__name__)

bp = Blueprint("service_routes")


class ServiceRoutes:

    @bp.post("/service")
    @openapi.summary("Add new service")
    @openapi.description("Add new service with name, state, and description")
    @openapi.body({"application/json": {"name": str, "state": str, "description": Optional[str]}})
    @openapi.response(201, {"application/json": {"name": str, "state": str, "description": Optional[str]}})
    async def add_service(request: Request):
        try:
            data = request.json
            logger.info(f"Received data: {data}")
            service = Service.create_or_update(data)
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return response.json({"error": "Validation error", "details": e.message}, status=400)
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return response.json({"error": str(e)}, status=400)
        except Exception as e:
            logger.exception("Failed to add or update service")
            raise ServerError("Failed to add or update service")

        return response.json(service.to_dict(), status=201)

    @bp.put("/service/<name>")
    @openapi.summary("Update service state")
    @openapi.description("Update the state existing service")
    @openapi.body({"application/json": {"state": str}})
    @openapi.response(200, {"application/json": {"name": str, "state": str, "description": Optional[str]}})
    async def update_service(request: Request, name: str):
        try:
            data = request.json
            data["name"] = name
            logger.info(f"Received data for update: {data}")
            service = Service.create_or_update(data)
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return response.json({"error": str(e)}, status=400)
        except NotFound as e:
            logger.error(f"Service not found: {name}")
            return response.json({"error": str(e)}, status=404)
        except Exception as e:
            logger.exception("Failed to update service")
            raise ServerError("Failed to update service")

        return response.json(service.to_dict(), status=200)

    @bp.get("/service/<name>")
    @openapi.summary("Get service history")
    @openapi.description("History service by name")
    @openapi.response(200, {"application/json": {"history": list}})
    async def get_service_history(request: Request, name: str):
        try:
            services = Service.get_history(name)
        except NotFound as e:
            logger.error(f"Service not found: {name}")
            return response.json({"error": str(e)}, status=404)
        except Exception as e:
            logger.exception(f"Failed to fetch service history for {name}")
            raise ServerError("Failed to fetch service history for {name}")

        return response.json({"history": [service.to_dict() for service in services]})

    @bp.get("/services")
    @openapi.summary("Get all services")
    @openapi.description("List all services")
    @openapi.response(200, {"application/json": {"services": list}})
    async def get_services(request: Request):
        try:
            services = Service.get_all()
        except Exception:
            logger.exception("Failed to fetch services")
            raise ServerError("Failed to fetch services")

        return response.json({"services": [service.to_dict() for service in services]})

    @bp.get("/sla/<name>")
    @openapi.summary("Get SLA for a service")
    @openapi.description("Calculate the SLA")
    @openapi.parameter("interval", str, location="query", required=True,
                       description="Time interval (e.g., '24h' or '7d')")
    @openapi.response(200, {"application/json": {"sla": float, "downtime": float}})
    async def get_service_sla(request: Request, name: str):
        interval = request.args.get("interval")
        try:
            result = Service.calculate_sla(name, interval)
        except Exception as e:
            logger.exception(f"Failed to calculate SLA for {name}")
            raise ServerError(f"Failed to calculate SLA for {name}")

        return response.json(result)

    @staticmethod
    def register_routes(app):
        app.blueprint(bp)
