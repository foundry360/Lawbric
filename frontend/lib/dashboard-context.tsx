'use client'

import { createContext, useContext, useState, ReactNode, useRef, useCallback } from 'react'
import { Case, casesApi } from '@/lib/api'

interface DashboardContextType {
  cases: Case[]
  setCases: (cases: Case[]) => void
  isLoading: boolean
  setIsLoading: (loading: boolean) => void
  refreshCases: () => Promise<void>
}

const DashboardContext = createContext<DashboardContextType | undefined>(undefined)

export function DashboardProvider({ children }: { children: ReactNode }) {
  const [cases, setCases] = useState<Case[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const hasLoadedRef = useRef(false)
  const isLoadingRef = useRef(false)

  const refreshCases = useCallback(async () => {
    // Don't reload if already loading (prevent concurrent loads)
    if (isLoadingRef.current) {
      return
    }
    
    isLoadingRef.current = true
    setIsLoading(true)
    try {
      // Fetch cases from API
      const response = await casesApi.list()
      let casesData = response.data || []
      
      // Sort by updated_at (most recent first), fallback to created_at if updated_at is null
      casesData.sort((a, b) => {
        const dateA = new Date(a.updated_at || a.created_at || 0).getTime()
        const dateB = new Date(b.updated_at || b.created_at || 0).getTime()
        return dateB - dateA // Descending order (newest first)
      })
      
      setCases(casesData)
      hasLoadedRef.current = true
    } catch (error: any) {
      console.error('Failed to load cases:', error)
      console.error('Error details:', error.response?.data || error.message)
      // If API is not available, set empty array
      setCases([])
      hasLoadedRef.current = true // Mark as loaded even with empty array
    } finally {
      setIsLoading(false)
      isLoadingRef.current = false
    }
  }, []) // No dependencies - function is stable, refs persist across renders

  return (
    <DashboardContext.Provider value={{ cases, setCases, isLoading, setIsLoading, refreshCases }}>
      {children}
    </DashboardContext.Provider>
  )
}

export function useDashboard() {
  const context = useContext(DashboardContext)
  if (context === undefined) {
    throw new Error('useDashboard must be used within a DashboardProvider')
  }
  return context
}
