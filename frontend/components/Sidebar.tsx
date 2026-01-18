'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth'
import { useRouter, usePathname } from 'next/navigation'
import { ChevronLeft, ChevronRight, ChevronDown, ChevronUp, Plus, LayoutDashboard, Clock, Briefcase, Sliders, Folder, FolderOpen } from 'lucide-react'
import { casesApi, queriesApi, Case, Query } from '@/lib/api'

export default function Sidebar() {
  const router = useRouter()
  const pathname = usePathname()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['Cases']))
  const [cases, setCases] = useState<Case[]>([])
  const [recentQueries, setRecentQueries] = useState<Query[]>([])
  const [showAllRecent, setShowAllRecent] = useState(false)
  const [expandedCases, setExpandedCases] = useState<Set<number>>(new Set())
  const [caseQueries, setCaseQueries] = useState<Record<number, Query[]>>({})

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed)
  }

  const toggleCategory = (category: string) => {
    const newExpanded = new Set<string>()
    if (!expandedCategories.has(category)) {
      // If clicking a closed category, open only that one
      newExpanded.add(category)
    }
    // If clicking an open category, close it (newExpanded stays empty)
    setExpandedCategories(newExpanded)
  }

  const toggleCase = (caseId: number) => {
    const newExpanded = new Set<number>()
    if (!expandedCases.has(caseId)) {
      // If clicking a closed case, open only that one
      newExpanded.add(caseId)
    }
    // If clicking an open case, close it (newExpanded stays empty)
    setExpandedCases(newExpanded)
  }

  useEffect(() => {
    const loadCases = async () => {
      try {
        const response = await casesApi.list()
        setCases(response.data || [])
      } catch (error: any) {
        console.error('Failed to load cases:', error)
        // If backend is unavailable, use mock data (dev mode)
        if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error') || error.isDevBypass) {
          const mockCases: Case[] = [
            {
              id: 1,
              name: 'Adams v. New York State Department of Transportation and Infrastructure',
              case_number: 'NY459870',
              description: 'Sample case for development',
              created_at: new Date().toISOString(),
              is_active: true,
            },
            {
              id: 2,
              name: 'Smith v. Johnson Corporation',
              case_number: 'CA2024-1234',
              description: 'Sample case for development',
              created_at: new Date(Date.now() - 86400000).toISOString(),
              is_active: true,
            },
            {
              id: 3,
              name: 'Williams Estate v. Metropolitan Insurance',
              case_number: 'TX-789456',
              description: 'Sample case for development',
              created_at: new Date(Date.now() - 172800000).toISOString(),
              is_active: true,
            },
          ]
          setCases(mockCases)
        }
      }
    }
    loadCases()
    loadRecentQueries()
  }, [])

  useEffect(() => {
    // Load queries for all cases
    const loadCaseQueries = async () => {
      const queriesMap: Record<number, Query[]> = {}
      for (const caseItem of cases) {
        try {
          const response = await queriesApi.list(caseItem.id)
          queriesMap[caseItem.id] = response.data || []
        } catch (error: any) {
          // If backend is unavailable, use mock data (dev mode)
          if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error') || error.isDevBypass) {
            // Create mock queries for each case
            queriesMap[caseItem.id] = [
              {
                id: caseItem.id * 10 + 1,
                question: 'What are the key facts in this case?',
                answer: 'Sample answer',
                citations: [],
                created_at: new Date().toISOString(),
              },
              {
                id: caseItem.id * 10 + 2,
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
    }
    if (cases.length > 0) {
      loadCaseQueries()
    }
  }, [cases])

  const loadRecentQueries = async () => {
    try {
      // Get all cases first
      const casesResponse = await casesApi.list()
      const allCases = casesResponse.data || []
      
      // Fetch queries from all cases
      const allQueries: (Query & { case_name?: string; case_id?: number })[] = []
      for (const caseItem of allCases) {
        try {
          const queriesResponse = await queriesApi.list(caseItem.id)
          const queries = queriesResponse.data || []
          // Add case info to each query for display
          const queriesWithCase = queries.map(q => ({ ...q, case_name: caseItem.name, case_id: caseItem.id }))
          allQueries.push(...queriesWithCase)
        } catch (error) {
          // Skip if case has no queries or error
          console.error(`Failed to load queries for case ${caseItem.id}:`, error)
        }
      }
      
      // Sort by created_at (most recent first) and limit to 20
      const sortedQueries = allQueries
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, 20)
      
      setRecentQueries(sortedQueries as Query[])
    } catch (error: any) {
      console.error('Failed to load recent queries:', error)
      // If backend is unavailable, use mock data (dev mode)
      if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error') || error.isDevBypass) {
        const mockQueries: (Query & { case_name?: string; case_id?: number })[] = [
          {
            id: 1,
            question: 'What are the key facts in this case?',
            answer: 'Sample answer',
            citations: [],
            created_at: new Date().toISOString(),
            case_name: 'Adams v. New York State Department of Transportation and Infrastructure',
            case_id: 1,
          },
          {
            id: 2,
            question: 'Who are the parties involved?',
            answer: 'Sample answer',
            citations: [],
            created_at: new Date(Date.now() - 3600000).toISOString(),
            case_name: 'Adams v. New York State Department of Transportation and Infrastructure',
            case_id: 1,
          },
        ]
        setRecentQueries(mockQueries as Query[])
      }
    }
  }

  return (
    <div className={`${isCollapsed ? 'w-24' : 'w-64'} bg-gray-100 text-gray-900 flex flex-col border-r border-gray-200 transition-all duration-300 relative`}>
      <div className="p-6 pb-2">
        {/* Logo removed - now in header */}
      </div>
      
      <nav className="flex-1 p-4 pt-2 overflow-y-auto">
        {/* Workspace - Top level */}
        {isCollapsed ? (
          <a
            href="/dashboard"
            className={`flex items-center justify-center px-4 py-3 mb-1 rounded-lg ${
              pathname === '/dashboard' 
                ? 'text-[#000000] bg-gray-200' 
                : 'text-[#000000] hover:bg-gray-200'
            }`}
            title="Workspace"
          >
            <LayoutDashboard className="w-5 h-5" style={{ color: '#000000' }} />
          </a>
        ) : (
          <a
            href="/dashboard"
            className={`flex items-center px-3 py-1 mb-1 text-[12px] font-semibold uppercase tracking-wider ${
              pathname === '/dashboard' 
                ? 'text-[#000000] border-l-4 border-[#000000] bg-gray-200' 
                : 'text-gray-500 hover:text-[#000000] hover:bg-gray-200 border-l-4 border-transparent'
            }`}
          >
            <span>Workspace</span>
          </a>
        )}

        {/* Divider */}
        {!isCollapsed && (
          <div className="border-t border-gray-200 my-[10px]"></div>
        )}

        {/* Recent */}
        {isCollapsed ? (
          <a
            href="#"
            className="flex items-center justify-center px-4 py-3 mb-1 rounded-lg text-[#000000] hover:bg-gray-200"
            title="Recent"
          >
            <Clock className="w-5 h-5" style={{ color: '#000000' }} />
          </a>
        ) : (
          <div className="mb-[10px]">
            <div className="px-3 py-1 text-[12px] font-semibold text-gray-500 uppercase tracking-wider">
              <span>Recent</span>
            </div>
            <div className="mt-1">
              {(showAllRecent ? recentQueries.slice(0, 20) : recentQueries.slice(0, 10)).map((query: Query & { case_name?: string; case_id?: number }) => {
                const questionText = query.question.length > 35 ? `${query.question.substring(0, 35)}...` : query.question
                return (
                  <a
                    key={query.id}
                    href={query.case_id ? `/dashboard/cases/${query.case_id}` : '#'}
                    className="flex items-start gap-2 px-3 py-1.5 mb-0.5 text-[12px] hover:bg-gray-200 border-l-4 border-transparent w-full"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="text-[#000000] truncate">{questionText}</div>
                      {query.case_name && (
                        <div className="text-[11px] text-gray-600 truncate">
                          {query.case_name.length > 20 ? `${query.case_name.substring(0, 20)}...` : query.case_name}
                        </div>
                      )}
                    </div>
                  </a>
                )
              })}
              {recentQueries.length > 10 && !showAllRecent && (
                <button
                  onClick={() => setShowAllRecent(true)}
                  className="flex items-center gap-1 px-3 py-1.5 mb-0.5 text-[12px] text-[#000000] hover:bg-gray-200 border-l-4 border-transparent w-full text-left"
                >
                  <span>View all &gt;</span>
                </button>
              )}
            </div>
          </div>
        )}

        {/* Divider under Recent */}
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
            <Folder className="w-5 h-5" style={{ color: '#000000' }} />
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
                <button
                  onClick={() => {
                    // Dispatch custom event to open new case modal
                    window.dispatchEvent(new CustomEvent('openNewCaseModal'))
                  }}
                  className="flex items-center gap-3 px-3 py-1 mb-0.5 text-[12px] text-[#000000] hover:bg-gray-200 border-l-4 border-transparent w-full text-left"
                >
                  <Plus className="w-4 h-4 flex-shrink-0" style={{ color: '#000000' }} />
                  <span>New Case</span>
                </button>
                {cases.map((caseItem) => {
                  const casePath = `/dashboard/cases/${caseItem.id}`
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
                          <FolderOpen className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#000000' }} />
                        ) : (
                          <Folder className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#000000' }} />
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
                              <a
                                key={query.id}
                                href={`/dashboard/cases/${caseItem.id}`}
                                className="flex items-start gap-2 px-3 py-[5px] mb-0 text-[12px] hover:bg-gray-200 border-l-4 border-transparent w-full"
                              >
                                <div className="flex-1 min-w-0">
                                  <div className="text-[#000000] truncate">{questionText}</div>
                                </div>
                              </a>
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
          <a
            href="#"
            className="flex items-center justify-center px-4 py-3 mb-1 rounded-lg text-[#000000] hover:bg-gray-200"
            title="Tools"
          >
            <Sliders className="w-5 h-5" style={{ color: '#000000' }} />
          </a>
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
                {/* Tool items will go here */}
              </div>
            )}
          </div>
        )}
      </nav>

      <div className={`p-4 border-t border-gray-200 ${isCollapsed ? 'px-2' : ''}`}>
        <button
          onClick={toggleCollapse}
          className={`w-full flex items-center justify-center p-2 hover:bg-gray-200 text-[#000000] transition-colors ${
            isCollapsed 
              ? 'min-w-[32px] rounded-none' 
              : 'rounded-lg'
          }`}
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? (
            <ChevronRight className="w-5 h-5 flex-shrink-0" style={{ color: '#000000' }} />
          ) : (
            <ChevronLeft className="w-5 h-5 flex-shrink-0" style={{ color: '#000000' }} />
          )}
        </button>
      </div>
    </div>
  )
}

