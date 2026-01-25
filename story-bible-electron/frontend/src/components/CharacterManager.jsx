/**
 * Character Manager Component
 * ===========================
 * Manages character profiles with card layout and AI generation.
 */

import { useState, useEffect, useRef } from 'react'
import useStore from '../hooks/useStore'
import { usePythonBridge } from '../hooks/usePythonBridge'
import { clsx } from 'clsx'

// Icons
const Icons = {
  PERSON: '👤',
  PLUS: '+',
  DELETE: '🗑️',
  ARCHIVE: '🗄️',
  VISIBLE: '👁️',
  HIDDEN: '👁️‍🗨️',
  AI: '🤖',
  SPARKLE: '✨',
  EDIT: '✏️',
  SAVE: '💾',
  MORE: '⋯',
  CLOSE: '✕',
  MAGIC: '🪄',
  IMPORT: '📥',
  EXPORT: '📤',
}

// Character field configuration
const CHARACTER_FIELDS = [
  { id: 'name', label: 'Name', type: 'text', required: true },
  { id: 'role', label: 'Role', type: 'text', placeholder: 'e.g., Protagonist, Antagonist, Supporting' },
  { id: 'pronouns', label: 'Pronouns', type: 'text', placeholder: 'e.g., he/him, she/her, they/them' },
  { id: 'personality_traits', label: 'Personality Traits', type: 'textarea', placeholder: 'Key personality characteristics...' },
  { id: 'physical_description', label: 'Physical Description', type: 'textarea', placeholder: 'Appearance, mannerisms...' },
  { id: 'backstory', label: 'Backstory', type: 'textarea', placeholder: 'Character history...' },
  { id: 'motivations', label: 'Motivations', type: 'textarea', placeholder: 'What drives this character...' },
  { id: 'internal_conflicts', label: 'Internal Conflicts', type: 'textarea', placeholder: 'Inner struggles...' },
  { id: 'strengths', label: 'Strengths', type: 'textarea', placeholder: 'Character strengths...' },
  { id: 'weaknesses', label: 'Weaknesses', type: 'textarea', placeholder: 'Character flaws...' },
  { id: 'speech_pattern', label: 'Speech Pattern', type: 'textarea', placeholder: 'How they talk...' },
  { id: 'character_arc', label: 'Character Arc', type: 'textarea', placeholder: 'How they change...' },
]

// Example prompts for inspiration
const EXAMPLE_PROMPTS = [
  "A wise old wizard with a mysterious past",
  "A young street thief with a heart of gold",
  "A ruthless CEO hiding a dark secret",
  "A cheerful baker who secretly fights crime at night",
  "A cynical detective who lost faith in humanity",
  "A naive princess who discovers her kingdom's corruption",
  "A reformed villain seeking redemption",
  "A time-traveling scientist stuck in the wrong era",
]

function CharacterCard({ character, isSelected, onClick, onToggleVisibility }) {
  const isVisible = character.is_visible !== 0
  
  return (
    <div
      className={clsx(
        'character-card',
        isSelected && 'border-accent-primary ring-2 ring-accent-primary/30'
      )}
      onClick={() => onClick(character)}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{Icons.PERSON}</span>
          <div>
            <h3 className="font-semibold text-text-primary">{character.name}</h3>
            <p className="text-sm text-text-muted">{character.role || 'No role'}</p>
          </div>
        </div>
        <button
          className={clsx(
            'w-8 h-8 flex items-center justify-center rounded-lg transition-colors',
            isVisible
              ? 'bg-green-500/20 text-green-400'
              : 'bg-red-500/20 text-red-400'
          )}
          onClick={(e) => {
            e.stopPropagation()
            onToggleVisibility(character)
          }}
          title={isVisible ? 'Visible to AI' : 'Hidden from AI'}
        >
          {isVisible ? Icons.VISIBLE : Icons.HIDDEN}
        </button>
      </div>
      
      {/* Preview */}
      {character.personality_traits && (
        <p className="text-sm text-text-secondary line-clamp-2">
          {character.personality_traits}
        </p>
      )}
    </div>
  )
}

