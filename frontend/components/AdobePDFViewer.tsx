'use client'

import { useEffect, useRef, useState } from 'react'

interface AdobePDFViewerProps {
  pdfUrl: string
  fileName: string
}

declare global {
  interface Window {
    AdobeDC: any
  }
}

export default function AdobePDFViewer({ pdfUrl, fileName }: AdobePDFViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [isReady, setIsReady] = useState(false)
  const [viewerId] = useState(() => `adobe-pdf-viewer-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`)
  const adobeDCViewRef = useRef<any>(null)

  useEffect(() => {
    // Wait for Adobe SDK to load
    const checkAdobeSDK = () => {
      if (window.AdobeDC && window.AdobeDC.View) {
        setIsReady(true)
      } else {
        setTimeout(checkAdobeSDK, 100)
      }
    }

    // Listen for Adobe SDK ready event
    const handleAdobeReady = () => {
      setIsReady(true)
    }

    if (window.AdobeDC && window.AdobeDC.View) {
      setIsReady(true)
    } else {
      document.addEventListener('adobe_dc_view_sdk.ready', handleAdobeReady)
      checkAdobeSDK()
    }

    return () => {
      document.removeEventListener('adobe_dc_view_sdk.ready', handleAdobeReady)
    }
  }, [])

  useEffect(() => {
    if (!isReady || !containerRef.current || !pdfUrl) return

    const clientId = process.env.NEXT_PUBLIC_ADOBE_CLIENT_ID || 'a36bb0a1cb0543ec86137af9152555f7'
    if (!clientId) {
      console.error('Adobe Client ID not configured')
      return
    }

    try {
      const adobeDCView = new window.AdobeDC.View({
        clientId: clientId,
        divId: viewerId,
      })

      adobeDCViewRef.current = adobeDCView

      adobeDCView.previewFile(
        {
          content: {
            location: {
              url: pdfUrl,
            },
          },
          metaData: {
            fileName: fileName,
          },
        },
        {
          embedMode: 'FULL_WINDOW',
          showDownloadPDF: false,
          showPrintPDF: false,
          showLeftHandPanels: false, // Hide sidebar/thumbnails
          showAnnotationTools: false, // Disable annotation tools (may help hide Select/Pan)
          defaultViewMode: 'FIT_WIDTH', // Fit to width instead of fit page
          enableFormFilling: false,
          showZoomControls: true,
          enableLinearization: false,
        }
      ).then((adobeViewer: any) => {
        // Set view mode to fit width after rendering (in case defaultViewMode doesn't work)
        setTimeout(() => {
          try {
            const apis = adobeViewer.getAPIs()
            if (apis && apis.setViewMode) {
              apis.setViewMode('FIT_WIDTH')
            }
            // Try to disable specific tools if available
            if (apis && apis.disableToolbar) {
              // Note: This may not work as Select/Pan are "quick tools" that can't be individually disabled
              try {
                apis.disableToolbar(['select', 'pan'])
              } catch (e) {
                // Ignore if not supported
              }
            }
            
            // Inject CSS to style Pan and Select buttons, background, and page borders
            const viewerElement = document.getElementById(viewerId)
            if (viewerElement) {
              const styleId = `adobe-pdf-viewer-styles-${viewerId}`
              let styleElement = document.getElementById(styleId) as HTMLStyleElement
              
              if (!styleElement) {
                styleElement = document.createElement('style')
                styleElement.id = styleId
                document.head.appendChild(styleElement)
              }
              
              styleElement.textContent = `
                /* White background for PDF viewer */
                #${viewerId},
                #${viewerId} > div,
                #${viewerId} iframe,
                #${viewerId} [class*="adobe"],
                #${viewerId} [id*="adobe-view"],
                #${viewerId} [class*="viewer"] {
                  background-color: #ffffff !important;
                }
                
                /* Light gray border for each PDF page */
                #${viewerId} canvas,
                #${viewerId} [class*="page"],
                #${viewerId} [data-page],
                #${viewerId} [class*="Page"],
                #${viewerId} div[style*="page"] {
                  border: 1px solid #e5e7eb !important;
                  margin: 8px auto !important;
                  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
                  background-color: #ffffff !important;
                }
                
                /* Style Pan and Select buttons in Adobe PDF viewer */
                #${viewerId} button[title*="Pan"],
                #${viewerId} button[title*="pan"],
                #${viewerId} button[title*="Select"],
                #${viewerId} button[title*="select"],
                #${viewerId} button[aria-label*="Pan"],
                #${viewerId} button[aria-label*="pan"],
                #${viewerId} button[aria-label*="Select"],
                #${viewerId} button[aria-label*="select"],
                #${viewerId} [data-tool="pan"],
                #${viewerId} [data-tool="select"] {
                  background-color: #ffffff !important;
                  border: 1px solid #e5e7eb !important;
                }
                
                #${viewerId} button[title*="Pan"]:hover,
                #${viewerId} button[title*="pan"]:hover,
                #${viewerId} button[title*="Select"]:hover,
                #${viewerId} button[title*="select"]:hover,
                #${viewerId} button[aria-label*="Pan"]:hover,
                #${viewerId} button[aria-label*="pan"]:hover,
                #${viewerId} button[aria-label*="Select"]:hover,
                #${viewerId} button[aria-label*="select"]:hover {
                  background-color: #f3f4f6 !important;
                }
              `
            }
          } catch (e) {
            console.warn('Could not set view mode or disable tools:', e)
          }
        }, 1500) // Increased timeout to allow viewer to fully render
      }).catch((error: any) => {
        console.error('Error previewing PDF:', error)
      })
    } catch (error) {
      console.error('Error initializing Adobe PDF viewer:', error)
    }

    return () => {
      // Cleanup style element
      const styleId = `adobe-pdf-viewer-styles-${viewerId}`
      const styleElement = document.getElementById(styleId)
      if (styleElement) {
        styleElement.remove()
      }
      
      // Cleanup viewer instance
      if (adobeDCViewRef.current) {
        adobeDCViewRef.current = null
      }
    }
  }, [isReady, pdfUrl, fileName, viewerId])

  if (!pdfUrl) return null

  return (
    <div className="w-full h-full flex flex-col rounded-lg overflow-hidden bg-white">
      <div
        id={viewerId}
        ref={containerRef}
        className="w-full flex-1"
        style={{ 
          backgroundColor: '#ffffff', 
          minHeight: 0,
          background: '#ffffff'
        }}
      />
    </div>
  )
}

