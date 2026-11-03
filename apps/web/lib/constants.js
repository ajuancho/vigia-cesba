// Vocabulario de dominio (espejo de packages/shared/constants.py).
export const TIPOS_NORMA = {
  DNU: { label: 'DNU', color: '#153B70', description: 'Decreto de Necesidad y Urgencia' },
  DECRETO: { label: 'Decreto', color: '#0079DC', description: 'Decreto del Poder Ejecutivo' },
  LEY: { label: 'Ley', color: '#18596C', description: 'Ley sancionada por el Congreso' },
  RESOLUCION: { label: 'Resolución', color: '#18A6C2', description: 'Resolución ministerial' },
  DISPOSICION: { label: 'Disposición', color: '#4E83FB', description: 'Disposición administrativa' },
  PROYECTO: { label: 'Proyecto', color: '#54BBC7', description: 'Expediente de la Legislatura porteña' },
  COMUNICACION: { label: 'Comunicación', color: '#00B2D1', description: 'Comunicación del BCRA (serie A)' },
  CONSULTA: { label: 'Consulta', color: '#7FB8C9', description: 'Consulta pública / anteproyecto en consulta' },
  OTRA: { label: 'Otra', color: '#93989E', description: 'Otra norma' },
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
};

// Tipos que aplican a la Ciudad (los nacionales — BCRA, consultas — quedan fuera).
export const TIPOS_CABA = ['DNU', 'DECRETO', 'LEY', 'RESOLUCION', 'DISPOSICION', 'PROYECTO', 'OTRA'];
