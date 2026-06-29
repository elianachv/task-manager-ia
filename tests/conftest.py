"""Fixtures compartidas para pruebas unitarias e integración."""

from __future__ import annotations

import logging
import sys
from collections.abc import Generator
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from reporting import REPORTS_DIR, report_collector

TEST_DATABASE_URL = "sqlite://"

# ---------------------------------------------------------------------------
# Logging e informe final (hooks de pytest)
# ---------------------------------------------------------------------------

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = REPORTS_DIR / "pytest_session.log"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8", mode="w"),
        logging.StreamHandler(sys.stdout),
    ],
    force=True,
)
logging.getLogger().handlers[1].setLevel(logging.INFO)
test_logger = logging.getLogger("task_manager.tests")


def pytest_configure(config: pytest.Config) -> None:
    report_collector.on_session_start()
    test_logger.info("Sesión de pruebas iniciada")
    test_logger.info("Log detallado: %s", LOG_FILE)


def pytest_sessionstart(session: pytest.Session) -> None:
    test_logger.info("Directorio de informes: %s", REPORTS_DIR.resolve())


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item: pytest.Item):
    report_collector.on_test_start(item)
    test_logger.info("SETUP %s", item.nodeid)
    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item: pytest.Item):
    test_logger.info("EJECUTANDO %s", item.nodeid)
    yield


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if report.when == "call":
        report_collector.on_test_finish(report)
        level = logging.INFO if report.passed else logging.ERROR
        test_logger.log(
            level,
            "RESULTADO %s => %s (%.0f ms)",
            report.nodeid,
            report.outcome,
            report.duration * 1000,
        )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    test_logger.info("Sesión finalizada con código %s", exitstatus)
    report_collector.finalize(exitstatus)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Base de datos SQLite en memoria, aislada por test."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Cliente HTTP contra la app FastAPI con DB de prueba."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def today() -> date:
    return date.today()


@pytest.fixture()
def valid_task_payload(today: date) -> dict[str, str]:
    return {
        "nombre": "Tarea de prueba",
        "descripcion": "Descripción válida",
        "estado": "pendiente",
        "responsable": "Ana García",
        "fecha_creacion": today.isoformat(),
        "fecha_vencimiento": (today + timedelta(days=7)).isoformat(),
    }


@pytest.fixture()
def seed_tasks(client: TestClient, today: date) -> list[dict]:
    """Datos semilla para filtros y ordenamientos."""
    payloads = [
        {
            "nombre": "Alpha tarea",
            "estado": "pendiente",
            "responsable": "Ana García",
            "fecha_creacion": (today - timedelta(days=10)).isoformat(),
            "fecha_vencimiento": (today + timedelta(days=2)).isoformat(),
        },
        {
            "nombre": "Beta tarea",
            "estado": "en progreso",
            "responsable": "Luis Martínez",
            "fecha_creacion": (today - timedelta(days=5)).isoformat(),
            "fecha_vencimiento": (today + timedelta(days=10)).isoformat(),
        },
        {
            "nombre": "Zebra tarea",
            "estado": "finalizada",
            "responsable": "Ana García",
            "fecha_creacion": (today - timedelta(days=1)).isoformat(),
            "fecha_vencimiento": (today + timedelta(days=20)).isoformat(),
        },
    ]

    created: list[dict] = []
    for payload in payloads:
        response = client.post("/tasks", json=payload)
        assert response.status_code == 201
        created.append(response.json())
    return created
