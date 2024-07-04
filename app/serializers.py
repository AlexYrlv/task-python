from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from bson import ObjectId

class ServiceSerializer(BaseModel):
    id: Optional[str] = None
    name: str
    state: str
    description: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    timestamp_end: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }

    def to_mongo_dict(self) -> dict:
        """
        Преобразование объекта в словарь для MongoDB.
        """
        data = self.dict(exclude_none=True)
        if 'id' in data:
            data['_id'] = ObjectId(data.pop('id'))
        return data
