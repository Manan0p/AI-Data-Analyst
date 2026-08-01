export interface SessionDataset {
  id: string;
  name: string;
  csvContent: string;
}

export const sessionStore = {
  save(ds: SessionDataset) {
    if (typeof window === 'undefined') return;
    try {
      sessionStorage.setItem(`ds_${ds.id}`, JSON.stringify(ds));
    } catch {}
  },

  get(id: string): SessionDataset | null {
    if (typeof window === 'undefined') return null;
    try {
      const raw = sessionStorage.getItem(`ds_${id}`);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  getAll(): SessionDataset[] {
    if (typeof window === 'undefined') return [];
    const list: SessionDataset[] = [];
    try {
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        if (key?.startsWith('ds_')) {
          const raw = sessionStorage.getItem(key);
          if (raw) list.push(JSON.parse(raw));
        }
      }
    } catch {}
    return list;
  },

  remove(id: string) {
    if (typeof window === 'undefined') return;
    try {
      sessionStorage.removeItem(`ds_${id}`);
    } catch {}
  },

  clear() {
    if (typeof window === 'undefined') return;
    try {
      const keys: string[] = [];
      for (let i = 0; i < sessionStorage.length; i++) {
        const k = sessionStorage.key(i);
        if (k?.startsWith('ds_')) keys.push(k);
      }
      keys.forEach(k => sessionStorage.removeItem(k));
    } catch {}
  },
};
