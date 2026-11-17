
import httpx
from fastapi import HTTPException

from app.core.config import settings


def get_user_address(
    address_id: int,
    access_token: str
):
    # Build the User Management API URL
    url = (
        settings.USER_SERVICE_URL.rstrip("/")
        + f"/api/users/addresses/{address_id}"
    )

    try:
        # Request the address using the customer's JWT
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
                detail="Shipping address not found"
            )

        if response.status_code == 403:
            raise HTTPException(
                status_code=403,
                detail="You cannot use this shipping address"
            )

        response.raise_for_status()
        address = response.json()

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502,
            detail="User Management Service returned an error"
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="User Management Service is unavailable"
        )

    # Return a snapshot of the address details
    return {
        "address_id": address["id"],
        "address_type": address["address_type"],
        "full_name": address["full_name"],
        "phone_number": address["phone_number"],
        "address_line_1": address["address_line_1"],
        "address_line_2": address.get("address_line_2"),
        "city": address["city"],
        "state": address["state"],
        "country": address["country"],
        "postal_code": address["postal_code"]
    }
