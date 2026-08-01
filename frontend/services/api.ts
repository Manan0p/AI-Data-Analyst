import { Analysis, Dataset, Profile } from '@/types';

const base = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' ? '/api' : 'http://localhost:8000/api');

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(base + path, init);
  if (!r.ok) {
    const body = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(body.detail ?? r.statusText);
  }
  return r.json();
}

export const api = {
  datasets: () => request<Dataset[]>('/datasets'),

  upload: (files: File[]) => {
    const body = new FormData();
    files.forEach(f => body.append('files', f));
    return request<Dataset[]>('/upload', { method: 'POST', body });
  },

  profile: (id: string) => request<Profile>(`/datasets/${id}/profile`),

  rows: (id: string, search = '') =>
    request<{ rows: Record<string, unknown>[]; total: number; columns: string[] }>(
      `/datasets/${id}/rows?search=${encodeURIComponent(search)}`
    ),

  chat: (dataset_id: string, message: string) =>
    request<Analysis>('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dataset_id, message }),
    }),

  generateSql: (dataset_id: string, query: string) =>
    request<Analysis>('/generate-sql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dataset_id, query }),
    }),

  generateChart: (dataset_id: string, chart_type: string, x: string, y?: string) =>
    request<Analysis>('/generate-chart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dataset_id, chart_type, x, y }),
    }),

  detectAnomalies: (dataset_id: string) =>
    request<Analysis>(`/detect-anomalies?dataset_id=${dataset_id}`, { method: 'POST' }),
};
