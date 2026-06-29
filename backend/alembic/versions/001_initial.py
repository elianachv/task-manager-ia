"""initial tasks table

Revision ID: 001_initial
Revises:
Create Date: 2026-06-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fecha_creacion", sa.Date(), nullable=False),
        sa.Column("fecha_vencimiento", sa.Date(), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column(
            "estado",
            sa.Enum(
                "pendiente",
                "en progreso",
                "finalizada",
                name="task_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("responsable", sa.String(length=120), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tasks_estado"), "tasks", ["estado"], unique=False)
    op.create_index(op.f("ix_tasks_fecha_creacion"), "tasks", ["fecha_creacion"], unique=False)
    op.create_index(
        op.f("ix_tasks_fecha_vencimiento"), "tasks", ["fecha_vencimiento"], unique=False
    )
    op.create_index(op.f("ix_tasks_id"), "tasks", ["id"], unique=False)
    op.create_index(op.f("ix_tasks_nombre"), "tasks", ["nombre"], unique=False)
    op.create_index(op.f("ix_tasks_responsable"), "tasks", ["responsable"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tasks_responsable"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_nombre"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_fecha_vencimiento"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_fecha_creacion"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_estado"), table_name="tasks")
    op.drop_table("tasks")
