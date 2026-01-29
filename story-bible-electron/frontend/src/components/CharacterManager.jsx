/**
 * Character Manager Component
 * ===========================
 * Manages character profiles with expandable list layout and AI generation.
 * Dark & Gold luxury theme
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
  DRAG: '⋮⋮',
  EXPAND: '▶',
  COLLAPSE: '▼',
  COPY: '📋',
  CLOCK: '🕐',
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

// Role options for dropdown
const ROLE_OPTIONS = [
  'Protagonist',
  'Antagonist',
  'Supporting',
  'Minor',
  'Mentor',
  'Love Interest',
  'Sidekick',
  'Villain',
  'Other'
]

// Editable field with AI rewrite capability
function EditableField({ label, value, onChange, onSave, onRewrite, placeholder, isRewriting }) {
  const [isFocused, setIsFocused] = useState(false)
  const [showRewriteInput, setShowRewriteInput] = useState(false)
  const [rewriteInstruction, setRewriteInstruction] = useState('')
  const textareaRef = useRef(null)
  
  const handleRewrite = async () => {
    if (rewriteInstruction.trim() && value?.trim()) {
      await onRewrite(rewriteInstruction.trim())
      setRewriteInstruction('')
      setShowRewriteInput(false)
      setIsFocused(false)
    }
  }
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault()
      handleRewrite()
    }
    if (e.key === 'Escape') {
      setShowRewriteInput(false)
      setRewriteInstruction('')
    }
  }
  
  // Close rewrite input when clicking outside
  const handleBlur = (e) => {
    // Check if the new focus target is within our component
    const currentTarget = e.currentTarget
    setTimeout(() => {
      if (!currentTarget.contains(document.activeElement) && !showRewriteInput) {
        setIsFocused(false)
        onSave()
      }
    }, 100)
  }
  
  return (
    <div 
      className={clsx(
        "rounded-xl p-4 border transition-all",
        isFocused || showRewriteInput
          ? "bg-dark-700/50 border-gold-rich/40"
          : "bg-dark-800/50 border-gold-rich/10"
      )}
      onBlur={handleBlur}
    >
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-medium text-gold-pale">{label}</label>
        <button
          className="w-6 h-6 flex items-center justify-center rounded text-text-muted hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
          title="More options"
        >
          {Icons.MORE}
        </button>
      </div>
      
      <div className="relative">
        <textarea
          ref={textareaRef}
          className={clsx(
            "w-full px-3 py-3 text-sm bg-dark-750 border border-gold-rich/20 rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-gold-rich/30 focus:border-gold-rich/40 min-h-[80px] resize-none transition-all",
            isRewriting ? "opacity-50" : ""
          )}
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setIsFocused(true)}
          placeholder={placeholder}
          disabled={isRewriting}
        />
        
        {/* Visibility toggle */}
        <button
          className="absolute top-3 right-3 w-6 h-6 flex items-center justify-center rounded text-text-muted hover:text-gold-rich transition-colors"
          title="Toggle visibility"
        >
          {Icons.VISIBLE}
        </button>
        
        {/* Loading overlay */}
        {isRewriting && (
          <div className="absolute inset-0 flex items-center justify-center bg-dark-800/80 rounded-lg">
            <div className="flex items-center gap-2 text-gold-rich">
              <div className="w-5 h-5 border-2 border-gold-rich/20 border-t-gold-rich rounded-full animate-spin" />
              <span className="text-sm font-medium">Rewriting...</span>
            </div>
          </div>
        )}
      </div>
      
      {/* Rewrite Button - Shows ONLY when input is focused and has content */}
      {isFocused && value?.trim() && !showRewriteInput && !isRewriting && (
        <button
          className="mt-3 flex items-center gap-1.5 text-sm text-gold-rich hover:text-gold-amber font-medium transition-colors"
          onClick={() => setShowRewriteInput(true)}
          onMouseDown={(e) => e.preventDefault()} // Prevent blur
        >
          <span className="text-base">✨</span>
          <span>Rewrite...</span>
        </button>
      )}
      
      {/* Rewrite Input */}
      {showRewriteInput && !isRewriting && (
        <div className="mt-3">
          <div className="flex items-center gap-2">
            <input
              type="text"
              className="flex-1 px-3 py-2.5 text-sm bg-dark-750 border border-gold-rich/20 rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-gold-rich/30 focus:border-gold-rich/40"
              placeholder={`Tell AI how to rewrite "${label}"...`}
              value={rewriteInstruction}
              onChange={(e) => setRewriteInstruction(e.target.value)}
              onKeyDown={handleKeyDown}
              autoFocus
            />
            <button
              className={clsx(
                'px-4 py-2.5 rounded-lg text-sm font-medium flex items-center gap-2 transition-all min-w-[90px] justify-center',
                rewriteInstruction.trim() && value?.trim()
                  ? 'bg-gradient-to-r from-gold-rich to-gold-deep text-dark-950 hover:from-gold-amber hover:to-gold-rich shadow-gold-sm'
                  : 'bg-dark-600 text-text-muted cursor-not-allowed'
              )}
              onClick={handleRewrite}
              disabled={!rewriteInstruction.trim() || !value?.trim() || isRewriting}
            >
              <span>Go</span>
              <span className="text-xs bg-dark-950/20 px-1.5 py-0.5 rounded">ctrl</span>
              <span className="text-xs">↵</span>
            </button>
          </div>
          <button
            className="mt-2 text-xs text-text-muted hover:text-gold-rich transition-colors"
            onClick={() => {
              setShowRewriteInput(false)
              setRewriteInstruction('')
            }}
          >
            Cancel (Esc)
          </button>
        </div>
      )}
    </div>
  )
}

