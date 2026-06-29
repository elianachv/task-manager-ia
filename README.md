# Gestor de Tareas

Aplicación web completa de gestión de tareas con backend **FastAPI** y frontend **HTML/CSS/JavaScript** vanilla, separados en carpetas independientes.

## Requisitos previos

- Python 3.11 o superior
- `pip` y `venv`
- Navegador web moderno

## Estructura del proyecto

```text
task-manager/
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   │   └── 001_initial.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── app/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── enums.py
│   │   └── main.py
│   ├── tests/
│   │   └── test_tasks.py
│   ├── .env.example
│   ├── alembic.ini
│   ├── requirements.txt
│   └── seed.py
├── frontend/
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── api.js
│   │   └── app.js
│   └── index.html
├── .gitignore
├── run.py
├── start.sh
├── start.bat
├── start.command
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── TESTING.md
└── README.md
```

## Instalación paso a paso

### 1. Backend

```bash
cd task-manager/backend
python3 -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Base de datos (opcional con Alembic)

La aplicación crea las tablas automáticamente al iniciar. Si prefieres usar migraciones:

```bash
alembic upgrade head
```

### 3. Datos de prueba (opcional)

```bash
python seed.py
```

## Cómo ejecutar

### Opción rápida (recomendada)

Un solo comando levanta backend, frontend y abre el navegador automáticamente.

**macOS / Linux:**

```bash
cd task-manager
python3 run.py
```

O bien:

```bash
./start.sh
```

**macOS (doble clic):** abre `start.command`

**Windows:** doble clic en `start.bat` o ejecuta:

```bat
python run.py
```

El lanzador hace automáticamente:

1. Crea el entorno virtual si no existe
2. Instala dependencias la primera vez
3. Crea `.env` desde `.env.example` si falta
4. Inicia API en http://127.0.0.1:8000
5. Inicia frontend en http://127.0.0.1:8080
6. Abre el navegador

Para detener todo: `Ctrl+C` en la terminal.

### Ejecución manual (paso a paso)

#### Backend

Desde `task-manager/backend` con el entorno virtual activado:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

URLs locales:

- API: http://localhost:8000
- Documentación Swagger: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Frontend

Desde `task-manager/frontend` en otra terminal:

```bash
python3 -m http.server 8080
```

URL local del frontend: http://localhost:8080

> El backend tiene CORS habilitado para `http://localhost:8080` y `http://127.0.0.1:8080`.

## API REST

| Método | Endpoint        | Descripción              |
|--------|-----------------|--------------------------|
| POST   | `/tasks`        | Crear tarea              |
| GET    | `/tasks`        | Listar tareas            |
| GET    | `/tasks/{id}`   | Obtener tarea por ID     |
| PUT    | `/tasks/{id}`   | Actualizar tarea         |
| DELETE | `/tasks/{id}`   | Eliminar tarea           |

### Campos de una tarea

- `id` (autogenerado)
- `fecha_creacion`
- `fecha_vencimiento`
- `nombre` (obligatorio)
- `descripcion`
- `estado`: `pendiente`, `en progreso`, `finalizada`
- `responsable`

### Filtros (`GET /tasks`)

| Parámetro            | Descripción                          |
|----------------------|--------------------------------------|
| `responsable`        | Filtra por responsable (parcial)     |
| `estado`             | Filtra por estado                    |
| `vencimiento_desde`  | Vencimiento desde (YYYY-MM-DD)       |
| `vencimiento_hasta`  | Vencimiento hasta (YYYY-MM-DD)       |
| `creacion_desde`     | Creación desde (YYYY-MM-DD)          |
| `creacion_hasta`     | Creación hasta (YYYY-MM-DD)          |

### Ordenamiento (`GET /tasks`)

| Parámetro    | Valores                                      | Default          |
|--------------|----------------------------------------------|------------------|
| `sort_by`    | `nombre`, `fecha_creacion`, `fecha_vencimiento` | `fecha_creacion` |
| `sort_order` | `asc`, `desc`                                | `desc`           |

### Ejemplos de uso

```bash
# Listar tareas pendientes de Ana, ordenadas por vencimiento ascendente
curl "http://localhost:8000/tasks?responsable=Ana&estado=pendiente&sort_by=fecha_vencimiento&sort_order=asc"

# Crear tarea
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Revisar informe",
    "descripcion": "Informe mensual",
    "estado": "pendiente",
    "responsable": "Ana García",
    "fecha_vencimiento": "2026-07-15"
  }'

# Actualizar tarea
curl -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "en progreso"}'

# Eliminar tarea
curl -X DELETE http://localhost:8000/tasks/1
```

## Cómo probar

### Pruebas automatizadas

El entorno completo de pruebas está en `tests/` (unitarias, integración y E2E). Consulta **[TESTING.md](TESTING.md)** para instrucciones detalladas.

```bash
cd tests
source ../backend/venv/bin/activate
pip install -r requirements-test.txt
playwright install chromium   # solo para E2E
pytest -q
```

### Prueba manual end-to-end

1. Levanta backend y frontend.
2. Abre http://localhost:8080.
3. Crea una tarea desde el formulario.
4. Aplica filtros y ordenamiento.
5. Edita y elimina tareas desde la tabla.

## Validaciones

- `nombre` es obligatorio.
- `estado` solo acepta: `pendiente`, `en progreso`, `finalizada`.
- `fecha_vencimiento` no puede ser anterior a `fecha_creacion`.
- Errores devueltos con códigos HTTP apropiados (`400`, `404`, `422`).

## Decisiones técnicas

- **Capas separadas**: router → service → repository → model.
- **Pydantic** para validación de entrada/salida.
- **SQLAlchemy 2.0** con SQLite para simplicidad local.
- **Alembic** incluido para evolución de esquema.
- **CORS** configurable vía `.env`.
- Frontend desacoplado servido como archivos estáticos.

## Paleta de colores (frontend)

- Aguamarina (`#40e0d0`)
- Blanco (`#ffffff`)
- Grises (`#f5f7f8`, `#e5e7eb`, `#4b5563`, `#1f2937`)
