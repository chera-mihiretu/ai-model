/**
 * Editor Component
 * ================
 * Rich text editor with TipTap and formatting toolbar.
 * Includes Sudowrite-style floating selection menu.
 * Dark & Gold luxury theme styling.
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
  // Selection menu icons
  REWRITE: '🔄',
  EXPAND: '📝',
  DESCRIBE: '✨',
  WORDS: '📖',
  COMMENT: '💭',
  EDIT: '✏️',
  SHRINK: '📉',
  CONTINUE: '➡️',
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

/**
 * SelectionMenu Component
 * =======================
 * Sudowrite-style floating menu that appears when text is selected.
 * Shows different options based on selection length.
 */
function SelectionMenu({ 
  isVisible, 
  position, 
  selectedText, 
  isWord, 
  onRewrite, 
  onExpand,
  onShrink,
  onDescribe, 
  onContinue,
  onClose 
}) {
  if (!isVisible) return null
  
  // Calculate word count
  const wordCount = selectedText.trim().split(/\s+/).filter(w => w.length > 0).length
  const charCount = selectedText.length
  
  return (
    <div 
      className="selection-menu fixed z-[100] animate-fade-in"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        transform: 'translateX(-50%)',
      }}
      onMouseDown={(e) => e.preventDefault()} // Prevent losing selection
    >
      <div className="selection-menu-content flex items-center gap-1 p-1.5 rounded-xl bg-dark-800/95 backdrop-blur-lg border border-gold-rich/30 shadow-lg shadow-black/50">
        {/* Different options based on selection type */}
        {isWord ? (
          // Single word options
          <>
            <SelectionMenuButton
              icon={Icons.DESCRIBE}
              label="Describe"
              onClick={onDescribe}
              tooltip="Generate sensory descriptions"
            />
            <SelectionMenuButton
              icon={Icons.WORDS}
              label="Synonyms"
              onClick={() => onRewrite('synonyms')}
              tooltip="Find related words"
            />
            <SelectionMenuButton
              icon={Icons.REWRITE}
              label="Rewrite"
              onClick={() => onRewrite('rephrase')}
              tooltip="Rephrase this word"
            />
          </>
        ) : (
          // Passage options
          <>
            <SelectionMenuButton
              icon={Icons.REWRITE}
              label="Rewrite"
              onClick={() => onRewrite('improve')}
              tooltip="Rewrite this passage"
              primary
            />
            <SelectionMenuButton
              icon={Icons.EXPAND}
              label="Expand"
              onClick={onExpand}
              tooltip="Expand with more detail"
            />
            <SelectionMenuButton
              icon={Icons.SHRINK}
              label="Shorten"
              onClick={onShrink}
              tooltip="Make more concise"
            />
            <SelectionMenuButton
              icon={Icons.DESCRIBE}
              label="Describe"
              onClick={onDescribe}
              tooltip="Add sensory details"
            />
            <SelectionMenuButton
              icon={Icons.CONTINUE}
              label="Continue"
              onClick={onContinue}
              tooltip="Continue from here"
            />
          </>
        )}
        
        {/* Divider and close */}
        <div className="w-px h-6 bg-gold-rich/20 mx-1" />
        <button
          className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-400/10 transition-colors text-sm"
          onClick={onClose}
          title="Close menu"
        >
          ✕
        </button>
      </div>
      
      {/* Selection info */}
      <div className="text-center mt-1">
        <span className="text-[10px] text-gray-500 bg-dark-900/80 px-2 py-0.5 rounded-full">
          {wordCount} word{wordCount !== 1 ? 's' : ''} • {charCount} chars
        </span>
      </div>
      
      {/* Arrow pointing down to selection */}
      <div className="selection-menu-arrow" />
    </div>
  )
}

