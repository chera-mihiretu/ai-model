/**
 * World Building Component
 * ========================
 * Manages world building elements (settings, locations, events, etc.)
 * Similar to character management but for non-character story elements.
 */

import { useState, useEffect, useRef } from 'react'
import useStore from '../hooks/useStore'
import { usePythonBridge } from '../hooks/usePythonBridge'
import { clsx } from 'clsx'

// Icons
const Icons = {
  WORLD: '🌍',
  LOCATION: '📍',
  EVENT: '📅',
  SYSTEM: '⚙️',
  ITEM: '🏺',
  OTHER: '📦',
  PLUS: '+',
  DELETE: '🗑️',
  EDIT: '✏️',
  SAVE: '💾',
  VISIBLE: '👁️',
  HIDDEN: '👁️‍🗨️',
  IMPORT: '📥',
  EXPORT: '📤',
  AI: '🤖',
  FILTER: '🔍',
}

// Element types with their icons and labels
const ELEMENT_TYPES = [
  { id: 'all', label: 'All Elements', icon: Icons.WORLD },
  { id: 'setting', label: 'Settings', icon: '🏙️' },
  { id: 'location', label: 'Locations', icon: Icons.LOCATION },
  { id: 'event', label: 'Events', icon: Icons.EVENT },
  { id: 'system', label: 'Systems', icon: Icons.SYSTEM },
  { id: 'item', label: 'Items', icon: Icons.ITEM },
  { id: 'other', label: 'Other', icon: Icons.OTHER },
]

// Element fields for the editor
const ELEMENT_FIELDS = [
  { id: 'name', label: 'Name', type: 'text', required: true, placeholder: 'Enter element name...' },
  { id: 'element_type', label: 'Type', type: 'select', options: ELEMENT_TYPES.filter(t => t.id !== 'all') },
  { id: 'description', label: 'Description', type: 'textarea', placeholder: 'Describe this element...' },
  { id: 'sensory_details', label: 'Sensory Details', type: 'textarea', placeholder: 'Sights, sounds, smells, textures...' },
  { id: 'significance', label: 'Story Significance', type: 'textarea', placeholder: 'Why is this important to the story?' },
  { id: 'custom_traits', label: 'Custom Traits', type: 'textarea', placeholder: 'JSON or key-value pairs for custom properties...' },
]

function WorldElementCard({ element, isSelected, onClick, onToggleVisibility, onDelete }) {
  const isVisible = element.is_visible !== 0
  const typeInfo = ELEMENT_TYPES.find(t => t.id === element.element_type) || ELEMENT_TYPES[6]
  
  return (
    <div
      className={clsx(
        'p-4 rounded-xl cursor-pointer transition-all duration-200',
        'bg-gradient-to-br from-bg-card/90 to-bg-sidebar/90',
        'border border-glass-border',
        'hover:border-accent-primary hover:shadow-lg hover:shadow-accent-primary/20',
        'hover:-translate-y-1',
        isSelected && 'border-accent-primary ring-2 ring-accent-primary/30'
      )}
      onClick={() => onClick(element)}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{typeInfo.icon}</span>
          <div>
            <h3 className="font-semibold text-text-primary">{element.name}</h3>
            <p className="text-xs text-text-muted">{typeInfo.label}</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            className={clsx(
              'w-7 h-7 flex items-center justify-center rounded-lg transition-colors text-sm',
              isVisible
                ? 'bg-green-500/20 text-green-400'
                : 'bg-red-500/20 text-red-400'
            )}
            onClick={(e) => {
              e.stopPropagation()
              onToggleVisibility(element)
            }}
            title={isVisible ? 'Visible to AI' : 'Hidden from AI'}
          >
            {isVisible ? Icons.VISIBLE : Icons.HIDDEN}
          </button>
          <button
            className="w-7 h-7 flex items-center justify-center rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors text-sm"
            onClick={(e) => {
              e.stopPropagation()
              onDelete(element)
            }}
            title="Delete"
          >
            {Icons.DELETE}
          </button>
        </div>
      </div>
      
      {/* Preview */}
      {element.description && (
        <p className="text-sm text-text-secondary line-clamp-2 mb-2">
          {element.description}
        </p>
      )}
      
      {/* Tags */}
      {element.significance && (
        <div className="mt-2 pt-2 border-t border-border/30">
          <p className="text-xs text-accent-secondary line-clamp-1">
            📌 {element.significance}
          </p>
        </div>
      )}
    </div>
  )
}

