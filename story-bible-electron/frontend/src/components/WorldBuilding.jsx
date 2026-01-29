/**
 * World Building Component
 * ========================
 * Manages world building elements with Sudowrite-style expandable list.
 * Dark & Gold luxury theme
 */

import { useState, useEffect, useRef } from 'react'
import useStore from '../hooks/useStore'
import { usePythonBridge } from '../hooks/usePythonBridge'
import { clsx } from 'clsx'

// Icons
const Icons = {
  WORLD: '🌍',
  PLUS: '+',
  DELETE: '🗑️',
  VISIBLE: '👁️',
  HIDDEN: '👁️‍🗨️',
  AI: '🤖',
  MORE: '⋯',
  DRAG: '⋮⋮',
  EXPAND: '▶',
  COLLAPSE: '▼',
  COPY: '📋',
  CLOCK: '🕐',
  CLOSE: '✕',
  MAGIC: '🪄',
}

// Element types
const ELEMENT_TYPES = [
  { id: 'location', label: 'Location' },
  { id: 'setting', label: 'Setting' },
  { id: 'event', label: 'Event' },
  { id: 'system', label: 'System' },
  { id: 'item', label: 'Item' },
  { id: 'lore', label: 'Lore' },
  { id: 'magic', label: 'Magic' },
  { id: 'other', label: 'Other' },
]

