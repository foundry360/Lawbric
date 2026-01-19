# Public Assets Directory

This directory contains static assets that are served from the root URL path.

## Structure

```
public/
├── favicon.ico          # Browser favicon
├── logo.svg             # Main logo (SVG format recommended)
├── logo.png             # Main logo (PNG format)
├── logo-dark.svg        # Dark mode logo variant
├── apple-touch-icon.png # iOS home screen icon
└── images/              # Other images
    └── ...
```

## Usage in Code

Files in the `public` directory are accessible from the root URL:

- `/favicon.ico` → `public/favicon.ico`
- `/logo.svg` → `public/logo.svg`
- `/images/example.png` → `public/images/example.png`

### Example in React/Next.js:

```tsx
// Using Next.js Image component (recommended)
import Image from 'next/image'
<Image src="/logo.svg" alt="Logo" width={40} height={40} />

// Or using regular img tag
<img src="/logo.svg" alt="Logo" className="w-10 h-10" />
```

## Favicon Setup

Add to `app/layout.tsx`:

```tsx
export const metadata = {
  icons: {
    icon: '/favicon.ico',
    apple: '/apple-touch-icon.png',
  },
}
```



