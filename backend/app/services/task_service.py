from sqlalchemy.orm import Session

from app.models.task import Task
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskListFilters, TaskUpdate


class TaskService:
    def __init__(self, db: Session) -> None:
        self.repository = TaskRepository(db)

    def create_task(self, task_data: TaskCreate) -> Task:
        return self.repository.create(task_data)

    def get_task(self, task_id: int) -> Task | None:
        return self.repository.get_by_id(task_id)

    def list_tasks(self, filters: TaskListFilters) -> list[Task]:
        return self.repository.list_tasks(filters)

    def update_task(self, task_id: int, task_data: TaskUpdate) -> Task | None:
        task = self.repository.get_by_id(task_id)
        if not task:
            return None
        return self.repository.update(task, task_data)

    def delete_task(self, task_id: int) -> bool:
        task = self.repository.get_by_id(task_id)
        if not task:
            return False
        self.repository.delete(task)
        return True
