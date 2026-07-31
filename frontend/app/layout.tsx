import './globals.css';
import type { Metadata } from 'next';
import { Providers } from './providers';
import { Sidebar } from '@/components/Sidebar';

export const metadata: Metadata = {
  title: 'InsightForge — AI Data Analyst',
  description: 'Upload CSVs, ask questions, generate charts, and detect anomalies with Gemini AI.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <Providers>
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 overflow-auto">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
