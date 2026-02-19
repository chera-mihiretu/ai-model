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
import { CgSpinner } from 'react-icons/cg'
import {
  LuArrowLeft, LuPenLine, LuRefreshCw, LuSparkles, LuWandSparkles,
  LuSettings, LuCircleHelp, LuUpload, LuPlay, LuSquare,
  LuVolume2, LuBookOpen, LuMenu, LuMessageSquare, LuX,
  LuDownload, LuCheck, LuMinus, LuMaximize, LuMinimize,
  LuEye, LuWind, LuDroplets, LuFingerprint, LuLightbulb,
  LuClapperboard, LuShuffle, LuScroll,
  LuCpu, LuFolderSearch, LuBrain,
} from 'react-icons/lu'

// Icon size classes
const ic = 'w-4 h-4'

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
          'px-3 py-2 rounded-lg flex items-center gap-2 min-w-0',
          'bg-dark-700 border border-gold-rich/20',
          'text-text-secondary text-sm font-medium whitespace-nowrap',
          'hover:bg-gold-rich/10 hover:border-gold-rich/40 hover:text-gold-rich',
          'transition-all duration-200',
          isOpen && 'bg-gold-rich/10 border-gold-rich/40 text-gold-rich'
        )}
        onClick={() => hasMenu ? setIsOpen(!isOpen) : onClick?.()}
        title={tooltip}
      >
        <span className="shrink-0">{icon}</span>
        <span className="truncate">{label}</span>
        {hasMenu && <span className="text-xs shrink-0">▾</span>}
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
            'px-3 py-2 rounded-l-lg flex items-center gap-2 min-w-0',
            'bg-dark-700 border border-gold-rich/20 border-r-0',
            'text-text-secondary text-sm font-medium whitespace-nowrap',
            'hover:bg-gold-rich/10 hover:border-gold-rich/40 hover:text-gold-rich',
            'transition-all duration-200'
          )}
          onClick={onDescribe}
          title={tooltip}
        >
          <span className="shrink-0">{icon}</span>
          <span className="truncate">{label}</span>
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
        {icon}
        <span>{label}</span>
      </label>
    )
  }
  
  return (
    <button
      className="dropdown-item w-full text-left flex items-center gap-2"
      onClick={onClick}
    >
      {icon}
      <span>{label}</span>
    </button>
  )
}

