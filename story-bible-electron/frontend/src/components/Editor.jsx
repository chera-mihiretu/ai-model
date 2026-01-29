/**
 * Editor Component
 * ================
 * Rich text editor with TipTap and formatting toolbar.
 * Paper-light theme styling.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import Placeholder from '@tiptap/extension-placeholder'
import useStore from '../hooks/useStore'
import { usePythonBridge } from '../hooks/usePythonBridge'
import { clsx } from 'clsx'

// Icons
const Icons = {
  UNDO: '↶',
  REDO: '↷',
  BOLD: 'B',
  ITALIC: 'I',
  UNDERLINE: 'U',
  STRIKE: 'S',
  BULLET: '•',
  NUMBERED: '1.',
  H1: 'H1',
  H2: 'H2',
  H3: 'H3',
  GENERATE: '⚡',
  SPARKLE: '✨',
  CHAT: '💬',
  CLOSE: '✕',
  MAGIC: '🪄',
}

// Tooltips
const Tooltips = {
  UNDO: 'Undo (Ctrl+Z)',
  REDO: 'Redo (Ctrl+Y)',
  BOLD: 'Bold (Ctrl+B)',
  ITALIC: 'Italic (Ctrl+I)',
  UNDERLINE: 'Underline (Ctrl+U)',
  STRIKE: 'Strikethrough',
  BULLET: 'Bullet List',
  NUMBERED: 'Numbered List',
  H1: 'Heading 1',
  H2: 'Heading 2',
  H3: 'Heading 3',
}

function FormatButton({ icon, tooltip, isActive, onClick, disabled }) {
  return (
    <button
      className={clsx(
        'format-btn',
        isActive && 'active'
      )}
      onClick={onClick}
      title={tooltip}
      disabled={disabled}
    >
      {icon}
    </button>
  )
}

function FormattingToolbar({ editor }) {
  if (!editor) return null
  
  return (
    <div className="flex items-center gap-1 p-2 paper-card mb-4">
      <FormatButton
        icon={Icons.UNDO}
        tooltip={Tooltips.UNDO}
        onClick={() => editor.chain().focus().undo().run()}
        disabled={!editor.can().undo()}
      />
      <FormatButton
        icon={Icons.REDO}
        tooltip={Tooltips.REDO}
        onClick={() => editor.chain().focus().redo().run()}
        disabled={!editor.can().redo()}
      />
      
      <div className="w-px h-6 bg-gray-200 mx-2" />
      
      <FormatButton
        icon={Icons.BOLD}
        tooltip={Tooltips.BOLD}
        isActive={editor.isActive('bold')}
        onClick={() => editor.chain().focus().toggleBold().run()}
      />
      <FormatButton
        icon={Icons.ITALIC}
        tooltip={Tooltips.ITALIC}
        isActive={editor.isActive('italic')}
        onClick={() => editor.chain().focus().toggleItalic().run()}
      />
      <FormatButton
        icon={Icons.UNDERLINE}
        tooltip={Tooltips.UNDERLINE}
        isActive={editor.isActive('underline')}
        onClick={() => editor.chain().focus().toggleUnderline().run()}
      />
      <FormatButton
        icon={Icons.STRIKE}
        tooltip={Tooltips.STRIKE}
        isActive={editor.isActive('strike')}
        onClick={() => editor.chain().focus().toggleStrike().run()}
      />
      
      <div className="w-px h-6 bg-gray-200 mx-2" />
      
      <FormatButton
        icon={Icons.BULLET}
        tooltip={Tooltips.BULLET}
        isActive={editor.isActive('bulletList')}
        onClick={() => editor.chain().focus().toggleBulletList().run()}
      />
      <FormatButton
        icon={Icons.NUMBERED}
        tooltip={Tooltips.NUMBERED}
        isActive={editor.isActive('orderedList')}
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
      />
      
      <div className="w-px h-6 bg-gray-200 mx-2" />
      
      <FormatButton
        icon={Icons.H1}
        tooltip={Tooltips.H1}
        isActive={editor.isActive('heading', { level: 1 })}
        onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
      />
      <FormatButton
        icon={Icons.H2}
        tooltip={Tooltips.H2}
        isActive={editor.isActive('heading', { level: 2 })}
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
      />
      <FormatButton
        icon={Icons.H3}
        tooltip={Tooltips.H3}
        isActive={editor.isActive('heading', { level: 3 })}
        onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
      />
    </div>
  )
}

// Generate Openings Modal
function GenerateOpeningsModal({ isOpen, onClose, onGenerate, isGenerating }) {
  const [formData, setFormData] = useState({
    mood: '',
    setting: '',
    character: '',
    hook: '',
    style: 'narrative',
  })
  
  const styles = [
    { id: 'narrative', label: 'Narrative (story-telling)' },
    { id: 'action', label: 'Action (in medias res)' },
    { id: 'dialogue', label: 'Dialogue (conversation)' },
    { id: 'descriptive', label: 'Descriptive (setting/atmosphere)' },
    { id: 'introspective', label: 'Introspective (character thoughts)' },
  ]
  
  const examplePrompts = [
    { mood: 'tense and suspenseful', setting: 'a dark alley at midnight', character: 'a detective on the run', hook: 'someone is following them' },
    { mood: 'warm and nostalgic', setting: 'a small coastal town', character: 'a woman returning home after years', hook: 'everything has changed' },
    { mood: 'mysterious and eerie', setting: 'an abandoned mansion', character: 'a curious explorer', hook: 'they hear a voice calling their name' },
  ]
  
  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }
  
  const handleSubmit = () => {
    onGenerate(formData)
  }
  
  const applyExample = (example) => {
    setFormData(prev => ({ ...prev, ...example }))
  }
  
  useEffect(() => {
    if (!isOpen) {
      setFormData({ mood: '', setting: '', character: '', hook: '', style: 'narrative' })
    }
  }, [isOpen])
  
  if (!isOpen) return null
  
  const hasContent = formData.mood || formData.setting || formData.character || formData.hook
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 modal-backdrop" onClick={!isGenerating ? onClose : undefined} />
      
      <div className="relative z-10 w-full max-w-2xl mx-4 modal-content p-6 animate-slide-up max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{Icons.SPARKLE}</span>
            <div>
              <h2 className="text-xl font-bold text-gray-800">Generate 3 Openings</h2>
              <p className="text-sm text-gray-500">Describe what you want and AI will create 3 different opening options</p>
            </div>
          </div>
          {!isGenerating && (
            <button className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors" onClick={onClose}>
              {Icons.CLOSE}
            </button>
          )}
        </div>
        
        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">Opening Style</label>
            <select
              className="input"
              value={formData.style}
              onChange={(e) => handleChange('style', e.target.value)}
              disabled={isGenerating}
            >
              {styles.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">Mood / Atmosphere</label>
            <input
              type="text"
              className="input"
              placeholder="e.g., tense and suspenseful, warm and cozy, dark and mysterious..."
              value={formData.mood}
              onChange={(e) => handleChange('mood', e.target.value)}
              disabled={isGenerating}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">Setting / Location</label>
            <input
              type="text"
              className="input"
              placeholder="e.g., a rainy city street, an ancient library, a spaceship..."
              value={formData.setting}
              onChange={(e) => handleChange('setting', e.target.value)}
              disabled={isGenerating}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">Character(s)</label>
            <input
              type="text"
              className="input"
              placeholder="e.g., a young detective, two estranged siblings, a lonely astronaut..."
              value={formData.character}
              onChange={(e) => handleChange('character', e.target.value)}
              disabled={isGenerating}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">Hook / What's Happening</label>
            <textarea
              className="input-textarea min-h-[80px]"
              placeholder="e.g., they discover a hidden letter, a stranger arrives with bad news, something goes wrong..."
              value={formData.hook}
              onChange={(e) => handleChange('hook', e.target.value)}
              disabled={isGenerating}
            />
          </div>
        </div>
        
        <div className="mb-6">
          <p className="text-sm font-medium text-gray-600 mb-2">Quick Examples:</p>
          <div className="flex flex-wrap gap-2">
            {examplePrompts.map((ex, i) => (
              <button
                key={i}
                className="px-3 py-1.5 text-xs rounded-lg bg-gray-100 text-gray-500 hover:bg-primary-50 hover:text-primary-600 transition-colors"
                onClick={() => applyExample(ex)}
                disabled={isGenerating}
              >
                {ex.mood} in {ex.setting}
              </button>
            ))}
          </div>
        </div>
        
        <div className="flex items-center justify-end gap-3">
          <button className="btn btn-ghost" onClick={onClose} disabled={isGenerating}>Cancel</button>
          <button
            className="btn btn-primary min-w-[180px]"
            onClick={handleSubmit}
            disabled={isGenerating}
          >
            {isGenerating ? (
              <><div className="spinner !w-4 !h-4" /><span>Generating...</span></>
            ) : (
              <><span>{Icons.SPARKLE}</span><span>Generate 3 Openings</span></>
            )}
          </button>
        </div>
        
        {isGenerating && (
          <div className="mt-6 p-4 rounded-lg bg-primary-50 border border-primary-200">
            <div className="flex items-center gap-3">
              <div className="spinner !w-6 !h-6" />
              <div>
                <p className="text-primary-600 font-medium">Creating your openings...</p>
                <p className="text-sm text-gray-500">AI is crafting 3 different ways to start your story.</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Generate Draft Modal
function GenerateDraftModal({ isOpen, onClose, onGenerate, isGenerating, hasExistingContent }) {
  const [formData, setFormData] = useState({
    whatToWrite: '',
    characters: '',
    events: '',
    emotion: '',
    length: 'medium',
  })
  
  const lengths = [
    { id: 'short', label: 'Short (1-2 paragraphs)' },
    { id: 'medium', label: 'Medium (3-5 paragraphs)' },
    { id: 'long', label: 'Long (full scene)' },
  ]
  
  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }
  
  const handleSubmit = () => {
    onGenerate(formData)
  }
  
  useEffect(() => {
    if (!isOpen) {
      setFormData({ whatToWrite: '', characters: '', events: '', emotion: '', length: 'medium' })
    }
  }, [isOpen])
  
  if (!isOpen) return null
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 modal-backdrop" onClick={!isGenerating ? onClose : undefined} />
      
      <div className="relative z-10 w-full max-w-2xl mx-4 modal-content p-6 animate-slide-up max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{Icons.MAGIC}</span>
            <div>
              <h2 className="text-xl font-bold text-gray-800">Generate Draft</h2>
              <p className="text-sm text-gray-500">
                {hasExistingContent 
                  ? 'Tell AI what to write next in your story' 
                  : 'Describe what you want AI to write for you'}
              </p>
            </div>
          </div>
          {!isGenerating && (
            <button className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors" onClick={onClose}>
              {Icons.CLOSE}
            </button>
          )}
        </div>
        
        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              What should happen in this section? <span className="text-red-500">*</span>
            </label>
            <textarea
              className="input-textarea min-h-[100px]"
              placeholder={hasExistingContent 
                ? "e.g., The protagonist discovers the hidden room and finds a clue about their past..."
                : "e.g., Open with the main character waking up to find their town deserted..."}
              value={formData.whatToWrite}
              onChange={(e) => handleChange('whatToWrite', e.target.value)}
              disabled={isGenerating}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Characters in this scene
            </label>
            <input
              type="text"
              className="input"
              placeholder="e.g., Sarah (nervous), Detective Mills (suspicious), the mysterious stranger..."
              value={formData.characters}
              onChange={(e) => handleChange('characters', e.target.value)}
              disabled={isGenerating}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Key events or plot points to include
            </label>
            <textarea
              className="input-textarea min-h-[80px]"
              placeholder="e.g., They argue about the letter, reveal a secret, make an important decision..."
              value={formData.events}
              onChange={(e) => handleChange('events', e.target.value)}
              disabled={isGenerating}
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Emotional tone
              </label>
              <input
                type="text"
                className="input"
                placeholder="e.g., tense, romantic, melancholic..."
                value={formData.emotion}
                onChange={(e) => handleChange('emotion', e.target.value)}
                disabled={isGenerating}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Length
              </label>
              <select
                className="input"
                value={formData.length}
                onChange={(e) => handleChange('length', e.target.value)}
                disabled={isGenerating}
              >
                {lengths.map(l => <option key={l.id} value={l.id}>{l.label}</option>)}
              </select>
            </div>
          </div>
        </div>
        
        <div className="mb-6 p-3 rounded-lg bg-primary-50 border border-primary-200">
          <p className="text-sm text-gray-600">
            <span className="text-primary-600 font-medium">💡 Tip:</span> The more specific you are, the better the result. 
            {hasExistingContent && " AI will read your existing content and continue naturally from where you left off."}
          </p>
        </div>
        
        <div className="flex items-center justify-end gap-3">
          <button className="btn btn-ghost" onClick={onClose} disabled={isGenerating}>Cancel</button>
          <button
            className="btn btn-primary min-w-[180px]"
            onClick={handleSubmit}
            disabled={isGenerating || !formData.whatToWrite.trim()}
          >
            {isGenerating ? (
              <><div className="spinner !w-4 !h-4" /><span>Generating...</span></>
            ) : (
              <><span>{Icons.GENERATE}</span><span>Generate Draft</span></>
            )}
          </button>
        </div>
        
        {isGenerating && (
          <div className="mt-6 p-4 rounded-lg bg-primary-50 border border-primary-200">
            <div className="flex items-center gap-3">
              <div className="spinner !w-6 !h-6" />
              <div>
                <p className="text-primary-600 font-medium">Writing your draft...</p>
                <p className="text-sm text-gray-500">AI is crafting your story. This may take 20-40 seconds.</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function ActionButtons({ onGenerate, onOpenings, onChat, isGenerating }) {
  return (
    <div className="flex items-center gap-3 mt-6">
      <button
        className="btn btn-secondary flex-1"
        onClick={onGenerate}
        disabled={isGenerating}
      >
        <span>{Icons.GENERATE}</span>
        <span>Generate Draft</span>
      </button>
      <button
        className="btn btn-secondary flex-1"
        onClick={onOpenings}
        disabled={isGenerating}
      >
        <span>{Icons.SPARKLE}</span>
        <span>3 Openings</span>
      </button>
      <button
        className="btn btn-secondary flex-1"
        onClick={onChat}
        disabled={isGenerating}
      >
        <span>{Icons.CHAT}</span>
        <span>Chat Ideas</span>
      </button>
    </div>
  )
}

function Editor() {
  const {
    editorContent,
    currentChapterId,
    currentProjectId,
    isAiGenerating,
    aiStreamedText,
    setEditorContent,
    markEditorClean,
    setPendingAiRequest,
    setEditorInsertCallback,
    setEditorCursorContextCallback,
    setEditorSelectionCallback,
    setCurrentEditorSelection,
    setEditorReplaceSelectionCallback,
    setEditorInstance,
  } = useStore()
  
  const {
    getChapterContent,
    updateChapterContent,
    startAiStream,
    getContextWindow,
  } = usePythonBridge()
  
  const [showOpeningsModal, setShowOpeningsModal] = useState(false)
  const [showDraftModal, setShowDraftModal] = useState(false)
  const saveTimeoutRef = useRef(null)
  const editorRef = useRef(null)
  
  // Initialize TipTap editor
  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      Placeholder.configure({
        placeholder: 'Start writing your story...',
      }),
    ],
    content: '',
    editorProps: {
      attributes: {
        class: 'editor-content outline-none min-h-[400px] p-4',
      },
    },
    onUpdate: ({ editor }) => {
      const html = editor.getHTML()
      const text = editor.getText()
      setEditorContent(text)
      
      // Debounced auto-save
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }
      
      if (currentChapterId) {
        saveTimeoutRef.current = setTimeout(async () => {
          await updateChapterContent(currentChapterId, html)
          markEditorClean()
        }, 1000)
      }
    },
    onSelectionUpdate: ({ editor }) => {
      // Track selection changes and store in global state
      const { from, to } = editor.state.selection
      const selectedText = editor.state.doc.textBetween(from, to, ' ')
      
      setCurrentEditorSelection({
        selectedText: selectedText,
        selectionStart: from,
        selectionEnd: to,
        hasSelection: from !== to && selectedText.trim().length > 0
      })
    },
  })
  
  // Load chapter content when chapter changes
  useEffect(() => {
    async function loadContent() {
      if (!currentChapterId || !editor) return
      
      const content = await getChapterContent(currentChapterId)
      if (content) {
        editor.commands.setContent(content)
        // Sync plain text to store for TTS and other features
        const plainText = editor.getText()
        setEditorContent(plainText)
      } else {
        editor.commands.clearContent()
        setEditorContent('')
      }
      markEditorClean()
    }
    
    loadContent()
  }, [currentChapterId, editor])
  
  // Note: AI no longer writes directly to editor
  // AI responses go to AssistantPanel and user can click "Insert" to add to editor
  
  // Keep editor reference updated
  useEffect(() => {
    editorRef.current = editor
  }, [editor])
  
  // Register the editor insert callback
  useEffect(() => {
    const insertCallback = (text) => {
      console.log('Insert callback called with:', text?.substring(0, 50))
      if (editorRef.current) {
        console.log('Editor found, inserting content')
        editorRef.current.chain().focus().insertContent(text).run()
      } else {
        console.log('No editor reference available')
      }
    }
    setEditorInsertCallback(insertCallback)
    return () => setEditorInsertCallback(null)
  }, [setEditorInsertCallback])
  
  // Register the editor cursor context callback
  useEffect(() => {
    const getCursorContext = () => {
      if (!editorRef.current) {
        return { precedingText: '', cursorPosition: 0, fullText: '', textAfterCursor: '' }
      }
      
      const editor = editorRef.current
      const { from } = editor.state.selection
      const fullText = editor.getText()
      
      // Get text before cursor (up to 1000 words)
      const textBeforeCursor = fullText.substring(0, from)
      const words = textBeforeCursor.split(/\s+/)
      const last1000Words = words.slice(-1000).join(' ')
      
      // Get text after cursor
      const textAfterCursor = fullText.substring(from)
      
      return {
        precedingText: last1000Words,
        cursorPosition: from,
        fullText: fullText,
        textAfterCursor: textAfterCursor,
        wordCount: words.length
      }
    }
    
    setEditorCursorContextCallback(() => getCursorContext)
    return () => setEditorCursorContextCallback(null)
  }, [setEditorCursorContextCallback])
  
  // Register the editor selection callback
  useEffect(() => {
    const getSelection = () => {
      if (!editorRef.current) {
        return { selectedText: '', selectionStart: 0, selectionEnd: 0, hasSelection: false }
      }
      
      const editor = editorRef.current
      const { from, to } = editor.state.selection
      const selectedText = editor.state.doc.textBetween(from, to, ' ')
      
      return {
        selectedText: selectedText,
        selectionStart: from,
        selectionEnd: to,
        hasSelection: from !== to && selectedText.trim().length > 0
      }
    }
    
    setEditorSelectionCallback(() => getSelection)
    return () => setEditorSelectionCallback(null)
  }, [setEditorSelectionCallback])
  
  // Register the editor replace selection callback
  // Can accept optional start/end positions to replace at specific location
  useEffect(() => {
    const replaceSelection = (newText, startPos, endPos) => {
      if (!editorRef.current) {
        console.error('No editor reference for replace selection')
        return false
      }
      
      const editor = editorRef.current
      
      // Use provided positions or fall back to current selection
      let from, to
      if (startPos !== undefined && endPos !== undefined) {
        from = startPos
        to = endPos
      } else {
        const sel = editor.state.selection
        from = sel.from
        to = sel.to
      }
      
      // If there's a range, replace it; otherwise insert at cursor
      if (from !== to) {
        editor.chain().focus().deleteRange({ from, to }).insertContent(newText).run()
      } else {
        editor.chain().focus().insertContent(newText).run()
      }
      
      return true
    }
    
    setEditorReplaceSelectionCallback(() => replaceSelection)
    return () => setEditorReplaceSelectionCallback(null)
  }, [setEditorReplaceSelectionCallback])
  
  // Store editor instance for direct access
  useEffect(() => {
    if (editor) {
      setEditorInstance(editor)
    }
    return () => setEditorInstance(null)
  }, [editor, setEditorInstance])
  
  // Handle generate draft with form data - sends to AssistantPanel
  const handleGenerateDraft = (formData) => {
    if (!currentProjectId || !currentChapterId) return
    
    const currentText = editor?.getText() || ''
    
    // Build detailed instruction from form data
    let instruction = ''
    
    if (formData.whatToWrite) {
      instruction = `Write the following for my story:\n${formData.whatToWrite}`
    }
    
    if (formData.characters) {
      instruction += `\n\nCharacters in this scene: ${formData.characters}`
    }
    
    if (formData.events) {
      instruction += `\n\nKey events to include: ${formData.events}`
    }
    
    if (formData.emotion) {
      instruction += `\n\nEmotional tone: ${formData.emotion}`
    }
    
    // Add length guidance
    const lengthGuide = {
      short: 'Keep it brief - 1-2 paragraphs.',
      medium: 'Write 3-5 solid paragraphs.',
      long: 'Write a full, detailed scene.',
    }
    instruction += `\n\n${lengthGuide[formData.length] || lengthGuide.medium}`
    
    if (currentText.trim().length > 50) {
      instruction += '\n\nHere is the existing story content to continue from:\n\n' + currentText.slice(-1000)
    }
    
    setShowDraftModal(false)
    
    // Send to AssistantPanel instead of directly to editor
    setPendingAiRequest({
      type: 'draft',
      instruction: instruction,
      formData: formData,
      context: currentText,
    })
  }
  
  // Handle generate openings with form data - sends to AssistantPanel
  const handleGenerateOpenings = (formData) => {
    const currentText = editor?.getText() || ''
    
    // Build detailed instruction from form data
    let instruction = 'Generate 3 DIFFERENT and DISTINCT opening paragraphs for a story. Label them as:\n\n**OPENING 1:**\n\n**OPENING 2:**\n\n**OPENING 3:**'
    
    if (formData.style) {
      const styleDesc = {
        narrative: 'narrative storytelling style',
        action: 'action-packed in medias res style',
        dialogue: 'dialogue-driven opening',
        descriptive: 'descriptive, atmospheric opening',
        introspective: 'introspective, character thoughts opening',
      }
      instruction += `\n\nStyle: ${styleDesc[formData.style] || 'narrative style'}`
    }
    
    if (formData.mood) {
      instruction += `\n\nMood/Atmosphere: ${formData.mood}`
    }
    
    if (formData.setting) {
      instruction += `\n\nSetting: ${formData.setting}`
    }
    
    if (formData.character) {
      instruction += `\n\nCharacter(s): ${formData.character}`
    }
    
    if (formData.hook) {
      instruction += `\n\nHook/What's happening: ${formData.hook}`
    }
    
    instruction += '\n\nMake each opening unique and engaging. Each should be 2-3 paragraphs.'
    
    setShowOpeningsModal(false)
    
    // Send to AssistantPanel instead of directly to editor
    setPendingAiRequest({
      type: 'openings',
      instruction: instruction,
      formData: formData,
    })
  }
  
  // Handle chat about ideas - opens assistant panel
  const handleChatIdeas = () => {
    // Send a chat request to the AssistantPanel
    setPendingAiRequest({
      type: 'chat',
      instruction: '',
      formData: {},
    })
  }
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }
    }
  }, [])
  
  return (
    <div className="h-full flex flex-col p-6 overflow-hidden">
      {/* Document Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-serif font-semibold text-gray-800">
            {currentChapterId ? 'Chapter Editor' : 'Welcome to Exelsias'}
          </h1>
          {!currentChapterId && (
            <p className="text-gray-500 mt-1">
              Select a chapter from the sidebar to start writing
            </p>
          )}
        </div>
        
        {currentChapterId && (
          <button
            className="px-3 py-1.5 rounded-lg bg-white text-gray-400 hover:bg-gray-100 text-sm border border-gray-200"
            title="Document Options"
          >
            ⋯
          </button>
        )}
      </div>
      
      {/* Formatting Toolbar */}
      {currentChapterId && <FormattingToolbar editor={editor} />}
      
      {/* Editor Area */}
      <div className="flex-1 overflow-hidden">
        {currentChapterId ? (
          <div className="h-full overflow-y-auto paper-card">
            <EditorContent editor={editor} />
          </div>
        ) : (
          <div className="h-full flex items-center justify-center paper-card">
            <div className="text-center max-w-md">
              <div className="text-6xl mb-6">📖</div>
              <h2 className="text-xl font-serif font-semibold text-gray-800 mb-2">
                No Chapter Selected
              </h2>
              <p className="text-gray-500 mb-6">
                Create a new project or select an existing chapter from the sidebar to begin writing your story.
              </p>
              <button className="btn btn-primary">
                Create New Project
              </button>
            </div>
          </div>
        )}
      </div>
      
      {/* Action Buttons */}
      {currentChapterId && (
        <ActionButtons
          onGenerate={() => setShowDraftModal(true)}
          onOpenings={() => setShowOpeningsModal(true)}
          onChat={handleChatIdeas}
          isGenerating={isAiGenerating}
        />
      )}
      
      {/* AI Generating Indicator */}
      {isAiGenerating && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 px-4 py-2 rounded-full bg-primary-500 text-white shadow-lg flex items-center gap-2 animate-pulse">
          <div className="spinner !w-4 !h-4 !border-white/30 !border-t-white" />
          <span>AI is writing...</span>
        </div>
      )}
      
      {/* Generate Openings Modal */}
      <GenerateOpeningsModal
        isOpen={showOpeningsModal}
        onClose={() => setShowOpeningsModal(false)}
        onGenerate={handleGenerateOpenings}
        isGenerating={isAiGenerating}
      />
      
      {/* Generate Draft Modal */}
      <GenerateDraftModal
        isOpen={showDraftModal}
        onClose={() => setShowDraftModal(false)}
        onGenerate={handleGenerateDraft}
        isGenerating={isAiGenerating}
        hasExistingContent={(editor?.getText() || '').trim().length > 50}
      />
    </div>
  )
}

export default Editor
