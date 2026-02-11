/**
 * Story Bible Pro - Main Application Component
 * =============================================
 * Main app layout with dashboard, sidebar, editor, and assistant panels.
 * Shows project dashboard first, then editor when a project is selected.
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import useStore from './hooks/useStore'
import { usePythonBridge } from './hooks/usePythonBridge'

// Components
import Dashboard from './components/Dashboard'
import Toolbar from './components/Toolbar'
import ProjectSidebar from './components/ProjectSidebar'
import Editor from './components/Editor'
import StoryBible from './components/StoryBible'
import CharacterManager from './components/CharacterManager'
import AssistantPanel from './components/AssistantPanel'
import Notifications from './components/Notifications'
import WorldBuilding from './components/WorldBuilding'
import SceneEditor from './components/SceneEditor'
import AnimatedBackground from './components/AnimatedBackground'

/**
 * ResizeHandle Component
 * Draggable handle for resizing sidebars
 */
function ResizeHandle({ onResize, position = 'left', minWidth, maxWidth }) {
  const handleRef = useRef(null)
  const isDragging = useRef(false)
  const startX = useRef(0)
  const startWidth = useRef(0)
  
  const handleMouseDown = useCallback((e) => {
    e.preventDefault()
    isDragging.current = true
    startX.current = e.clientX
    
    // Get the current width from the parent
    const sidebar = position === 'left' 
      ? handleRef.current?.previousElementSibling 
      : handleRef.current?.nextElementSibling
    startWidth.current = sidebar?.offsetWidth || 280
    
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [position])
  
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isDragging.current) return
      
      const delta = position === 'left' 
        ? e.clientX - startX.current 
        : startX.current - e.clientX
      
      const newWidth = startWidth.current + delta
      onResize(newWidth)
    }
    
    const handleMouseUp = () => {
      if (isDragging.current) {
        isDragging.current = false
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
      }
    }
    
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [onResize, position])
  
  return (
    <div
      ref={handleRef}
      className={`
        resize-handle group flex-shrink-0 w-1 cursor-col-resize
        bg-transparent hover:bg-gold-rich/30 active:bg-gold-rich/50
        transition-colors duration-150 relative z-10
        ${position === 'left' ? 'hover:border-r hover:border-gold-rich/40' : 'hover:border-l hover:border-gold-rich/40'}
      `}
      onMouseDown={handleMouseDown}
      title="Drag to resize"
    >
      {/* Visual indicator on hover */}
      <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-1 opacity-0 group-hover:opacity-100 transition-opacity bg-gold-rich/50 rounded-full" />
    </div>
  )
}

function App() {
  const {
    currentView,
    currentProjectId,
    sidebarCollapsed,
    assistantCollapsed,
    sidebarWidth,
    assistantWidth,
    setSidebarWidth,
    setAssistantWidth,
    setProjects,
    setCharacters,
    setStoryBibleData,
    setTtsVoices,
    setCurrentView,
  } = useStore()
  
  const {
    isApiAvailable,
    getProjectsWithChapters,
    getAiStatus,
    getCharacters,
    getStoryBible,
    getTtsVoices,
  } = usePythonBridge()
  
  const [isLoading, setIsLoading] = useState(true)
  
  // Initialize app
  useEffect(() => {
    async function init() {
      try {
        // Load projects (works in both Electron and browser mode)
        const projects = await getProjectsWithChapters()
        setProjects(projects || [])
        
        // Check AI status
        const aiStatus = await getAiStatus()
        console.log('AI Status:', aiStatus)
        
        // Load TTS voices
        const voices = await getTtsVoices()
        setTtsVoices(voices || [])
        
      } catch (error) {
        console.error('Initialization error:', error)
      } finally {
        setIsLoading(false)
      }
    }
    
    init()
  }, [isApiAvailable])
  
  // Load project data when project changes
  useEffect(() => {
    async function loadProjectData() {
      if (!currentProjectId || !isApiAvailable) return
      
      try {
        // Load characters
        const characters = await getCharacters(currentProjectId)
        setCharacters(characters)
        
        // Load story bible
        const bibleData = await getStoryBible(currentProjectId)
        setStoryBibleData(bibleData)
        
      } catch (error) {
        console.error('Failed to load project data:', error)
      }
    }
    
    loadProjectData()
  }, [currentProjectId, isApiAvailable])
  
  // When no project is selected and not in dashboard, go to dashboard
  useEffect(() => {
    if (!currentProjectId && currentView !== 'dashboard') {
      setCurrentView('dashboard')
    }
  }, [currentProjectId, currentView])
  
  // Render loading screen
  if (isLoading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center relative overflow-hidden">
        <AnimatedBackground />
        <div className="text-center relative z-10">
          <div className="spinner mx-auto mb-4" />
          <p className="text-gray-600">Loading Exelsias...</p>
        </div>
      </div>
    )
  }
  
  // Render main content based on current view
  const renderMainContent = () => {
    switch (currentView) {
      case 'characters':
        return <CharacterManager />
      case 'storyBible':
        return <StoryBible />
      case 'worldBuilding':
        return <WorldBuilding />
      case 'scenes':
        return <SceneEditor />
      case 'editor':
      default:
        return <Editor />
    }
  }
  
  // Show Dashboard when no project is selected
  if (!currentProjectId || currentView === 'dashboard') {
    return (
      <div className="h-screen w-screen overflow-hidden relative">
        <AnimatedBackground />
        <div className="relative z-10 h-full">
          <Dashboard />
        </div>
        <Notifications />
      </div>
    )
  }
  
  // Show Editor layout when project is selected
  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden relative">
      <AnimatedBackground />
      
      {/* Content Layer */}
      <div className="relative z-10 h-full flex flex-col">
        {/* Toolbar - higher z-index so dropdowns appear above content */}
        <div className="relative z-50">
          <Toolbar />
        </div>
        
        {/* Main Content Area */}
        <div className="flex-1 flex overflow-hidden relative z-0">
          {/* Project Sidebar (Left) */}
          <div 
            className={`
              glass-sidebar flex-shrink-0 overflow-hidden
              ${sidebarCollapsed ? 'w-0' : ''}
            `}
            style={{ 
              width: sidebarCollapsed ? 0 : sidebarWidth,
              transition: sidebarCollapsed ? 'width 0.3s ease' : 'none'
            }}
          >
            <ProjectSidebar />
          </div>
          
          {/* Left Resize Handle */}
          {!sidebarCollapsed && (
            <ResizeHandle 
              position="left" 
              onResize={setSidebarWidth}
            />
          )}
          
          {/* Center Panel */}
          <div className="flex-1 overflow-hidden min-w-0">
            {renderMainContent()}
          </div>
          
          {/* Right Resize Handle */}
          {!assistantCollapsed && (
            <ResizeHandle 
              position="right" 
              onResize={setAssistantWidth}
            />
          )}
          
          {/* Assistant Panel (Right) */}
          <div 
            className={`
              glass-sidebar flex-shrink-0 overflow-hidden
              ${assistantCollapsed ? 'w-0' : ''}
            `}
            style={{ 
              width: assistantCollapsed ? 0 : assistantWidth,
              transition: assistantCollapsed ? 'width 0.3s ease' : 'none'
            }}
          >
            <AssistantPanel />
          </div>
        </div>
      </div>
      
      {/* Notifications */}
      <Notifications />
    </div>
  )
}

export default App