function Toolbar() {
  const {
    aiStatus,
    aiStatusMessage,
    aiContextSize,
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
    ttsDownload,
    getContextWindow,
    getCharacters,
    getStoryBible,
    getSceneContext,
    getSeriesContextForProject,
    getContextHealth,
    listModels,
    selectModel,
    browseForModel,
    getAiStatus: refreshAiStatus,
  } = usePythonBridge()
  
  // Write mode state
  const [writeMode, setWriteMode] = useState('Continue Writing')
  
  // Context health state
  const [contextHealth, setContextHealth] = useState(null)
  
  // Periodically check context health when a project is active
  useEffect(() => {
    if (!currentProjectId) {
      setContextHealth(null)
      return
    }
    
    const checkHealth = async () => {
      try {
        const health = await getContextHealth(currentProjectId)
        setContextHealth(health)
      } catch (e) {
        // Silently ignore
      }
    }
    
    checkHealth()
    const interval = setInterval(checkHealth, 60000) // Check every 60 seconds
    return () => clearInterval(interval)
  }, [currentProjectId, getContextHealth])
  
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
    
    // Get scene context for the current chapter
    let sceneContext = ''
    try {
      if (currentChapterId) {
        const sceneData = await getSceneContext(currentChapterId)
        if (sceneData?.formatted) {
          sceneContext = sceneData.formatted
        }
      }
    } catch (e) {
      console.log('Could not get scene context:', e)
    }
    
    // Get series context if project belongs to a series (shared characters & worldbuilding)
    let seriesContext = ''
    try {
      if (currentProjectId) {
        const seriesCtx = await getSeriesContextForProject(currentProjectId)
        if (seriesCtx) {
          seriesContext = seriesCtx
        }
      }
    } catch (e) {
      console.log('Could not get series context:', e)
    }
    
    // Get character, story bible, worldbuilding, and outline context for consistency
    let characterContext = ''
    let storyContext = ''
    let worldbuildingContext = ''
    let outlineContext = ''
    try {
      const characters = await getCharacters(currentProjectId)
      if (characters && characters.length > 0) {
        const visibleChars = characters.filter(c => c.is_visible !== 0)
        if (visibleChars.length > 0) {
          characterContext = visibleChars.slice(0, 8).map(c => {
            let entry = `${c.name}${c.role ? ` (${c.role})` : ''}`
            if (c.personality_traits) entry += `: ${c.personality_traits}`
            if (c.speech_pattern) entry += ` | Speech: ${c.speech_pattern}`
            if (c.motivations) entry += ` | Motivations: ${c.motivations}`
            return entry
          }).join('\n')
        }
      }
      
      const bible = await getStoryBible(currentProjectId)
      if (bible) {
        // Use summary if available, fall back to raw content (trimmed)
        if (bible.synopsis_summary) {
          storyContext = bible.synopsis_summary
        } else if (bible.synopsis) {
          storyContext = bible.synopsis.substring(0, 800)
        }
        
        // Worldbuilding context
        if (bible.worldbuilding_summary) {
          worldbuildingContext = bible.worldbuilding_summary
        } else if (bible.worldbuilding) {
          worldbuildingContext = bible.worldbuilding.substring(0, 600)
        }
        
        // Outline context
        if (bible.outline_summary) {
          outlineContext = bible.outline_summary
        } else if (bible.outline) {
          // Try to parse JSON outline for a cleaner representation
          try {
            const outlineData = JSON.parse(bible.outline)
            if (Array.isArray(outlineData)) {
              outlineContext = outlineData.slice(0, 15).map(ch => 
                `Ch ${ch.chapter_number || '?'}: ${ch.title || 'Untitled'} - ${ch.summary || ''}`
              ).join('\n')
            }
          } catch {
            outlineContext = bible.outline.substring(0, 600)
          }
        }
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
    
    // Build full context for AI - Sudowrite-style comprehensive awareness
    let fullPrompt = instruction + '\n\n'
    
    if (chapterContinuity) {
      fullPrompt += `=== PREVIOUS CHAPTER SUMMARY ===\n${chapterContinuity}\n\n`
    }
    
    if (storyContext) {
      fullPrompt += `=== STORY SYNOPSIS ===\n${storyContext}\n\n`
    }
    
    if (outlineContext) {
      fullPrompt += `=== STORY OUTLINE ===\n${outlineContext}\n\n`
    }
    
    if (worldbuildingContext) {
      fullPrompt += `=== WORLDBUILDING ===\n${worldbuildingContext}\n\n`
    }
    
    if (characterContext) {
      fullPrompt += `=== KEY CHARACTERS ===\n${characterContext}\n\n`
    }
    
    if (sceneContext) {
      fullPrompt += `=== CHAPTER SCENES ===\n${sceneContext}\n\n`
    }
    
    if (seriesContext) {
      fullPrompt += `=== SERIES CONTEXT (shared across books) ===\n${seriesContext}\n\n`
    }
    
    if (textAfterCursor && textAfterCursor.trim()) {
      // Trim to ~500 chars so the model knows what comes next without overwhelming context
      const aheadText = textAfterCursor.substring(0, 500)
      fullPrompt += `=== TEXT AHEAD (do not repeat this, just be aware of what follows) ===\n${aheadText}\n\n`
    }
    
    if (precedingText) {
      fullPrompt += `=== TEXT TO CONTINUE FROM (last ~1000 words) ===\n${precedingText}\n\n`
      fullPrompt += `Continue from here, matching the style and voice exactly. DO NOT repeat the existing text - just continue naturally.`
    }
    
    console.log('Write button - cursor position:', cursorPosition)
    console.log('Write button - preceding text words:', precedingText.split(/\s+/).length)
    console.log('Write button - has chapter continuity:', !!chapterContinuity)
    console.log('Write button - has worldbuilding:', !!worldbuildingContext)
    console.log('Write button - has outline:', !!outlineContext)
    console.log('Write button - has text ahead:', !!textAfterCursor)
    
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
        worldbuildingContext,
        outlineContext,
        sceneContext,
        seriesContext,
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
    
    // Get surrounding editor context so the AI understands the local scene
    let surroundingContext = { precedingText: '', textAfterCursor: '' }
    if (editorCursorContextCallback) {
      surroundingContext = editorCursorContextCallback()
    }
    
    // Build the rewrite instruction based on style
    const styleDescriptions = {
      'Show Don\'t Tell': 'using "show don\'t tell" - demonstrate through action, dialogue, sensory details, and body language instead of stating directly',
      'Dramatic': 'in a more dramatic, intense style with heightened tension, emotions, and stakes',
      'Gritty': 'in a gritty, raw style that feels more real, edgy, and unpolished',
      'Elegant': 'in an elegant, refined style with sophisticated language and flowing sentences',
      'Concise': 'to be more concise and punchy, removing unnecessary words',
    }
    
    const styleDesc = styleDescriptions[style] || `in a ${style.toLowerCase()} style`
    
    let instruction = `Rewrite this text ${styleDesc}:\n\n"${selectedText}"\n\n`
    
    // Include surrounding text so the AI can match tone and flow
    if (surroundingContext.precedingText) {
      const precedingSnippet = surroundingContext.precedingText.slice(-500)
      instruction += `=== SURROUNDING CONTEXT (text before selection) ===\n${precedingSnippet}\n\n`
    }
    if (surroundingContext.textAfterCursor) {
      const followingSnippet = surroundingContext.textAfterCursor.substring(0, 300)
      instruction += `=== SURROUNDING CONTEXT (text after selection) ===\n${followingSnippet}\n\n`
    }
    
    instruction += `RULES:
- Output ONLY the rewritten text, nothing else
- Do NOT start with "Here's" or "Here is" or any introduction
- Do NOT end with explanations like "I maintained..." or "This version..."
- Do NOT include quotes around the output
- Keep the same meaning and point of view
- Match the tone and voice of the surrounding context
- The output should be ready to paste directly into a document`
    
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
      context: {
        precedingText: surroundingContext.precedingText?.slice(-500) || '',
        textAfterCursor: surroundingContext.textAfterCursor?.substring(0, 300) || '',
      },
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
    
    // Get surrounding editor context for scene awareness
    let surroundingContext = { precedingText: '', textAfterCursor: '' }
    if (editorCursorContextCallback) {
      surroundingContext = editorCursorContextCallback()
    }
    
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
    
    // Include surrounding context so descriptions match the scene
    if (surroundingContext.precedingText) {
      const precedingSnippet = surroundingContext.precedingText.slice(-400)
      fullPrompt += `=== SCENE CONTEXT (text before selection) ===\n${precedingSnippet}\n\n`
    }
    if (surroundingContext.textAfterCursor) {
      const followingSnippet = surroundingContext.textAfterCursor.substring(0, 200)
      fullPrompt += `=== SCENE CONTEXT (text after selection) ===\n${followingSnippet}\n\n`
    }
    
    fullPrompt += `=== REQUESTED DESCRIPTIONS ===\n`
    
    senses.forEach(sense => {
      fullPrompt += `\n### ${sense.toUpperCase()}\n${senseInstructions[sense]}\n`
    })
    
    fullPrompt += `\n=== FORMAT ===\n`
    fullPrompt += `For each sense type, write a header like "## SIGHT" or "## METAPHOR" followed by your description paragraphs.\n`
    fullPrompt += `Make each description evocative, specific, and literary. Show, don't tell. Match the tone and atmosphere of the surrounding scene.`
    
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
      context: {
        precedingText: surroundingContext.precedingText?.slice(-400) || '',
        textAfterCursor: surroundingContext.textAfterCursor?.substring(0, 200) || '',
      },
    })
    
    addNotification({ type: 'info', message: `Generating ${senses.join(', ')} descriptions...` })
  }
  
  // Handle TTS
  const { setTtsPlaying } = useStore()
  const [isDownloading, setIsDownloading] = useState(false)
  
  // Model picker state
  const [modelPickerOpen, setModelPickerOpen] = useState(false)
  const [availableModels, setAvailableModels] = useState([])
  const [isLoadingModel, setIsLoadingModel] = useState(false)
  const modelPickerRef = useRef(null)
  
  // Close model picker on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (modelPickerRef.current && !modelPickerRef.current.contains(event.target)) {
        setModelPickerOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  // Fetch available models when picker opens
  const handleOpenModelPicker = async () => {
    setModelPickerOpen(!modelPickerOpen)
    if (!modelPickerOpen) {
      const models = await listModels()
      setAvailableModels(models)
    }
  }
  
  // Handle model selection
  const handleSelectModel = async (modelPath) => {
    setIsLoadingModel(true)
    setModelPickerOpen(false)
    try {
      await selectModel(modelPath)
    } finally {
      setIsLoadingModel(false)
    }
  }
  
  // Handle browse for model
  const handleBrowseForModel = async () => {
    setIsLoadingModel(true)
    setModelPickerOpen(false)
    try {
      await browseForModel()
    } finally {
      setIsLoadingModel(false)
    }
  }
  
  // Extract model name from path for display
  const getModelDisplayName = (path) => {
    if (!path) return 'No Model'
    const filename = path.split(/[\\/]/).pop()
    // Remove .gguf extension and clean up
    return filename.replace(/\.gguf$/i, '').replace(/[-_]/g, ' ')
  }
  
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
  
  const handleTtsDownload = async () => {
    if (isDownloading) return
    setIsDownloading(true)
    try {
      await ttsDownload(editorContent, selectedVoice)
    } finally {
      setIsDownloading(false)
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
      <div className="flex items-center gap-2 no-drag shrink-0">
        {/* Back to Dashboard */}
        <button
          className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:bg-gold-rich/10 hover:text-gold-rich transition-colors"
          onClick={handleBackToDashboard}
          title="Back to Projects"
        >
          <LuArrowLeft className="w-4 h-4" />
        </button>
        
        {/* Toggle Sidebar */}
        <button
          className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:bg-gold-rich/10 hover:text-gold-rich transition-colors"
          onClick={toggleSidebar}
          title="Toggle Sidebar"
        >
          <LuMenu className={ic} />
        </button>
      </div>
      
      {/* Center: AI Tools */}
      <div className="flex items-center gap-2 flex-1 justify-center no-drag min-w-0 overflow-hidden">
        {/* Write Button */}
        <ToolbarButton
          icon={<LuPenLine className={ic} />}
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
          icon={<LuRefreshCw className={ic} />}
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
          icon={<LuSparkles className={ic} />}
          label="Describe"
          tooltip="Describe selected text with sensory details"
          onDescribe={handleDescribe}
          activeSenses={activeSenses}
        >
          <div className="px-3 py-2 text-xs text-text-muted font-medium border-b border-gold-rich/10">
            Select senses to describe:
          </div>
          <MenuItem
            icon={<LuEye className={ic} />}
            label="Sight"
            checkbox
            checked={activeSenses.Sight}
            onCheck={(checked) => setActiveSenses(s => ({ ...s, Sight: checked }))}
          />
          <MenuItem
            icon={<LuVolume2 className={ic} />}
            label="Sound"
            checkbox
            checked={activeSenses.Sound}
            onCheck={(checked) => setActiveSenses(s => ({ ...s, Sound: checked }))}
          />
          <MenuItem
            icon={<LuWind className={ic} />}
            label="Smell"
            checkbox
            checked={activeSenses.Smell}
            onCheck={(checked) => setActiveSenses(s => ({ ...s, Smell: checked }))}
          />
          <MenuItem
            icon={<LuDroplets className={ic} />}
            label="Taste"
            checkbox
            checked={activeSenses.Taste}
            onCheck={(checked) => setActiveSenses(s => ({ ...s, Taste: checked }))}
          />
          <MenuItem
            icon={<LuFingerprint className={ic} />}
            label="Touch"
            checkbox
            checked={activeSenses.Touch}
            onCheck={(checked) => setActiveSenses(s => ({ ...s, Touch: checked }))}
          />
          <MenuItem
            icon={<LuLightbulb className={ic} />}
            label="Metaphor"
            checkbox
            checked={activeSenses.Metaphor}
            onCheck={(checked) => setActiveSenses(s => ({ ...s, Metaphor: checked }))}
          />
        </DescribeSplitButton>
        
        {/* More Tools Button */}
        <ToolbarButton
          icon={<LuWandSparkles className={ic} />}
          label="More Tools"
          tooltip="Additional AI tools"
          hasMenu
        >
          <MenuItem icon={<LuClapperboard className={ic} />} label="Visualize" onClick={() => {}} />
          <MenuItem icon={<LuShuffle className={ic} />} label="Twist" onClick={() => {}} />
          <MenuItem icon={<LuScroll className={ic} />} label="Poem" onClick={() => {}} />
          <hr className="my-2 border-gold-rich/10" />
          <MenuItem icon={<LuUpload className={ic} />} label="Export" onClick={() => {}} />
          <MenuItem icon={<LuSettings className={ic} />} label="Settings" onClick={() => {}} />
        </ToolbarButton>
      </div>
      
      {/* Right: Status & Controls */}
      <div className="flex items-center gap-3 no-drag shrink-0">
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
              'px-3 py-1.5 flex items-center gap-2 text-sm whitespace-nowrap',
              'transition-all duration-200',
              isTtsPlaying
                ? 'bg-gold-rich text-dark-950'
                : 'bg-dark-700 text-text-secondary border border-gold-rich/20 hover:bg-gold-rich/10 hover:text-gold-rich'
            )}
            onClick={handleTts}
            title={isTtsPlaying ? 'Stop Reading' : 'Read Aloud'}
          >
            {isTtsPlaying ? <LuSquare className={ic} /> : <LuPlay className={ic} />}
            <span>{isTtsPlaying ? 'Stop' : 'Read'}</span>
          </button>
          
          {/* Download Speech Button */}
          <button
            className={clsx(
              'p-1.5 flex items-center justify-center',
              'transition-all duration-200 rounded-r-lg',
              isDownloading
                ? 'bg-gold-rich/60 text-dark-950 cursor-wait'
                : 'bg-dark-700 text-text-secondary border border-gold-rich/20 hover:bg-gold-rich/10 hover:text-gold-rich'
            )}
            onClick={handleTtsDownload}
            disabled={isDownloading}
            title="Download chapter as MP3 audio"
          >
            {isDownloading
              ? <CgSpinner className={`${ic} animate-spin`} />
              : <LuDownload className={ic} />
            }
          </button>
        </div>
        
        {/* Context Health Indicator */}
        {contextHealth && contextHealth.overall && contextHealth.overall !== 'empty' && (
          <div
            className={clsx(
              'px-2 py-1.5 rounded-lg text-xs border flex items-center gap-1.5 cursor-help',
              contextHealth.overall === 'fresh' && 'bg-green-500/10 text-green-400 border-green-500/30',
              contextHealth.overall === 'stale' && 'bg-amber-500/10 text-amber-400 border-amber-500/30',
              contextHealth.overall === 'missing' && 'bg-red-500/10 text-red-400 border-red-500/30',
            )}
            title={`AI Context: ${contextHealth.overall === 'fresh' ? 'All summaries up-to-date' : contextHealth.overall === 'stale' ? 'Some summaries are outdated - will auto-refresh' : 'Missing summaries - writing to Story Bible will generate them'}\n\nCharacters: ${contextHealth.characters || 'empty'}\nWorld: ${contextHealth.world_elements || 'empty'}\nSynopsis: ${contextHealth.synopsis || 'empty'}\nOutline: ${contextHealth.outline || 'empty'}\nChapters: ${contextHealth.chapters || 'empty'}`}
          >
            <span className={clsx(
              'w-1.5 h-1.5 rounded-full',
              contextHealth.overall === 'fresh' && 'bg-green-400',
              contextHealth.overall === 'stale' && 'bg-amber-400',
              contextHealth.overall === 'missing' && 'bg-red-400',
            )} />
            <LuBrain className="w-3 h-3" />
          </div>
        )}
        
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
          {isEditorDirty ? 'Unsaved' : (<span className="flex items-center gap-1"><LuCheck className="w-3.5 h-3.5" /> Saved</span>)}
        </div>
        
        {/* AI Status & Model Picker */}
        <div className="relative" ref={modelPickerRef} style={{ zIndex: modelPickerOpen ? 9999 : 'auto' }}>
          <button
            className={clsx(
              'ai-status cursor-pointer',
              aiStatus === 'ready' && 'ready',
              aiStatus === 'loading' && 'loading',
              aiStatus === 'error' && 'error',
              isLoadingModel && 'loading'
            )}
            onClick={handleOpenModelPicker}
            title={aiStatusMessage || 'Click to manage AI models'}
          >
            {isLoadingModel ? (
              <CgSpinner className="w-3.5 h-3.5 animate-spin shrink-0" />
            ) : (
              <span className={clsx(
                'w-2 h-2 rounded-full shrink-0',
                aiStatus === 'ready' && 'bg-green-400',
                aiStatus === 'loading' && 'bg-gold-rich animate-pulse',
                aiStatus === 'error' && 'bg-red-400'
              )} />
            )}
            <span className="truncate max-w-[140px]">
              {isLoadingModel
                ? 'Loading Model...'
                : isAiGenerating 
                  ? 'Generating...' 
                  : aiStatus === 'ready' 
                    ? 'AI Ready' 
                    : aiStatus === 'loading'
                      ? 'Loading Model...'
                      : 'No AI Model'}
            </span>
            <span className="text-xs shrink-0">▾</span>
          </button>
          
          {modelPickerOpen && (
            <div className="absolute right-0 top-full mt-1 w-72 rounded-xl bg-dark-800 border border-gold-rich/20 shadow-2xl py-2" style={{ zIndex: 9999 }}>
              {/* Header */}
              <div className="px-4 py-2 border-b border-gold-rich/10">
                <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                  <LuBrain className="w-4 h-4 text-gold-rich" />
                  AI Model Selection
                </div>
                <p className="text-xs text-text-muted mt-1">
                  {aiStatus === 'ready' 
                    ? 'Select a different model or browse for one.' 
                    : 'No model loaded. Pick one from the list or browse.'}
                </p>
              </div>
              
              {/* Current model indicator */}
              {aiStatus === 'ready' && aiStatusMessage && (
                <div className="px-4 py-2 border-b border-gold-rich/10">
                  <div className="text-xs text-text-muted mb-1">Current Model</div>
                  <div className="text-sm text-green-400 flex items-center gap-2">
                    <LuCheck className="w-3.5 h-3.5 shrink-0" />
                    <span className="truncate">{aiStatusMessage}</span>
                  </div>
                  {aiContextSize > 0 && (
                    <div className="text-xs text-text-muted mt-1">
                      Context window: {aiContextSize.toLocaleString()} tokens
                    </div>
                  )}
                </div>
              )}
              
              {/* Available models list */}
              {availableModels.length > 0 && (
                <div className="py-1">
                  <div className="px-4 py-1.5 text-xs font-medium text-text-muted">
                    Models in models/llama/
                  </div>
                  {availableModels.map((model) => (
                    <button
                      key={model.path}
                      className={clsx(
                        'w-full px-4 py-2 flex items-center gap-3 text-left text-sm',
                        'hover:bg-gold-rich/10 transition-colors',
                        model.is_active 
                          ? 'text-gold-rich bg-gold-rich/5' 
                          : 'text-text-secondary'
                      )}
                      onClick={() => handleSelectModel(model.path)}
                    >
                      <LuCpu className={clsx('w-4 h-4 shrink-0', model.is_active ? 'text-gold-rich' : 'text-text-muted')} />
                      <div className="min-w-0 flex-1">
                        <div className="truncate font-medium">{model.name.replace(/\.gguf$/i, '')}</div>
                        <div className="text-xs text-text-muted">{model.size_gb} GB</div>
                      </div>
                      {model.is_active && (
                        <LuCheck className="w-4 h-4 text-green-400 shrink-0" />
                      )}
                    </button>
                  ))}
                </div>
              )}
              
              {/* No models found message */}
              {availableModels.length === 0 && (
                <div className="px-4 py-3 text-center">
                  <LuCpu className="w-8 h-8 text-text-muted mx-auto mb-2" />
                  <p className="text-sm text-text-muted">No .gguf models found</p>
                  <p className="text-xs text-text-muted mt-1">
                    Place models in <code className="text-gold-rich/80">models/llama/</code> or browse below
                  </p>
                </div>
              )}
              
              {/* Browse action */}
              <div className="border-t border-gold-rich/10 pt-1 mt-1">
                <button
                  className="w-full px-4 py-2.5 flex items-center gap-3 text-left text-sm text-text-secondary hover:bg-gold-rich/10 hover:text-gold-rich transition-colors"
                  onClick={handleBrowseForModel}
                >
                  <LuFolderSearch className="w-4 h-4 shrink-0" />
                  <span>Browse for model file...</span>
                </button>
              </div>
            </div>
          )}
        </div>
        
        {/* Toggle Assistant */}
        <button
          className="w-10 h-10 flex items-center justify-center rounded-lg text-text-muted hover:bg-gold-rich/10 hover:text-gold-rich transition-colors"
          onClick={toggleAssistant}
          title="Toggle Assistant Panel"
        >
          <LuMessageSquare className="w-5 h-5" />
        </button>
        
        {/* Window Controls */}
        <div className="flex items-center ml-1">
          <button
            className="w-7 h-7 flex items-center justify-center rounded text-text-muted hover:bg-white/10 hover:text-text-primary transition-colors"
            onClick={() => window.api?.windowMinimize?.()}
            title="Minimize"
          >
            <LuMinus className="w-3.5 h-3.5" />
          </button>
          <button
            className="w-7 h-7 flex items-center justify-center rounded text-text-muted hover:bg-white/10 hover:text-text-primary transition-colors"
            onClick={() => window.api?.windowMaximize?.()}
            title="Maximize"
          >
            <LuMaximize className="w-3 h-3" />
          </button>
          <button
            className="w-7 h-7 flex items-center justify-center rounded text-text-muted hover:bg-red-500/80 hover:text-white transition-colors"
            onClick={() => window.api?.windowClose?.()}
            title="Close"
          >
            <LuX className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </header>
  )
}

export default Toolbar
