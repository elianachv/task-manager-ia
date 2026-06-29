#!/usr/bin/env python3
"""
Lanzador de un solo clic para el Gestor de Tareas.
Crea el entorno virtual si no existe, instala dependencias,
levanta backend + frontend y abre el navegador.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
VENV_DIR = BACKEND / "venv"
REQUIREMENTS = BACKEND / "requirements.txt"
ENV_FILE = BACKEND / ".env"
ENV_EXAMPLE = BACKEND / ".env.example"

API_HOST = "127.0.0.1"
API_PORT = 8000
WEB_PORT = 8080
API_URL = f"http://{API_HOST}:{API_PORT}"
WEB_URL = f"http://{API_HOST}:{WEB_PORT}"

processes: list[subprocess.Popen] = []


def log(message: str) -> None:
    print(f"[launcher] {message}", flush=True)


def venv_python() -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def venv_uvicorn() -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "uvicorn.exe"
    return VENV_DIR / "bin" / "uvicorn"


def ensure_venv() -> Path:
    python = venv_python()
    if python.exists():
        return python

    log("Creando entorno virtual...")
    subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
    return venv_python()


def ensure_dependencies(python: Path) -> None:
    uvicorn = venv_uvicorn()
    if uvicorn.exists():
        return

    log("Instalando dependencias del backend (solo la primera vez)...")
    subprocess.run(
        [str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)],
        cwd=BACKEND,
        check=True,
    )


def ensure_env_file() -> None:
    if ENV_FILE.exists() or not ENV_EXAMPLE.exists():
        return
    shutil.copy(ENV_EXAMPLE, ENV_FILE)
    log("Archivo .env creado desde .env.example")


def start_backend(python: Path) -> subprocess.Popen:
    log(f"Iniciando backend en {API_URL} ...")
    return subprocess.Popen(
        [
            str(python),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            API_HOST,
            "--port",
            str(API_PORT),
        ],
        cwd=BACKEND,
    )


def start_frontend(python: Path) -> subprocess.Popen:
    log(f"Iniciando frontend en {WEB_URL} ...")
    return subprocess.Popen(
        [str(python), "-m", "http.server", str(WEB_PORT), "--bind", API_HOST],
        cwd=FRONTEND,
    )


def wait_for_backend(timeout_seconds: int = 30) -> bool:
    health_url = f"{API_URL}/health"
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=2) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.5)

    return False


def stop_processes() -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()

    for process in processes:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def handle_shutdown(signum: int, _frame) -> None:
    log("Deteniendo servicios...")
    stop_processes()
    sys.exit(0)


def main() -> int:
    if not BACKEND.exists() or not FRONTEND.exists():
        log("No se encontraron las carpetas backend/ y frontend/.")
        return 1

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    try:
        python = ensure_venv()
        ensure_dependencies(python)
        ensure_env_file()

        processes.append(start_backend(python))
        processes.append(start_frontend(python))

        if not wait_for_backend():
            log("El backend no respondió a tiempo.")
            stop_processes()
            return 1

        log("Aplicación lista.")
        log(f"Frontend: {WEB_URL}")
        log(f"API:      {API_URL}")
        log("Presiona Ctrl+C para detener.")

        webbrowser.open(WEB_URL)

        while True:
            for process in processes:
                code = process.poll()
                if code is not None:
                    log(f"Un servicio terminó inesperadamente (código {code}).")
                    stop_processes()
                    return code or 1
            time.sleep(1)

    except subprocess.CalledProcessError as exc:
        log(f"Error durante la preparación: {exc}")
        stop_processes()
        return exc.returncode or 1
    except KeyboardInterrupt:
        handle_shutdown(signal.SIGINT, None)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