function CharacterRow({ character, onToggleVisibility, onDuplicate, onDelete, onRoleChange, onSave, onRewriteField, isFromSeries = false, sourceProjectName = '' }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const [menuPosition, setMenuPosition] = useState({ top: 0, right: 0 })
  const [editData, setEditData] = useState(character)
  const [isDirty, setIsDirty] = useState(false)
  const [rewritingField, setRewritingField] = useState(null)
  const menuRef = useRef(null)
  const menuButtonRef = useRef(null)
  const isVisible = character.is_visible !== 0
  
  // Update editData when character changes
  useEffect(() => {
    setEditData(character)
    setIsDirty(false)
  }, [character])
  
  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  // Handle field change
  const handleChange = (field, value) => {
    setEditData(prev => ({ ...prev, [field]: value }))
    setIsDirty(true)
  }
  
  // Handle save
  const handleSave = () => {
    if (isDirty) {
      onSave(editData)
      setIsDirty(false)
    }
  }
  
  // Handle name change with blur save
  const handleNameBlur = () => {
    if (isDirty && editData.name?.trim()) {
      handleSave()
    }
  }
  
  // Handle AI rewrite for a field
  const handleRewrite = async (field, instruction) => {
    if (!onRewriteField) return
    
    setRewritingField(field)
    try {
      const rewritten = await onRewriteField(field, editData[field], instruction, editData.name)
      if (rewritten) {
        handleChange(field, rewritten)
        // Auto-save after rewrite
        const newData = { ...editData, [field]: rewritten }
        onSave(newData)
      }
    } finally {
      setRewritingField(null)
    }
  }
  
  // Field configuration for the expanded view
  const fields = [
    { id: 'pronouns', label: 'Pronouns', placeholder: 'e.g., he/him, she/her, they/them' },
    { id: 'personality_traits', label: 'Personality Traits', placeholder: 'Key personality characteristics...' },
    { id: 'physical_description', label: 'Physical Description', placeholder: 'Appearance, mannerisms...' },
    { id: 'backstory', label: 'Backstory', placeholder: 'Character history...' },
    { id: 'motivations', label: 'Motivations', placeholder: 'What drives this character...' },
    { id: 'internal_conflicts', label: 'Internal Conflicts', placeholder: 'Inner struggles...' },
    { id: 'strengths', label: 'Strengths', placeholder: 'Character strengths...' },
    { id: 'weaknesses', label: 'Weaknesses', placeholder: 'Character flaws...' },
    { id: 'speech_pattern', label: 'Speech Pattern', placeholder: 'How they talk...' },
    { id: 'character_arc', label: 'Character Arc', placeholder: 'How they change throughout the story...' },
  ]
  
  return (
    <div className="border-b border-gold-rich/10 last:border-b-0">
      {/* Main Row */}
      <div className="flex items-center gap-3 px-4 py-3 hover:bg-gold-rich/5 transition-colors group">
        {/* Drag Handle */}
        <span className="text-text-muted cursor-grab text-sm">{Icons.DRAG}</span>
        
        {/* Expand Arrow */}
        <button
          className="w-5 h-5 flex items-center justify-center text-text-muted hover:text-gold-rich transition-colors"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? Icons.COLLAPSE : Icons.EXPAND}
        </button>
        
        {/* Character Name - Editable */}
        <div className="flex-1 flex items-center gap-2">
          <input
            type="text"
            className={clsx(
              "flex-1 font-medium bg-transparent border-none focus:outline-none focus:ring-0 hover:bg-dark-700/50 focus:bg-dark-700 px-2 py-1 rounded",
              isFromSeries ? "text-text-secondary" : "text-text-primary"
            )}
            value={editData.name || ''}
            onChange={(e) => handleChange('name', e.target.value)}
            onBlur={handleNameBlur}
            placeholder="Character name..."
            disabled={isFromSeries}
          />
          {isFromSeries && sourceProjectName && (
            <span className="text-xs px-2 py-0.5 rounded bg-gold-rich/10 text-gold-rich/80 border border-gold-rich/20 whitespace-nowrap">
              from {sourceProjectName}
            </span>
          )}
        </div>
        
        {/* Role Dropdown */}
        <div className="relative">
          <select
            className="appearance-none bg-dark-700 border border-gold-rich/20 rounded-lg px-3 py-1.5 text-sm text-text-secondary cursor-pointer hover:bg-dark-600 hover:border-gold-rich/30 focus:outline-none focus:ring-2 focus:ring-gold-rich/30"
            value={editData.role || 'Other'}
            onChange={(e) => {
              handleChange('role', e.target.value)
              onRoleChange(character, e.target.value)
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {ROLE_OPTIONS.map(role => (
              <option key={role} value={role}>{role}</option>
            ))}
          </select>
          <span className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-gold-rich/60 text-xs">▼</span>
        </div>
        
        {/* Action Icons */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {/* Visibility Toggle */}
          <button
            className={clsx(
              'w-8 h-8 flex items-center justify-center rounded-lg transition-colors',
              isVisible
                ? 'text-text-muted hover:text-green-400 hover:bg-green-400/10'
                : 'text-red-400 hover:text-red-300 hover:bg-red-400/10'
            )}
            onClick={() => onToggleVisibility(character)}
            title={isVisible ? 'Visible to AI (click to hide)' : 'Hidden from AI (click to show)'}
          >
            {isVisible ? Icons.VISIBLE : Icons.HIDDEN}
          </button>
          
          {/* Clock/History (placeholder) */}
          <button
            className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
            title="History"
          >
            {Icons.CLOCK}
          </button>
          
          {/* Duplicate */}
          <button
            className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
            onClick={() => onDuplicate(character)}
            title="Duplicate"
          >
            {Icons.COPY}
          </button>
          
          {/* More Menu */}
          <div className="relative" ref={menuRef}>
            <button
              ref={menuButtonRef}
              className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
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
                className="fixed bg-dark-800 rounded-xl shadow-lg shadow-black/50 border border-gold-rich/20 min-w-[140px] py-2 z-[9999]"
                style={{ top: menuPosition.top, right: menuPosition.right }}
              >
                <button
                  className="w-full px-4 py-2 text-left text-sm text-text-secondary hover:bg-gold-rich/10 hover:text-gold-rich flex items-center gap-2"
                  onClick={() => {
                    onDuplicate(character)
                    setShowMenu(false)
                  }}
                >
                  {Icons.COPY} Duplicate
                </button>
                <button
                  className="w-full px-4 py-2 text-left text-sm text-red-400 hover:bg-red-400/10 flex items-center gap-2"
                  onClick={() => {
                    onDelete(character)
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
      
      {/* Expanded Content - All fields vertical */}
      {isExpanded && (
        <div className="px-12 pb-6 bg-dark-850/50 animate-fade-in">
          <div className="space-y-4">
            {fields.map(field => (
              <EditableField
                key={field.id}
                label={field.label}
                value={editData[field.id]}
                onChange={(value) => handleChange(field.id, value)}
                onSave={handleSave}
                onRewrite={(instruction) => handleRewrite(field.id, instruction)}
                placeholder={field.placeholder}
                isRewriting={rewritingField === field.id}
              />
            ))}
          </div>
          
          {/* Save indicator */}
          {isDirty && (
            <div className="mt-4 flex items-center justify-end gap-2">
              <span className="text-xs text-text-muted">Unsaved changes</span>
              <button
                className="px-4 py-2 text-sm bg-gradient-to-r from-gold-rich to-gold-deep text-dark-950 rounded-lg hover:from-gold-amber hover:to-gold-rich font-medium shadow-gold-sm"
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
            <label className="block text-sm font-medium text-gold-pale mb-1">
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
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
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
              className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gold-rich/10 text-text-muted hover:text-gold-rich transition-colors"
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
            <label className="block text-sm font-medium text-gold-pale mb-2">
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
            <label className="block text-sm font-medium text-gold-pale mb-2">
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
            <label className="block text-sm font-medium text-gold-pale mb-2">
              Need inspiration? Click one:
            </label>
            <div className="flex flex-wrap gap-2">
              {EXAMPLE_PROMPTS.map((example, index) => (
                <button
                  key={index}
                  type="button"
                  className="px-3 py-1.5 text-xs rounded-full bg-dark-700 border border-gold-rich/20 text-text-muted hover:bg-gold-rich/10 hover:border-gold-rich/40 hover:text-gold-rich transition-colors"
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
          <div className="mt-6 p-4 rounded-lg bg-gold-rich/10 border border-gold-rich/30">
            <div className="flex items-center gap-3">
              <div className="spinner !w-6 !h-6" />
              <div>
                <p className="text-gold-rich font-medium">Creating your character...</p>
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
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
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
    currentSeriesId,
    currentSeriesProjects,
    projects,
    setCharacters,
    setSelectedCharacter,
    addCharacter,
    updateCharacter,
    addNotification,
  } = useStore()
  
  const {
    getCharacters,
    saveCharacter,
    deleteCharacter,
    isElectronApi,
    exportCharactersCsv,
    importCharactersCsv,
  } = usePythonBridge()
  
  const [view, setView] = useState('list') // 'list' | 'edit'
  const [editingCharacter, setEditingCharacter] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [showGenerateModal, setShowGenerateModal] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  const [isSectionExpanded, setIsSectionExpanded] = useState(true)
  const [showSectionMenu, setShowSectionMenu] = useState(false)
  const [seriesCharacters, setSeriesCharacters] = useState([]) // Characters from other projects in series
  const sectionMenuRef = useRef(null)
  
  // Check if current project is part of a series
  const isInSeries = currentSeriesId !== null && currentSeriesProjects.length > 0
  
  // Close section menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (sectionMenuRef.current && !sectionMenuRef.current.contains(event.target)) {
        setShowSectionMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  // Refresh characters (including series characters if applicable)
  useEffect(() => {
    async function loadCharacters() {
      if (!currentProjectId) return
      
      // Load current project's characters
      const chars = await getCharacters(currentProjectId)
      setCharacters(chars)
      
      // If part of a series, also load characters from other series projects
      if (isInSeries && currentSeriesProjects.length > 1) {
        const otherProjectIds = currentSeriesProjects.filter(id => id !== currentProjectId)
        const allSeriesChars = []
        
        for (const projectId of otherProjectIds) {
          const projectChars = await getCharacters(projectId)
          // Add source project info to each character
          const projectName = projects.find(p => p.id === projectId)?.name || 'Unknown Project'
          const charsWithSource = projectChars.map(c => ({
            ...c,
            _sourceProjectId: projectId,
            _sourceProjectName: projectName,
            _isFromSeries: true
          }))
          allSeriesChars.push(...charsWithSource)
        }
        
        setSeriesCharacters(allSeriesChars)
      } else {
        setSeriesCharacters([])
      }
    }
    loadCharacters()
  }, [currentProjectId, currentSeriesId, currentSeriesProjects])
  
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
      
      // Only change view if we're in edit mode (for new character creation)
      if (view === 'edit') {
        setView('list')
        setEditingCharacter(null)
        addNotification({ type: 'success', message: 'Character saved' })
      }
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
  
  // Handle role change
  const handleRoleChange = async (character, newRole) => {
    await saveCharacter({
      ...character,
      role: newRole,
    })
    
    // Refresh characters
    const chars = await getCharacters(currentProjectId)
    setCharacters(chars)
  }
  
  // Handle duplicate character
  const handleDuplicateCharacter = async (character) => {
    const duplicateChar = {
      ...character,
      id: undefined,
      name: `${character.name} (Copy)`,
      project_id: currentProjectId,
    }
    
    const success = await saveCharacter(duplicateChar)
    if (success) {
      const chars = await getCharacters(currentProjectId)
      setCharacters(chars)
      addNotification({ type: 'success', message: `Character duplicated` })
    }
  }
  
  // Handle delete character
  const handleDeleteCharacter = async (character) => {
    if (!confirm(`Delete "${character.name}"? This cannot be undone.`)) return
    
    console.log('Deleting character:', character)
    console.log('Character ID:', character.id, 'Type:', typeof character.id)
    
    try {
      if (!character.id) {
        addNotification({ type: 'error', message: 'Character has no ID - cannot delete' })
        return
      }
      
      // Try to use deleteCharacter if available
      if (deleteCharacter) {
        console.log('Calling deleteCharacter with id:', character.id)
        const result = await deleteCharacter(character.id)
        console.log('Delete result:', result)
        
        if (result === false) {
          addNotification({ type: 'error', message: 'Failed to delete character from database' })
          return
        }
      } else {
        addNotification({ type: 'error', message: 'Delete function not available' })
        return
      }
      
      const chars = await getCharacters(currentProjectId)
      setCharacters(chars)
      addNotification({ type: 'success', message: 'Character deleted' })
    } catch (error) {
      console.error('Delete error:', error)
      addNotification({ type: 'error', message: `Failed to delete character: ${error.message}` })
    }
  }
  
  // Handle AI rewrite for a field
  const handleRewriteField = async (fieldId, currentValue, instruction, characterName) => {
    if (!isElectronApi) {
      addNotification({ type: 'warning', message: 'AI rewrite requires the Python backend' })
      return null
    }
    
    if (!currentValue?.trim()) {
      addNotification({ type: 'warning', message: 'Please add some content first before rewriting' })
      return null
    }
    
    try {
      // Build a prompt for the AI to rewrite the field
      const fieldLabels = {
        pronouns: 'Pronouns',
        personality_traits: 'Personality Traits',
        physical_description: 'Physical Description',
        backstory: 'Backstory',
        motivations: 'Motivations',
        internal_conflicts: 'Internal Conflicts',
        strengths: 'Strengths',
        weaknesses: 'Weaknesses',
        speech_pattern: 'Speech Pattern',
        character_arc: 'Character Arc',
      }
      
      const fieldLabel = fieldLabels[fieldId] || fieldId
      
      // Use the plugin response API to rewrite
      const prompt = `You are helping rewrite a character's ${fieldLabel} for "${characterName}".

Current content:
${currentValue}

User's instruction for improvement:
${instruction}

Please rewrite the ${fieldLabel} following the user's instruction. Keep it concise and well-written. Only output the rewritten content, no explanations or formatting.`

      const result = await window.api.generatePluginResponse(prompt, 'rewrite', { genre: 'fiction' })
      
      if (result && !result.error) {
        addNotification({ type: 'success', message: `${fieldLabel} rewritten` })
        return result
      } else {
        addNotification({ type: 'error', message: result?.error || 'Failed to rewrite' })
        return null
      }
    } catch (error) {
      console.error('Rewrite error:', error)
      addNotification({ type: 'error', message: 'Failed to rewrite field' })
      return null
    }
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
      {/* Section Header - Collapsible */}
      <div className="bg-dark-800/80 rounded-xl shadow-lg shadow-black/20 border border-gold-rich/20 mb-4 backdrop-blur-sm">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gold-rich/10">
          <button
            className="flex items-center gap-3 text-left"
            onClick={() => setIsSectionExpanded(!isSectionExpanded)}
          >
            <span className="text-gold-rich/60 text-sm">
              {isSectionExpanded ? Icons.COLLAPSE : Icons.EXPAND}
            </span>
            <span className="text-lg">{Icons.PERSON}</span>
            <span className="font-semibold text-gold-rich">Characters</span>
          </button>
          
          <div className="flex items-center gap-2">
            {/* Add Character Button */}
            <button
              className="flex items-center gap-1 text-gold-rich hover:text-gold-amber font-medium text-sm transition-colors"
              onClick={handleCreateBlankCharacter}
            >
              <span>+</span>
              <span>Add Character</span>
            </button>
            
            {/* Section Menu */}
            <div className="relative" ref={sectionMenuRef}>
              <button
                className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
                onClick={() => setShowSectionMenu(!showSectionMenu)}
              >
                {Icons.MORE}
              </button>
              
              {showSectionMenu && (
                <div className="absolute right-0 top-full mt-1 bg-dark-800 rounded-xl shadow-lg shadow-black/50 border border-gold-rich/20 min-w-[180px] py-2 z-50">
                  <button
                    className="w-full px-4 py-2 text-left text-sm text-text-secondary hover:bg-gold-rich/10 hover:text-gold-rich flex items-center gap-2"
                    onClick={() => {
                      setShowGenerateModal(true)
                      setShowSectionMenu(false)
                    }}
                  >
                    {Icons.MAGIC} Generate with AI
                  </button>
                  <button
                    className="w-full px-4 py-2 text-left text-sm text-text-secondary hover:bg-gold-rich/10 hover:text-gold-rich flex items-center gap-2"
                    onClick={() => {
                      setShowImportModal(true)
                      setShowSectionMenu(false)
                    }}
                  >
                    {Icons.IMPORT} Import CSV
                  </button>
                  <button
                    className="w-full px-4 py-2 text-left text-sm text-text-secondary hover:bg-gold-rich/10 hover:text-gold-rich flex items-center gap-2"
                    onClick={() => {
                      handleExport()
                      setShowSectionMenu(false)
                    }}
                  >
                    {Icons.EXPORT} Export CSV
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Character List */}
        {isSectionExpanded && (
          <div className="max-h-[calc(100vh-250px)] overflow-y-auto">
            {characters.length === 0 && seriesCharacters.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-5xl mb-4 opacity-50">👥</div>
                <h2 className="text-lg font-semibold text-text-primary mb-2">
                  No Characters Yet
                </h2>
                <p className="text-text-muted mb-4 text-sm">
                  Create your first character to start building your story's cast.
                </p>
                <div className="flex items-center justify-center gap-3">
                  <button
                    className="px-4 py-2 rounded-lg bg-dark-700 border border-gold-rich/20 text-text-secondary hover:bg-gold-rich/10 hover:text-gold-rich hover:border-gold-rich/40 text-sm font-medium flex items-center gap-2 transition-colors"
                    onClick={() => setShowGenerateModal(true)}
                  >
                    {Icons.MAGIC} Generate with AI
                  </button>
                  <button
                    className="px-4 py-2 rounded-lg bg-gradient-to-r from-gold-rich to-gold-deep text-dark-950 hover:from-gold-amber hover:to-gold-rich text-sm font-medium flex items-center gap-2 shadow-gold-sm transition-all"
                    onClick={handleCreateBlankCharacter}
                  >
                    {Icons.PLUS} Create Manually
                  </button>
                </div>
              </div>
            ) : (
              <>
                {/* Current Project Characters */}
                {characters.length > 0 && (
                  <>
                    {isInSeries && (
                      <div className="px-4 py-2 text-xs font-semibold text-gold-pale/70 uppercase tracking-wider bg-dark-750/50 border-b border-gold-rich/10">
                        This Project ({characters.length})
                      </div>
                    )}
                    {characters.map(character => (
                      <CharacterRow
                        key={character.id || character.name}
                        character={character}
                        onToggleVisibility={handleToggleVisibility}
                        onDuplicate={handleDuplicateCharacter}
                        onDelete={handleDeleteCharacter}
                        onRoleChange={handleRoleChange}
                        onSave={handleSaveCharacter}
                        onRewriteField={handleRewriteField}
                      />
                    ))}
                  </>
                )}
                
                {/* Series Characters from other projects */}
                {isInSeries && seriesCharacters.length > 0 && (
                  <>
                    <div className="px-4 py-2 text-xs font-semibold text-gold-pale/70 uppercase tracking-wider bg-dark-750/50 border-y border-gold-rich/10 flex items-center gap-2">
                      <span className="text-base">🔗</span>
                      <span>Shared from Series ({seriesCharacters.length})</span>
                    </div>
                    {seriesCharacters.map(character => (
                      <CharacterRow
                        key={`series-${character._sourceProjectId}-${character.id || character.name}`}
                        character={character}
                        onToggleVisibility={handleToggleVisibility}
                        onDuplicate={handleDuplicateCharacter}
                        onDelete={handleDeleteCharacter}
                        onRoleChange={handleRoleChange}
                        onSave={handleSaveCharacter}
                        onRewriteField={handleRewriteField}
                        isFromSeries={true}
                        sourceProjectName={character._sourceProjectName}
                      />
                    ))}
                  </>
                )}
              </>
            )}
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
