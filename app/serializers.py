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
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }

    def dict(self, **kwargs):
        data = super().dict(**kwargs)
        if "timestamp" in data and data["timestamp"]:
            data["timestamp"] = data["timestamp"].isoformat()
        if "timestamp_end" in data and data["timestamp_end"]:
            data["timestamp_end"] = data["timestamp_end"].isoformat()
        return data
