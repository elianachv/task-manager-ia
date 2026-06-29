const elements = {
  alert: document.getElementById("alert"),
  apiUrlLabel: document.getElementById("api-url-label"),
  taskForm: document.getElementById("task-form"),
  formTitle: document.getElementById("form-title"),
  taskId: document.getElementById("task-id"),
  nombre: document.getElementById("nombre"),
  descripcion: document.getElementById("descripcion"),
  estado: document.getElementById("estado"),
  responsable: document.getElementById("responsable"),
  fechaCreacion: document.getElementById("fecha_creacion"),
  fechaVencimiento: document.getElementById("fecha_vencimiento"),
  submitBtn: document.getElementById("submit-btn"),
  cancelEditBtn: document.getElementById("cancel-edit-btn"),
  refreshBtn: document.getElementById("refresh-btn"),
  filtersForm: document.getElementById("filters-form"),
  clearFiltersBtn: document.getElementById("clear-filters-btn"),
  filterResponsable: document.getElementById("filter-responsable"),
  filterEstado: document.getElementById("filter-estado"),
  filterCreacionDesde: document.getElementById("filter-creacion-desde"),
  filterCreacionHasta: document.getElementById("filter-creacion-hasta"),
  filterVencimientoDesde: document.getElementById("filter-vencimiento-desde"),
  filterVencimientoHasta: document.getElementById("filter-vencimiento-hasta"),
  sortBy: document.getElementById("sort-by"),
  sortOrder: document.getElementById("sort-order"),
  tableBody: document.getElementById("tasks-table-body"),
};

function todayISO() {
  return new Date().toISOString().split("T")[0];
}

function showAlert(message, type = "success") {
  elements.alert.textContent = message;
  elements.alert.className = `alert alert-${type}`;
  elements.alert.classList.remove("hidden");
}

function hideAlert() {
  elements.alert.classList.add("hidden");
}

function statusClass(estado) {
  if (estado === "pendiente") return "status-pendiente";
  if (estado === "en progreso") return "status-en-progreso";
  return "status-finalizada";
}

function resetForm() {
  elements.taskForm.reset();
  elements.taskId.value = "";
  elements.fechaCreacion.value = todayISO();
  elements.fechaVencimiento.value = todayISO();
  elements.formTitle.textContent = "Nueva tarea";
  elements.submitBtn.textContent = "Crear tarea";
  elements.cancelEditBtn.classList.add("hidden");
}

function getFormPayload() {
  const payload = {
    nombre: elements.nombre.value.trim(),
    descripcion: elements.descripcion.value.trim() || null,
    estado: elements.estado.value,
    responsable: elements.responsable.value.trim() || null,
    fecha_vencimiento: elements.fechaVencimiento.value,
  };

  if (elements.fechaCreacion.value) {
    payload.fecha_creacion = elements.fechaCreacion.value;
  }

  return payload;
}

function validateForm(payload) {
  if (!payload.nombre) {
    throw new Error("El nombre es obligatorio");
  }
  if (!payload.fecha_vencimiento) {
    throw new Error("La fecha de vencimiento es obligatoria");
  }
  const creation = payload.fecha_creacion || todayISO();
  if (payload.fecha_vencimiento < creation) {
    throw new Error("La fecha de vencimiento no puede ser anterior a la fecha de creación");
  }
}

function getFilters() {
  return {
    responsable: elements.filterResponsable.value.trim(),
    estado: elements.filterEstado.value,
    creacion_desde: elements.filterCreacionDesde.value,
    creacion_hasta: elements.filterCreacionHasta.value,
    vencimiento_desde: elements.filterVencimientoDesde.value,
    vencimiento_hasta: elements.filterVencimientoHasta.value,
    sort_by: elements.sortBy.value,
    sort_order: elements.sortOrder.value,
  };
}

