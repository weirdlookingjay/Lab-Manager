'use client';

import { useTheme } from "@/hooks/useTheme";
import { useEffect } from "react";

const themeStyles = {
  blue: {
    primary: 'hsl(221.2, 83.2%, 53.3%)',
    secondary: 'hsl(210, 40%, 96.1%)',
    accent: 'hsl(210, 40%, 96.1%)',
    ring: 'hsl(221.2, 83.2%, 53.3%)',
  },
  purple: {
    primary: 'hsl(271.2, 83.2%, 53.3%)',
    secondary: 'hsl(270, 40%, 96.1%)',
    accent: 'hsl(270, 40%, 96.1%)',
    ring: 'hsl(271.2, 83.2%, 53.3%)',
  },
};

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { theme } = useTheme();

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  return <>{children}</>;
}