function SelectionMenuButton({ icon, label, onClick, tooltip, primary }) {
  return (
    <button
      className={clsx(
        'flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all duration-150',
        primary 
          ? 'bg-gold-rich/20 text-gold-rich hover:bg-gold-rich/30 border border-gold-rich/30'
          : 'text-gray-300 hover:text-gold-rich hover:bg-gold-rich/10'
      )}
      onClick={onClick}
      title={tooltip}
    >
      <span className="text-sm">{icon}</span>
      <span>{label}</span>
    </button>
  )
}

/**
 * Rewrite Style Modal
 * ===================
 * Modal for selecting rewrite style
 */
function RewriteStyleModal({ isOpen, onClose, onSelect, selectedText }) {
  const styles = [
    { id: 'improve', label: 'Improve Writing', desc: 'Enhance clarity, flow, and impact', icon: '✨' },
    { id: 'formal', label: 'More Formal', desc: 'Professional, sophisticated tone', icon: '🎩' },
    { id: 'casual', label: 'More Casual', desc: 'Relaxed, conversational tone', icon: '💬' },
    { id: 'dramatic', label: 'More Dramatic', desc: 'Heightened tension and emotion', icon: '🎭' },
    { id: 'poetic', label: 'More Poetic', desc: 'Lyrical, evocative language', icon: '🌸' },
    { id: 'concise', label: 'More Concise', desc: 'Tighter, more direct prose', icon: '✂️' },
    { id: 'descriptive', label: 'More Descriptive', desc: 'Rich sensory details', icon: '🎨' },
    { id: 'mysterious', label: 'More Mysterious', desc: 'Enigmatic, intriguing tone', icon: '🌙' },
  ]
  
  if (!isOpen) return null
  
  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 w-full max-w-md mx-4 glass-card p-5 animate-slide-up">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-100">Rewrite Style</h3>
            <p className="text-xs text-gray-400 mt-0.5">Choose how to rewrite your selection</p>
          </div>
          <button 
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gold-rich/10 text-gray-400 hover:text-gold-rich"
            onClick={onClose}
          >
            ✕
          </button>
        </div>
        
        {/* Preview of selected text */}
        <div className="mb-4 p-3 rounded-lg bg-dark-700/50 border border-gold-rich/10">
          <p className="text-xs text-gray-500 mb-1">Selected text:</p>
          <p className="text-sm text-gray-300 line-clamp-2 italic">"{selectedText}"</p>
        </div>
        
        {/* Style grid */}
        <div className="grid grid-cols-2 gap-2 max-h-[300px] overflow-y-auto">
          {styles.map(style => (
            <button
              key={style.id}
              className="flex items-start gap-2 p-3 rounded-lg bg-dark-700/50 hover:bg-gold-rich/10 border border-gold-rich/10 hover:border-gold-rich/30 transition-all text-left group"
              onClick={() => onSelect(style.id)}
            >
              <span className="text-xl">{style.icon}</span>
              <div>
                <p className="text-sm font-medium text-gray-200 group-hover:text-gold-rich">{style.label}</p>
                <p className="text-xs text-gray-500">{style.desc}</p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
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
      
      <div className="w-px h-6 bg-gold-rich/20 mx-2" />
      
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
      
      <div className="w-px h-6 bg-gold-rich/20 mx-2" />
      
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
      
      <div className="w-px h-6 bg-gold-rich/20 mx-2" />
      
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
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={!isGenerating ? onClose : undefined} />
      
      <div className="relative z-10 w-full max-w-2xl mx-4 glass-card p-6 animate-slide-up max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{Icons.SPARKLE}</span>
            <div>
              <h2 className="text-xl font-bold text-gray-100">Generate 3 Openings</h2>
              <p className="text-sm text-gray-400">Describe what you want and AI will create 3 different opening options</p>
            </div>
          </div>
          {!isGenerating && (
            <button className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gold-rich/10 text-gray-400 hover:text-gold-rich transition-colors" onClick={onClose}>
              {Icons.CLOSE}
            </button>
          )}
        </div>
        
        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gold-pale mb-1">Opening Style</label>
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
            <label className="block text-sm font-medium text-gold-pale mb-1">Mood / Atmosphere</label>
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
            <label className="block text-sm font-medium text-gold-pale mb-1">Setting / Location</label>
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
            <label className="block text-sm font-medium text-gold-pale mb-1">Character(s)</label>
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
            <label className="block text-sm font-medium text-gold-pale mb-1">Hook / What's Happening</label>
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
          <p className="text-sm font-medium text-gold-pale mb-2">Quick Examples:</p>
          <div className="flex flex-wrap gap-2">
            {examplePrompts.map((ex, i) => (
              <button
                key={i}
                className="px-3 py-1.5 text-xs rounded-lg bg-dark-700 text-gray-400 hover:bg-gold-rich/10 hover:text-gold-rich border border-gold-rich/20 transition-colors"
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
          <div className="mt-6 p-4 rounded-lg bg-gold-rich/10 border border-gold-rich/30">
            <div className="flex items-center gap-3">
              <div className="spinner !w-6 !h-6" />
              <div>
                <p className="text-gold-rich font-medium">Creating your openings...</p>
                <p className="text-sm text-gray-400">AI is crafting 3 different ways to start your story.</p>
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
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={!isGenerating ? onClose : undefined} />
      
      <div className="relative z-10 w-full max-w-2xl mx-4 glass-card p-6 animate-slide-up max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{Icons.MAGIC}</span>
            <div>
              <h2 className="text-xl font-bold text-gray-100">Generate Draft</h2>
              <p className="text-sm text-gray-400">
                {hasExistingContent 
                  ? 'Tell AI what to write next in your story' 
                  : 'Describe what you want AI to write for you'}
              </p>
            </div>
          </div>
          {!isGenerating && (
            <button className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gold-rich/10 text-gray-400 hover:text-gold-rich transition-colors" onClick={onClose}>
              {Icons.CLOSE}
            </button>
          )}
        </div>
        
        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gold-pale mb-1">
              What should happen in this section? <span className="text-red-400">*</span>
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
            <label className="block text-sm font-medium text-gold-pale mb-1">
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
            <label className="block text-sm font-medium text-gold-pale mb-1">
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
              <label className="block text-sm font-medium text-gold-pale mb-1">
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
              <label className="block text-sm font-medium text-gold-pale mb-1">
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
        
        <div className="mb-6 p-3 rounded-lg bg-gold-rich/10 border border-gold-rich/30">
          <p className="text-sm text-gray-300">
            <span className="text-gold-rich font-medium">💡 Tip:</span> The more specific you are, the better the result. 
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
          <div className="mt-6 p-4 rounded-lg bg-gold-rich/10 border border-gold-rich/30">
            <div className="flex items-center gap-3">
              <div className="spinner !w-6 !h-6" />
              <div>
                <p className="text-gold-rich font-medium">Writing your draft...</p>
                <p className="text-sm text-gray-400">AI is crafting your story. This may take 20-40 seconds.</p>
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
  const [showRewriteModal, setShowRewriteModal] = useState(false)
  const saveTimeoutRef = useRef(null)
  const editorRef = useRef(null)
  const editorContainerRef = useRef(null)
  
  // Selection menu state
  const [selectionMenu, setSelectionMenu] = useState({
    isVisible: false,
    position: { x: 0, y: 0 },
    selectedText: '',
    selectionStart: 0,
    selectionEnd: 0,
    isWord: false,
  })
  
  // Track if mouse is being held down (for selection)
  const isMouseDownRef = useRef(false)
  const pendingSelectionRef = useRef(null)
  
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
      const hasSelection = from !== to && selectedText.trim().length > 0
      
      setCurrentEditorSelection({
        selectedText: selectedText,
        selectionStart: from,
        selectionEnd: to,
        hasSelection: hasSelection
      })
      
      // Store selection data but DON'T show menu yet (wait for mouseup)
      if (hasSelection && selectedText.trim().length >= 1) {
        // Get selection coordinates for positioning the menu
        const domSelection = window.getSelection()
        
        if (domSelection && domSelection.rangeCount > 0) {
          const range = domSelection.getRangeAt(0)
          const rect = range.getBoundingClientRect()
          
          // Position menu above the selection, centered
          const menuX = rect.left + (rect.width / 2)
          const menuY = rect.top - 10 // 10px above selection
          
          // Determine if single word or passage
          const wordCount = selectedText.trim().split(/\s+/).filter(w => w.length > 0).length
          const isWord = wordCount <= 2
          
          // Store pending selection data (will show on mouseup)
          pendingSelectionRef.current = {
            position: { x: menuX, y: menuY },
            selectedText: selectedText.trim(),
            selectionStart: from,
            selectionEnd: to,
            isWord: isWord,
          }
          
          // If mouse is not being held down (e.g., keyboard selection), show immediately
          if (!isMouseDownRef.current) {
            setSelectionMenu({
              isVisible: true,
              ...pendingSelectionRef.current,
            })
          }
        }
      } else {
        // Hide menu and clear pending when no selection
        pendingSelectionRef.current = null
        setSelectionMenu(prev => ({ ...prev, isVisible: false }))
      }
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
  
  // Track mouse down/up to show menu only on release
  useEffect(() => {
    const handleMouseDown = (e) => {
      // Check if mousedown is in the editor
      if (e.target.closest('.ProseMirror')) {
        isMouseDownRef.current = true
        // Hide menu when starting a new selection
        setSelectionMenu(prev => ({ ...prev, isVisible: false }))
      }
    }
    
    const handleMouseUp = (e) => {
      // Small delay to let selection finalize
      setTimeout(() => {
        isMouseDownRef.current = false
        
        // Show the menu if we have a pending selection
        if (pendingSelectionRef.current) {
          // Re-calculate position in case it shifted
          const domSelection = window.getSelection()
          if (domSelection && domSelection.rangeCount > 0 && !domSelection.isCollapsed) {
            const range = domSelection.getRangeAt(0)
            const rect = range.getBoundingClientRect()
            
            setSelectionMenu({
              isVisible: true,
              position: { x: rect.left + (rect.width / 2), y: rect.top - 10 },
              selectedText: pendingSelectionRef.current.selectedText,
              selectionStart: pendingSelectionRef.current.selectionStart,
              selectionEnd: pendingSelectionRef.current.selectionEnd,
              isWord: pendingSelectionRef.current.isWord,
            })
          }
        }
      }, 10)
    }
    
    document.addEventListener('mousedown', handleMouseDown)
    document.addEventListener('mouseup', handleMouseUp)
    
    return () => {
      document.removeEventListener('mousedown', handleMouseDown)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [])
  
  // Close selection menu when clicking outside or pressing Escape
  useEffect(() => {
    const handleClickOutside = (e) => {
      // Don't close if clicking on the menu itself
      if (e.target.closest('.selection-menu')) return
      // Don't close if clicking in the editor (selection might change)
      if (e.target.closest('.ProseMirror')) return
      
      setSelectionMenu(prev => ({ ...prev, isVisible: false }))
      pendingSelectionRef.current = null
    }
    
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setSelectionMenu(prev => ({ ...prev, isVisible: false }))
        pendingSelectionRef.current = null
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleKeyDown)
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [])
  
  // Selection menu handlers
  const handleSelectionMenuClose = () => {
    setSelectionMenu(prev => ({ ...prev, isVisible: false }))
  }
  
  const handleRewrite = (style) => {
    if (!selectionMenu.selectedText) return
    
    // For 'synonyms' or simple word rewrite, directly send request
    // For passages, show style modal if style not specified
    if (style === 'synonyms') {
      // Generate synonyms/related words
      setPendingAiRequest({
        type: 'rewrite',
        instruction: `Provide 5-8 synonyms for: "${selectionMenu.selectedText}"

OUTPUT FORMAT: word1, word2, word3, word4, word5

RULES:
- Output ONLY the comma-separated words
- Do NOT write "Here are synonyms" or any introduction
- Do NOT explain your choices
- Do NOT add any text before or after the words`,
        style: 'synonyms',
        originalText: selectionMenu.selectedText,
        replaceSelection: false, // Synonyms are for reference, not replacement
        selectionStart: selectionMenu.selectionStart,
        selectionEnd: selectionMenu.selectionEnd,
      })
      setSelectionMenu(prev => ({ ...prev, isVisible: false }))
    } else if (style === 'rephrase') {
      // Simple word/phrase rephrase
      setPendingAiRequest({
        type: 'rewrite',
        instruction: `Rewrite this text: "${selectionMenu.selectedText}"

RULES:
- Output ONLY the rewritten text, nothing else
- Do NOT start with "Here's" or "Here is" or any introduction
- Do NOT end with explanations like "I maintained..." or "This version..."
- The output should be ready to paste directly into a document`,
        style: 'rephrase',
        originalText: selectionMenu.selectedText,
        replaceSelection: true,
        selectionStart: selectionMenu.selectionStart,
        selectionEnd: selectionMenu.selectionEnd,
      })
      setSelectionMenu(prev => ({ ...prev, isVisible: false }))
    } else if (style === 'improve') {
      // Show rewrite style modal for passages
      setShowRewriteModal(true)
    } else {
      // Direct rewrite with specific style
      const styleInstructions = {
        formal: 'in a more formal, professional tone',
        casual: 'in a more casual, conversational tone',
        dramatic: 'with more dramatic tension and emotion',
        poetic: 'in a more lyrical, poetic style',
        concise: 'to be more concise and direct',
        descriptive: 'with richer, more vivid descriptions',
        mysterious: 'with a more mysterious, enigmatic tone',
      }
      
      setPendingAiRequest({
        type: 'rewrite',
        instruction: `Rewrite this text ${styleInstructions[style] || 'improved'}:

"${selectionMenu.selectedText}"

RULES:
- Output ONLY the rewritten text, nothing else
- Do NOT start with "Here's" or "Here is" or any introduction
- Do NOT end with explanations like "I maintained..." or "This version..."
- Do NOT include quotes around the output
- The output should be ready to paste directly into a document`,
        style: style,
        originalText: selectionMenu.selectedText,
        replaceSelection: true,
        selectionStart: selectionMenu.selectionStart,
        selectionEnd: selectionMenu.selectionEnd,
      })
      setSelectionMenu(prev => ({ ...prev, isVisible: false }))
      setShowRewriteModal(false)
    }
  }
  
  const handleExpand = () => {
    if (!selectionMenu.selectedText) return
    
    setPendingAiRequest({
      type: 'rewrite',
      instruction: `Expand this passage with more detail and depth:

"${selectionMenu.selectedText}"

Add sensory details, emotional depth, and richer prose. Make it approximately 2-3x longer.

RULES:
- Output ONLY the expanded text, nothing else
- Do NOT start with "Here's" or "Here is" or any introduction
- Do NOT end with explanations like "I added..." or "This version..."
- Do NOT include quotes around the output
- The output should be ready to paste directly into a document`,
      style: 'expand',
      originalText: selectionMenu.selectedText,
      replaceSelection: true,
      selectionStart: selectionMenu.selectionStart,
      selectionEnd: selectionMenu.selectionEnd,
    })
    setSelectionMenu(prev => ({ ...prev, isVisible: false }))
  }
  
  const handleShrink = () => {
    if (!selectionMenu.selectedText) return
    
    setPendingAiRequest({
      type: 'rewrite',
      instruction: `Make this passage more concise:

"${selectionMenu.selectedText}"

Remove unnecessary words, tighten the prose. Reduce length by about 30-50%.

RULES:
- Output ONLY the shortened text, nothing else
- Do NOT start with "Here's" or "Here is" or any introduction
- Do NOT end with explanations like "I removed..." or "This version..."
- Do NOT include quotes around the output
- The output should be ready to paste directly into a document`,
      style: 'shrink',
      originalText: selectionMenu.selectedText,
      replaceSelection: true,
      selectionStart: selectionMenu.selectionStart,
      selectionEnd: selectionMenu.selectionEnd,
    })
    setSelectionMenu(prev => ({ ...prev, isVisible: false }))
  }
  
  const handleDescribe = () => {
    if (!selectionMenu.selectedText) return
    
    // Use the describe feature to add sensory details
    setPendingAiRequest({
      type: 'describe',
      instruction: `Generate rich sensory descriptions for this text:\n\n"${selectionMenu.selectedText}"\n\nProvide descriptions for each sense (sight, sound, smell, taste, touch) plus metaphorical descriptions. Format with clear section headers.`,
      originalText: selectionMenu.selectedText,
      senses: ['sight', 'sound', 'smell', 'taste', 'touch', 'metaphor'],
      replaceSelection: false, // Descriptions are for inspiration, not replacement
      selectionStart: selectionMenu.selectionStart,
      selectionEnd: selectionMenu.selectionEnd,
    })
    setSelectionMenu(prev => ({ ...prev, isVisible: false }))
  }
  
  const handleContinue = () => {
    if (!selectionMenu.selectedText) return
    
    const fullText = editor?.getText() || ''
    const textBeforeSelection = fullText.substring(0, selectionMenu.selectionEnd)
    
    setPendingAiRequest({
      type: 'write',
      instruction: `Continue writing from where this text ends. Match the style, tone, and voice of the existing writing:\n\n"${selectionMenu.selectedText}"\n\nWrite 2-3 natural paragraphs that flow seamlessly from this point.`,
      mode: 'Continue from selection',
      insertAtCursor: true,
      context: textBeforeSelection,
    })
    setSelectionMenu(prev => ({ ...prev, isVisible: false }))
  }
  
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
          <h1 className="text-2xl font-serif font-semibold text-gold-pale">
            {currentChapterId ? 'Chapter Editor' : 'Welcome to Exelsias'}
          </h1>
          {!currentChapterId && (
            <p className="text-gray-400 mt-1">
              Select a chapter from the sidebar to start writing
            </p>
          )}
        </div>
        
        {currentChapterId && (
          <button
            className="px-3 py-1.5 rounded-lg bg-dark-700 text-gray-400 hover:bg-gold-rich/10 hover:text-gold-rich text-sm border border-gold-rich/20"
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
              <h2 className="text-xl font-serif font-semibold text-gray-100 mb-2">
                No Chapter Selected
              </h2>
              <p className="text-gray-400 mb-6">
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
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 px-4 py-2 rounded-full bg-gold-rich text-dark-950 shadow-lg flex items-center gap-2 animate-pulse">
          <div className="spinner !w-4 !h-4 !border-dark-950/30 !border-t-dark-950" />
          <span className="font-medium">AI is writing...</span>
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
      
      {/* Selection Menu - Floating context menu */}
      <SelectionMenu
        isVisible={selectionMenu.isVisible && !isAiGenerating}
        position={selectionMenu.position}
        selectedText={selectionMenu.selectedText}
        isWord={selectionMenu.isWord}
        onRewrite={handleRewrite}
        onExpand={handleExpand}
        onShrink={handleShrink}
        onDescribe={handleDescribe}
        onContinue={handleContinue}
        onClose={handleSelectionMenuClose}
      />
      
      {/* Rewrite Style Modal */}
      <RewriteStyleModal
        isOpen={showRewriteModal}
        onClose={() => setShowRewriteModal(false)}
        onSelect={(style) => handleRewrite(style)}
        selectedText={selectionMenu.selectedText}
      />
    </div>
  )
}

export default Editor
