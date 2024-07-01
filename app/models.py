from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Service(BaseModel):
    id: Optional[str] = None
    name: str
    state: str
    description: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    timestamp_end: Optional[datetime] = None



# Этот файл содержит описание моделей данных.
# В данном случае у нас есть модель Service, которая представляет сервис с определенными атрибутами.