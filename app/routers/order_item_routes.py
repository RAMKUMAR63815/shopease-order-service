
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.order_model import Order
from app.models.order_item_model import OrderItem
from app.schemas.order_item_schema import OrderItemResponse
from app.core.security import get_current_user

router = APIRouter(
    prefix="/api/orders",
    tags=["Order Items"]
)


@router.get("/{order_id}/items", response_model=list[OrderItemResponse])
def get_order_items(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Find the requested order
    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # Customers can only access their own order items
    if (
        current_user["role"] != "ADMIN"
        and order.user_id != current_user["user_id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to access these order items"
        )

    # Return items belonging to the authorized order
    return db.query(OrderItem).filter(
        OrderItem.order_id == order_id
    ).all()
