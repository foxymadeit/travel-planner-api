from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import places, projects


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup 
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Travel Planner API",
    description=(
        "Manage travel projects and places sourced from the "
        "Art Institute of Chicago collection."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api/v1")
app.include_router(places.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
