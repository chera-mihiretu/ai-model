/**
 * Project Sidebar Component
 * =========================
 * Left sidebar showing only the current project's chapters.
 * Dark & Gold luxury theme styling.
 */

import { useState, useEffect } from 'react'
import useStore from '../hooks/useStore'
import { usePythonBridge } from '../hooks/usePythonBridge'
import { clsx } from 'clsx'
import { Document, Packer, Paragraph, TextRun, HeadingLevel, UnderlineType, AlignmentType } from 'docx'
import { saveAs } from 'file-saver'

// Helper: Convert TipTap HTML to DOCX paragraphs using DOMParser for reliable formatting
function htmlToDocxParagraphs(html) {
  if (!html) return []

  const parser = new DOMParser()
  const doc = parser.parseFromString(html, 'text/html')
  const paragraphs = []

  const HEADING_MAP = {
    H1: HeadingLevel.HEADING_1,
    H2: HeadingLevel.HEADING_2,
    H3: HeadingLevel.HEADING_3,
    H4: HeadingLevel.HEADING_4,
    H5: HeadingLevel.HEADING_5,
    H6: HeadingLevel.HEADING_6,
  }

  // Inline formatting tags that accumulate styles as we recurse
  const INLINE_STYLE_TAGS = {
    STRONG: { bold: true },
    B: { bold: true },
    EM: { italics: true },
    I: { italics: true },
    U: { underline: { type: UnderlineType.SINGLE } },
    S: { strike: true },
    STRIKE: { strike: true },
    DEL: { strike: true },
  }

  // Recursively collect TextRun objects from a DOM node
  function getTextRuns(node, styles = {}) {
    const runs = []

    for (const child of node.childNodes) {
      // Text node
      if (child.nodeType === Node.TEXT_NODE) {
        const text = child.textContent
        if (text) {
          runs.push(new TextRun({ text, ...styles }))
        }
        continue
      }

      // Element node
      if (child.nodeType === Node.ELEMENT_NODE) {
        const tag = child.tagName

        // Line break
        if (tag === 'BR') {
          runs.push(new TextRun({ text: '', break: 1 }))
          continue
        }

        // Inline code
        if (tag === 'CODE' && child.parentElement?.tagName !== 'PRE') {
          runs.push(new TextRun({ text: child.textContent || '', font: 'Courier New', ...styles }))
          continue
        }

        // Inline formatting - merge styles and recurse into children
        if (INLINE_STYLE_TAGS[tag]) {
          const merged = { ...styles, ...INLINE_STYLE_TAGS[tag] }
          runs.push(...getTextRuns(child, merged))
          continue
        }

        // For any other inline/unknown element, recurse with current styles
        runs.push(...getTextRuns(child, styles))
      }
    }

    return runs
  }

  // Walk top-level and block-level nodes
  function walkNodes(nodes) {
    for (const node of nodes) {
      // Skip pure whitespace text nodes between block elements
      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent?.trim()
        if (text) {
          paragraphs.push(new Paragraph({ children: [new TextRun(text)] }))
        }
        continue
      }

      if (node.nodeType !== Node.ELEMENT_NODE) continue

      const tag = node.tagName

      // Headings
      if (HEADING_MAP[tag]) {
        const runs = getTextRuns(node)
        paragraphs.push(new Paragraph({
          children: runs.length > 0 ? runs : [new TextRun('')],
          heading: HEADING_MAP[tag],
        }))
        continue
      }

      // Paragraph
      if (tag === 'P') {
        const runs = getTextRuns(node)
        // Always add the paragraph (even if empty) to preserve spacing
        paragraphs.push(new Paragraph({
          children: runs.length > 0 ? runs : [new TextRun('')],
        }))
        continue
      }

      // Div - treat like paragraph
      if (tag === 'DIV') {
        const runs = getTextRuns(node)
        if (runs.length > 0) {
          paragraphs.push(new Paragraph({ children: runs }))
        }
        continue
      }

      // Unordered list
      if (tag === 'UL') {
        for (const li of node.children) {
          if (li.tagName === 'LI') {
            const runs = getTextRuns(li)
            paragraphs.push(new Paragraph({
              children: [
                new TextRun({ text: '\u2022  ' }), // bullet character
                ...(runs.length > 0 ? runs : [new TextRun('')]),
              ],
              indent: { left: 720 }, // 0.5 inch indent
            }))
          }
        }
        continue
      }

      // Ordered list
      if (tag === 'OL') {
        let num = 1
        for (const li of node.children) {
          if (li.tagName === 'LI') {
            const runs = getTextRuns(li)
            paragraphs.push(new Paragraph({
              children: [
                new TextRun({ text: `${num}.  ` }),
                ...(runs.length > 0 ? runs : [new TextRun('')]),
              ],
              indent: { left: 720 },
            }))
            num++
          }
        }
        continue
      }

      // Blockquote
      if (tag === 'BLOCKQUOTE') {
        // Recurse into blockquote children (could contain <p> elements)
        for (const child of node.childNodes) {
          if (child.nodeType === Node.ELEMENT_NODE && child.tagName === 'P') {
            const runs = getTextRuns(child)
            paragraphs.push(new Paragraph({
              children: runs.length > 0 ? runs : [new TextRun('')],
              indent: { left: 720 },
            }))
          } else if (child.nodeType === Node.TEXT_NODE) {
            const text = child.textContent?.trim()
            if (text) {
              paragraphs.push(new Paragraph({
                children: [new TextRun(text)],
                indent: { left: 720 },
              }))
            }
          }
        }
        continue
      }

      // Code block: <pre><code>...</code></pre>
      if (tag === 'PRE') {
        const codeText = node.textContent || ''
        const lines = codeText.split('\n')
        for (const line of lines) {
          paragraphs.push(new Paragraph({
            children: [new TextRun({ text: line, font: 'Courier New', size: 20 })],
          }))
        }
        continue
      }

      // Horizontal rule
      if (tag === 'HR') {
        paragraphs.push(new Paragraph({
          children: [new TextRun({ text: '———————————————————————————' })],
          alignment: AlignmentType.CENTER,
        }))
        continue
      }

      // Fallback: recurse into any other element's children
      walkNodes(node.childNodes)
    }
  }

  walkNodes(doc.body.childNodes)

  // Safety: if nothing was produced, create a single plain-text paragraph
  if (paragraphs.length === 0 && html.trim()) {
    paragraphs.push(new Paragraph({
      children: [new TextRun(doc.body.textContent || '')],
    }))
  }

  return paragraphs
}

