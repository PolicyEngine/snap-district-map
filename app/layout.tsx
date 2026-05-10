import type { Metadata, Viewport } from 'next';
import PolicyEngineHeader from './components/PolicyEngineHeader';
import './globals.css';

const TITLE = 'SNAP Benefits by Congressional District | PolicyEngine';
const DESCRIPTION =
  'Interactive map of Supplemental Nutrition Assistance Program (SNAP) benefits by U.S. congressional district.';

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
};

export const viewport: Viewport = {
  themeColor: '#2C6496',
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <PolicyEngineHeader />
        {children}
      </body>
    </html>
  );
}
