export interface SessionDataset {
  id: string;
  name: string;
  csvContent: string;
  ownerId?: string;
}

function key(ownerId: string | undefined, id: string) {
  return `ds_${ownerId || 'anonymous'}_${id}`;
}

export const sessionStore = {
  save(ds: SessionDataset, ownerId?: string) {
    if (typeof window === 'undefined') return;
    try {
      const value = { ...ds, ownerId: ownerId || ds.ownerId };
      sessionStorage.setItem(key(ownerId || ds.ownerId, ds.id), JSON.stringify(value));
    } catch {}
  },

  get(id: string, ownerId?: string): SessionDataset | null {
    if (typeof window === 'undefined') return null;
    try {
      const raw = sessionStorage.getItem(key(ownerId, id));
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  getAll(ownerId?: string): SessionDataset[] {
    if (typeof window === 'undefined') return [];
    const list: SessionDataset[] = [];
    try {
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        if (!key || !key.startsWith(`ds_${ownerId || 'anonymous'}_`)) continue;
        if (key.startsWith('ds_')) {
          const raw = sessionStorage.getItem(key);
          if (raw) list.push(JSON.parse(raw));
        }
      }
    } catch {}
    return list;
  },

  remove(id: string, ownerId?: string) {
    if (typeof window === 'undefined') return;
    try {
      sessionStorage.removeItem(key(ownerId, id));
    } catch {}
  },

  clear(ownerId?: string) {
    if (typeof window === 'undefined') return;
    try {
      const keys: string[] = [];
      for (let i = 0; i < sessionStorage.length; i++) {
        const k = sessionStorage.key(i);
        if (k?.startsWith(`ds_${ownerId || 'anonymous'}_`)) keys.push(k);
      }
      keys.forEach(k => sessionStorage.removeItem(k));
    } catch {}
  },
};
