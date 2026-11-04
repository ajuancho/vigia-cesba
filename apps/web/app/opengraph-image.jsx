import { ImageResponse } from 'next/og';

/* Imagen OpenGraph (1200×630) — identidad CESBA: gradiente institucional,
   título en mayúsculas bold con bajada en minúsculas, barra de acento vital
   y la línea de pie institucional. */

export const alt = 'Monitor BOCBA — La normativa porteña, al día. Herramienta del CESBA.';
export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

const FONT_BASE = 'https://cdn.jsdelivr.net/fontsource/fonts';

async function loadFont(path) {
  const res = await fetch(`${FONT_BASE}/${path}`);
  if (!res.ok) throw new Error(`font ${path}: ${res.status}`);
  return res.arrayBuffer();
}

export default async function OpengraphImage() {
  const [bold, light, medium] = await Promise.all([
    loadFont('montserrat@latest/latin-700-normal.ttf'),
    loadFont('montserrat@latest/latin-300-normal.ttf'),
    loadFont('montserrat@latest/latin-500-normal.ttf'),
  ]);

  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          backgroundImage: 'linear-gradient(180deg, #1B9FC7 0%, #153B70 100%)',
          color: '#FFFFFF',
          fontFamily: 'Montserrat',
        }}
      >
        {/* Cuerpo */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '0 88px' }}>
          <div style={{ display: 'flex', fontWeight: 500, fontSize: 20, letterSpacing: 3, color: 'rgba(255,255,255,0.86)', marginBottom: 36 }}>
            CONSEJO ECONÓMICO Y SOCIAL DE LA CIUDAD DE BUENOS AIRES
          </div>
          <div style={{ display: 'flex', alignItems: 'stretch' }}>
            <div style={{ width: 10, backgroundColor: '#00FAB9', marginRight: 32 }} />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontWeight: 700, fontSize: 84, lineHeight: 1.02, letterSpacing: 2 }}>LA NORMATIVA PORTEÑA,</span>
              <span style={{ fontWeight: 700, fontSize: 84, lineHeight: 1.02, letterSpacing: 2 }}>AL DÍA</span>
              <span style={{ fontWeight: 300, fontSize: 34, marginTop: 22 }}>boletín oficial, legislatura y tribunal superior de la ciudad</span>
            </div>
          </div>
        </div>

        {/* Pie institucional */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 88px',
            height: 72,
            borderTop: '1px solid rgba(255,255,255,0.28)',
            fontWeight: 500,
            fontSize: 20,
            letterSpacing: 2,
          }}
        >
          <span>www.cesba.gob.ar</span>
          <span style={{ fontWeight: 700 }}>MONITOR BOCBA · CESBA</span>
        </div>
      </div>
    ),
    {
      ...size,
      fonts: [
        { name: 'Montserrat', data: bold, weight: 700, style: 'normal' },
        { name: 'Montserrat', data: light, weight: 300, style: 'normal' },
        { name: 'Montserrat', data: medium, weight: 500, style: 'normal' },
      ],
    }
  );
}
