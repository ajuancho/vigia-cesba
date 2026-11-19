// Vocabulario de dominio (espejo de packages/shared/constants.py).
export const TIPOS_NORMA = {
  DNU: { label: 'DNU', color: '#A0175A', description: 'Decreto de Necesidad y Urgencia' },
  DECRETO: { label: 'Decreto', color: '#4DB4B0', description: 'Decreto del Poder Ejecutivo' },
  LEY: { label: 'Ley', color: '#1D1D1B', description: 'Ley sancionada por el Congreso' },
  RESOLUCION: { label: 'Resolución', color: '#E62580', description: 'Resolución ministerial' },
  DISPOSICION: { label: 'Disposición', color: '#8F82BA', description: 'Disposición administrativa' },
  PROYECTO: { label: 'Proyecto', color: '#D3D93A', description: 'Expediente de la Legislatura porteña' },
  SENTENCIA: { label: 'Sentencia', color: '#5C5C57', description: 'Resolución del Tribunal Superior de Justicia' },
  COMUNICACION: { label: 'Comunicación', color: '#6E6E68', description: 'Comunicación del BCRA (serie A)' },
  CONSULTA: { label: 'Consulta', color: '#B4B4AE', description: 'Consulta pública / anteproyecto en consulta' },
  OTRA: { label: 'Otra', color: '#93938D', description: 'Otra norma' },
};

export const JURISDICCIONES = [
  'Nacional', 'Buenos Aires', 'CABA', 'Córdoba', 'Santa Fe', 'Mendoza', 'Tucumán', 'Entre Ríos',
];

export const SECTORES = [
  'Economía', 'Energía', 'Salud', 'Educación', 'Justicia', 'Trabajo', 'Ambiente', 'Tecnología',
  'Comercio', 'Transporte', 'Minería', 'Agro', 'Defensa', 'Seguridad',
];

// Fuentes de la instancia (vigia_shared.fuentes). Vacío en un filtro = todas.
export const FUENTES = {
  boletin: 'Boletín Oficial',
  legislatura: 'Legislatura',
  tsj: 'Tribunal Superior',
};

// Tipos que aplican a la Ciudad (los nacionales — BCRA, consultas — quedan fuera).
export const TIPOS_CABA = ['DNU', 'DECRETO', 'LEY', 'RESOLUCION', 'DISPOSICION', 'PROYECTO', 'SENTENCIA', 'OTRA'];
