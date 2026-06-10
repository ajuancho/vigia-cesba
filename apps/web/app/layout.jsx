import './globals.css';
import Providers from '@/components/Providers';

export const metadata = {
  title: 'Vigía — Inteligencia Legislativa Argentina',
  description:
    'Vigía — Plataforma de Inteligencia Legislativa y Regulatoria para Argentina. Monitoreo en tiempo real del Boletín Oficial, Congreso y normativa nacional.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600;700&family=Familjen+Grotesk:ital,wght@0,400..700;1,400..700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
