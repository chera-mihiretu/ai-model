/**
 * Scene Editor / Draft Tool Component
 * ===================================
 * Break chapters into scenes and expand them with AI.
 */

import { useState, useEffect } from 'react'
import useStore from '../hooks/useStore'
import { usePythonBridge } from '../hooks/usePythonBridge'
import { clsx } from 'clsx'

// Icons
const Icons = {
  SCENE: '🎬',
  PLUS: '+',
  DELETE: '🗑️',
  EDIT: '✏️',
  EXPAND: '✨',
  POV: '👁️',
  LOCATION: '📍',
  DRAG: '⋮⋮',
  COLLAPSE: '▼',
  AI: '🤖',
  MERGE: '📋',
  SAVE: '💾',
}

function SceneCard({ scene, index, onEdit, onDelete, onExpand, isExpanding }) {
  const [isOpen, setIsOpen] = useState(false)
  
  return (
    <div className={clsx(
      'rounded-xl overflow-hidden transition-all',
      'bg-gradient-to-br from-bg-card/90 to-bg-sidebar/90',
      'border border-glass-border',
      'hover:border-accent-primary/50'
    )}>
      {/* Header */}
      <div
        className="p-4 flex items-start gap-3 cursor-pointer"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="text-text-muted">{Icons.DRAG}</span>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-text-muted">#{index + 1}</span>
            <h3 className="font-semibold text-text-primary">
              {scene.title || 'Untitled Scene'}
            </h3>
          </div>
          
          {/* Meta */}
          <div className="flex items-center gap-3 mt-1 text-xs text-text-muted">
            {scene.pov_character && (
              <span className="flex items-center gap-1">
                <span>{Icons.POV}</span>
                <span>{scene.pov_character}</span>
              </span>
            )}
            {scene.location && (
              <span className="flex items-center gap-1">
                <span>{Icons.LOCATION}</span>
                <span>{scene.location}</span>
              </span>
            )}
          </div>
          
          {/* Summary preview */}
          {scene.summary && !isOpen && (
            <p className="text-sm text-text-secondary mt-2 line-clamp-2">
              {scene.summary}
            </p>
          )}
        </div>
        
        <span className={clsx(
          'text-text-muted transition-transform',
          isOpen && 'rotate-180'
        )}>
          {Icons.COLLAPSE}
        </span>
      </div>
      
      {/* Expanded content */}
      {isOpen && (
        <div className="px-4 pb-4 pt-2 border-t border-border/30">
          {/* Summary */}
          {scene.summary && (
            <div className="mb-4">
              <h4 className="text-xs font-medium text-text-secondary uppercase mb-1">Summary</h4>
              <p className="text-sm text-text-primary">{scene.summary}</p>
            </div>
          )}
          
          {/* Content */}
          {scene.content && (
            <div className="mb-4">
              <h4 className="text-xs font-medium text-text-secondary uppercase mb-1">Content</h4>
              <div className="p-3 rounded-lg bg-bg-hover/50 max-h-40 overflow-y-auto">
                <p className="text-sm text-text-primary whitespace-pre-wrap">{scene.content}</p>
              </div>
            </div>
          )}
          
          {/* Actions */}
          <div className="flex items-center gap-2 mt-4">
            <button
              className="btn btn-secondary text-sm"
              onClick={(e) => {
                e.stopPropagation()
                onEdit(scene)
              }}
            >
              {Icons.EDIT} Edit
            </button>
            <button
              className="btn btn-secondary text-sm"
              onClick={(e) => {
                e.stopPropagation()
                onExpand(scene)
              }}
              disabled={isExpanding || !scene.summary}
            >
              {isExpanding ? (
                <>
                  <div className="spinner !w-3 !h-3" />
                  <span>Expanding...</span>
                </>
              ) : (
                <>
                  {Icons.EXPAND} Expand with AI
                </>
              )}
            </button>
            <button
              className="btn btn-ghost text-sm text-red-400 hover:text-red-300"
              onClick={(e) => {
                e.stopPropagation()
                onDelete(scene)
              }}
            >
              {Icons.DELETE}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function SceneEditModal({ scene, onSave, onClose }) {
  const [formData, setFormData] = useState(scene || {
    title: '',
    summary: '',
    pov_character: '',
    location: ''
  })
  
  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="glass-card p-6 w-full max-w-lg">
        <h2 className="text-xl font-bold text-text-primary mb-4">
          {scene?.id ? 'Edit Scene' : 'New Scene'}
        </h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Scene Title
            </label>
            <input
              type="text"
              className="input"
              placeholder="e.g., The First Meeting"
              value={formData.title || ''}
              onChange={(e) => handleChange('title', e.target.value)}
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">
                POV Character
              </label>
              <input
                type="text"
                className="input"
                placeholder="Who's perspective?"
                value={formData.pov_character || ''}
                onChange={(e) => handleChange('pov_character', e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">
                Location
              </label>
              <input
                type="text"
                className="input"
                placeholder="Where does it happen?"
                value={formData.location || ''}
                onChange={(e) => handleChange('location', e.target.value)}
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Scene Summary *
            </label>
            <textarea
              className="input-textarea min-h-[100px]"
              placeholder="What happens in this scene? (Used for AI expansion)"
              value={formData.summary || ''}
              onChange={(e) => handleChange('summary', e.target.value)}
            />
          </div>
          
          {formData.content && (
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">
                Scene Content
              </label>
              <textarea
                className="input-textarea min-h-[150px]"
                placeholder="Written prose for this scene..."
                value={formData.content || ''}
                onChange={(e) => handleChange('content', e.target.value)}
              />
            </div>
          )}
        </div>
        
        <div className="flex justify-end gap-3 mt-6">
          <button className="btn btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={() => onSave(formData)}
            disabled={!formData.summary?.trim()}
          >
            {Icons.SAVE} Save Scene
          </button>
        </div>
      </div>
    </div>
  )
}

function SceneEditor() {
  const {
    currentProjectId,
    currentChapterId,
    addNotification,
  } = useStore()
  
  const {
    getScenes,
    createScene,
    updateScene,
    deleteScene,
    getChapterContent,
    updateChapterContent,
    isElectronApi,
  } = usePythonBridge()
  
  const [scenes, setScenes] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [editingScene, setEditingScene] = useState(null)
  const [expandingSceneId, setExpandingSceneId] = useState(null)
  
  // Load scenes
  useEffect(() => {
    async function loadScenes() {
      if (!currentChapterId) {
        setScenes([])
        setIsLoading(false)
        return
      }
      
      setIsLoading(true)
      const data = await getScenes(currentChapterId)
      setScenes(data || [])
      setIsLoading(false)
    }
    loadScenes()
  }, [currentChapterId])
  
  const handleCreateScene = () => {
    setEditingScene({})
  }
  
  const handleSaveScene = async (data) => {
    if (data.id) {
      // Update existing
      await updateScene(data.id, data)
      addNotification({ type: 'success', message: 'Scene updated' })
    } else {
      // Create new
      await createScene(currentChapterId, data)
      addNotification({ type: 'success', message: 'Scene created' })
    }
    
    // Refresh
    const updated = await getScenes(currentChapterId)
    setScenes(updated || [])
    setEditingScene(null)
  }
  
  const handleDeleteScene = async (scene) => {
    if (!confirm(`Delete scene "${scene.title || 'Untitled'}"?`)) return
    
    await deleteScene(scene.id)
    const updated = await getScenes(currentChapterId)
    setScenes(updated || [])
    addNotification({ type: 'success', message: 'Scene deleted' })
  }
  
  const handleExpandScene = async (scene) => {
    if (!scene.summary) {
      addNotification({ type: 'warning', message: 'Scene needs a summary to expand' })
      return
    }
    
    if (!isElectronApi) {
      addNotification({ type: 'warning', message: 'AI expansion requires the Python backend' })
      return
    }
    
    setExpandingSceneId(scene.id)
    
    try {
      // Get previous scene content as context
      const sceneIndex = scenes.findIndex(s => s.id === scene.id)
      let context = ''
      if (sceneIndex > 0) {
        const prevScene = scenes[sceneIndex - 1]
        context = prevScene.content || prevScene.summary || ''
      }
      
      const result = await window.api.expandSceneFromSummary(
        scene.summary,
        context,
        'fiction'
      )
      
      if (result) {
        // Update scene with expanded content
        await updateScene(scene.id, { content: result })
        
        // Refresh
        const updated = await getScenes(currentChapterId)
        setScenes(updated || [])
        
        addNotification({ type: 'success', message: 'Scene expanded with AI' })
      }
    } catch (error) {
      console.error('Scene expansion error:', error)
      addNotification({ type: 'error', message: 'Failed to expand scene' })
    } finally {
      setExpandingSceneId(null)
    }
  }
  
  const handleMergeToChapter = async () => {
    if (scenes.length === 0) {
      addNotification({ type: 'warning', message: 'No scenes to merge' })
      return
    }
    
    const scenesWithContent = scenes.filter(s => s.content?.trim())
    if (scenesWithContent.length === 0) {
      addNotification({ type: 'warning', message: 'No expanded scenes to merge. Expand scenes first.' })
      return
    }
    
    if (!confirm(`Merge ${scenesWithContent.length} scene(s) into chapter content?`)) return
    
    // Get current chapter content
    const currentContent = await getChapterContent(currentChapterId)
    
    // Combine scene contents
    const mergedContent = scenesWithContent
      .map(s => s.content)
      .join('\n\n')
    
    // Append to chapter
    const newContent = currentContent
      ? currentContent + '\n\n' + mergedContent
      : mergedContent
    
    await updateChapterContent(currentChapterId, newContent)
    addNotification({ type: 'success', message: 'Scenes merged into chapter' })
  }
  
  if (!currentChapterId) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-6">{Icons.SCENE}</div>
          <h2 className="text-xl font-semibold text-text-primary mb-2">
            Select a Chapter
          </h2>
          <p className="text-text-muted">
            Select a chapter from the sidebar to manage its scenes.
          </p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary flex items-center gap-2">
            <span>{Icons.SCENE}</span>
            <span>Scene Editor</span>
          </h1>
          <p className="text-text-muted mt-1">
            Break your chapter into scenes and expand them with AI
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            className="btn btn-secondary"
            onClick={handleMergeToChapter}
            disabled={scenes.length === 0}
          >
            {Icons.MERGE} Merge to Chapter
          </button>
          <button
            className="btn btn-primary"
            onClick={handleCreateScene}
          >
            <span>{Icons.PLUS}</span>
            <span>Add Scene</span>
          </button>
        </div>
      </div>
      
      {/* Scenes List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="spinner mx-auto mb-4" />
              <p className="text-text-muted">Loading scenes...</p>
            </div>
          </div>
        ) : scenes.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md">
              <div className="text-6xl mb-6">{Icons.SCENE}</div>
              <h2 className="text-xl font-semibold text-text-primary mb-2">
                No Scenes Yet
              </h2>
              <p className="text-text-muted mb-6">
                Break your chapter into scenes. Write a summary for each scene, 
                then use AI to expand them into full prose.
              </p>
              <button
                className="btn btn-primary"
                onClick={handleCreateScene}
              >
                <span>{Icons.PLUS}</span>
                <span>Create First Scene</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {scenes.map((scene, index) => (
              <SceneCard
                key={scene.id}
                scene={scene}
                index={index}
                onEdit={setEditingScene}
                onDelete={handleDeleteScene}
                onExpand={handleExpandScene}
                isExpanding={expandingSceneId === scene.id}
              />
            ))}
          </div>
        )}
      </div>
      
      {/* Edit Modal */}
      {editingScene !== null && (
        <SceneEditModal
          scene={editingScene}
          onSave={handleSaveScene}
          onClose={() => setEditingScene(null)}
        />
      )}
    </div>
  )
}

export default SceneEditor

