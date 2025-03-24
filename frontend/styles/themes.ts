export const themes = {
  blue: {
    primary: '#2563eb',
    secondary: '#60a5fa',
    accent: '#3b82f6',
    background: '#ffffff',
    foreground: '#000000',
    muted: '#f3f4f6',
    mutedForeground: '#6b7280',
    border: '#e5e7eb',
    input: '#ffffff',
    ring: '#2563eb',
  },
  purple: {
    primary: '#7c3aed',
    secondary: '#a78bfa',
    accent: '#8b5cf6',
    background: '#ffffff',
    foreground: '#000000',
    muted: '#f5f3ff',
    mutedForeground: '#6b7280',
    border: '#e5e7eb',
    input: '#ffffff',
    ring: '#7c3aed',
  }
}

export type ThemeType = keyof typeof themes;
