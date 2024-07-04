# app/models.py
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId

from .exceptions import NotFound, ServerError  # Изменен импорт

VALID_STATES = ["работает", "не работает"]

class Service:
    """
    Класс, представляющий сервис с его состоянием и временными метками.
    """

    def __init__(self, name: str, state: str, id: Optional[str] = None, description: Optional[str] = None,
                 timestamp: Optional[datetime] = None, timestamp_end: Optional[datetime] = None):
        self.id = id or str(ObjectId())
        self.name = name
        self.state = self.validate_state(state)
        self.description = description
        self.timestamp = timestamp or datetime.utcnow()
        self.timestamp_end = timestamp_end

    @staticmethod
    def validate_state(state: str) -> str:
        """
        Проверка допустимости состояния сервиса.
        """
        if state not in VALID_STATES:
            raise ValueError(f"Invalid state: {state}. State must be one of {VALID_STATES}")
        return state

    def to_dict(self) -> dict:
        """
        Преобразование объекта сервиса в словарь.
        """
        return {
            "_id": self.id,
            "name": self.name,
            "state": self.state,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "timestamp_end": self.timestamp_end.isoformat() if self.timestamp_end else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Service:
        """
        Создание объекта сервиса из словаря.
        """
        return cls(
            id=str(data.get("_id")),
            name=data["name"],
            state=data["state"],
            description=data.get("description"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if isinstance(data["timestamp"], str) else data["timestamp"],
            timestamp_end=datetime.fromisoformat(data["timestamp_end"]) if data.get("timestamp_end") and isinstance(
                data["timestamp_end"], str) else data["timestamp_end"]
        )

    @classmethod
    async def get_all(cls, collection: AsyncIOMotorCollection) -> List[Service]:
        """
        Получение всех сервисов из коллекции.
        """
        services = []
        async for document in collection.find():
            services.append(cls.from_dict(document))
        return services

    @classmethod
    async def create_or_update(cls, collection: AsyncIOMotorCollection, data: Dict[str, Any]) -> Service:
        """
        Создание нового или обновление существующего сервиса.
        """
        name = data.get("name")
        new_state = data.get("state")
        description = data.get("description")

        if not name or not new_state:
            raise ValueError("Name and state are required")

        await cls.update_end_timestamp(collection, name)
        existing_service = await collection.find_one({"name": name, "timestamp_end": None})

        if existing_service:
            return await cls.update_service_state(collection, existing_service, new_state, description)
        else:
            return await cls.create_new_service(collection, data)

    @classmethod
    async def create_new_service(cls, collection: AsyncIOMotorCollection, data: Dict[str, Any]) -> Service:
        """
        Создание нового сервиса.
        """
        service = cls(**data)
        result = await collection.insert_one(service.to_dict())
        service.id = str(result.inserted_id)
        return service

    @classmethod
    async def update_service_state(cls, collection: AsyncIOMotorCollection, existing_service: dict, new_state: str, description: Optional[str]) -> Service:
        """
        Обновление состояния существующего сервиса.
        """
        if existing_service["state"] == new_state:
            raise ValueError(f"Service {existing_service['name']} is already in state {new_state}")

        await collection.update_one(
            {"_id": existing_service["_id"]},
            {"$set": {"timestamp_end": datetime.utcnow()}}
        )

        service = cls(name=existing_service["name"], state=new_state, description=description)
        result = await collection.insert_one(service.to_dict())
        service.id = str(result.inserted_id)
        return service

    @classmethod
    async def update_end_timestamp(cls, collection: AsyncIOMotorCollection, name: str) -> int:
        """
        Обновление временной метки завершения для всех записей сервиса с незавершенным состоянием.
        """
        result = await collection.update_many(
            {"name": name, "timestamp_end": None},
            {"$set": {"timestamp_end": datetime.utcnow()}}
        )
        return result.modified_count

    @classmethod
    async def get_history(cls, collection: AsyncIOMotorCollection, name: str) -> List[Service]:
        """
        Получение истории изменения состояния сервиса.
        """
        services = []
        async for document in collection.find({"name": name}):
            services.append(cls.from_dict(document))
        if not services:
            raise NotFound(f"No service found with name {name}")
        return services

    @classmethod
    async def calculate_sla(cls, collection: AsyncIOMotorCollection, name: str, interval: str) -> Dict[str, Any]:
        """
        Расчет SLA (Service Level Agreement) для сервиса за указанный интервал времени.
        """
        try:
            interval_seconds = cls.parse_interval(interval)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(seconds=interval_seconds)

            total_time = interval_seconds
            downtime = await cls.calculate_downtime(collection, name, start_time, end_time)

            uptime = total_time - downtime
            sla = (uptime / total_time) * 100

            return {"sla": round(sla, 3), "downtime": round(downtime / 3600, 3)}
        except NotFound as e:
            raise e
        except Exception as e:
            raise ServerError("Failed to calculate SLA")

    @staticmethod
    def parse_interval(interval: str) -> int:
        """
        Преобразование интервала времени в секунды.
        """
        if interval.endswith("h"):
            return int(interval[:-1]) * 3600
        elif interval.endswith("d"):
            return int(interval[:-1]) * 86400
        else:
            raise ValueError('Invalid interval format. Use "h" for hours or "d" for days.')

    @classmethod
    async def calculate_downtime(cls, collection: AsyncIOMotorCollection, name: str, start_time: datetime, end_time: datetime) -> int:
        """
        Расчет времени простоя сервиса.
        """
        service_exists = await collection.find_one({"name": name})
        if not service_exists:
            raise NotFound(f"No service found with name {name}")

        service_entries = await collection.find({"name": name, "$or": [
            {"timestamp": {"$gte": start_time, "$lt": end_time}},
            {"timestamp_end": {"$gte": start_time, "$lt": end_time}}
        ]}).sort("timestamp").to_list(length=None)

        downtime = 0
        for service in service_entries:
            service_start_time, service_end_time = cls.get_service_times(service, start_time, end_time)
            if service["state"] != "работает":
                downtime += (service_end_time - service_start_time).total_seconds()

        return downtime

    @staticmethod
    def get_service_times(service: dict, start_time: datetime, end_time: datetime) -> tuple[datetime, datetime]:
        """
        Получение временных меток начала и конца для сервиса.
        """
        service_end_time = service.get("timestamp_end", end_time)
        if isinstance(service_end_time, str):
            service_end_time = datetime.fromisoformat(service_end_time)
        service_start_time = service["timestamp"]
        if isinstance(service_start_time, str):
            service_start_time = datetime.fromisoformat(service_start_time)

        if service_start_time < start_time:
            service_start_time = start_time
        if service_end_time > end_time:
            service_end_time = end_time

        return service_start_time, service_end_time
