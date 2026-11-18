export const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/$/, '');
export const BACKEND_ORIGIN = (import.meta.env.VITE_BACKEND_URL || API_URL.replace(/\/api$/, '')).replace(/\/$/, '');
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

export function validarRutChileno(rut) {
  const limpio = String(rut || '').toUpperCase().replace(/[.\s]/g, '');
  if (!/^\d{7,8}-[\dK]$/.test(limpio)) {
    return 'Formato de RUT inválido (ej: 18456789-K).';
  }
  const [cuerpo, dv] = limpio.split('-');
  let suma = 0;
  let multiplo = 2;
  for (let i = cuerpo.length - 1; i >= 0; i -= 1) {
    suma += Number(cuerpo[i]) * multiplo;
    multiplo = multiplo === 7 ? 2 : multiplo + 1;
  }
  const resto = 11 - (suma % 11);
  const esperado = resto === 11 ? '0' : resto === 10 ? 'K' : String(resto);
  if (dv !== esperado) {
    return `RUT inválido (dígito verificador debería ser -${esperado}).`;
  }
  return '';
}

export function validarEmail(email) {
  const val = String(email || '').trim();
  if (!val) {
    return '';
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(val)) {
    return 'Correo electrónico inválido (ej: tutor@correo.cl).';
  }
  return '';
}

export function whatsappUrl(telefono, mensaje = '') {
  let digits = String(telefono || '').replace(/\D/g, '');
  if (digits.length === 9 && digits.startsWith('9')) {
    digits = `56${digits}`;
  }
  if (digits.length < 8) {
    return '';
  }
  const query = mensaje ? `?text=${encodeURIComponent(mensaje)}` : '';
  return `https://wa.me/${digits}${query}`;
}
