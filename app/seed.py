from decimal import Decimal

from pwdlib import PasswordHash

from .db import SessionLocal
from .models import Users, Products, RolesEnum

password_hash = PasswordHash.recommended()

PRODUCTS = [
    {"name": "Maruti Suzuki Swift", "price": Decimal("650000.00"), "product_type": "hatchback"},
    {"name": "Hyundai i20", "price": Decimal("750000.00"), "product_type": "hatchback"},
    {"name": "Tata Altroz", "price": Decimal("700000.00"), "product_type": "hatchback"},
    {"name": "Honda City", "price": Decimal("1250000.00"), "product_type": "sedan"},
    {"name": "Hyundai Verna", "price": Decimal("1150000.00"), "product_type": "sedan"},
    {"name": "Skoda Slavia", "price": Decimal("1300000.00"), "product_type": "sedan"},
    {"name": "Hyundai Creta", "price": Decimal("1400000.00"), "product_type": "suv"},
    {"name": "Mahindra XUV700", "price": Decimal("1900000.00"), "product_type": "suv"},
    {"name": "Tata Nexon EV", "price": Decimal("1450000.00"), "product_type": "electric"},
    {"name": "MG ZS EV", "price": Decimal("1900000.00"), "product_type": "electric"},
]

USERS = [
    {"name": "Admin", "email": "admin@shop.com", "role": RolesEnum.admin, "password": "admin123"},
    {"name": "Viona", "email": "viona@shop.com", "role": RolesEnum.customer, "password": "customer123"},
]


def seed():
    db = SessionLocal()
    try:
        if db.query(Products).first():
            print("Already seeded, skipping")
            return

        db.add_all([Products(**p) for p in PRODUCTS])
        db.add_all([
            Users(
                name=u["name"],
                email=u["email"],
                role=u["role"],
                hashed_password=password_hash.hash(u["password"]),
            )
            for u in USERS
        ])
        db.commit()
        print(f"Seeded {len(PRODUCTS)} products and {len(USERS)} users")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()