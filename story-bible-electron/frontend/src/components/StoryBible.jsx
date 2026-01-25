/**
 * Story Bible Component
 * =====================
 * Displays Story Bible tabs (Braindump, Genre, Style, Synopsis, etc.)
 * Includes AI-powered generation from synopsis.
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
    // Check required fields
    const hasProtagonist = answers.protagonist?.trim()
    const hasConflict = answers.conflict?.trim()
    
    if (!hasProtagonist || !hasConflict) {
      return
    }
    
    onGenerate(answers, selectedGenre, wordCount)
  }
  
  // Reset form when modal closes
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
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={!isGenerating ? onClose : undefined}
      />
      
      {/* Modal */}
      <div className="relative z-10 w-full max-w-3xl mx-4 glass-card p-6 animate-slide-up max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{Icons.MAGIC}</span>
            <div>
              <h2 className="text-xl font-bold text-text-primary">Generate Synopsis with AI</h2>
              <p className="text-sm text-text-muted">Answer a few questions and AI will create your synopsis</p>
            </div>
          </div>
          {!isGenerating && (
            <button
              className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-bg-hover text-text-muted hover:text-text-primary transition-colors"
              onClick={onClose}
            >
              {Icons.CLOSE}
            </button>
          )}
        </div>
        
        {/* Genre and Length Selection */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
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
            <label className="block text-sm font-medium text-text-secondary mb-2">
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
        
        {/* Questions */}
        <div className="space-y-4 mb-6">
          {SYNOPSIS_QUESTIONS.map(question => (
            <div key={question.id}>
              <label className="block text-sm font-medium text-text-secondary mb-1">
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
        
        {/* Info Note */}
        <div className="mb-6 p-3 rounded-lg bg-accent-primary/10 border border-accent-primary/20">
          <p className="text-sm text-text-muted">
            <span className="text-accent-primary font-medium">💡 Tip:</span> The more detail you provide, the better your synopsis will be. 
            At minimum, fill in the protagonist and main conflict.
          </p>
        </div>
        
        {/* Actions */}
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
        
        {/* Generating State */}
        {isGenerating && (
          <div className="mt-6 p-4 rounded-lg bg-accent-primary/10 border border-accent-primary/30">
            <div className="flex items-center gap-3">
              <div className="spinner !w-6 !h-6" />
              <div>
                <p className="text-accent-primary font-medium">Creating your synopsis...</p>
                <p className="text-sm text-text-muted">AI is weaving your story elements together. This may take 20-30 seconds.</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Outline Chapter Card Component
function OutlineChapterCard({ chapter, index, onUpdate, onDelete }) {
  const [isEditing, setIsEditing] = useState(false)
  const [editData, setEditData] = useState(chapter)
  
  const handleSave = () => {
    onUpdate(index, editData)
    setIsEditing(false)
  }
  
  const handleCancel = () => {
    setEditData(chapter)
    setIsEditing(false)
  }
  
  if (isEditing) {
    return (
      <div className="glass-card p-4 border-2 border-accent-primary">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-lg font-bold text-accent-primary">Ch {chapter.chapter_number}</span>
          <input
            type="text"
            className="input flex-1"
            value={editData.title}
            onChange={(e) => setEditData({ ...editData, title: e.target.value })}
            placeholder="Chapter Title"
          />
        </div>
        <textarea
          className="input-textarea min-h-[100px] mb-3"
          value={editData.summary}
          onChange={(e) => setEditData({ ...editData, summary: e.target.value })}
          placeholder="Chapter summary..."
        />
        <textarea
          className="input-textarea min-h-[60px] mb-3"
          value={editData.key_events || ''}
          onChange={(e) => setEditData({ ...editData, key_events: e.target.value })}
          placeholder="Key events..."
        />
        <div className="flex justify-end gap-2">
          <button className="btn btn-ghost text-sm" onClick={handleCancel}>Cancel</button>
          <button className="btn btn-primary text-sm" onClick={handleSave}>Save</button>
        </div>
      </div>
    )
  }
  
  return (
    <div 
      className="glass-card p-4 hover:border-accent-primary/50 transition-all cursor-pointer group"
      onClick={() => setIsEditing(true)}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="w-8 h-8 rounded-lg bg-accent-primary/20 text-accent-primary flex items-center justify-center font-bold text-sm">
            {chapter.chapter_number}
          </span>
          <h3 className="font-semibold text-text-primary">{chapter.title}</h3>
        </div>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            className="w-7 h-7 flex items-center justify-center rounded text-text-muted hover:text-text-primary hover:bg-bg-hover"
            onClick={(e) => { e.stopPropagation(); setIsEditing(true); }}
            title="Edit"
          >
            ✏️
          </button>
          <button
            className="w-7 h-7 flex items-center justify-center rounded text-text-muted hover:text-red-400 hover:bg-red-500/20"
            onClick={(e) => { e.stopPropagation(); onDelete(index); }}
            title="Delete"
          >
            🗑️
          </button>
        </div>
      </div>
      <p className="text-text-secondary text-sm mb-2">{chapter.summary}</p>
      {chapter.key_events && (
        <p className="text-text-muted text-xs italic">📌 {chapter.key_events}</p>
      )}
    </div>
  )
}

// Outline Editor with Chapter Cards
function OutlineEditor({ chapters, onSave, onGenerateFromSynopsis, isGenerating, hasSynopsis }) {
  const [outlineChapters, setOutlineChapters] = useState([])
  
  useEffect(() => {
    // Parse chapters from string if needed
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
      // Renumber chapters
      newChapters.forEach((ch, i) => ch.chapter_number = i + 1)
      setOutlineChapters(newChapters)
      onSave(JSON.stringify(newChapters))
    }
  }
  
  const handleAddChapter = () => {
    const newChapter = {
      chapter_number: outlineChapters.length + 1,
      title: `Chapter ${outlineChapters.length + 1}`,
      summary: '',
      key_events: ''
    }
    const newChapters = [...outlineChapters, newChapter]
    setOutlineChapters(newChapters)
    onSave(JSON.stringify(newChapters))
  }
  
  return (
    <div className="h-full flex flex-col">
      {/* Actions Bar */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-text-muted text-sm">
          {outlineChapters.length} chapter{outlineChapters.length !== 1 ? 's' : ''} in outline
        </p>
        <div className="flex items-center gap-2">
          {hasSynopsis && (
            <button
              className="btn btn-secondary text-sm"
              onClick={onGenerateFromSynopsis}
              disabled={isGenerating}
            >
              {isGenerating ? (
                <><div className="spinner !w-3 !h-3" /> Generating...</>
              ) : (
                <>🤖 Generate from Synopsis</>
              )}
            </button>
          )}
          <button className="btn btn-primary text-sm" onClick={handleAddChapter}>
            + Add Chapter
          </button>
        </div>
      </div>
      
      {/* Chapter Cards Grid */}
      <div className="flex-1 overflow-y-auto">
        {outlineChapters.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md">
              <div className="text-6xl mb-4">📋</div>
              <h3 className="text-lg font-semibold text-text-primary mb-2">No Outline Yet</h3>
              <p className="text-text-muted mb-4">
                {hasSynopsis 
                  ? 'Generate chapter outline from your synopsis or add chapters manually.'
                  : 'Write a synopsis first, then generate an outline, or add chapters manually.'}
              </p>
              <div className="flex items-center justify-center gap-2">
                {hasSynopsis && (
                  <button
                    className="btn btn-secondary"
                    onClick={onGenerateFromSynopsis}
                    disabled={isGenerating}
                  >
                    🤖 Generate from Synopsis
                  </button>
                )}
                <button className="btn btn-primary" onClick={handleAddChapter}>
                  + Add Manually
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pb-4">
            {outlineChapters.map((chapter, index) => (
              <OutlineChapterCard
                key={index}
                chapter={chapter}
                index={index}
                onUpdate={handleUpdateChapter}
                onDelete={handleDeleteChapter}
              />
            ))}
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
  
  // Get current tab config
  const currentTab = TABS.find(t => t.id === currentBibleTab) || TABS[0]
  const content = storyBibleData[currentBibleTab] || ''
  const synopsisContent = storyBibleData['synopsis'] || ''
  const genreContent = storyBibleData['genre'] || 'fiction'
  
  // Load story bible data
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
  
  // Handle content change with debounced save
  const handleContentChange = (value) => {
    updateBibleField(currentBibleTab, value)
    
    // Debounced save
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current)
    }
    
    saveTimeoutRef.current = setTimeout(async () => {
      setIsSaving(true)
      await saveBibleField(currentProjectId, currentBibleTab, value)
      setIsSaving(false)
    }, 1000)
  }
  
  // Handle AI expand
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
  
  // Handle Generate Synopsis from questions
  const handleGenerateSynopsis = async (answers, genre, wordCount) => {
    if (!isElectronApi) {
      addNotification({ type: 'warning', message: 'AI generation requires the Python backend' })
      return
    }
    
    setIsGenerating(true)
    setGeneratingAction('synopsis')
    
    try {
      // Build a structured prompt from the answers
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
      
      // Use the AI to generate a synopsis
      const result = await window.api.generateSynopsis(structuredInput, genre, targetWords)
      
      if (result && !result.error) {
        // Update the synopsis field
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
  
  // Generate Cast from Synopsis
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
        // Save characters one by one and track successes
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
        
        // Refresh characters list
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
  
  // Generate World from Synopsis
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
        // Save world elements
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
  
  // Generate Outline from Synopsis
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
        // Convert array to JSON string for storage
        const outlineData = Array.isArray(result) ? JSON.stringify(result) : result
        
        // Update the outline field
        updateBibleField('outline', outlineData)
        await saveBibleField(currentProjectId, 'outline', outlineData)
        
        const chapterCount = Array.isArray(result) ? result.length : 'unknown'
        addNotification({ type: 'success', message: `Generated ${chapterCount} chapter outline from synopsis` })
        
        // Switch to outline tab
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
  
  // Cleanup
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
          <h1 className="text-2xl font-semibold text-text-primary flex items-center gap-2">
            <span>{currentTab.icon}</span>
            <span>{currentTab.label}</span>
          </h1>
          <p className="text-text-muted mt-1">{currentTab.description}</p>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Save Status */}
          <div className={clsx(
            'px-3 py-1.5 rounded-lg text-sm',
            isSaving
              ? 'bg-yellow-500/20 text-yellow-400'
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
        <div className="flex items-center gap-2 mb-4 p-3 rounded-xl bg-accent-primary/10 border border-accent-primary/20">
          <span className="text-sm text-text-muted mr-2">{Icons.GENERATE} Generate from Synopsis:</span>
          
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
                ? 'bg-accent-primary text-white'
                : 'bg-bg-card/60 text-text-muted hover:bg-bg-hover hover:text-text-primary'
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
            className="w-full h-full input-textarea text-editor"
            value={content}
            onChange={(e) => handleContentChange(e.target.value)}
            placeholder={currentTab.placeholder}
          />
        )}
      </div>
      
      {/* Word Count (only for text tabs) */}
      {currentBibleTab !== 'outline' && (
        <div className="mt-4 text-sm text-text-muted text-right">
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

