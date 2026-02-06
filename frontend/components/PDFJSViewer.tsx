'use client'

import { useState, useEffect, useRef } from 'react'
import { ZoomIn, ZoomOut, ChevronsLeft, ChevronsRight, AlertCircle, Loader2 } from 'lucide-react'

interface PDFJSViewerProps {
  pdfUrl: string
  fileName: string
  scale?: number
  onScaleChange?: (scale: number) => void
  currentPage?: number
  onPageChange?: (page: number) => void
  numPages?: number | null
  onNumPagesChange?: (numPages: number) => void
}

declare global {
  interface Window {
    pdfjsLib: any
  }
}

export default function PDFJSViewer({ 
  pdfUrl, 
  fileName,
  scale: externalScale = 1.0,
  onScaleChange,
  currentPage: externalCurrentPage = 1,
  onPageChange,
  numPages: externalNumPages,
  onNumPagesChange
}: PDFJSViewerProps) {
  const [numPages, setNumPages] = useState<number | null>(externalNumPages || null)
  const [currentPage, setCurrentPage] = useState(externalCurrentPage)
  const [scale, setScale] = useState(externalScale)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pagesRendered, setPagesRendered] = useState<Set<number>>(new Set())
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRefs = useRef<{ [key: number]: HTMLCanvasElement | null }>({})
  const pdfDocRef = useRef<any>(null)
  const loadingCancelledRef = useRef<boolean>(false)
  const loadingTaskRef = useRef<any>(null)
  
  // Use external scale if provided
  const effectiveScale = onScaleChange ? externalScale : scale
  const effectiveCurrentPage = onPageChange ? externalCurrentPage : currentPage

  // Load PDF.js from CDN
  useEffect(() => {
    if (typeof window === 'undefined' || window.pdfjsLib) return

    const script = document.createElement('script')
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js'
    script.onload = () => {
      if (window.pdfjsLib) {
        window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js'
      }
    }
    document.head.appendChild(script)

    return () => {
      const existingScript = document.querySelector('script[src*="pdf.min.js"]')
      if (existingScript) {
        existingScript.remove()
      }
    }
  }, [])

  // Load PDF document
  useEffect(() => {
    // Reset cancellation flag
    loadingCancelledRef.current = false
    
    if (!pdfUrl) {
      console.log('PDFJSViewer: No pdfUrl provided - cleaning up')
      // Immediately cancel any ongoing loading
      loadingCancelledRef.current = true
      
      // Cancel loading task if it exists
      if (loadingTaskRef.current) {
        try {
          loadingTaskRef.current.destroy?.()
        } catch (e) {
          // Ignore errors
        }
        loadingTaskRef.current = null
      }
      
      // Clear any existing PDF document when URL is cleared
      if (pdfDocRef.current) {
        try {
          pdfDocRef.current.destroy().catch(() => {})
        } catch (e) {
          // Ignore errors
        }
        pdfDocRef.current = null
      }
      
      setNumPages(null)
      setPagesRendered(new Set())
      setLoading(false)
      setError(null)
      return
    }

    const loadPDF = async () => {
      try {
        console.log('PDFJSViewer: Loading PDF from URL:', pdfUrl.substring(0, 50) + '...')
        setLoading(true)
        setError(null)

        const loadingTask = window.pdfjsLib.getDocument({
          url: pdfUrl,
          withCredentials: false,
        })
        
        // Store loading task reference so we can cancel it if needed
        loadingTaskRef.current = loadingTask

        const pdf = await loadingTask.promise
        
        // Check if loading was cancelled
        if (loadingCancelledRef.current) {
          // Destroy asynchronously to avoid worker errors
          setTimeout(() => {
            try {
              pdf.destroy().catch((err: any) => {
                // Ignore "Worker was destroyed" errors
                if (!err.message || !err.message.includes('Worker was destroyed')) {
                  // Only log non-worker errors
                }
              })
            } catch (e) {
              // Ignore
            }
          }, 50)
          return
        }
        
        console.log('PDFJSViewer: PDF loaded successfully, pages:', pdf.numPages)
        pdfDocRef.current = pdf
        const pages = pdf.numPages
        setNumPages(pages)
        setPagesRendered(new Set()) // Reset rendered pages when new PDF loads
        if (onNumPagesChange) {
          onNumPagesChange(pages)
        }
        if (!onPageChange) {
          setCurrentPage(1)
        } else if (onPageChange) {
          onPageChange(1)
        }
        setLoading(false)
        
        // Scroll to top after PDF loads
        if (containerRef.current && !loadingCancelledRef.current) {
          setTimeout(() => {
            if (containerRef.current && !loadingCancelledRef.current) {
              containerRef.current.scrollTop = 0
            }
          }, 100)
        }
      } catch (err: any) {
        // Don't set error if loading was cancelled
        if (loadingCancelledRef.current) {
          return
        }
        
        // Ignore errors related to blob URL being revoked (error code 0)
        if (err.message && err.message.includes('Unexpected server response (0)')) {
          console.log('PDFJSViewer: Blob URL was revoked, ignoring error')
          return
        }
        
        console.error('PDFJSViewer: Error loading PDF:', err)
        setError(err.message || 'Failed to load PDF')
        setLoading(false)
      }
    }
    
    if (!window.pdfjsLib) {
      console.log('PDFJSViewer: Waiting for PDF.js library to load...')
      const checkInterval = setInterval(() => {
        if (window.pdfjsLib && pdfUrl && !loadingCancelledRef.current) {
          console.log('PDFJSViewer: PDF.js library loaded')
          clearInterval(checkInterval)
          // Trigger load after library is ready
          setTimeout(() => {
            if (pdfUrl && !loadingCancelledRef.current) {
              loadPDF()
            }
          }, 100)
        }
      }, 100)
      return () => {
        clearInterval(checkInterval)
        loadingCancelledRef.current = true
        if (pdfDocRef.current) {
          const pdfDoc = pdfDocRef.current
          pdfDocRef.current = null
          // Destroy asynchronously to avoid worker errors
          setTimeout(() => {
            try {
              pdfDoc.destroy().catch((err: any) => {
                // Ignore "Worker was destroyed" errors
                if (!err.message || !err.message.includes('Worker was destroyed')) {
                  // Only log non-worker errors
                }
              })
            } catch (e) {
              // Ignore
            }
          }, 50)
        }
      }
    }

    // Load immediately if library is ready
    loadPDF()
    
    // Cleanup function to cancel loading if URL changes
    return () => {
      loadingCancelledRef.current = true
      
      // Cancel loading task if it exists
      if (loadingTaskRef.current) {
        try {
          // Don't destroy the loading task - just cancel it
          if (typeof loadingTaskRef.current.cancel === 'function') {
            loadingTaskRef.current.cancel()
          }
        } catch (e) {
          // Ignore errors
        }
        loadingTaskRef.current = null
      }
      
      // Destroy PDF document (but don't destroy the worker - it's shared globally)
      if (pdfDocRef.current) {
        try {
          const pdfDoc = pdfDocRef.current
          pdfDocRef.current = null // Clear ref first to prevent new operations
          
          // Destroy asynchronously to avoid worker errors
          // The worker is shared globally, so we just need to clean up the document instance
          setTimeout(() => {
            try {
              pdfDoc.destroy().catch((err: any) => {
                // Ignore "Worker was destroyed" errors - they're harmless
                // The worker is shared and may be used by other PDF instances
                if (!err.message || !err.message.includes('Worker was destroyed')) {
                  // Only log non-worker errors
                }
              })
            } catch (e) {
              // Ignore
            }
          }, 100)
        } catch (e) {
          // Ignore
          pdfDocRef.current = null
        }
      }
    }
  }, [pdfUrl, onNumPagesChange, onPageChange])
  
  // Expose cleanup method on container element (only when needed for archiving)
  useEffect(() => {
    if (!containerRef.current) return
    
    const cleanup = () => {
      console.log('PDFJSViewer: Cleanup called')
      loadingCancelledRef.current = true
      
      // Cancel loading task first
      if (loadingTaskRef.current) {
        try {
          console.log('PDFJSViewer: Canceling loading task')
          // Try to cancel the loading task
          if (typeof loadingTaskRef.current.cancel === 'function') {
            loadingTaskRef.current.cancel()
          }
          if (typeof loadingTaskRef.current.destroy === 'function') {
            loadingTaskRef.current.destroy()
          }
        } catch (e) {
          console.warn('PDFJSViewer: Error canceling loading task:', e)
        }
        loadingTaskRef.current = null
      }
      
      // Destroy PDF document (but don't destroy the worker - it's shared)
      if (pdfDocRef.current) {
        try {
          console.log('PDFJSViewer: Destroying PDF document')
          // Cancel any ongoing operations first
          const pdfDoc = pdfDocRef.current
          pdfDocRef.current = null // Clear ref first to prevent new operations
          
          // Destroy the document asynchronously to avoid worker errors
          setTimeout(() => {
            try {
              pdfDoc.destroy().catch((err: any) => {
                // Ignore "Worker was destroyed" errors - they're harmless
                if (!err.message || !err.message.includes('Worker was destroyed')) {
                  console.warn('PDFJSViewer: Error destroying PDF document:', err)
                }
              })
            } catch (e) {
              // Ignore errors
            }
          }, 100)
        } catch (e) {
          console.warn('PDFJSViewer: Error destroying PDF document:', e)
          pdfDocRef.current = null
        }
      }
      
      // Clear state (but don't clear canvas refs - let React handle that)
      setNumPages(null)
      setLoading(false)
      setError(null)
      console.log('PDFJSViewer: Cleanup complete')
    }
    
    // Expose cleanup method on container
    (containerRef.current as any).cleanupPDF = cleanup
    
    // Don't run cleanup on unmount - only when explicitly called
  }, [])

  // Render PDF pages
  useEffect(() => {
    if (!pdfDocRef.current || !window.pdfjsLib || loading || loadingCancelledRef.current) return

    const renderPage = async (pageNum: number) => {
      // Check if cancelled before rendering
      if (loadingCancelledRef.current) return
      
      try {
        const page = await pdfDocRef.current.getPage(pageNum)
        
        // Check again after getting page
        if (loadingCancelledRef.current) {
          page.cleanup?.()
          return
        }
        
        // Wait for canvas to be mounted (with retry)
        let canvas = canvasRefs.current[pageNum]
        if (!canvas) {
          // Retry after a short delay - canvas might not be mounted yet
          await new Promise(resolve => setTimeout(resolve, 100))
          canvas = canvasRefs.current[pageNum]
          if (!canvas) {
            console.warn(`PDFJSViewer: Canvas not found for page ${pageNum} after retry`)
            return
          }
        }

        const viewport = page.getViewport({ scale: effectiveScale })
        canvas.height = viewport.height
        canvas.width = viewport.width

        const context = canvas.getContext('2d')
        if (!context) {
          console.warn(`PDFJSViewer: Could not get 2d context for page ${pageNum}`)
          return
        }

        const renderContext = {
          canvasContext: context,
          viewport: viewport,
        }

        await page.render(renderContext).promise
        console.log(`PDFJSViewer: Page ${pageNum} rendered successfully`)
        // Mark page as rendered
        setPagesRendered(prev => new Set([...prev, pageNum]))
      } catch (err: any) {
        // Ignore errors if loading was cancelled or blob URL was revoked
        if (loadingCancelledRef.current) {
          return
        }
        if (err.message && err.message.includes('Unexpected server response (0)')) {
          return
        }
        console.error(`PDFJSViewer: Error rendering page ${pageNum}:`, err)
      }
    }

    // Render all pages
    const pages = numPages || externalNumPages
    if (pages) {
      console.log(`PDFJSViewer: Starting to render ${pages} pages`)
      
      // Wait for canvases to be mounted, then render
      const checkAndRender = () => {
        if (loadingCancelledRef.current || !pdfDocRef.current) return
        
        // Check if at least one canvas is mounted
        let hasCanvas = false
        for (let i = 1; i <= pages; i++) {
          if (canvasRefs.current[i]) {
            hasCanvas = true
            break
          }
        }
        
        if (hasCanvas) {
          // Canvases are ready, render all pages
          for (let i = 1; i <= pages; i++) {
            renderPage(i)
          }
        } else {
          // Canvases not ready yet, retry
          setTimeout(checkAndRender, 50)
        }
      }
      
      // Start checking after a short delay
      const renderTimer = setTimeout(checkAndRender, 100)
      
      return () => {
        clearTimeout(renderTimer)
      }
    }
  }, [numPages, externalNumPages, effectiveScale, loading])

  // Scroll to top when PDF URL changes (new document loaded)
  useEffect(() => {
    if (pdfUrl && containerRef.current) {
      // Scroll to top when a new PDF is loaded
      containerRef.current.scrollTop = 0
    }
  }, [pdfUrl])

  // Detect current page based on scroll position using Intersection Observer
  useEffect(() => {
    if (!containerRef.current || loading) return

    const container = containerRef.current
    const pages = numPages || externalNumPages
    if (!pages) return

    // Use Intersection Observer to detect which page is most visible
    const observerOptions = {
      root: container,
      rootMargin: '-20% 0px -60% 0px', // Consider page visible if it's in the top 40% of viewport
      threshold: [0, 0.1, 0.5, 1.0]
    }

    const observer = new IntersectionObserver((entries) => {
      // Find the page with the highest intersection ratio
      let maxRatio = 0
      let mostVisiblePage = effectiveCurrentPage

      entries.forEach((entry) => {
        const pageNum = parseInt(entry.target.getAttribute('data-page') || '1')
        if (entry.intersectionRatio > maxRatio) {
          maxRatio = entry.intersectionRatio
          mostVisiblePage = pageNum
        }
      })

      // Update current page if it changed and has significant visibility
      if (mostVisiblePage !== effectiveCurrentPage && maxRatio > 0.1) {
        // Mark as scroll detection to prevent circular scrolling
        isScrollDetectionRef.current = true
        if (onPageChange) {
          onPageChange(mostVisiblePage)
        } else {
          setCurrentPage(mostVisiblePage)
        }
      }
    }, observerOptions)

    // Observe all page elements
    for (let i = 1; i <= pages; i++) {
      const pageElement = container.querySelector(`[data-page="${i}"]`)
      if (pageElement) {
        observer.observe(pageElement)
      }
    }

    return () => {
      observer.disconnect()
    }
  }, [numPages, externalNumPages, loading, effectiveCurrentPage, onPageChange])

  // Track if page change is from scroll detection (to avoid circular scrolling)
  const isScrollDetectionRef = useRef(false)

  // Scroll to current page when it changes via buttons (not from scroll detection)
  useEffect(() => {
    // Only scroll if this was NOT from scroll detection (i.e., button click)
    if (effectiveCurrentPage && containerRef.current && !loading && !isScrollDetectionRef.current) {
      const pageElement = containerRef.current.querySelector(`[data-page="${effectiveCurrentPage}"]`)
      if (pageElement) {
        pageElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }
    // Reset flag after handling
    isScrollDetectionRef.current = false
  }, [effectiveCurrentPage, loading])

  if (error) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-white">
        <div className="text-center">
          <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      </div>
    )
  }

  const pages = numPages || externalNumPages

  return (
    <div className="w-full h-full flex flex-col bg-white" data-pdf-viewer="true">
      {/* PDF Viewer - Only scrollable content, no header */}
      <div 
        ref={containerRef}
        className="flex-1 overflow-auto bg-white p-4"
      >
        {loading && (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
          </div>
        )}

        <div className="flex flex-col items-center">
          {pages && Array.from({ length: pages }, (_, i) => i + 1).map((pageNum) => {
            const isRendered = pagesRendered.has(pageNum)
            return (
              <div
                key={pageNum}
                data-page={pageNum}
                className="mb-4 shadow-sm border border-gray-200 bg-white"
                style={{ 
                  visibility: isRendered ? 'visible' : 'hidden',
                  minHeight: isRendered ? 'auto' : '100px'
                }}
              >
                <canvas
                  ref={(el) => {
                    canvasRefs.current[pageNum] = el
                  }}
                  className="block"
                  style={{ display: isRendered ? 'block' : 'none' }}
                />
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
