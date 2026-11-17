export const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/$/, '');
export const S3_STATIC_URL = (import.meta.env.VITE_S3_STATIC_URL || '').replace(/\/$/, '');

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

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data.detail || `Error HTTP ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return data;
}
