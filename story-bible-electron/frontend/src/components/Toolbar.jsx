/**
 * Toolbar Component
 * =================
 * Main application toolbar with AI writing tools and status indicators.
 */

import { useState, useRef, useEffect } from 'react'
import useStore from '../hooks/useStore'
import { usePythonBridge } from '../hooks/usePythonBridge'
import { clsx } from 'clsx'

// Icons (matching the Python Icons class)
const Icons = {
  BACK: '←',
  WRITE: '✍️',
  REWRITE: '🔄',
  DESCRIBE: '✨',
  WAND: '🪄',
  SETTINGS: '⚙️',
  HELP: '❓',
  EXPORT: '📤',
  PLAY: '▶️',
  STOP: '⏹️',
  SPEAKER: '🔊',
}

function ToolbarButton({ icon, label, tooltip, hasMenu, onClick, children }) {
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
    <div className="relative" ref={menuRef} style={{ zIndex: isOpen ? 9999 : 'auto' }}>
      <button
        className={clsx(
          'px-4 py-2 rounded-lg flex items-center gap-2',
          'bg-[rgba(12,15,20,0.8)] border border-golden-500/20',
          'text-golden-400/80 text-sm font-medium',
          'hover:bg-golden-500/15 hover:border-golden-500/50 hover:text-golden-300',
          'transition-all duration-200',
          isOpen && 'bg-golden-500/15 border-golden-500/50 text-golden-300'
        )}
        onClick={() => hasMenu ? setIsOpen(!isOpen) : onClick?.()}
        title={tooltip}
      >
        <span>{icon}</span>
        <span>{label}</span>
        {hasMenu && <span className="text-xs">▾</span>}
      </button>
      
      {hasMenu && isOpen && (
        <div className="dropdown-menu min-w-[180px]" style={{ zIndex: 9999 }}>
          {children}
        </div>
      )}
    </div>
  )
}

function MenuItem({ icon, label, onClick, checkbox, checked, onCheck }) {
  if (checkbox) {
    return (
      <label className="dropdown-item flex items-center gap-3 cursor-pointer">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onCheck?.(e.target.checked)}
          className="w-4 h-4 rounded border-border bg-bg-input accent-accent-primary"
        />
        {icon && <span>{icon}</span>}
        <span>{label}</span>
      </label>
    )
  }
  
  return (
    <button
      className="dropdown-item w-full text-left flex items-center gap-2"
      onClick={onClick}
    >
      {icon && <span>{icon}</span>}
      <span>{label}</span>
    </button>
  )
}

