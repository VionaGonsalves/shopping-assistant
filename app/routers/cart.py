from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from ..auth import get_current_user
from ..db import get_db
from ..models import CartItems, Products, Users
from ..schemas import CartItemCreate, CartItemRead, CartItemUpdate

router = APIRouter(prefix="/cart", tags=["cart"])


def get_user_cart_item(item_id: int, user: Users, db: Session) -> CartItems:
    """Load a cart item only if it belongs to this user. Otherwise 404."""
    item = (
        db.query(CartItems)
        .filter(CartItems.id == item_id, CartItems.user_id == user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    return item


@router.get("", response_model=list[CartItemRead])
def view_cart(
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    return (
        db.query(CartItems)
        .options(joinedload(CartItems.product))   
        .filter(CartItems.user_id == current_user.id)
        .all()
    )


@router.post("/items", response_model=CartItemRead, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    item_in: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    product = db.get(Products, item_in.product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    existing = (
        db.query(CartItems)
        .filter(CartItems.user_id == current_user.id, CartItems.product_id == item_in.product_id)
        .first()
    )
    if existing:
        existing.quantity += item_in.quantity
        item = existing
    else:
        item = CartItems(
            user_id=current_user.id,          # from the token
            product_id=item_in.product_id,
            quantity=item_in.quantity,
        )
        db.add(item)

    db.commit()
    db.refresh(item)
    return item


@router.patch("/items/{item_id}", response_model=CartItemRead)
def update_cart_item(
    item_id: int,
    item_in: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    item = get_user_cart_item(item_id, current_user, db)
    item.quantity = item_in.quantity
    db.commit()
    db.refresh(item)
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    item = get_user_cart_item(item_id, current_user, db)
    db.delete(item)
    db.commit()