from sqlalchemy import Column, Integer, String, Boolean, Numeric, Date, ForeignKey, JSON, TIMESTAMP, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Drug(Base):
    __tablename__ = "drugs"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    generic_name = Column(String)
    spec = Column(String)
    manufacturer = Column(String)
    is_rx = Column(Boolean, default=False)
    contraindications_json = Column(JSON)
    flags_json = Column(JSON)

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True)
    drug_id = Column(Integer, ForeignKey("drugs.id"))
    stock = Column(Integer, default=0)
    batch_no = Column(String)
    expire_date = Column(Date)

class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True)
    drug_id = Column(Integer, ForeignKey("drugs.id"))
    list_price = Column(Numeric(10,2))
    member_tier = Column(String)
    discount_rate = Column(Numeric(5,2), default=1.0)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer)
    total = Column(Numeric(10,2))
    created_at = Column(TIMESTAMP, server_default=func.now())
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    drug_id = Column(Integer)
    qty = Column(Integer)
    unit_price = Column(Numeric(10,2))
    final_price = Column(Numeric(10,2))
    order = relationship("Order", back_populates="items")