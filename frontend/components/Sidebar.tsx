'use client'

import { useState, useEffect, memo } from 'react'
import Link from 'next/link'
import { useAuth } from '@/lib/auth'
import { useRouter, usePathname } from 'next/navigation'
import { PanelLeftClose, PanelLeftOpen, ChevronDown, ChevronUp, LayoutDashboard, Briefcase, Sliders, FolderClosed, FolderOpen, Share2, ShieldCheck, Link as LinkIcon, Settings } from 'lucide-react'
import { casesApi, queriesApi, Case, Query } from '@/lib/api'
import { useDashboard } from '@/lib/dashboard-context'

function Sidebar() {
  const router = useRouter()
  const pathname = usePathname()
  const [isCollapsed, setIsCollapsed] = useState(false)
  // Load persisted expanded categories from localStorage
  const loadExpandedCategories = (): Set<string> => {
    if (typeof window === 'undefined') return new Set(['Cases'])
    try {
      const saved = localStorage.getItem('sidebarExpandedCategories')
      if (saved) {
        const categories = JSON.parse(saved) as string[]
        return new Set(categories)
      }
    } catch (e) {
      console.warn('Failed to load expanded categories from localStorage:', e)
    }
    return new Set(['Cases'])
  }

  // Load persisted expanded cases from localStorage
  const loadExpandedCases = (): Set<string | number> => {
    if (typeof window === 'undefined') return new Set()
    try {
      const saved = localStorage.getItem('sidebarExpandedCases')
      if (saved) {
        const caseIds = JSON.parse(saved) as (string | number)[]
        return new Set(caseIds)
      }
    } catch (e) {
      console.warn('Failed to load expanded cases from localStorage:', e)
    }
    return new Set()
  }

  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(loadExpandedCategories)
  // Use dashboard context for cases instead of loading independently
  const { cases, refreshCases } = useDashboard()
  const [expandedCases, setExpandedCases] = useState<Set<string | number>>(loadExpandedCases)
  const [caseQueries, setCaseQueries] = useState<Record<string | number, Query[]>>({})
  const [dataLoaded, setDataLoaded] = useState(false)
  
  // Filter cases to only show those that were recently worked on (have queries in last 30 days)
  const getRecentlyWorkedOnCases = (): Case[] => {
    const thirtyDaysAgo = new Date()
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)
    
    return cases.filter((caseItem) => {
      const queries = caseQueries[caseItem.id] || []
      // Check if case has any queries created in the last 30 days
      const hasRecentQueries = queries.some((query) => {
        const queryDate = new Date(query.created_at)
        return queryDate >= thirtyDaysAgo
      })
      // If no queries loaded yet, show the case (will be filtered once queries load)
      // Or if case has recent queries, show it
      return Object.keys(caseQueries).length === 0 || hasRecentQueries
    })
  }
  
  const recentlyWorkedOnCases = getRecentlyWorkedOnCases()

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed)
  }

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories)
    if (newExpanded.has(category)) {
      // If clicking an open category, close it
      newExpanded.delete(category)
    } else {
      // If clicking a closed category, open it (keep others open)
      newExpanded.add(category)
    }
    setExpandedCategories(newExpanded)
    // Persist to localStorage
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('sidebarExpandedCategories', JSON.stringify(Array.from(newExpanded)))
      } catch (e) {
        console.warn('Failed to save expanded categories to localStorage:', e)
      }
    }
  }

  const toggleCase = (caseId: string | number) => {
    const newExpanded = new Set(expandedCases)
    if (newExpanded.has(caseId)) {
      // If clicking an open case, close it
      newExpanded.delete(caseId)
    } else {
      // If clicking a closed case, open it (keep others open)
      newExpanded.add(caseId)
    }
    setExpandedCases(newExpanded)
    // Persist to localStorage
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('sidebarExpandedCases', JSON.stringify(Array.from(newExpanded)))
      } catch (e) {
        console.warn('Failed to save expanded cases to localStorage:', e)
      }
    }
  }

  const [queriesLoaded, setQueriesLoaded] = useState(false)

  useEffect(() => {
    // Only load case queries if cases exist and we haven't loaded them yet
    if (cases.length > 0 && Object.keys(caseQueries).length === 0) {
      const loadCaseQueries = async () => {
        const queriesMap: Record<string | number, Query[]> = {}
        for (const caseItem of cases) {
          try {
            // Convert case ID to number for API call (legacy support)
            // TODO: Update queries API to use UUID when queries table is migrated
            const caseId = typeof caseItem.id === 'string' ? parseInt(caseItem.id) : caseItem.id
            const response = await queriesApi.list(caseId)
            queriesMap[caseItem.id] = response.data || []
          } catch (error: any) {
            // If backend is unavailable, use mock data (dev mode)
            if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error') || error.isDevBypass) {
              // Create mock queries for each case
              const mockId = typeof caseItem.id === 'string' ? 1 : caseItem.id
              queriesMap[caseItem.id] = [
                {
                  id: mockId * 10 + 1,
                  question: 'What are the key facts in this case?',
                  answer: 'Sample answer',
                  citations: [],
                  created_at: new Date().toISOString(),
                },
                {
                  id: mockId * 10 + 2,
                  question: 'Who are the parties involved?',
                  answer: 'Sample answer',
                  citations: [],
                  created_at: new Date(Date.now() - 3600000).toISOString(),
                },
              ]
            } else {
              queriesMap[caseItem.id] = []
            }
          }
        }
        setCaseQueries(queriesMap)
        setQueriesLoaded(true)
      }
      loadCaseQueries()
    }
  }, [cases, caseQueries])


  return (
    <div className={`${isCollapsed ? 'w-24' : 'w-64'} bg-gray-100 text-gray-900 flex flex-col border-r border-gray-200 transition-all duration-300 relative`}>
      <div className="p-6 pb-2">
        {/* Logo removed - now in header */}
      </div>
      
      <nav className="flex-1 p-4 pt-2 overflow-y-auto">
        {/* Workspace - Top level */}
        {isCollapsed ? (
          <Link
            href="/workspace"
            className={`flex items-center justify-center px-4 py-3 mb-1 rounded-lg ${
              pathname === '/workspace' 
                ? 'text-[#000000] bg-gray-200' 
                : 'text-[#000000] hover:bg-gray-200'
            }`}
            title="Workspace"
          >
            <LayoutDashboard className="w-5 h-5" style={{ color: pathname === '/workspace' ? '#000000' : '#6b7280' }} />
          </Link>
        ) : (
          <Link
            href="/workspace"
            className={`flex items-center px-3 py-1 mb-1 text-[12px] font-semibold uppercase tracking-wider ${
              pathname === '/workspace' 
                ? 'text-[#000000] border-l-4 border-[#000000] bg-gray-200' 
                : 'text-gray-500 hover:text-[#000000] hover:bg-gray-200 border-l-4 border-transparent'
            }`}
          >
            <span>Workspace</span>
          </Link>
        )}

        {/* Sharing Center */}
        {isCollapsed ? (
          <Link
            href="/sharing"
            className={`flex items-center justify-center px-4 py-3 mb-1 rounded-lg ${
              pathname === '/sharing' 
                ? 'text-[#000000] bg-gray-200' 
                : 'text-[#000000] hover:bg-gray-200'
            }`}
            title="Sharing Center"
          >
            <Share2 className="w-5 h-5" style={{ color: pathname === '/sharing' ? '#000000' : '#6b7280' }} />
          </Link>
        ) : (
          <Link
            href="/sharing"
            className={`flex items-center px-3 py-1 mb-1 text-[12px] font-semibold uppercase tracking-wider ${
              pathname === '/sharing' 
                ? 'text-[#000000] border-l-4 border-[#000000] bg-gray-200' 
                : 'text-gray-500 hover:text-[#000000] hover:bg-gray-200 border-l-4 border-transparent'
            }`}
          >
            <span>Sharing Center</span>
          </Link>
        )}

        {/* Vault */}
        {isCollapsed ? (
          <Link
            href="/vault"
            className={`flex items-center justify-center px-4 py-3 mb-1 rounded-lg ${
              pathname === '/vault' 
                ? 'text-[#000000] bg-gray-200' 
                : 'text-[#000000] hover:bg-gray-200'
            }`}
            title="Vault"
          >
            <ShieldCheck className="w-5 h-5" style={{ color: pathname === '/vault' ? '#000000' : '#6b7280' }} />
          </Link>
        ) : (
          <Link
            href="/vault"
            className={`flex items-center px-3 py-1 mb-1 text-[12px] font-semibold uppercase tracking-wider ${
              pathname === '/vault' 
                ? 'text-[#000000] border-l-4 border-[#000000] bg-gray-200' 
                : 'text-gray-500 hover:text-[#000000] hover:bg-gray-200 border-l-4 border-transparent'
            }`}
          >
            <span>Vault</span>
          </Link>
        )}

        {/* Divider */}
        {!isCollapsed && (
          <div className="border-t border-gray-200 my-[10px]"></div>
        )}

        {/* Cases */}
        {isCollapsed ? (
          <a
            href="#"
            className="flex items-center justify-center px-4 py-3 mb-1 rounded-lg text-[#000000] hover:bg-gray-200"
            title="Cases"
          >
            <FolderClosed className="w-5 h-5" style={{ color: '#6b7280' }} />
          </a>
        ) : (
          <div className="mb-[10px]">
            <button
              onClick={() => toggleCategory('Cases')}
              className="w-full flex items-center justify-between px-3 py-1 text-[12px] font-semibold text-gray-500 uppercase tracking-wider hover:text-[#000000]"
            >
              <span>Cases</span>
              {expandedCategories.has('Cases') ? (
                <ChevronUp className="w-4 h-4" style={{ color: '#000000' }} />
              ) : (
                <ChevronDown className="w-4 h-4" style={{ color: '#000000' }} />
              )}
            </button>
            {expandedCategories.has('Cases') && (
              <div className="mt-1">
                {recentlyWorkedOnCases.map((caseItem) => {
                  const casePath = `/cases/${caseItem.id}`
                  const isActive = pathname === casePath || pathname?.startsWith(casePath + '/')
                  const isExpanded = expandedCases.has(caseItem.id)
                  const queries = caseQueries[caseItem.id] || []
                  return (
                    <div key={caseItem.id} className="mb-0">
                      <button
                        onClick={() => {
                          toggleCase(caseItem.id)
                          router.push(casePath)
                        }}
                        className={`flex items-start gap-3 px-3 py-[6px] text-[12px] border-l-4 w-full text-left ${
                          isActive
                            ? 'bg-gray-200 text-[#000000] border-l-4 border-[#000000]' 
                            : 'text-[#000000] hover:bg-gray-200 border-transparent'
                        }`}
                      >
                        {isActive ? (
                          <FolderOpen className="w-4 h-4 flex-shrink-0 mt-0.5 text-gray-600" />
                        ) : (
                          <FolderClosed className="w-4 h-4 flex-shrink-0 mt-0.5 text-gray-600" />
                        )}
                        <div className="flex-1 min-w-0">
                            <div className="font-medium truncate">
                              {caseItem.name.length > 25 ? `${caseItem.name.substring(0, 25)}...` : caseItem.name}
                            </div>
                          {caseItem.case_number && (
                            <div className="text-[11px] text-gray-600 truncate">{caseItem.case_number}</div>
                          )}
                        </div>
                      </button>
                      {isExpanded && queries.length > 0 && (
                        <div className="ml-8 mt-0.5">
                          {queries.map((query) => {
                            const questionText = query.question.length > 30 ? `${query.question.substring(0, 30)}...` : query.question
                            return (
                              <Link
                                key={query.id}
                                href={`/cases/${caseItem.id}`}
                                className="flex items-start gap-2 px-3 py-[5px] mb-0 text-[12px] hover:bg-gray-200 border-l-4 border-transparent w-full"
                              >
                                <div className="flex-1 min-w-0">
                                  <div className="text-[#000000] truncate">{questionText}</div>
                                </div>
                              </Link>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* Tools */}
        {isCollapsed ? (
          <>
            <Link
              href="/settings"
              className={`flex items-center justify-center px-4 py-3 mb-1 rounded-lg ${
                pathname === '/settings' 
                  ? 'text-[#000000] bg-gray-200' 
                  : 'text-[#000000] hover:bg-gray-200'
              }`}
              title="Settings"
            >
              <Settings className="w-5 h-5" style={{ color: pathname === '/settings' ? '#000000' : '#6b7280' }} />
            </Link>
            <Link
              href="/connected-apps"
              className={`flex items-center justify-center px-4 py-3 mb-1 rounded-lg ${
                pathname === '/connected-apps' 
                  ? 'text-[#000000] bg-gray-200' 
                  : 'text-[#000000] hover:bg-gray-200'
              }`}
              title="Connected Apps"
            >
              <LinkIcon className="w-5 h-5" style={{ color: pathname === '/connected-apps' ? '#000000' : '#6b7280' }} />
            </Link>
          </>
        ) : (
          <div className="mb-[10px]">
            <button
              onClick={() => toggleCategory('Tools')}
              className="w-full flex items-center justify-between px-3 py-1 text-[12px] font-semibold text-gray-500 uppercase tracking-wider hover:text-[#000000]"
            >
              <span>Tools</span>
              {expandedCategories.has('Tools') ? (
                <ChevronUp className="w-4 h-4" style={{ color: '#000000' }} />
              ) : (
                <ChevronDown className="w-4 h-4" style={{ color: '#000000' }} />
              )}
            </button>
            {expandedCategories.has('Tools') && (
              <div className="mt-1">
                <Link
                  href="/settings"
                  className={`flex items-center gap-3 px-3 py-1 mb-0.5 text-[12px] border-l-4 w-full ${
                    pathname === '/settings'
                      ? 'bg-gray-200 text-[#000000] border-l-4 border-[#000000]' 
                      : 'text-[#000000] hover:bg-gray-200 border-transparent'
                  }`}
                >
                  <Settings className="w-4 h-4 flex-shrink-0 text-gray-600" />
                  <span>Settings</span>
                </Link>
                <Link
                  href="/connected-apps"
                  className={`flex items-center gap-3 px-3 py-1 mb-0.5 text-[12px] border-l-4 w-full ${
                    pathname === '/connected-apps'
                      ? 'bg-gray-200 text-[#000000] border-l-4 border-[#000000]' 
                      : 'text-[#000000] hover:bg-gray-200 border-transparent'
                  }`}
                >
                  <LinkIcon className="w-4 h-4 flex-shrink-0 text-gray-600" />
                  <span>Connected Apps</span>
                </Link>
              </div>
            )}
          </div>
        )}
      </nav>

      <div className={`p-4 border-t border-gray-200 ${isCollapsed ? 'px-2' : ''}`}>
        <button
          onClick={toggleCollapse}
          className={`w-full flex items-center p-2 hover:bg-gray-200 text-[#000000] transition-colors ${
            isCollapsed 
              ? 'min-w-[32px] rounded-none justify-center' 
              : 'rounded-lg justify-end'
          }`}
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? (
            <PanelLeftOpen className="w-5 h-5 flex-shrink-0" style={{ color: '#9ca3af' }} />
          ) : (
            <PanelLeftClose className="w-5 h-5 flex-shrink-0" style={{ color: '#9ca3af' }} />
          )}
        </button>
      </div>
    </div>
  )
}

export default memo(Sidebar)

