
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    ForeignKey,
    DateTime,
    func
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class OrderItem(Base):
    # Database table name
    __tablename__ = "order_items"

    # Unique item ID
    id = Column(Integer, primary_key=True, index=True)

    # Connect this item to its parent order
    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Product information from Product Catalog Service
    # These are snapshots, not copies of the product master table
    product_id = Column(Integer, nullable=False)
    product_name = Column(String(255), nullable=False)
    sku = Column(String(100), nullable=False)

    # Price and quantity at the time of ordering
    unit_price = Column(Numeric(12, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    # Connect this item back to its order
    order = relationship("Order", back_populates="items")
