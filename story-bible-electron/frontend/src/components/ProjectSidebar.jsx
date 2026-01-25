/**
 * Project Sidebar Component
 * =========================
 * Left sidebar showing only the current project's chapters.
 */

import { useState, useEffect } from 'react'
import useStore from '../hooks/useStore'
import { usePythonBridge } from '../hooks/usePythonBridge'
import { clsx } from 'clsx'

// Icons
const Icons = {
  CHAPTER: '📄',
  PLUS: '+',
  EDIT: '✏️',
  TRASH: '🗑️',
  UP: '▲',
  DOWN: '▼',
  DRAG: '⋮⋮',
  BOOK: '📖',
  BRAINDUMP: '📝',
  GENRE: '🎭',
  STYLE: '🎨',
  SYNOPSIS: '📖',
  CHARACTERS: '👥',
  WORLD: '🌍',
  OUTLINE: '📋',
  SCENE: '🎬',
  EXPAND: '▼',
  COLLAPSE: '▶',
}

// Story Bible tabs configuration
const BIBLE_TABS = [
  { id: 'braindump', label: 'Braindump', icon: Icons.BRAINDUMP },
  { id: 'genre', label: 'Genre', icon: Icons.GENRE },
  { id: 'style', label: 'Style', icon: Icons.STYLE },
  { id: 'synopsis', label: 'Synopsis', icon: Icons.SYNOPSIS },
  { id: 'characters', label: 'Characters', icon: Icons.CHARACTERS },
  { id: 'worldElements', label: 'World Building', icon: Icons.WORLD },
  { id: 'outline', label: 'Outline', icon: Icons.OUTLINE },
  { id: 'scenes', label: 'Scene Editor', icon: Icons.SCENE },
]

function ChapterItem({ chapter, index, isActive, onClick, onDelete, onRename, onMoveUp, onMoveDown, isFirst, isLast }) {
  const [isHovered, setIsHovered] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(chapter.title || `Chapter ${index + 1}`)
  
  const handleRename = () => {
    if (editTitle.trim() && editTitle !== chapter.title) {
      onRename(chapter.id, editTitle.trim())
    }
    setIsEditing(false)
  }
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleRename()
    } else if (e.key === 'Escape') {
      setEditTitle(chapter.title || `Chapter ${index + 1}`)
      setIsEditing(false)
    }
  }
  
  return (
    <div
      className={clsx(
        'group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all duration-200',
        'border border-transparent',
        isActive
          ? 'bg-accent-primary/20 border-accent-primary text-accent-primary'
          : 'hover:bg-bg-hover text-text-secondary hover:text-text-primary'
      )}
      onClick={() => !isEditing && onClick(chapter.id)}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Drag Handle */}
      <span className="text-text-muted/50 text-xs">{Icons.DRAG}</span>
      
      {/* Chapter Icon & Number */}
      <span className="text-lg">{Icons.CHAPTER}</span>
      <span className="text-xs font-mono text-text-muted w-6">{index + 1}.</span>
      
      {/* Title */}
      {isEditing ? (
        <input
          type="text"
          className="flex-1 bg-bg-card px-2 py-1 rounded text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-accent-primary"
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onBlur={handleRename}
          onKeyDown={handleKeyDown}
          onClick={(e) => e.stopPropagation()}
          autoFocus
        />
      ) : (
        <span className="flex-1 truncate text-sm font-medium">
          {chapter.title || `Chapter ${index + 1}`}
        </span>
      )}
      
      {/* Actions (visible on hover) */}
      {isHovered && !isEditing && (
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {!isFirst && (
            <button
              className="w-5 h-5 flex items-center justify-center rounded text-text-muted hover:text-accent-primary hover:bg-accent-primary/20 text-xs"
              onClick={(e) => {
                e.stopPropagation()
                onMoveUp(chapter.id)
              }}
              title="Move Up"
            >
              {Icons.UP}
            </button>
          )}
          {!isLast && (
            <button
              className="w-5 h-5 flex items-center justify-center rounded text-text-muted hover:text-accent-primary hover:bg-accent-primary/20 text-xs"
              onClick={(e) => {
                e.stopPropagation()
                onMoveDown(chapter.id)
              }}
              title="Move Down"
            >
              {Icons.DOWN}
            </button>
          )}
          <button
            className="w-5 h-5 flex items-center justify-center rounded text-text-muted hover:text-accent-primary hover:bg-accent-primary/20 text-xs"
            onClick={(e) => {
              e.stopPropagation()
              setIsEditing(true)
            }}
            title="Rename"
          >
            {Icons.EDIT}
          </button>
          <button
            className="w-5 h-5 flex items-center justify-center rounded text-text-muted hover:text-red-400 hover:bg-red-500/20 text-xs"
            onClick={(e) => {
              e.stopPropagation()
              onDelete(chapter.id)
            }}
            title="Delete"
          >
            {Icons.TRASH}
          </button>
        </div>
      )}
    </div>
  )
}

