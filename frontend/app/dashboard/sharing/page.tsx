'use client'

import { useState } from 'react'

export default function SharingCenterPage() {
  const [activeTab, setActiveTab] = useState<'shared' | 'received'>('shared')

  return (
    <div className="h-full overflow-y-auto p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Sharing Center</h1>
          <p className="text-gray-600 mt-2">Manage shared cases, documents, and queries</p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('shared')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'shared'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Shared by Me
            </button>
            <button
              onClick={() => setActiveTab('received')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'received'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Shared with Me
            </button>
          </nav>
        </div>

        {/* Content */}
        <div className="bg-white rounded-lg shadow p-6">
          {activeTab === 'shared' ? (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Shared by Me</h2>
              <div className="text-center py-12">
                <p className="text-gray-600">No shared items yet</p>
                <p className="text-sm text-gray-500 mt-2">Items you share with others will appear here</p>
              </div>
            </div>
          ) : (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Shared with Me</h2>
              <div className="text-center py-12">
                <p className="text-gray-600">No shared items yet</p>
                <p className="text-sm text-gray-500 mt-2">Items shared with you will appear here</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

