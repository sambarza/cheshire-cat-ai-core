
from typing import List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel

class CRUDSelect(BaseModel):
    id: UUID
    name: str
    updated_at: datetime
    #user_id: UUID

class CRUDUpdate(BaseModel):
    name: str = "No name"
