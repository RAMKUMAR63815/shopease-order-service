
from pydantic import BaseModel, Field

# Data submitted when updating an order status
class OrderStatusUpdate(BaseModel):
    status: str = Field(
        min_length=1,
        max_length=30
    )