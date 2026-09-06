import './globals.css';
import type { Metadata } from 'next';
import { Providers } from './providers';
import { AppShell } from '@/components/AppShell';

export const metadata: Metadata = {
  title: 'InsightForge — AI Data Analyst',
  description: 'Upload CSVs, ask questions, generate charts, and detect anomalies with Gemini AI and LangGraph.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <Providers>
          <AppShell>
            {children}
          </AppShell>
        </Providers>
      </body>
    </html>
  );
}