function WorldElementEditor({ element, onSave, onClose }) {
  const [formData, setFormData] = useState(element || { element_type: 'other' })
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
          {element?.id ? 'Edit Element' : 'New World Element'}
        </h2>
        <div className="flex items-center gap-2">
          <button className="btn btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button
            className={clsx('btn btn-primary', !isDirty && 'opacity-50')}
            onClick={handleSave}
            disabled={!isDirty || !formData.name?.trim()}
          >
            <span>{Icons.SAVE}</span>
            <span>Save</span>
          </button>
        </div>
      </div>
      
      {/* Form */}
      <div className="flex-1 overflow-y-auto pr-2 space-y-4">
        {ELEMENT_FIELDS.map(field => (
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
            ) : field.type === 'select' ? (
              <select
                className="input"
                value={formData[field.id] || 'other'}
                onChange={(e) => handleChange(field.id, e.target.value)}
              >
                {field.options.map(opt => (
                  <option key={opt.id} value={opt.id}>
                    {opt.icon} {opt.label}
                  </option>
                ))}
              </select>
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

// AI Generation Modal for World Elements
function GenerateElementModal({ isOpen, onClose, onGenerate, isGenerating, error, clearError }) {
  const [description, setDescription] = useState('')
  const [elementType, setElementType] = useState('location')
  const [genre, setGenre] = useState('Fantasy')
  
  const genres = ['Fantasy', 'Sci-Fi', 'Romance', 'Thriller', 'Mystery', 'Horror', 'Historical', 'Literary', 'Urban Fantasy', 'Post-Apocalyptic']
  
  const inspirationPrompts = {
    location: [
      "A hidden underground city lit by bioluminescent fungi",
      "An abandoned space station orbiting a dying star",
      "A floating market on a river delta at sunset",
      "A cursed forest where time moves backwards",
    ],
    setting: [
      "A world where magic is powered by emotions",
      "A steampunk Victorian society on the brink of revolution",
      "A medieval kingdom ruled by a council of dragons",
      "A cyberpunk megacity built on the ruins of the old world",
    ],
    event: [
      "The day the sun turned black and never recovered",
      "A royal wedding interrupted by an ancient prophecy",
      "The discovery of a portal to another dimension",
      "A plague that grants supernatural abilities",
    ],
    system: [
      "A magic system based on musical notes and harmony",
      "A political structure with five competing noble houses",
      "An economic system where memories are currency",
      "A religious hierarchy centered around elemental spirits",
    ],
    item: [
      "A sword that whispers the secrets of those it kills",
      "An ancient map that reveals hidden pathways",
      "A crown that corrupts anyone who wears it",
      "A mechanical heart that grants immortality",
    ],
    other: [
      "A mysterious organization pulling strings from the shadows",
      "An ancient language that can reshape reality when spoken",
      "A phenomenon where dreams become physically real",
      "A creature that exists between worlds",
    ],
  }
  
  const currentPrompts = inspirationPrompts[elementType] || inspirationPrompts.other
  
  const handleSubmit = () => {
    if (description.trim().length < 10) return
    onGenerate(description, elementType, genre)
  }
  
  useEffect(() => {
    if (isOpen) {
      setDescription('')
      setElementType('location')
      setGenre('Fantasy')
      clearError()
    }
  }, [isOpen])
  
  if (!isOpen) return null
  
  const elementTypeOptions = ELEMENT_TYPES.filter(t => t.id !== 'all')
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 w-full max-w-2xl mx-4 glass-card p-6 animate-slide-up overflow-y-auto max-h-[90vh]">
        <h2 className="text-xl font-semibold text-text-primary mb-6 flex items-center gap-2">
          {Icons.AI} Generate World Element with AI
        </h2>

        {error && (
          <div className="bg-red-500/20 text-red-400 p-3 rounded-lg mb-4 flex items-center gap-2">
            <span>⚠️</span>
            <span>Error: {error}</span>
          </div>
        )}

        <div className="mb-4">
          <label className="block text-sm font-medium text-text-secondary mb-2">
            Element Description <span className="text-red-400">*</span>
          </label>
          <textarea
            className="input-textarea min-h-[120px]"
            placeholder="Describe the world element you want to create (e.g., 'A haunted castle on a cliff')."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows="4"
            disabled={isGenerating}
          />
          <p className="text-xs text-text-muted mt-1">
            {description.length} characters (min 10)
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Element Type
            </label>
            <select
              className="input"
              value={elementType}
              onChange={(e) => setElementType(e.target.value)}
              disabled={isGenerating}
            >
              {elementTypeOptions.map(t => (
                <option key={t.id} value={t.id}>{t.icon} {t.label}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Story Genre
            </label>
            <select
              className="input"
              value={genre}
              onChange={(e) => setGenre(e.target.value)}
              disabled={isGenerating}
            >
              {genres.map(g => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="mb-6">
          <p className="text-sm font-medium text-text-secondary mb-2">Inspiration Prompts:</p>
          <div className="flex flex-wrap gap-2">
            {currentPrompts.map((prompt, index) => (
              <button
                key={index}
                className="px-3 py-1 text-xs rounded-full bg-bg-card/60 text-text-muted hover:bg-bg-hover hover:text-text-primary transition-colors text-left"
                onClick={() => setDescription(prompt)}
                disabled={isGenerating}
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-end gap-3">
          <button type="button" className="btn btn-ghost" onClick={onClose} disabled={isGenerating}>
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={isGenerating || description.trim().length < 10}
          >
            {isGenerating ? (
              <><div className="spinner !w-4 !h-4 mr-2" /> Generating...</>
            ) : (
              <><span>{Icons.AI}</span> Generate Element</>
            )}
          </button>
        </div>
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
  
  if (!isOpen) return null
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="glass-card p-6 w-full max-w-2xl">
        <h2 className="text-xl font-bold text-text-primary mb-4">Import World Elements from CSV</h2>
        
        <div className="mb-4">
          <p className="text-text-muted text-sm mb-2">
            CSV format: name,element_type,description,sensory_details,significance,custom_traits
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
            Import Elements
          </button>
        </div>
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
    exportWorldElementsCsv,
    importWorldElementsCsv,
    generateSingleWorldElement,
    isElectronApi,
    isApiAvailable
  } = usePythonBridge()
  
  const [elements, setElements] = useState([])
  const [selectedType, setSelectedType] = useState('all')
  const [view, setView] = useState('list') // 'list' | 'edit'
  const [editingElement, setEditingElement] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [showImportModal, setShowImportModal] = useState(false)
  const [showGenerateModal, setShowGenerateModal] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generateError, setGenerateError] = useState('')
  
  // Load world elements
  useEffect(() => {
    async function loadElements() {
      if (!currentProjectId) return
      setIsLoading(true)
      
      try {
        const data = await getWorldElements(currentProjectId, null, null)
        setElements(data || [])
      } catch (error) {
        console.error('Failed to load world elements:', error)
        addNotification({ type: 'error', message: 'Failed to load world elements' })
      } finally {
        setIsLoading(false)
      }
    }
    loadElements()
  }, [currentProjectId, getWorldElements, addNotification])
  
  // Filter elements by type
  const filteredElements = selectedType === 'all' 
    ? elements 
    : elements.filter(e => e.element_type === selectedType)
  
  // Handle create new element
  const handleCreateElement = () => {
    setEditingElement({ element_type: 'other' })
    setView('edit')
  }
  
  // Handle save element
  const handleSaveElement = async (data) => {
    try {
      if (data.id) {
        // Update existing
        await updateWorldElement(data.id, data)
        addNotification({ type: 'success', message: 'Element updated' })
      } else {
        // Create new
        await createWorldElement(currentProjectId, data)
        addNotification({ type: 'success', message: 'Element created' })
      }
      
      // Refresh list
      const updated = await getWorldElements(currentProjectId, null, null)
      setElements(updated || [])
      setView('list')
      setEditingElement(null)
    } catch (error) {
      console.error('Failed to save element:', error)
      addNotification({ type: 'error', message: 'Failed to save element' })
    }
  }
  
  // Handle toggle visibility
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
  
  // Handle delete element
  const handleDeleteElement = async (element) => {
    if (!confirm(`Delete "${element.name}"? This cannot be undone.`)) return
    
    try {
      await deleteWorldElement(element.id)
      addNotification({ type: 'success', message: 'Element deleted' })
      
      const updated = await getWorldElements(currentProjectId, null, null)
      setElements(updated || [])
    } catch (error) {
      console.error('Failed to delete element:', error)
      addNotification({ type: 'error', message: 'Failed to delete element' })
    }
  }
  
  // Handle edit element
  const handleEditElement = (element) => {
    setEditingElement(element)
    setView('edit')
  }
  
  // Handle CSV export
  const handleExport = async () => {
    try {
      const csvData = await exportWorldElementsCsv(currentProjectId)
      if (!csvData) {
        addNotification({ type: 'warning', message: 'No elements to export' })
        return
      }
      
      // Download CSV
      const blob = new Blob([csvData], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'world_elements.csv'
      a.click()
      URL.revokeObjectURL(url)
      
      addNotification({ type: 'success', message: 'Elements exported' })
    } catch (error) {
      console.error('Failed to export:', error)
      addNotification({ type: 'error', message: 'Failed to export elements' })
    }
  }
  
  // Handle CSV import
  const handleImport = async (csvData) => {
    try {
      const result = await importWorldElementsCsv(currentProjectId, csvData)
      
      if (result.imported > 0) {
        addNotification({ type: 'success', message: `Imported ${result.imported} elements` })
      }
      if (result.errors?.length > 0) {
        addNotification({ type: 'warning', message: `${result.errors.length} errors during import` })
      }
      
      // Refresh list
      const updated = await getWorldElements(currentProjectId, null, null)
      setElements(updated || [])
    } catch (error) {
      console.error('Failed to import:', error)
      addNotification({ type: 'error', message: 'Failed to import elements' })
    }
  }
  
  // Handle AI generate element
  const handleGenerateElement = async (description, elementType, genre) => {
    if (!isElectronApi) {
      setGenerateError('AI generation requires the full Electron app with Python backend.')
      return
    }
    if (!currentProjectId) {
      setGenerateError('Please select a project first.')
      return
    }

    setIsGenerating(true)
    setGenerateError('')
    try {
      console.log('Generating world element:', { description, elementType, genre })
      const result = await generateSingleWorldElement(description, elementType, genre)
      console.log('AI Generation Result:', result)

      if (result && !result.error) {
        const elementToSave = {
          name: result.name || 'Unnamed Element',
          element_type: result.element_type || elementType,
          description: result.description || '',
          sensory_details: result.sensory_details || '',
          significance: result.significance || '',
          custom_traits: result.custom_traits || '',
          is_visible: 1,
        }
        
        const newId = await createWorldElement(currentProjectId, elementToSave)
        
        if (newId) {
          addNotification({ type: 'success', message: `World element "${elementToSave.name}" generated and saved!` })
          const updated = await getWorldElements(currentProjectId, null, null)
          setElements(updated || [])
          setShowGenerateModal(false)
        } else {
          setGenerateError('Failed to save the generated element to the database.')
        }
      } else {
        setGenerateError(result.error || 'AI failed to generate an element. Please try a different description.')
      }
    } catch (error) {
      console.error('Generate element error:', error)
      setGenerateError(`An unexpected error occurred during generation: ${error.message}`)
    } finally {
      setIsGenerating(false)
    }
  }
  
  // Render editor view
  if (view === 'edit') {
    return (
      <div className="h-full p-6">
        <WorldElementEditor
          element={editingElement}
          onSave={handleSaveElement}
          onClose={() => {
            setView('list')
            setEditingElement(null)
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
          <h1 className="text-2xl font-semibold text-text-primary flex items-center gap-2">
            <span>{Icons.WORLD}</span>
            <span>World Building</span>
          </h1>
          <p className="text-text-muted mt-1">
            {elements.length} element{elements.length !== 1 ? 's' : ''} in project
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
            className="btn btn-secondary"
            onClick={() => setShowGenerateModal(true)}
            title="Generate with AI"
          >
            <span>{Icons.AI}</span>
            <span>Generate with AI</span>
          </button>
          <button
            className="btn btn-primary"
            onClick={handleCreateElement}
          >
            <span>{Icons.PLUS}</span>
            <span>New Element</span>
          </button>
        </div>
      </div>
      
      {/* Type Filter Tabs */}
      <div className="flex items-center gap-2 mb-4 overflow-x-auto pb-2">
        {ELEMENT_TYPES.map(type => (
          <button
            key={type.id}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all',
              selectedType === type.id
                ? 'bg-accent-primary text-white'
                : 'bg-bg-card/60 text-text-muted hover:bg-bg-hover hover:text-text-primary'
            )}
            onClick={() => setSelectedType(type.id)}
          >
            <span className="mr-2">{type.icon}</span>
            <span>{type.label}</span>
            {type.id !== 'all' && (
              <span className="ml-2 text-xs opacity-70">
                ({elements.filter(e => e.element_type === type.id).length})
              </span>
            )}
          </button>
        ))}
      </div>
      
      {/* Elements Grid */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="spinner mx-auto mb-4" />
              <p className="text-text-muted">Loading world elements...</p>
            </div>
          </div>
        ) : filteredElements.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md">
              <div className="text-6xl mb-6">{Icons.WORLD}</div>
              <h2 className="text-xl font-semibold text-text-primary mb-2">
                {selectedType === 'all' ? 'No World Elements Yet' : `No ${ELEMENT_TYPES.find(t => t.id === selectedType)?.label}`}
              </h2>
              <p className="text-text-muted mb-6">
                Build your world by adding settings, locations, events, and more.
              </p>
              <button
                className="btn btn-primary"
                onClick={handleCreateElement}
              >
                <span>{Icons.PLUS}</span>
                <span>Create Element</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredElements.map(element => (
              <WorldElementCard
                key={element.id}
                element={element}
                isSelected={editingElement?.id === element.id}
                onClick={handleEditElement}
                onToggleVisibility={handleToggleVisibility}
                onDelete={handleDeleteElement}
              />
            ))}
          </div>
        )}
      </div>
      
      {/* Import Modal */}
      <CSVImportModal
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        onImport={handleImport}
      />
      
      {/* Generate Element Modal */}
      <GenerateElementModal
        isOpen={showGenerateModal}
        onClose={() => setShowGenerateModal(false)}
        onGenerate={handleGenerateElement}
        isGenerating={isGenerating}
        error={generateError}
        clearError={() => setGenerateError('')}
      />
    </div>
  )
}

export default WorldBuilding

