from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.routers import tasks

settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Gestor de Tareas API",
    description="API REST para gestión de tareas con filtros y ordenamiento",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
