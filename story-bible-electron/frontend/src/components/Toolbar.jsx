/**
 * Toolbar Component
 * =================
 * Main application toolbar with AI writing tools and status indicators.
 * Dark & Gold luxury theme styling.
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

function ToolbarButton({ icon, label, tooltip, hasMenu, onClick, children, closeOnClick = true }) {
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
  
  // Close menu handler to pass to children
  const closeMenu = () => setIsOpen(false)
  
  return (
    <div className="relative" ref={menuRef} style={{ zIndex: isOpen ? 9999 : 'auto' }}>
      <button
        className={clsx(
          'px-4 py-2 rounded-lg flex items-center gap-2',
          'bg-dark-700 border border-gold-rich/20',
          'text-text-secondary text-sm font-medium',
          'hover:bg-gold-rich/10 hover:border-gold-rich/40 hover:text-gold-rich',
          'transition-all duration-200',
          isOpen && 'bg-gold-rich/10 border-gold-rich/40 text-gold-rich'
        )}
        onClick={() => hasMenu ? setIsOpen(!isOpen) : onClick?.()}
        title={tooltip}
      >
        <span>{icon}</span>
        <span>{label}</span>
        {hasMenu && <span className="text-xs">▾</span>}
      </button>
      
      {hasMenu && isOpen && (
        <div className="dropdown-menu min-w-[180px]" style={{ zIndex: 9999 }} onClick={closeOnClick ? closeMenu : undefined}>
          {children}
        </div>
      )}
    </div>
  )
}

// Split button for Describe - main button triggers action, dropdown arrow selects options
function DescribeSplitButton({ icon, label, tooltip, onDescribe, children, activeSenses }) {
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
  
  // Count active senses for badge
  const activeCount = Object.values(activeSenses).filter(Boolean).length
  
  return (
    <div className="relative" ref={menuRef} style={{ zIndex: isOpen ? 9999 : 'auto' }}>
      <div className="flex">
        {/* Main Describe Button */}
        <button
          className={clsx(
            'px-4 py-2 rounded-l-lg flex items-center gap-2',
            'bg-dark-700 border border-gold-rich/20 border-r-0',
            'text-text-secondary text-sm font-medium',
            'hover:bg-gold-rich/10 hover:border-gold-rich/40 hover:text-gold-rich',
            'transition-all duration-200'
          )}
          onClick={onDescribe}
          title={tooltip}
        >
          <span>{icon}</span>
          <span>{label}</span>
          {activeCount > 0 && (
            <span className="ml-1 px-1.5 py-0.5 text-xs bg-gold-rich text-dark-950 rounded-full font-semibold">
              {activeCount}
            </span>
          )}
        </button>
        
        {/* Dropdown Arrow */}
        <button
          className={clsx(
            'px-2 py-2 rounded-r-lg flex items-center',
            'bg-dark-700 border border-gold-rich/20',
            'text-text-secondary text-sm',
            'hover:bg-gold-rich/10 hover:border-gold-rich/40 hover:text-gold-rich',
            'transition-all duration-200',
            isOpen && 'bg-gold-rich/10 border-gold-rich/40 text-gold-rich'
          )}
          onClick={() => setIsOpen(!isOpen)}
          title="Select senses to describe"
        >
          <span className="text-xs">▾</span>
        </button>
      </div>
      
      {isOpen && (
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
          className="w-4 h-4 rounded border-gold-rich/30 accent-gold-rich bg-dark-700"
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
    currentChapterId,
    projects,
    setCurrentProject,
    setCurrentView,
    editorCursorContextCallback,
    currentEditorSelection,
    editorInstance,
    setPendingAiRequest,
    addNotification,
  } = useStore()
  
  // Get current project name
  const currentProject = projects.find(p => p.id === currentProjectId)
  
  const {
    startAiStream,
    generatePluginResponse,
    ttsSpeak,
    ttsStop,
    getContextWindow,
    getCharacters,
    getStoryBible,
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
  
  // Handle Write action - Sudowrite-style context-aware writing
  const handleWrite = async (mode) => {
    setWriteMode(mode)
    
    // Check if we have an editor and chapter selected
    if (!currentChapterId) {
      addNotification({ type: 'warning', message: 'Please select a chapter first' })
      return
    }
    
    // Get cursor context (up to 1000 words preceding the cursor)
    let cursorContext = { precedingText: '', cursorPosition: 0, fullText: '', textAfterCursor: '' }
    if (editorCursorContextCallback) {
      cursorContext = editorCursorContextCallback()
    }
    
    const { precedingText, textAfterCursor, cursorPosition } = cursorContext
    
    // If no preceding text, show a message
    if (!precedingText.trim() && mode === 'Continue Writing') {
      addNotification({ type: 'info', message: 'Write some text first, then place your cursor where you want AI to continue.' })
      return
    }
    
    // Get chapter continuity context (summaries from previous chapters)
    let chapterContinuity = ''
    try {
      const contextWindow = await getContextWindow(currentProjectId, currentChapterId, 2000)
      if (contextWindow?.prev_summary) {
        chapterContinuity = contextWindow.prev_summary
      }
    } catch (e) {
      console.log('Could not get chapter continuity:', e)
    }
    
    // Get character and story bible context for consistency
    let characterContext = ''
    let storyContext = ''
    try {
      const characters = await getCharacters(currentProjectId)
      if (characters && characters.length > 0) {
        const visibleChars = characters.filter(c => c.is_visible !== 0)
        if (visibleChars.length > 0) {
          characterContext = visibleChars.slice(0, 5).map(c => 
            `${c.name}${c.role ? ` (${c.role})` : ''}: ${c.personality_traits || c.backstory || ''}`
          ).join('\n')
        }
      }
      
      const bible = await getStoryBible(currentProjectId)
      if (bible?.synopsis) {
        storyContext = bible.synopsis.substring(0, 500)
      }
    } catch (e) {
      console.log('Could not get character/story context:', e)
    }
    
    // Build the instruction based on mode
    let instruction = ''
    switch (mode) {
      case 'Continue Writing':
        instruction = `Continue writing the story naturally from where it left off. Match the tone, style, and pacing of the existing text. Write 2-3 paragraphs that flow seamlessly from the last sentence.`
        break
      case 'Write Scene':
        instruction = `Write a new dramatic scene that advances the plot. Include vivid descriptions, character interactions, and forward momentum. Write 3-4 paragraphs.`
        break
      case 'Generate Opening':
        instruction = `Write a captivating opening paragraph that hooks the reader immediately. Use vivid imagery and establish the scene.`
        break
      default:
        instruction = 'Write creative narrative prose that continues the story.'
    }
    
    // Build full context for AI
    let fullPrompt = instruction + '\n\n'
    
    if (chapterContinuity) {
      fullPrompt += `=== PREVIOUS CHAPTER SUMMARY ===\n${chapterContinuity}\n\n`
    }
    
    if (storyContext) {
      fullPrompt += `=== STORY CONTEXT ===\n${storyContext}\n\n`
    }
    
    if (characterContext) {
      fullPrompt += `=== KEY CHARACTERS ===\n${characterContext}\n\n`
    }
    
    if (precedingText) {
      fullPrompt += `=== TEXT TO CONTINUE FROM (last ~1000 words) ===\n${precedingText}\n\n`
      fullPrompt += `Continue from here, matching the style and voice exactly. DO NOT repeat the existing text - just continue naturally.`
    }
    
    console.log('Write button - cursor position:', cursorPosition)
    console.log('Write button - preceding text words:', precedingText.split(/\s+/).length)
    console.log('Write button - has chapter continuity:', !!chapterContinuity)
    
    // Send to AssistantPanel for generation and insertion
    setPendingAiRequest({
      type: 'write',
      instruction: fullPrompt,
      mode: mode,
      cursorPosition: cursorPosition,
      insertAtCursor: true,
      context: {
        precedingText,
        textAfterCursor,
        chapterContinuity,
        characterContext,
        storyContext,
      }
    })
    
    addNotification({ type: 'info', message: `AI is writing... (using ${precedingText.split(/\s+/).length} words of context)` })
  }
  
  // Handle Rewrite action - rewrites selected text in a specific style
  const handleRewrite = async (style) => {
    // Use the stored selection state (captured before click)
    const selection = currentEditorSelection || { selectedText: '', hasSelection: false }
    
    console.log('Rewrite - selection state:', selection)
    
    // Check if there's selected text
    if (!selection.hasSelection || !selection.selectedText.trim()) {
      addNotification({ type: 'warning', message: 'Please select some text to rewrite first' })
      return
    }
    
    const selectedText = selection.selectedText.trim()
    
    // Build the rewrite instruction based on style
    let styleInstruction = ''
    switch (style) {
      case 'Show Don\'t Tell':
        styleInstruction = 'Rewrite this text using "show don\'t tell" technique. Instead of stating emotions or facts directly, demonstrate them through action, dialogue, sensory details, and body language.'
        break
      case 'Dramatic':
        styleInstruction = 'Rewrite this text in a more dramatic, intense style. Heighten the tension, emotions, and stakes. Make it more gripping and impactful.'
        break
      case 'Gritty':
        styleInstruction = 'Rewrite this text in a gritty, raw style. Make it feel more real, edgy, and unpolished. Add texture and roughness.'
        break
      case 'Elegant':
        styleInstruction = 'Rewrite this text in an elegant, refined style. Use sophisticated language, flowing sentences, and poetic imagery.'
        break
      case 'Concise':
        styleInstruction = 'Rewrite this text to be more concise and punchy. Remove unnecessary words, tighten the prose, and make every word count.'
        break
      default:
        styleInstruction = `Rewrite this text in a ${style.toLowerCase()} style.`
    }
    
    const instruction = `${styleInstruction}

=== TEXT TO REWRITE ===
${selectedText}

=== INSTRUCTIONS ===
- Keep the same meaning and key information
- Maintain the same point of view and tense
- Only output the rewritten text, no explanations
- Make it approximately the same length (can be slightly shorter or longer)`
    
    console.log('Rewrite - selected text length:', selectedText.length)
    console.log('Rewrite - style:', style)
    
    // Send to AssistantPanel for generation
    setPendingAiRequest({
      type: 'rewrite',
      instruction: instruction,
      style: style,
      originalText: selectedText,
      selectionStart: selection.selectionStart,
      selectionEnd: selection.selectionEnd,
      replaceSelection: true,
    })
    
    addNotification({ type: 'info', message: `Rewriting ${selectedText.split(/\s+/).length} words in "${style}" style...` })
  }
  
  // Handle Describe action - describes selected text based on chosen senses
  const handleDescribe = async () => {
    // Get selected text from editor
    const selection = currentEditorSelection || { selectedText: '', hasSelection: false }
    
    // Check if there's selected text
    if (!selection.hasSelection || !selection.selectedText.trim()) {
      addNotification({ type: 'warning', message: 'Please select some text to describe first' })
      return
    }
    
    const selectedText = selection.selectedText.trim()
    
    // Get active senses
    const senses = Object.entries(activeSenses)
      .filter(([, active]) => active)
      .map(([sense]) => sense)
    
    if (senses.length === 0) {
      addNotification({ type: 'warning', message: 'Please select at least one sense type from the dropdown' })
      return
    }
    
    // Build descriptions for each sense type with specific instructions
    const senseInstructions = {
      Sight: 'Describe what this looks like visually. Focus on colors, shapes, lighting, movement, and visual details that paint a picture.',
      Sound: 'Describe what sounds are associated with this. Focus on the quality, volume, rhythm, and character of sounds.',
      Smell: 'Describe the scents and aromas. Focus on the intensity, character, and associations of smells.',
      Taste: 'Describe the taste sensations. Focus on flavors, textures in the mouth, and the overall taste experience.',
      Touch: 'Describe the tactile sensations. Focus on texture, temperature, weight, and how it feels physically.',
      Metaphor: 'Create evocative metaphors and similes. Compare this to unexpected things that capture its essence poetically.',
    }
    
    // Build the full prompt with all selected senses
    let fullPrompt = `Generate vivid sensory descriptions for the following text. Write 2-3 paragraphs for EACH requested sense type.\n\n`
    fullPrompt += `=== TEXT TO DESCRIBE ===\n"${selectedText}"\n\n`
    fullPrompt += `=== REQUESTED DESCRIPTIONS ===\n`
    
    senses.forEach(sense => {
      fullPrompt += `\n### ${sense.toUpperCase()}\n${senseInstructions[sense]}\n`
    })
    
    fullPrompt += `\n=== FORMAT ===\n`
    fullPrompt += `For each sense type, write a header like "## SIGHT" or "## METAPHOR" followed by your description paragraphs.\n`
    fullPrompt += `Make each description evocative, specific, and literary. Show, don't tell.`
    
    console.log('Describe - selected text:', selectedText)
    console.log('Describe - senses:', senses)
    
    // Send to AssistantPanel for generation
    setPendingAiRequest({
      type: 'describe',
      instruction: fullPrompt,
      senses: senses,
      originalText: selectedText,
      selectionStart: selection.selectionStart,
      selectionEnd: selection.selectionEnd,
    })
    
    addNotification({ type: 'info', message: `Generating ${senses.join(', ')} descriptions...` })
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
    <header className="h-toolbar flex items-center px-4 gap-4 glass drag-region">
      {/* Left: Navigation */}
      <div className="flex items-center gap-3 no-drag">
        {/* Back to Dashboard */}
        <button
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-text-muted hover:bg-gold-rich/10 hover:text-gold-rich transition-colors"
          onClick={handleBackToDashboard}
          title="Back to Projects"
        >
          <span className="text-lg">{Icons.BACK}</span>
          <span className="text-sm font-medium hidden sm:inline">Projects</span>
        </button>
        
        {/* Separator */}
        <div className="w-px h-6 bg-gold-rich/20" />
        
        {/* Current Project Name */}
        {currentProject && (
          <div className="flex items-center gap-2">
            <span className="text-lg">📖</span>
            <span className="text-sm font-medium text-gold-pale max-w-[150px] truncate">
              {currentProject.name}
            </span>
          </div>
        )}
        
        {/* Toggle Sidebar */}
        <button
          className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:bg-gold-rich/10 hover:text-gold-rich transition-colors"
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
        
        {/* Describe Button - Split button: main button describes, dropdown selects senses */}
        <DescribeSplitButton
          icon={Icons.DESCRIBE}
          label="Describe"
          tooltip="Describe selected text with sensory details"
          onDescribe={handleDescribe}
          activeSenses={activeSenses}
        >
          <div className="px-3 py-2 text-xs text-text-muted font-medium border-b border-gold-rich/10">
            Select senses to describe:
          </div>
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
        </DescribeSplitButton>
        
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
          <hr className="my-2 border-gold-rich/10" />
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
              className="px-2 py-1.5 rounded-l-lg bg-dark-700 text-text-secondary text-sm border border-gold-rich/20 focus:outline-none focus:ring-1 focus:ring-gold-rich cursor-pointer max-w-[100px]"
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
                ? 'bg-gold-rich text-dark-950'
                : 'bg-dark-700 text-text-secondary border border-gold-rich/20 hover:bg-gold-rich/10 hover:text-gold-rich'
            )}
            onClick={handleTts}
            title={isTtsPlaying ? 'Stop Reading' : 'Read Aloud'}
          >
            {isTtsPlaying ? Icons.STOP : Icons.PLAY}
            <span>{isTtsPlaying ? 'Stop' : 'Read'}</span>
          </button>
        </div>
        
        {/* Word Count */}
        <div className="px-3 py-1.5 rounded-lg bg-dark-700/80 text-text-muted text-sm border border-gold-rich/20">
          {wordCount.toLocaleString()} words
        </div>
        
        {/* Save Status */}
        <div className={clsx(
          'px-3 py-1.5 rounded-lg text-sm border',
          isEditorDirty
            ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
            : 'bg-green-500/10 text-green-400 border-green-500/30'
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
            aiStatus === 'loading' && 'bg-gold-rich animate-pulse',
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
          className="w-10 h-10 flex items-center justify-center rounded-lg text-text-muted hover:bg-gold-rich/10 hover:text-gold-rich transition-colors"
          onClick={toggleAssistant}
          title="Toggle Assistant Panel"
        >
          💬
        </button>
      </div>
    </header>
  )
}

export default Toolbar
