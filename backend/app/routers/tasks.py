from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums import TaskStatus
from app.schemas.task import (
    SortByField,
    SortOrder,
    TaskCreate,
    TaskListFilters,
    TaskResponse,
    TaskUpdate,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    return TaskService(db)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task = service.create_task(task_data)
    return TaskResponse.model_validate(task)


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    responsable: str | None = Query(default=None),
    estado: TaskStatus | None = Query(default=None),
    vencimiento_desde: date | None = Query(default=None),
    vencimiento_hasta: date | None = Query(default=None),
    creacion_desde: date | None = Query(default=None),
    creacion_hasta: date | None = Query(default=None),
    sort_by: SortByField = Query(default=SortByField.fecha_creacion),
    sort_order: SortOrder = Query(default=SortOrder.desc),
    service: TaskService = Depends(get_task_service),
) -> list[TaskResponse]:
    try:
        filters = TaskListFilters(
            responsable=responsable,
            estado=estado,
            vencimiento_desde=vencimiento_desde,
            vencimiento_hasta=vencimiento_hasta,
            creacion_desde=creacion_desde,
            creacion_hasta=creacion_hasta,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    tasks = service.list_tasks(filters)
    return [TaskResponse.model_validate(task) for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarea con id {task_id} no encontrada",
        )
    return TaskResponse.model_validate(task)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    try:
        task = service.update_task(task_id, task_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarea con id {task_id} no encontrada",
        )
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
) -> None:
    deleted = service.delete_task(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarea con id {task_id} no encontrada",
        )
