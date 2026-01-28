/**
 * Dashboard Component
 * ===================
 * Landing page showing all projects in a beautiful grid layout.
 * Users select a project to enter the editor.
 */

import { useState, useEffect } from 'react'
import useStore from '../hooks/useStore'
import { usePythonBridge } from '../hooks/usePythonBridge'
import { clsx } from 'clsx'

import ImportNovel from './ImportNovel'
import SeriesManager from './SeriesManager'

// Icons
const Icons = {
  PROJECT: '📂',
  PLUS: '+',
  BOOK: '📖',
  CHAPTER: '📄',
  CHARACTER: '👥',
  CLOCK: '🕐',
  GENRE: '🎭',
  TRASH: '🗑️',
  EDIT: '✏️',
  IMPORT: '📥',
  SERIES: '📚',
}

function ProjectCard({ project, onSelect, onDelete, onRename }) {
  const [showMenu, setShowMenu] = useState(false)
  
  const chapterCount = project.chapters?.length || 0
  
  return (
    <div
      className={clsx(
        'relative group cursor-pointer',
        'bg-gradient-to-br from-[rgba(12,15,20,0.9)] to-[rgba(8,10,14,0.95)]',
        'border border-golden-500/20 rounded-2xl',
        'p-6 transition-all duration-300',
        'hover:border-golden-500/60 hover:shadow-lg hover:shadow-golden-500/20',
        'hover:-translate-y-1'
      )}
      onClick={() => onSelect(project)}
    >
      {/* Menu Button */}
      <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          className="w-8 h-8 rounded-lg bg-bg-hover/80 flex items-center justify-center text-text-muted hover:text-text-primary hover:bg-bg-hover"
          onClick={(e) => {
            e.stopPropagation()
            setShowMenu(!showMenu)
          }}
        >
          ⋯
        </button>
        
        {showMenu && (
          <div className="absolute right-0 top-10 z-10 dropdown-menu min-w-[140px]">
            <button
              className="dropdown-item flex items-center gap-2 w-full"
              onClick={(e) => {
                e.stopPropagation()
                onRename(project)
                setShowMenu(false)
              }}
            >
              {Icons.EDIT} Rename
            </button>
            <button
              className="dropdown-item flex items-center gap-2 w-full text-red-400 hover:!bg-red-500/20"
              onClick={(e) => {
                e.stopPropagation()
                onDelete(project)
                setShowMenu(false)
              }}
            >
              {Icons.TRASH} Delete
            </button>
          </div>
        )}
      </div>
      
      {/* Project Icon */}
      <div className="w-16 h-16 rounded-2xl bg-accent-primary/20 flex items-center justify-center text-3xl mb-4">
        {Icons.BOOK}
      </div>
      
      {/* Project Name */}
      <h3 className="text-xl font-semibold text-text-primary mb-2 truncate">
        {project.name}
      </h3>
      
      {/* Genre Badge */}
      {project.genre && (
        <div className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-accent-secondary/20 text-accent-secondary text-xs mb-3">
          {Icons.GENRE} {project.genre}
        </div>
      )}
      
      {/* Stats */}
      <div className="flex items-center gap-4 text-sm text-text-muted mt-4">
        <span className="flex items-center gap-1">
          {Icons.CHAPTER} {chapterCount} chapter{chapterCount !== 1 ? 's' : ''}
        </span>
      </div>
    </div>
  )
}

function CreateProjectCard({ onClick }) {
  return (
    <div
      className={clsx(
        'cursor-pointer',
        'border-2 border-dashed border-border rounded-2xl',
        'p-6 transition-all duration-300',
        'hover:border-accent-primary hover:bg-accent-primary/5',
        'flex flex-col items-center justify-center min-h-[200px]'
      )}
      onClick={onClick}
    >
      <div className="w-16 h-16 rounded-full bg-accent-primary/20 flex items-center justify-center text-3xl mb-4 text-accent-primary">
        {Icons.PLUS}
      </div>
      <p className="text-text-primary font-medium">Create New Project</p>
      <p className="text-text-muted text-sm mt-1">Start your next story</p>
    </div>
  )
}

