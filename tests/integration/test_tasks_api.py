"""Pruebas de integración de la API REST (CP-05 a CP-16, CP-23, CP-24)."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_cp05_post_tasks_crear_tarea(
    client: TestClient, valid_task_payload: dict[str, str]
) -> None:
    """CP-05: POST /tasks crear tarea."""
    response = client.post("/tasks", json=valid_task_payload)

    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == valid_task_payload["nombre"]
    assert data["estado"] == "pendiente"
    assert data["responsable"] == valid_task_payload["responsable"]


@pytest.mark.integration
def test_cp06_get_tasks_listar_tareas(client: TestClient, seed_tasks: list[dict]) -> None:
    """CP-06: GET /tasks listar tareas."""
    response = client.get("/tasks")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(seed_tasks)


@pytest.mark.integration
def test_cp07_get_tasks_id_existente(client: TestClient, valid_task_payload: dict[str, str]) -> None:
    """CP-07: GET /tasks/{id} existente."""
    created = client.post("/tasks", json=valid_task_payload).json()
    response = client.get(f"/tasks/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


@pytest.mark.integration
def test_cp08_get_tasks_id_inexistente_404(client: TestClient) -> None:
    """CP-08: GET /tasks/{id} inexistente (404)."""
    response = client.get("/tasks/99999")

    assert response.status_code == 404
    assert "no encontrada" in response.json()["detail"].lower()


@pytest.mark.integration
def test_cp09_put_tasks_id_actualizar_tarea(
    client: TestClient, valid_task_payload: dict[str, str]
) -> None:
    """CP-09: PUT /tasks/{id} actualizar tarea."""
    task_id = client.post("/tasks", json=valid_task_payload).json()["id"]
    response = client.put(
        f"/tasks/{task_id}",
        json={"nombre": "Tarea actualizada", "estado": "en progreso"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["nombre"] == "Tarea actualizada"
    assert data["estado"] == "en progreso"


@pytest.mark.integration
def test_cp10_delete_tasks_id_eliminar_tarea(
    client: TestClient, valid_task_payload: dict[str, str]
) -> None:
    """CP-10: DELETE /tasks/{id} eliminar tarea."""
    task_id = client.post("/tasks", json=valid_task_payload).json()["id"]
    response = client.delete(f"/tasks/{task_id}")

    assert response.status_code == 204
    assert client.get(f"/tasks/{task_id}").status_code == 404


@pytest.mark.integration
def test_cp11_filtro_por_estado(client: TestClient, seed_tasks: list[dict]) -> None:
    """CP-11: Filtro por estado."""
    response = client.get("/tasks", params={"estado": "pendiente"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert all(task["estado"] == "pendiente" for task in data)


@pytest.mark.integration
def test_cp12_filtro_por_responsable(client: TestClient, seed_tasks: list[dict]) -> None:
    """CP-12: Filtro por responsable."""
    response = client.get("/tasks", params={"responsable": "Ana"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all("Ana" in (task["responsable"] or "") for task in data)


@pytest.mark.integration
def test_cp13_filtro_por_rango_fecha_creacion(
    client: TestClient, seed_tasks: list[dict], today: date
) -> None:
    """CP-13: Filtro por rango fecha creación."""
    response = client.get(
        "/tasks",
        params={
            "creacion_desde": (today - timedelta(days=6)).isoformat(),
            "creacion_hasta": today.isoformat(),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for task in data:
        creation = date.fromisoformat(task["fecha_creacion"])
        assert today - timedelta(days=6) <= creation <= today


@pytest.mark.integration
def test_cp14_filtro_por_rango_fecha_vencimiento(
    client: TestClient, seed_tasks: list[dict], today: date
) -> None:
    """CP-14: Filtro por rango fecha vencimiento."""
    response = client.get(
        "/tasks",
        params={
            "vencimiento_desde": today.isoformat(),
            "vencimiento_hasta": (today + timedelta(days=5)).isoformat(),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["nombre"] == "Alpha tarea"


@pytest.mark.integration
def test_cp15_orden_por_nombre_asc_desc(client: TestClient, seed_tasks: list[dict]) -> None:
    """CP-15: Orden por nombre asc/desc."""
    asc_response = client.get("/tasks", params={"sort_by": "nombre", "sort_order": "asc"})
    desc_response = client.get("/tasks", params={"sort_by": "nombre", "sort_order": "desc"})

    asc_names = [task["nombre"] for task in asc_response.json()]
    desc_names = [task["nombre"] for task in desc_response.json()]

    assert asc_names == ["Alpha tarea", "Beta tarea", "Zebra tarea"]
    assert desc_names == ["Zebra tarea", "Beta tarea", "Alpha tarea"]


@pytest.mark.integration
def test_cp16_orden_por_fechas_asc_desc(client: TestClient, seed_tasks: list[dict]) -> None:
    """CP-16: Orden por fechas asc/desc."""
    creation_asc = client.get(
        "/tasks", params={"sort_by": "fecha_creacion", "sort_order": "asc"}
    ).json()
    creation_desc = client.get(
        "/tasks", params={"sort_by": "fecha_creacion", "sort_order": "desc"}
    ).json()
    due_asc = client.get(
        "/tasks", params={"sort_by": "fecha_vencimiento", "sort_order": "asc"}
    ).json()
    due_desc = client.get(
        "/tasks", params={"sort_by": "fecha_vencimiento", "sort_order": "desc"}
    ).json()

    assert creation_asc[0]["nombre"] == "Alpha tarea"
    assert creation_desc[0]["nombre"] == "Zebra tarea"
    assert due_asc[0]["nombre"] == "Alpha tarea"
    assert due_desc[0]["nombre"] == "Zebra tarea"


@pytest.mark.integration
def test_cp23_manejo_payload_invalido_422(client: TestClient, today: date) -> None:
    """CP-23: Manejo de payload inválido (422)."""
    response = client.post(
        "/tasks",
        json={
            "nombre": "",
            "estado": "pendiente",
            "fecha_creacion": today.isoformat(),
            "fecha_vencimiento": (today - timedelta(days=2)).isoformat(),
        },
    )

    assert response.status_code == 422


@pytest.mark.integration
def test_cp24_persistencia_y_consistencia_de_datos(
    client: TestClient, valid_task_payload: dict[str, str]
) -> None:
    """CP-24: Persistencia/consistencia de datos."""
    create_response = client.post("/tasks", json=valid_task_payload)
    created = create_response.json()

    first_get = client.get(f"/tasks/{created['id']}")
    assert first_get.status_code == 200
    assert first_get.json()["nombre"] == valid_task_payload["nombre"]

    update_response = client.put(
        f"/tasks/{created['id']}",
        json={"descripcion": "Descripción persistida", "estado": "finalizada"},
    )
    assert update_response.status_code == 200

    second_get = client.get(f"/tasks/{created['id']}")
    persisted = second_get.json()
    assert persisted["descripcion"] == "Descripción persistida"
    assert persisted["estado"] == "finalizada"
    assert persisted["nombre"] == valid_task_payload["nombre"]
