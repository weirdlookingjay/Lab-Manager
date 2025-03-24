import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import "./globals.css"
import { LayoutWrapper } from './components/layout-wrapper'
import { Providers } from './providers'
import { Toaster } from '@/components/ui/toaster'
import { ThemeProvider } from './providers/theme-provider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Lab Manager',
  description: 'Lab Manager Application',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning data-theme="blue">
      <body className={inter.className} suppressHydrationWarning>
        <Providers>
          <ThemeProvider>
            <LayoutWrapper>
              {children}
            </LayoutWrapper>
            <Toaster />
          </ThemeProvider>
        </Providers>
      </body>
    </html>
  )
}