function CharacterEditor({ character, onSave, onClose }) {
  const [formData, setFormData] = useState(character || {})
  const [isDirty, setIsDirty] = useState(false)
  
  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setIsDirty(true)
  }
  
  const handleSave = () => {
    onSave(formData)
    setIsDirty(false)
  }
  
  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-text-primary">
          {character?.id ? 'Edit Character' : 'New Character'}
        </h2>
        <div className="flex items-center gap-2">
          <button
            className="btn btn-ghost"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            className={clsx('btn btn-primary', !isDirty && 'opacity-50')}
            onClick={handleSave}
            disabled={!isDirty}
          >
            <span>{Icons.SAVE}</span>
            <span>Save</span>
          </button>
        </div>
      </div>
      
      {/* Form */}
      <div className="flex-1 overflow-y-auto pr-2 space-y-4">
        {CHARACTER_FIELDS.map(field => (
          <div key={field.id}>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              {field.label}
              {field.required && <span className="text-red-400 ml-1">*</span>}
            </label>
            {field.type === 'textarea' ? (
              <textarea
                className="input-textarea min-h-[100px]"
                value={formData[field.id] || ''}
                onChange={(e) => handleChange(field.id, e.target.value)}
                placeholder={field.placeholder}
              />
            ) : (
              <input
                type="text"
                className="input"
                value={formData[field.id] || ''}
                onChange={(e) => handleChange(field.id, e.target.value)}
                placeholder={field.placeholder}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function GenerateCharacterModal({ isOpen, onClose, onGenerate, isGenerating }) {
  const [prompt, setPrompt] = useState('')
  const [genre, setGenre] = useState('fiction')
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (prompt.trim() && prompt.trim().length >= 10) {
      onGenerate(prompt.trim(), genre)
    }
  }
  
  const handleExampleClick = (example) => {
    setPrompt(example)
  }
  
  // Reset form when modal closes
  useEffect(() => {
    if (!isOpen) {
      setPrompt('')
      setGenre('fiction')
    }
  }, [isOpen])
  
  if (!isOpen) return null
  
  const isValidPrompt = prompt.trim().length >= 10
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={!isGenerating ? onClose : undefined}
      />
      
      {/* Modal */}
      <div className="relative z-10 w-full max-w-2xl mx-4 glass-card p-6 animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{Icons.MAGIC}</span>
            <div>
              <h2 className="text-xl font-bold text-text-primary">Generate Character with AI</h2>
              <p className="text-sm text-text-muted">Describe your character and AI will create a complete profile</p>
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
        
        {/* Form */}
        <form onSubmit={handleSubmit}>
          {/* Prompt Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Character Description <span className="text-red-400">*</span>
            </label>
            <textarea
              className="input-textarea min-h-[120px] text-base"
              placeholder="Describe the character you want to create in at least 10 characters...&#10;&#10;Example: A cunning spy who works for two sides, hiding a tragic past and a secret love..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={isGenerating}
              autoFocus
            />
            <p className="text-xs text-text-muted mt-1">
              {prompt.trim().length}/10 characters minimum
              {prompt.trim().length > 0 && prompt.trim().length < 10 && (
                <span className="text-yellow-400 ml-2">Need at least 10 characters</span>
              )}
            </p>
          </div>
          
          {/* Genre Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Story Genre
            </label>
            <select
              className="input"
              value={genre}
              onChange={(e) => setGenre(e.target.value)}
              disabled={isGenerating}
            >
              <option value="fiction">General Fiction</option>
              <option value="fantasy">Fantasy</option>
              <option value="sci-fi">Science Fiction</option>
              <option value="romance">Romance</option>
              <option value="thriller">Thriller</option>
              <option value="mystery">Mystery</option>
              <option value="horror">Horror</option>
              <option value="historical">Historical Fiction</option>
              <option value="literary">Literary Fiction</option>
            </select>
          </div>
          
          {/* Example Prompts */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Need inspiration? Click one:
            </label>
            <div className="flex flex-wrap gap-2">
              {EXAMPLE_PROMPTS.map((example, index) => (
                <button
                  key={index}
                  type="button"
                  className="px-3 py-1.5 text-xs rounded-full bg-bg-hover text-text-muted hover:bg-accent-primary/20 hover:text-accent-primary transition-colors"
                  onClick={() => handleExampleClick(example)}
                  disabled={isGenerating}
                >
                  {example}
                </button>
              ))}
            </div>
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
              type="submit"
              className="btn btn-primary min-w-[180px]"
              disabled={!isValidPrompt || isGenerating}
            >
              {isGenerating ? (
                <>
                  <div className="spinner !w-4 !h-4" />
                  <span>Generating...</span>
                </>
              ) : (
                <>
                  <span>{Icons.SPARKLE}</span>
                  <span>Generate Character</span>
                </>
              )}
            </button>
          </div>
        </form>
        
        {/* Generating State */}
        {isGenerating && (
          <div className="mt-6 p-4 rounded-lg bg-accent-primary/10 border border-accent-primary/30">
            <div className="flex items-center gap-3">
              <div className="spinner !w-6 !h-6" />
              <div>
                <p className="text-accent-primary font-medium">Creating your character...</p>
                <p className="text-sm text-text-muted">AI is filling all character fields. This may take 10-20 seconds.</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function CSVImportModal({ isOpen, onClose, onImport }) {
  const [csvContent, setCsvContent] = useState('')
  const fileInputRef = useRef(null)
  
  const handleFileUpload = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    
    const reader = new FileReader()
    reader.onload = (event) => {
      setCsvContent(event.target.result)
    }
    reader.readAsText(file)
  }
  
  const handleImport = () => {
    if (csvContent.trim()) {
      onImport(csvContent)
      setCsvContent('')
      onClose()
    }
  }
  
  // Reset when modal closes
  useEffect(() => {
    if (!isOpen) {
      setCsvContent('')
    }
  }, [isOpen])
  
  if (!isOpen) return null
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="glass-card p-6 w-full max-w-2xl">
        <h2 className="text-xl font-bold text-text-primary mb-4 flex items-center gap-2">
          <span>{Icons.IMPORT}</span>
          Import Characters from CSV
        </h2>
        
        <div className="mb-4">
          <p className="text-text-muted text-sm mb-2">
            CSV format: name,role,pronouns,personality_traits,physical_description,backstory,motivations,internal_conflicts,strengths,weaknesses,speech_pattern,character_arc
          </p>
          <input
            type="file"
            ref={fileInputRef}
            accept=".csv"
            className="hidden"
            onChange={handleFileUpload}
          />
          <button
            className="btn btn-secondary"
            onClick={() => fileInputRef.current?.click()}
          >
            {Icons.IMPORT} Choose CSV File
          </button>
        </div>
        
        <textarea
          className="input-textarea h-48 font-mono text-sm mb-4"
          placeholder="Or paste CSV content here..."
          value={csvContent}
          onChange={(e) => setCsvContent(e.target.value)}
        />
        
        <div className="flex justify-end gap-3">
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button 
            className="btn btn-primary" 
            onClick={handleImport}
            disabled={!csvContent.trim()}
          >
            Import Characters
          </button>
        </div>
      </div>
    </div>
  )
}

function CharacterManager() {
  const {
    characters,
    selectedCharacterId,
    currentProjectId,
    setCharacters,
    setSelectedCharacter,
    addCharacter,
    updateCharacter,
    addNotification,
  } = useStore()
  
  const {
    getCharacters,
    saveCharacter,
    isElectronApi,
    exportCharactersCsv,
    importCharactersCsv,
  } = usePythonBridge()
  
  const [view, setView] = useState('list') // 'list' | 'edit'
  const [editingCharacter, setEditingCharacter] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [showGenerateModal, setShowGenerateModal] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  
  // Refresh characters
  useEffect(() => {
    async function loadCharacters() {
      if (!currentProjectId) return
      const chars = await getCharacters(currentProjectId)
      setCharacters(chars)
    }
    loadCharacters()
  }, [currentProjectId])
  
  // Handle create new blank character
  const handleCreateBlankCharacter = () => {
    setEditingCharacter({ project_id: currentProjectId })
    setView('edit')
  }
  
  // Handle AI generate character
  const handleGenerateCharacter = async (description, genre) => {
    if (!isElectronApi) {
      addNotification({ type: 'warning', message: 'AI generation requires the Python backend' })
      return
    }
    
    if (!description || !description.trim()) {
      addNotification({ type: 'warning', message: 'Please enter a character description' })
      return
    }
    
    setIsGenerating(true)
    
    try {
      console.log('Generating character with description:', description, 'genre:', genre)
      
      // Call the AI to generate a character
      const generatedCharacter = await window.api.generateSingleCharacter(description, genre)
      
      console.log('AI response:', generatedCharacter)
      
      // Check for error response
      if (generatedCharacter && generatedCharacter.error) {
        addNotification({ type: 'error', message: generatedCharacter.error })
        return
      }
      
      // Check if we have a valid character with a name
      if (generatedCharacter && generatedCharacter.name && generatedCharacter.name.trim()) {
        // Add project_id and save immediately
        const characterToSave = {
          project_id: currentProjectId,
          name: generatedCharacter.name,
          role: generatedCharacter.role || '',
          pronouns: generatedCharacter.pronouns || '',
          personality_traits: generatedCharacter.personality_traits || '',
          physical_description: generatedCharacter.physical_description || '',
          backstory: generatedCharacter.backstory || '',
          motivations: generatedCharacter.motivations || '',
          internal_conflicts: generatedCharacter.internal_conflicts || '',
          strengths: generatedCharacter.strengths || '',
          weaknesses: generatedCharacter.weaknesses || '',
          speech_pattern: generatedCharacter.speech_pattern || '',
          character_arc: generatedCharacter.character_arc || '',
          is_visible: 1,
        }
        
        console.log('Saving character:', characterToSave)
        
        const success = await saveCharacter(characterToSave)
        
        if (success) {
          // Refresh characters list
          const chars = await getCharacters(currentProjectId)
          setCharacters(chars)
          
          // Close modal and show success
          setShowGenerateModal(false)
          addNotification({ 
            type: 'success', 
            message: `Character "${generatedCharacter.name}" created successfully!` 
          })
        } else {
          addNotification({ type: 'error', message: 'Failed to save the generated character to database' })
        }
      } else {
        console.error('Invalid character response:', generatedCharacter)
        addNotification({ 
          type: 'error', 
          message: 'AI could not generate a valid character. Please try a different or more detailed description.' 
        })
      }
    } catch (error) {
      console.error('Character generation error:', error)
      addNotification({ 
        type: 'error', 
        message: `Failed to generate character: ${error.message || 'Unknown error'}` 
      })
    } finally {
      setIsGenerating(false)
    }
  }
  
  // Handle save character
  const handleSaveCharacter = async (data) => {
    const success = await saveCharacter({
      ...data,
      project_id: currentProjectId,
    })
    
    if (success) {
      // Refresh characters list
      const chars = await getCharacters(currentProjectId)
      setCharacters(chars)
      setView('list')
      setEditingCharacter(null)
      addNotification({ type: 'success', message: 'Character saved' })
    }
  }
  
  // Handle toggle visibility
  const handleToggleVisibility = async (character) => {
    const newVisibility = character.is_visible === 0 ? 1 : 0
    await saveCharacter({
      ...character,
      is_visible: newVisibility,
    })
    
    // Refresh characters
    const chars = await getCharacters(currentProjectId)
    setCharacters(chars)
  }
  
  // Handle edit character
  const handleEditCharacter = (character) => {
    setEditingCharacter(character)
    setView('edit')
  }
  
  // Handle CSV export
  const handleExport = async () => {
    try {
      const csvData = await exportCharactersCsv(currentProjectId)
      if (!csvData) {
        addNotification({ type: 'warning', message: 'No characters to export' })
        return
      }
      
      // Download CSV
      const blob = new Blob([csvData], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'characters.csv'
      a.click()
      URL.revokeObjectURL(url)
      
      addNotification({ type: 'success', message: 'Characters exported' })
    } catch (error) {
      console.error('Failed to export:', error)
      addNotification({ type: 'error', message: 'Failed to export characters' })
    }
  }
  
  // Handle CSV import
  const handleImport = async (csvData) => {
    try {
      const result = await importCharactersCsv(currentProjectId, csvData)
      
      if (result.imported > 0) {
        addNotification({ type: 'success', message: `Imported ${result.imported} characters` })
      }
      if (result.errors?.length > 0) {
        addNotification({ type: 'warning', message: `${result.errors.length} errors during import` })
      }
      
      // Refresh list
      const chars = await getCharacters(currentProjectId)
      setCharacters(chars)
    } catch (error) {
      console.error('Failed to import:', error)
      addNotification({ type: 'error', message: 'Failed to import characters' })
    }
  }
  
  // Render
  if (view === 'edit') {
    return (
      <div className="h-full p-6">
        <CharacterEditor
          character={editingCharacter}
          onSave={handleSaveCharacter}
          onClose={() => {
            setView('list')
            setEditingCharacter(null)
          }}
        />
      </div>
    )
  }
  
  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">Characters</h1>
          <p className="text-text-muted mt-1">
            {characters.length} character{characters.length !== 1 ? 's' : ''} in project
          </p>
        </div>
        
        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            className="btn btn-ghost"
            onClick={() => setShowImportModal(true)}
            title="Import CSV"
          >
            <span>{Icons.IMPORT}</span>
            <span>Import</span>
          </button>
          <button
            className="btn btn-ghost"
            onClick={handleExport}
            title="Export CSV"
          >
            <span>{Icons.EXPORT}</span>
            <span>Export</span>
          </button>
          <button 
            className="btn btn-secondary flex items-center gap-2"
            onClick={() => setShowGenerateModal(true)}
            title="Generate character with AI"
          >
            <span>{Icons.MAGIC}</span>
            <span>Generate with AI</span>
          </button>
          <button 
            className="btn btn-primary flex items-center gap-2"
            onClick={handleCreateBlankCharacter}
          >
            <span>{Icons.PLUS}</span>
            <span>New Character</span>
          </button>
        </div>
      </div>
      
      {/* Character Grid */}
      <div className="flex-1 overflow-y-auto">
        {characters.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md">
              <div className="text-6xl mb-6">👥</div>
              <h2 className="text-xl font-semibold text-text-primary mb-2">
                No Characters Yet
              </h2>
              <p className="text-text-muted mb-6">
                Create your first character to start building your story's cast.
              </p>
              <div className="flex items-center justify-center gap-3">
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowGenerateModal(true)}
                >
                  <span>{Icons.MAGIC}</span>
                  <span>Generate with AI</span>
                </button>
                <button
                  className="btn btn-primary"
                  onClick={handleCreateBlankCharacter}
                >
                  <span>{Icons.PLUS}</span>
                  <span>Create Manually</span>
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {characters.map(character => (
              <CharacterCard
                key={character.id || character.name}
                character={character}
                isSelected={selectedCharacterId === character.id}
                onClick={handleEditCharacter}
                onToggleVisibility={handleToggleVisibility}
              />
            ))}
          </div>
        )}
      </div>
      
      {/* Generate Character Modal */}
      <GenerateCharacterModal
        isOpen={showGenerateModal}
        onClose={() => setShowGenerateModal(false)}
        onGenerate={handleGenerateCharacter}
        isGenerating={isGenerating}
      />
      
      {/* CSV Import Modal */}
      <CSVImportModal
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        onImport={handleImport}
      />
    </div>
  )
}

export default CharacterManager
