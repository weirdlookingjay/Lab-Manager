'use client'

import * as React from 'react'
import { ThemeProvider as NextThemesProvider } from 'next-themes'

interface ThemeContextType {
  theme: string;
  mode: 'light' | 'dark';
  setAppTheme: (theme: string) => void;
  setAppMode: (mode: 'light' | 'dark') => void;
}

export const ThemeContext = React.createContext<ThemeContextType>({
  theme: 'green',
  mode: 'light',
  setAppTheme: () => {},
  setAppMode: () => {},
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = React.useState(false);
  const [theme, setTheme] = React.useState(() => 
    typeof window !== 'undefined' ? localStorage.getItem('app-theme') || 'green' : 'green'
  );
  const [mode, setMode] = React.useState<'light' | 'dark'>(() => 
    typeof window !== 'undefined' ? (localStorage.getItem('app-mode') as 'light' | 'dark') || 'light' : 'light'
  );

  React.useEffect(() => {
    const savedTheme = localStorage.getItem('app-theme') || 'green';
    const savedMode = localStorage.getItem('app-mode') || 'light';
    setTheme(savedTheme);
    setMode(savedMode as 'light' | 'dark');
    document.documentElement.setAttribute('data-theme', savedTheme);
    document.documentElement.setAttribute('data-mode', savedMode);
    setMounted(true);
  }, []);

  const setAppTheme = React.useCallback((newTheme: string) => {
    setTheme(newTheme);
    localStorage.setItem('app-theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  }, []);

  const setAppMode = React.useCallback((newMode: 'light' | 'dark') => {
    setMode(newMode);
    localStorage.setItem('app-mode', newMode);
    document.documentElement.setAttribute('data-mode', newMode);
  }, []);

  if (!mounted) {
    return null;
  }

  return (
    <ThemeContext.Provider value={{ theme, mode, setAppTheme, setAppMode }}>
      <NextThemesProvider
        attribute="data-theme"
        defaultTheme={theme}
        enableSystem={false}
        disableTransitionOnChange
        themes={['purple', 'blue', 'green']}
        forcedTheme={theme}
      >
        {children}
      </NextThemesProvider>
    </ThemeContext.Provider>
  )
}