// Icons
const Icons = {
  CHAPTER: '📄',
  PLUS: '+',
  EDIT: '✏️',
  TRASH: '🗑️',
  UP: '▲',
  DOWN: '▼',
  DRAG: '⋮⋮',
  BOOK: '📖',
  BRAINDUMP: '📝',
  GENRE: '🎭',
  STYLE: '🎨',
  SYNOPSIS: '📖',
  CHARACTERS: '👥',
  WORLD: '🌍',
  OUTLINE: '📋',
  SCENE: '🎬',
  EXPAND: '▼',
  COLLAPSE: '▶',
  EXPORT: '📤',
}

// Story Bible tabs configuration
const BIBLE_TABS = [
  { id: 'braindump', label: 'Braindump', icon: Icons.BRAINDUMP },
  { id: 'genre', label: 'Genre', icon: Icons.GENRE },
  { id: 'style', label: 'Style', icon: Icons.STYLE },
  { id: 'synopsis', label: 'Synopsis', icon: Icons.SYNOPSIS },
  { id: 'characters', label: 'Characters', icon: Icons.CHARACTERS },
  { id: 'worldElements', label: 'World Building', icon: Icons.WORLD },
  { id: 'outline', label: 'Outline', icon: Icons.OUTLINE },
  { id: 'scenes', label: 'Scene Editor', icon: Icons.SCENE },
]

