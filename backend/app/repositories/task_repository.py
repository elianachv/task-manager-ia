from datetime import date

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.enums import TaskStatus
from app.models.task import Task
from app.schemas.task import SortByField, SortOrder, TaskCreate, TaskListFilters, TaskUpdate


class TaskRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, task_data: TaskCreate) -> Task:
        task = Task(
            nombre=task_data.nombre,
            descripcion=task_data.descripcion,
            estado=task_data.estado,
            responsable=task_data.responsable,
            fecha_creacion=task_data.fecha_creacion or date.today(),
            fecha_vencimiento=task_data.fecha_vencimiento,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_by_id(self, task_id: int) -> Task | None:
        return self.db.query(Task).filter(Task.id == task_id).first()

    def list_tasks(self, filters: TaskListFilters) -> list[Task]:
        query = self.db.query(Task)

        if filters.responsable:
            query = query.filter(Task.responsable.ilike(f"%{filters.responsable}%"))

        if filters.estado:
            query = query.filter(Task.estado == filters.estado)

        if filters.vencimiento_desde:
            query = query.filter(Task.fecha_vencimiento >= filters.vencimiento_desde)

        if filters.vencimiento_hasta:
            query = query.filter(Task.fecha_vencimiento <= filters.vencimiento_hasta)

        if filters.creacion_desde:
            query = query.filter(Task.fecha_creacion >= filters.creacion_desde)

        if filters.creacion_hasta:
            query = query.filter(Task.fecha_creacion <= filters.creacion_hasta)

        sort_column_map = {
            SortByField.nombre: Task.nombre,
            SortByField.fecha_creacion: Task.fecha_creacion,
            SortByField.fecha_vencimiento: Task.fecha_vencimiento,
        }
        sort_column = sort_column_map[filters.sort_by]
        ordering = asc(sort_column) if filters.sort_order == SortOrder.asc else desc(sort_column)

        return query.order_by(ordering, Task.id).all()

    def update(self, task: Task, task_data: TaskUpdate) -> Task:
        update_data = task_data.model_dump(exclude_unset=True)

        if "fecha_creacion" in update_data or "fecha_vencimiento" in update_data:
            creation = update_data.get("fecha_creacion", task.fecha_creacion)
            due = update_data.get("fecha_vencimiento", task.fecha_vencimiento)
            if due < creation:
                raise ValueError(
                    "La fecha de vencimiento no puede ser anterior a la fecha de creación"
                )

        for field, value in update_data.items():
            setattr(task, field, value)

        self.db.commit()
        self.db.refresh(task)
        return task

    def delete(self, task: Task) -> None:
        self.db.delete(task)
        self.db.commit()
