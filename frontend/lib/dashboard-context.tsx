'use client'

import { createContext, useContext, useState, ReactNode, useRef, useCallback } from 'react'
import { Case } from '@/lib/api'
import { supabase } from '@/lib/supabase'

interface DashboardContextType {
  cases: Case[]
  setCases: (cases: Case[]) => void
  isLoading: boolean
  setIsLoading: (loading: boolean) => void
  refreshCases: () => Promise<void>
}

const DashboardContext = createContext<DashboardContextType | undefined>(undefined)

// Map Supabase case to Case interface
const mapSupabaseCase = (supabaseCase: any): Case => {
  return {
    id: supabaseCase.id,
    name: supabaseCase.name,
    case_number: supabaseCase.case_number || undefined,
    description: supabaseCase.description || undefined,
    created_at: supabaseCase.created_at,
    updated_at: supabaseCase.updated_at || undefined,
    is_active: supabaseCase.is_active !== false
  }
}

export function DashboardProvider({ children }: { children: ReactNode }) {
  const [cases, setCases] = useState<Case[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const hasLoadedRef = useRef(false)
  const isLoadingRef = useRef(false)

  const refreshCases = useCallback(async () => {
    // Don't reload if already loading or already loaded
    if (isLoadingRef.current || hasLoadedRef.current) {
      return
    }
    
    isLoadingRef.current = true
    setIsLoading(true)
    try {
      // Fetch cases from Supabase
      const { data, error } = await supabase
        .from('cases')
        .select('*')
        .eq('is_active', true)
        .order('created_at', { ascending: false })
      
      if (error) {
        console.error('Failed to load cases from Supabase:', error)
        throw error
      }
      
      // Map Supabase cases to Case interface
      const casesData = (data || []).map(mapSupabaseCase)
      setCases(casesData)
      hasLoadedRef.current = true
    } catch (error: any) {
      console.error('Failed to load cases:', error)
      // If Supabase is not available, set empty array
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
