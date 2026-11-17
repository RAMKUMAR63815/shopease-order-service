
from decimal import Decimal
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.order_item_schema import (
    OrderItemCreate,
    OrderItemResponse
)


# Data customers submit when creating an order
class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)
    shipping_address_id: int = Field(gt=0)
    notes: Optional[str] = None


# Data returned after creating or retrieving an order
class OrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: int

    status: str
    payment_status: str

    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    shipping_fee: Decimal
    total_amount: Decimal

    shipping_address: dict
    notes: Optional[str]

    created_at: datetime
    updated_at: datetime

    items: list[OrderItemResponse]

    # Read values from SQLAlchemy model objects
    model_config = ConfigDict(from_attributes=True)
