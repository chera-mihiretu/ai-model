/**
 * Dashboard Component
 * ===================
 * Landing page showing projects organized in folders and series.
 * Beautiful warm gradient background with clean, airy design.
 */

import { useState, useEffect, useRef, useMemo } from 'react'
import useStore from '../hooks/useStore'
import { usePythonBridge } from '../hooks/usePythonBridge'
import { clsx } from 'clsx'

import ImportNovel from './ImportNovel'
import SeriesManager from './SeriesManager'

// Icons
const Icons = {
  PROJECT: '📄',
  FOLDER: '📁',
  SERIES: '📚',
  PLUS: '+',
  BOOK: '📖',
  CHAPTER: '📄',
  CLOCK: '🕐',
  TRASH: '🗑️',
  EDIT: '✏️',
  IMPORT: '📥',
  BACK: '←',
  CLOSE: '✕',
  MENU: '⋯',
}

// Project Card - with folded corner effect for standalone projects
function ProjectCard({ project, onSelect, onDelete, onRename, onDuplicate }) {
  const [showMenu, setShowMenu] = useState(false)
  const menuRef = useRef(null)
  
  const wordCount = project.word_count || 0
  
  // Format timestamp
  const formatTime = (timestamp) => {
    if (!timestamp) return 'Just now'
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now - date
    
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`
    return date.toLocaleDateString()
  }
  
  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  return (
    <div
      className={clsx(
        'relative group cursor-pointer',
        'bg-white rounded-xl',
        'shadow-paper hover:shadow-paper-hover',
        'transition-all duration-300 hover:-translate-y-1',
        'min-h-[220px] flex flex-col'
      )}
      style={{ zIndex: showMenu ? 50 : 1 }}
      onClick={() => onSelect(project)}
    >
      {/* Three-dot Menu Button */}
      <div className="absolute top-3 right-3" ref={menuRef} style={{ zIndex: 200 }}>
        <button
          className={clsx(
            'w-8 h-8 rounded-lg flex items-center justify-center',
            'text-gray-300 hover:text-gray-500 hover:bg-gray-100',
            'opacity-0 group-hover:opacity-100 transition-all'
          )}
          onClick={(e) => {
            e.stopPropagation()
            setShowMenu(!showMenu)
          }}
        >
          ⋯
        </button>
        
        {showMenu && (
          <div className="absolute right-0 top-10 bg-white rounded-xl shadow-lg border border-gray-100 min-w-[140px] py-2" style={{ zIndex: 99999 }}>
            <button
              className="dropdown-item flex items-center gap-2 w-full"
              onClick={(e) => {
                e.stopPropagation()
                onDuplicate?.(project)
                setShowMenu(false)
              }}
            >
              📋 Duplicate
            </button>
            <button
              className="dropdown-item flex items-center gap-2 w-full"
              onClick={(e) => {
                e.stopPropagation()
                onRename(project)
                setShowMenu(false)
              }}
            >
              ✏️ Rename
            </button>
            <button
              className="dropdown-item flex items-center gap-2 w-full text-red-500 hover:!bg-red-50"
              onClick={(e) => {
                e.stopPropagation()
                onDelete(project)
                setShowMenu(false)
              }}
            >
              🗑️ Delete
            </button>
          </div>
        )}
      </div>
      
      {/* Project Content */}
      <div className="flex-1 flex items-center justify-center p-6">
        <h3 className="text-xl font-serif font-medium text-gray-800 text-center leading-tight">
          {project.name}
        </h3>
      </div>
      
      {/* Stats at bottom */}
      <div className="text-center pb-4 px-4 border-t border-gray-50 pt-3">
        <p className="text-sm text-gray-400">
          {wordCount.toLocaleString()} words
        </p>
        <p className="text-xs text-gray-300 mt-0.5">
          {formatTime(project.updated_at)}
        </p>
      </div>
    </div>
  )
}

// Folder Card - file folder shape with papers inside
function FolderCard({ folder, onClick, onDelete, onRename, onDuplicateProject, onDeleteProject }) {
  const [showMenu, setShowMenu] = useState(false)
  const [showProjectMenu, setShowProjectMenu] = useState(null) // track which project menu is open
  const menuRef = useRef(null)
  const projectMenuRef = useRef(null)
  
  const projects = folder.projects || []
  const projectCount = projects.length
  const papersToShow = Math.min(projectCount, 3) // Max 3 papers shown
  
  const formatTime = (timestamp) => {
    if (!timestamp) return 'Just now'
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now - date
    
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`
    return date.toLocaleDateString()
  }
  
  // Close menus when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false)
      }
      if (projectMenuRef.current && !projectMenuRef.current.contains(event.target)) {
        setShowProjectMenu(null)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  // Paper angles for stacking effect
  const paperAngles = [-2, 1, -0.5]
  
  return (
    <div
      className="relative group cursor-pointer transition-all duration-300 hover:-translate-y-1"
      onClick={() => onClick(folder)}
      style={{ zIndex: showMenu || showProjectMenu !== null ? 100 : 1 }}
    >
      {/* Folder shape with tab */}
      <div className="relative">
        {/* Folder tab */}
        <div 
          className="absolute -top-2 left-3 w-16 h-4 rounded-t-lg"
          style={{ backgroundColor: '#f5f0eb' }}
        />
        
        {/* Folder body */}
        <div
          className="relative rounded-xl overflow-hidden"
          style={{ 
            backgroundColor: '#f5f0eb',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06), 0 4px 20px rgba(0, 0, 0, 0.04)'
          }}
        >
          {/* Menu Button */}
          <div className="absolute top-3 right-3" ref={menuRef} style={{ zIndex: 200 }}>
            <button
              className={clsx(
                'w-8 h-8 rounded-lg flex items-center justify-center',
                'text-gray-400 hover:text-gray-600 hover:bg-white/50',
                'opacity-0 group-hover:opacity-100 transition-all'
              )}
              onClick={(e) => {
                e.stopPropagation()
                setShowMenu(!showMenu)
              }}
            >
              {Icons.MENU}
            </button>
            
            {showMenu && (
              <div 
                className="absolute right-0 top-10 bg-white rounded-xl shadow-lg border border-gray-100 min-w-[140px] py-2"
                style={{ zIndex: 99999 }}
              >
                <button
                  className="dropdown-item flex items-center gap-2 w-full"
                  onClick={(e) => {
                    e.stopPropagation()
                    onRename(folder)
                    setShowMenu(false)
                  }}
                >
                  {Icons.EDIT} Rename
                </button>
                <button
                  className="dropdown-item flex items-center gap-2 w-full text-red-500 hover:!bg-red-50"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDelete(folder)
                    setShowMenu(false)
                  }}
                >
                  {Icons.TRASH} Delete
                </button>
              </div>
            )}
          </div>
          
          {/* Folder Content */}
          <div className="p-4 pt-5 pb-3">
            <h3 className="text-xl font-serif font-medium text-gray-800 leading-tight">
              {folder.name}
            </h3>
          </div>
          
          {/* Papers inside folder */}
          {papersToShow > 0 && (
            <div className="relative px-3 pb-3" style={{ minHeight: '80px' }} ref={projectMenuRef}>
              {projects.slice(0, 3).map((project, index) => (
                <div
                  key={project.id || index}
                  className="absolute bg-white rounded-lg shadow-sm border border-gray-100 p-3 group/paper"
                  style={{
                    width: 'calc(100% - 24px)',
                    height: '70px',
                    transform: `rotate(${paperAngles[index]}deg)`,
                    top: `${index * 4}px`,
                    left: '12px',
                    zIndex: 10 - index,
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <p className="text-sm font-medium text-gray-700 truncate pr-6">
                    {project.name || 'Untitled'}
                  </p>
                  
                  {/* Three dot menu on each paper */}
                  <button
                    className={clsx(
                      'absolute top-2 right-2 w-6 h-6 rounded flex items-center justify-center',
                      'text-gray-300 hover:text-gray-500 hover:bg-gray-100',
                      'opacity-0 group-hover/paper:opacity-100 transition-all text-xs'
                    )}
                    onClick={(e) => {
                      e.stopPropagation()
                      setShowProjectMenu(showProjectMenu === project.id ? null : project.id)
                    }}
                  >
                    ⋯
                  </button>
                  
                  {/* Project dropdown menu */}
                  {showProjectMenu === project.id && (
                    <div 
                      className="absolute right-0 top-8 bg-white rounded-xl shadow-lg border border-gray-100 min-w-[120px] py-2"
                      style={{ zIndex: 99999 }}
                    >
                      <button
                        className="dropdown-item flex items-center gap-2 w-full text-sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          onDuplicateProject?.(project, folder)
                          setShowProjectMenu(null)
                        }}
                      >
                        📋 Duplicate
                      </button>
                      <button
                        className="dropdown-item flex items-center gap-2 w-full text-sm text-red-500 hover:!bg-red-50"
                        onClick={(e) => {
                          e.stopPropagation()
                          onDeleteProject?.(project)
                          setShowProjectMenu(null)
                        }}
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          
          {/* Empty state inside folder */}
          {papersToShow === 0 && (
            <div className="px-4 pb-4 pt-2">
              <div className="h-16 rounded-lg border-2 border-dashed border-gray-300/50 flex items-center justify-center">
                <span className="text-xs text-gray-400">No projects</span>
              </div>
            </div>
          )}
          
          {/* Stats at bottom */}
          <div className="px-4 pb-4 pt-2">
            <p className="text-sm text-gray-500">
              {projectCount} project{projectCount !== 1 ? 's' : ''}
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              {formatTime(folder.updated_at)}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

// Series Card - file folder shape with SERIES badge and papers inside
function SeriesCard({ series, onClick, onDelete, onRename, onDuplicateProject, onDeleteProject }) {
  const [showMenu, setShowMenu] = useState(false)
  const [showProjectMenu, setShowProjectMenu] = useState(null)
  const menuRef = useRef(null)
  const projectMenuRef = useRef(null)
  
  const projects = series.projects || []
  const projectCount = projects.length
  const papersToShow = Math.min(projectCount, 3)
  
  const formatTime = (timestamp) => {
    if (!timestamp) return 'Just now'
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now - date
    
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`
    return date.toLocaleDateString()
  }
  
  // Close menus when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false)
      }
      if (projectMenuRef.current && !projectMenuRef.current.contains(event.target)) {
        setShowProjectMenu(null)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  // Paper angles for stacking effect
  const paperAngles = [-2, 1, -0.5]
  
  return (
    <div
      className="relative group cursor-pointer transition-all duration-300 hover:-translate-y-1"
      onClick={() => onClick(series)}
      style={{ zIndex: showMenu || showProjectMenu !== null ? 100 : 1 }}
    >
      {/* Folder shape with tab */}
      <div className="relative">
        {/* Folder tab */}
        <div 
          className="absolute -top-2 left-3 w-16 h-4 rounded-t-lg"
          style={{ backgroundColor: '#f5f0eb' }}
        />
        
        {/* Folder body */}
        <div
          className="relative rounded-xl overflow-hidden"
          style={{ 
            backgroundColor: '#f5f0eb',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06), 0 4px 20px rgba(0, 0, 0, 0.04)'
          }}
        >
          {/* Menu Button */}
          <div className="absolute top-3 right-3" ref={menuRef} style={{ zIndex: 200 }}>
            <button
              className={clsx(
                'w-8 h-8 rounded-lg flex items-center justify-center',
                'text-gray-400 hover:text-gray-600 hover:bg-white/50',
                'opacity-0 group-hover:opacity-100 transition-all'
              )}
              onClick={(e) => {
                e.stopPropagation()
                setShowMenu(!showMenu)
              }}
            >
              {Icons.MENU}
            </button>
            
            {showMenu && (
              <div 
                className="absolute right-0 top-10 bg-white rounded-xl shadow-lg border border-gray-100 min-w-[140px] py-2"
                style={{ zIndex: 99999 }}
              >
                <button
                  className="dropdown-item flex items-center gap-2 w-full"
                  onClick={(e) => {
                    e.stopPropagation()
                    onRename(series)
                    setShowMenu(false)
                  }}
                >
                  {Icons.EDIT} Rename
                </button>
                <button
                  className="dropdown-item flex items-center gap-2 w-full text-red-500 hover:!bg-red-50"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDelete(series)
                    setShowMenu(false)
                  }}
                >
                  {Icons.TRASH} Delete
                </button>
              </div>
            )}
          </div>
          
          {/* Series Badge */}
          <div className="px-4 pt-4">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-white/60 text-gray-600">
              {Icons.SERIES} SERIES
            </span>
          </div>
          
          {/* Folder Content */}
          <div className="p-4 pt-2 pb-3">
            <h3 className="text-xl font-serif font-medium text-gray-800 leading-tight">
              {series.name}
            </h3>
          </div>
          
          {/* Papers inside folder */}
          {papersToShow > 0 && (
            <div className="relative px-3 pb-3" style={{ minHeight: '80px' }} ref={projectMenuRef}>
              {projects.slice(0, 3).map((project, index) => (
                <div
                  key={project.id || index}
                  className="absolute bg-white rounded-lg shadow-sm border border-gray-100 p-3 group/paper"
                  style={{
                    width: 'calc(100% - 24px)',
                    height: '70px',
                    transform: `rotate(${paperAngles[index]}deg)`,
                    top: `${index * 4}px`,
                    left: '12px',
                    zIndex: 10 - index,
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <p className="text-sm font-medium text-gray-700 truncate pr-6">
                    {project.name || 'Untitled'}
                  </p>
                  
                  {/* Three dot menu on each paper */}
                  <button
                    className={clsx(
                      'absolute top-2 right-2 w-6 h-6 rounded flex items-center justify-center',
                      'text-gray-300 hover:text-gray-500 hover:bg-gray-100',
                      'opacity-0 group-hover/paper:opacity-100 transition-all text-xs'
                    )}
                    onClick={(e) => {
                      e.stopPropagation()
                      setShowProjectMenu(showProjectMenu === project.id ? null : project.id)
                    }}
                  >
                    ⋯
                  </button>
                  
                  {/* Project dropdown menu */}
                  {showProjectMenu === project.id && (
                    <div 
                      className="absolute right-0 top-8 bg-white rounded-xl shadow-lg border border-gray-100 min-w-[120px] py-2"
                      style={{ zIndex: 99999 }}
                    >
                      <button
                        className="dropdown-item flex items-center gap-2 w-full text-sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          onDuplicateProject?.(project, series)
                          setShowProjectMenu(null)
                        }}
                      >
                        📋 Duplicate
                      </button>
                      <button
                        className="dropdown-item flex items-center gap-2 w-full text-sm text-red-500 hover:!bg-red-50"
                        onClick={(e) => {
                          e.stopPropagation()
                          onDeleteProject?.(project)
                          setShowProjectMenu(null)
                        }}
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          
          {/* Empty state inside folder */}
          {papersToShow === 0 && (
            <div className="px-4 pb-4 pt-2">
              <div className="h-16 rounded-lg border-2 border-dashed border-gray-300/50 flex items-center justify-center">
                <span className="text-xs text-gray-400">No projects</span>
              </div>
            </div>
          )}
          
          {/* Stats at bottom */}
          <div className="px-4 pb-4 pt-2">
            <p className="text-sm text-gray-500">
              {projectCount} project{projectCount !== 1 ? 's' : ''}
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              {formatTime(series.updated_at)}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

// Feature Card with stacked effect
function FeatureCard() {
  return (
    <div className="relative">
      {/* Stacked cards behind */}
      <div className="absolute top-2 left-2 right-2 bottom-0 bg-gray-50 rounded-xl transform rotate-2" />
      <div className="absolute top-1 left-1 right-1 bottom-0 bg-gray-100 rounded-xl transform rotate-1" />
      
      {/* Main card */}
      <div className="relative bg-white rounded-xl shadow-paper p-6 min-h-[200px]">
        {/* Close button */}
        <button className="absolute top-3 right-3 text-gray-300 hover:text-gray-500 text-lg">
          ×
        </button>
        
        {/* Content */}
        <div className="text-center pt-4">
          <span className="text-xs font-semibold text-primary-500 uppercase tracking-wider">
            NEW
          </span>
          <h3 className="text-lg font-serif font-semibold text-gray-800 mt-2 leading-tight">
            AI-Powered
            <br />
            Writing Assistant
          </h3>
          <p className="text-sm text-gray-500 mt-3">
            Let Exelsias help you write
            <br />
            your next chapter.
          </p>
          <button className="mt-4 px-6 py-2 border border-gray-200 rounded-full text-sm text-gray-600 hover:bg-gray-50 transition-colors">
            Learn More
          </button>
        </div>
      </div>
    </div>
  )
}

// New Button Dropdown
function NewButtonDropdown({ onCreateProject, onCreateFolder, onCreateSeries }) {
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef(null)
  
  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  return (
    <div className="relative" ref={menuRef} style={{ zIndex: 9999 }}>
      <button
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors font-medium"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="text-lg">+</span> New
      </button>
      
      {isOpen && (
        <div 
          className="absolute left-0 top-full mt-2 bg-white rounded-xl shadow-lg border border-gray-100 min-w-[160px] py-2"
          style={{ zIndex: 99999 }}
        >
          <button
            className="dropdown-item flex items-center gap-3 w-full"
            onClick={() => {
              onCreateProject()
              setIsOpen(false)
            }}
          >
            <span className="text-lg">📄</span>
            <span>Project</span>
          </button>
          <button
            className="dropdown-item flex items-center gap-3 w-full"
            onClick={() => {
              onCreateFolder()
              setIsOpen(false)
            }}
          >
            <span className="text-lg">📁</span>
            <span>Folder</span>
          </button>
          <button
            className="dropdown-item flex items-center gap-3 w-full"
            onClick={() => {
              onCreateSeries()
              setIsOpen(false)
            }}
          >
            <span className="text-lg">📚</span>
            <span>Series</span>
          </button>
        </div>
      )}
    </div>
  )
}

// Create Modal (for Project, Folder, or Series)
function CreateModal({ isOpen, onClose, onCreate, type = 'project' }) {
  const [name, setName] = useState('')
  const [genre, setGenre] = useState('')
  
  const genres = [
    'Fantasy', 'Sci-Fi', 'Romance', 'Mystery', 'Thriller', 
    'Horror', 'Literary Fiction', 'Historical', 'Young Adult', 'Other'
  ]
  
  const titles = {
    project: 'Create New Project',
    folder: 'Create New Folder',
    series: 'Create New Series',
  }
  
  const placeholders = {
    project: 'My Amazing Story',
    folder: 'My Folder',
    series: 'My Series',
  }
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (name.trim()) {
      onCreate(name.trim(), genre, type)
      setName('')
      setGenre('')
      onClose()
    }
  }
  
  useEffect(() => {
    if (!isOpen) {
      setName('')
      setGenre('')
    }
  }, [isOpen])
  
  if (!isOpen) return null
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 modal-backdrop"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative z-10 w-full max-w-md mx-4 modal-content p-6 animate-slide-up">
        <h2 className="text-xl font-semibold text-gray-800 mb-6">
          {titles[type]}
        </h2>
        
        <form onSubmit={handleSubmit}>
          {/* Name */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-600 mb-2">
              Name *
            </label>
            <input
              type="text"
              className="input"
              placeholder={placeholders[type]}
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
          </div>
          
          {/* Genre - only for projects */}
          {type === 'project' && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-600 mb-2">
                Genre
              </label>
              <select
                className="input"
                value={genre}
                onChange={(e) => setGenre(e.target.value)}
              >
                <option value="">Select a genre...</option>
                {genres.map(g => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
            </div>
          )}
          
          {/* Actions */}
          <div className="flex items-center justify-end gap-3 mt-6">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!name.trim()}
            >
              Create {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Folder View - when inside a folder
function FolderView({ folder, onBack, onSelectProject, onCreateProject, onDeleteProject, onRenameProject, onDuplicateProject }) {
  const formatTime = (timestamp) => {
    if (!timestamp) return 'Just now'
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now - date
    
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`
    return date.toLocaleDateString()
  }
  
  const projects = folder.projects || []
  
  return (
    <div className="h-full flex flex-col">
      {/* Folder Header */}
      <div className="px-8 py-6">
        <div className="max-w-5xl mx-auto">
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-gray-500 mb-2">
            <button 
              className="hover:text-gray-700 transition-colors"
              onClick={onBack}
            >
              Home
            </button>
            <span className="text-gray-300">›</span>
            <span className="text-gray-700">{folder.name}</span>
          </div>
          
          {/* Folder Title */}
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-serif font-medium text-gray-800">
                {folder.name}
              </h1>
              <p className="text-gray-500 mt-1">
                {projects.length} project{projects.length !== 1 ? 's' : ''} • Last edited {formatTime(folder.updated_at)}
              </p>
            </div>
            
            <div className="flex items-center gap-2">
              <button className="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100">
                {Icons.MENU}
              </button>
              <button 
                className="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                onClick={onBack}
              >
                {Icons.CLOSE}
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Projects Grid */}
      <div className="flex-1 overflow-y-auto px-8 pb-8">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {projects.map(project => (
              <ProjectCard
                key={project.id}
                project={project}
                onSelect={onSelectProject}
                onDelete={onDeleteProject}
                onRename={onRenameProject}
                onDuplicate={onDuplicateProject}
              />
            ))}
            
            {/* Add Project Button */}
            <button
              className={clsx(
                'min-h-[180px] rounded-xl',
                'border-2 border-dashed border-gray-200',
                'flex flex-col items-center justify-center',
                'text-gray-400 hover:text-gray-600 hover:border-gray-300',
                'transition-all duration-200'
              )}
              onClick={onCreateProject}
            >
              <span className="text-3xl mb-2">+</span>
              <span className="text-sm font-medium">New Project</span>
            </button>
          </div>
          
          {/* Empty State */}
          {projects.length === 0 && (
            <div className="text-center py-12">
              <div className="text-5xl mb-4 opacity-50">📁</div>
              <p className="text-gray-500">This folder is empty</p>
              <p className="text-gray-400 text-sm mt-1">Create a project to get started</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StorageModeIndicator({ mode }) {
  const isLocal = mode === 'local'
  
  return (
    <div
      className={clsx(
        'flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium',
        isLocal 
          ? 'bg-amber-50 text-amber-600 border border-amber-200'
          : 'bg-green-50 text-green-600 border border-green-200'
      )}
      title={isLocal 
        ? 'Running in offline mode. Data is saved locally in your browser.' 
        : 'Connected to Python backend. Data is saved to database.'}
    >
      <span className={clsx(
        'w-2 h-2 rounded-full',
        isLocal ? 'bg-amber-400' : 'bg-green-400'
      )} />
      <span>{isLocal ? 'Offline Mode' : 'Connected'}</span>
    </div>
  )
}

function Dashboard() {
  const {
    projects,
    setProjects,
    setCurrentProject,
    setCurrentView,
    addNotification,
    storageMode,
  } = useStore()
  
  const {
    getProjectsWithChapters,
    createProject,
    deleteProject,
    renameProject,
    storageMode: bridgeStorageMode,
  } = usePythonBridge()
  
  const [isLoading, setIsLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [createType, setCreateType] = useState('project')
  const [showImportModal, setShowImportModal] = useState(false)
  
  // Folder/Series state
  const [folders, setFolders] = useState([])
  const [series, setSeries] = useState([])
  const [currentFolder, setCurrentFolder] = useState(null)
  const [currentSeries, setCurrentSeries] = useState(null)
  
  // Load projects on mount
  useEffect(() => {
    async function loadProjects() {
      setIsLoading(true)
      try {
        const projectList = await getProjectsWithChapters()
        const loadedProjects = projectList || []
        setProjects(loadedProjects)
        
        // Load folders and series from localStorage
        const savedFolders = localStorage.getItem('exelsias_folders')
        const savedSeries = localStorage.getItem('exelsias_series')
        
        // Sync folders: match stored project IDs with actual projects from backend
        if (savedFolders) {
          const parsedFolders = JSON.parse(savedFolders)
          const syncedFolders = parsedFolders.map(folder => ({
            ...folder,
            // Match project IDs with actual project data, filter out deleted projects
            projects: (folder.projects || [])
              .map(storedProject => {
                const actualProject = loadedProjects.find(p => p.id === storedProject.id)
                return actualProject || null
              })
              .filter(Boolean)
          }))
          setFolders(syncedFolders)
          // Save synced version back to localStorage
          localStorage.setItem('exelsias_folders', JSON.stringify(syncedFolders))
        }
        
        // Sync series: match stored project IDs with actual projects from backend
        if (savedSeries) {
          const parsedSeries = JSON.parse(savedSeries)
          const syncedSeries = parsedSeries.map(s => ({
            ...s,
            // Match project IDs with actual project data, filter out deleted projects
            projects: (s.projects || [])
              .map(storedProject => {
                const actualProject = loadedProjects.find(p => p.id === storedProject.id)
                return actualProject || null
              })
              .filter(Boolean)
          }))
          setSeries(syncedSeries)
          // Save synced version back to localStorage
          localStorage.setItem('exelsias_series', JSON.stringify(syncedSeries))
        }
      } catch (error) {
        console.error('Failed to load projects:', error)
        addNotification({ type: 'error', message: 'Failed to load projects' })
      } finally {
        setIsLoading(false)
      }
    }
    
    loadProjects()
  }, [])
  
  // Get standalone projects (not in any folder or series) - memoized to prevent flicker
  const standaloneProjects = useMemo(() => {
    const folderProjectIds = folders.flatMap(f => f.projects?.map(p => p.id) || [])
    const seriesProjectIds = series.flatMap(s => s.projects?.map(p => p.id) || [])
    const usedIds = new Set([...folderProjectIds, ...seriesProjectIds])
    
    return projects.filter(p => !usedIds.has(p.id))
  }, [projects, folders, series])
  
  // Handle select project
  const handleSelectProject = (project) => {
    setCurrentProject(project.id)
    setCurrentView('editor')
  }
  
  // Handle create
  const handleCreate = async (name, genre, type) => {
    if (type === 'project') {
      try {
        const projectId = await createProject(name, genre)
        if (projectId) {
          const updatedProjects = await getProjectsWithChapters()
          setProjects(updatedProjects || [])
          
          // If we're in a folder, add project to folder
          if (currentFolder) {
            const newProject = updatedProjects.find(p => p.id === projectId)
            if (newProject) {
              setFolders(prev => {
                const updated = prev.map(f => 
                  f.id === currentFolder.id 
                    ? { ...f, projects: [...(f.projects || []), newProject], updated_at: new Date().toISOString() }
                    : f
                )
                localStorage.setItem('exelsias_folders', JSON.stringify(updated))
                return updated
              })
              setCurrentFolder(prev => ({
                ...prev,
                projects: [...(prev.projects || []), newProject],
                updated_at: new Date().toISOString()
              }))
            }
          } else if (currentSeries) {
            // If we're in a series, add project to series
            const newProject = updatedProjects.find(p => p.id === projectId)
            if (newProject) {
              setSeries(prev => {
                const updated = prev.map(s => 
                  s.id === currentSeries.id 
                    ? { ...s, projects: [...(s.projects || []), newProject], updated_at: new Date().toISOString() }
                    : s
                )
                localStorage.setItem('exelsias_series', JSON.stringify(updated))
                return updated
              })
              setCurrentSeries(prev => ({
                ...prev,
                projects: [...(prev.projects || []), newProject],
                updated_at: new Date().toISOString()
              }))
            }
          } else {
            // Enter the new project
            setCurrentProject(projectId)
            setCurrentView('editor')
          }
          
          addNotification({ type: 'success', message: `Project "${name}" created!` })
        }
      } catch (error) {
        console.error('Failed to create project:', error)
        addNotification({ type: 'error', message: 'Failed to create project' })
      }
    } else if (type === 'folder') {
      const newFolder = {
        id: Date.now().toString(),
        name,
        projects: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      setFolders(prev => {
        const updated = [...prev, newFolder]
        localStorage.setItem('exelsias_folders', JSON.stringify(updated))
        return updated
      })
      addNotification({ type: 'success', message: `Folder "${name}" created!` })
    } else if (type === 'series') {
      const newSeries = {
        id: Date.now().toString(),
        name,
        projects: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      setSeries(prev => {
        const updated = [...prev, newSeries]
        localStorage.setItem('exelsias_series', JSON.stringify(updated))
        return updated
      })
      addNotification({ type: 'success', message: `Series "${name}" created!` })
    }
  }
  
  // Handle delete project
  const handleDeleteProject = async (project) => {
    if (!confirm(`Are you sure you want to delete "${project.name}"? This cannot be undone.`)) {
      return
    }
    
    try {
      await deleteProject(project.id)
      
      // Immediately remove from local state (Zustand setProjects takes direct value, not callback)
      setProjects(projects.filter(p => p.id !== project.id))
      
      // Remove from folder if in one
      const updatedFolders = folders.map(f => ({
        ...f,
        projects: f.projects?.filter(p => p.id !== project.id) || []
      }))
      setFolders(updatedFolders)
      localStorage.setItem('exelsias_folders', JSON.stringify(updatedFolders))
      
      // Remove from series if in one
      const updatedSeries = series.map(s => ({
        ...s,
        projects: s.projects?.filter(p => p.id !== project.id) || []
      }))
      setSeries(updatedSeries)
      localStorage.setItem('exelsias_series', JSON.stringify(updatedSeries))
      
      // Update current folder/series view
      if (currentFolder) {
        setCurrentFolder({
          ...currentFolder,
          projects: currentFolder.projects?.filter(p => p.id !== project.id) || []
        })
      }
      if (currentSeries) {
        setCurrentSeries({
          ...currentSeries,
          projects: currentSeries.projects?.filter(p => p.id !== project.id) || []
        })
      }
      
      addNotification({ type: 'success', message: `Project "${project.name}" deleted` })
    } catch (error) {
      console.error('Failed to delete project:', error)
      addNotification({ type: 'error', message: 'Failed to delete project' })
    }
  }
  
  // Handle rename project
  const handleRenameProject = async (project) => {
    const newName = prompt('Enter new project name:', project.name)
    if (newName && newName.trim() && newName !== project.name) {
      try {
        await renameProject(project.id, newName.trim())
        const updatedProjects = await getProjectsWithChapters()
        setProjects(updatedProjects || [])
        addNotification({ type: 'success', message: 'Project renamed' })
      } catch (error) {
        console.error('Failed to rename project:', error)
        addNotification({ type: 'error', message: 'Failed to rename project' })
      }
    }
  }
  
  // Handle duplicate project
  const handleDuplicateProject = async (project, container) => {
    try {
      const duplicateName = `${project.name} (Copy)`
      const projectId = await createProject(duplicateName, project.genre || '')
      
      if (projectId) {
        const updatedProjects = await getProjectsWithChapters()
        setProjects(updatedProjects || [])
        
        // If duplicating from a folder, add to same folder
        if (container && container.id) {
          const newProject = updatedProjects.find(p => p.id === projectId)
          if (newProject) {
            // Check if it's a folder or series
            const isFolder = folders.some(f => f.id === container.id)
            if (isFolder) {
              setFolders(prev => {
                const updated = prev.map(f => 
                  f.id === container.id 
                    ? { ...f, projects: [...(f.projects || []), newProject], updated_at: new Date().toISOString() }
                    : f
                )
                localStorage.setItem('exelsias_folders', JSON.stringify(updated))
                return updated
              })
            } else {
              setSeries(prev => {
                const updated = prev.map(s => 
                  s.id === container.id 
                    ? { ...s, projects: [...(s.projects || []), newProject], updated_at: new Date().toISOString() }
                    : s
                )
                localStorage.setItem('exelsias_series', JSON.stringify(updated))
                return updated
              })
            }
          }
        }
        
        addNotification({ type: 'success', message: `Project duplicated as "${duplicateName}"` })
      }
    } catch (error) {
      console.error('Failed to duplicate project:', error)
      addNotification({ type: 'error', message: 'Failed to duplicate project' })
    }
  }
  
  // Handle delete folder
  const handleDeleteFolder = (folder) => {
    if (!confirm(`Delete folder "${folder.name}"? Projects inside will become standalone.`)) {
      return
    }
    const updated = folders.filter(f => f.id !== folder.id)
    setFolders(updated)
    localStorage.setItem('exelsias_folders', JSON.stringify(updated))
    addNotification({ type: 'success', message: 'Folder deleted' })
  }
  
  // Handle rename folder
  const handleRenameFolder = (folder) => {
    const newName = prompt('Enter new folder name:', folder.name)
    if (newName && newName.trim() && newName !== folder.name) {
      setFolders(prev => {
        const updated = prev.map(f => 
          f.id === folder.id ? { ...f, name: newName.trim(), updated_at: Date.now() } : f
        )
        localStorage.setItem('exelsias_folders', JSON.stringify(updated))
        return updated
      })
      addNotification({ type: 'success', message: 'Folder renamed' })
    }
  }
  
  // Handle delete series
  const handleDeleteSeries = (s) => {
    if (!confirm(`Delete series "${s.name}"? Projects inside will become standalone.`)) {
      return
    }
    const updated = series.filter(ser => ser.id !== s.id)
    setSeries(updated)
    localStorage.setItem('exelsias_series', JSON.stringify(updated))
    addNotification({ type: 'success', message: 'Series deleted' })
  }
  
  // Handle rename series
  const handleRenameSeries = (s) => {
    const newName = prompt('Enter new series name:', s.name)
    if (newName && newName.trim() && newName !== s.name) {
      setSeries(prev => {
        const updated = prev.map(ser => 
          ser.id === s.id ? { ...ser, name: newName.trim(), updated_at: Date.now() } : ser
        )
        localStorage.setItem('exelsias_series', JSON.stringify(updated))
        return updated
      })
      addNotification({ type: 'success', message: 'Series renamed' })
    }
  }
  
  // Open folder
  const handleOpenFolder = (folder) => {
    // Sync folder projects with current project data
    const syncedProjects = folder.projects?.map(fp => 
      projects.find(p => p.id === fp.id) || fp
    ).filter(Boolean) || []
    
    setCurrentFolder({ ...folder, projects: syncedProjects })
  }
  
  // Open series
  const handleOpenSeries = (s) => {
    // Sync series projects with current project data
    const syncedProjects = s.projects?.map(sp => 
      projects.find(p => p.id === sp.id) || sp
    ).filter(Boolean) || []
    
    setCurrentSeries({ ...s, projects: syncedProjects })
  }
  
  // If viewing a folder
  if (currentFolder) {
    return (
      <div className="h-full flex flex-col">
        {/* Header */}
        <header className="px-8 py-4 glass relative" style={{ zIndex: 100000 }}>
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <NewButtonDropdown
              onCreateProject={() => {
                setCreateType('project')
                setShowCreateModal(true)
              }}
              onCreateFolder={() => {
                setCreateType('folder')
                setShowCreateModal(true)
              }}
              onCreateSeries={() => {
                setCreateType('series')
                setShowCreateModal(true)
              }}
            />
            
            <div className="flex items-center gap-2">
              <span className="text-2xl font-serif tracking-tight text-gray-800">
                exel<span className="relative top-[1px]">s</span>ias
              </span>
            </div>
            
            <StorageModeIndicator mode={bridgeStorageMode || storageMode} />
          </div>
        </header>
        
        <FolderView
          folder={currentFolder}
          onBack={() => setCurrentFolder(null)}
          onSelectProject={handleSelectProject}
          onCreateProject={() => {
            setCreateType('project')
            setShowCreateModal(true)
          }}
          onDeleteProject={handleDeleteProject}
          onRenameProject={handleRenameProject}
          onDuplicateProject={(p) => handleDuplicateProject(p, currentFolder)}
        />
        
        <CreateModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreate}
          type={createType}
        />
      </div>
    )
  }
  
  // If viewing a series
  if (currentSeries) {
    return (
      <div className="h-full flex flex-col">
        {/* Header */}
        <header className="px-8 py-4 glass relative" style={{ zIndex: 100000 }}>
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <NewButtonDropdown
              onCreateProject={() => {
                setCreateType('project')
                setShowCreateModal(true)
              }}
              onCreateFolder={() => {
                setCreateType('folder')
                setShowCreateModal(true)
              }}
              onCreateSeries={() => {
                setCreateType('series')
                setShowCreateModal(true)
              }}
            />
            
            <div className="flex items-center gap-2">
              <span className="text-2xl font-serif tracking-tight text-gray-800">
                exel<span className="relative top-[1px]">s</span>ias
              </span>
            </div>
            
            <StorageModeIndicator mode={bridgeStorageMode || storageMode} />
          </div>
        </header>
        
        <FolderView
          folder={currentSeries}
          onBack={() => setCurrentSeries(null)}
          onSelectProject={handleSelectProject}
          onCreateProject={() => {
            setCreateType('project')
            setShowCreateModal(true)
          }}
          onDeleteProject={handleDeleteProject}
          onRenameProject={handleRenameProject}
          onDuplicateProject={(p) => handleDuplicateProject(p, currentSeries)}
        />
        
        <CreateModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreate}
          type={createType}
        />
      </div>
    )
  }
  
  // Main Dashboard View
  return (
    <div className="h-full flex flex-col">
      {/* Header - Minimal like Sudowrite */}
      <header className="px-8 py-4 glass relative" style={{ zIndex: 100000 }}>
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          {/* Left side - New & Import */}
          <div className="flex items-center gap-6">
            <NewButtonDropdown
              onCreateProject={() => {
                setCreateType('project')
                setShowCreateModal(true)
              }}
              onCreateFolder={() => {
                setCreateType('folder')
                setShowCreateModal(true)
              }}
              onCreateSeries={() => {
                setCreateType('series')
                setShowCreateModal(true)
              }}
            />
            
            <button
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors font-medium"
              onClick={() => setShowImportModal(true)}
            >
              <span className="text-sm">↓</span> Import Novel
            </button>
          </div>
          
          {/* Center - Logo */}
          <div className="flex items-center gap-2">
            <span className="text-2xl font-serif tracking-tight text-gray-800">
              exel<span className="relative top-[1px]">s</span>ias
            </span>
          </div>
          
          {/* Right side - Status */}
          <div className="flex items-center gap-4">
            <StorageModeIndicator mode={bridgeStorageMode || storageMode} />
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-5xl mx-auto">
          {/* Loading State */}
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="spinner mx-auto mb-4" />
                <p className="text-gray-500">Loading projects...</p>
              </div>
            </div>
          ) : (
            /* Project Grid */
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {/* Standalone Projects (with folded corner) */}
              {standaloneProjects.map(project => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  onSelect={handleSelectProject}
                  onDelete={handleDeleteProject}
                  onRename={handleRenameProject}
                  onDuplicate={(p) => handleDuplicateProject(p, null)}
                />
              ))}
              
              {/* Folders */}
              {folders.map(folder => (
                <FolderCard
                  key={folder.id}
                  folder={folder}
                  onClick={handleOpenFolder}
                  onDelete={handleDeleteFolder}
                  onRename={handleRenameFolder}
                  onDuplicateProject={handleDuplicateProject}
                  onDeleteProject={handleDeleteProject}
                />
              ))}
              
              {/* Series */}
              {series.map(s => (
                <SeriesCard
                  key={s.id}
                  series={s}
                  onClick={handleOpenSeries}
                  onDelete={handleDeleteSeries}
                  onRename={handleRenameSeries}
                  onDuplicateProject={handleDuplicateProject}
                  onDeleteProject={handleDeleteProject}
                />
              ))}
              
              {/* Feature Card */}
              {(standaloneProjects.length > 0 || folders.length > 0 || series.length > 0) && (
                <FeatureCard />
              )}
            </div>
          )}
          
          {/* Empty State */}
          {!isLoading && standaloneProjects.length === 0 && folders.length === 0 && series.length === 0 && (
            <div className="text-center py-16">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-white shadow-paper mb-6">
                <span className="text-4xl">📚</span>
              </div>
              <h3 className="text-xl font-serif font-semibold text-gray-800 mb-2">
                No projects yet
              </h3>
              <p className="text-gray-500 mb-6 max-w-md mx-auto">
                Create your first project to start writing your story with AI assistance.
              </p>
              <div className="flex items-center justify-center gap-4">
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    setCreateType('project')
                    setShowCreateModal(true)
                  }}
                >
                  + Create Project
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowImportModal(true)}
                >
                  ↓ Import Novel
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
      
      {/* Create Modal */}
      <CreateModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreate}
        type={createType}
      />
      
      {/* Import Novel Modal */}
      <ImportNovel
        isOpen={showImportModal}
        onClose={() => {
          setShowImportModal(false)
          // Refresh projects after import
          getProjectsWithChapters().then(projectList => {
            setProjects(projectList || [])
          })
        }}
      />
    </div>
  )
}

export default Dashboard
