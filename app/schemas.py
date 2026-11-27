from pydantic import BaseModel, EmailStr, ConfigDict, Field
from decimal import Decimal
from typing import Annotated
from .models import RolesEnum
from typing import Literal

Price = Annotated[Decimal, Field(max_digits=12, decimal_places=2, gt=0)]

class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=8)

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: RolesEnum

class ProductCreate(BaseModel):
    name: str
    price: Price
    product_type: str

class ProductUpdate(BaseModel):
    name: str | None = None
    price: Price | None = None
    product_type: str | None = None

class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Price
    product_type: str

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1, gt=0)

class CartItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product: ProductRead
    quantity: int

class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    message: str = Field(min_length=1)

class ChatResponse(BaseModel):
    reply: str