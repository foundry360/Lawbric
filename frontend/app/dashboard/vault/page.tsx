'use client'

import { useState } from 'react'
import { Lock, Shield, Archive } from 'lucide-react'

export default function VaultPage() {
  const [activeTab, setActiveTab] = useState<'archived' | 'secure'>('archived')

  return (
    <div className="h-full overflow-y-auto p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Vault</h1>
          <p className="text-gray-600 mt-2">Secure storage for archived and sensitive content</p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('archived')}
              className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                activeTab === 'archived'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Archive className="w-4 h-4" />
              Archived
            </button>
            <button
              onClick={() => setActiveTab('secure')}
              className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                activeTab === 'secure'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Shield className="w-4 h-4" />
              Secure Documents
            </button>
          </nav>
        </div>

        {/* Content */}
        <div className="bg-white rounded-lg shadow p-6">
          {activeTab === 'archived' ? (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Archive className="w-5 h-5" />
                Archived Items
              </h2>
              <div className="text-center py-12">
                <Archive className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No archived items yet</p>
                <p className="text-sm text-gray-500 mt-2">Archived cases and documents will appear here</p>
              </div>
            </div>
          ) : (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Lock className="w-5 h-5" />
                Secure Documents
              </h2>
              <div className="text-center py-12">
                <Shield className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No secure documents yet</p>
                <p className="text-sm text-gray-500 mt-2">Encrypted and protected documents will appear here</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