// Editable field with AI rewrite capability
function EditableField({ label, value, onChange, onSave, onRewrite, placeholder, isRewriting }) {
  const [isFocused, setIsFocused] = useState(false)
  const [showRewriteInput, setShowRewriteInput] = useState(false)
  const [rewriteInstruction, setRewriteInstruction] = useState('')
  const containerRef = useRef(null)
  const textareaRef = useRef(null)
  
  // Auto-resize textarea based on content
  const autoResize = () => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.max(80, textarea.scrollHeight)}px`
    }
  }
  
  useEffect(() => {
    autoResize()
  }, [value])
  
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
  
  // Handle clicks outside to close
  useEffect(() => {
    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        if (!showRewriteInput) {
          setIsFocused(false)
          onSave()
        }
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showRewriteInput, onSave])
  
  return (
    <div 
      ref={containerRef}
      className={clsx(
        "rounded-xl p-4 border transition-all",
        isFocused || showRewriteInput
          ? "bg-dark-700/50 border-gold-rich/40"
          : "bg-dark-800/50 border-gold-rich/10"
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-medium text-gold-pale">{label}</label>
        <button
          className="w-6 h-6 flex items-center justify-center rounded text-gray-500 hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
          title="More options"
        >
          {Icons.MORE}
        </button>
      </div>
      
      <div className="relative">
        <textarea
          ref={textareaRef}
          className={clsx(
            "w-full px-3 py-3 text-sm bg-dark-750 border border-gold-rich/20 rounded-lg text-gray-200 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gold-rich/30 focus:border-gold-rich/40 min-h-[80px] resize-none transition-all overflow-hidden",
            isRewriting ? "opacity-50" : ""
          )}
          value={value || ''}
          onChange={(e) => {
            onChange(e.target.value)
            autoResize()
          }}
          onFocus={() => setIsFocused(true)}
          placeholder={placeholder}
          disabled={isRewriting}
        />
        
        <button
          className="absolute top-3 right-3 w-6 h-6 flex items-center justify-center rounded text-gray-500 hover:text-gold-rich transition-colors"
          title="Toggle visibility"
        >
          {Icons.VISIBLE}
        </button>
        
        {isRewriting && (
          <div className="absolute inset-0 flex items-center justify-center bg-dark-800/80 rounded-lg">
            <div className="flex items-center gap-2 text-gold-rich">
              <div className="w-5 h-5 border-2 border-gold-rich/20 border-t-gold-rich rounded-full animate-spin" />
              <span className="text-sm font-medium">Rewriting...</span>
            </div>
          </div>
        )}
      </div>
      
      {/* Rewrite Button - Shows when focused */}
      {isFocused && !showRewriteInput && !isRewriting && (
        <button
          className="mt-3 flex items-center gap-1.5 text-sm text-gold-rich hover:text-gold-amber font-medium transition-colors"
          onClick={() => setShowRewriteInput(true)}
        >
          <span className="text-base">✨</span>
          <span>Rewrite...</span>
        </button>
      )}
      
      {/* Rewrite Input */}
      {showRewriteInput && !isRewriting && (
        <div className="mt-3">
          {!value?.trim() && (
            <p className="text-xs text-amber-400 mb-2">Please add some content first before rewriting</p>
          )}
          <div className="flex items-center gap-2">
            <input
              type="text"
              className="flex-1 px-3 py-2.5 text-sm bg-dark-750 border border-gold-rich/20 rounded-lg text-gray-200 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gold-rich/30 focus:border-gold-rich/40"
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
                  ? 'bg-gradient-to-r from-gold-rich to-gold-deep text-dark-950 hover:from-gold-amber hover:to-gold-rich'
                  : 'bg-dark-600 text-gray-500 cursor-not-allowed'
              )}
              onClick={handleRewrite}
              disabled={!rewriteInstruction.trim() || !value?.trim() || isRewriting}
            >
              <span>Go</span>
              <span className="text-xs bg-white/20 px-1.5 py-0.5 rounded">ctrl</span>
              <span className="text-xs">↵</span>
            </button>
          </div>
          <button
            className="mt-2 text-xs text-gray-500 hover:text-gray-300 transition-colors"
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

// World Element Row Component
function WorldElementRow({ element, onToggleVisibility, onDuplicate, onDelete, onSave, onRewriteField }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const [menuPosition, setMenuPosition] = useState({ top: 0, right: 0 })
  const [editData, setEditData] = useState(element)
  const [isDirty, setIsDirty] = useState(false)
  const [rewritingField, setRewritingField] = useState(null)
  const menuRef = useRef(null)
  const menuButtonRef = useRef(null)
  const isVisible = element.is_visible !== 0
  
  useEffect(() => {
    setEditData(element)
    setIsDirty(false)
  }, [element])
  
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
      onSave(editData)
      setIsDirty(false)
    }
  }
  
  const handleNameBlur = () => {
    if (isDirty && editData.name?.trim()) {
      handleSave()
    }
  }
  
  const handleRewrite = async (field, instruction) => {
    if (!onRewriteField) return
    
    setRewritingField(field)
    try {
      const rewritten = await onRewriteField(field, editData[field], instruction, editData.name)
      if (rewritten) {
        handleChange(field, rewritten)
        const newData = { ...editData, [field]: rewritten }
        onSave(newData)
      }
    } finally {
      setRewritingField(null)
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
          {isExpanded ? Icons.COLLAPSE : Icons.EXPAND}
        </button>
        
        {/* Element Name - Editable */}
        <input
          type="text"
          className="flex-1 font-medium text-gold-soft bg-transparent border-none focus:outline-none focus:ring-0 hover:bg-dark-700 focus:bg-dark-700 px-2 py-1 rounded"
          value={editData.name || ''}
          onChange={(e) => handleChange('name', e.target.value)}
          onBlur={handleNameBlur}
          placeholder="Element name..."
        />
        
        {/* Type Dropdown */}
        <div className="relative">
          <select
            className="appearance-none bg-dark-700 border border-gold-rich/20 rounded-lg px-3 py-1.5 text-sm text-gray-300 cursor-pointer hover:bg-dark-600 focus:outline-none focus:ring-2 focus:ring-gold-rich/30 pr-8"
            value={editData.element_type || 'other'}
            onChange={(e) => {
              handleChange('element_type', e.target.value)
              onSave({ ...editData, element_type: e.target.value })
            }}
          >
            {ELEMENT_TYPES.map(type => (
              <option key={type.id} value={type.id}>{type.label}</option>
            ))}
          </select>
          <span className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-gray-500 text-xs">▼</span>
        </div>
        
        {/* Action Icons */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            className={clsx(
              'w-8 h-8 flex items-center justify-center rounded-lg transition-colors',
              isVisible
                ? 'text-gray-500 hover:text-green-400 hover:bg-green-400/10'
                : 'text-red-400 hover:text-red-300 hover:bg-red-400/10'
            )}
            onClick={() => onToggleVisibility(element)}
            title={isVisible ? 'Visible to AI' : 'Hidden from AI'}
          >
            {isVisible ? Icons.VISIBLE : Icons.HIDDEN}
          </button>
          
          <button
            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-500 hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
            title="History"
          >
            {Icons.CLOCK}
          </button>
          
          <button
            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-500 hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
            onClick={() => onDuplicate(element)}
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
                    onDuplicate(element)
                    setShowMenu(false)
                  }}
                >
                  {Icons.COPY} Duplicate
                </button>
                <button
                  className="w-full px-4 py-2 text-left text-sm text-red-400 hover:bg-red-400/10 flex items-center gap-2"
                  onClick={() => {
                    onDelete(element)
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
            {/* Other Names */}
            <div>
              <label className="block text-sm font-medium text-gold-pale mb-2">Other Names</label>
              <input
                type="text"
                className="w-full px-3 py-2.5 text-sm bg-dark-750 border border-gold-rich/20 rounded-lg text-gray-200 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gold-rich/30"
                value={editData.other_names || ''}
                onChange={(e) => handleChange('other_names', e.target.value)}
                onBlur={handleSave}
                placeholder="Alternative names, aliases..."
              />
            </div>
            
            {/* Description */}
            <EditableField
              label="Description"
              value={editData.description}
              onChange={(value) => handleChange('description', value)}
              onSave={handleSave}
              onRewrite={(instruction) => handleRewrite('description', instruction)}
              placeholder="Describe this element in detail..."
              isRewriting={rewritingField === 'description'}
            />
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

// AI Generation Modal
function GenerateElementModal({ isOpen, onClose, onGenerate, isGenerating }) {
  const [description, setDescription] = useState('')
  const [elementType, setElementType] = useState('location')
  
  const handleSubmit = () => {
    if (description.trim().length >= 10) {
      onGenerate(description, elementType)
    }
  }
  
  useEffect(() => {
    if (!isOpen) {
      setDescription('')
      setElementType('location')
    }
  }, [isOpen])
  
  if (!isOpen) return null
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 w-full max-w-lg mx-4 glass-card p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-100 flex items-center gap-2">
            {Icons.MAGIC} Generate Element with AI
          </h2>
          <button
            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-500 hover:text-gold-rich hover:bg-gold-rich/10"
            onClick={onClose}
          >
            {Icons.CLOSE}
          </button>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gold-pale mb-2">Element Type</label>
            <select
              className="w-full px-3 py-2.5 bg-dark-750 border border-gold-rich/20 rounded-lg text-gray-200 focus:outline-none focus:ring-2 focus:ring-gold-rich/30"
              value={elementType}
              onChange={(e) => setElementType(e.target.value)}
              disabled={isGenerating}
            >
              {ELEMENT_TYPES.map(type => (
                <option key={type.id} value={type.id}>{type.label}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gold-pale mb-2">Description</label>
            <textarea
              className="w-full px-3 py-3 bg-dark-750 border border-gold-rich/20 rounded-lg text-gray-200 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gold-rich/30 min-h-[120px] resize-none"
              placeholder="Describe the element you want to create (min 10 characters)..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={isGenerating}
            />
            <p className="text-xs text-gray-500 mt-1">{description.length}/10 characters minimum</p>
          </div>
        </div>
        
        <div className="flex items-center justify-end gap-3 mt-6">
          <button
            className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200"
            onClick={onClose}
            disabled={isGenerating}
          >
            Cancel
          </button>
          <button
            className={clsx(
              'px-6 py-2.5 rounded-lg text-sm font-medium flex items-center gap-2 transition-all',
              description.trim().length >= 10
                ? 'bg-gradient-to-r from-gold-rich to-gold-deep text-dark-950 hover:from-gold-amber hover:to-gold-rich'
                : 'bg-dark-600 text-gray-500 cursor-not-allowed'
            )}
            onClick={handleSubmit}
            disabled={description.trim().length < 10 || isGenerating}
          >
            {isGenerating ? (
              <>
                <div className="w-4 h-4 border-2 border-dark-950/30 border-t-dark-950 rounded-full animate-spin" />
                <span>Generating...</span>
              </>
            ) : (
              <>
                <span>{Icons.MAGIC}</span>
                <span>Generate</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

// Create Element Modal
function CreateElementModal({ isOpen, onClose, onCreate }) {
  const [name, setName] = useState('')
  const [elementType, setElementType] = useState('location')
  const [isCreating, setIsCreating] = useState(false)
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    
    setIsCreating(true)
    try {
      await onCreate(name.trim(), elementType)
      setName('')
      setElementType('location')
      onClose()
    } finally {
      setIsCreating(false)
    }
  }
  
  useEffect(() => {
    if (!isOpen) {
      setName('')
      setElementType('location')
    }
  }, [isOpen])
  
  if (!isOpen) return null
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 w-full max-w-md mx-4 glass-card p-6">
        <h2 className="text-xl font-semibold text-gray-100 mb-6">Create New Element</h2>
        
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gold-pale mb-2">Element Name *</label>
              <input
                type="text"
                className="w-full px-3 py-2.5 bg-dark-750 border border-gold-rich/20 rounded-lg text-gray-200 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gold-rich/30"
                placeholder="Enter element name..."
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
                disabled={isCreating}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gold-pale mb-2">Type</label>
              <select
                className="w-full px-3 py-2.5 bg-dark-750 border border-gold-rich/20 rounded-lg text-gray-200 focus:outline-none focus:ring-2 focus:ring-gold-rich/30"
                value={elementType}
                onChange={(e) => setElementType(e.target.value)}
                disabled={isCreating}
              >
                {ELEMENT_TYPES.map(type => (
                  <option key={type.id} value={type.id}>{type.label}</option>
                ))}
              </select>
            </div>
          </div>
          
          <div className="flex items-center justify-end gap-3 mt-6">
            <button
              type="button"
              className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200"
              onClick={onClose}
              disabled={isCreating}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={clsx(
                'px-6 py-2.5 rounded-lg text-sm font-medium transition-all',
                name.trim()
                  ? 'bg-gradient-to-r from-gold-rich to-gold-deep text-dark-950 hover:from-gold-amber hover:to-gold-rich'
                  : 'bg-dark-600 text-gray-500 cursor-not-allowed'
              )}
              disabled={!name.trim() || isCreating}
            >
              {isCreating ? (
                <span className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-dark-950/30 border-t-dark-950 rounded-full animate-spin" />
                  Creating...
                </span>
              ) : (
                'Create Element'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function WorldBuilding() {
  const { currentProjectId, addNotification } = useStore()
  const { 
    getWorldElements, 
    createWorldElement, 
    updateWorldElement, 
    deleteWorldElement,
    isElectronApi,
  } = usePythonBridge()
  
  const [elements, setElements] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSectionExpanded, setIsSectionExpanded] = useState(true)
  const [showSectionMenu, setShowSectionMenu] = useState(false)
  const [showGenerateModal, setShowGenerateModal] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const sectionMenuRef = useRef(null)
  
  useEffect(() => {
    function handleClickOutside(event) {
      if (sectionMenuRef.current && !sectionMenuRef.current.contains(event.target)) {
        setShowSectionMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  // Load elements
  useEffect(() => {
    async function loadElements() {
      if (!currentProjectId) return
      setIsLoading(true)
      try {
        const data = await getWorldElements(currentProjectId, null, null)
        setElements(data || [])
      } catch (error) {
        console.error('Failed to load world elements:', error)
      } finally {
        setIsLoading(false)
      }
    }
    loadElements()
  }, [currentProjectId])
  
  // Create new element
  const handleCreateElement = async (name, elementType) => {
    if (!name?.trim()) {
      addNotification({ type: 'warning', message: 'Please enter a name' })
      return
    }
    
    if (!currentProjectId) {
      addNotification({ type: 'error', message: 'No project selected' })
      return
    }
    
    try {
      console.log('Creating world element:', { name, elementType, projectId: currentProjectId })
      const result = await createWorldElement(currentProjectId, { 
        name: name.trim(), 
        element_type: elementType || 'other',
        description: '',
        is_visible: 1 
      })
      console.log('Create result:', result)
      
      if (result) {
        const updated = await getWorldElements(currentProjectId, null, null)
        setElements(updated || [])
        addNotification({ type: 'success', message: `Element "${name}" created!` })
      } else {
        addNotification({ type: 'error', message: 'Failed to create element' })
      }
    } catch (error) {
      console.error('Create element error:', error)
      addNotification({ type: 'error', message: `Failed to create element: ${error.message}` })
    }
  }
  
  // Save element
  const handleSaveElement = async (data) => {
    try {
      await updateWorldElement(data.id, data)
      const updated = await getWorldElements(currentProjectId, null, null)
      setElements(updated || [])
    } catch (error) {
      console.error('Failed to save element:', error)
    }
  }
  
  // Toggle visibility
  const handleToggleVisibility = async (element) => {
    try {
      await updateWorldElement(element.id, { 
        is_visible: element.is_visible === 0 ? 1 : 0 
      })
      const updated = await getWorldElements(currentProjectId, null, null)
      setElements(updated || [])
    } catch (error) {
      console.error('Failed to toggle visibility:', error)
    }
  }
  
  // Duplicate element
  const handleDuplicateElement = async (element) => {
    try {
      await createWorldElement(currentProjectId, {
        ...element,
        id: undefined,
        name: `${element.name} (Copy)`,
      })
      const updated = await getWorldElements(currentProjectId, null, null)
      setElements(updated || [])
      addNotification({ type: 'success', message: 'Element duplicated' })
    } catch (error) {
      addNotification({ type: 'error', message: 'Failed to duplicate element' })
    }
  }
  
  // Delete element
  const handleDeleteElement = async (element) => {
    if (!confirm(`Delete "${element.name}"? This cannot be undone.`)) return
    
    try {
      await deleteWorldElement(element.id)
      const updated = await getWorldElements(currentProjectId, null, null)
      setElements(updated || [])
      addNotification({ type: 'success', message: 'Element deleted' })
    } catch (error) {
      addNotification({ type: 'error', message: 'Failed to delete element' })
    }
  }
  
  // AI rewrite field
  const handleRewriteField = async (fieldId, currentValue, instruction, elementName) => {
    if (!isElectronApi) {
      addNotification({ type: 'warning', message: 'AI rewrite requires the Python backend' })
      return null
    }
    
    if (!currentValue?.trim()) {
      addNotification({ type: 'warning', message: 'Please add content first' })
      return null
    }
    
    try {
      const prompt = `You are helping rewrite a world building element's ${fieldId} for "${elementName}".