function Toolbar() {
  const {
    aiStatus,
    aiStatusMessage,
    isAiGenerating,
    wordCount,
    isEditorDirty,
    isTtsPlaying,
    selectedVoice,
    ttsVoices,
    setSelectedVoice,
    toggleSidebar,
    toggleAssistant,
    editorContent,
    currentProjectId,
    projects,
    setCurrentProject,
    setCurrentView,
  } = useStore()
  
  // Get current project name
  const currentProject = projects.find(p => p.id === currentProjectId)
  
  const {
    startAiStream,
    generatePluginResponse,
    ttsSpeak,
    ttsStop,
  } = usePythonBridge()
  
  // Write mode state
  const [writeMode, setWriteMode] = useState('Continue Writing')
  
  // Describe senses state
  const [activeSenses, setActiveSenses] = useState({
    Sight: false,
    Sound: false,
    Smell: false,
    Taste: false,
    Touch: false,
    Metaphor: false,
  })
  
  // Handle Write action
  const handleWrite = async (mode) => {
    setWriteMode(mode)
    
    // Simple instructions - Python backend handles the proper prompt formatting
    let instruction = ''
    switch (mode) {
      case 'Continue Writing':
        instruction = 'Continue writing the story naturally.'
        break
      case 'Write Scene':
        instruction = 'Write a new dramatic scene that advances the plot.'
        break
      case 'Generate Opening':
        instruction = 'Write a captivating opening paragraph for a story.'
        break
      default:
        instruction = 'Write creative narrative prose.'
    }
    
    await startAiStream(instruction, {
      currentText: editorContent,
    })
  }
  
  // Handle Rewrite action
  const handleRewrite = async (style) => {
    if (!editorContent || editorContent.trim().length < 10) {
      return
    }
    
    // Simple style instruction
    const instruction = `Rewrite the text in a ${style.toLowerCase()} style.`
    await startAiStream(instruction, { currentText: editorContent })
  }
  
  // Handle Describe action
  const handleDescribe = async () => {
    const senses = Object.entries(activeSenses)
      .filter(([, active]) => active)
      .map(([sense]) => sense)
    
    if (senses.length === 0) {
      return
    }
    
    const senseList = senses.join(', ')
    const instruction = `Add vivid sensory descriptions focusing on: ${senseList}.`
    await startAiStream(instruction, { currentText: editorContent })
  }
  
  // Handle TTS
  const { setTtsPlaying } = useStore()
  
  const handleTts = async () => {
    if (isTtsPlaying) {
      await ttsStop()
      setTtsPlaying(false)
    } else {
      const success = await ttsSpeak(editorContent, selectedVoice)
      if (success) {
        setTtsPlaying(true)
      }
    }
  }
  
  // Handle back to dashboard
  const handleBackToDashboard = () => {
    setCurrentProject(null)
    setCurrentView('dashboard')
  }
  
  return (
    <header className="h-toolbar flex items-center px-4 gap-4 bg-[rgba(8,10,14,0.9)] backdrop-blur-xl border-b border-golden-500/10 drag-region">
      {/* Left: Navigation */}
      <div className="flex items-center gap-3 no-drag">
        {/* Back to Dashboard */}
        <button
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-golden-500/60 hover:bg-golden-500/10 hover:text-golden-400 transition-colors"
          onClick={handleBackToDashboard}
          title="Back to Projects"
        >
          <span className="text-lg">{Icons.BACK}</span>
          <span className="text-sm font-medium hidden sm:inline">Projects</span>
        </button>
        
        {/* Separator */}
        <div className="w-px h-6 bg-golden-500/20" />
        
        {/* Current Project Name */}
        {currentProject && (
          <div className="flex items-center gap-2">
            <span className="text-lg">📖</span>
            <span className="text-sm font-medium text-golden-400 max-w-[150px] truncate">
              {currentProject.name}
            </span>
          </div>
        )}
        
        {/* Toggle Sidebar */}
        <button
          className="w-8 h-8 flex items-center justify-center rounded-lg text-golden-500/60 hover:bg-golden-500/10 hover:text-golden-400 transition-colors"
          onClick={toggleSidebar}
          title="Toggle Sidebar"
        >
          ☰
        </button>
      </div>
      
      {/* Center: AI Tools */}
      <div className="flex items-center gap-2 flex-1 justify-center no-drag">
        {/* Write Button */}
        <ToolbarButton
          icon={Icons.WRITE}
          label={`Write: ${writeMode.split(' ')[0]}`}
          tooltip="AI writing tools"
          hasMenu
        >
          <MenuItem label="Continue Writing" onClick={() => handleWrite('Continue Writing')} />
          <MenuItem label="Write Scene" onClick={() => handleWrite('Write Scene')} />
          <MenuItem label="Generate Opening" onClick={() => handleWrite('Generate Opening')} />
        </ToolbarButton>
        
        {/* Rewrite Button */}
        <ToolbarButton
          icon={Icons.REWRITE}
          label="Rewrite"
          tooltip="Rewrite selected text in different styles"
          hasMenu
        >
          <MenuItem label="Show Don't Tell" onClick={() => handleRewrite('Show Don\'t Tell')} />
          <MenuItem label="Dramatic" onClick={() => handleRewrite('Dramatic')} />
          <MenuItem label="Gritty" onClick={() => handleRewrite('Gritty')} />
          <MenuItem label="Elegant" onClick={() => handleRewrite('Elegant')} />
          <MenuItem label="Concise" onClick={() => handleRewrite('Concise')} />
        </ToolbarButton>
        
        {/* Describe Button */}
        <ToolbarButton
          icon={Icons.DESCRIBE}
          label="Describe"
          tooltip="Add sensory descriptions"
          hasMenu
        >
          <MenuItem
            icon="👁️"
            label="Sight"
            checkbox
            checked={activeSenses.Sight}
            onCheck={(checked) => setActiveSenses(s => ({ ...s, Sight: checked }))}
          />
          <MenuItem
            icon="🔊"
            label="Sound"
            checkbox
            checked={activeSenses.Sound}
            onCheck={(checked) => setActiveSenses(s => ({ ...s, Sound: checked }))}
          />
          <MenuItem
            icon="👃"
            label="Smell"
            checkbox
            checked={activeSenses.Smell}
            onCheck={(checked) => setActiveSenses(s => ({ ...s, Smell: checked }))}
          />
          <MenuItem
            icon="👅"
            label="Taste"
            checkbox
            checked={activeSenses.Taste}
            onCheck={(checked) => setActiveSenses(s => ({ ...s, Taste: checked }))}
          />
          <MenuItem
            icon="🖐️"
            label="Touch"
            checkbox
            checked={activeSenses.Touch}
            onCheck={(checked) => setActiveSenses(s => ({ ...s, Touch: checked }))}
          />
          <MenuItem
            icon="🎭"
            label="Metaphor"
            checkbox
            checked={activeSenses.Metaphor}
            onCheck={(checked) => setActiveSenses(s => ({ ...s, Metaphor: checked }))}
          />
          <hr className="my-2 border-border" />
          <MenuItem label="Apply Descriptions" onClick={handleDescribe} />
        </ToolbarButton>
        
        {/* More Tools Button */}
        <ToolbarButton
          icon={Icons.WAND}
          label="More Tools"
          tooltip="Additional AI tools"
          hasMenu
        >
          <MenuItem icon="🎬" label="Visualize" onClick={() => {}} />
          <MenuItem icon="🔀" label="Twist" onClick={() => {}} />
          <MenuItem icon="📜" label="Poem" onClick={() => {}} />
          <hr className="my-2 border-border" />
          <MenuItem icon={Icons.EXPORT} label="Export" onClick={() => {}} />
          <MenuItem icon={Icons.SETTINGS} label="Settings" onClick={() => {}} />
        </ToolbarButton>
      </div>
      
      {/* Right: Status & Controls */}
      <div className="flex items-center gap-4 no-drag">
        {/* TTS Controls */}
        <div className="flex items-center gap-1">
          {/* Voice Selector */}
          {ttsVoices.length > 0 && (
            <select
              className="px-2 py-1.5 rounded-l-lg bg-bg-card/80 text-text-muted text-sm border-0 focus:outline-none focus:ring-1 focus:ring-accent-primary cursor-pointer max-w-[100px]"
              value={selectedVoice}
              onChange={(e) => setSelectedVoice(e.target.value)}
              title="Select Voice"
            >
              {ttsVoices.map(voice => (
                <option key={voice} value={voice}>{voice}</option>
              ))}
            </select>
          )}
          
          {/* Play/Stop Button */}
          <button
            className={clsx(
              'px-3 py-1.5 flex items-center gap-2 text-sm',
              'transition-all duration-200',
              ttsVoices.length > 0 ? 'rounded-r-lg' : 'rounded-lg',
              isTtsPlaying
                ? 'bg-accent-primary text-white'
                : 'bg-bg-card/80 text-text-muted hover:bg-bg-hover hover:text-text-primary'
            )}
            onClick={handleTts}
            title={isTtsPlaying ? 'Stop Reading' : 'Read Aloud'}
          >
            {isTtsPlaying ? Icons.STOP : Icons.PLAY}
            <span>{isTtsPlaying ? 'Stop' : 'Read'}</span>
          </button>
        </div>
        
        {/* Word Count */}
        <div className="px-3 py-1.5 rounded-lg bg-bg-card/60 text-text-muted text-sm">
          {wordCount.toLocaleString()} words
        </div>
        
        {/* Save Status */}
        <div className={clsx(
          'px-3 py-1.5 rounded-lg text-sm',
          isEditorDirty
            ? 'bg-yellow-500/20 text-yellow-400'
            : 'bg-green-500/20 text-green-400'
        )}>
          {isEditorDirty ? 'Unsaved' : '✓ Saved'}
        </div>
        
        {/* AI Status */}
        <div 
          className={clsx(
            'ai-status cursor-help',
            aiStatus === 'ready' && 'ready',
            aiStatus === 'loading' && 'loading',
            aiStatus === 'error' && 'error'
          )}
          title={aiStatusMessage || 'AI Status'}
        >
          <span className={clsx(
            'w-2 h-2 rounded-full',
            aiStatus === 'ready' && 'bg-green-400',
            aiStatus === 'loading' && 'bg-yellow-400 animate-pulse',
            aiStatus === 'error' && 'bg-red-400'
          )} />
          <span>
            {isAiGenerating 
              ? 'Generating...' 
              : aiStatus === 'ready' 
                ? 'AI Ready' 
                : aiStatus === 'loading'
                  ? 'Loading Model...'
                  : 'AI Offline'}
          </span>
        </div>
        
        {/* Toggle Assistant */}
        <button
          className="w-10 h-10 flex items-center justify-center rounded-lg text-text-muted hover:bg-bg-hover hover:text-text-primary transition-colors"
          onClick={toggleAssistant}
          title="Toggle Assistant Panel"
        >
          💬
        </button>
        
        {/* Exit App Button */}
        <button
          className="w-10 h-10 flex items-center justify-center rounded-lg text-text-muted hover:bg-red-500/20 hover:text-red-400 transition-colors"
          onClick={() => window.api?.windowClose?.()}
          title="Exit Application"
        >
          ✕
        </button>
      </div>
    </header>
  )
}

export default Toolbar

