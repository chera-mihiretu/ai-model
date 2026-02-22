/**
 * Story Bible Pro - Main Application Component
 * =============================================
 * Main app layout with dashboard, sidebar, editor, and assistant panels.
 * Shows project dashboard first, then editor when a project is selected.
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import useStore from './hooks/useStore'
import { usePythonBridge } from './hooks/usePythonBridge'
import { LuBrain, LuDownload, LuFolderOpen } from 'react-icons/lu'

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
    isElectronApi,
    getProjectsWithChapters,
    getAiStatus,
    getCharacters,
    getStoryBible,
    getTtsVoices,
    browseAndCopyModel,
    listModels,
  } = usePythonBridge()
  
  const [isLoading, setIsLoading] = useState(true)
  const [showModelSetup, setShowModelSetup] = useState(false)
  const [isSettingUpModel, setIsSettingUpModel] = useState(false)
  
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
        
        // Check if we need to show model setup (only in Electron mode)
        if (isElectronApi && !aiStatus.is_loaded) {
          // Check if there are any models available
          const models = await listModels()
          if (!models || models.length === 0) {
            // No models found, show setup dialog
            setShowModelSetup(true)
          }
        }
        
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
  }, [isApiAvailable, isElectronApi, getAiStatus, listModels])
  
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
  
  // Handle model setup
  const handleBrowseForModel = async () => {
    setIsSettingUpModel(true)
    try {
      const result = await browseAndCopyModel()
      if (result && result.is_loaded) {
        setShowModelSetup(false)
      }
    } catch (error) {
      console.error('Failed to setup model:', error)
    } finally {
      setIsSettingUpModel(false)
    }
  }
  
  const handleSkipModelSetup = () => {
    setShowModelSetup(false)
  }
  
  // Render model setup dialog
  if (showModelSetup && !isLoading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center relative overflow-hidden">
        <AnimatedBackground />
        <div className="relative z-10 max-w-2xl mx-auto p-8">
          <div className="glass-panel rounded-2xl p-8 shadow-2xl">
            <div className="flex items-center gap-3 mb-6">
              <LuBrain className="w-12 h-12 text-gold-rich" />
              <div>
                <h1 className="text-3xl font-bold text-text-primary">Welcome to Exelsias</h1>
                <p className="text-text-muted">AI-Powered Story Bible</p>
              </div>
            </div>
            
            <div className="space-y-4 mb-8">
              <p className="text-text-secondary text-lg">
                No AI model detected. To use AI features, you need to select a GGUF model file.
              </p>
              
              <div className="bg-dark-700/50 rounded-lg p-4 border border-gold-rich/20">
                <h3 className="text-sm font-semibold text-gold-rich mb-2">What you need:</h3>
                <ul className="text-sm text-text-muted space-y-1 list-disc list-inside">
                  <li>A GGUF format language model (e.g., LLaMA, Mistral, etc.)</li>
                  <li>The model will be copied to the application directory</li>
                  <li>Recommended: 4GB+ models for better quality</li>
                </ul>
              </div>
            </div>
            
            <div className="flex gap-4">
              <button
                onClick={handleBrowseForModel}
                disabled={isSettingUpModel}
                className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gold-rich hover:bg-gold-rich/90 text-dark-900 font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSettingUpModel ? (
                  <>
                    <div className="spinner-small" />
                    <span>Setting up model...</span>
                  </>
                ) : (
                  <>
                    <LuFolderOpen className="w-5 h-5" />
                    <span>Browse for Model</span>
                  </>
                )}
              </button>
              
              <button
                onClick={handleSkipModelSetup}
                disabled={isSettingUpModel}
                className="px-6 py-3 bg-dark-700 hover:bg-dark-600 text-text-secondary font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Skip for Now
              </button>
            </div>
            
            <p className="text-xs text-text-muted mt-4 text-center">
              You can always add a model later from the toolbar
            </p>
          </div>
        </div>
        <Notifications />
      </div>
    )
  }
  
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
