from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Enum as SQLEnum, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship
from enum import Enum

class RolesEnum(str,Enum):
    customer = 'customer'
    admin = 'admin'

Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(SQLEnum(RolesEnum), default=RolesEnum.customer, nullable=False)
    hashed_password = Column(String, nullable=False)

class Products(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Numeric(12,2), nullable=False)
    product_type = Column(String, nullable=False)

class CartItems(Base):
    __tablename__ = 'cart_items'
    __table_args__ = (UniqueConstraint("user_id", "product_id"), CheckConstraint("quantity>0"))
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    product = relationship("Products")