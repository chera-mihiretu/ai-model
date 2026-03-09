/**
 * Story Bible Component
 * =====================
 * Displays Story Bible tabs (Braindump, Genre, Style, Synopsis, etc.)
 * Includes AI-powered generation from synopsis.
 * Dark & Gold luxury theme
 */

import { useState, useEffect, useRef } from 'react'
import useStore from '../hooks/useStore'
import { usePythonBridge } from '../hooks/usePythonBridge'
import { clsx } from 'clsx'

// Icons
const Icons = {
  BRAINDUMP: '📝',
  GENRE: '🎭',
  STYLE: '🎨',
  SYNOPSIS: '📖',
  WORLD: '🌍',
  OUTLINE: '📋',
  SAVE: '💾',
  AI: '🤖',
  EXPAND: '✨',
  CHARACTERS: '👥',
  GENERATE: '⚡',
  MAGIC: '🪄',
  CLOSE: '✕',
  DRAG: '⋮⋮',
  ARROW_EXPAND: '▶',
  ARROW_COLLAPSE: '▼',
  COPY: '📋',
  DELETE: '🗑️',
  EDIT: '✏️',
  MORE: '⋯',
  PLUS: '+',
  REWRITE: '🔄',
}

// Outline Chapter Row Component
function OutlineChapterRow({ chapter, index, onUpdate, onDelete, onDuplicate, onGenerate, isGeneratingThis }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [editData, setEditData] = useState(chapter)
  const [isDirty, setIsDirty] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const [customInstructions, setCustomInstructions] = useState('')
  const [showInstructions, setShowInstructions] = useState(false)
  const menuRef = useRef(null)
  const menuButtonRef = useRef(null)
  const [menuPosition, setMenuPosition] = useState({ top: 0, right: 0 })
  
  useEffect(() => {
    setEditData(chapter)
    setIsDirty(false)
  }, [chapter])
  
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  const handleChange = (field, value) => {
    setEditData(prev => ({ ...prev, [field]: value }))
    setIsDirty(true)
  }
  
  const handleSave = () => {
    if (isDirty) {
      onUpdate(index, editData)
      setIsDirty(false)
    }
  }
  
  const handleTitleBlur = () => {
    if (isDirty && editData.title?.trim()) {
      handleSave()
    }
  }
  
  return (
    <div className="bg-dark-800 rounded-xl border border-gold-rich/10 shadow-sm mb-3 overflow-hidden">
      {/* Collapsed Row: "Chapter N: Title" */}
      <div
        className="flex items-center gap-3 px-4 py-3 hover:bg-dark-750 transition-colors cursor-pointer group"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="text-gray-600 cursor-grab text-sm" onClick={(e) => e.stopPropagation()}>{Icons.DRAG}</span>
        
        <span className="text-gray-500 text-sm w-4 text-center flex-shrink-0">
          {isExpanded ? Icons.ARROW_COLLAPSE : Icons.ARROW_EXPAND}
        </span>
        
        {/* "Chapter N: Title" label */}
        <span className="font-medium text-gold-soft whitespace-nowrap flex-shrink-0">
          Chapter {chapter.chapter_number}:
        </span>
        <span className="text-gray-200 truncate flex-1">
          {editData.title || 'Untitled'}
        </span>
        
        {/* Summary preview when collapsed */}
        {!isExpanded && editData.summary && (
          <span className="text-xs text-gray-500 truncate max-w-[250px] hidden lg:inline">
            {editData.summary.slice(0, 80)}{editData.summary.length > 80 ? '...' : ''}
          </span>
        )}
        
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity" onClick={(e) => e.stopPropagation()}>
          <button
            className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-500 hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
            onClick={() => onDuplicate(index)}
            title="Duplicate"
          >
            {Icons.COPY}
          </button>
          
          <div className="relative" ref={menuRef}>
            <button
              ref={menuButtonRef}
              className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-500 hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
              onClick={() => {
                if (!showMenu && menuButtonRef.current) {
                  const rect = menuButtonRef.current.getBoundingClientRect()
                  setMenuPosition({ top: rect.bottom + 4, right: window.innerWidth - rect.right })
                }
                setShowMenu(!showMenu)
              }}
            >
              {Icons.MORE}
            </button>
            
            {showMenu && (
              <div 
                className="fixed bg-dark-800 rounded-xl shadow-lg border border-gold-rich/20 min-w-[140px] py-2 z-[9999]"
                style={{ top: menuPosition.top, right: menuPosition.right }}
              >
                <button
                  className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gold-rich/10 hover:text-gold-rich flex items-center gap-2"
                  onClick={() => { onDuplicate(index); setShowMenu(false) }}
                >
                  {Icons.COPY} Duplicate
                </button>
                <button
                  className="w-full px-4 py-2 text-left text-sm text-red-400 hover:bg-red-400/10 flex items-center gap-2"
                  onClick={() => { onDelete(index); setShowMenu(false) }}
                >
                  {Icons.DELETE} Delete
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Expanded: Title edit + Summary */}
      {isExpanded && (
        <div className="px-6 pb-5 bg-dark-850/50 animate-fade-in">
          {/* Chapter title edit */}
          <div className="mb-3">
            <label className="block text-xs font-medium text-gray-500 mb-1">Title</label>
            <input
              type="text"
              className="w-full px-3 py-2 text-sm bg-dark-750 border border-gold-rich/20 rounded-lg text-gold-soft placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gold-rich/30 font-medium"
              value={editData.title || ''}
              onChange={(e) => handleChange('title', e.target.value)}
              onBlur={handleTitleBlur}
              placeholder="Chapter title..."
            />
          </div>
          
          {/* Summary */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-medium text-gray-500">Summary</label>
              <button
                className="flex items-center gap-1 text-xs text-gray-400 hover:text-gold-rich border border-gold-rich/20 rounded-lg px-2 py-1 hover:bg-gold-rich/10 transition-colors"
                onClick={() => onGenerate(index, editData.title, customInstructions)}
                disabled={isGeneratingThis}
                title="Generate a summary for this chapter using AI"
              >
                {isGeneratingThis ? (
                  <><div className="spinner !w-3 !h-3" /> Generating...</>
                ) : (
                  <><span>{Icons.MAGIC}</span> Generate</>
                )}
              </button>
            </div>
            <textarea
              className="w-full px-3 py-3 text-sm bg-dark-750 border border-gold-rich/20 rounded-lg text-gray-200 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gold-rich/30 min-h-[140px] resize-y"
              value={editData.summary || ''}
              onChange={(e) => handleChange('summary', e.target.value)}
              onBlur={handleSave}
              placeholder="Detailed summary of everything this chapter contains: opening scene, plot events, character actions, conflicts, and how it ends..."
            />
            
            {/* Rewrite + Custom Instructions row */}
            <div className="flex items-center justify-between mt-1">
              {editData.summary?.trim() ? (
                <button
                  className="flex items-center gap-1 text-xs text-gray-400 hover:text-gold-rich border border-gold-rich/20 rounded-lg px-2 py-1 hover:bg-gold-rich/10 transition-colors"
                  onClick={() => onGenerate(index, editData.title, customInstructions)}
                  disabled={isGeneratingThis}
                  title="Rewrite this chapter summary using AI"
                >
                  {isGeneratingThis ? (
                    <><div className="spinner !w-3 !h-3" /> Rewriting...</>
                  ) : (
                    <><span>{Icons.REWRITE}</span> Rewrite</>
                  )}
                </button>
              ) : <span />}
              <button
                className="text-xs text-gray-500 hover:text-gray-400 transition-colors"
                onClick={() => setShowInstructions(!showInstructions)}
              >
                {showInstructions ? '▼ Hide custom instructions' : '▶ Custom instructions (optional)'}
              </button>
            </div>
            {showInstructions && (
              <input
                type="text"
                className="w-full mt-1 px-3 py-2 text-xs bg-dark-750 border border-gold-rich/15 rounded-lg text-gray-300 placeholder:text-gray-600 focus:outline-none focus:ring-1 focus:ring-gold-rich/20"
                value={customInstructions}
                onChange={(e) => setCustomInstructions(e.target.value)}
                placeholder='e.g. "Add a subplot about trust" or "End in a cliffhanger"'
              />
            )}
          </div>
          
          {isDirty && (
            <div className="mt-3 flex items-center justify-end gap-2">
              <span className="text-xs text-gray-500">Unsaved changes</span>
              <button
                className="px-3 py-1.5 text-sm bg-gradient-to-r from-gold-rich to-gold-deep text-dark-950 rounded-lg hover:from-gold-amber hover:to-gold-rich font-medium"
                onClick={handleSave}
              >
                Save
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Outline Editor with Expandable Chapter Rows
function OutlineEditor({ chapters, onSave, onGenerateFromSynopsis, onGenerateFromContext, isGenerating, generatingAction, hasSynopsis, hasSource, storyBibleData, addNotification }) {
  const [outlineChapters, setOutlineChapters] = useState([])
  const [generatingChapterIdx, setGeneratingChapterIdx] = useState(null)
  
  useEffect(() => {
    if (typeof chapters === 'string') {
      try {
        const parsed = JSON.parse(chapters)
        setOutlineChapters(Array.isArray(parsed) ? parsed : [])
      } catch {
        setOutlineChapters([])
      }
    } else if (Array.isArray(chapters)) {
      setOutlineChapters(chapters)
    } else {
      setOutlineChapters([])
    }
  }, [chapters])
  
  const handleUpdateChapter = (index, updatedChapter) => {
    const newChapters = [...outlineChapters]
    newChapters[index] = updatedChapter
    setOutlineChapters(newChapters)
    onSave(JSON.stringify(newChapters))
  }
  
  const handleDeleteChapter = (index) => {
    if (confirm('Delete this chapter from the outline?')) {
      const newChapters = outlineChapters.filter((_, i) => i !== index)
      newChapters.forEach((ch, i) => ch.chapter_number = i + 1)
      setOutlineChapters(newChapters)
      onSave(JSON.stringify(newChapters))
    }
  }
  
  const handleDuplicateChapter = (index) => {
    const chapterToCopy = outlineChapters[index]
    const newChapter = {
      ...chapterToCopy,
      title: `${chapterToCopy.title} (Copy)`,
      chapter_number: outlineChapters.length + 1
    }
    const newChapters = [...outlineChapters, newChapter]
    setOutlineChapters(newChapters)
    onSave(JSON.stringify(newChapters))
  }
  
  const handleAddChapter = () => {
    const newChapter = {
      chapter_number: outlineChapters.length + 1,
      title: '',
      summary: ''
    }
    const newChapters = [...outlineChapters, newChapter]
    setOutlineChapters(newChapters)
    onSave(JSON.stringify(newChapters))
  }
  
  const handleGenerateChapterSummary = async (index, title, customInstructions) => {
    const sourceContent = storyBibleData?.['synopsis']?.trim() || storyBibleData?.['braindump']?.trim()
    if (!sourceContent) {
      addNotification?.({ type: 'warning', message: 'Please write a Synopsis or Braindump first.' })
      return
    }
    
    const genre = storyBibleData?.['genre'] || 'fiction'
    
    const outlineSummary = outlineChapters
      .filter((_, i) => i !== index)
      .map(ch => `Chapter ${ch.chapter_number}: ${ch.title} - ${(ch.summary || '').slice(0, 120)}`)
      .join('\n')
    
    setGeneratingChapterIdx(index)
    try {
      const result = await window.api.generateChapterSummary(
        outlineChapters[index].chapter_number,
        title || `Chapter ${index + 1}`,
        sourceContent,
        genre,
        customInstructions || '',
        outlineSummary
      )
      
      if (result && result.summary) {
        const updated = { ...outlineChapters[index], summary: result.summary }
        handleUpdateChapter(index, updated)
        addNotification?.({ type: 'success', message: `Chapter ${outlineChapters[index].chapter_number} summary generated.` })
      } else {
        addNotification?.({ type: 'error', message: result?.error || 'Failed to generate chapter summary.' })
      }
    } catch (error) {
      console.error('Generate chapter summary error:', error)
      addNotification?.({ type: 'error', message: `Failed: ${error.message}` })
    } finally {
      setGeneratingChapterIdx(null)
    }
  }
  
  const isOutlineGenerating = isGenerating && (generatingAction === 'outline' || generatingAction === 'generate_section')
  
  return (
    <div className="h-full flex flex-col">
      <div className="bg-dark-800 rounded-xl shadow-sm border border-gold-rich/10 mb-4">
        {/* Header */}
        <div className="px-5 py-4 border-b border-gold-rich/10">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{Icons.OUTLINE}</span>
              <div>
                <h1 className="text-xl font-semibold text-gold-soft">Story Outline</h1>
                <p className="text-sm text-gray-400">
                  {outlineChapters.length} chapter{outlineChapters.length !== 1 ? 's' : ''} planned
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              {hasSource && (
                <button
                  className="flex items-center gap-1.5 text-gray-400 hover:text-gold-rich font-medium text-sm border border-gold-rich/20 rounded-lg px-3 py-1.5 hover:bg-gold-rich/10 transition-colors"
                  onClick={hasSynopsis ? onGenerateFromSynopsis : onGenerateFromContext}
                  disabled={isGenerating}
                  title={hasSynopsis ? 'Generate entire outline from Synopsis' : 'Generate entire outline from Braindump'}
                >
                  {isOutlineGenerating ? (
                    <><div className="spinner !w-3 !h-3" /> Generating...</>
                  ) : (
                    <><span>🤖</span> Generate Outline</>
                  )}
                </button>
              )}
              <button
                className="flex items-center gap-1.5 text-gold-rich hover:text-gold-amber font-medium text-sm border border-gold-rich/30 rounded-lg px-3 py-1.5 hover:bg-gold-rich/10 transition-colors"
                onClick={handleAddChapter}
              >
                <span>+</span> Add Chapter
              </button>
            </div>
          </div>
          {!hasSource && (
            <p className="text-xs text-amber-200/70 mt-1">
              To generate an outline with AI, first write a Synopsis or Braindump.
            </p>
          )}
        </div>
        
        {/* Chapters List */}
        <div className="p-4 max-h-[calc(100vh-350px)] overflow-y-auto">
          {outlineChapters.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-5xl mb-4 opacity-50">{Icons.OUTLINE}</div>
              <h2 className="text-lg font-semibold text-gray-200 mb-2">No Chapters Yet</h2>
              <p className="text-gray-400 mb-2 text-sm max-w-md mx-auto">
                The Outline is where you define the structure of your story. Each chapter has a summary capturing what happens in that part.
              </p>
              <p className="text-gray-500 mb-6 text-xs max-w-md mx-auto">
                Use "Generate Outline" to create the entire outline at once, or add chapters manually one at a time.
              </p>
              <div className="flex items-center justify-center gap-3">
                {hasSource && (
                  <button
                    className="px-4 py-2 rounded-lg bg-dark-700 text-gray-300 hover:bg-dark-600 text-sm font-medium flex items-center gap-2 border border-gold-rich/20"
                    onClick={hasSynopsis ? onGenerateFromSynopsis : onGenerateFromContext}
                    disabled={isGenerating}
                  >
                    🤖 Generate Outline
                  </button>
                )}
                <button
                  className="px-4 py-2 rounded-lg bg-gradient-to-r from-gold-rich to-gold-deep text-dark-950 hover:from-gold-amber hover:to-gold-rich text-sm font-medium flex items-center gap-2"
                  onClick={handleAddChapter}
                >
                  + Add Chapter
                </button>
              </div>
            </div>
          ) : (
            outlineChapters.map((chapter, index) => (
              <OutlineChapterRow
                key={index}
                chapter={chapter}
                index={index}
                onUpdate={handleUpdateChapter}
                onDelete={handleDeleteChapter}
                onDuplicate={handleDuplicateChapter}
                onGenerate={handleGenerateChapterSummary}
                isGeneratingThis={generatingChapterIdx === index}
              />
            ))
          )}
        </div>
      </div>
    </div>
  )
}

// Tab configuration with hierarchical dependency metadata
const TABS = [
  { 
    id: 'braindump', 
    label: 'Braindump', 
    icon: Icons.BRAINDUMP,
    placeholder: 'Write a braindump of everything you know about the story. You can include information about plot, characters, worldbuilding, theme - anything!',
    description: 'Write a braindump of everything you know about the story. You can include information about plot, characters, worldbuilding, theme - anything!',
    affects: 'Synopsis',
    wordLimit: 4000,
    aiGenerate: false,
    requires: [],
  },
  { 
    id: 'genre', 
    label: 'Genre', 
    icon: Icons.GENRE,
    placeholder: 'Romance, Horror, Fantasy, Cozy mystery, Friends-to-Lovers, Gumshoe...',
    description: 'What genre are you writing in? Feel free to include sub-genres and tropes.',
    affects: 'Synopsis, Outline, Scenes, and Draft',
    wordLimit: 40,
    aiGenerate: false,
    requires: [],
  },
  { 
    id: 'style', 
    label: 'Style', 
    icon: Icons.STYLE,
    placeholder: 'Describe your writing style, tone, POV, tense preferences... e.g. "moody and atmospheric, written in short, sharp sentences"',
    description: 'Define your writing style, tone, and voice. You can type a description or paste a writing sample.',
    affects: 'Scenes and Draft',
    aiGenerate: false,
    requires: [],
  },
  { 
    id: 'synopsis', 
    label: 'Synopsis', 
    icon: Icons.SYNOPSIS,
    placeholder: 'Introduce the characters, their goals, and the central conflict, while conveying the story\'s tone, themes, and unique elements.',
    description: 'Introduce the characters, their goals, and the central conflict, while conveying the story\'s tone, themes, and unique elements.',
    affects: 'Characters, Worldbuilding, Outline, and Scenes',
    wordLimit: 4000,
    aiGenerate: true,
    requires: ['braindump'],
  },
  { 
    id: 'outline', 
    label: 'Outline', 
    icon: Icons.OUTLINE,
    placeholder: 'Structure your story... chapters, scenes, plot beats...',
    description: 'Plan your story structure and major plot points.',
    affects: 'Scenes',
    aiGenerate: true,
    requires: ['synopsis', 'braindump'],
  },
]

// Dependency check: returns { canGenerate, missingMessage } for a given tab
function checkDependencies(tabId, storyBibleData) {
  const tab = TABS.find(t => t.id === tabId)
  if (!tab || !tab.aiGenerate) return { canGenerate: false, missingMessage: '' }
  
  if (tabId === 'synopsis') {
    const hasBraindump = storyBibleData['braindump']?.trim()
    if (!hasBraindump) {
      return { canGenerate: false, missingMessage: 'To generate your Synopsis with AI, first write your Braindump with your story ideas.' }
    }
    return { canGenerate: true, missingMessage: '' }
  }
  
  if (tabId === 'outline') {
    const hasSynopsis = storyBibleData['synopsis']?.trim()
    const hasBraindump = storyBibleData['braindump']?.trim()
    if (!hasSynopsis && !hasBraindump) {
      return { canGenerate: false, missingMessage: 'To generate your Outline with AI, first write a Synopsis or Braindump.' }
    }
    return { canGenerate: true, missingMessage: '' }
  }
  
  return { canGenerate: true, missingMessage: '' }
}

function StoryBible() {
  const {
    storyBibleData,
    currentBibleTab,
    currentProjectId,
    setCurrentBibleTab,
    updateBibleField,
    addNotification,
    setCharacters,
  } = useStore()
  
  const {
    saveBibleField,
    getStoryBible,
    generatePluginResponse,
    isElectronApi,
    saveCharacter,
    getCharacters,
    createWorldElement,
  } = usePythonBridge()
  
  const [isSaving, setIsSaving] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatingAction, setGeneratingAction] = useState('')
  const saveTimeoutRef = useRef(null)
  
  const currentTab = TABS.find(t => t.id === currentBibleTab) || TABS[0]
  const content = storyBibleData[currentBibleTab] || ''
  const synopsisContent = storyBibleData['synopsis'] || ''
  const braindumpContent = storyBibleData['braindump'] || ''
  const genreContent = storyBibleData['genre'] || 'fiction'
  
  const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0
  const { canGenerate, missingMessage } = checkDependencies(currentBibleTab, storyBibleData)
  
  useEffect(() => {
    async function loadBibleData() {
      if (!currentProjectId) return
      const data = await getStoryBible(currentProjectId)
      if (data) {
        Object.keys(data).forEach(key => {
          updateBibleField(key, data[key])
        })
      }
    }
    loadBibleData()
  }, [currentProjectId])
  
  const handleContentChange = (value) => {
    updateBibleField(currentBibleTab, value)
    
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current)
    }
    
    saveTimeoutRef.current = setTimeout(async () => {
      setIsSaving(true)
      await saveBibleField(currentProjectId, currentBibleTab, value)
      setIsSaving(false)
    }, 1000)
  }
  
  const handleAiExpand = async () => {
    if (!content.trim()) return
    
    setIsGenerating(true)
    setGeneratingAction('expand')
    try {
      const expanded = await generatePluginResponse(
        content,
        'expand_scene',
        { genre: genreContent }
      )
      if (expanded) {
        handleContentChange(content + '\n\n' + expanded)
      }
    } finally {
      setIsGenerating(false)
      setGeneratingAction('')
    }
  }
  
  const handleGenerateSection = async () => {
    if (!isElectronApi) {
      addNotification({ type: 'warning', message: 'AI generation requires the Python backend' })
      return
    }
    
    if (!currentProjectId) {
      addNotification({ type: 'warning', message: 'Please select a project first' })
      return
    }
    
    if (!canGenerate) {
      addNotification({ type: 'warning', message: missingMessage })
      return
    }
    
    setIsGenerating(true)
    setGeneratingAction('generate_section')
    
    try {
      const result = await window.api.generateBibleSection(currentBibleTab, currentProjectId)
      
      if (result && !result.error) {
        handleContentChange(result)
        addNotification({ type: 'success', message: `${currentTab.label} generated successfully!` })
      } else {
        addNotification({ type: 'error', message: result?.error || `Failed to generate ${currentTab.label.toLowerCase()}` })
      }
    } catch (error) {
      console.error('Generate section error:', error)
      addNotification({ type: 'error', message: `Failed to generate ${currentTab.label.toLowerCase()}: ${error.message}` })
    } finally {
      setIsGenerating(false)
      setGeneratingAction('')
    }
  }
  
  const handleGenerateCast = async () => {
    const sourceContent = synopsisContent.trim() || braindumpContent.trim()
    if (!sourceContent) {
      addNotification({ type: 'warning', message: 'Please write a Synopsis or Braindump first to generate characters.' })
      return
    }
    
    if (!isElectronApi) {
      addNotification({ type: 'warning', message: 'AI generation requires the Python backend' })
      return
    }
    
    setIsGenerating(true)
    setGeneratingAction('characters')
    
    try {
      const result = await window.api.generateCharactersFromSynopsis(sourceContent, genreContent)
      
      if (result && result.length > 0) {
        let savedCount = 0
        let errors = []
        
        for (const char of result) {
          try {
            await saveCharacter({ ...char, project_id: currentProjectId })
            savedCount++
          } catch (saveError) {
            console.error('Save character error:', saveError)
            errors.push(char.name || 'Unknown')
          }
        }
        
        const chars = await getCharacters(currentProjectId)
        setCharacters(chars)
        
        if (savedCount > 0) {
          addNotification({ type: 'success', message: `Generated and saved ${savedCount} characters from synopsis` })
        }
        if (errors.length > 0) {
          addNotification({ type: 'warning', message: `Failed to save: ${errors.join(', ')}` })
        }
      } else {
        addNotification({ type: 'warning', message: 'No characters could be extracted from the synopsis' })
      }
    } catch (error) {
      console.error('Generate cast error:', error)
      addNotification({ type: 'error', message: `Failed to generate characters: ${error.message}` })
    } finally {
      setIsGenerating(false)
      setGeneratingAction('')
    }
  }
  
  const handleGenerateWorld = async () => {
    const sourceContent = synopsisContent.trim() || braindumpContent.trim()
    if (!sourceContent) {
      addNotification({ type: 'warning', message: 'Please write a Synopsis or Braindump first to generate world elements.' })
      return
    }
    
    if (!isElectronApi) {
      addNotification({ type: 'warning', message: 'AI generation requires the Python backend' })
      return
    }
    
    setIsGenerating(true)
    setGeneratingAction('world')
    
    try {
      const result = await window.api.generateWorldFromSynopsis(sourceContent, genreContent)
      
      if (result && result.length > 0) {
        for (const elem of result) {
          await createWorldElement(currentProjectId, elem)
        }
        
        addNotification({ type: 'success', message: `Generated ${result.length} world elements from synopsis` })
      } else {
        addNotification({ type: 'warning', message: 'No world elements could be extracted from the synopsis' })
      }
    } catch (error) {
      console.error('Generate world error:', error)
      addNotification({ type: 'error', message: 'Failed to generate world elements' })
    } finally {
      setIsGenerating(false)
      setGeneratingAction('')
    }
  }
  
  const handleGenerateOutline = async () => {
    const sourceContent = synopsisContent.trim() || braindumpContent.trim()
    if (!sourceContent) {
      addNotification({ type: 'warning', message: 'Please write a Synopsis or Braindump first to generate an outline.' })
      return
    }
    
    if (!isElectronApi) {
      addNotification({ type: 'warning', message: 'AI generation requires the Python backend' })
      return
    }
    
    setIsGenerating(true)
    setGeneratingAction('outline')
    
    try {
      const result = await window.api.generateOutlineFromSynopsis(sourceContent, 10, genreContent)
      
      if (result && (Array.isArray(result) ? result.length > 0 : result)) {
        const outlineData = Array.isArray(result) ? JSON.stringify(result) : result
        
        updateBibleField('outline', outlineData)
        await saveBibleField(currentProjectId, 'outline', outlineData)
        
        const chapterCount = Array.isArray(result) ? result.length : 'unknown'
        addNotification({ type: 'success', message: `Generated ${chapterCount} chapter outline from synopsis` })
        
        setCurrentBibleTab('outline')
      } else {
        addNotification({ type: 'warning', message: 'Could not generate outline' })
      }
    } catch (error) {
      console.error('Generate outline error:', error)
      addNotification({ type: 'error', message: 'Failed to generate outline' })
    } finally {
      setIsGenerating(false)
      setGeneratingAction('')
    }
  }
  
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }
    }
  }, [])
  
  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-semibold text-gold-soft flex items-center gap-2">
            <span>{currentTab.icon}</span>
            <span>{currentTab.label}</span>
          </h1>
          <p className="text-gray-400 mt-1">{currentTab.description}</p>
          {currentTab.affects && (
            <p className="text-sm text-gold-rich/70 mt-1">
              This section affects: {currentTab.affects}
            </p>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {/* Save Status */}
          <div className={clsx(
            'px-3 py-1.5 rounded-lg text-sm',
            isSaving
              ? 'bg-gold-rich/20 text-gold-rich'
              : 'bg-green-500/20 text-green-400'
          )}>
            {isSaving ? 'Saving...' : '✓ Saved'}
          </div>
          
          {/* AI Generate Button - for synopsis tab */}
          {currentBibleTab === 'synopsis' && (
            <button
              className="btn btn-secondary"
              onClick={handleGenerateSection}
              disabled={isGenerating || !canGenerate}
              title={canGenerate ? 'Generate synopsis from your Braindump and Genre' : missingMessage}
            >
              {isGenerating && generatingAction === 'generate_section' ? (
                <>
                  <div className="spinner !w-4 !h-4" />
                  <span>Generating...</span>
                </>
              ) : (
                <>
                  <span>{Icons.MAGIC}</span>
                  <span>AI Generate</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
      
      {/* Inline Guidance Banner - shows when AI generation is available but dependencies are missing */}
      {currentTab.aiGenerate && !canGenerate && (
        <div className="mb-4 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚠️</span>
            <p className="text-sm text-amber-200/90">{missingMessage}</p>
          </div>
        </div>
      )}
      
      {/* Synopsis Generation Buttons - shows when synopsis has content */}
      {currentBibleTab === 'synopsis' && synopsisContent.trim() && (
        <div className="flex items-center gap-2 mb-4 p-3 rounded-xl bg-gold-rich/10 border border-gold-rich/20">
          <span className="text-sm text-gray-400 mr-2">{Icons.GENERATE} Generate from Synopsis:</span>
          
          <button
            className="btn btn-secondary text-sm py-1.5"
            onClick={handleGenerateCast}
            disabled={isGenerating}
            title="Generate character profiles from synopsis"
          >
            {isGenerating && generatingAction === 'characters' ? (
              <>
                <div className="spinner !w-3 !h-3" />
                <span>Generating...</span>
              </>
            ) : (
              <>
                <span>{Icons.CHARACTERS}</span>
                <span>Cast</span>
              </>
            )}
          </button>
          
          <button
            className="btn btn-secondary text-sm py-1.5"
            onClick={handleGenerateWorld}
            disabled={isGenerating}
            title="Generate world building elements from synopsis"
          >
            {isGenerating && generatingAction === 'world' ? (
              <>
                <div className="spinner !w-3 !h-3" />
                <span>Generating...</span>
              </>
            ) : (
              <>
                <span>{Icons.WORLD}</span>
                <span>World</span>
              </>
            )}
          </button>
          
          <button
            className="btn btn-secondary text-sm py-1.5"
            onClick={handleGenerateOutline}
            disabled={isGenerating}
            title="Generate chapter outline from synopsis"
          >
            {isGenerating && generatingAction === 'outline' ? (
              <>
                <div className="spinner !w-3 !h-3" />
                <span>Generating...</span>
              </>
            ) : (
              <>
                <span>{Icons.OUTLINE}</span>
                <span>Outline</span>
              </>
            )}
          </button>
        </div>
      )}
      
      {/* Tabs */}
      <div className="flex items-center gap-2 mb-4 overflow-x-auto pb-2">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all',
              currentBibleTab === tab.id
                ? 'bg-gradient-to-r from-gold-rich to-gold-deep text-dark-950'
                : 'bg-dark-700 text-gray-400 hover:bg-dark-600 hover:text-gray-200'
            )}
            onClick={() => setCurrentBibleTab(tab.id)}
          >
            <span className="mr-2">{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>
      
      {/* Content Area */}
      <div className="flex-1 overflow-hidden">
        {currentBibleTab === 'outline' ? (
          <OutlineEditor
            chapters={content}
            onSave={(data) => handleContentChange(data)}
            onGenerateFromSynopsis={handleGenerateOutline}
            onGenerateFromContext={handleGenerateSection}
            isGenerating={isGenerating}
            generatingAction={generatingAction}
            hasSynopsis={!!synopsisContent.trim()}
            hasSource={!!(synopsisContent.trim() || braindumpContent.trim())}
            storyBibleData={storyBibleData}
            addNotification={addNotification}
          />
        ) : (
          <textarea
            className="w-full h-full px-4 py-4 bg-dark-800 border border-gold-rich/10 rounded-xl text-gray-200 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gold-rich/30 focus:border-gold-rich/30 resize-none"
            value={content}
            onChange={(e) => handleContentChange(e.target.value)}
            placeholder={currentTab.placeholder}
          />
        )}
      </div>
      
      {/* Word Count with optional limit */}
      {currentBibleTab !== 'outline' && (
        <div className="mt-4 text-sm text-gray-500 text-right">
          {wordCount}{currentTab.wordLimit ? ` / ${currentTab.wordLimit}` : ''} words
        </div>
      )}
      
    </div>
  )
}

export default StoryBible
