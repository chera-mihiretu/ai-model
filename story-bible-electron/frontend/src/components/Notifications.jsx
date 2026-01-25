/**
 * Notifications Component
 * =======================
 * Toast notifications system.
 */

import { useEffect } from 'react'
import useStore from '../hooks/useStore'
import { clsx } from 'clsx'

// Icons for notification types
const Icons = {
  success: '✅',
  error: '❌',
  warning: '⚠️',
  info: 'ℹ️',
}

function Notification({ notification, onDismiss }) {
  const { id, type = 'info', message } = notification
  
  // Auto-dismiss after 5 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss(id)
    }, 5000)
    
    return () => clearTimeout(timer)
  }, [id, onDismiss])
  
  return (
    <div
      className={clsx(
        'flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg animate-slide-up',
        'bg-bg-sidebar border border-glass-border',
        'max-w-sm'
      )}
    >
      <span className="text-lg">{Icons[type] || Icons.info}</span>
      <p className="flex-1 text-sm text-text-primary">{message}</p>
      <button
        className="w-6 h-6 flex items-center justify-center rounded hover:bg-bg-hover text-text-muted hover:text-text-primary"
        onClick={() => onDismiss(id)}
      >
        ✕
      </button>
    </div>
  )
}

function Notifications() {
  const { notifications, removeNotification } = useStore()
  
  if (notifications.length === 0) return null
  
  return (
    <div className="fixed bottom-6 right-6 z-50 space-y-2">
      {notifications.map(notification => (
        <Notification
          key={notification.id}
          notification={notification}
          onDismiss={removeNotification}
        />
      ))}
    </div>
  )
}

export default Notifications

