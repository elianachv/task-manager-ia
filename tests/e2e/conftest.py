"""Fixtures para pruebas E2E: levanta backend y frontend con DB temporal."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Generator
from datetime import date, timedelta
from pathlib import Path

import pytest
from playwright.sync_api import Page

from reporting import REPORTS_DIR

TASK_MANAGER_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = TASK_MANAGER_ROOT / "backend"
FRONTEND_DIR = TASK_MANAGER_ROOT / "frontend"

API_PORT = 18000
WEB_PORT = 18080

e2e_logger = logging.getLogger("task_manager.tests.e2e")


def _python_executable() -> str:
    if sys.platform == "win32":
        venv_python = BACKEND_DIR / "venv" / "Scripts" / "python.exe"
    else:
        venv_python = BACKEND_DIR / "venv" / "bin" / "python"
    return str(venv_python) if venv_python.exists() else sys.executable


def _wait_for_url(url: str, timeout_seconds: float = 45.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.5)
    raise RuntimeError(f"No se pudo conectar a {url}")


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args: dict) -> dict:
    """Navegador visible por defecto para observar las pruebas E2E."""
    headless = os.getenv("E2E_HEADLESS", "false").lower() in {"1", "true", "yes"}
    slow_mo = int(os.getenv("E2E_SLOW_MO", "350"))
    e2e_logger.info(
        "Playwright: headless=%s, slow_mo=%sms (usa E2E_HEADLESS=true para ocultar)",
        headless,
        slow_mo,
    )
    return {
        **browser_type_launch_args,
        "headless": headless,
        "slow_mo": slow_mo,
    }


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    return {
        **browser_context_args,
        "viewport": {"width": 1360, "height": 900},
    }


@pytest.fixture(scope="session")
def e2e_servers() -> Generator[dict[str, str], None, None]:
    """Levanta API y frontend en procesos aislados con SQLite temporal."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["CORS_ORIGINS"] = f"http://127.0.0.1:{WEB_PORT}"

    python = _python_executable()
    api_url = f"http://127.0.0.1:{API_PORT}"
    web_url = f"http://127.0.0.1:{WEB_PORT}"

    backend_log = open(REPORTS_DIR / "e2e_backend.log", "w", encoding="utf-8")
    frontend_log = open(REPORTS_DIR / "e2e_frontend.log", "w", encoding="utf-8")

    e2e_logger.info("Iniciando backend E2E en %s", api_url)
    e2e_logger.info("Iniciando frontend E2E en %s", web_url)
    e2e_logger.info("Base de datos temporal: %s", db_path)

    backend_proc = subprocess.Popen(
        [
            python,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(API_PORT),
            "--log-level",
            "info",
        ],
        cwd=BACKEND_DIR,
        env=env,
        stdout=backend_log,
        stderr=subprocess.STDOUT,
    )
    frontend_proc = subprocess.Popen(
        [python, "-m", "http.server", str(WEB_PORT), "--bind", "127.0.0.1"],
        cwd=FRONTEND_DIR,
        stdout=frontend_log,
        stderr=subprocess.STDOUT,
    )

    try:
        _wait_for_url(f"{api_url}/health")
        _wait_for_url(web_url)
        e2e_logger.info("Servidores E2E listos. Abriendo navegador visible...")
        yield {"api_url": api_url, "web_url": web_url, "db_path": db_path}
    finally:
        e2e_logger.info("Deteniendo servidores E2E")
        for proc in (backend_proc, frontend_proc):
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        backend_log.close()
        frontend_log.close()
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture()
def app_page(page: Page, e2e_servers: dict[str, str]) -> Page:
    """Abre la app configurando la URL de API antes de cargar scripts."""
    page.add_init_script(f"window.API_BASE_URL = '{e2e_servers['api_url']}';")
    e2e_logger.info("Navegando a %s", e2e_servers["web_url"])
    page.goto(e2e_servers["web_url"])
    page.wait_for_selector("#task-form")
    return page


@pytest.fixture(autouse=True)
def e2e_clean_state(app_page: Page, e2e_servers: dict[str, str]) -> Generator[None, None, None]:
    """Limpia tareas y recarga la UI antes de cada prueba E2E."""
    e2e_logger.info("Limpiando estado E2E antes del test")
    response = app_page.request.get(f"{e2e_servers['api_url']}/tasks")
    if response.ok:
        for task in response.json():
            app_page.request.delete(f"{e2e_servers['api_url']}/tasks/{task['id']}")

    app_page.reload()
    app_page.wait_for_selector("#task-form")
    yield


def seed_tasks_via_api(page: Page, api_url: str, tasks: list[dict]) -> list[dict]:
    """Crea tareas por API para preparar escenarios UI."""
    created: list[dict] = []
    for payload in tasks:
        e2e_logger.info("Semilla API: creando tarea '%s'", payload.get("nombre"))
        response = page.request.post(
            f"{api_url}/tasks",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
        )
        assert response.ok, response.text()
        created.append(response.json())
    return created


@pytest.fixture()
def today() -> date:
    return date.today()


@pytest.fixture()
def ui_seed_tasks(app_page: Page, e2e_servers: dict[str, str], today: date) -> list[dict]:
    created = seed_tasks_via_api(
        app_page,
        e2e_servers["api_url"],
        [
            {
                "nombre": "Alpha UI",
                "estado": "pendiente",
                "responsable": "Ana UI",
                "fecha_creacion": (today - timedelta(days=3)).isoformat(),
                "fecha_vencimiento": (today + timedelta(days=2)).isoformat(),
            },
            {
                "nombre": "Beta UI",
                "estado": "en progreso",
                "responsable": "Luis UI",
                "fecha_creacion": (today - timedelta(days=2)).isoformat(),
                "fecha_vencimiento": (today + timedelta(days=8)).isoformat(),
            },
            {
                "nombre": "Zebra UI",
                "estado": "finalizada",
                "responsable": "Ana UI",
                "fecha_creacion": (today - timedelta(days=1)).isoformat(),
                "fecha_vencimiento": (today + timedelta(days=15)).isoformat(),
            },
        ],
    )
    app_page.click("#refresh-btn")
    app_page.wait_for_selector("#tasks-table-body tr td")
    return created
