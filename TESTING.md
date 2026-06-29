# Entorno de pruebas automatizadas — Gestor de Tareas

Guía para ejecutar pruebas **unitarias**, de **integración API** y **E2E/UI** del proyecto.

## Prerrequisitos

- Python 3.11 o superior
- Entorno virtual del backend creado (`backend/venv`)
- Dependencias del backend instaladas
- Para pruebas E2E: navegadores de Playwright

## Estructura de pruebas

```text
tests/
├── conftest.py              # Fixtures + hooks de logging e informe
├── reporting.py             # Generador de informes final
├── pytest.ini
├── run_tests.sh             # Script de ejecución recomendado
├── requirements-test.txt
├── reports/                 # Informes y logs generados
│   ├── ultimo_informe.txt
│   ├── ultimo_informe.html
│   └── pytest_session.log
```

## Instalación de dependencias de pruebas

Desde la raíz del proyecto (`task-manager/`):

```bash
cd backend
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r ../tests/requirements-test.txt
playwright install chromium       # Solo necesario para E2E
```

## Cómo ejecutar las pruebas

Todos los comandos se ejecutan desde `task-manager/tests/` con el venv activado.

### Ejecución recomendada (con logs e informe final)

```bash
cd tests
./run_tests.sh
```

Este comando:
- Muestra **logs en consola** por cada caso (inicio, resultado, duración)
- Genera un **informe final** en consola al terminar
- Guarda artefactos en `tests/reports/`:
  - `ultimo_informe.txt` — resumen legible
  - `ultimo_informe.html` — informe visual en navegador
  - `pytest_session.log` — log detallado de la sesión
  - `e2e_backend.log` / `e2e_frontend.log` — logs de servidores E2E
  - `informe_YYYYMMDD_HHMMSS.txt/html` — histórico por ejecución

### Todas las pruebas

```bash
cd tests
pytest -q
```

### Solo unitarias

```bash
pytest unit -q
# o por marcador
pytest -m unit -q
```

### Solo integración

```bash
pytest integration -q
# o
pytest -m integration -q
```

### Solo E2E (navegador visible)

Las pruebas E2E abren **Chromium en modo visible** para que puedas ver la interacción con la UI. La velocidad se reduce ligeramente (`slow_mo=350ms`) para facilitar la observación.

```bash
pytest e2e -q
# o
pytest -m e2e -q
```

Para ejecutar E2E sin ventana (CI/headless):

```bash
E2E_HEADLESS=true pytest e2e -q
```

Ajustar velocidad visual:

```bash
E2E_SLOW_MO=600 pytest e2e -q
```

### Modo verbose (depuración)

```bash
pytest -v
```

## Cobertura de casos de prueba

| ID | Tipo | Descripción |
|----|------|-------------|
| CP-01 | Unit | Crear tarea con datos válidos |
| CP-02 | Unit | Rechazar estado inválido |
| CP-03 | Unit | Rechazar fecha_vencimiento < fecha_creacion |
| CP-04 | Unit | Rechazar tarea sin nombre |
| CP-05 | Integration | POST /tasks crear tarea |
| CP-06 | Integration | GET /tasks listar tareas |
| CP-07 | Integration | GET /tasks/{id} existente |
| CP-08 | Integration | GET /tasks/{id} inexistente (404) |
| CP-09 | Integration | PUT /tasks/{id} actualizar tarea |
| CP-10 | Integration | DELETE /tasks/{id} eliminar tarea |
| CP-11 | Integration | Filtro por estado |
| CP-12 | Integration | Filtro por responsable |
| CP-13 | Integration | Filtro por rango fecha creación |
| CP-14 | Integration | Filtro por rango fecha vencimiento |
| CP-15 | Integration | Orden por nombre asc/desc |
| CP-16 | Integration | Orden por fechas asc/desc |
| CP-17 | E2E | Crear tarea desde interfaz |
| CP-18 | E2E | Validaciones UI en formulario |
| CP-19 | E2E | Editar tarea desde interfaz |
| CP-20 | E2E | Eliminar tarea desde interfaz |
| CP-21 | E2E | Filtrar tareas desde interfaz |
| CP-22 | E2E | Ordenar tareas desde interfaz |
| CP-23 | Integration | Manejo de payload inválido (422) |
| CP-24 | Integration | Persistencia/consistencia de datos |

## Aislamiento de base de datos

- **Unitarias / Integración:** SQLite en memoria (`sqlite://`) por test, sin tocar `backend/tasks.db`.
- **E2E:** SQLite temporal en archivo, levantado solo durante la sesión E2E.

## Solución de errores comunes

### `ModuleNotFoundError: No module named 'app'`

Ejecuta pytest desde `tests/` o usa la configuración incluida:

```bash
cd tests
pytest -q
```

`pytest.ini` ya define `pythonpath = ../backend`.

### `playwright._impl._errors.Error: Executable doesn't exist`

Instala navegadores:

```bash
playwright install chromium
```

### Puerto ocupado en E2E (18000 / 18080)

Cierra procesos previos:

```bash
lsof -ti:18000 | xargs kill -9
lsof -ti:18080 | xargs kill -9
```

### Fallos por CORS en E2E

Las pruebas E2E configuran `CORS_ORIGINS` automáticamente al levantar el backend temporal.

### `fastapi.testclient` deprecation warning

Es un aviso de Starlette/FastAPI reciente. No afecta la ejecución de las pruebas.

## Validación esperada

Al finalizar verás un informe como este:

```text
========================================================================
INFORME FINAL DE PRUEBAS — GESTOR DE TAREAS

Inicio:     2026-06-29 15:30:00
Fin:        2026-06-29 15:30:12
Duración:   12.45 s
Estado:     EXITOSO (código 0)

RESUMEN
  Total:    24
  Pasaron:  24
  Fallaron: 0
  ...
========================================================================

📄 Informe guardado en:
   - tests/reports/informe_YYYYMMDD_HHMMSS.txt
   - tests/reports/informe_YYYYMMDD_HHMMSS.html
```

## Nota sobre pruebas legacy

Existe un conjunto mínimo anterior en `backend/tests/`. El entorno oficial y completo de pruebas es `tests/` en la raíz del proyecto.
