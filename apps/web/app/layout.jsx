import './globals.css';
import Providers from '@/components/Providers';

const TITLE = 'Monitor Normativo CABA — CESBA';
const DESCRIPTION =
  'La normativa de la Ciudad de Buenos Aires, al día. Monitoreo del Boletín Oficial CABA y de los proyectos de la Legislatura porteña: búsqueda, alertas por email y reportes. Herramienta interna del CESBA.';

export const metadata = {
  metadataBase: new URL('https://normativa.cesba.gob.ar'),
  title: {
    default: TITLE,
    template: '%s · Monitor BOCBA',
  },
  description: DESCRIPTION,
  keywords: ['boletín oficial CABA', 'normativa CABA', 'BOCBA', 'Legislatura porteña', 'proyectos de ley CABA', 'legislación porteña', 'CESBA', 'Ciudad de Buenos Aires'],
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: 'https://normativa.cesba.gob.ar',
    siteName: 'Monitor Normativo CABA · CESBA',
    locale: 'es_AR',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: TITLE,
    description: DESCRIPTION,
  },
  robots: {
    index: false,
    follow: false,
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
