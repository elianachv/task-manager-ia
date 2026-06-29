from enum import Enum


class TaskStatus(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en progreso"
    finalizada = "finalizada"
