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
  LuCpu, LuFolderSearch, LuBrain, LuCloud, LuHardDrive, LuTrash2,
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
    // TTS Mode
    ttsMode,
    setTtsMode,
    ttsAvailability,
    setTtsAvailability,
    localVoices,
    setLocalVoices,
    isDownloadingVoice,
    setIsDownloadingVoice,
    voiceDownloadProgress,
    setVoiceDownloadProgress,
    setTtsVoices,
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
    // TTS Mode methods
    getTtsMode: fetchTtsMode,
    setTtsMode: applyTtsMode,
    getTtsAvailability: fetchTtsAvailability,
    getLocalVoices: fetchLocalVoices,
    downloadLocalVoice,
    deleteLocalVoice,
    getTtsVoices,
    // App state for persistence
    saveAppState,
    getAppState,
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
  
  // Guided Generation state
  const [showGuidedPrompt, setShowGuidedPrompt] = useState(false)
  const [guidedPrompt, setGuidedPrompt] = useState('')
  
  // Handle Guided Generation - show prompt dialog
  const handleGuidedGeneration = () => {
    if (!currentChapterId) {
      addNotification({ type: 'warning', message: 'Please select a chapter first' })
      return
    }
    setShowGuidedPrompt(true)
  }
  
  // Execute guided generation with user prompt
  const executeGuidedGeneration = async () => {
    if (!guidedPrompt.trim()) {
      addNotification({ type: 'warning', message: 'Please enter a prompt' })
      return
    }
    
    setShowGuidedPrompt(false)
    setWriteMode('Guided Generation')
    
    // Get cursor position context from editor
    const editorText = currentEditorSelection?.fullText || ''
    const cursorPos = currentEditorSelection?.cursorPosition || 0
    
    // Extract context around cursor (last 1000 chars before cursor)
    const contextStart = Math.max(0, cursorPos - 1000)
    const chapterContext = editorText.substring(contextStart, cursorPos)
    
    // Get genre from story bible
    let genre = 'fiction'
    try {
      const bible = await getStoryBible(currentProjectId)
      if (bible?.genre) genre = bible.genre
    } catch (e) {
      // Use default
    }
    
    // Send request to AI via setPendingAiRequest (same as other write modes)
    const request = {
      type: 'guided_generation',
      instruction: guidedPrompt.trim(),
      chapterContext: chapterContext,
      genre: genre,
      chapterId: currentChapterId,
      cursorPosition: cursorPos,
      insertAtCursor: true
    }
    
    // Open assistant panel if not already open
    if (!useStore.getState().isAssistantOpen) {
      toggleAssistant()
    }
    
    setPendingAiRequest(request)
    
    setGuidedPrompt('')
  }
  
  // Handle Write action - Sudowrite-style context-aware writing
  const handleWrite = async (mode) => {
    setWriteMode(mode)
    
    // Check if we have a chapter selected
    if (!currentChapterId) {
      addNotification({ type: 'warning', message: 'Please select a chapter first' })
      return
    }
    
    // Get current selection for Expand mode
    const hasSelection = currentEditorSelection?.hasSelection && currentEditorSelection?.selectedText?.trim()
    const selection = hasSelection ? currentEditorSelection : null
    
    // === MODE-SPECIFIC VALIDATION ===
    
    // Expand: requires text selection
    if (mode === 'Expand') {
      if (!hasSelection) {
        addNotification({ type: 'warning', message: 'Please select text first to expand' })
        return
      }
    }
    
    // === GATHER CONTEXT (with timeouts to prevent hanging) ===
    let outlineContext = ''
    let storyContext = ''  // synopsis
    let braindumpContext = ''
    let characterContext = ''
    let worldbuildingContext = ''
    let styleContext = ''
    let genreContext = ''
    let sceneContext = ''
    let chapterContinuity = ''
    let seriesContext = ''
    
    try {
      // Get story bible data (contains outline, synopsis, braindump, style, genre, worldbuilding)
      const bible = await Promise.race([
        getStoryBible(currentProjectId),
        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 5000))
      ]).catch(() => null)
      
      if (bible) {
        // Extract outline
        if (bible.outline_summary) {
          outlineContext = bible.outline_summary
        } else if (bible.outline) {
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
        
        // Extract synopsis
        if (bible.synopsis_summary) {
          storyContext = bible.synopsis_summary
        } else if (bible.synopsis) {
          storyContext = bible.synopsis.substring(0, 800)
        }
        
        // Extract braindump
        if (bible.braindump) {
          braindumpContext = bible.braindump.substring(0, 600)
        }
        
        // Extract other context
        if (bible.worldbuilding_summary) {
          worldbuildingContext = bible.worldbuilding_summary
        } else if (bible.worldbuilding) {
          worldbuildingContext = bible.worldbuilding.substring(0, 600)
        }
        
        if (bible.style) styleContext = bible.style.substring(0, 300)
        if (bible.genre) genreContext = bible.genre.substring(0, 100)
      }
      
      // Get characters with full details
      const characters = await Promise.race([
        getCharacters(currentProjectId),
        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 3000))
      ]).catch(() => null)
      
      if (characters && characters.length > 0) {
        const visibleChars = characters.filter(c => c.is_visible !== 0)
        if (visibleChars.length > 0) {
          characterContext = visibleChars.slice(0, 8).map(c => {
            let entry = `**${c.name}**${c.role ? ` (${c.role})` : ''}`
            if (c.personality_traits) entry += `\n  Personality: ${c.personality_traits}`
            if (c.motivations) entry += `\n  Motivations: ${c.motivations}`
            if (c.backstory) entry += `\n  Background: ${c.backstory.substring(0, 200)}`
            if (c.speech_pattern) entry += `\n  Speech style: ${c.speech_pattern}`
            if (c.physical_description) entry += `\n  Appearance: ${c.physical_description.substring(0, 150)}`
            return entry
          }).join('\n\n')
        }
      }
      
      // Get scene context (optional, don't block)
      const sceneData = await Promise.race([
        getSceneContext(currentChapterId),
        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 2000))
      ]).catch(() => null)
      
      if (sceneData?.formatted) {
        sceneContext = sceneData.formatted
      }
      
      // Get chapter continuity (optional)
      const contextWindow = await Promise.race([
        getContextWindow(currentProjectId, currentChapterId, 2000),
        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 2000))
      ]).catch(() => null)
      
      if (contextWindow?.prev_summary) {
        chapterContinuity = contextWindow.prev_summary
      }
      
    } catch (e) {
      // Silently handle context gathering errors
    }
    
    // === CHECK IF WE HAVE ENOUGH CONTEXT FOR WRITE SCENE / GENERATE OPENING ===
    // Priority: outline -> synopsis -> braindump -> error
    const primaryContext = outlineContext || storyContext || braindumpContext
    
    if (mode === 'Write Scene' || mode === 'Generate Opening') {
      if (!primaryContext) {
        addNotification({ 
          type: 'error', 
          message: 'Please add a chapter outline, synopsis, or braindump first to generate content' 
        })
        return
      }
    }
    
    // === BUILD INSTRUCTION BASED ON MODE ===
    let instruction = ''
    switch (mode) {
      case 'Continue Writing':
        instruction = 'Continue writing the story naturally from where it left off. Match the tone, style, and pacing of the existing text. Write 2-3 paragraphs that flow seamlessly from the last sentence.'
        break
      case 'Write Scene':
        instruction = hasExistingText
          ? 'Write a new dramatic scene that advances the plot. Include vivid descriptions, character interactions, and forward momentum. Write 3-4 paragraphs.'
          : 'Write a dramatic opening scene for this chapter. Ground the reader in the setting, introduce conflict, and establish momentum. Write 3-4 paragraphs.'
        break
      case 'Generate Opening':
        instruction = 'Write a captivating opening paragraph that hooks the reader immediately. Use vivid imagery, establish the scene, and create intrigue. This is the very first line the reader will see.'
        break
      case 'Expand':
        instruction = `Expand and enrich the following selected text with more detail, sensory descriptions, internal thoughts, and nuance. Deepen the scene without changing its direction.\n\nSELECTED TEXT TO EXPAND:\n${selection.selectedText}`
        break
      default:
        instruction = 'Write creative narrative prose that continues the story.'
    }
    
    // === BUILD FULL PROMPT WITH ALL AVAILABLE CONTEXT ===
    let fullPrompt = instruction + '\n\n'
    
    // Story structure context (outline is primary guide)
    if (outlineContext) {
      fullPrompt += `=== CHAPTER OUTLINE (follow this structure) ===\n${outlineContext}\n\n`
    }
    
    // Synopsis provides overall story direction
    if (storyContext) {
      fullPrompt += `=== STORY SYNOPSIS ===\n${storyContext}\n\n`
    }
    
    // Braindump contains additional story ideas and notes
    if (braindumpContext) {
      fullPrompt += `=== STORY IDEAS & NOTES ===\n${braindumpContext}\n\n`
    }
    
    // Characters - ALWAYS include for consistent characterization
    if (characterContext) {
      fullPrompt += `=== KEY CHARACTERS (use these names, traits, and speech patterns) ===\n${characterContext}\n\n`
    }
    
    // Scene context for this specific chapter
    if (sceneContext) {
      fullPrompt += `=== SCENE BLUEPRINT ===\n${sceneContext}\n\n`
    }
    
    // Worldbuilding - ALWAYS include for consistent setting
    if (worldbuildingContext) {
      fullPrompt += `=== WORLDBUILDING (setting, rules, atmosphere) ===\n${worldbuildingContext}\n\n`
    }
    
    // Genre & Style
    if (genreContext) {
      fullPrompt += `=== GENRE ===\n${genreContext}\n\n`
    }
    if (styleContext) {
      fullPrompt += `=== WRITING STYLE ===\n${styleContext}\n\n`
    }
    
    // Chapter continuity for story flow
    if (chapterContinuity) {
      fullPrompt += `=== PREVIOUS CHAPTER SUMMARY ===\n${chapterContinuity}\n\n`
    }
    
    // Text context for continuation (only for Continue Writing)
    if (mode === 'Continue Writing') {
      // Get the current chapter content from editor
      const currentText = editorContent || ''
      
      // Trim to last ~3000 chars to stay within token limits
      const maxPrecedingChars = 3000
      const trimmedText = currentText.length > maxPrecedingChars 
        ? currentText.slice(-maxPrecedingChars) 
        : currentText
      
      if (trimmedText.trim()) {
        fullPrompt += `=== EXISTING CHAPTER TEXT ===\n${trimmedText}\n\n`
        fullPrompt += `Continue the story from where it left off. Match the style, voice, and tone exactly. DO NOT repeat the existing text. Generate new content that naturally follows what came before and advances the plot.`
      } else {
        fullPrompt += `Generate the opening of this chapter. Match the style and voice from the story context provided above.`
      }
    }
    
    // Send to AssistantPanel for generation
    setPendingAiRequest({
      type: 'write',
      instruction: fullPrompt,
      mode: mode,
      insertAtCursor: mode === 'Continue Writing', // Continue Writing inserts at end
      replaceSelection: mode === 'Expand',
      originalText: mode === 'Expand' ? selection?.selectedText : undefined,
      selectionStart: mode === 'Expand' ? selection?.selectionStart : undefined,
      selectionEnd: mode === 'Expand' ? selection?.selectionEnd : undefined,
      context: {
        chapterContinuity,
        characterContext,
        storyContext,
        worldbuildingContext,
        outlineContext,
        sceneContext,
        seriesContext,
        styleContext,
        genreContext,
      }
    })
    
    addNotification({ type: 'info', message: `AI is generating ${mode.toLowerCase()}...` })
  }
  
  // Helper: get the current editor selection from multiple sources
  const getEditorSelection = () => {
    if (currentEditorSelection?.hasSelection && currentEditorSelection.selectedText?.trim()) {
      return currentEditorSelection
    }
    if (editorInstance) {
      const { from, to } = editorInstance.state.selection
      if (from !== to) {
        const text = editorInstance.state.doc.textBetween(from, to, ' ')
        if (text.trim()) {
          return { selectedText: text, selectionStart: from, selectionEnd: to, hasSelection: true }
        }
      }
    }
    return { selectedText: '', hasSelection: false, selectionStart: 0, selectionEnd: 0 }
  }

  // Handle Rewrite action - rewrites selected text in a specific style
  const handleRewrite = async (style) => {
    const selection = getEditorSelection()
    
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
    const selection = getEditorSelection()
    
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

  // Handle More Tools (Brainstorm, Visualize, Twist, Poem)
  const handleMoreTool = (tool) => {
    const editorText = editorInstance?.getText()?.trim() || ''
    const excerpt = editorText.slice(-600) || '(No content yet)'

    const toolPrompts = {
      brainstorm: {
        instruction: 'Brainstorm 5-7 creative ideas for the current story. Consider plot developments, character arcs, thematic depth, and surprising twists. Number each idea with a brief explanation.',
        message: 'Brainstorming ideas...',
      },
      visualize: {
        instruction: `Create a vivid, cinematic visualization of this scene. Describe the setting in rich sensory detail — lighting, atmosphere, character positioning, and mood.\n\nScene text:\n${editorText.slice(-800) || '(Describe the opening scene based on available story context.)'}`,
        message: 'Visualizing scene...',
      },
      twist: {
        instruction: `Generate 5 unexpected plot twists for this story. Each should subvert expectations, raise stakes, and feel earned. Number each with setup and payoff.\n\nCurrent text:\n${excerpt}`,
        message: 'Generating plot twists...',
      },
      poem: {
        instruction: `Write a poem inspired by this story capturing themes, emotions, and imagery. Choose the style that fits the tone best.\n\nStory excerpt:\n${excerpt}`,
        message: 'Writing poem...',
      },
    }

    const config = toolPrompts[tool]
    if (!config) return

    setPendingAiRequest({
      type: tool === 'brainstorm' ? 'brainstorm' : 'write',
      instruction: config.instruction,
      formData: { tool },
    })

    addNotification({ type: 'info', message: config.message })
  }

  // Handle TTS
  const { setTtsPlaying } = useStore()
  const [isDownloading, setIsDownloading] = useState(false)
  const [downloadProgress, setDownloadProgress] = useState(0)
  
  // Model picker state
  const [modelPickerOpen, setModelPickerOpen] = useState(false)
  const [availableModels, setAvailableModels] = useState([])
  const [isLoadingModel, setIsLoadingModel] = useState(false)
  const modelPickerRef = useRef(null)
  
  // TTS Mode picker state
  const [ttsPickerOpen, setTtsPickerOpen] = useState(false)
  const ttsPickerRef = useRef(null)
  
  // Initialize TTS mode and availability on mount
  useEffect(() => {
    const initTtsMode = async () => {
      try {
        // Try to restore saved TTS mode preference
        const savedMode = await getAppState('tts_mode')
        const savedVoice = await getAppState('selected_voice')
        
        const availability = await fetchTtsAvailability()
        setTtsAvailability(availability)
        
        let currentMode = 'cloud'
        
        // Apply saved mode if valid, otherwise get current mode from backend
        if (savedMode && (savedMode === 'cloud' || savedMode === 'local')) {
          // Only apply local mode if it's available
          if (savedMode === 'local' && availability?.local) {
            await applyTtsMode(savedMode)
            setTtsMode(savedMode)
            currentMode = savedMode
          } else if (savedMode === 'cloud' && availability?.cloud) {
            await applyTtsMode(savedMode)
            setTtsMode(savedMode)
            currentMode = savedMode
          } else {
            // Fallback to current backend mode
            const mode = await fetchTtsMode()
            setTtsMode(mode)
            currentMode = mode
          }
        } else {
          const mode = await fetchTtsMode()
          setTtsMode(mode)
          currentMode = mode
        }
        
        const voices = await fetchLocalVoices()
        setLocalVoices(voices)
        
        // Fetch cloud voices for the dropdown
        const cloudVoices = await getTtsVoices()
        if (cloudVoices && cloudVoices.length > 0) {
          setTtsVoices(cloudVoices)
        }
        
        // Set selected voice based on current mode
        if (currentMode === 'local') {
          const downloadedVoices = voices.filter(v => v.downloaded)
          if (savedVoice && downloadedVoices.some(v => v.name === savedVoice)) {
            setSelectedVoice(savedVoice)
          } else if (downloadedVoices.length > 0) {
            setSelectedVoice(downloadedVoices[0].name)
          }
        } else {
          // Cloud mode
          if (savedVoice && cloudVoices && cloudVoices.includes(savedVoice)) {
            setSelectedVoice(savedVoice)
          } else if (cloudVoices && cloudVoices.length > 0) {
            setSelectedVoice(cloudVoices[0])
          }
        }
      } catch (e) {
        console.log('Could not initialize TTS mode:', e)
      }
    }
    initTtsMode()
  }, [fetchTtsMode, fetchTtsAvailability, fetchLocalVoices, getTtsVoices, setTtsMode, setTtsAvailability, setLocalVoices, setTtsVoices, getAppState, applyTtsMode, setSelectedVoice])
  
  // Close model picker on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (modelPickerRef.current && !modelPickerRef.current.contains(event.target)) {
        setModelPickerOpen(false)
      }
      if (ttsPickerRef.current && !ttsPickerRef.current.contains(event.target)) {
        setTtsPickerOpen(false)
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
    setDownloadProgress(0)
    
    // Simulate smooth progress for better UX
    let simulatedProgress = 0
    const progressSimulator = setInterval(() => {
      simulatedProgress = Math.min(simulatedProgress + 2, 90)
      setDownloadProgress(prev => Math.max(prev, simulatedProgress))
    }, 100)
    
    try {
      await ttsDownload(editorContent, selectedVoice, (progress) => {
        setDownloadProgress(Math.max(progress, simulatedProgress))
      })
      setDownloadProgress(100)
    } finally {
      clearInterval(progressSimulator)
      // Keep progress visible briefly before resetting
      setTimeout(() => {
        setIsDownloading(false)
        setDownloadProgress(0)
      }, 500)
    }
  }
  
  // Handle back to dashboard
  const handleBackToDashboard = () => {
    setCurrentProject(null)
    setCurrentView('dashboard')
  }
  
  // Handle TTS mode switch
  const handleTtsModeSwitch = async (mode) => {
    const result = await applyTtsMode(mode)
    
    // Even if backend returns error (e.g., piper not installed), we still switch UI mode
    // to allow users to download voices in advance
    setTtsMode(mode)
    await saveAppState('tts_mode', mode)
    
    // Refresh local voices list if switching to local
    if (mode === 'local') {
      const voices = await fetchLocalVoices()
      setLocalVoices(voices)
      
      // Show helpful message if no voices downloaded yet
      const downloadedVoices = voices.filter(v => v.downloaded)
      if (downloadedVoices.length === 0) {
        addNotification({ 
          type: 'info', 
          message: 'Download a voice to use Local TTS. Click on any voice below to download.' 
        })
      }
      
      // Update selected voice to first available local voice
      if (downloadedVoices.length > 0) {
        setSelectedVoice(downloadedVoices[0].name)
        await saveAppState('selected_voice', downloadedVoices[0].name)
      }
    } else {
      // Switching to cloud mode - set to first cloud voice if available
      if (ttsVoices && ttsVoices.length > 0) {
        setSelectedVoice(ttsVoices[0])
        await saveAppState('selected_voice', ttsVoices[0])
      }
    }
    
    if (result?.warning) {
      addNotification({ type: 'warning', message: result.warning })
    }
  }
  
  // Handle local voice download
  const handleDownloadVoice = async (voiceName) => {
    if (isDownloadingVoice) return
    
    setIsDownloadingVoice(true)
    setVoiceDownloadProgress(0)
    
    const success = await downloadLocalVoice(voiceName, (progress) => {
      setVoiceDownloadProgress(progress)
    })
    
    if (success) {
      // Refresh local voices list
      const voices = await fetchLocalVoices()
      setLocalVoices(voices)
    }
    
    setIsDownloadingVoice(false)
    setVoiceDownloadProgress(0)
  }
  
  // Handle local voice delete
  const handleDeleteVoice = async (voiceName) => {
    const success = await deleteLocalVoice(voiceName)
    if (success) {
      const voices = await fetchLocalVoices()
      setLocalVoices(voices)
    }
  }
  
  // Get current voices based on mode
  const currentModeVoices = ttsMode === 'local' 
    ? localVoices.filter(v => v.downloaded).map(v => v.name)
    : ttsVoices
  
  return (
    <>
    <header className="h-toolbar flex items-center px-4 gap-4 glass drag-region overflow-visible">
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
      <div className="flex items-center gap-2 flex-1 justify-center no-drag min-w-0 overflow-visible">
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
          <MenuItem label="Expand" onClick={() => handleWrite('Expand')} />
          <MenuItem label="Guided Generation" onClick={handleGuidedGeneration} />
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
          <MenuItem icon={<LuLightbulb className={ic} />} label="Brainstorm" onClick={() => handleMoreTool('brainstorm')} />
          <MenuItem icon={<LuClapperboard className={ic} />} label="Visualize" onClick={() => handleMoreTool('visualize')} />
          <MenuItem icon={<LuShuffle className={ic} />} label="Twist" onClick={() => handleMoreTool('twist')} />
          <MenuItem icon={<LuScroll className={ic} />} label="Poem" onClick={() => handleMoreTool('poem')} />
          <hr className="my-2 border-gold-rich/10" />
          <MenuItem icon={<LuUpload className={ic} />} label="Export" onClick={() => {}} />
          <MenuItem icon={<LuSettings className={ic} />} label="Settings" onClick={() => {}} />
        </ToolbarButton>
      </div>
      
      {/* Right: Status & Controls */}
      <div className="flex items-center gap-3 no-drag shrink-0">
        {/* TTS Controls */}
        <div className="flex items-center gap-1 relative" ref={ttsPickerRef}>
          {/* TTS Mode Toggle */}
          <button
            className={clsx(
              'px-2 py-1.5 rounded-l-lg flex items-center gap-1.5 text-sm',
              'bg-dark-700 border border-gold-rich/20',
              'text-text-secondary hover:bg-gold-rich/10 hover:text-gold-rich',
              'transition-all duration-200',
              ttsPickerOpen && 'bg-gold-rich/10 border-gold-rich/40 text-gold-rich'
            )}
            onClick={() => setTtsPickerOpen(!ttsPickerOpen)}
            title={`TTS Mode: ${ttsMode === 'local' ? 'Local (Offline)' : 'Cloud'} - Click to manage`}
          >
            {ttsMode === 'local' ? (
              <LuHardDrive className="w-3.5 h-3.5" />
            ) : (
              <LuCloud className="w-3.5 h-3.5" />
            )}
            <span className="text-xs">▾</span>
          </button>
          
          {/* TTS Mode Picker Dropdown */}
          {ttsPickerOpen && (
            <div className="absolute right-0 top-full mt-1 w-72 rounded-xl bg-dark-800 border border-gold-rich/20 shadow-2xl py-2 z-50">
              {/* Header */}
              <div className="px-4 py-2 border-b border-gold-rich/10">
                <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                  <LuVolume2 className="w-4 h-4 text-gold-rich" />
                  Text-to-Speech Settings
                </div>
              </div>
              
              {/* Mode Selection */}
              <div className="px-4 py-3 border-b border-gold-rich/10">
                <div className="text-xs text-text-muted mb-2">TTS Mode</div>
                <div className="flex gap-2">
                  <button
                    className={clsx(
                      'flex-1 px-3 py-2 rounded-lg flex items-center justify-center gap-2 text-sm',
                      'border transition-all duration-200',
                      ttsMode === 'cloud'
                        ? 'bg-gold-rich/20 border-gold-rich/40 text-gold-rich'
                        : 'bg-dark-700 border-gold-rich/10 text-text-secondary hover:bg-gold-rich/10'
                    )}
                    onClick={() => handleTtsModeSwitch('cloud')}
                    disabled={!ttsAvailability?.cloud}
                    title={ttsAvailability?.cloud ? 'Use cloud TTS (requires internet)' : 'Cloud TTS not available'}
                  >
                    <LuCloud className="w-4 h-4" />
                    <span>Cloud</span>
                    {ttsMode === 'cloud' && <LuCheck className="w-3.5 h-3.5 text-green-400" />}
                  </button>
                  <button
                    className={clsx(
                      'flex-1 px-3 py-2 rounded-lg flex items-center justify-center gap-2 text-sm',
                      'border transition-all duration-200',
                      ttsMode === 'local'
                        ? 'bg-gold-rich/20 border-gold-rich/40 text-gold-rich'
                        : 'bg-dark-700 border-gold-rich/10 text-text-secondary hover:bg-gold-rich/10'
                    )}
                    onClick={() => handleTtsModeSwitch('local')}
                    title="Use local TTS (works offline)"
                  >
                    <LuHardDrive className="w-4 h-4" />
                    <span>Local</span>
                    {ttsMode === 'local' && <LuCheck className="w-3.5 h-3.5 text-green-400" />}
                  </button>
                </div>
                <p className="text-xs text-text-muted mt-2">
                  {ttsMode === 'cloud' 
                    ? 'Cloud: High quality, requires internet' 
                    : 'Local: Works offline, requires voice download'}
                </p>
                
                {/* Show warning if local TTS engine is not available */}
                {ttsMode === 'local' && !ttsAvailability?.local && (
                  <div className="mt-2 p-2 rounded-lg bg-amber-500/10 border border-amber-500/30">
                    <p className="text-xs text-amber-400">
                      Local TTS engine (Piper) is not installed. Voice downloads will still work, but playback requires the piper-tts package.
                    </p>
                  </div>
                )}
              </div>
              
              {/* Local Voices Section (show when local mode OR when user wants to download) */}
              {(ttsMode === 'local' || localVoices.length > 0) && ttsMode === 'local' && (
                <div className="py-2">
                  <div className="px-4 py-1.5 text-xs font-medium text-text-muted flex items-center justify-between">
                    <span>Local Voices</span>
                    {isDownloadingVoice && (
                      <span className="flex items-center gap-1 text-gold-rich">
                        <CgSpinner className="w-3 h-3 animate-spin" />
                        {voiceDownloadProgress}%
                      </span>
                    )}
                  </div>
                  
                  {localVoices.length === 0 ? (
                    <div className="px-4 py-3 text-center text-text-muted text-sm">
                      Loading voices...
                    </div>
                  ) : (
                    <div className="max-h-48 overflow-y-auto">
                      {localVoices.map((voice) => (
                        <div
                          key={voice.id}
                          className="px-4 py-2 flex items-center justify-between hover:bg-gold-rich/5"
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <LuVolume2 className={clsx(
                              'w-4 h-4 shrink-0',
                              voice.downloaded ? 'text-green-400' : 'text-text-muted'
                            )} />
                            <div className="min-w-0">
                              <div className={clsx(
                                'text-sm truncate',
                                voice.downloaded ? 'text-text-primary' : 'text-text-secondary'
                              )}>
                                {voice.name}
                              </div>
                              <div className="text-xs text-text-muted">
                                {voice.size_mb} MB
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-1 shrink-0">
                            {voice.downloaded ? (
                              <>
                                <LuCheck className="w-4 h-4 text-green-400" />
                                <button
                                  className="p-1 text-text-muted hover:text-red-400 transition-colors"
                                  onClick={() => handleDeleteVoice(voice.name)}
                                  title="Delete voice"
                                >
                                  <LuTrash2 className="w-3.5 h-3.5" />
                                </button>
                              </>
                            ) : (
                              <button
                                className={clsx(
                                  'px-2 py-1 text-xs rounded',
                                  'bg-gold-rich/20 text-gold-rich hover:bg-gold-rich/30',
                                  'transition-colors',
                                  isDownloadingVoice && 'opacity-50 cursor-not-allowed'
                                )}
                                onClick={() => handleDownloadVoice(voice.name)}
                                disabled={isDownloadingVoice}
                              >
                                Download
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
          
          {/* Voice Selector */}
          {currentModeVoices.length > 0 && (
            <select
              className="px-2 py-1.5 bg-dark-700 text-text-secondary text-sm border border-gold-rich/20 focus:outline-none focus:ring-1 focus:ring-gold-rich cursor-pointer max-w-[100px]"
              value={selectedVoice}
              onChange={(e) => {
                setSelectedVoice(e.target.value)
                saveAppState('selected_voice', e.target.value)
              }}
              title="Select Voice"
            >
              {currentModeVoices.map(voice => (
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
              'relative flex items-center justify-center overflow-hidden',
              'transition-all duration-200 rounded-r-lg',
              isDownloading
                ? 'bg-gold-rich/60 text-dark-950 cursor-wait px-8'
                : 'bg-dark-700 text-text-secondary border border-gold-rich/20 hover:bg-gold-rich/10 hover:text-gold-rich p-1.5'
            )}
            onClick={handleTtsDownload}
            disabled={isDownloading}
            title={isDownloading ? `Downloading: ${downloadProgress}%` : 'Download chapter as MP3 audio'}
          >
            {isDownloading ? (
              <>
                {/* Progress bar background */}
                <div 
                  className="absolute left-0 top-0 bottom-0 bg-gold-rich/30 transition-all duration-300"
                  style={{ width: `${downloadProgress}%` }}
                />
                {/* Content */}
                <div className="relative flex items-center gap-1.5">
                  <CgSpinner className={`${ic} animate-spin`} />
                  <span className="text-xs font-medium">{downloadProgress}%</span>
                </div>
              </>
            ) : (
              <LuDownload className={ic} />
            )}
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
    
    {/* Guided Generation Prompt Modal - Rendered outside header for proper centering */}
    {showGuidedPrompt && (
      <div 
        className="fixed inset-0 bg-black/60 flex items-center justify-center z-[10000]" 
        style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0 }}
        onClick={() => setShowGuidedPrompt(false)}
      >
        <div 
          className="bg-dark-800 border border-gold-rich/30 rounded-xl shadow-2xl w-full max-w-lg mx-4" 
          onClick={(e) => e.stopPropagation()}
        >
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gold-rich mb-2">Guided Generation</h3>
            <p className="text-sm text-text-muted mb-4">
              Describe what you want to write. The AI will use the context around your cursor position to generate relevant content.
            </p>
            <textarea
              className="w-full h-32 px-4 py-3 bg-dark-700 border border-gold-rich/20 rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-gold-rich/50 resize-none"
              placeholder="Example: Write a tense dialogue between the protagonist and antagonist where secrets are revealed..."
              value={guidedPrompt}
              onChange={(e) => setGuidedPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                  executeGuidedGeneration()
                }
              }}
              autoFocus
            />
            <div className="flex justify-end gap-3 mt-4">
              <button
                className="px-4 py-2 rounded-lg text-sm text-text-secondary hover:bg-dark-700 transition-colors"
                onClick={() => {
                  setShowGuidedPrompt(false)
                  setGuidedPrompt('')
                }}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 rounded-lg text-sm bg-gold-rich/20 text-gold-rich hover:bg-gold-rich/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={executeGuidedGeneration}
                disabled={!guidedPrompt.trim()}
              >
                Generate (Ctrl+Enter)
              </button>
            </div>
          </div>
        </div>
      </div>
    )}
  </>
  )
}

export default Toolbar
