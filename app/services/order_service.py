
from datetime import datetime
from decimal import Decimal
from secrets import token_hex

from sqlalchemy.orm import Session

from app.models.order_model import Order
from app.models.order_item_model import OrderItem

# Generate a unique business order number
def generate_order_number():
    date_part = datetime.now().strftime("%Y%m%d")
    unique_part = token_hex(4).upper() #Generates 4 random bytes and converts them into 8 hexadecimal characters.

    return f"ORD-{date_part}-{unique_part}"

# Calculate order subtotal and final amount
def calculate_order_totals(
    items,
    discount=Decimal("0.00"),
    tax=Decimal("0.00"),
    shipping_fee=Decimal("0.00")
):
    subtotal = Decimal("0.00")

    for item in items:
        price = Decimal(str(item["unit_price"]))
        quantity = int(item["quantity"])

        subtotal += price * quantity

    total = subtotal - discount + tax + shipping_fee

    return {
        "subtotal": subtotal,
        "discount": discount,
        "tax": tax,
        "shipping_fee": shipping_fee,
        "total_amount": total
    }

# Save an order and its items in one database transaction
def create_order(
    db: Session,
    user_id: int,
    items: list,
    shipping_address: dict,
    notes: str = None
):
    try:
        # Calculate the order amounts
        totals = calculate_order_totals(items)

        # Create the main order
        order = Order(
            order_number=generate_order_number(),
            user_id=user_id,
            status="PENDING",
            payment_status="PENDING",
            shipping_address=shipping_address,
            notes=notes,
            **totals
        )

        db.add(order)

        # Get the database-generated order ID
        db.flush() #Sends the pending INSERT statement to MySQL.

        # Create individual order items
        for item in items:
            unit_price = Decimal(str(item["unit_price"]))
            quantity = int(item["quantity"])

            order_item = OrderItem(
                order_id=order.id,
                product_id=item["product_id"],
                product_name=item["product_name"],
                sku=item["sku"],
                unit_price=unit_price,
                quantity=quantity,
                line_total=unit_price * quantity
            )

            db.add(order_item)

        # Save the order and all its items together
        db.commit()

        db.refresh(order)

        return order

    except Exception:
        # Undo all changes if something goes wrong
        db.rollback()
        raise


# Define valid order status transitions
ALLOWED_TRANSITIONS = {
    "PENDING": ["CONFIRMED", "CANCELLED"],
    "CONFIRMED": ["PROCESSING", "CANCELLED"],
    "PROCESSING": ["SHIPPED", "CANCELLED"],
    "SHIPPED": ["DELIVERED"],
    "DELIVERED": [],
    "CANCELLED": []
}

# Update an order's status
def update_order_status(db, order_id: int, new_status: str):
    try:
        order = db.query(Order).filter(
            Order.id == order_id
        ).first()

        if not order:
            raise ValueError("Order not found")

        current_status = order.status
        new_status = new_status.upper()

        # Check whether the new status is valid
        if new_status not in ALLOWED_TRANSITIONS:
            raise ValueError("Invalid order status")

        # Check whether the transition is allowed
        allowed = ALLOWED_TRANSITIONS[current_status]

        if new_status not in allowed:
            raise ValueError(
                f"Cannot change order from {current_status} to {new_status}"
            )

        order.status = new_status

        db.commit()
        db.refresh(order)

        return order

    except Exception:
        db.rollback()
        raise



#
# Cancel an order and restore its reserved inventory
def cancel_order(db: Session, order_id: int):
    try:
        # Lock the order to prevent simultaneous cancellations
        order = db.query(Order).filter(
            Order.id == order_id
        ).with_for_update().first()

        if not order:
            raise ValueError("Order not found")

        # Repeated cancellation must not restore stock again
        if order.status == "CANCELLED":
            return order

        # Orders cannot be cancelled after shipment
        if order.status not in [
            "PENDING",
            "CONFIRMED",
            "PROCESSING"
        ]:
            raise ValueError(
                f"Order cannot be cancelled from {order.status} status"
            )

        # Combine quantities for duplicate product IDs
        product_quantities = {}

        for item in order.items:
            product_quantities[item.product_id] = (
                product_quantities.get(item.product_id, 0)
                + item.quantity
            )

        # Restore stock for every product
        for product_id, quantity in product_quantities.items():
            restore_product_stock(
                product_id=product_id,
                quantity=quantity,
                order_reference=order.order_number
            )

        # Mark the order cancelled only after restoration succeeds
        order.status = "CANCELLED"

        db.commit()
        db.refresh(order)

        return order

    except Exception:
        db.rollback()
        raise
