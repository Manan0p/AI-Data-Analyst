import { Analysis, Dataset, Profile } from '@/types';
import { sessionStore } from './sessionStore';

const base = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' ? '/api' : 'http://localhost:8000/api');

async function rehydrateDataset(dataset_id: string | null): Promise<boolean> {
  let stored = dataset_id ? sessionStore.get(dataset_id) : null;
  if (!stored) {
    const all = sessionStore.getAll();
    if (all.length === 0) return false;
    stored = all[0];
  }

  try {
    const file = new File([stored.csvContent], stored.name, { type: 'text/csv' });
    const formData = new FormData();
    formData.append('files', file);
    const res = await fetch(base + '/upload', { method: 'POST', body: formData });
    return res.ok;
  } catch {
    return false;
  }
}

function extractDatasetId(path: string, init?: RequestInit, errorMsg?: string): string | null {
  const matchPath = path.match(/datasets\/([a-zA-Z0-9_-]+)/);
  if (matchPath) return matchPath[1];

  const matchQuery = path.match(/[?&]dataset_id=([a-zA-Z0-9_-]+)/);
  if (matchQuery) return matchQuery[1];

  if (init?.body) {
    try {
      const parsed = JSON.parse(String(init.body));
      if (parsed.dataset_id) return String(parsed.dataset_id);
    } catch {}
  }

  if (errorMsg) {
    const matchError = errorMsg.match(/Dataset ['"]?([a-zA-Z0-9_-]+)['"]? was not found/i);
    if (matchError) return matchError[1];
  }

  return null;
}

async function request<T>(path: string, init?: RequestInit, isRetry = false): Promise<T> {
  const r = await fetch(base + path, init);
  if (!r.ok) {
    const body = await r.json().catch(() => ({ detail: r.statusText }));
    const errorMsg = String(body.detail ?? r.statusText);

    // Re-seed stateless Vercel Serverless Lambda worker seamlessly if dataset was purged
    if ((r.status === 404 || r.status === 400 || errorMsg.includes('not found')) && !isRetry) {
      const dataset_id = extractDatasetId(path, init, errorMsg);
      const ok = await rehydrateDataset(dataset_id);
      if (ok) {
        return request<T>(path, init, true);
      }
    }

    throw new Error(errorMsg);
  }
  return r.json();
}

export const api = {
  datasets: async () => {
    let list = await request<Dataset[]>('/datasets');
    if (list.length === 0) {
      const stored = sessionStore.getAll();
      if (stored.length > 0) {
        for (const s of stored) {
          await rehydrateDataset(s.id);
        }
        list = await request<Dataset[]>('/datasets');
      }
    }
    // Deduplicate datasets by ID
    return Array.from(new Map(list.map(d => [d.id, d])).values());
  },

  upload: async (files: File[]) => {
    const fileTexts = await Promise.all(
      files.map(async f => ({ name: f.name, text: await f.text() }))
    );

    const body = new FormData();
    files.forEach(f => body.append('files', f));
    const result = await request<Dataset[]>('/upload', { method: 'POST', body });

    for (const ds of result) {
      const match = fileTexts.find(t => t.name === ds.name);
      if (match) {
        sessionStore.save({ id: ds.id, name: ds.name, csvContent: match.text });
      }
    }

    return Array.from(new Map(result.map(d => [d.id, d])).values());
  },

  deleteDataset: async (id: string) => {
    sessionStore.remove(id);
    return request<{ message: string }>(`/datasets/${id}`, { method: 'DELETE' });
  },

  deleteAllDatasets: async () => {
    sessionStore.clear();
    return request<{ message: string }>('/datasets', { method: 'DELETE' });
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