function renderTasks(tasks) {
  if (!tasks.length) {
    elements.tableBody.innerHTML = `
      <tr>
        <td colspan="7" class="empty-state">No hay tareas para los filtros seleccionados.</td>
      </tr>
    `;
    return;
  }

  elements.tableBody.innerHTML = tasks
    .map(
      (task) => `
        <tr>
          <td>${task.id}</td>
          <td>
            <strong>${escapeHtml(task.nombre)}</strong>
            ${task.descripcion ? `<div class="task-description">${escapeHtml(task.descripcion)}</div>` : ""}
          </td>
          <td>${escapeHtml(task.responsable || "-")}</td>
          <td><span class="status-badge ${statusClass(task.estado)}">${escapeHtml(task.estado)}</span></td>
          <td>${task.fecha_creacion}</td>
          <td>${task.fecha_vencimiento}</td>
          <td>
            <div class="actions">
              <button class="btn btn-secondary btn-small" data-action="edit" data-id="${task.id}">Editar</button>
              <button class="btn btn-danger btn-small" data-action="delete" data-id="${task.id}">Eliminar</button>
            </div>
          </td>
        </tr>
      `
    )
    .join("");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function loadTasks() {
  try {
    hideAlert();
    const tasks = await TasksAPI.list(getFilters());
    renderTasks(tasks);
  } catch (error) {
    showAlert(error.message, "error");
    elements.tableBody.innerHTML = `
      <tr>
        <td colspan="7" class="empty-state">No se pudieron cargar las tareas.</td>
      </tr>
    `;
  }
}

async function handleSubmit(event) {
  event.preventDefault();
  try {
    hideAlert();
    const payload = getFormPayload();
    validateForm(payload);
    const editingId = elements.taskId.value;

    if (editingId) {
      await TasksAPI.update(editingId, payload);
      showAlert("Tarea actualizada correctamente");
    } else {
      await TasksAPI.create(payload);
      showAlert("Tarea creada correctamente");
    }

    resetForm();
    await loadTasks();
  } catch (error) {
    showAlert(error.message, "error");
  }
}

async function handleTableClick(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;

  const taskId = button.dataset.id;
  const action = button.dataset.action;

  try {
    hideAlert();

    if (action === "edit") {
      const task = await TasksAPI.getById(taskId);
      elements.taskId.value = task.id;
      elements.nombre.value = task.nombre;
      elements.descripcion.value = task.descripcion || "";
      elements.estado.value = task.estado;
      elements.responsable.value = task.responsable || "";
      elements.fechaCreacion.value = task.fecha_creacion;
      elements.fechaVencimiento.value = task.fecha_vencimiento;
      elements.formTitle.textContent = `Editar tarea #${task.id}`;
      elements.submitBtn.textContent = "Guardar cambios";
      elements.cancelEditBtn.classList.remove("hidden");
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }

    if (action === "delete") {
      const confirmed = window.confirm(`¿Eliminar la tarea #${taskId}?`);
      if (!confirmed) return;
      await TasksAPI.delete(taskId);
      showAlert("Tarea eliminada correctamente");
      if (elements.taskId.value === taskId) {
        resetForm();
      }
      await loadTasks();
    }
  } catch (error) {
    showAlert(error.message, "error");
  }
}

function clearFilters() {
  elements.filtersForm.reset();
  elements.sortBy.value = "fecha_creacion";
  elements.sortOrder.value = "desc";
  loadTasks();
}

function init() {
  elements.apiUrlLabel.textContent = TasksAPI.baseUrl;
  resetForm();
  loadTasks();

  elements.taskForm.addEventListener("submit", handleSubmit);
  elements.filtersForm.addEventListener("submit", (event) => {
    event.preventDefault();
    loadTasks();
  });
  elements.clearFiltersBtn.addEventListener("click", clearFilters);
  elements.refreshBtn.addEventListener("click", loadTasks);
  elements.cancelEditBtn.addEventListener("click", resetForm);
  elements.tableBody.addEventListener("click", handleTableClick);
}

document.addEventListener("DOMContentLoaded", init);
