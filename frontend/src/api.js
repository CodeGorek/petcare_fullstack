export const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/$/, '');
export const BACKEND_ORIGIN = API_URL.replace(/\/api$/, '');
export const S3_STATIC_URL = (import.meta.env.VITE_S3_STATIC_URL || '').replace(/\/$/, '');

function formatApiError(data, status) {
  if (!data || typeof data !== 'object') {
    return `Error HTTP ${status}`;
  }
  if (typeof data.detail === 'string') {
    return data.detail;
  }
  const messages = [];
  for (const [field, val] of Object.entries(data)) {
    const text = Array.isArray(val) ? val.join(', ') : String(val);
    messages.push(field === 'non_field_errors' ? text : `${field}: ${text}`);
  }
  return messages.length ? messages.join(' · ') : `Error HTTP ${status}`;
}

export async function apiRequest(endpoint, { method = 'GET', token = '', body = null } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers.Authorization = `Token ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
  });

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(formatApiError(data, response.status));
    error.status = response.status;
    throw error;
  }
  return data;
}

export function formatClp(valor) {
  return `$${Number(valor || 0).toLocaleString('es-CL')}`;
}
