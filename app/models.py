from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId

from app import NotFound, ServerError


class Service:
    def __init__(self, name: str, state: str, id: Optional[str] = None, description: Optional[str] = None,
                 timestamp: Optional[datetime] = None,
                 timestamp_end: Optional[datetime] = None):
        self.id = id or str(ObjectId())
        self.name = name
        self.state = self.validate_state(state)
        self.description = description
        self.timestamp = timestamp or datetime.utcnow()
        self.timestamp_end = timestamp_end

    @staticmethod
    def validate_state(state: str) -> str:
        valid_states = ["работает", "не работает"]
        if state not in valid_states:
            raise ValueError(f"Invalid state: {state}. State must be one of {valid_states}")
        return state

    def to_dict(self) -> dict:
        return {
            "_id": self.id,
            "name": self.name,
            "state": self.state,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "timestamp_end": self.timestamp_end.isoformat() if self.timestamp_end else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Service":
        return cls(
            id=str(data.get("_id")),
            name=data["name"],
            state=data["state"],
            description=data.get("description"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if isinstance(data["timestamp"], str) else data[
                "timestamp"],
            timestamp_end=datetime.fromisoformat(data["timestamp_end"]) if data.get("timestamp_end") and isinstance(
                data["timestamp_end"], str) else data["timestamp_end"]
        )

    @classmethod
    async def get_all(cls, collection: AsyncIOMotorCollection) -> List["Service"]:
        services = []
        async for document in collection.find():
            services.append(cls.from_dict(document))
        return services

    @classmethod
    async def create_or_update(cls, collection: AsyncIOMotorCollection, data: Dict[str, Any]) -> "Service":
        name = data.get("name")
        new_state = data.get("state")
        if not name:
            raise ValueError("Name is required")
        if not new_state:
            raise ValueError("State is required")

        await cls.update_end_timestamp(collection, name)

        existing_service = await collection.find_one({"name": name, "timestamp_end": None})
        if existing_service:
            if existing_service["state"] == new_state:
                raise ValueError(f"Service {name} is already in state {new_state}")

            await collection.update_one(
                {"_id": existing_service["_id"]},
                {"$set": {"timestamp_end": datetime.utcnow()}}
            )

            service = cls(name=name, state=new_state, description=data.get("description"))
            result = await collection.insert_one(service.to_dict())
            service.id = str(result.inserted_id)
            return service
        else:
            service = cls(**data)
            result = await collection.insert_one(service.to_dict())
            service.id = str(result.inserted_id)
            return service

    @classmethod
    async def update_end_timestamp(cls, collection: AsyncIOMotorCollection, name: str) -> int:
        result = await collection.update_many(
            {"name": name, "timestamp_end": None},
            {"$set": {"timestamp_end": datetime.utcnow()}}
        )
        return result.modified_count

    @classmethod
    async def get_history(cls, collection: AsyncIOMotorCollection, name: str) -> List["Service"]:
        services = []
        async for document in collection.find({"name": name}):
            services.append(cls.from_dict(document))
        if not services:
            raise NotFound(f"No service found with name {name}")
        return services

    @classmethod
    async def calculate_sla(cls, collection: AsyncIOMotorCollection, name: str, interval: str) -> Dict[str, Any]:
        try:
            if interval.endswith("h"):
                interval_seconds = int(interval[:-1]) * 3600
            elif interval.endswith("d"):
                interval_seconds = int(interval[:-1]) * 86400
            else:
                return {"error": 'Invalid interval format. Use "h" for hours or "d" for days.'}

            end_time = datetime.utcnow()
            start_time = end_time - timedelta(seconds=interval_seconds)

            total_time = interval_seconds
            downtime = 0

            service_exists = await collection.find_one({"name": name})
            if not service_exists:
                raise NotFound(f"No service found with name {name}")

            service_entries = await collection.find({"name": name, "$or": [
                {"timestamp": {"$gte": start_time, "$lt": end_time}},
                {"timestamp_end": {"$gte": start_time, "$lt": end_time}}
            ]}).sort("timestamp").to_list(length=None)

            for service in service_entries:
                service_end_time = service.get("timestamp_end", end_time)
                if isinstance(service_end_time, str):
                    service_end_time = datetime.fromisoformat(service_end_time)
                if isinstance(service["timestamp"], str):
                    service_start_time = datetime.fromisoformat(service["timestamp"])
                else:
                    service_start_time = service["timestamp"]

                if service_start_time < start_time:
                    service_start_time = start_time
                if service_end_time > end_time:
                    service_end_time = end_time

                if service["state"] != "работает":
                    downtime += (service_end_time - service_start_time).total_seconds()

            uptime = total_time - downtime
            sla = (uptime / total_time) * 100

            return {"sla": round(sla, 3), "downtime": round(downtime / 3600, 3)}
        except NotFound as e:
            raise e
        except Exception as e:
            raise ServerError("Failed to calculate SLA")