Current content:
${currentValue}

User's instruction:
${instruction}

Please rewrite following the instruction. Only output the rewritten content.`

      const result = await window.api.generatePluginResponse(prompt, 'rewrite', { genre: 'fiction' })
      
      if (result && !result.error) {
        return result
      }
      return null
    } catch (error) {
      console.error('Rewrite error:', error)
      return null
    }
  }
  
  // Generate element with AI
  const handleGenerateElement = async (description, elementType) => {
    if (!isElectronApi) {
      addNotification({ type: 'warning', message: 'AI generation requires the Python backend' })
      return
    }
    
    setIsGenerating(true)
    try {
      const result = await window.api.generateSingleWorldElement(description, elementType, 'fiction')
      
      if (result && !result.error) {
        await createWorldElement(currentProjectId, {
          name: result.name || 'Unnamed Element',
          element_type: result.element_type || elementType,
          description: result.description || '',
          is_visible: 1,
        })
        
        const updated = await getWorldElements(currentProjectId, null, null)
        setElements(updated || [])
        setShowGenerateModal(false)
        addNotification({ type: 'success', message: `Element "${result.name}" created!` })
      } else {
        addNotification({ type: 'error', message: result?.error || 'Failed to generate' })
      }
    } catch (error) {
      addNotification({ type: 'error', message: 'Failed to generate element' })
    } finally {
      setIsGenerating(false)
    }
  }
  
  return (
    <div className="h-full flex flex-col p-6">
      {/* Section Header */}
      <div className="bg-dark-800 rounded-xl shadow-sm border border-gold-rich/10 mb-4">
        <div className="flex items-center justify-between px-4 py-4 border-b border-gold-rich/10">
          <button
            className="flex items-center gap-3 text-left"
            onClick={() => setIsSectionExpanded(!isSectionExpanded)}
          >
            <span className="text-gray-500 text-sm">
              {isSectionExpanded ? Icons.COLLAPSE : Icons.EXPAND}
            </span>
            <span className="text-2xl">{Icons.WORLD}</span>
            <div>
              <h1 className="text-xl font-semibold text-gold-soft">Worldbuilding</h1>
              <p className="text-sm text-gray-400">Bring your world to life with Locations, Lore, Magic, and more</p>
            </div>
          </button>
          
          <div className="flex items-center gap-2">
            <button
              className="flex items-center gap-1 text-gold-rich hover:text-gold-amber font-medium text-sm"
              onClick={() => setShowCreateModal(true)}
            >
              <span>+</span>
              <span>Add Element</span>
            </button>
            
            <div className="relative" ref={sectionMenuRef}>
              <button
                className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-500 hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
                onClick={() => setShowSectionMenu(!showSectionMenu)}
              >
                {Icons.MORE}
              </button>
              
              {showSectionMenu && (
                <div className="absolute right-0 top-full mt-1 bg-dark-800 rounded-xl shadow-lg border border-gold-rich/20 min-w-[180px] py-2 z-50">
                  <button
                    className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gold-rich/10 hover:text-gold-rich flex items-center gap-2"
                    onClick={() => {
                      setShowGenerateModal(true)
                      setShowSectionMenu(false)
                    }}
                  >
                    {Icons.MAGIC} Generate with AI
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Elements List */}
        {isSectionExpanded && (
          <div className="p-4 max-h-[calc(100vh-250px)] overflow-y-auto">
            {isLoading ? (
              <div className="text-center py-8">
                <div className="w-8 h-8 border-2 border-gold-rich/20 border-t-gold-rich rounded-full animate-spin mx-auto mb-3" />
                <p className="text-gray-400">Loading elements...</p>
              </div>
            ) : elements.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-5xl mb-4 opacity-50">{Icons.WORLD}</div>
                <h2 className="text-lg font-semibold text-gray-200 mb-2">No Elements Yet</h2>
                <p className="text-gray-400 mb-4 text-sm">
                  Start building your world by adding locations, lore, and more.
                </p>
                <div className="flex items-center justify-center gap-3">
                  <button
                    className="px-4 py-2 rounded-lg bg-dark-700 text-gray-300 hover:bg-dark-600 text-sm font-medium flex items-center gap-2 border border-gold-rich/20"
                    onClick={() => setShowGenerateModal(true)}
                  >
                    {Icons.MAGIC} Generate with AI
                  </button>
                  <button
                    className="px-4 py-2 rounded-lg bg-gradient-to-r from-gold-rich to-gold-deep text-dark-950 hover:from-gold-amber hover:to-gold-rich text-sm font-medium flex items-center gap-2"
                    onClick={() => setShowCreateModal(true)}
                  >
                    {Icons.PLUS} Create Manually
                  </button>
                </div>
              </div>
            ) : (
              elements.map(element => (
                <WorldElementRow
                  key={element.id}
                  element={element}
                  onToggleVisibility={handleToggleVisibility}
                  onDuplicate={handleDuplicateElement}
                  onDelete={handleDeleteElement}
                  onSave={handleSaveElement}
                  onRewriteField={handleRewriteField}
                />
              ))
            )}
          </div>
        )}
      </div>
      
      {/* Create Modal */}
      <CreateElementModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreateElement}
      />
      
      {/* Generate Modal */}
      <GenerateElementModal
        isOpen={showGenerateModal}
        onClose={() => setShowGenerateModal(false)}
        onGenerate={handleGenerateElement}
        isGenerating={isGenerating}
      />
    </div>
  )
}

export default WorldBuilding
