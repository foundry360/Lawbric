import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/lib/auth'
import { DashboardProvider } from '@/lib/dashboard-context'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Legal Discovery AI Platform',
  description: 'AI-powered legal document discovery and analysis',
  icons: {
    icon: '/favicon.ico',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <DashboardProvider>
            {children}
          </DashboardProvider>
        </AuthProvider>
      </body>
    </html>
  )
}