// Modal for creating new chapter
function NewChapterModal({ isOpen, onClose, onSubmit, isCreating }) {
  const [title, setTitle] = useState('')
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (title.trim()) {
      onSubmit(title.trim())
      setTitle('')
    }
  }
  
  // Reset when modal closes
  useEffect(() => {
    if (!isOpen) setTitle('')
  }, [isOpen])
  
  if (!isOpen) return null
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 w-full max-w-md mx-4 glass-card p-6 animate-slide-up">
        <h2 className="text-xl font-bold text-text-primary mb-4">Create New Chapter</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Chapter Title
            </label>
            <input
              type="text"
              className="input"
              placeholder="Enter chapter title..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              autoFocus
              disabled={isCreating}
            />
          </div>
          <div className="flex items-center justify-end gap-3">
            <button 
              type="button" 
              className="btn btn-ghost" 
              onClick={onClose}
              disabled={isCreating}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={!title.trim() || isCreating}
            >
              {isCreating ? (
                <>
                  <div className="spinner !w-4 !h-4" />
                  <span>Creating...</span>
                </>
              ) : (
                <>
                  <span>+</span>
                  <span>Create Chapter</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function ProjectSidebar() {
  const {
    projects,
    currentProjectId,
    currentChapterId,
    currentBibleTab,
    isBibleExpanded,
    setCurrentChapter,
    setCurrentView,
    setCurrentBibleTab,
    toggleBibleExpanded,
    setProjects,
    addNotification,
  } = useStore()
  
  const {
    getProjectsWithChapters,
    createChapter,
    deleteChapter,
    renameChapter,
    moveChapterUp,
    moveChapterDown,
  } = usePythonBridge()
  
  const [showNewChapterModal, setShowNewChapterModal] = useState(false)
  const [isCreatingChapter, setIsCreatingChapter] = useState(false)
  
  // Get current project
  const currentProject = projects.find(p => p.id === currentProjectId)
  const chapters = currentProject?.chapters || []
  
  // Refresh projects
  const refreshProjects = async () => {
    const updatedProjects = await getProjectsWithChapters()
    setProjects(updatedProjects)
  }
  
  // Handle chapter click
  const handleChapterClick = (chapterId) => {
    setCurrentChapter(chapterId)
    setCurrentView('editor')
  }
  
  // Handle add chapter
  const handleAddChapter = async (title) => {
    if (!currentProjectId || !title) return
    
    setIsCreatingChapter(true)
    try {
      console.log('Creating chapter:', title, 'for project:', currentProjectId)
      const chapterId = await createChapter(currentProjectId, title)
      console.log('Chapter created with ID:', chapterId)
      
      if (chapterId) {
        await refreshProjects()
        setCurrentChapter(chapterId)
        setCurrentView('editor')
        setShowNewChapterModal(false)
        addNotification({ type: 'success', message: `Chapter "${title}" created` })
      } else {
        addNotification({ type: 'error', message: 'Failed to create chapter' })
      }
    } catch (error) {
      console.error('Error creating chapter:', error)
      addNotification({ type: 'error', message: `Error: ${error.message}` })
    } finally {
      setIsCreatingChapter(false)
    }
  }
  
  // Handle delete chapter
  const handleDeleteChapter = async (chapterId) => {
    const chapter = chapters.find(c => c.id === chapterId)
    if (!chapter) return
    
    if (confirm(`Delete "${chapter.title || 'Untitled Chapter'}"? This cannot be undone.`)) {
      const success = await deleteChapter(chapterId)
      if (success) {
        await refreshProjects()
        // If deleted chapter was active, clear selection
        if (currentChapterId === chapterId) {
          setCurrentChapter(null)
        }
        addNotification({ type: 'success', message: 'Chapter deleted' })
      }
    }
  }
  
  // Handle rename chapter
  const handleRenameChapter = async (chapterId, newTitle) => {
    if (!renameChapter) {
      // Fallback if renameChapter not available
      addNotification({ type: 'warning', message: 'Rename not available' })
      return
    }
    
    const success = await renameChapter(chapterId, newTitle)
    if (success) {
      await refreshProjects()
    }
  }
  
  // Handle move chapter up
  const handleMoveUp = async (chapterId) => {
    const success = await moveChapterUp(chapterId)
    if (success) {
      await refreshProjects()
    }
  }
  
  // Handle move chapter down
  const handleMoveDown = async (chapterId) => {
    const success = await moveChapterDown(chapterId)
    if (success) {
      await refreshProjects()
    }
  }
  
  // Handle Bible tab click
  const handleBibleTabClick = (tabId) => {
    setCurrentBibleTab(tabId)
    
    // Route to appropriate view
    switch (tabId) {
      case 'characters':
        setCurrentView('characters')
        break
      case 'worldElements':
        setCurrentView('worldBuilding')
        break
      case 'scenes':
        setCurrentView('scenes')
        break
      default:
        setCurrentView('storyBible')
        break
    }
  }
  
  if (!currentProjectId || !currentProject) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-6 text-center">
        <p className="text-text-muted">No project selected</p>
      </div>
    )
  }
  
  return (
    <div className="h-full flex flex-col p-4 overflow-hidden">
      {/* Project Header */}
      <div className="mb-4">
        <h2 className="text-lg font-bold text-text-primary truncate" title={currentProject.name}>
          {currentProject.name}
        </h2>
        <p className="text-xs text-text-muted mt-1">
          {chapters.length} chapter{chapters.length !== 1 ? 's' : ''}
        </p>
      </div>
      
      {/* Add Chapter Button */}
      <button
        className="w-full mb-4 px-4 py-2 rounded-lg bg-accent-primary/20 text-accent-primary hover:bg-accent-primary hover:text-white transition-colors flex items-center justify-center gap-2 font-medium"
        onClick={() => setShowNewChapterModal(true)}
      >
        <span className="text-lg font-bold">{Icons.PLUS}</span>
        <span>New Chapter</span>
      </button>
      
      {/* Chapters List */}
      <div className="flex-1 overflow-y-auto custom-scrollbar space-y-1">
        {chapters.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-3 opacity-50">{Icons.CHAPTER}</div>
            <p className="text-text-muted text-sm">No chapters yet</p>
            <p className="text-text-muted/60 text-xs mt-1">Click "New Chapter" to get started</p>
          </div>
        ) : (
          chapters.map((chapter, index) => (
            <ChapterItem
              key={chapter.id}
              chapter={chapter}
              index={index}
              isActive={currentChapterId === chapter.id}
              onClick={handleChapterClick}
              onDelete={handleDeleteChapter}
              onRename={handleRenameChapter}
              onMoveUp={handleMoveUp}
              onMoveDown={handleMoveDown}
              isFirst={index === 0}
              isLast={index === chapters.length - 1}
            />
          ))
        )}
      </div>
      
      {/* Divider */}
      <div className="border-t border-glass-border my-4" />
      
      {/* Story Bible Section */}
      <div>
        <button
          className={clsx(
            'w-full px-4 py-3 rounded-lg text-left flex items-center gap-3',
            'text-text-secondary transition-all duration-200',
            isBibleExpanded 
              ? 'bg-accent-primary/20 text-accent-primary border border-accent-primary'
              : 'bg-bg-card/60 hover:bg-accent-primary/10 border border-transparent'
          )}
          onClick={toggleBibleExpanded}
        >
          <span>{Icons.BOOK}</span>
          <span className="flex-1 font-medium">Story Bible</span>
          <span className="text-xs">{isBibleExpanded ? Icons.EXPAND : Icons.COLLAPSE}</span>
        </button>
        
        {isBibleExpanded && (
          <div className="mt-2 space-y-1 animate-fade-in max-h-48 overflow-y-auto custom-scrollbar">
            {BIBLE_TABS.map(tab => (
              <button
                key={tab.id}
                className={clsx(
                  'bible-tab w-full text-left flex items-center gap-2',
                  currentBibleTab === tab.id && 'active'
                )}
                onClick={() => handleBibleTabClick(tab.id)}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        )}
      </div>
      
      {/* New Chapter Modal */}
      <NewChapterModal
        isOpen={showNewChapterModal}
        onClose={() => setShowNewChapterModal(false)}
        onSubmit={handleAddChapter}
        isCreating={isCreatingChapter}
      />
    </div>
  )
}

export default ProjectSidebar
