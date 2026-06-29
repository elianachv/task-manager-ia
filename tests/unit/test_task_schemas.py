"""Pruebas unitarias de esquemas y validaciones Pydantic (CP-01 a CP-04)."""

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.task import TaskCreate, TaskUpdate


@pytest.mark.unit
def test_cp01_crear_tarea_con_datos_validos() -> None:
    """CP-01: Crear tarea con datos válidos."""
    today = date.today()
    task = TaskCreate(
        nombre="  Revisar informe  ",
        descripcion="Informe mensual",
        estado="pendiente",
        responsable="María López",
        fecha_creacion=today,
        fecha_vencimiento=today + timedelta(days=3),
    )

    assert task.nombre == "Revisar informe"
    assert task.estado.value == "pendiente"
    assert task.fecha_creacion == today
    assert task.fecha_vencimiento == today + timedelta(days=3)


@pytest.mark.unit
def test_cp02_rechazar_estado_invalido() -> None:
    """CP-02: Rechazar estado inválido."""
    today = date.today()
    with pytest.raises(ValidationError) as exc_info:
        TaskCreate(
            nombre="Tarea inválida",
            estado="cancelada",
            fecha_vencimiento=today + timedelta(days=1),
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("estado",) for error in errors)


@pytest.mark.unit
def test_cp03_rechazar_fecha_vencimiento_anterior_a_creacion() -> None:
    """CP-03: Rechazar fecha_vencimiento < fecha_creacion."""
    today = date.today()
    with pytest.raises(ValidationError) as exc_info:
        TaskCreate(
            nombre="Tarea con fechas inválidas",
            estado="pendiente",
            fecha_creacion=today,
            fecha_vencimiento=today - timedelta(days=1),
        )

    assert "fecha de vencimiento" in str(exc_info.value).lower()


@pytest.mark.unit
def test_cp04_rechazar_tarea_sin_nombre() -> None:
    """CP-04: Rechazar tarea sin nombre."""
    today = date.today()

    with pytest.raises(ValidationError):
        TaskCreate(
            nombre="   ",
            estado="pendiente",
            fecha_vencimiento=today + timedelta(days=2),
        )

    with pytest.raises(ValidationError):
        TaskUpdate(nombre="   ")
