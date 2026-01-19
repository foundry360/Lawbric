'use client'

import { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { usersApi, AppUser } from '@/lib/api'
import { mapSupabaseUserWithProfile, getCurrentUser } from '@/lib/supabase-auth'
import { supabase } from '@/lib/supabase'
import Image from 'next/image'
import { Settings, ArrowLeft, Trash2, X, Camera, MoreVertical, Edit } from 'lucide-react'

type SettingsTab = 'account' | 'notifications' | 'appearance' | 'users'

export default function SettingsPage() {
  const router = useRouter()
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<SettingsTab>('account')
  const [notifications, setNotifications] = useState(true)
  const [emailUpdates, setEmailUpdates] = useState(false)
  const [theme, setTheme] = useState('light')
  const [displayUser, setDisplayUser] = useState(user) // Local state to hold fresh profile data
  const [uploadingAvatar, setUploadingAvatar] = useState(false)
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const isAdmin = user?.role === 'admin' || user?.role === 'ADMIN'
  
  // Fetch fresh profile data on mount and when user changes
  useEffect(() => {
    const refreshProfile = async () => {
      if (user?.id) {
        try {
          const currentUser = await getCurrentUser()
          if (currentUser) {
            const profileUser = await mapSupabaseUserWithProfile(currentUser)
            if (profileUser) {
              console.log('✅ Fetched fresh profile for settings page:', profileUser)
              console.log('   - role:', profileUser.role)
              console.log('   - title:', profileUser.title)
              console.log('   - title type:', typeof profileUser.title)
              setDisplayUser(profileUser)
            } else {
              console.warn('⚠️ profileUser is null')
            }
          }
        } catch (error) {
          console.error('Error fetching fresh profile:', error)
          // Fall back to user from context
          setDisplayUser(user)
        }
      } else {
        setDisplayUser(user)
      }
    }
    
    refreshProfile()
  }, [user?.id]) // Only re-fetch if user ID changes

  // Use displayUser for rendering (has fresh profile data) or fall back to user from context
  const userToDisplay = displayUser || user

  // Handle avatar upload
  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !user?.id) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      alert('Image size must be less than 5MB')
      return
    }

    setUploadingAvatar(true)
    
    try {
      // Create preview
      const reader = new FileReader()
      reader.onloadend = () => {
        setAvatarPreview(reader.result as string)
      }
      reader.readAsDataURL(file)

      // Upload to Supabase storage
      const fileExt = file.name.split('.').pop()
      const fileName = `${user.id}-${Date.now()}.${fileExt}`
      const filePath = fileName

      console.log('📤 Uploading file to storage:', filePath)
      const { data: uploadData, error: uploadError } = await supabase.storage
        .from('profile-avatars')
        .upload(filePath, file, {
          cacheControl: '3600',
          upsert: false
        })

      if (uploadError) {
        console.error('❌ Storage upload error:', uploadError)
        console.error('   Error code:', uploadError.error)
        console.error('   Error message:', uploadError.message)
        throw uploadError
      }
      
      console.log('✅ File uploaded successfully:', uploadData)

      // Get public URL
      const { data } = supabase.storage
        .from('profile-avatars')
        .getPublicUrl(filePath)

      const avatarUrl = data.publicUrl

      // Update profile in database
      console.log('🔄 Updating profile with avatar_url:', avatarUrl)
      console.log('   User ID:', user.id)
      const { data: sessionData } = await supabase.auth.getSession()
      console.log('   Current session:', !!sessionData.session)
      console.log('   Session user ID:', sessionData.session?.user?.id)
      
      const { data: updateData, error: updateError } = await supabase
        .from('profiles')
        .update({ avatar_url: avatarUrl })
        .eq('id', user.id)
        .select()

      if (updateError) {
        console.error('❌ Update error:', updateError)
        console.error('   Error code:', updateError.code)
        console.error('   Error message:', updateError.message)
        console.error('   Error details:', updateError.details)
        console.error('   Error hint:', updateError.hint)
        throw updateError
      }
      
      console.log('✅ Profile updated successfully:', updateData)

      // Refresh user profile
      const currentUser = await getCurrentUser()
      if (currentUser) {
        const profileUser = await mapSupabaseUserWithProfile(currentUser)
        if (profileUser) {
          setDisplayUser(profileUser)
          // Update auth context user
          if (typeof window !== 'undefined') {
            window.location.reload() // Simple way to refresh user context
          }
        }
      }

      setAvatarPreview(null) // Clear preview after successful upload
    } catch (error: any) {
      console.error('Error uploading avatar:', error)
      alert(`Failed to upload avatar: ${error.message || 'Unknown error'}`)
      setAvatarPreview(null)
    } finally {
      setUploadingAvatar(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  // Handle remove avatar
  const handleRemoveAvatar = async () => {
    if (!user?.id || !displayUser?.avatar_url) return

    if (!confirm('Are you sure you want to remove your profile picture?')) {
      return
    }

    setUploadingAvatar(true)

    try {
      // Extract file path from URL
      const urlParts = displayUser.avatar_url.split('/')
      const fileName = urlParts[urlParts.length - 1]
      const filePath = fileName

      // Delete from storage
      const { error: deleteError } = await supabase.storage
        .from('profile-avatars')
        .remove([filePath])

      if (deleteError) {
        console.warn('Error deleting file from storage (continuing):', deleteError)
      }

      // Update profile to remove avatar_url
      const { error: updateError } = await supabase
        .from('profiles')
        .update({ avatar_url: null })
        .eq('id', user.id)

      if (updateError) throw updateError

      // Refresh user profile
      const currentUser = await getCurrentUser()
      if (currentUser) {
        const profileUser = await mapSupabaseUserWithProfile(currentUser)
        if (profileUser) {
          setDisplayUser(profileUser)
        }
      }

      setAvatarPreview(null)
    } catch (error: any) {
      console.error('Error removing avatar:', error)
      alert(`Failed to remove avatar: ${error.message || 'Unknown error'}`)
    } finally {
      setUploadingAvatar(false)
    }
  }

  // Debug logging
  useEffect(() => {
    if (userToDisplay) {
      console.log('Settings page - Current user:', {
        id: userToDisplay.id,
        email: userToDisplay.email,
        role: userToDisplay.role,
        title: userToDisplay.title,
        isAdmin: isAdmin
      })
    }
  }, [userToDisplay, isAdmin])

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/dashboard')}
            className="p-2 rounded-lg hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition-colors"
            title="Back to Dashboard"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-3">
            <Settings className="w-6 h-6 text-gray-900" />
            <h1 className="text-xl font-bold text-gray-900">Settings</h1>
          </div>
        </div>
      </div>

      {/* Settings Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-5xl mx-auto">
          {/* Horizontal Navigation Tabs */}
          <div className="border-b border-gray-200 mb-6 relative">
            <nav className="flex items-center gap-1">
              <button
                onClick={() => setActiveTab('account')}
                className={`px-4 py-2 text-sm font-medium transition-colors relative ${
                  activeTab === 'account'
                    ? 'text-gray-900'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Account
                {activeTab === 'account' && (
                  <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-black"></div>
                )}
              </button>
              <button
                onClick={() => setActiveTab('notifications')}
                className={`px-4 py-2 text-sm font-medium transition-colors relative ${
                  activeTab === 'notifications'
                    ? 'text-gray-900'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Notifications
                {activeTab === 'notifications' && (
                  <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-black"></div>
                )}
              </button>
              <button
                onClick={() => setActiveTab('appearance')}
                className={`px-4 py-2 text-sm font-medium transition-colors relative ${
                  activeTab === 'appearance'
                    ? 'text-gray-900'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Appearance
                {activeTab === 'appearance' && (
                  <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-black"></div>
                )}
              </button>
              {isAdmin && (
                <button
                  onClick={() => setActiveTab('users')}
                  className={`px-4 py-2 text-sm font-medium transition-colors relative ${
                    activeTab === 'users'
                      ? 'text-gray-900'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  User Management
                  {activeTab === 'users' && (
                    <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-black"></div>
                  )}
                </button>
              )}
            </nav>
          </div>

          {/* Settings Content Area */}
          <div className="space-y-8">
              {/* Account Tab */}
              {activeTab === 'account' && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h2 className="text-base font-semibold text-gray-900 mb-4">Account</h2>
                  <div className="space-y-4">
                    {/* Avatar Upload */}
                    <div>
                      <label className="block text-sm font-medium text-gray-900 mb-2">Profile Picture</label>
                      <div className="flex items-center gap-4">
                        <div className="relative">
                          <input
                            type="file"
                            ref={fileInputRef}
                            accept="image/*"
                            className="hidden"
                            onChange={handleAvatarUpload}
                          />
                          <button
                            type="button"
                            onClick={() => fileInputRef.current?.click()}
                            disabled={uploadingAvatar}
                            className="relative group cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {displayUser?.avatar_url || avatarPreview ? (
                              <div className="relative w-20 h-20 rounded-full overflow-hidden border-2 border-gray-200">
                                <Image
                                  src={avatarPreview || displayUser?.avatar_url || ''}
                                  alt="Profile avatar"
                                  fill
                                  className="object-cover"
                                />
                                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-all flex items-center justify-center rounded-full">
                                  <Camera className="w-6 h-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                                </div>
                              </div>
                            ) : (
                              <div className="w-20 h-20 rounded-full bg-primary-600 flex items-center justify-center text-white font-semibold text-lg border-2 border-gray-200 relative">
                                {(displayUser?.email || 'U')[0].toUpperCase()}
                                <div className="absolute inset-0 flex items-center justify-center">
                                  <Camera className="w-6 h-6 text-white opacity-60" />
                                </div>
                              </div>
                            )}
                          </button>
                        </div>
                        {(displayUser?.avatar_url || avatarPreview) && (
                          <button
                            type="button"
                            onClick={handleRemoveAvatar}
                            disabled={uploadingAvatar}
                            className="px-3 py-1.5 text-xs bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                          >
                            <X className="w-3 h-3" />
                            Remove
                          </button>
                        )}
                      </div>
                      <p className="text-xs text-gray-500 mt-1">JPG, PNG or GIF. Max size 5MB</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-900 mb-2">Email</label>
                      <input
                        type="email"
                        value={userToDisplay?.email || ''}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-gray-50"
                        readOnly
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-900 mb-2">Full Name</label>
                      <input
                        type="text"
                        value={userToDisplay?.full_name || ''}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-gray-50"
                        readOnly
                      />
                    </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-900 mb-2">Role</label>
                    <input
                      type="text"
                      value={userToDisplay?.role || 'user'}
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-gray-50 capitalize"
                      readOnly
                    />
                    <p className="text-xs text-gray-500 mt-1">Permissions level (user or admin)</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-900 mb-2">Title</label>
                    <input
                      type="text"
                      value={userToDisplay?.title ?? ''}
                      placeholder="attorney"
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-gray-50 capitalize"
                      readOnly
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Job title (attorney, paralegal, finance, etc.)
                      {!userToDisplay?.title && <span className="text-red-500 ml-2">⚠️ Title not loaded</span>}
                    </p>
                  </div>
                    <div>
                      <button className="px-4 py-2 text-sm bg-black text-white rounded-lg hover:bg-gray-900 transition-colors">
                        Change Password
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Notifications Tab */}
              {activeTab === 'notifications' && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h2 className="text-base font-semibold text-gray-900 mb-4">Notifications</h2>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">Enable Notifications</p>
                        <p className="text-xs text-gray-600">Receive notifications for important updates</p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={notifications}
                          onChange={(e) => setNotifications(e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                      </label>
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">Email Updates</p>
                        <p className="text-xs text-gray-600">Receive email notifications for case updates</p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={emailUpdates}
                          onChange={(e) => setEmailUpdates(e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                      </label>
                    </div>
                  </div>
                </div>
              )}

              {/* Appearance Tab */}
              {activeTab === 'appearance' && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h2 className="text-base font-semibold text-gray-900 mb-4">Appearance</h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-900 mb-2">Theme</label>
                      <select
                        value={theme}
                        onChange={(e) => setTheme(e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      >
                        <option value="light">Light</option>
                        <option value="dark">Dark</option>
                        <option value="system">System</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* User Management Tab (Admin Only) */}
              {activeTab === 'users' && isAdmin && (
                <UserManagementSection />
              )}
          </div>
        </div>
      </div>
    </div>
  )
}

// User Management Component
function UserManagementSection() {
  const [users, setUsers] = useState<AppUser[]>([])
  const [loading, setLoading] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingUser, setEditingUser] = useState<AppUser | null>(null)
  const [newUser, setNewUser] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'user',  // user or admin (permissions)
    title: 'attorney'  // attorney, paralegal, finance, etc. (job title)
  })
  const [editUser, setEditUser] = useState({
    full_name: '',
    role: 'user',
    title: 'attorney'
  })
  const [error, setError] = useState('')
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)
  const [menuPosition, setMenuPosition] = useState<{ top: number; right: number } | null>(null)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [userToDelete, setUserToDelete] = useState<AppUser | null>(null)
  const [deleteConfirmText, setDeleteConfirmText] = useState('')
  const menuRefs = useRef<{ [key: string]: HTMLDivElement | null }>({})

  // Load users on mount
  useEffect(() => {
    loadUsers()
  }, [])

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const clickedElement = event.target as HTMLElement
      // Check if click is inside any menu button or the dropdown menu itself
      const isClickInsideButton = Object.values(menuRefs.current).some(
        (ref) => ref && ref.contains(clickedElement)
      )
      const isClickInsideMenu = clickedElement.closest('[data-dropdown-menu]')
      
      if (!isClickInsideButton && !isClickInsideMenu) {
        setOpenMenuId(null)
        setMenuPosition(null)
      }
    }

    if (openMenuId) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [openMenuId])

  const loadUsers = async () => {
    setLoading(true)
    setError('')
    try {
      console.log('🔄 Loading users from Supabase...')
      
      // Fetch users directly from Supabase profiles table
      const { data, error: supabaseError } = await supabase
        .from('profiles')
        .select('*')
        .order('created_at', { ascending: false })
      
      if (supabaseError) {
        console.error('❌ Supabase error loading users:', supabaseError)
        console.error('   Error code:', supabaseError.code)
        console.error('   Error message:', supabaseError.message)
        console.error('   Error details:', supabaseError.details)
        throw supabaseError
      }
      
      console.log('✅ Loaded users from Supabase:', data?.length || 0)
      
      // Map to AppUser format
      const mappedUsers: AppUser[] = (data || []).map((profile: any) => ({
        id: profile.id,
        email: profile.email,
        full_name: profile.full_name || undefined,
        role: profile.role || 'user',
        title: profile.title || 'attorney',
        avatar_url: profile.avatar_url || undefined,
        is_active: profile.is_active !== false
      }))
      
      setUsers(mappedUsers)
    } catch (err: any) {
      console.error('❌ Failed to load users:', err)
      const errorMsg = err.message || err.details || 'Failed to load users'
      setError(errorMsg)
      setUsers([])
    } finally {
      setLoading(false)
    }
  }

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    try {
      await usersApi.create({
        email: newUser.email,
        password: newUser.password,
        full_name: newUser.full_name || undefined,
        role: newUser.role,
        title: newUser.title
      })
      
      // Reload users
      await loadUsers()
      setShowCreateModal(false)
      setNewUser({ email: '', password: '', full_name: '', role: 'user', title: 'attorney' })
    } catch (err: any) {
      console.error('Failed to create user:', err)
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to create user'
      setError(errorMsg)
    }
  }

  const handleDeleteUser = (userId: string) => {
    setOpenMenuId(null) // Close menu
    setMenuPosition(null) // Clear menu position
    const user = users.find(u => u.id === userId)
    if (user) {
      setUserToDelete(user)
      setDeleteConfirmText('')
      setShowDeleteModal(true)
    }
  }

  const confirmDeleteUser = async () => {
    if (!userToDelete || deleteConfirmText.toLowerCase() !== 'delete user') {
      return
    }

    setDeletingId(userToDelete.id)
    try {
      // Delete user from Supabase (this will cascade delete the profile)
      // Note: We can't directly delete from auth.users via the client SDK
      // This should be done via the backend API with admin privileges
      // For now, we'll use the backend API
      await usersApi.delete(userToDelete.id)
      await loadUsers()
      setShowDeleteModal(false)
      setUserToDelete(null)
      setDeleteConfirmText('')
    } catch (err: any) {
      console.error('Failed to delete user:', err)
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to delete user'
      setError(errorMsg)
    } finally {
      setDeletingId(null)
    }
  }

  const handleEditUser = (userId: string) => {
    setOpenMenuId(null) // Close menu
    setMenuPosition(null) // Clear menu position
    const user = users.find(u => u.id === userId)
    if (user) {
      setEditingUser(user)
      setEditUser({
        full_name: user.full_name || '',
        role: user.role || 'user',
        title: user.title || 'attorney'
      })
      setShowEditModal(true)
      setError('')
    }
  }

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingUser) return
    
    setError('')
    
    try {
      // Update user profile in Supabase
      const { error: updateError } = await supabase
        .from('profiles')
        .update({
          full_name: editUser.full_name || null,
          role: editUser.role,
          title: editUser.title
        })
        .eq('id', editingUser.id)
      
      if (updateError) throw updateError
      
      // Reload users
      await loadUsers()
      setShowEditModal(false)
      setEditingUser(null)
      setEditUser({ full_name: '', role: 'user', title: 'attorney' })
    } catch (err: any) {
      console.error('Failed to update user:', err)
      const errorMsg = err.message || err.details || 'Failed to update user'
      setError(errorMsg)
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-base font-semibold text-gray-900">User Management</h2>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-900 transition-colors flex items-center gap-2"
        >
          <span>+</span>
          Create User
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-900">Loading users...</div>
      ) : (
        <div className="overflow-x-auto" style={{ overflowY: 'visible' }}>
          <table className="w-full border-collapse bg-white">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left py-2 px-4 text-sm font-semibold text-gray-900">Email</th>
                <th className="text-left py-2 px-4 text-sm font-semibold text-gray-900">Full Name</th>
                <th className="text-left py-2 px-4 text-sm font-semibold text-gray-900">Role</th>
                <th className="text-left py-2 px-4 text-sm font-semibold text-gray-900">Title</th>
                <th className="text-right py-2 px-4 text-sm font-semibold text-gray-900">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 px-4 text-center text-sm text-gray-500">
                    No users found. Click "Create User" to add your first user.
                  </td>
                </tr>
              ) : (
                users.map((user) => (
                <tr key={user.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 px-4 text-sm text-gray-900">{user.email}</td>
                  <td className="py-2 px-4 text-sm text-gray-900">{user.full_name || '-'}</td>
                  <td className="py-2 px-4">
                    <span className={`px-2 py-1 text-sm font-medium rounded capitalize ${
                      user.role === 'admin' 
                        ? 'text-blue-800' 
                        : 'text-gray-800'
                    }`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="py-2 px-4">
                    <span className="px-2 py-1 text-sm font-medium rounded text-gray-800 capitalize">
                      {user.title || 'attorney'}
                    </span>
                  </td>
                  <td className="py-2 px-4 text-right text-sm text-gray-900 relative">
                    <div className="inline-block" ref={(el) => { menuRefs.current[user.id] = el }}>
                      <button
                        onClick={(e) => {
                          const buttonElement = e.currentTarget
                          const rect = buttonElement.getBoundingClientRect()
                          setMenuPosition({
                            top: rect.bottom + 4,
                            right: window.innerWidth - rect.right
                          })
                          setOpenMenuId(openMenuId === user.id ? null : user.id)
                        }}
                        className="p-1 rounded hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition-colors"
                        title="Actions"
                      >
                        <MoreVertical className="w-4 h-4" />
                      </button>
                      {openMenuId === user.id && menuPosition && typeof window !== 'undefined' && createPortal(
                        <div
                          data-dropdown-menu
                          className="fixed w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-50"
                          style={{
                            top: `${menuPosition.top}px`,
                            right: `${menuPosition.right}px`
                          }}
                        >
                          <button
                            onClick={() => handleEditUser(user.id)}
                            className="w-full text-left px-4 py-2 text-xs text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                          >
                            <Edit className="w-3 h-3" />
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteUser(user.id)}
                            disabled={deletingId === user.id}
                            className="w-full text-left px-4 py-2 text-xs text-red-600 hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                          >
                            <Trash2 className="w-3 h-3" />
                            {deletingId === user.id ? 'Deleting...' : 'Delete'}
                          </button>
                        </div>,
                        document.body
                      )}
                    </div>
                  </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-bold mb-4 text-gray-900">Create New User</h3>
            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email *
                </label>
                <input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="user@lawfirm.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Password *
                </label>
                <input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  required
                  minLength={6}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="••••••••"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Full Name
                </label>
                <input
                  type="text"
                  value={newUser.full_name}
                  onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="John Doe"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Role (Permissions) *
                </label>
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">Controls access level (admin can manage users)</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Title (Job Title) *
                </label>
                <select
                  value={newUser.title}
                  onChange={(e) => setNewUser({ ...newUser, title: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="attorney">Attorney</option>
                  <option value="paralegal">Paralegal</option>
                  <option value="finance">Finance</option>
                  <option value="admin">Admin</option>
                  <option value="user">User</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">Job title/position</p>
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false)
                    setNewUser({ email: '', password: '', full_name: '', role: 'user', title: 'attorney' })
                    setError('')
                  }}
                  className="flex-1 px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-900"
                >
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditModal && editingUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-bold mb-4 text-gray-900">Edit User</h3>
            <form onSubmit={handleUpdateUser} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={editingUser.email}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-gray-50"
                  readOnly
                />
                <p className="text-xs text-gray-500 mt-1">Email cannot be changed</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Full Name
                </label>
                <input
                  type="text"
                  value={editUser.full_name}
                  onChange={(e) => setEditUser({ ...editUser, full_name: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="John Doe"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Role (Permissions) *
                </label>
                <select
                  value={editUser.role}
                  onChange={(e) => setEditUser({ ...editUser, role: e.target.value })}
                  required
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">Controls access level (admin can manage users)</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Title (Job Title) *
                </label>
                <select
                  value={editUser.title}
                  onChange={(e) => setEditUser({ ...editUser, title: e.target.value })}
                  required
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="attorney">Attorney</option>
                  <option value="paralegal">Paralegal</option>
                  <option value="finance">Finance</option>
                  <option value="admin">Admin</option>
                  <option value="user">User</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">Job title/position</p>
              </div>
              {error && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded">
                  {error}
                </div>
              )}
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false)
                    setEditingUser(null)
                    setEditUser({ full_name: '', role: 'user', title: 'attorney' })
                    setError('')
                  }}
                  className="flex-1 px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 text-sm bg-black text-white rounded-lg hover:bg-gray-900"
                >
                  Update User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete User Confirmation Modal */}
      {showDeleteModal && userToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-bold mb-4 text-gray-900">Delete User</h3>
            <div className="space-y-4">
              <p className="text-sm text-gray-700">
                Are you sure you want to delete <strong>{userToDelete.email}</strong>? This action cannot be undone.
              </p>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Type <strong>"delete user"</strong> to confirm:
                </label>
                <input
                  type="text"
                  value={deleteConfirmText}
                  onChange={(e) => setDeleteConfirmText(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="delete user"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && deleteConfirmText.toLowerCase() === 'delete user') {
                      confirmDeleteUser()
                    }
                  }}
                />
              </div>
              {error && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded">
                  {error}
                </div>
              )}
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowDeleteModal(false)
                    setUserToDelete(null)
                    setDeleteConfirmText('')
                    setError('')
                  }}
                  disabled={deletingId === userToDelete.id}
                  className="flex-1 px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={confirmDeleteUser}
                  disabled={deleteConfirmText.toLowerCase() !== 'delete user' || deletingId === userToDelete.id}
                  className="flex-1 px-4 py-2 text-sm bg-black text-white rounded-lg hover:bg-gray-900 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-black"
                >
                  {deletingId === userToDelete.id ? 'Deleting...' : 'Delete User'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}



