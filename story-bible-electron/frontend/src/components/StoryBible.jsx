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
}

// Synopsis generation questions
const SYNOPSIS_QUESTIONS = [
  { id: 'protagonist', label: 'Main Character / Protagonist', placeholder: 'Who is your main character? What do they want?', required: true },
  { id: 'setting', label: 'Setting / World', placeholder: 'Where and when does the story take place?' },
  { id: 'conflict', label: 'Main Conflict', placeholder: 'What is the central problem or challenge?', required: true },
  { id: 'stakes', label: 'Stakes', placeholder: 'What happens if the protagonist fails?' },
  { id: 'antagonist', label: 'Antagonist / Opposition', placeholder: 'Who or what stands in the way?' },
  { id: 'journey', label: 'Key Plot Points', placeholder: 'What major events happen? What challenges do they face?' },
  { id: 'climax', label: 'Climax', placeholder: 'What is the big confrontation or turning point?' },
  { id: 'resolution', label: 'Resolution / Ending', placeholder: 'How does the story end? What changes?' },
  { id: 'theme', label: 'Theme / Message', placeholder: 'What deeper meaning or theme does the story explore?' },
]

// Synopsis Generation Modal
function GenerateSynopsisModal({ isOpen, onClose, onGenerate, isGenerating, genre }) {
  const [answers, setAnswers] = useState({})
  const [selectedGenre, setSelectedGenre] = useState(genre || 'fiction')
  const [wordCount, setWordCount] = useState('medium')
  
  const genres = ['Fiction', 'Fantasy', 'Sci-Fi', 'Romance', 'Thriller', 'Mystery', 'Horror', 'Historical', 'Literary', 'Young Adult']
  const wordCounts = [
    { id: 'short', label: 'Short (100-200 words)' },
    { id: 'medium', label: 'Medium (300-500 words)' },
    { id: 'long', label: 'Long (600-800 words)' },
  ]
  
  const handleChange = (questionId, value) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }))
  }
  
  const handleSubmit = () => {
    const hasProtagonist = answers.protagonist?.trim()
    const hasConflict = answers.conflict?.trim()
    
    if (!hasProtagonist || !hasConflict) {
      return
    }
    
    onGenerate(answers, selectedGenre, wordCount)
  }
  
  useEffect(() => {
    if (!isOpen) {
      setAnswers({})
      setSelectedGenre(genre || 'fiction')
      setWordCount('medium')
    }
  }, [isOpen, genre])
  
  if (!isOpen) return null
  
  const hasRequiredFields = answers.protagonist?.trim() && answers.conflict?.trim()
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div 
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={!isGenerating ? onClose : undefined}
      />
      
      <div className="relative z-10 w-full max-w-3xl mx-4 glass-card p-6 animate-slide-up max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{Icons.MAGIC}</span>
            <div>
              <h2 className="text-xl font-bold text-gray-100">Generate Synopsis with AI</h2>
              <p className="text-sm text-gray-400">Answer a few questions and AI will create your synopsis</p>
            </div>
          </div>
          {!isGenerating && (
            <button
              className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gold-rich/10 text-gray-500 hover:text-gold-rich transition-colors"
              onClick={onClose}
            >
              {Icons.CLOSE}
            </button>
          )}
        </div>
        
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gold-pale mb-2">
              Story Genre
            </label>
            <select
              className="input"
              value={selectedGenre}
              onChange={(e) => setSelectedGenre(e.target.value)}
              disabled={isGenerating}
            >
              {genres.map(g => (
                <option key={g} value={g.toLowerCase()}>{g}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gold-pale mb-2">
              Synopsis Length
            </label>
            <select
              className="input"
              value={wordCount}
              onChange={(e) => setWordCount(e.target.value)}
              disabled={isGenerating}
            >
              {wordCounts.map(wc => (
                <option key={wc.id} value={wc.id}>{wc.label}</option>
              ))}
            </select>
          </div>
        </div>
        
        <div className="space-y-4 mb-6">
          {SYNOPSIS_QUESTIONS.map(question => (
            <div key={question.id}>
              <label className="block text-sm font-medium text-gold-pale mb-1">
                {question.label}
                {question.required && <span className="text-red-400 ml-1">*</span>}
              </label>
              <textarea
                className="input-textarea min-h-[80px]"
                placeholder={question.placeholder}
                value={answers[question.id] || ''}
                onChange={(e) => handleChange(question.id, e.target.value)}
                disabled={isGenerating}
              />
            </div>
          ))}
        </div>
        
        <div className="mb-6 p-3 rounded-lg bg-gold-rich/10 border border-gold-rich/20">
          <p className="text-sm text-gray-300">
            <span className="text-gold-rich font-medium">💡 Tip:</span> The more detail you provide, the better your synopsis will be. 
            At minimum, fill in the protagonist and main conflict.
          </p>
        </div>
        
        <div className="flex items-center justify-end gap-3">
          <button
            type="button"
            className="btn btn-ghost"
            onClick={onClose}
            disabled={isGenerating}
          >
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-primary min-w-[180px]"
            onClick={handleSubmit}
            disabled={!hasRequiredFields || isGenerating}
          >
            {isGenerating ? (
              <>
                <div className="spinner !w-4 !h-4" />
                <span>Generating...</span>
              </>
            ) : (
              <>
                <span>{Icons.MAGIC}</span>
                <span>Generate Synopsis</span>
              </>
            )}
          </button>
        </div>
        
        {isGenerating && (
          <div className="mt-6 p-4 rounded-lg bg-gold-rich/10 border border-gold-rich/30">
            <div className="flex items-center gap-3">
              <div className="spinner !w-6 !h-6" />
              <div>
                <p className="text-gold-rich font-medium">Creating your synopsis...</p>
                <p className="text-sm text-gray-400">AI is weaving your story elements together. This may take 20-30 seconds.</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Outline Chapter Row Component - Similar to Character/World rows
function OutlineChapterRow({ chapter, index, onUpdate, onDelete, onDuplicate }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [editData, setEditData] = useState(chapter)
  const [isDirty, setIsDirty] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
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
      {/* Main Row */}
      <div className="flex items-center gap-3 px-4 py-3 hover:bg-dark-750 transition-colors group">
        {/* Drag Handle */}
        <span className="text-gray-600 cursor-grab text-sm">{Icons.DRAG}</span>
        
        {/* Expand Arrow */}
        <button
          className="w-5 h-5 flex items-center justify-center text-gray-500 hover:text-gold-rich transition-colors"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? Icons.ARROW_COLLAPSE : Icons.ARROW_EXPAND}
        </button>
        
        {/* Chapter Number Badge */}
        <span className="w-8 h-8 rounded-lg bg-gold-rich/20 text-gold-rich flex items-center justify-center font-bold text-sm flex-shrink-0">
          {chapter.chapter_number}
        </span>
        
        {/* Chapter Title - Editable */}
        <input
          type="text"
          className="flex-1 font-medium text-gold-soft bg-transparent border-none focus:outline-none focus:ring-0 hover:bg-dark-700 focus:bg-dark-700 px-2 py-1 rounded"
          value={editData.title || ''}
          onChange={(e) => handleChange('title', e.target.value)}
          onBlur={handleTitleBlur}
          placeholder="Chapter title..."
        />
        
        {/* Action Icons */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-500 hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
            onClick={() => setIsExpanded(!isExpanded)}
            title="Edit"
          >
            {Icons.EDIT}
          </button>
          
          <button
            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-500 hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
            onClick={() => onDuplicate(index)}
            title="Duplicate"
          >
            {Icons.COPY}
          </button>
          
          <div className="relative" ref={menuRef}>
            <button
              ref={menuButtonRef}
              className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-500 hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
              onClick={() => {
                if (!showMenu && menuButtonRef.current) {
                  const rect = menuButtonRef.current.getBoundingClientRect()
                  setMenuPosition({
                    top: rect.bottom + 4,
                    right: window.innerWidth - rect.right
                  })
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
                  onClick={() => {
                    onDuplicate(index)
                    setShowMenu(false)
                  }}
                >
                  {Icons.COPY} Duplicate
                </button>
                <button
                  className="w-full px-4 py-2 text-left text-sm text-red-400 hover:bg-red-400/10 flex items-center gap-2"
                  onClick={() => {
                    onDelete(index)
                    setShowMenu(false)
                  }}
                >
                  {Icons.DELETE} Delete
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-12 pb-6 bg-dark-850/50 animate-fade-in">
          <div className="space-y-4">
            {/* Summary */}
            <div>
              <label className="block text-sm font-medium text-gold-pale mb-2">Summary</label>
              <textarea
                className="w-full px-3 py-3 text-sm bg-dark-750 border border-gold-rich/20 rounded-lg text-gray-200 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gold-rich/30 min-h-[100px] resize-none"
                value={editData.summary || ''}
                onChange={(e) => handleChange('summary', e.target.value)}
                onBlur={handleSave}
                placeholder="What happens in this chapter..."
              />
            </div>
            
            {/* Key Events */}
            <div>
              <label className="block text-sm font-medium text-gold-pale mb-2">Key Events</label>
              <textarea
                className="w-full px-3 py-3 text-sm bg-dark-750 border border-gold-rich/20 rounded-lg text-gray-200 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gold-rich/30 min-h-[80px] resize-none"
                value={editData.key_events || ''}
                onChange={(e) => handleChange('key_events', e.target.value)}
                onBlur={handleSave}
                placeholder="Important plot points, reveals, character moments..."
              />
            </div>
            
            {/* Characters in Chapter */}
            <div>
              <label className="block text-sm font-medium text-gold-pale mb-2">Characters</label>
              <input
                type="text"
                className="w-full px-3 py-2.5 text-sm bg-dark-750 border border-gold-rich/20 rounded-lg text-gray-200 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gold-rich/30"
                value={editData.characters || ''}
                onChange={(e) => handleChange('characters', e.target.value)}
                onBlur={handleSave}
                placeholder="Characters appearing in this chapter..."
              />
            </div>
            
            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-gold-pale mb-2">Notes</label>
              <textarea
                className="w-full px-3 py-3 text-sm bg-dark-750 border border-gold-rich/20 rounded-lg text-gray-200 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gold-rich/30 min-h-[60px] resize-none"
                value={editData.notes || ''}
                onChange={(e) => handleChange('notes', e.target.value)}
                onBlur={handleSave}
                placeholder="Additional notes, reminders, ideas..."
              />
            </div>
          </div>
          
          {isDirty && (
            <div className="mt-4 flex items-center justify-end gap-2">
              <span className="text-xs text-gray-500">Unsaved changes</span>
              <button
                className="px-4 py-2 text-sm bg-gradient-to-r from-gold-rich to-gold-deep text-dark-950 rounded-lg hover:from-gold-amber hover:to-gold-rich font-medium"
                onClick={handleSave}
              >
                Save Changes
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Outline Editor with Expandable Chapter Rows
function OutlineEditor({ chapters, onSave, onGenerateFromSynopsis, isGenerating, hasSynopsis }) {
  const [outlineChapters, setOutlineChapters] = useState([])
  const [isSectionExpanded, setIsSectionExpanded] = useState(true)
  
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
      title: `Chapter ${outlineChapters.length + 1}`,
      summary: '',
      key_events: '',
      characters: '',
      notes: ''
    }
    const newChapters = [...outlineChapters, newChapter]
    setOutlineChapters(newChapters)
    onSave(JSON.stringify(newChapters))
  }
  
  return (
    <div className="h-full flex flex-col">
      {/* Section Header */}
      <div className="bg-dark-800 rounded-xl shadow-sm border border-gold-rich/10 mb-4">
        <div className="flex items-center justify-between px-4 py-4 border-b border-gold-rich/10">
          <button
            className="flex items-center gap-3 text-left"
            onClick={() => setIsSectionExpanded(!isSectionExpanded)}
          >
            <span className="text-gray-500 text-sm">
              {isSectionExpanded ? Icons.ARROW_COLLAPSE : Icons.ARROW_EXPAND}
            </span>
            <span className="text-2xl">{Icons.OUTLINE}</span>
            <div>
              <h1 className="text-xl font-semibold text-gold-soft">Story Outline</h1>
              <p className="text-sm text-gray-400">
                {outlineChapters.length} chapter{outlineChapters.length !== 1 ? 's' : ''} planned
              </p>
            </div>
          </button>
          
          <div className="flex items-center gap-2">
            {hasSynopsis && (
              <button
                className="flex items-center gap-1 text-gray-400 hover:text-gold-rich font-medium text-sm border border-gold-rich/20 rounded-lg px-3 py-1.5 hover:bg-gold-rich/10 transition-colors"
                onClick={onGenerateFromSynopsis}
                disabled={isGenerating}
              >
                {isGenerating ? (
                  <><div className="spinner !w-3 !h-3" /> Generating...</>
                ) : (
                  <><span>🤖</span> <span>Generate from Synopsis</span></>
                )}
              </button>
            )}
            <button
              className="flex items-center gap-1 text-gold-rich hover:text-gold-amber font-medium text-sm"
              onClick={handleAddChapter}
            >
              <span>+</span>
              <span>Add Chapter</span>
            </button>
          </div>
        </div>
        
        {/* Chapters List */}
        {isSectionExpanded && (
          <div className="p-4 max-h-[calc(100vh-350px)] overflow-y-auto">
            {outlineChapters.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-5xl mb-4 opacity-50">{Icons.OUTLINE}</div>
                <h2 className="text-lg font-semibold text-gray-200 mb-2">No Chapters Yet</h2>
                <p className="text-gray-400 mb-4 text-sm">
                  {hasSynopsis 
                    ? 'Generate chapter outline from your synopsis or add chapters manually.'
                    : 'Write a synopsis first, then generate an outline, or add chapters manually.'}
                </p>
                <div className="flex items-center justify-center gap-3">
                  {hasSynopsis && (
                    <button
                      className="px-4 py-2 rounded-lg bg-dark-700 text-gray-300 hover:bg-dark-600 text-sm font-medium flex items-center gap-2 border border-gold-rich/20"
                      onClick={onGenerateFromSynopsis}
                      disabled={isGenerating}
                    >
                      🤖 Generate from Synopsis
                    </button>
                  )}
                  <button
                    className="px-4 py-2 rounded-lg bg-gradient-to-r from-gold-rich to-gold-deep text-dark-950 hover:from-gold-amber hover:to-gold-rich text-sm font-medium flex items-center gap-2"
                    onClick={handleAddChapter}
                  >
                    + Add Manually
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
                />
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// Tab configuration
const TABS = [
  { 
    id: 'braindump', 
    label: 'Braindump', 
    icon: Icons.BRAINDUMP,
    placeholder: 'Dump all your ideas here... notes, fragments, random thoughts about your story.',
    description: 'A free-form space for all your story ideas, notes, and random thoughts.'
  },
  { 
    id: 'genre', 
    label: 'Genre', 
    icon: Icons.GENRE,
    placeholder: 'Define your story\'s genre(s), subgenres, and genre conventions...',
    description: 'Set your story\'s genre and understand its conventions.'
  },
  { 
    id: 'style', 
    label: 'Style', 
    icon: Icons.STYLE,
    placeholder: 'Describe your writing style, tone, POV, tense preferences...',
    description: 'Define your writing style, tone, and voice.'
  },
  { 
    id: 'synopsis', 
    label: 'Synopsis', 
    icon: Icons.SYNOPSIS,
    placeholder: 'Write a summary of your story... beginning, middle, end.',
    description: 'A comprehensive overview of your story from start to finish.'
  },
  { 
    id: 'outline', 
    label: 'Outline', 
    icon: Icons.OUTLINE,
    placeholder: 'Structure your story... chapters, scenes, plot beats...',
    description: 'Plan your story structure and major plot points.'
  },
]

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
  const [showSynopsisModal, setShowSynopsisModal] = useState(false)
  const saveTimeoutRef = useRef(null)
  
  const currentTab = TABS.find(t => t.id === currentBibleTab) || TABS[0]
  const content = storyBibleData[currentBibleTab] || ''
  const synopsisContent = storyBibleData['synopsis'] || ''
  const genreContent = storyBibleData['genre'] || 'fiction'
  
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
  
  const handleGenerateSynopsis = async (answers, genre, wordCount) => {
    if (!isElectronApi) {
      addNotification({ type: 'warning', message: 'AI generation requires the Python backend' })
      return
    }
    
    setIsGenerating(true)
    setGeneratingAction('synopsis')
    
    try {
      const wordCountMap = { short: '100-200', medium: '300-500', long: '600-800' }
      const targetWords = wordCountMap[wordCount] || '300-500'
      
      const promptParts = []
      if (answers.protagonist) promptParts.push(`PROTAGONIST: ${answers.protagonist}`)
      if (answers.setting) promptParts.push(`SETTING: ${answers.setting}`)
      if (answers.conflict) promptParts.push(`MAIN CONFLICT: ${answers.conflict}`)
      if (answers.stakes) promptParts.push(`STAKES: ${answers.stakes}`)
      if (answers.antagonist) promptParts.push(`ANTAGONIST: ${answers.antagonist}`)
      if (answers.journey) promptParts.push(`KEY PLOT POINTS: ${answers.journey}`)
      if (answers.climax) promptParts.push(`CLIMAX: ${answers.climax}`)
      if (answers.resolution) promptParts.push(`RESOLUTION: ${answers.resolution}`)
      if (answers.theme) promptParts.push(`THEME: ${answers.theme}`)
      
      const structuredInput = promptParts.join('\n\n')
      
      const result = await window.api.generateSynopsis(structuredInput, genre, targetWords)
      
      if (result && !result.error) {
        handleContentChange(result)
        setShowSynopsisModal(false)
        addNotification({ type: 'success', message: 'Synopsis generated successfully!' })
      } else {
        addNotification({ type: 'error', message: result?.error || 'Failed to generate synopsis' })
      }
    } catch (error) {
      console.error('Generate synopsis error:', error)
      addNotification({ type: 'error', message: `Failed to generate synopsis: ${error.message}` })
    } finally {
      setIsGenerating(false)
      setGeneratingAction('')
    }
  }
  
  const handleGenerateCast = async () => {
    if (!synopsisContent.trim()) {
      addNotification({ type: 'warning', message: 'Please write a synopsis first' })
      return
    }
    
    if (!isElectronApi) {
      addNotification({ type: 'warning', message: 'AI generation requires the Python backend' })
      return
    }
    
    setIsGenerating(true)
    setGeneratingAction('characters')
    
    try {
      const result = await window.api.generateCharactersFromSynopsis(synopsisContent, genreContent)
      
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
    if (!synopsisContent.trim()) {
      addNotification({ type: 'warning', message: 'Please write a synopsis first' })
      return
    }
    
    if (!isElectronApi) {
      addNotification({ type: 'warning', message: 'AI generation requires the Python backend' })
      return
    }
    
    setIsGenerating(true)
    setGeneratingAction('world')
    
    try {
      const result = await window.api.generateWorldFromSynopsis(synopsisContent, genreContent)
      
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
    if (!synopsisContent.trim()) {
      addNotification({ type: 'warning', message: 'Please write a synopsis first' })
      return
    }
    
    if (!isElectronApi) {
      addNotification({ type: 'warning', message: 'AI generation requires the Python backend' })
      return
    }
    
    setIsGenerating(true)
    setGeneratingAction('outline')
    
    try {
      const result = await window.api.generateOutlineFromSynopsis(synopsisContent, 10, genreContent)
      
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
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gold-soft flex items-center gap-2">
            <span>{currentTab.icon}</span>
            <span>{currentTab.label}</span>
          </h1>
          <p className="text-gray-400 mt-1">{currentTab.description}</p>
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
          
          {/* AI Generate Button (for Synopsis) */}
          {currentBibleTab === 'synopsis' && (
            <button
              className="btn btn-secondary"
              onClick={() => setShowSynopsisModal(true)}
              disabled={isGenerating}
            >
              <span>{Icons.MAGIC}</span>
              <span>AI Generate</span>
            </button>
          )}
          
          {/* AI Expand Button (for text tabs only, not outline) */}
          {currentBibleTab !== 'outline' && (
            <button
              className="btn btn-secondary"
              onClick={handleAiExpand}
              disabled={isGenerating || !content.trim()}
              title="Expand existing content with AI"
            >
              {isGenerating && generatingAction === 'expand' ? (
                <>
                  <div className="spinner !w-4 !h-4" />
                  <span>Expanding...</span>
                </>
              ) : (
                <>
                  <span>{Icons.EXPAND}</span>
                  <span>AI Expand</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
      
      {/* Synopsis Generation Buttons */}
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
            isGenerating={isGenerating && generatingAction === 'outline'}
            hasSynopsis={!!synopsisContent.trim()}
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
      
      {/* Word Count (only for text tabs) */}
      {currentBibleTab !== 'outline' && (
        <div className="mt-4 text-sm text-gray-500 text-right">
          {content.trim() ? content.trim().split(/\s+/).length : 0} words
        </div>
      )}
      
      {/* Generate Synopsis Modal */}
      <GenerateSynopsisModal
        isOpen={showSynopsisModal}
        onClose={() => setShowSynopsisModal(false)}
        onGenerate={handleGenerateSynopsis}
        isGenerating={isGenerating && generatingAction === 'synopsis'}
        genre={genreContent}
      />
    </div>
  )
}

export default StoryBible