function ChapterItem({ chapter, index, isActive, onClick, onDelete, onRename, onMoveUp, onMoveDown, onExport, isFirst, isLast }) {
  const [isHovered, setIsHovered] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(chapter.title || `Chapter ${index + 1}`)
  
  const handleRename = () => {
    if (editTitle.trim() && editTitle !== chapter.title) {
      onRename(chapter.id, editTitle.trim())
    }
    setIsEditing(false)
  }
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleRename()
    } else if (e.key === 'Escape') {
      setEditTitle(chapter.title || `Chapter ${index + 1}`)
      setIsEditing(false)
    }
  }
  
  return (
    <div
      className={clsx(
        'group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all duration-200',
        'border border-transparent',
        isActive
          ? 'bg-gold-rich/15 border-gold-rich/30 text-gold-pale'
          : 'hover:bg-gold-rich/5 text-gray-300 hover:text-gray-100'
      )}
      onClick={() => !isEditing && onClick(chapter.id)}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Drag Handle */}
      <span className="text-gray-500 text-xs">{Icons.DRAG}</span>
      
      {/* Chapter Icon & Number */}
      <span className="text-lg">{Icons.CHAPTER}</span>
      <span className="text-xs font-mono text-gray-500 w-6">{index + 1}.</span>
      
      {/* Title */}
      {isEditing ? (
        <input
          type="text"
          className="flex-1 bg-dark-700 px-2 py-1 rounded text-sm text-gray-100 focus:outline-none focus:ring-1 focus:ring-gold-rich border border-gold-rich/20"
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onBlur={handleRename}
          onKeyDown={handleKeyDown}
          onClick={(e) => e.stopPropagation()}
          autoFocus
        />
      ) : (
        <span className="flex-1 truncate text-sm font-medium">
          {chapter.title || `Chapter ${index + 1}`}
        </span>
      )}
      
      {/* Actions (visible on hover) */}
      {isHovered && !isEditing && (
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {!isFirst && (
            <button
              className="w-5 h-5 flex items-center justify-center rounded text-gray-500 hover:text-gold-rich hover:bg-gold-rich/10 text-xs"
              onClick={(e) => {
                e.stopPropagation()
                onMoveUp(chapter.id)
              }}
              title="Move Up"
            >
              {Icons.UP}
            </button>
          )}
          {!isLast && (
            <button
              className="w-5 h-5 flex items-center justify-center rounded text-gray-500 hover:text-gold-rich hover:bg-gold-rich/10 text-xs"
              onClick={(e) => {
                e.stopPropagation()
                onMoveDown(chapter.id)
              }}
              title="Move Down"
            >
              {Icons.DOWN}
            </button>
          )}
          <button
            className="w-5 h-5 flex items-center justify-center rounded text-gray-500 hover:text-gold-rich hover:bg-gold-rich/10 text-xs"
            onClick={(e) => {
              e.stopPropagation()
              setIsEditing(true)
            }}
            title="Rename"
          >
            {Icons.EDIT}
          </button>
          <button
            className="w-5 h-5 flex items-center justify-center rounded text-gray-500 hover:text-gold-rich hover:bg-gold-rich/10 text-xs"
            onClick={(e) => {
              e.stopPropagation()
              onExport?.(chapter)
            }}
            title="Export (.docx)"
          >
            {Icons.EXPORT}
          </button>
          <button
            className="w-5 h-5 flex items-center justify-center rounded text-gray-500 hover:text-red-400 hover:bg-red-400/10 text-xs"
            onClick={(e) => {
              e.stopPropagation()
              onDelete(chapter.id)
            }}
            title="Delete"
          >
            {Icons.TRASH}
          </button>
        </div>
      )}
    </div>
  )
}

