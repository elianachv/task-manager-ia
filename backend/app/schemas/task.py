from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.enums import TaskStatus


class SortByField(str, Enum):
    nombre = "nombre"
    fecha_creacion = "fecha_creacion"
    fecha_vencimiento = "fecha_vencimiento"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class TaskBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    descripcion: str | None = Field(default=None, max_length=2000)
    estado: TaskStatus = TaskStatus.pendiente
    responsable: str | None = Field(default=None, max_length=120)
    fecha_vencimiento: date

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("El nombre es obligatorio")
        return cleaned


class TaskCreate(TaskBase):
    fecha_creacion: date | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "TaskCreate":
        creation = self.fecha_creacion or date.today()
        if self.fecha_vencimiento < creation:
            raise ValueError(
                "La fecha de vencimiento no puede ser anterior a la fecha de creación"
            )
        self.fecha_creacion = creation
        return self


class TaskUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    descripcion: str | None = Field(default=None, max_length=2000)
    estado: TaskStatus | None = None
    responsable: str | None = Field(default=None, max_length=120)
    fecha_creacion: date | None = None
    fecha_vencimiento: date | None = None

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("El nombre es obligatorio")
        return cleaned

    @model_validator(mode="after")
    def validate_dates(self) -> "TaskUpdate":
        if self.fecha_creacion and self.fecha_vencimiento:
            if self.fecha_vencimiento < self.fecha_creacion:
                raise ValueError(
                    "La fecha de vencimiento no puede ser anterior a la fecha de creación"
                )
        return self


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha_creacion: date
    fecha_vencimiento: date
    nombre: str
    descripcion: str | None
    estado: TaskStatus
    responsable: str | None


class TaskListFilters(BaseModel):
    responsable: str | None = None
    estado: TaskStatus | None = None
    vencimiento_desde: date | None = None
    vencimiento_hasta: date | None = None
    creacion_desde: date | None = None
    creacion_hasta: date | None = None
    sort_by: SortByField = SortByField.fecha_creacion
    sort_order: SortOrder = SortOrder.desc

    @model_validator(mode="after")
    def validate_ranges(self) -> "TaskListFilters":
        if (
            self.vencimiento_desde
            and self.vencimiento_hasta
            and self.vencimiento_desde > self.vencimiento_hasta
        ):
            raise ValueError(
                "vencimiento_desde no puede ser posterior a vencimiento_hasta"
            )
        if (
            self.creacion_desde
            and self.creacion_hasta
            and self.creacion_desde > self.creacion_hasta
        ):
            raise ValueError(
                "creacion_desde no puede ser posterior a creacion_hasta"
            )
        return self


class ErrorResponse(BaseModel):
    detail: str


SortByLiteral = Literal["nombre", "fecha_creacion", "fecha_vencimiento"]
SortOrderLiteral = Literal["asc", "desc"]
