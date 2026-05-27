from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.state import get_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_agent()
    yield


app = FastAPI(title="SHL Assessment Recommender", lifespan=lifespan)
app.include_router(router)
