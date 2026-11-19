import { ImageResponse } from 'next/og';

/* Imagen OpenGraph (1200×630) — identidad nuevosBAires: fondo carbón (versión
   negativa del logo), las cuatro barras del isotipo, título en Rethink Sans
   Bold y la línea de pie con el sitio. */

export const alt = 'Monitor Normativo · nuevosBAires — La normativa porteña, al día.';
export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

const FONT_BASE = 'https://cdn.jsdelivr.net/fontsource/fonts';

async function loadFont(path) {
  const res = await fetch(`${FONT_BASE}/${path}`);
  if (!res.ok) throw new Error(`font ${path}: ${res.status}`);
  return res.arrayBuffer();
}

// Barras del isotipo: lima, magenta, turquesa, lavanda (alturas desiguales).
const BARRAS = [
  { color: '#D3D93A', alto: 520 },
  { color: '#E62580', alto: 322 },
  { color: '#4DB4B0', alto: 416 },
  { color: '#8F82BA', alto: 218 },
];

export default async function OpengraphImage() {
  const [bold, regular] = await Promise.all([
    loadFont('rethink-sans@latest/latin-700-normal.ttf'),
    loadFont('rethink-sans@latest/latin-400-normal.ttf'),
  ]);

  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: '#1D1D1B',
          color: '#FFFFFF',
          fontFamily: 'Rethink Sans',
          position: 'relative',
        }}
      >
        {/* Barras de la marca, ancladas abajo a la derecha */}
        <div style={{ position: 'absolute', right: 80, bottom: 72, display: 'flex', alignItems: 'flex-end', gap: 22 }}>
          {BARRAS.map((b) => (
            <div key={b.color} style={{ width: 78, height: b.alto, backgroundColor: b.color }} />
          ))}
        </div>

        {/* Cuerpo */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '0 88px', maxWidth: 780 }}>
          <div style={{ display: 'flex', fontSize: 24, letterSpacing: 4, color: 'rgba(255,255,255,0.86)', marginBottom: 36 }}>
            MONITOR NORMATIVO · NUEVOSBAIRES
          </div>
          <div style={{ display: 'flex', alignItems: 'stretch' }}>
            <div style={{ width: 10, backgroundColor: '#D3D93A', marginRight: 32 }} />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontWeight: 700, fontSize: 88, lineHeight: 1.02, letterSpacing: -2 }}>La normativa porteña,</span>
              <span style={{ fontWeight: 700, fontSize: 88, lineHeight: 1.02, letterSpacing: -2 }}>al día</span>
              <span style={{ fontWeight: 400, fontSize: 32, marginTop: 22, color: 'rgba(255,255,255,0.86)' }}>
                boletín oficial, legislatura y tribunal superior
              </span>
            </div>
          </div>
        </div>

        {/* Pie */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 88px',
            height: 72,
            borderTop: '1px solid rgba(255,255,255,0.28)',
            fontSize: 22,
            backgroundColor: '#1D1D1B',
          }}
        >
          <span style={{ fontWeight: 700 }}>nuevosBAires</span>
          <span>nuevosbaires.com.ar</span>
        </div>
      </div>
    ),
    {
      ...size,
      fonts: [
        { name: 'Rethink Sans', data: bold, weight: 700, style: 'normal' },
        { name: 'Rethink Sans', data: regular, weight: 400, style: 'normal' },
      ],
    }
  );
}
