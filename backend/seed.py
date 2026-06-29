"""Script para poblar la base de datos con tareas de ejemplo."""

from datetime import date, timedelta

from app.database import SessionLocal
from app.enums import TaskStatus
from app.models.task import Task


def seed() -> None:
    db = SessionLocal()
    try:
        existing = db.query(Task).count()
        if existing > 0:
            print(f"La base de datos ya contiene {existing} tareas. Seed omitido.")
            return

        today = date.today()
        sample_tasks = [
            Task(
                nombre="Configurar entorno local",
                descripcion="Instalar dependencias y levantar backend y frontend.",
                estado=TaskStatus.finalizada,
                responsable="Ana García",
                fecha_creacion=today - timedelta(days=10),
                fecha_vencimiento=today - timedelta(days=5),
            ),
            Task(
                nombre="Diseñar interfaz de tareas",
                descripcion="Crear formulario y listado con filtros.",
                estado=TaskStatus.en_progreso,
                responsable="Luis Martínez",
                fecha_creacion=today - timedelta(days=4),
                fecha_vencimiento=today + timedelta(days=3),
            ),
            Task(
                nombre="Implementar API REST",
                descripcion="Endpoints CRUD con validaciones Pydantic.",
                estado=TaskStatus.en_progreso,
                responsable="Ana García",
                fecha_creacion=today - timedelta(days=7),
                fecha_vencimiento=today + timedelta(days=1),
            ),
            Task(
                nombre="Escribir pruebas de API",
                descripcion="Cobertura mínima con pytest y TestClient.",
                estado=TaskStatus.pendiente,
                responsable="María López",
                fecha_creacion=today - timedelta(days=2),
                fecha_vencimiento=today + timedelta(days=7),
            ),
            Task(
                nombre="Documentar README",
                descripcion="Instrucciones de instalación y ejecución local.",
                estado=TaskStatus.pendiente,
                responsable="Luis Martínez",
                fecha_creacion=today,
                fecha_vencimiento=today + timedelta(days=5),
            ),
        ]

        db.add_all(sample_tasks)
        db.commit()
        print(f"Se insertaron {len(sample_tasks)} tareas de ejemplo.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
