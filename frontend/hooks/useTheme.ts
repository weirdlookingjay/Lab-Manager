'use client';

import { useContext } from 'react';
import { ThemeContext } from '@/app/providers/theme-provider';

export type Theme = 'blue' | 'purple' | 'green';
export type Mode = 'light' | 'dark';

export function useTheme() {
  const { theme, mode, setAppTheme, setAppMode } = useContext(ThemeContext);
  
  return {
    theme: theme as Theme,
    mode,
    setTheme: (newTheme: Theme) => {
      setAppTheme(newTheme);
    },
    setMode: (newMode: Mode) => {
      setAppMode(newMode);
    }
  };
}
