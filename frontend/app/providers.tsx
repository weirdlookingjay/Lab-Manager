'use client';

import { AuthProvider } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { ThemeProvider } from '@/components/ThemeProvider';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <NotificationProvider>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </NotificationProvider>
    </AuthProvider>
  );
}
