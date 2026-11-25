from contextlib import asynccontextmanager
from fastapi import FastAPI
from .models import Base
from .db import engine



@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()



app = FastAPI(lifespan=lifespan)