function CreateProjectModal({ isOpen, onClose, onCreate }) {
  const [name, setName] = useState('')
  const [genre, setGenre] = useState('')
  
  const genres = [
    'Fantasy', 'Sci-Fi', 'Romance', 'Mystery', 'Thriller', 
    'Horror', 'Literary Fiction', 'Historical', 'Young Adult', 'Other'
  ]
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (name.trim()) {
      onCreate(name.trim(), genre)
      setName('')
      setGenre('')
      onClose()
    }
  }
  
  if (!isOpen) return null
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative z-10 w-full max-w-md mx-4 glass-card p-6 animate-slide-up">
        <h2 className="text-xl font-semibold text-text-primary mb-6">
          Create New Project
        </h2>
        
        <form onSubmit={handleSubmit}>
          {/* Project Name */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Project Name *
            </label>
            <input
              type="text"
              className="input"
              placeholder="My Amazing Story"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
          </div>
          
          {/* Genre */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-text-secondary mb-2">
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
          
          {/* Actions */}
          <div className="flex items-center justify-end gap-3">
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
              Create Project
            </button>
          </div>
        </form>
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
          ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
          : 'bg-green-500/20 text-green-400 border border-green-500/30'
      )}
      title={isLocal 
        ? 'Running in offline mode. Data is saved locally in your browser.' 
        : 'Connected to Python backend. Data is saved to database.'}
    >
      <span className={clsx(
        'w-2 h-2 rounded-full',
        isLocal ? 'bg-yellow-400' : 'bg-green-400'
      )} />
      <span>{isLocal ? 'Offline Mode' : 'Backend Connected'}</span>
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
  const [showImportModal, setShowImportModal] = useState(false)
  const [showSeriesView, setShowSeriesView] = useState(false)
  
  // Load projects on mount
  useEffect(() => {
    async function loadProjects() {
      setIsLoading(true)
      try {
        const projectList = await getProjectsWithChapters()
        setProjects(projectList || [])
      } catch (error) {
        console.error('Failed to load projects:', error)
        addNotification({ type: 'error', message: 'Failed to load projects' })
      } finally {
        setIsLoading(false)
      }
    }
    
    loadProjects()
  }, [])
  
  // Handle select project
  const handleSelectProject = (project) => {
    setCurrentProject(project.id)
    setCurrentView('editor')
  }
  
  // Handle create project
  const handleCreateProject = async (name, genre) => {
    try {
      const projectId = await createProject(name, genre)
      if (projectId) {
        // Refresh projects list
        const updatedProjects = await getProjectsWithChapters()
        setProjects(updatedProjects || [])
        
        // Enter the new project
        setCurrentProject(projectId)
        setCurrentView('editor')
        
        addNotification({ type: 'success', message: `Project "${name}" created!` })
      }
    } catch (error) {
      console.error('Failed to create project:', error)
      addNotification({ type: 'error', message: 'Failed to create project' })
    }
  }
  
  // Handle delete project
  const handleDeleteProject = async (project) => {
    if (!confirm(`Are you sure you want to delete "${project.name}"? This cannot be undone.`)) {
      return
    }
    
    try {
      await deleteProject(project.id)
      const updatedProjects = await getProjectsWithChapters()
      setProjects(updatedProjects || [])
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
  
  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <header className="px-8 py-6 border-b border-glass-border glass">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-accent-primary flex items-center justify-center text-2xl text-white">
              📖
            </div>
            <div>
              <h1 className="text-2xl font-bold text-golden-400">Exelsias</h1>
              <p className="text-golden-500/70 text-sm">Your AI-powered writing companion</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Storage Mode Indicator */}
            <StorageModeIndicator mode={bridgeStorageMode || storageMode} />
            
            <button
              className="btn btn-secondary"
              onClick={() => setShowSeriesView(true)}
              title="Manage Series"
            >
              {Icons.SERIES} Series
            </button>
            
            <button
              className="btn btn-secondary"
              onClick={() => setShowImportModal(true)}
              title="Import Novel"
            >
              {Icons.IMPORT} Import
            </button>
            
            <button
              className="btn btn-primary"
              onClick={() => setShowCreateModal(true)}
            >
              {Icons.PLUS} New Project
            </button>
            
            {/* Exit App Button */}
            <button
              className="w-10 h-10 flex items-center justify-center rounded-lg bg-[rgba(12,15,20,0.8)] border border-golden-500/20 text-text-muted hover:bg-red-500/20 hover:border-red-500/50 hover:text-red-400 transition-all duration-200"
              onClick={() => window.api?.windowClose?.()}
              title="Exit Application"
            >
              ✕
            </button>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-6xl mx-auto">
          {/* Section Title */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-text-primary">Your Projects</h2>
            <p className="text-text-muted mt-1">
              {projects.length} project{projects.length !== 1 ? 's' : ''}
            </p>
          </div>
          
          {/* Loading State */}
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="spinner mx-auto mb-4" />
                <p className="text-text-muted">Loading projects...</p>
              </div>
            </div>
          ) : (
            /* Project Grid */
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {projects.map(project => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  onSelect={handleSelectProject}
                  onDelete={handleDeleteProject}
                  onRename={handleRenameProject}
                />
              ))}
              
              {/* Create New Project Card */}
              <CreateProjectCard onClick={() => setShowCreateModal(true)} />
            </div>
          )}
          
          {/* Empty State */}
          {!isLoading && projects.length === 0 && (
            <div className="text-center py-16">
              <div className="text-6xl mb-6">📚</div>
              <h3 className="text-xl font-semibold text-text-primary mb-2">
                No projects yet
              </h3>
              <p className="text-text-muted mb-6 max-w-md mx-auto">
                Create your first project to start writing your story with AI assistance, 
                or import an existing manuscript.
              </p>
              <div className="flex items-center justify-center gap-4">
                <button
                  className="btn btn-primary btn-lg"
                  onClick={() => setShowCreateModal(true)}
                >
                  {Icons.PLUS} Create Project
                </button>
                <button
                  className="btn btn-secondary btn-lg"
                  onClick={() => setShowImportModal(true)}
                >
                  {Icons.IMPORT} Import Novel
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
      
      {/* Create Project Modal */}
      <CreateProjectModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreateProject}
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
      
      {/* Series Manager Modal */}
      {showSeriesView && (
        <div className="fixed inset-0 z-50 bg-bg-main">
          <div className="absolute top-4 right-4">
            <button
              className="btn btn-ghost"
              onClick={() => setShowSeriesView(false)}
            >
              ✕ Close
            </button>
          </div>
          <SeriesManager />
        </div>
      )}
    </div>
  )
}

export default Dashboard

