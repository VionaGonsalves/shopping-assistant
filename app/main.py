from contextlib import asynccontextmanager
from fastapi import FastAPI
from .models import Base
from .db import engine
from .routers import auth, products, cart



@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()



app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
