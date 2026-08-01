export interface StoredDataset {
  id: string;
  name: string;
  csvContent: string;
}

const DB_NAME = 'insightforge_db';
const STORE_NAME = 'datasets';

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof window === 'undefined' || !window.indexedDB) {
      return reject(new Error('IndexedDB not supported'));
    }
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id' });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export const datasetStore = {
  async save(dataset: StoredDataset): Promise<void> {
    try {
      const db = await openDB();
      return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        tx.objectStore(STORE_NAME).put(dataset);
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
      });
    } catch {
      // Fallback to localStorage
      try {
        localStorage.setItem(`ds_${dataset.id}`, JSON.stringify(dataset));
      } catch {}
    }
  },

  async get(id: string): Promise<StoredDataset | null> {
    try {
      const db = await openDB();
      return new Promise((resolve) => {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const req = tx.objectStore(STORE_NAME).get(id);
        req.onsuccess = () => resolve(req.result || null);
        req.onerror = () => resolve(null);
      });
    } catch {
      try {
        const raw = localStorage.getItem(`ds_${id}`);
        return raw ? JSON.parse(raw) : null;
      } catch {
        return null;
      }
    }
  },

  async getAll(): Promise<StoredDataset[]> {
    try {
      const db = await openDB();
      return new Promise((resolve) => {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const req = tx.objectStore(STORE_NAME).getAll();
        req.onsuccess = () => resolve(req.result || []);
        req.onerror = () => resolve([]);
      });
    } catch {
      const items: StoredDataset[] = [];
      try {
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key?.startsWith('ds_')) {
            const raw = localStorage.getItem(key);
            if (raw) items.push(JSON.parse(raw));
          }
        }
      } catch {}
      return items;
    }
  },
};
