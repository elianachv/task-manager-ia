const API_BASE_URL = window.API_BASE_URL || "http://localhost:8000";

async function parseError(response) {
  try {
    const data = await response.json();
    if (typeof data.detail === "string") {
      return data.detail;
    }
    if (Array.isArray(data.detail)) {
      return data.detail.map((item) => item.msg || JSON.stringify(item)).join(", ");
    }
    return "Ocurrió un error inesperado";
  } catch {
    return `Error HTTP ${response.status}`;
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const message = await parseError(response);
    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

const TasksAPI = {
  baseUrl: API_BASE_URL,

  list(filters = {}) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        params.append(key, value);
      }
    });
    const query = params.toString();
    return request(`/tasks${query ? `?${query}` : ""}`);
  },

  getById(id) {
    return request(`/tasks/${id}`);
  },

  create(payload) {
    return request("/tasks", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  update(id, payload) {
    return request(`/tasks/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  delete(id) {
    return request(`/tasks/${id}`, {
      method: "DELETE",
    });
  },
};

window.TasksAPI = TasksAPI;
