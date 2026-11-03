'use client';

// Flag público: ¿está activada la auth? (lo setea el deploy con NEXT_PUBLIC_AUTH_ENABLED).
export const AUTH_ENABLED = process.env.NEXT_PUBLIC_AUTH_ENABLED === 'true';

import { API_BASE } from '@/lib/api';

// Error de la API con el status HTTP y el `detail` de FastAPI (status 0 = no hubo
// respuesta: red caída, CORS o servidor inaccesible).
export class ApiError extends Error {
  constructor(status, path, detail) {
    super(status ? `API ${status} en ${path}${detail ? ` (${detail})` : ''}` : `No se pudo conectar con la API (${path})`);
    this.status = status;
    this.path = path;
    this.detail = detail;
  }
}

async function authedRequest(apiJwt, path, init) {
  const headers = new Headers(init.headers || {});
  if (apiJwt) headers.set('Authorization', `Bearer ${apiJwt}`);
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...init, headers, cache: 'no-store' });
  } catch {
    throw new ApiError(0, path);
  }
  if (!res.ok) {
    let detail;
    try { detail = (await res.json())?.detail; } catch { /* cuerpo no JSON */ }
    throw new ApiError(res.status, path, typeof detail === 'string' ? detail : undefined);
  }
  return res;
}

// Fetch autenticado para endpoints de workspace (usa el apiJwt de la sesión NextAuth).
export async function authedFetch(apiJwt, path, init = {}) {
  const res = await authedRequest(apiJwt, path, init);
  return res.status === 204 ? null : res.json();
}

// Variante que devuelve un Blob (descargas: CSV de reportes).
export async function authedFetchBlob(apiJwt, path, init = {}) {
  const res = await authedRequest(apiJwt, path, init);
  return res.blob();
}
