"""Pruebas E2E de interfaz con Playwright (CP-17 a CP-22)."""

from datetime import timedelta

import pytest
from playwright.sync_api import Page, expect


def _fill_task_form(
    page: Page,
    *,
    nombre: str,
    responsable: str = "Tester UI",
    estado: str = "pendiente",
    fecha_creacion: str,
    fecha_vencimiento: str,
    descripcion: str = "Tarea creada desde E2E",
) -> None:
    page.fill("#nombre", nombre)
    page.fill("#responsable", responsable)
    page.select_option("#estado", estado)
    page.fill("#fecha_creacion", fecha_creacion)
    page.fill("#fecha_vencimiento", fecha_vencimiento)
    page.fill("#descripcion", descripcion)


def _task_names(page: Page) -> list[str]:
    return page.locator("#tasks-table-body tr td:nth-child(2) strong").all_text_contents()


@pytest.mark.e2e
def test_cp17_crear_tarea_desde_interfaz(app_page: Page, today) -> None:
    """CP-17: Crear tarea desde interfaz."""
    task_name = "Tarea E2E Crear"
    _fill_task_form(
        app_page,
        nombre=task_name,
        fecha_creacion=today.isoformat(),
        fecha_vencimiento=(today + timedelta(days=4)).isoformat(),
    )
    app_page.click("#submit-btn")
    app_page.locator("#tasks-table-body").filter(has_text=task_name).wait_for(state="visible")

    expect(app_page.locator("#tasks-table-body")).to_contain_text(task_name)


@pytest.mark.e2e
def test_cp18_validaciones_ui_en_formulario(app_page: Page, today) -> None:
    """CP-18: Validaciones UI en formulario."""
    app_page.fill("#nombre", "   ")
    app_page.fill("#fecha_creacion", today.isoformat())
    app_page.fill("#fecha_vencimiento", (today - timedelta(days=1)).isoformat())
    app_page.click("#submit-btn")

    alert = app_page.locator("#alert")
    expect(alert).to_be_visible()
    expect(alert).to_contain_text("obligatorio")


@pytest.mark.e2e
def test_cp19_editar_tarea_desde_interfaz(app_page: Page, ui_seed_tasks: list[dict]) -> None:
    """CP-19: Editar tarea desde interfaz."""
    task = ui_seed_tasks[0]
    row = app_page.locator(f"#tasks-table-body button[data-action='edit'][data-id='{task['id']}']")
    row.click()

    expect(app_page.locator("#form-title")).to_contain_text(f"Editar tarea #{task['id']}")
    app_page.fill("#nombre", "Alpha UI Editada")
    app_page.select_option("#estado", "en progreso")
    app_page.click("#submit-btn")

    alert = app_page.locator("#alert")
    expect(alert).to_contain_text("Tarea actualizada correctamente")
    expect(app_page.locator("#tasks-table-body")).to_contain_text("Alpha UI Editada")


@pytest.mark.e2e
def test_cp20_eliminar_tarea_desde_interfaz(app_page: Page, ui_seed_tasks: list[dict]) -> None:
    """CP-20: Eliminar tarea desde interfaz."""
    task = ui_seed_tasks[1]
    app_page.once("dialog", lambda dialog: dialog.accept())

    app_page.locator(f"#tasks-table-body button[data-action='delete'][data-id='{task['id']}']").click()

    alert = app_page.locator("#alert")
    expect(alert).to_contain_text("Tarea eliminada correctamente")
    expect(app_page.locator("#tasks-table-body")).not_to_contain_text(task["nombre"])


@pytest.mark.e2e
def test_cp21_filtrar_tareas_desde_interfaz(app_page: Page, ui_seed_tasks: list[dict]) -> None:
    """CP-21: Filtrar tareas desde interfaz."""
    app_page.fill("#filter-responsable", "Ana UI")
    app_page.select_option("#filter-estado", "pendiente")
    app_page.click("#filters-form button[type='submit']")
    app_page.wait_for_function(
        "() => document.querySelectorAll('#tasks-table-body tr td:nth-child(2) strong').length === 1"
    )

    names = _task_names(app_page)
    assert names == ["Alpha UI"]


@pytest.mark.e2e
def test_cp22_ordenar_tareas_desde_interfaz(app_page: Page, ui_seed_tasks: list[dict]) -> None:
    """CP-22: Ordenar tareas desde interfaz."""
    app_page.select_option("#sort-by", "nombre")
    app_page.select_option("#sort-order", "asc")
    app_page.click("#filters-form button[type='submit']")
    app_page.wait_for_function(
        """() => {
            const names = Array.from(document.querySelectorAll('#tasks-table-body tr td:nth-child(2) strong'))
              .map(el => el.textContent.trim());
            return names.length === 3 && names[0] === 'Alpha UI' && names[2] === 'Zebra UI';
        }"""
    )

    assert _task_names(app_page) == ["Alpha UI", "Beta UI", "Zebra UI"]

    app_page.select_option("#sort-order", "desc")
    app_page.click("#filters-form button[type='submit']")
    app_page.wait_for_function(
        """() => {
            const names = Array.from(document.querySelectorAll('#tasks-table-body tr td:nth-child(2) strong'))
              .map(el => el.textContent.trim());
            return names.length === 3 && names[0] === 'Zebra UI';
        }"""
    )

    assert _task_names(app_page) == ["Zebra UI", "Beta UI", "Alpha UI"]
