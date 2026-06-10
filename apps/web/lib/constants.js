// Vocabulario de dominio (espejo de packages/shared/constants.py).
export const TIPOS_NORMA = {
  DNU: { label: 'DNU', color: '#ef4444', description: 'Decreto de Necesidad y Urgencia' },
  DECRETO: { label: 'Decreto', color: '#f59e0b', description: 'Decreto del Poder Ejecutivo' },
  LEY: { label: 'Ley', color: '#10b981', description: 'Ley sancionada por el Congreso' },
  RESOLUCION: { label: 'Resolución', color: '#3b82f6', description: 'Resolución ministerial' },
  DISPOSICION: { label: 'Disposición', color: '#8b5cf6', description: 'Disposición administrativa' },
  PROYECTO: { label: 'Proyecto', color: '#06b6d4', description: 'Proyecto de ley en trámite' },
  COMUNICACION: { label: 'Comunicación', color: '#f472b6', description: 'Comunicación del BCRA (serie A)' },
  OTRA: { label: 'Otra', color: '#64748b', description: 'Otra norma' },
};

export const JURISDICCIONES = [
  'Nacional', 'Buenos Aires', 'CABA', 'Córdoba', 'Santa Fe', 'Mendoza', 'Tucumán', 'Entre Ríos',
];

export const SECTORES = [
  'Economía', 'Energía', 'Salud', 'Educación', 'Justicia', 'Trabajo', 'Ambiente', 'Tecnología',
  'Comercio', 'Transporte', 'Minería', 'Agro', 'Defensa', 'Seguridad',
];
