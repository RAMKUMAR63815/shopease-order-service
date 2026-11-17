
from fastapi import FastAPI

from app.routers.order_routes import router as order_router
from app.routers.order_item_routes import router as order_item_router


app = FastAPI(
    title="ShopEase Order Management Service",
    description="Microservice for managing customer orders",
    version="1.0.0"
)


# Register application routers
app.include_router(order_router)
app.include_router(order_item_router)


@app.get("/")
def home():
    return {
        "message": "ShopEase Order Management Service is running"
    }


@app.get("/health")
def health_check():
    return {
        "service": "order-service",
        "status": "healthy"
    }
