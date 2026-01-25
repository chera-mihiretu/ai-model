/**
 * Story Bible Pro - Main Application Component
 * =============================================
 * Main app layout with dashboard, sidebar, editor, and assistant panels.
 * Shows project dashboard first, then editor when a project is selected.
 */

import { useEffect, useState } from 'react'
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

function App() {
  const {
    currentView,
    currentProjectId,
    sidebarCollapsed,
    assistantCollapsed,
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
      <div className="h-screen w-screen flex items-center justify-center bg-[#0A0A0C] relative overflow-hidden">
        <AnimatedBackground />
        <div className="text-center relative z-10">
          <div className="spinner mx-auto mb-4" style={{ borderTopColor: '#705C38' }} />
          <p className="text-golden-400">Loading Exelsias...</p>
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
        {/* Toolbar */}
        <Toolbar />
        
        {/* Main Content Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Project Sidebar */}
          <div 
            className={`
              glass-sidebar transition-all duration-300 flex-shrink-0
              ${sidebarCollapsed ? 'w-0 overflow-hidden' : 'w-[280px]'}
            `}
          >
            <ProjectSidebar />
          </div>
          
          {/* Center Panel */}
          <div className="flex-1 overflow-hidden">
            {renderMainContent()}
          </div>
          
          {/* Assistant Panel */}
          <div 
            className={`
              glass-sidebar transition-all duration-300 flex-shrink-0
              ${assistantCollapsed ? 'w-0 overflow-hidden' : 'w-[360px]'}
            `}
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
