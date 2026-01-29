import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Script from 'next/script'
import './globals.css'
import './quill.css'
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
      <head>
        <script src="https://acrobatservices.adobe.com/view-sdk/viewer.js" async />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              // Suppress LastPass and other browser extension console errors
              (function() {
                const originalError = console.error;
                const originalWarn = console.warn;
                
                // List of error patterns to suppress
                const suppressedPatterns = [
                  /Cannot create item with duplicate id/i,
                  /Invalid frameId for foreground/i,
                  /runtime\.lastError/i,
                  /background-redux-new\.js/i,
                  /chrome-extension:/i,
                  /moz-extension:/i,
                  /safari-extension:/i
                ];
                
                console.error = function(...args) {
                  const message = args.join(' ');
                  const shouldSuppress = suppressedPatterns.some(pattern => pattern.test(message));
                  if (!shouldSuppress) {
                    originalError.apply(console, args);
                  }
                };
                
                console.warn = function(...args) {
                  const message = args.join(' ');
                  const shouldSuppress = suppressedPatterns.some(pattern => pattern.test(message));
                  if (!shouldSuppress) {
                    originalWarn.apply(console, args);
                  }
                };
                
                // Suppress unhandled promise rejections from extensions
                window.addEventListener('unhandledrejection', function(event) {
                  const message = event.reason?.message || event.reason?.toString() || '';
                  const shouldSuppress = suppressedPatterns.some(pattern => pattern.test(message));
                  if (shouldSuppress) {
                    event.preventDefault();
                  }
                });
              })();
            `,
          }}
        />
      </head>
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

