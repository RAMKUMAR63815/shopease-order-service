
import httpx
from decimal import Decimal

from fastapi import HTTPException

from app.core.config import settings


def get_product(
    product_id: int,
    access_token: str
):
    # Build the Product Catalog API URL
    url = (
        settings.PRODUCT_SERVICE_URL.rstrip("/") #rstrip("/") is a Python string method that removes / characters from the end (right side) of a string.
        + f"/api/products/{product_id}"
    )

    try:
        # Request product details from Product Catalog
        response = httpx.get(
            url,
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            timeout=5.0
        )

        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Product {product_id} not found"
            )

        response.raise_for_status()
        product = response.json()

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502,
            detail="Product Catalog returned an error"
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Product Catalog Service is unavailable"
        )

    # Reject inactive products
    if not product.get("is_active"):
        raise HTTPException(
            status_code=400,
            detail=f"Product {product_id} is inactive"
        )

    # Convert the authoritative product price to Decimal
    price = Decimal(str(product["discount_price"] or product["price"]))

    if price < Decimal("0.00"):
        raise HTTPException(
            status_code=502,
            detail="Product Catalog returned an invalid price"
        )

    return {
        "product_id": product["id"],
        "product_name": product["name"],
        "sku": product["sku"],
        "unit_price": price,
        "stock_quantity": product["stock_quantity"]
    }



# Send internal inventory requests to Product Catalog
def update_product_inventory(
    product_id: int,
    quantity: int,
    order_reference: str,
    action: str
):
    # Check internal service token configuration
    if not settings.INTERNAL_SERVICE_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Internal service authentication is not configured"
        )

    # Select the inventory endpoint
    if action == "reserve":
        endpoint = "reserve"
        transaction_type = "STOCK_OUT"
    elif action == "restore":
        endpoint = "restore"
        transaction_type = "STOCK_IN"
    else:
        raise ValueError("Invalid inventory action")

    # Build the inventory API URL
    url = (
        settings.PRODUCT_SERVICE_URL.rstrip("/")
        + f"/api/inventory/internal/{product_id}/{endpoint}"
    )

    # Prepare the inventory transaction
    payload = {
        "transaction_type": transaction_type,
        "quantity": quantity,
        "reference_id": order_reference,
        "remarks": f"Order {action}"
    }

    try:
        # Send authenticated internal request
        response = httpx.post(
            url,
            json=payload,
            headers={
                "X-Service-Token": settings.INTERNAL_SERVICE_TOKEN
            },
            timeout=5.0
        )

        response.raise_for_status()

        return response.json()

    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code

        try:
            detail = exc.response.json().get(
                "detail",
                "Inventory operation failed"
            )
        except ValueError:
            detail = "Inventory operation failed"

        if status_code == 409:
            raise HTTPException(
                status_code=409,
                detail=detail
            )

        if status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=detail
            )

        raise HTTPException(
            status_code=502,
            detail="Product Catalog inventory operation failed"
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Product Catalog Service is unavailable"
        )


# Reserve product stock for an order
def reserve_product_stock(
    product_id: int,
    quantity: int,
    order_reference: str
):
    return update_product_inventory(
        product_id,
        quantity,
        order_reference,
        "reserve"
    )


# Restore product stock after order cancellation
def restore_product_stock(
    product_id: int,
    quantity: int,
    order_reference: str
):
    return update_product_inventory(
        product_id,
        quantity,
        order_reference,
        "restore"
    )
