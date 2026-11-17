
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from app.database.connection import get_db
from app.models.order_model import Order
from app.schemas.order_schema import OrderCreate, OrderResponse
from app.services.order_service import create_order
from app.schemas.order_status_schema import OrderStatusUpdate
from app.services.order_service import update_order_status
from app.services.order_service import cancel_order
from app.core.security import get_current_user
from app.services.product_client import (
    get_product,
    reserve_product_stock,
    restore_product_stock
)
from app.services.user_client import get_user_address


router = APIRouter(
    prefix="/api/orders",
    tags=["Orders"]
)





@router.post("/", response_model=OrderResponse, status_code=201)
def create_new_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    access_token = current_user["access_token"]

    reserved_products = []
    order = None

    try:
        order_items = []
        products = {}

        # Fetch product details and combine duplicate product quantities
        for item in order_data.items:
            product = get_product(
                product_id=item.product_id,
                access_token=access_token
            )

            if product["product_id"] not in products:
                products[product["product_id"]] = {
                    **product,
                    "quantity": 0
                }

            products[product["product_id"]]["quantity"] += item.quantity

        # Check stock and prepare order items
        for product in products.values():
            if product["stock_quantity"] < product["quantity"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for product {product['product_id']}"
                )

        # Preserve the customer's original order lines
        for item in order_data.items:
            product = products[item.product_id]

            order_items.append({
                "product_id": product["product_id"],
                "product_name": product["product_name"],
                "sku": product["sku"],
                "unit_price": product["unit_price"],
                "quantity": item.quantity
            })

        # Retrieve the customer's shipping address
        shipping_address = get_user_address(
            address_id=order_data.shipping_address_id,
            access_token=access_token
        )

        # Save the order before reserving inventory
        order = create_order(
            db=db,
            user_id=user_id,
            items=order_items,
            shipping_address=shipping_address,
            notes=order_data.notes
        )

        # Reserve stock once per unique product
        for product in products.values():
            reserve_product_stock(
                product_id=product["product_id"],
                quantity=product["quantity"],
                order_reference=order.order_number
            )

            reserved_products.append(product)

        return order

    except Exception as error:
        db.rollback()

        # Restore products successfully reserved before a failure
        restoration_failed = False

        if order is not None:
            for product in reversed(reserved_products):
                try:
                    restore_product_stock(
                        product_id=product["product_id"],
                        quantity=product["quantity"],
                        order_reference=order.order_number
                    )
                except Exception:
                    restoration_failed = True

            # Mark the order cancelled only after successful compensation
            if not restoration_failed:
                try:
                    db.query(Order).filter(
                        Order.id == order.id
                    ).update({"status": "CANCELLED"})
                    db.commit()
                except Exception:
                    db.rollback()
                    restoration_failed = True

        if restoration_failed:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Order reservation failed and inventory compensation "
                    "needs recovery"
                )
            )

        if isinstance(error, HTTPException):
            raise error

        raise HTTPException(
            status_code=500,
            detail="Unable to create order"
        )

# Retrieve all orders with pagination
@router.get("/", response_model=list[OrderResponse])
def get_all_orders(
    skip: int = 0,
    limit: int = Query(default=10, le=100),
    status: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(Order).options(
        selectinload(Order.items)
    )

    # Customers can only view their own orders
    if current_user["role"] != "ADMIN":
        query = query.filter(
            Order.user_id == current_user["user_id"]
        )

    # Apply status filter when provided
    if status:
        query = query.filter(Order.status == status.upper())

    return query.order_by(
        Order.created_at.desc()
    ).offset(skip).limit(limit).all()


# Retrieve one order using its database ID
@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    order = db.query(Order).options(
        selectinload(Order.items)
    ).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # Customers cannot access another customer's order
    if (
        current_user["role"] != "ADMIN"
        and order.user_id != current_user["user_id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to access this order"
        )

    return order


# Retrieve one order using its order number
@router.get("/number/{order_number}", response_model=OrderResponse)
def get_order_by_number(
    order_number: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    order = db.query(Order).options(
        selectinload(Order.items)
    ).filter(
        Order.order_number == order_number
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # Customers can only access their own orders
    if (
        current_user["role"] != "ADMIN"
        and order.user_id != current_user["user_id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to access this order"
        )

    return order


# Update an order's status

@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Only administrators can manually update order status
    if current_user["role"] != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only administrators can update order status"
        )

    try:
        order = update_order_status(
            db=db,
            order_id=order_id,
            new_status=status_data.status
        )

        return order

    except ValueError as error:
        message = str(error)

        raise HTTPException(
            status_code=404 if message == "Order not found" else 400,
            detail=message
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to update order status"
        )


# Cancel an order

# Cancel an order
@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_existing_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Find the order
    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # Customers can only cancel their own orders
    if (
        current_user["role"] != "ADMIN"
        and order.user_id != current_user["user_id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to cancel this order"
        )

    try:
        return cancel_order(
            db=db,
            order_id=order_id
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to cancel order"
        )
