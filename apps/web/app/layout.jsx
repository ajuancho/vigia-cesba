import './globals.css';
import Providers from '@/components/Providers';

const TITLE = 'Monitor Normativo · nuevosBAires';
const DESCRIPTION =
  'La normativa de la Ciudad de Buenos Aires, al día. Monitoreo del Boletín Oficial CABA, los proyectos de la Legislatura porteña y las sentencias del Tribunal Superior de Justicia: búsqueda, alertas por email y reportes. Un proyecto de nuevosBAires.';

export const metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'https://nuevosbaires.com.ar'),
  title: {
    default: TITLE,
    template: '%s · Monitor Normativo · nuevosBAires',
  },
  description: DESCRIPTION,
  keywords: ['boletín oficial CABA', 'normativa CABA', 'BOCBA', 'Legislatura porteña', 'proyectos de ley CABA', 'legislación porteña', 'nuevosBAires', 'Nuevos Baires', 'Ciudad de Buenos Aires'],
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: process.env.NEXT_PUBLIC_SITE_URL || 'https://nuevosbaires.com.ar',
    siteName: 'Monitor Normativo · nuevosBAires',
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
          href="https://fonts.googleapis.com/css2?family=Rethink+Sans:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
