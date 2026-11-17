import httpx

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings


# Read the Bearer token from the Authorization header
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    # Reject requests without a Bearer token
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Extract the actual JWT string
    access_token = credentials.credentials

    # Build the Auth Service verification URL
    verify_url = (
        settings.AUTH_SERVICE_URL.rstrip("/")+ "/api/auth/verify-token")

    try:
        # Ask Auth Service to verify the token
        response = httpx.post(
            verify_url,
            json={"access_token": access_token},
            timeout=5.0
        )
        response.raise_for_status()
        result = response.json()

    except httpx.HTTPStatusError:
        # Auth Service returned an unsuccessful HTTP status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service returned an error"
        )

    except (httpx.RequestError, ValueError):
        # Auth Service is unreachable or returned invalid JSON
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is unavailable"
        )

    # Reject invalid or incomplete verification responses
    if (
        not result.get("valid")
        or result.get("user_id") is None
        or not result.get("role")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Return only the identity verified by Auth Service
    return {
        "user_id": result["user_id"],
        "role": result["role"].upper(),
        "access_token": access_token
    }