// Modal for creating new chapter
function NewChapterModal({ isOpen, onClose, onSubmit, isCreating }) {
  const [title, setTitle] = useState('')
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (title.trim()) {
      onSubmit(title.trim())
      setTitle('')
    }
  }
  
  // Reset when modal closes
  useEffect(() => {
    if (!isOpen) setTitle('')
  }, [isOpen])
  
  if (!isOpen) return null
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 w-full max-w-md mx-4 glass-card p-6 animate-slide-up">
        <h2 className="text-xl font-bold text-gray-100 mb-4">Create New Chapter</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gold-pale mb-2">
              Chapter Title
            </label>
            <input
              type="text"
              className="input"
              placeholder="Enter chapter title..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              autoFocus
              disabled={isCreating}
            />
          </div>
          <div className="flex items-center justify-end gap-3">
            <button 
              type="button" 
              className="btn btn-ghost" 
              onClick={onClose}
              disabled={isCreating}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={!title.trim() || isCreating}
            >
              {isCreating ? (
                <>
                  <div className="spinner !w-4 !h-4" />
                  <span>Creating...</span>
                </>
              ) : (
                <>
                  <span>+</span>
                  <span>Create Chapter</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function ProjectSidebar() {
  const {
    projects,
    currentProjectId,
    currentChapterId,
    currentBibleTab,
    isBibleExpanded,
    setCurrentChapter,
    setCurrentView,
    setCurrentBibleTab,
    toggleBibleExpanded,
    setProjects,
    addNotification,
  } = useStore()
  
  const {
    getProjectsWithChapters,
    createChapter,
    deleteChapter,
    renameChapter,
    moveChapterUp,
    moveChapterDown,
    getChapterContent,
  } = usePythonBridge()
  
  const [isCreatingChapter, setIsCreatingChapter] = useState(false)
  
  // Get current project
  const currentProject = projects.find(p => p.id === currentProjectId)
  const chapters = currentProject?.chapters || []
  
  // Refresh projects
  const refreshProjects = async () => {
    const updatedProjects = await getProjectsWithChapters()
    setProjects(updatedProjects)
  }
  
  // Handle chapter click
  const handleChapterClick = (chapterId) => {
    setCurrentChapter(chapterId)
    setCurrentView('editor')
  }
  
  // Handle add chapter - creates with "Untitled" by default
  const handleAddChapter = async () => {
    if (!currentProjectId) return
    
    setIsCreatingChapter(true)
    try {
      const chapterId = await createChapter(currentProjectId, 'Untitled')
      
      if (chapterId) {
        await refreshProjects()
        setCurrentChapter(chapterId)
        setCurrentView('editor')
      } else {
        addNotification({ type: 'error', message: 'Failed to create chapter' })
      }
    } catch (error) {
      console.error('Error creating chapter:', error)
      addNotification({ type: 'error', message: `Error: ${error.message}` })
    } finally {
      setIsCreatingChapter(false)
    }
  }
  
  // Handle delete chapter
  const handleDeleteChapter = async (chapterId) => {
    const chapter = chapters.find(c => c.id === chapterId)
    if (!chapter) return
    
    if (confirm(`Delete "${chapter.title || 'Untitled Chapter'}"? This cannot be undone.`)) {
      const success = await deleteChapter(chapterId)
      if (success) {
        await refreshProjects()
        // If deleted chapter was active, clear selection
        if (currentChapterId === chapterId) {
          setCurrentChapter(null)
        }
        addNotification({ type: 'success', message: 'Chapter deleted' })
      }
    }
  }
  
  // Handle rename chapter
  const handleRenameChapter = async (chapterId, newTitle) => {
    if (!renameChapter) {
      addNotification({ type: 'warning', message: 'Rename not available' })
      return
    }
    
    const success = await renameChapter(chapterId, newTitle)
    if (success) {
      await refreshProjects()
    }
  }
  
  // Handle move chapter up
  const handleMoveUp = async (chapterId) => {
    const success = await moveChapterUp(chapterId)
    if (success) {
      await refreshProjects()
    }
  }
  
  // Handle move chapter down
  const handleMoveDown = async (chapterId) => {
    const success = await moveChapterDown(chapterId)
    if (success) {
      await refreshProjects()
    }
  }
  
  // Handle export chapter as .docx
  const handleExportChapter = async (chapter) => {
    try {
      addNotification({ type: 'info', message: 'Preparing export...' })
      
      // Get chapter content
      const content = await getChapterContent(chapter.id)
      
      if (!content) {
        addNotification({ type: 'warning', message: 'Chapter has no content to export' })
        return
      }
      
      // Convert HTML to DOCX paragraphs with formatting preserved
      const contentParagraphs = htmlToDocxParagraphs(content)
      
      // Create DOCX document
      const doc = new Document({
        sections: [{
          children: [
            new Paragraph({
              text: chapter.title || 'Chapter',
              heading: HeadingLevel.HEADING_1,
            }),
            new Paragraph({ text: '' }),
            ...contentParagraphs,
          ],
        }],
      })
      
      const docxBlob = await Packer.toBlob(doc)
      const safeTitle = (chapter.title || 'chapter')
        .replace(/[^a-z0-9]/gi, '_')
        .substring(0, 50)
      saveAs(docxBlob, `${safeTitle}.docx`)
      
      addNotification({ type: 'success', message: `Exported "${chapter.title}" to ${safeTitle}.docx` })
    } catch (error) {
      console.error('Export chapter failed:', error)
      addNotification({ type: 'error', message: 'Failed to export chapter' })
    }
  }
  
  // Handle Bible tab click
  const handleBibleTabClick = (tabId) => {
    setCurrentBibleTab(tabId)
    
    // Route to appropriate view
    switch (tabId) {
      case 'characters':
        setCurrentView('characters')
        break
      case 'worldElements':
        setCurrentView('worldBuilding')
        break
      case 'scenes':
        setCurrentView('scenes')
        break
      default:
        setCurrentView('storyBible')
        break
    }
  }
  
  if (!currentProjectId || !currentProject) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-6 text-center">
        <p className="text-gray-400">No project selected</p>
      </div>
    )
  }
  
  return (
    <div className="h-full flex flex-col p-4 overflow-hidden">
      {/* Project Header */}
      <div className="mb-4">
        <h2 className="text-lg font-serif font-semibold text-gold-pale truncate" title={currentProject.name}>
          {currentProject.name}
        </h2>
        <p className="text-xs text-gray-400 mt-1">
          {chapters.length} chapter{chapters.length !== 1 ? 's' : ''}
        </p>
      </div>
      
      {/* Add Chapter Button */}
      <button
        className="w-full mb-4 px-4 py-2 rounded-lg bg-gold-rich/10 text-gold-rich hover:bg-gold-rich/20 transition-colors flex items-center justify-center gap-2 font-medium border border-gold-rich/30"
        onClick={handleAddChapter}
        disabled={isCreatingChapter}
      >
        {isCreatingChapter ? (
          <>
            <div className="spinner !w-4 !h-4" />
            <span>Creating...</span>
          </>
        ) : (
          <>
            <span className="text-lg font-bold">{Icons.PLUS}</span>
            <span>New Chapter</span>
          </>
        )}
      </button>
      
      {/* Chapters List */}
      <div className="flex-1 overflow-y-auto space-y-1">
        {chapters.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-3 opacity-50">{Icons.CHAPTER}</div>
            <p className="text-gray-400 text-sm">No chapters yet</p>
            <p className="text-gray-500 text-xs mt-1">Click "New Chapter" to get started</p>
          </div>
        ) : (
          chapters.map((chapter, index) => (
            <ChapterItem
              key={chapter.id}
              chapter={chapter}
              index={index}
              isActive={currentChapterId === chapter.id}
              onClick={handleChapterClick}
              onDelete={handleDeleteChapter}
              onRename={handleRenameChapter}
              onMoveUp={handleMoveUp}
              onMoveDown={handleMoveDown}
              onExport={handleExportChapter}
              isFirst={index === 0}
              isLast={index === chapters.length - 1}
            />
          ))
        )}
      </div>
      
      {/* Divider */}
      <div className="border-t border-gold-rich/20 my-4" />
      
      {/* Story Bible Section */}
      <div>
        <button
          className={clsx(
            'w-full px-4 py-3 rounded-lg text-left flex items-center gap-3',
            'transition-all duration-200',
            isBibleExpanded 
              ? 'bg-gold-rich/15 text-gold-pale border border-gold-rich/30'
              : 'bg-dark-700/50 text-gray-300 hover:bg-dark-700 border border-transparent'
          )}
          onClick={toggleBibleExpanded}
        >
          <span>{Icons.BOOK}</span>
          <span className="flex-1 font-medium">Story Bible</span>
          <span className="text-xs">{isBibleExpanded ? Icons.EXPAND : Icons.COLLAPSE}</span>
        </button>
        
        {isBibleExpanded && (
          <div className="mt-2 space-y-1 animate-fade-in max-h-48 overflow-y-auto">
            {BIBLE_TABS.map(tab => (
              <button
                key={tab.id}
                className={clsx(
                  'bible-tab w-full text-left flex items-center gap-2',
                  currentBibleTab === tab.id && 'active'
                )}
                onClick={() => handleBibleTabClick(tab.id)}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        )}
      </div>
      
    </div>
  )
}

export default ProjectSidebar
