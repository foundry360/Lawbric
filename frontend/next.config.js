/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // Required for Docker
  // Environment variables are loaded from .env.local file or Docker environment
  // NEXT_PUBLIC_* variables are automatically available in the browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9001',
  },
  transpilePackages: ['@tiptap/react', '@tiptap/starter-kit', '@tiptap/extension-placeholder', '@tiptap/extension-underline', 'react-markdown'],
  webpack: (config, { isServer, dev }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        canvas: false,
        encoding: false,
        path: false,
        stream: false,
        http2: false,
      }
      
      // Handle node: protocol imports - these are used by react-markdown dependencies
      // We need to provide empty modules or polyfills for browser compatibility
      const webpack = require('webpack')
      config.plugins.push(
        new webpack.NormalModuleReplacementPlugin(/^node:/, (resource) => {
          resource.request = resource.request.replace(/^node:/, '')
        })
      )
      
      // Also add fallbacks for the node: protocol
      config.resolve.fallback = {
        ...config.resolve.fallback,
        'node:path': false,
        'node:process': false,
        'node:url': false,
        'node:util': false,
        'node:buffer': false,
        'node:crypto': false,
      }
    }
    
    // Handle ESM modules like Tiptap
    config.resolve.extensionAlias = {
      '.js': ['.js', '.ts', '.tsx'],
      '.jsx': ['.jsx', '.tsx'],
    }
    // Ensure Tiptap packages are resolved correctly
    config.experiments = {
      ...config.experiments,
      topLevelAwait: true,
    }
    return config
  },
  images: {
    // Configure remote image patterns as needed
    // remotePatterns: [
    //   {
    //     protocol: 'https',
    //     hostname: 'example.com',
    //     pathname: '/images/**',
    //   },
    // ],
  },
}

module.exports = nextConfig




