'use client'

import { useState } from 'react'
import { Plug2, CheckCircle, X } from 'lucide-react'

export default function ConnectedAppsPage() {
  const [connectedApps] = useState<any[]>([])

  return (
    <div className="h-full overflow-y-auto p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Connected Apps</h1>
          <p className="text-gray-600 mt-2">Manage integrations and connected third-party applications</p>
        </div>

        {/* Connected Apps List */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Connected Applications</h2>
          
          {connectedApps.length === 0 ? (
            <div className="text-center py-12">
              <Plug2 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No connected apps yet</p>
              <p className="text-sm text-gray-500 mt-2">Connect third-party applications to enhance your workflow</p>
            </div>
          ) : (
            <div className="space-y-4">
              {connectedApps.map((app) => (
                <div
                  key={app.id}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-gray-200 rounded-lg flex items-center justify-center">
                      <Plug2 className="w-5 h-5 text-gray-600" />
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">{app.name}</h3>
                      <p className="text-xs text-gray-500">{app.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <button className="text-red-600 hover:text-red-700">
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Available Apps */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Available Integrations</h2>
          <div className="text-center py-12">
            <p className="text-gray-600">No available integrations at this time</p>
            <p className="text-sm text-gray-500 mt-2">New integrations will appear here when available</p>
          </div>
        </div>
      </div>
    </div>
  )
}

