
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


# Data customers are allowed to submit
class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


# Data returned for an order item
class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    sku: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal
    created_at: datetime

    # Read values from SQLAlchemy model objects
    model_config = ConfigDict(from_attributes=True)
