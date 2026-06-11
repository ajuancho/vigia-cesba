// Cliente del API de Vigía. En el browser usa NEXT_PUBLIC_API_URL.
const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function qs(params) {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params || {})) {
    if (v !== undefined && v !== null && v !== '') sp.set(k, v);
  }
  const s = sp.toString();
  return s ? `?${s}` : '';
}

async function get(path) {
  const res = await fetch(`${BASE}${path}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`API ${res.status} en ${path}`);
  return res.json();
}

export const api = {
  listNormas: (params) => get(`/normas${qs(params)}`),
  getNorma: (id) => get(`/normas/${id}`),
  search: (params) => get(`/search${qs(params)}`),
  dashboard: () => get('/stats/dashboard'),
  dnuStats: () => get('/stats/dnu'),
  series: (params) => get(`/stats/series${qs(params)}`),
  organismos: (params) => get(`/stats/organismos${qs(params)}`),
  listAvisos: (params) => get(`/avisos${qs(params)}`),
  avisosRubros: (params) => get(`/avisos/rubros${qs(params)}`),
  universo: (params) => get(`/stats/universo${qs(params)}`),
};

export { BASE as API_BASE };
