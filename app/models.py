from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Tuple
from mongoengine import Document, StringField, DateTimeField, ObjectIdField, EmbeddedDocument, EmbeddedDocumentField, \
    ListField
from .exceptions import NotFound, ServerError
from bson import ObjectId

VALID_STATES = ["работает", "не работает"]


class StateHistory(EmbeddedDocument):
    state = StringField(required=True, choices=VALID_STATES)
    timestamp = DateTimeField(default=datetime.utcnow)
    timestamp_end = DateTimeField()

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "timestamp_end": self.timestamp_end.isoformat() if self.timestamp_end else None,
        }


class Service(Document):
    id = ObjectIdField(primary_key=True, default=lambda: ObjectId())
    name = StringField(required=True)
    state = StringField(required=True, choices=VALID_STATES)
    description = StringField()
    timestamp = DateTimeField(default=datetime.utcnow)
    timestamp_end = DateTimeField()
    history = ListField(EmbeddedDocumentField(StateHistory), default=list)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "state": self.state,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "timestamp_end": self.timestamp_end.isoformat() if self.timestamp_end else None,
            "history": [h.to_dict() for h in self.history]
        }

    @classmethod
    def get_all(cls) -> List[Service]:
        return list(cls.objects)

    @classmethod
    def create_or_update(cls, data: Dict[str, Any]) -> Service:
        name = data.get("name")
        new_state = data.get("state")
        description = data.get("description")

        if not name or not new_state:
            raise ValueError("Name and state are required")

        existing_service = cls.objects(name=name).first()

        if existing_service:
            return cls.update_service_state(existing_service, new_state, description)
        else:
            return cls.create_new_service(data)

    @classmethod
    def create_new_service(cls, data: Dict[str, Any]) -> Service:
        service = cls(**data)
        service.history.append(StateHistory(state=service.state, timestamp=service.timestamp))
        service.save()
        return service

    @classmethod
    def update_service_state(cls, existing_service: Service, new_state: str, description: Optional[str]) -> Service:
        if existing_service.state == new_state:
            raise ValueError(f"Service {existing_service.name} is already in state {new_state}")

        if existing_service.history:
            existing_service.history[-1].timestamp_end = datetime.utcnow()

        existing_service.history.append(StateHistory(state=new_state, timestamp=datetime.utcnow()))

        existing_service.state = new_state
        existing_service.description = description
        existing_service.timestamp = datetime.utcnow()
        existing_service.timestamp_end = None
        existing_service.save()
        return existing_service

    @classmethod
    def get_history(cls, name: str) -> List[Service]:
        services = list(cls.objects(name=name))
        if not services:
            raise NotFound(f"No service found with name {name}")
        return services

    @classmethod
    def calculate_sla(cls, name: str, interval: str) -> Dict[str, Any]:
        try:
            interval_seconds = cls.parse_interval(interval)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(seconds=interval_seconds)

            total_time = interval_seconds
            downtime = cls.calculate_downtime(name, start_time, end_time)

            uptime = total_time - downtime
            sla = (uptime / total_time) * 100
        except NotFound as e:
            raise NotFound(f"No service found with name {name}")
        except Exception as e:
            raise ServerError("Failed to calculate SLA")

        return {"sla": round(sla, 3), "downtime": round(downtime / 3600, 3)}

    @staticmethod
    def parse_interval(interval: str) -> int:
        if interval.endswith("h"):
            return int(interval[:-1]) * 3600
        elif interval.endswith("d"):
            return int(interval[:-1]) * 86400
        else:
            raise ValueError('Invalid interval format. Use "h" for hours or "d" for days.')

    @classmethod
    def calculate_downtime(cls, name: str, start_time: datetime, end_time: datetime) -> int:
        service_exists = cls.objects(name=name).first()
        if not service_exists:
            raise NotFound(f"No service found with name {name}")

        service_entries = cls.objects(
            name=name,
            __raw__={
                "$or": [
                    {"history.timestamp": {"$gte": start_time, "$lt": end_time}},
                    {"history.timestamp_end": {"$gte": start_time, "$lt": end_time}}
                ]
            }
        )

        downtime = 0
        for service in service_entries:
            for entry in service.history:
                service_start_time, service_end_time = cls.get_service_times(entry, start_time, end_time)
                if entry.state != "работает":
                    downtime += (service_end_time - service_start_time).total_seconds()

        return downtime

    @staticmethod
    def get_service_times(entry: StateHistory, start_time: datetime, end_time: datetime) -> Tuple[datetime, datetime]:
        service_end_time = entry.timestamp_end or end_time
        service_start_time = entry.timestamp

        if service_start_time < start_time:
            service_start_time = start_time
        if service_end_time > end_time:
            service_end_time = end_time

        return service_start_time, service_end_time
