from collections.abc import Generator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite://"


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_task(client: TestClient) -> None:
    payload = {
        "nombre": "Nueva tarea",
        "descripcion": "Descripción de prueba",
        "estado": "pendiente",
        "responsable": "Tester",
        "fecha_vencimiento": (date.today() + timedelta(days=5)).isoformat(),
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Nueva tarea"
    assert data["estado"] == "pendiente"
    assert "id" in data


def test_create_task_invalid_due_date(client: TestClient) -> None:
    payload = {
        "nombre": "Tarea inválida",
        "estado": "pendiente",
        "fecha_creacion": date.today().isoformat(),
        "fecha_vencimiento": (date.today() - timedelta(days=1)).isoformat(),
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 422


def test_list_tasks_with_filters(client: TestClient) -> None:
    today = date.today()
    tasks = [
        {
            "nombre": "Tarea A",
            "estado": "pendiente",
            "responsable": "Ana",
            "fecha_vencimiento": (today + timedelta(days=2)).isoformat(),
        },
        {
            "nombre": "Tarea B",
            "estado": "finalizada",
            "responsable": "Luis",
            "fecha_vencimiento": (today + timedelta(days=10)).isoformat(),
        },
    ]
    for task in tasks:
        client.post("/tasks", json=task)

    response = client.get("/tasks", params={"responsable": "Ana", "estado": "pendiente"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["nombre"] == "Tarea A"


def test_get_update_delete_task(client: TestClient) -> None:
    create_response = client.post(
        "/tasks",
        json={
            "nombre": "Tarea CRUD",
            "estado": "pendiente",
            "responsable": "María",
            "fecha_vencimiento": (date.today() + timedelta(days=3)).isoformat(),
        },
    )
    task_id = create_response.json()["id"]

    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200

    update_response = client.put(
        f"/tasks/{task_id}",
        json={"estado": "en progreso", "nombre": "Tarea actualizada"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["estado"] == "en progreso"

    delete_response = client.delete(f"/tasks/{task_id}")
    assert delete_response.status_code == 204

    not_found_response = client.get(f"/tasks/{task_id}")
    assert not_found_response.status_code == 404


def test_sort_tasks_by_name(client: TestClient) -> None:
    today = date.today()
    for name in ["Zebra", "Alpha", "Beta"]:
        client.post(
            "/tasks",
            json={
                "nombre": name,
                "estado": "pendiente",
                "fecha_vencimiento": (today + timedelta(days=1)).isoformat(),
            },
        )

    response = client.get("/tasks", params={"sort_by": "nombre", "sort_order": "asc"})
    assert response.status_code == 200
    names = [task["nombre"] for task in response.json()]
    assert names == sorted(names)
