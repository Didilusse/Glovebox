from typing import Optional
from pydantic import BaseModel

class Parts(BaseModel):
    name: str
    part_number: Optional[str] = None
    brand: Optional[str] = None
    cost: Optional[float] = None
    quantity: Optional[int] = 1
