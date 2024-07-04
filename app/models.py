from datetime import datetime
from mongoengine import Document, StringField, DateTimeField, ObjectIdField
from .exceptions import NotFound, ServerError

VALID_STATES = ["работает", "не работает"]


class Service(Document):
    """
    Класс, представляющий сервис с его состоянием и временными метками.
    """
    id = ObjectIdField(primary_key=True, default=None)
    name = StringField(required=True)
    state = StringField(required=True, choices=VALID_STATES)
    description = StringField()
    timestamp = DateTimeField(default=datetime.utcnow)
    timestamp_end = DateTimeField()

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
            "id": str(self.id),
            "name": self.name,
            "state": self.state,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "timestamp_end": self.timestamp_end.isoformat() if self.timestamp_end else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Service":
        """
        Создание объекта сервиса из словаря.
        """
        return cls(
            id=data.get("id"),
            name=data["name"],
            state=data["state"],
            description=data.get("description"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if isinstance(data["timestamp"], str) else data[
                "timestamp"],
            timestamp_end=datetime.fromisoformat(data["timestamp_end"]) if data.get("timestamp_end") and isinstance(
                data["timestamp_end"], str) else data["timestamp_end"]
        )

    @classmethod
    def get_all(cls) -> List["Service"]:
        """
        Получение всех сервисов из коллекции.
        """
        return list(cls.objects)

    @classmethod
    def create_or_update(cls, data: Dict[str, Any]) -> "Service":
        """
        Создание нового или обновление существующего сервиса.
        """
        name = data.get("name")
        new_state = data.get("state")
        description = data.get("description")

        if not name or not new_state:
            raise ValueError("Name and state are required")

        existing_service = cls.objects(name=name, timestamp_end=None).first()

        if existing_service:
            return cls.update_service_state(existing_service, new_state, description)
        else:
            return cls.create_new_service(data)

    @classmethod
    def create_new_service(cls, data: Dict[str, Any]) -> "Service":
        """
        Создание нового сервиса.
        """
        service = cls(**data)
        service.save()
        return service

    @classmethod
    def update_service_state(cls, existing_service: Document, new_state: str, description: Optional[str]) -> "Service":
        """
        Обновление состояния существующего сервиса.
        """
        if existing_service.state == new_state:
            raise ValueError(f"Service {existing_service.name} is already in state {new_state}")

        existing_service.update(set__timestamp_end=datetime.utcnow())

        service = cls(name=existing_service.name, state=new_state, description=description)
        service.save()
        return service

    @classmethod
    def get_history(cls, name: str) -> List["Service"]:
        """
        Получение истории изменения состояния сервиса.
        """
        services = list(cls.objects(name=name))
        if not services:
            raise NotFound(f"No service found with name {name}")
        return services

    @classmethod
    def calculate_sla(cls, name: str, interval: str) -> Dict[str, Any]:
        """
        Расчет SLA (Service Level Agreement) для сервиса за указанный интервал времени.
        """
        try:
            interval_seconds = cls.parse_interval(interval)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(seconds=interval_seconds)

            total_time = interval_seconds
            downtime = cls.calculate_downtime(name, start_time, end_time)

            uptime = total_time - downtime
            sla = (uptime / total_time) * 100

            return {"sla": round(sla, 3), "downtime": round(downtime / 3600, 3)}
        except NotFound as e:
            raise NotFound(f"No service found with name {name}")
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
    def calculate_downtime(cls, name: str, start_time: datetime, end_time: datetime) -> int:
        """
        Расчет времени простоя сервиса.
        """
        service_exists = cls.objects(name=name).first()
        if not service_exists:
            raise NotFound(f"No service found with name {name}")

        service_entries = cls.objects(name=name, timestamp__gte=start_time, timestamp__lt=end_time) | \
                          cls.objects(name=name, timestamp_end__gte=start_time, timestamp_end__lt=end_time)

        downtime = 0
        for service in service_entries:
            service_start_time, service_end_time = cls.get_service_times(service, start_time, end_time)
            if service.state != "работает":
                downtime += (service_end_time - service_start_time).total_seconds()

        return downtime

    @staticmethod
    def get_service_times(service: Document, start_time: datetime, end_time: datetime) -> (datetime, datetime):
        """
        Получение временных меток начала и конца для сервиса.
        """
        service_end_time = service.timestamp_end or end_time
        service_start_time = service.timestamp

        if service_start_time < start_time:
            service_start_time = start_time
        if service_end_time > end_time:
            service_end_time = end_time

        return service_start_time, service_end_time
