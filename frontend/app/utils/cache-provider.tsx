'use client';

import { Cache, SWRConfig } from 'swr';

interface StorageData {
  [key: string]: any;
}

// Custom implementation of Cache interface
class CacheMap implements Cache<any> {
  private storage: Map<string, any>;

  constructor() {
    this.storage = new Map<string, any>();
  }

  get(key: string): any | undefined {
    return this.storage.get(key);
  }

  set(key: string, value: any): void {
    this.storage.set(key, value);
  }

  delete(key: string): void {
    this.storage.delete(key);
  }

  *keys(): Generator<string, undefined, unknown> {
    yield* this.storage.keys();
    return undefined;
  }

  getAll(): readonly any[] {
    return Array.from(this.storage.values());
  }
}

// Local storage cache provider
const localStorageProvider = () => {
  const cache = new CacheMap();

  // When initializing, restore data from localStorage
  if (typeof window !== 'undefined') {
    try {
      const data = localStorage.getItem('app-cache');
      const stored = data ? JSON.parse(data) as StorageData : {};
      Object.entries(stored).forEach(([key, value]) => {
        cache.set(key, value);
      });

      // Listen to storage changes
      window.addEventListener('storage', (event) => {
        if (event.key === 'app-cache') {
          const newData = event.newValue ? JSON.parse(event.newValue) as StorageData : {};
          // Update the cache with new values
          Object.entries(newData).forEach(([key, value]) => {
            cache.set(key, value);
          });
        }
      });

      // Save to localStorage before unloading
      window.addEventListener('beforeunload', () => {
        const data: StorageData = {};
        for (const key of cache.keys()) {
          const value = cache.get(key);
          if (value !== undefined) {
            data[key] = value;
          }
        }
        localStorage.setItem('app-cache', JSON.stringify(data));
      });
    } catch (error) {
      console.error('Error initializing cache:', error);
    }
  }

  return cache;
};

export function CacheProvider({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig 
      value={{
        provider: localStorageProvider,
        isVisible: () => true,
        initFocus: (callback) => {
          let hidden: string | undefined;
          if (typeof document !== 'undefined') {
            hidden = document?.hidden ? 'hidden' : 'visibilitychange';
            document?.addEventListener(hidden, callback);
          }
          return () => {
            if (hidden && typeof document !== 'undefined') {
              document?.removeEventListener(hidden, callback);
            }
          };
        }
      }}
    >
      {children}
    </SWRConfig>
  );
}
