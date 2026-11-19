// Detección de nombres de fuente en el texto del buscador (espejo de
// vigia_shared.fuentes.quitar_fuentes). Las normas no dicen "boletín oficial"
// en su texto, así que buscar esas palabras no devuelve nada: se aplican como
// filtro de fuente y se quitan de la búsqueda.

const FRASES = [
  ['boletin oficial de la ciudad de buenos aires', 'boletin'],
  ['boletin oficial de la ciudad', 'boletin'],
  ['boletin oficial', 'boletin'],
  ['bocba', 'boletin'],
  ['boletin', 'boletin'],
  ['legislatura portena', 'legislatura'],
  ['legislatura de la ciudad', 'legislatura'],
  ['legislatura', 'legislatura'],
  ['tribunal superior de justicia', 'tsj'],
  ['tribunal superior', 'tsj'],
  ['tsj', 'tsj'],
  ['sentencias', 'tsj'],
];
const CONECTORES = 'en|del|de|la|el|los|las|por|y|o';

const plano = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
const escapar = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

/**
 * "vivienda boletín oficial" → { fuente: 'boletin', texto: 'vivienda' }.
 * Toma la primera fuente nombrada; sin coincidencias → { fuente: null, texto }.
 */
export function detectarFuente(texto) {
  const original = texto || '';
  let base = original;
  let p = plano(base);
  if (p.length !== base.length) base = p; // caracteres combinados: trabajar sobre la versión plana
  for (const [frase, fuente] of FRASES) {
    const re = new RegExp(`(?:(?<![\\p{L}\\d])(?:${CONECTORES})\\s+)*(?<![\\p{L}\\d-])${escapar(frase)}(?![\\p{L}\\d])`, 'gu');
    if (!re.test(p)) continue;
    re.lastIndex = 0;
    let out = '';
    let prev = 0;
    for (const m of p.matchAll(re)) {
      out += `${base.slice(prev, m.index)} `;
      prev = m.index + m[0].length;
    }
    out += base.slice(prev);
    return { fuente, texto: out.replace(/\s+/g, ' ').trim() };
  }
  return { fuente: null, texto: original.trim() };
}
