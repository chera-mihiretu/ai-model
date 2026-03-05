/**
 * Dashboard Component
 * ===================
 * Landing page showing projects organized in folders and series.
 * Dark & Gold luxury theme with elegant styling.
 */

import { useState, useEffect, useRef, useMemo } from 'react'
import useStore from '../hooks/useStore'
import { usePythonBridge } from '../hooks/usePythonBridge'
import { clsx } from 'clsx'
import JSZip from 'jszip'
import { saveAs } from 'file-saver'
import { Document, Packer, Paragraph, TextRun, HeadingLevel, UnderlineType, AlignmentType } from 'docx'

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

import ImportNovel from './ImportNovel'
import SeriesManager from './SeriesManager'

// Icons
const Icons = {
  PROJECT: '📄',
  FOLDER: '📁',
  SERIES: '📚',
  PLUS: '+',
  BOOK: '📖',
  CHAPTER: '📄',
  CLOCK: '🕐',
  TRASH: '🗑️',
  EDIT: '✏️',
  IMPORT: '📥',
  BACK: '←',
  CLOSE: '✕',
  MENU: '⋯',
}

// Project Card - with gold accent styling
function ProjectCard({ project, onSelect, onDelete, onRename, onDuplicate, onExport }) {
  const [showMenu, setShowMenu] = useState(false)
  const menuRef = useRef(null)
  
  const wordCount = project.word_count || 0
  
  // Format timestamp
  const formatTime = (timestamp) => {
    if (!timestamp) return 'Just now'
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now - date
    
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`
    return date.toLocaleDateString()
  }
  
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
  
  return (
    <div
      className={clsx(
        'relative group cursor-pointer',
        'bg-dark-800 rounded-xl',
        'shadow-card hover:shadow-card-hover',
        'border border-gold-rich/20 hover:border-gold-rich/40',
        'transition-all duration-300 hover:-translate-y-1',
        'min-h-[220px] flex flex-col'
      )}
      style={{ zIndex: showMenu ? 50 : 1 }}
      onClick={() => onSelect(project)}
    >
      {/* Three-dot Menu Button */}
      <div className="absolute top-3 right-3" ref={menuRef} style={{ zIndex: 200 }}>
        <button
          className={clsx(
            'w-8 h-8 rounded-lg flex items-center justify-center',
            'text-text-muted hover:text-gold-rich hover:bg-gold-rich/10',
            'opacity-0 group-hover:opacity-100 transition-all'
          )}
          onClick={(e) => {
            e.stopPropagation()
            setShowMenu(!showMenu)
          }}
        >
          ⋯
        </button>
        
        {showMenu && (
          <div className="absolute right-0 top-10 bg-dark-800 rounded-xl shadow-lg shadow-black/50 border border-gold-rich/20 min-w-[160px] py-2" style={{ zIndex: 99999 }}>
            <button
              className="dropdown-item flex items-center gap-2 w-full"
              onClick={(e) => {
                e.stopPropagation()
                onExport?.(project, 'zip')
                setShowMenu(false)
              }}
            >
              📦 Export (.zip)
            </button>
            <button
              className="dropdown-item flex items-center gap-2 w-full"
              onClick={(e) => {
                e.stopPropagation()
                onDuplicate?.(project)
                setShowMenu(false)
              }}
            >
              📋 Duplicate
            </button>
            <button
              className="dropdown-item flex items-center gap-2 w-full"
              onClick={(e) => {
                e.stopPropagation()
                onRename(project)
                setShowMenu(false)
              }}
            >
              ✏️ Rename
            </button>
            <button
              className="dropdown-item flex items-center gap-2 w-full text-red-400 hover:!bg-red-500/10"
              onClick={(e) => {
                e.stopPropagation()
                onDelete(project)
                setShowMenu(false)
              }}
            >
              🗑️ Delete
            </button>
          </div>
        )}
      </div>
      
      {/* Project Content */}
      <div className="flex-1 flex items-center justify-center p-6">
        <h3 className="text-xl font-serif font-medium text-gold-soft text-center leading-tight">
          {project.name}
        </h3>
      </div>
      
      {/* Stats at bottom */}
      <div className="text-center pb-4 px-4 border-t border-gold-rich/10 pt-3">
        <p className="text-sm text-gray-400">
          {wordCount.toLocaleString()} words
        </p>
        <p className="text-xs text-gray-500 mt-0.5">
          {formatTime(project.updated_at)}
        </p>
      </div>
    </div>
  )
}

// Folder Card - elegant dark gold styling
function FolderCard({ folder, onClick, onDelete, onRename, onDuplicateProject, onDeleteProject, onExportProject }) {
  const [showMenu, setShowMenu] = useState(false)
  const [showProjectMenu, setShowProjectMenu] = useState(null)
  const menuRef = useRef(null)
  const projectMenuRef = useRef(null)
  
  const projects = folder.projects || []
  const projectCount = projects.length
  const papersToShow = Math.min(projectCount, 3)
  
  const formatTime = (timestamp) => {
    if (!timestamp) return 'Just now'
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now - date
    
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`
    return date.toLocaleDateString()
  }
  
  // Close menus when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false)
      }
      if (projectMenuRef.current && !projectMenuRef.current.contains(event.target)) {
        setShowProjectMenu(null)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  // Paper angles for stacking effect
  const paperAngles = [-2, 1, -0.5]
  
  return (
    <div
      className="relative group cursor-pointer transition-all duration-300 hover:-translate-y-1"
      onClick={() => onClick(folder)}
      style={{ zIndex: showMenu || showProjectMenu !== null ? 100 : 1 }}
    >
      {/* Folder shape with tab */}
      <div className="relative">
        {/* Folder tab */}
        <div 
          className="absolute -top-2 left-3 w-16 h-4 rounded-t-lg"
          style={{ backgroundColor: '#1E1E28' }}
        />
        
        {/* Folder body */}
        <div
          className="relative rounded-xl overflow-hidden border border-gold-rich/20 hover:border-gold-rich/40 transition-all"
          style={{ 
            background: 'linear-gradient(145deg, #1E1E28, #16161D)',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3), 0 0 1px rgba(212, 175, 55, 0.2)'
          }}
        >
          {/* Menu Button */}
          <div className="absolute top-3 right-3" ref={menuRef} style={{ zIndex: 200 }}>
            <button
              className={clsx(
                'w-8 h-8 rounded-lg flex items-center justify-center',
                'text-text-muted hover:text-gold-rich hover:bg-gold-rich/10',
                'opacity-0 group-hover:opacity-100 transition-all'
              )}
              onClick={(e) => {
                e.stopPropagation()
                setShowMenu(!showMenu)
              }}
            >
              {Icons.MENU}
            </button>
            
            {showMenu && (
              <div 
                className="absolute right-0 top-10 bg-dark-800 rounded-xl shadow-lg shadow-black/50 border border-gold-rich/20 min-w-[140px] py-2"
                style={{ zIndex: 99999 }}
              >
                <button
                  className="dropdown-item flex items-center gap-2 w-full"
                  onClick={(e) => {
                    e.stopPropagation()
                    onRename(folder)
                    setShowMenu(false)
                  }}
                >
                  {Icons.EDIT} Rename
                </button>
                <button
                  className="dropdown-item flex items-center gap-2 w-full text-red-400 hover:!bg-red-500/10"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDelete(folder)
                    setShowMenu(false)
                  }}
                >
                  {Icons.TRASH} Delete
                </button>
              </div>
            )}
          </div>
          
          {/* Folder Content */}
          <div className="p-4 pt-5 pb-3">
            <h3 className="text-xl font-serif font-medium text-gold-soft leading-tight">
              {folder.name}
            </h3>
          </div>
          
          {/* Papers inside folder */}
          {papersToShow > 0 && (
            <div className="relative px-3 pb-3" style={{ minHeight: '80px' }} ref={projectMenuRef}>
              {projects.slice(0, 3).map((project, index) => (
                <div
                  key={project.id || index}
                  className="absolute bg-dark-700 rounded-lg shadow-sm border border-gold-rich/10 p-3 group/paper"
                  style={{
                    width: 'calc(100% - 24px)',
                    height: '70px',
                    transform: `rotate(${paperAngles[index]}deg)`,
                    top: `${index * 4}px`,
                    left: '12px',
                    zIndex: 10 - index,
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <p className="text-sm font-medium text-text-secondary truncate pr-6">
                    {project.name || 'Untitled'}
                  </p>
                  
                  {/* Three dot menu on each paper */}
                  <button
                    className={clsx(
                      'absolute top-2 right-2 w-6 h-6 rounded flex items-center justify-center',
                      'text-text-muted hover:text-gold-rich hover:bg-gold-rich/10',
                      'opacity-0 group-hover/paper:opacity-100 transition-all text-xs'
                    )}
                    onClick={(e) => {
                      e.stopPropagation()
                      setShowProjectMenu(showProjectMenu === project.id ? null : project.id)
                    }}
                  >
                    ⋯
                  </button>
                  
                  {/* Project dropdown menu */}
                  {showProjectMenu === project.id && (
                    <div 
                      className="absolute right-0 top-8 bg-dark-800 rounded-xl shadow-lg shadow-black/50 border border-gold-rich/20 min-w-[120px] py-2"
                      style={{ zIndex: 99999 }}
                    >
                      <button
                        className="dropdown-item flex items-center gap-2 w-full text-sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          onDuplicateProject?.(project, folder)
                          setShowProjectMenu(null)
                        }}
                      >
                        📋 Duplicate
                      </button>
                      <button
                        className="dropdown-item flex items-center gap-2 w-full text-sm text-red-400 hover:!bg-red-500/10"
                        onClick={(e) => {
                          e.stopPropagation()
                          onDeleteProject?.(project)
                          setShowProjectMenu(null)
                        }}
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          
          {/* Empty state inside folder */}
          {papersToShow === 0 && (
            <div className="px-4 pb-4 pt-2">
              <div className="h-16 rounded-lg border-2 border-dashed border-gold-rich/20 flex items-center justify-center">
                <span className="text-xs text-gray-500">No projects</span>
              </div>
            </div>
          )}
          
          {/* Stats at bottom */}
          <div className="px-4 pb-4 pt-2">
            <p className="text-sm text-gray-400">
              {projectCount} project{projectCount !== 1 ? 's' : ''}
            </p>
            <p className="text-xs text-gray-500 mt-0.5">
              {formatTime(folder.updated_at)}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

// Series Card - elegant dark gold styling with SERIES badge
function SeriesCard({ series, onClick, onDelete, onRename, onDuplicateProject, onDeleteProject, onExportProject }) {
  const [showMenu, setShowMenu] = useState(false)
  const [showProjectMenu, setShowProjectMenu] = useState(null)
  const menuRef = useRef(null)
  const projectMenuRef = useRef(null)
  
  const projects = series.projects || []
  const projectCount = projects.length
  const papersToShow = Math.min(projectCount, 3)
  
  const formatTime = (timestamp) => {
    if (!timestamp) return 'Just now'
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now - date
    
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`
    return date.toLocaleDateString()
  }
  
  // Close menus when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false)
      }
      if (projectMenuRef.current && !projectMenuRef.current.contains(event.target)) {
        setShowProjectMenu(null)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  // Paper angles for stacking effect
  const paperAngles = [-2, 1, -0.5]
  
  return (
    <div
      className="relative group cursor-pointer transition-all duration-300 hover:-translate-y-1"
      onClick={() => onClick(series)}
      style={{ zIndex: showMenu || showProjectMenu !== null ? 100 : 1 }}
    >
      {/* Folder shape with tab */}
      <div className="relative">
        {/* Folder tab */}
        <div 
          className="absolute -top-2 left-3 w-16 h-4 rounded-t-lg"
          style={{ backgroundColor: '#1E1E28' }}
        />
        
        {/* Folder body */}
        <div
          className="relative rounded-xl overflow-hidden border border-gold-rich/20 hover:border-gold-rich/40 transition-all"
          style={{ 
            background: 'linear-gradient(145deg, #1E1E28, #16161D)',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3), 0 0 1px rgba(212, 175, 55, 0.2)'
          }}
        >
          {/* Menu Button */}
          <div className="absolute top-3 right-3" ref={menuRef} style={{ zIndex: 200 }}>
            <button
              className={clsx(
                'w-8 h-8 rounded-lg flex items-center justify-center',
                'text-text-muted hover:text-gold-rich hover:bg-gold-rich/10',
                'opacity-0 group-hover:opacity-100 transition-all'
              )}
              onClick={(e) => {
                e.stopPropagation()
                setShowMenu(!showMenu)
              }}
            >
              {Icons.MENU}
            </button>
            
            {showMenu && (
              <div 
                className="absolute right-0 top-10 bg-dark-800 rounded-xl shadow-lg shadow-black/50 border border-gold-rich/20 min-w-[140px] py-2"
                style={{ zIndex: 99999 }}
              >
                <button
                  className="dropdown-item flex items-center gap-2 w-full"
                  onClick={(e) => {
                    e.stopPropagation()
                    onRename(series)
                    setShowMenu(false)
                  }}
                >
                  {Icons.EDIT} Rename
                </button>
                <button
                  className="dropdown-item flex items-center gap-2 w-full text-red-400 hover:!bg-red-500/10"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDelete(series)
                    setShowMenu(false)
                  }}
                >
                  {Icons.TRASH} Delete
                </button>
              </div>
            )}
          </div>
          
          {/* Series Badge */}
          <div className="px-4 pt-4">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-gold-rich/20 text-gold-rich border border-gold-rich/30">
              {Icons.SERIES} SERIES
            </span>
          </div>
          
          {/* Folder Content */}
          <div className="p-4 pt-2 pb-3">
            <h3 className="text-xl font-serif font-medium text-gold-soft leading-tight">
              {series.name}
            </h3>
          </div>
          
          {/* Papers inside folder */}
          {papersToShow > 0 && (
            <div className="relative px-3 pb-3" style={{ minHeight: '80px' }} ref={projectMenuRef}>
              {projects.slice(0, 3).map((project, index) => (
                <div
                  key={project.id || index}
                  className="absolute bg-dark-700 rounded-lg shadow-sm border border-gold-rich/10 p-3 group/paper"
                  style={{
                    width: 'calc(100% - 24px)',
                    height: '70px',
                    transform: `rotate(${paperAngles[index]}deg)`,
                    top: `${index * 4}px`,
                    left: '12px',
                    zIndex: 10 - index,
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <p className="text-sm font-medium text-text-secondary truncate pr-6">
                    {project.name || 'Untitled'}
                  </p>
                  
                  {/* Three dot menu on each paper */}
                  <button
                    className={clsx(
                      'absolute top-2 right-2 w-6 h-6 rounded flex items-center justify-center',
                      'text-text-muted hover:text-gold-rich hover:bg-gold-rich/10',
                      'opacity-0 group-hover/paper:opacity-100 transition-all text-xs'
                    )}
                    onClick={(e) => {
                      e.stopPropagation()
                      setShowProjectMenu(showProjectMenu === project.id ? null : project.id)
                    }}
                  >
                    ⋯
                  </button>
                  
                  {/* Project dropdown menu */}
                  {showProjectMenu === project.id && (
                    <div 
                      className="absolute right-0 top-8 bg-dark-800 rounded-xl shadow-lg shadow-black/50 border border-gold-rich/20 min-w-[120px] py-2"
                      style={{ zIndex: 99999 }}
                    >
                      <button
                        className="dropdown-item flex items-center gap-2 w-full text-sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          onDuplicateProject?.(project, series)
                          setShowProjectMenu(null)
                        }}
                      >
                        📋 Duplicate
                      </button>
                      <button
                        className="dropdown-item flex items-center gap-2 w-full text-sm text-red-400 hover:!bg-red-500/10"
                        onClick={(e) => {
                          e.stopPropagation()
                          onDeleteProject?.(project)
                          setShowProjectMenu(null)
                        }}
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          
          {/* Empty state inside folder */}
          {papersToShow === 0 && (
            <div className="px-4 pb-4 pt-2">
              <div className="h-16 rounded-lg border-2 border-dashed border-gold-rich/20 flex items-center justify-center">
                <span className="text-xs text-gray-500">No projects</span>
              </div>
            </div>
          )}
          
          {/* Stats at bottom */}
          <div className="px-4 pb-4 pt-2">
            <p className="text-sm text-gray-400">
              {projectCount} project{projectCount !== 1 ? 's' : ''}
            </p>
            <p className="text-xs text-gray-500 mt-0.5">
              {formatTime(series.updated_at)}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

// Feature Card with gold accent
function FeatureCard() {
  return (
    <div className="relative">
      {/* Stacked cards behind */}
      <div className="absolute top-2 left-2 right-2 bottom-0 bg-dark-700 rounded-xl transform rotate-2 border border-gold-rich/10" />
      <div className="absolute top-1 left-1 right-1 bottom-0 bg-dark-750 rounded-xl transform rotate-1 border border-gold-rich/10" />
      
      {/* Main card */}
      <div className="relative bg-dark-800 rounded-xl shadow-card border border-gold-rich/20 p-6 min-h-[200px]">
        {/* Close button */}
        <button className="absolute top-3 right-3 text-text-muted hover:text-gold-rich text-lg">
          ×
        </button>
        
        {/* Content */}
        <div className="text-center pt-4">
          <span className="text-xs font-semibold text-gold-rich uppercase tracking-wider">
            NEW
          </span>
          <h3 className="text-lg font-serif font-semibold text-text-primary mt-2 leading-tight">
            AI-Powered
            <br />
            Writing Assistant
          </h3>
          <p className="text-sm text-text-muted mt-3">
            Let Exelsias help you write
            <br />
            your next chapter.
          </p>
          <button className="mt-4 px-6 py-2 border border-gold-rich/30 rounded-full text-sm text-gold-rich hover:bg-gold-rich/10 transition-colors">
            Learn More
          </button>
        </div>
      </div>
    </div>
  )
}

// Header Icons
const HeaderIcons = {
  PLUS: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
    </svg>
  ),
  IMPORT: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
    </svg>
  ),
  PROJECT: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  ),
  FOLDER: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
    </svg>
  ),
  SERIES: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
    </svg>
  ),
  CHEVRON_DOWN: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  ),
  MINIMIZE: (
    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
    </svg>
  ),
  MAXIMIZE: (
    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
    </svg>
  ),
  CLOSE: (
    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
}

// Window Controls Component
function WindowControls() {
  return (
    <div className="flex items-center ml-2">
      <button
        className="w-7 h-7 flex items-center justify-center rounded text-text-muted hover:bg-white/10 hover:text-text-primary transition-colors"
        onClick={() => window.api?.windowMinimize?.()}
        title="Minimize"
      >
        {HeaderIcons.MINIMIZE}
      </button>
      <button
        className="w-7 h-7 flex items-center justify-center rounded text-text-muted hover:bg-white/10 hover:text-text-primary transition-colors"
        onClick={() => window.api?.windowMaximize?.()}
        title="Maximize"
      >
        {HeaderIcons.MAXIMIZE}
      </button>
      <button
        className="w-7 h-7 flex items-center justify-center rounded text-text-muted hover:bg-red-500/80 hover:text-white transition-colors"
        onClick={() => window.api?.windowClose?.()}
        title="Close"
      >
        {HeaderIcons.CLOSE}
      </button>
    </div>
  )
}

// New Button Dropdown
function NewButtonDropdown({ onCreateProject, onCreateFolder, onCreateSeries }) {
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef(null)
  
  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  return (
    <div className="relative" ref={menuRef} style={{ zIndex: 9999 }}>
      <button
        className={clsx(
          'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-200',
          'bg-gold-rich/10 text-gold-rich hover:bg-gold-rich/20 border border-gold-rich/30 hover:border-gold-rich/50',
          isOpen && 'bg-gold-rich/20 border-gold-rich/50'
        )}
        onClick={() => setIsOpen(!isOpen)}
      >
        {HeaderIcons.PLUS}
        <span>New</span>
        <span className={clsx('transition-transform duration-200', isOpen && 'rotate-180')}>
          {HeaderIcons.CHEVRON_DOWN}
        </span>
      </button>
      
      {isOpen && (
        <div 
          className="absolute left-0 top-full mt-2 bg-dark-800 rounded-xl shadow-lg shadow-black/50 border border-gold-rich/20 min-w-[180px] py-2 animate-slide-up"
          style={{ zIndex: 99999 }}
        >
          <button
            className="dropdown-item flex items-center gap-3 w-full px-4 py-2.5 text-text-secondary hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
            onClick={() => {
              onCreateProject()
              setIsOpen(false)
            }}
          >
            <span className="text-gold-rich/70">{HeaderIcons.PROJECT}</span>
            <span>Project</span>
          </button>
          <button
            className="dropdown-item flex items-center gap-3 w-full px-4 py-2.5 text-text-secondary hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
            onClick={() => {
              onCreateFolder()
              setIsOpen(false)
            }}
          >
            <span className="text-gold-rich/70">{HeaderIcons.FOLDER}</span>
            <span>Folder</span>
          </button>
          <button
            className="dropdown-item flex items-center gap-3 w-full px-4 py-2.5 text-text-secondary hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
            onClick={() => {
              onCreateSeries()
              setIsOpen(false)
            }}
          >
            <span className="text-gold-rich/70">{HeaderIcons.SERIES}</span>
            <span>Series</span>
          </button>
        </div>
      )}
    </div>
  )
}

// Create Modal (for Project, Folder, or Series)
function CreateModal({ isOpen, onClose, onCreate, type = 'project' }) {
  const [name, setName] = useState('')
  const [genre, setGenre] = useState('')
  
  const genres = [
    'Fantasy', 'Sci-Fi', 'Romance', 'Mystery', 'Thriller', 
    'Horror', 'Literary Fiction', 'Historical', 'Young Adult', 'Other'
  ]
  
  const titles = {
    project: 'Create New Project',
    folder: 'Create New Folder',
    series: 'Create New Series',
  }
  
  const placeholders = {
    project: 'My Amazing Story',
    folder: 'My Folder',
    series: 'My Series',
  }
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (name.trim()) {
      onCreate(name.trim(), genre, type)
      setName('')
      setGenre('')
      onClose()
    }
  }
  
  useEffect(() => {
    if (!isOpen) {
      setName('')
      setGenre('')
    }
  }, [isOpen])
  
  if (!isOpen) return null
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative z-10 w-full max-w-md mx-4 glass-card p-6 animate-slide-up">
        <h2 className="text-xl font-semibold text-text-primary mb-6">
          {titles[type]}
        </h2>
        
        <form onSubmit={handleSubmit}>
          {/* Name */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gold-pale mb-2">
              Name *
            </label>
            <input
              type="text"
              className="input"
              placeholder={placeholders[type]}
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
          </div>
          
          {/* Genre - only for projects */}
          {type === 'project' && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gold-pale mb-2">
                Genre
              </label>
              <select
                className="input"
                value={genre}
                onChange={(e) => setGenre(e.target.value)}
              >
                <option value="">Select a genre...</option>
                {genres.map(g => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
            </div>
          )}
          
          {/* Actions */}
          <div className="flex items-center justify-end gap-3 mt-6">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!name.trim()}
            >
              Create {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Rename Modal (for Project, Folder, or Series)
function RenameModal({ isOpen, onClose, onRename, currentName, type = 'project' }) {
  const [name, setName] = useState('')
  
  const titles = {
    project: 'Rename Project',
    folder: 'Rename Folder',
    series: 'Rename Series',
  }
  
  useEffect(() => {
    if (isOpen && currentName) {
      setName(currentName)
    }
    if (!isOpen) {
      setName('')
    }
  }, [isOpen, currentName])
  
  const handleSubmit = (e) => {
    e.preventDefault()
    if (name.trim() && name.trim() !== currentName) {
      onRename(name.trim())
      onClose()
    }
  }
  
  if (!isOpen) return null
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative z-10 w-full max-w-md mx-4 glass-card p-6 animate-slide-up">
        <h2 className="text-xl font-semibold text-text-primary mb-6">
          {titles[type]}
        </h2>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gold-pale mb-2">
              New Name *
            </label>
            <input
              type="text"
              className="input"
              placeholder={`Enter new ${type} name...`}
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
          </div>
          
          <div className="flex items-center justify-end gap-3 mt-6">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!name.trim() || name.trim() === currentName}
            >
              Rename
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Recycle Bin Modal
function RecycleBinModal({ 
  isOpen, 
  onClose, 
  items, 
  loading, 
  onRestore, 
  onPermanentDelete, 
  onEmptyBin 
}) {
  if (!isOpen) return null
  
  const formatDate = (dateStr) => {
    if (!dateStr) return 'Unknown'
    const date = new Date(dateStr)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  
  const getItemIcon = (itemType) => {
    switch (itemType) {
      case 'folder':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
        )
      case 'series':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
        )
      default:
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        )
    }
  }
  
  const getItemName = (item) => {
    return item.item_data?.name || 'Unknown'
  }
  
  const getProjectCount = (item) => {
    if (item.item_type === 'project') return 0
    return item.item_data?.projects?.length || 0
  }
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative z-10 w-full max-w-2xl mx-4 glass-card p-6 animate-slide-up max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <svg className="w-6 h-6 text-gold-rich" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            <h2 className="text-xl font-semibold text-text-primary">
              Recycle Bin
            </h2>
          </div>
          
          {items.length > 0 && (
            <button
              className="text-sm text-red-400 hover:text-red-300 transition-colors"
              onClick={() => {
                if (confirm('Permanently delete all items in the recycle bin? This cannot be undone.')) {
                  onEmptyBin()
                }
              }}
            >
              Empty Recycle Bin
            </button>
          )}
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="spinner" />
            </div>
          ) : items.length === 0 ? (
            <div className="text-center py-12">
              <svg className="w-16 h-16 mx-auto text-gray-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              <p className="text-gray-400">Recycle bin is empty</p>
            </div>
          ) : (
            <div className="space-y-3">
              {items.map(item => (
                <div 
                  key={item.id}
                  className="glass p-4 rounded-lg border border-white/5 hover:border-gold-rich/30 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      <div className="text-gold-rich/70 mt-0.5">
                        {getItemIcon(item.item_type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-text-primary truncate">
                            {getItemName(item)}
                          </span>
                          <span className="text-xs px-2 py-0.5 rounded bg-white/5 text-text-muted capitalize">
                            {item.item_type}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 mt-1 text-sm text-text-muted">
                          <span>Deleted: {formatDate(item.deleted_at)}</span>
                          {getProjectCount(item) > 0 && (
                            <span className="text-gold-pale">
                              {getProjectCount(item)} project{getProjectCount(item) !== 1 ? 's' : ''} inside
                            </span>
                          )}
                        </div>
                        
                        {/* Show nested projects for folders/series */}
                        {(item.item_type === 'folder' || item.item_type === 'series') && 
                          item.item_data?.projects?.length > 0 && (
                          <div className="mt-2 pl-2 border-l border-white/10">
                            <div className="text-xs text-text-muted mb-1">Contains:</div>
                            <div className="flex flex-wrap gap-1">
                              {item.item_data.projects.slice(0, 5).map((proj, idx) => (
                                <span 
                                  key={idx}
                                  className="text-xs px-2 py-0.5 rounded bg-white/5 text-text-secondary"
                                >
                                  {proj.name}
                                </span>
                              ))}
                              {item.item_data.projects.length > 5 && (
                                <span className="text-xs text-text-muted">
                                  +{item.item_data.projects.length - 5} more
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        className="px-3 py-1.5 text-sm rounded bg-gold-rich/20 text-gold-rich hover:bg-gold-rich/30 transition-colors"
                        onClick={() => onRestore(item)}
                        title="Restore"
                      >
                        Restore
                      </button>
                      <button
                        className="px-3 py-1.5 text-sm rounded bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
                        onClick={() => {
                          const projectCount = getProjectCount(item)
                          const msg = projectCount > 0 
                            ? `Permanently delete "${getItemName(item)}" and its ${projectCount} project(s)? This cannot be undone.`
                            : `Permanently delete "${getItemName(item)}"? This cannot be undone.`
                          if (confirm(msg)) {
                            onPermanentDelete(item)
                          }
                        }}
                        title="Delete Permanently"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-white/10">
          <button
            className="btn btn-ghost"
            onClick={onClose}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

// Folder View - when inside a folder
function FolderView({ folder, onBack, onSelectProject, onCreateProject, onDeleteProject, onRenameProject, onDuplicateProject, onExportProject }) {
  const formatTime = (timestamp) => {
    if (!timestamp) return 'Just now'
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now - date
    
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`
    return date.toLocaleDateString()
  }
  
  const projects = folder.projects || []
  
  return (
    <div className="h-full flex flex-col">
      {/* Folder Header */}
      <div className="px-8 py-6">
        <div className="max-w-5xl mx-auto">
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-text-muted mb-2">
            <button 
              className="hover:text-gold-rich transition-colors"
              onClick={onBack}
            >
              Home
            </button>
            <span className="text-text-light">›</span>
            <span className="text-gold-rich">{folder.name}</span>
          </div>
          
          {/* Folder Title */}
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-serif font-medium text-gold-rich">
                {folder.name}
              </h1>
              <p className="text-text-muted mt-1">
                {projects.length} project{projects.length !== 1 ? 's' : ''} • Last edited {formatTime(folder.updated_at)}
              </p>
            </div>
            
            <div className="flex items-center gap-2">
              <button className="w-8 h-8 rounded-lg flex items-center justify-center text-text-muted hover:text-gold-rich hover:bg-gold-rich/10">
                {Icons.MENU}
              </button>
              <button 
                className="w-8 h-8 rounded-lg flex items-center justify-center text-text-muted hover:text-gold-rich hover:bg-gold-rich/10"
                onClick={onBack}
              >
                {Icons.CLOSE}
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Projects Grid */}
      <div className="flex-1 overflow-y-auto px-8 pb-8">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {projects.map(project => (
              <ProjectCard
                key={project.id}
                project={project}
                onSelect={onSelectProject}
                onDelete={onDeleteProject}
                onRename={onRenameProject}
                onDuplicate={onDuplicateProject}
                onExport={onExportProject}
              />
            ))}
            
            {/* Add Project Button */}
            <button
              className={clsx(
                'min-h-[180px] rounded-xl',
                'border-2 border-dashed border-gold-rich/30',
                'flex flex-col items-center justify-center',
                'text-text-muted hover:text-gold-rich hover:border-gold-rich/50',
                'transition-all duration-200'
              )}
              onClick={onCreateProject}
            >
              <span className="text-3xl mb-2">+</span>
              <span className="text-sm font-medium">New Project</span>
            </button>
          </div>
          
          {/* Empty State */}
          {projects.length === 0 && (
            <div className="text-center py-12">
              <div className="text-5xl mb-4 opacity-50">📁</div>
              <p className="text-text-muted">This folder is empty</p>
              <p className="text-text-light text-sm mt-1">Create a project to get started</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Series Timeline Item - draggable project in timeline
function SeriesTimelineItem({ project, index, onDragStart, onDragOver, onDragEnd, onDrop, isDragging, onMoveToHome }) {
  const [showMenu, setShowMenu] = useState(false)
  const menuRef = useRef(null)
  
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
  
  return (
    <div
      className={clsx(
        'flex items-center gap-3 px-4 py-3 rounded-lg bg-dark-700/50 border border-gold-rich/10',
        'transition-all duration-200 cursor-grab active:cursor-grabbing',
        isDragging ? 'opacity-50 scale-95' : 'hover:bg-dark-700 hover:border-gold-rich/30'
      )}
      draggable
      onDragStart={(e) => onDragStart(e, index)}
      onDragOver={(e) => onDragOver(e, index)}
      onDragEnd={onDragEnd}
      onDrop={(e) => onDrop(e, index)}
    >
      {/* Drag Handle */}
      <span className="text-text-muted text-sm select-none">⋮⋮</span>
      
      {/* Project Name */}
      <span className="flex-1 text-text-primary font-medium truncate">
        {project.name || 'Untitled Project'}
      </span>
      
      {/* Book order indicator */}
      <span className="text-xs text-text-muted px-2 py-0.5 rounded bg-dark-800">
        Book {index + 1}
      </span>
      
      {/* Menu */}
      <div className="relative" ref={menuRef}>
        <button
          className="w-6 h-6 rounded flex items-center justify-center text-text-muted hover:text-gold-rich hover:bg-gold-rich/10 text-xs"
          onClick={(e) => {
            e.stopPropagation()
            setShowMenu(!showMenu)
          }}
        >
          ⋯
        </button>
        
        {showMenu && (
          <div 
            className="absolute right-0 top-8 bg-dark-800 rounded-xl shadow-lg shadow-black/50 border border-gold-rich/20 min-w-[140px] py-2"
            style={{ zIndex: 99999 }}
          >
            <button
              className="dropdown-item flex items-center gap-2 w-full text-sm"
              onClick={(e) => {
                e.stopPropagation()
                onMoveToHome(project)
                setShowMenu(false)
              }}
            >
              🏠 Move to Home
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// Series Timeline Component - collapsible, draggable project list
function SeriesTimelineSection({ projects, isExpanded, onToggle, onReorder, onMoveToHome }) {
  const [draggedIndex, setDraggedIndex] = useState(null)
  const [dragOverIndex, setDragOverIndex] = useState(null)
  
  const handleDragStart = (e, index) => {
    setDraggedIndex(index)
    e.dataTransfer.effectAllowed = 'move'
  }
  
  const handleDragOver = (e, index) => {
    e.preventDefault()
    if (draggedIndex !== null && draggedIndex !== index) {
      setDragOverIndex(index)
    }
  }
  
  const handleDragEnd = () => {
    setDraggedIndex(null)
    setDragOverIndex(null)
  }
  
  const handleDrop = (e, dropIndex) => {
    e.preventDefault()
    if (draggedIndex !== null && draggedIndex !== dropIndex) {
      // Create new order
      const newProjects = [...projects]
      const [draggedProject] = newProjects.splice(draggedIndex, 1)
      newProjects.splice(dropIndex, 0, draggedProject)
      onReorder(newProjects)
    }
    setDraggedIndex(null)
    setDragOverIndex(null)
  }
  
  return (
    <div className="bg-dark-800/80 rounded-xl border border-gold-rich/20 overflow-hidden">
      {/* Header */}
      <button
        className="w-full px-5 py-4 flex items-center justify-between hover:bg-dark-700/50 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">📚</span>
          <div className="text-left">
            <h3 className="font-semibold text-text-primary">Series Timeline</h3>
            <p className="text-xs text-text-muted">Drag your projects into the correct order for an accurate timeline.</p>
          </div>
        </div>
        <span className={clsx(
          'text-text-muted transition-transform duration-200',
          isExpanded ? 'rotate-180' : ''
        )}>
          ▼
        </span>
      </button>
      
      {/* Timeline List */}
      {isExpanded && (
        <div className="px-4 pb-4 space-y-2">
          {projects.length === 0 ? (
            <div className="text-center py-6 text-text-muted text-sm">
              No projects in this series yet
            </div>
          ) : (
            projects.map((project, index) => (
              <SeriesTimelineItem
                key={project.id}
                project={project}
                index={index}
                onDragStart={handleDragStart}
                onDragOver={handleDragOver}
                onDragEnd={handleDragEnd}
                onDrop={handleDrop}
                isDragging={draggedIndex === index}
                onMoveToHome={onMoveToHome}
              />
            ))
          )}
        </div>
      )}
    </div>
  )
}

// Series View - when inside a series folder (different from regular folder)
function SeriesView({ 
  series, 
  onBack, 
  onSelectProject, 
  onCreateProject, 
  onDeleteProject, 
  onRenameProject, 
  onDuplicateProject,
  onExportProject,
  onReorderProjects,
  onMoveProjectToHome
}) {
  const [timelineExpanded, setTimelineExpanded] = useState(true)
  
  const formatTime = (timestamp) => {
    if (!timestamp) return 'Just now'
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now - date
    
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`
    return date.toLocaleDateString()
  }
  
  const projects = series.projects || []
  
  return (
    <div className="h-full flex flex-col">
      {/* Series Header */}
      <div className="px-8 py-6">
        <div className="max-w-5xl mx-auto">
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-text-muted mb-2">
            <button 
              className="hover:text-gold-rich transition-colors"
              onClick={onBack}
            >
              Home
            </button>
            <span className="text-text-light">›</span>
            <span className="text-gold-rich">{series.name}</span>
          </div>
          
          {/* Series Title */}
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-serif font-medium text-gold-rich">
                {series.name}
              </h1>
              <p className="text-text-muted mt-1">
                {projects.length} project{projects.length !== 1 ? 's' : ''} • Last edited {formatTime(series.updated_at)}
              </p>
            </div>
            
            <div className="flex items-center gap-2">
              <button className="w-8 h-8 rounded-lg flex items-center justify-center text-text-muted hover:text-gold-rich hover:bg-gold-rich/10">
                {Icons.MENU}
              </button>
              <button 
                className="w-8 h-8 rounded-lg flex items-center justify-center text-text-muted hover:text-gold-rich hover:bg-gold-rich/10"
                onClick={onBack}
              >
                {Icons.CLOSE}
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Series Content */}
      <div className="flex-1 overflow-y-auto px-8 pb-8">
        <div className="max-w-5xl mx-auto space-y-6">
          {/* Series Timeline Section */}
          <SeriesTimelineSection
            projects={projects}
            isExpanded={timelineExpanded}
            onToggle={() => setTimelineExpanded(!timelineExpanded)}
            onReorder={onReorderProjects}
            onMoveToHome={onMoveProjectToHome}
          />
          
          {/* Shared Elements Info Banner */}
          <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-gold-rich/10 border border-gold-rich/30">
            <span className="text-lg">🔗</span>
            <p className="text-sm text-gold-pale">
              <span className="font-medium">Shared Story Bible:</span> Characters, Worldbuilding, and Outline are shared across all projects in this series.
            </p>
          </div>
          
          {/* Projects Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {projects.map(project => (
              <ProjectCard
                key={project.id}
                project={project}
                onSelect={onSelectProject}
                onDelete={onDeleteProject}
                onRename={onRenameProject}
                onDuplicate={onDuplicateProject}
                onExport={onExportProject}
              />
            ))}
            
            {/* Add Project Button */}
            <button
              className={clsx(
                'min-h-[180px] rounded-xl',
                'border-2 border-dashed border-gold-rich/30',
                'flex flex-col items-center justify-center',
                'text-text-muted hover:text-gold-rich hover:border-gold-rich/50',
                'transition-all duration-200'
              )}
              onClick={onCreateProject}
            >
              <span className="text-3xl mb-2">+</span>
              <span className="text-sm font-medium">New Project</span>
            </button>
          </div>
          
          {/* Empty State */}
          {projects.length === 0 && (
            <div className="text-center py-12">
              <div className="text-5xl mb-4 opacity-50">📚</div>
              <p className="text-text-muted">This series is empty</p>
              <p className="text-text-light text-sm mt-1">Create a project to start your series</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StorageModeIndicator({ mode }) {
  const isLocal = mode === 'local'
  
  return (
    <div
      className={clsx(
        'flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border',
        isLocal 
          ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
          : 'bg-green-500/10 text-green-400 border-green-500/30'
      )}
      title={isLocal 
        ? 'Running in offline mode. Data is saved locally in your browser.' 
        : 'Connected to Python backend. Data is saved to database.'}
    >
      <span className={clsx(
        'w-2 h-2 rounded-full',
        isLocal ? 'bg-amber-400' : 'bg-green-400'
      )} />
      <span>{isLocal ? 'Offline Mode' : 'Connected'}</span>
    </div>
  )
}

function Dashboard() {
  const {
    projects,
    setProjects,
    currentProjectId,
    setCurrentProject,
    clearCurrentProject,
    setCurrentView,
    addNotification,
    storageMode,
    setSeriesContext,
    clearSeriesContext,
  } = useStore()
  
  const {
    getProjectsWithChapters,
    createProject,
    deleteProject,
    renameProject,
    getChapterContent,
    storageMode: bridgeStorageMode,
    moveProjectToRecycleBin,
    moveToRecycleBin,
    getRecycleBinItems,
    restoreFromRecycleBin,
    permanentDeleteFromRecycleBin,
    emptyRecycleBin,
    getFullProjectData,
  } = usePythonBridge()
  
  const [isLoading, setIsLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [createType, setCreateType] = useState('project')
  const [showImportModal, setShowImportModal] = useState(false)
  const [showRenameModal, setShowRenameModal] = useState(false)
  const [renameTarget, setRenameTarget] = useState(null)
  const [renameType, setRenameType] = useState('project')
  
  // Folder/Series state
  const [folders, setFolders] = useState([])
  const [series, setSeries] = useState([])
  const [currentFolder, setCurrentFolder] = useState(null)
  const [currentSeries, setCurrentSeries] = useState(null)
  
  // Recycle Bin state
  const [showRecycleBin, setShowRecycleBin] = useState(false)
  const [recycleBinItems, setRecycleBinItems] = useState([])
  const [recycleBinLoading, setRecycleBinLoading] = useState(false)
  
  // Load projects on mount
  useEffect(() => {
    async function loadProjects() {
      setIsLoading(true)
      try {
        const projectList = await getProjectsWithChapters()
        const loadedProjects = projectList || []
        setProjects(loadedProjects)
        
        // Load folders and series from localStorage
        const savedFolders = localStorage.getItem('exelsias_folders')
        const savedSeries = localStorage.getItem('exelsias_series')
        
        // Sync folders: match stored project IDs with actual projects from backend
        if (savedFolders) {
          const parsedFolders = JSON.parse(savedFolders)
          const syncedFolders = parsedFolders.map(folder => ({
            ...folder,
            // Match project IDs with actual project data, filter out deleted projects
            projects: (folder.projects || [])
              .map(storedProject => {
                const actualProject = loadedProjects.find(p => p.id === storedProject.id)
                return actualProject || null
              })
              .filter(Boolean)
          }))
          setFolders(syncedFolders)
          // Save synced version back to localStorage
          localStorage.setItem('exelsias_folders', JSON.stringify(syncedFolders))
        }
        
        // Sync series: match stored project IDs with actual projects from backend
        if (savedSeries) {
          const parsedSeries = JSON.parse(savedSeries)
          const syncedSeries = parsedSeries.map(s => ({
            ...s,
            // Match project IDs with actual project data, filter out deleted projects
            projects: (s.projects || [])
              .map(storedProject => {
                const actualProject = loadedProjects.find(p => p.id === storedProject.id)
                return actualProject || null
              })
              .filter(Boolean)
          }))
          setSeries(syncedSeries)
          // Save synced version back to localStorage
          localStorage.setItem('exelsias_series', JSON.stringify(syncedSeries))
        }
      } catch (error) {
        console.error('Failed to load projects:', error)
        addNotification({ type: 'error', message: 'Failed to load projects' })
      } finally {
        setIsLoading(false)
      }
    }
    
    loadProjects()
  }, [])
  
  // Get standalone projects (not in any folder or series) - memoized to prevent flicker
  const standaloneProjects = useMemo(() => {
    const folderProjectIds = folders.flatMap(f => f.projects?.map(p => p.id) || [])
    const seriesProjectIds = series.flatMap(s => s.projects?.map(p => p.id) || [])
    const usedIds = new Set([...folderProjectIds, ...seriesProjectIds])
    
    return projects.filter(p => !usedIds.has(p.id))
  }, [projects, folders, series])
  
  // Handle select project
  const handleSelectProject = (project) => {
    // Check if this project is part of a series
    const parentSeries = series.find(s => s.projects?.some(p => p.id === project.id))
    
    if (parentSeries) {
      // Set series context so shared elements are available
      const seriesProjectIds = parentSeries.projects?.map(p => p.id) || []
      setSeriesContext(parentSeries.id, seriesProjectIds)
    } else {
      // Not part of a series, clear any existing context
      clearSeriesContext()
    }
    
    setCurrentProject(project.id)
    setCurrentView('editor')
  }
  
  // Handle create
  const handleCreate = async (name, genre, type) => {
    if (type === 'project') {
      try {
        const projectId = await createProject(name, genre)
        if (projectId) {
          const updatedProjects = await getProjectsWithChapters()
          setProjects(updatedProjects || [])
          
          // If we're in a folder, add project to folder
          if (currentFolder) {
            const newProject = updatedProjects.find(p => p.id === projectId)
            if (newProject) {
              setFolders(prev => {
                const updated = prev.map(f => 
                  f.id === currentFolder.id 
                    ? { ...f, projects: [...(f.projects || []), newProject], updated_at: new Date().toISOString() }
                    : f
                )
                localStorage.setItem('exelsias_folders', JSON.stringify(updated))
                return updated
              })
              setCurrentFolder(prev => ({
                ...prev,
                projects: [...(prev.projects || []), newProject],
                updated_at: new Date().toISOString()
              }))
            }
          } else if (currentSeries) {
            // If we're in a series, add project to series
            const newProject = updatedProjects.find(p => p.id === projectId)
            if (newProject) {
              setSeries(prev => {
                const updated = prev.map(s => 
                  s.id === currentSeries.id 
                    ? { ...s, projects: [...(s.projects || []), newProject], updated_at: new Date().toISOString() }
                    : s
                )
                localStorage.setItem('exelsias_series', JSON.stringify(updated))
                return updated
              })
              setCurrentSeries(prev => ({
                ...prev,
                projects: [...(prev.projects || []), newProject],
                updated_at: new Date().toISOString()
              }))
            }
          } else {
            // Enter the new project
            setCurrentProject(projectId)
            setCurrentView('editor')
          }
          
          addNotification({ type: 'success', message: `Project "${name}" created!` })
        }
      } catch (error) {
        console.error('Failed to create project:', error)
        addNotification({ type: 'error', message: 'Failed to create project' })
      }
    } else if (type === 'folder') {
      const newFolder = {
        id: Date.now().toString(),
        name,
        projects: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      setFolders(prev => {
        const updated = [...prev, newFolder]
        localStorage.setItem('exelsias_folders', JSON.stringify(updated))
        return updated
      })
      addNotification({ type: 'success', message: `Folder "${name}" created!` })
    } else if (type === 'series') {
      const newSeries = {
        id: Date.now().toString(),
        name,
        projects: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      setSeries(prev => {
        const updated = [...prev, newSeries]
        localStorage.setItem('exelsias_series', JSON.stringify(updated))
        return updated
      })
      addNotification({ type: 'success', message: `Series "${name}" created!` })
    }
  }
  
  // Handle delete project
  const handleDeleteProject = async (project) => {
    if (!confirm(`Are you sure you want to move "${project.name}" to the recycle bin?`)) {
      return
    }
    
    try {
      // Move to recycle bin instead of hard delete
      await moveProjectToRecycleBin(project.id)
      
      // If we're deleting the currently open project, clear it first
      if (currentProjectId === project.id) {
        clearCurrentProject()
      }
      
      // Reload projects from backend to ensure consistent state (avoids stale closure issues)
      const freshProjects = await getProjectsWithChapters()
      setProjects(freshProjects || [])
      
      // Update folders - filter out the deleted project
      const updatedFolders = folders.map(f => ({
        ...f,
        projects: f.projects?.filter(p => p.id !== project.id) || []
      }))
      setFolders(updatedFolders)
      localStorage.setItem('exelsias_folders', JSON.stringify(updatedFolders))
      
      // Update series - filter out the deleted project
      const updatedSeries = series.map(s => ({
        ...s,
        projects: s.projects?.filter(p => p.id !== project.id) || []
      }))
      setSeries(updatedSeries)
      localStorage.setItem('exelsias_series', JSON.stringify(updatedSeries))
      
      // Update current folder/series view
      if (currentFolder) {
        setCurrentFolder({
          ...currentFolder,
          projects: currentFolder.projects?.filter(p => p.id !== project.id) || []
        })
      }
      if (currentSeries) {
        setCurrentSeries({
          ...currentSeries,
          projects: currentSeries.projects?.filter(p => p.id !== project.id) || []
        })
      }
      
      addNotification({ type: 'success', message: `Project "${project.name}" moved to recycle bin` })
    } catch (error) {
      console.error('Failed to delete project:', error)
      addNotification({ type: 'error', message: 'Failed to delete project' })
    }
  }
  
  // Handle rename project
  const handleRenameProject = (project) => {
    setRenameTarget(project)
    setRenameType('project')
    setShowRenameModal(true)
  }
  
  // Execute project rename (called from RenameModal)
  const executeRenameProject = async (newName) => {
    if (!renameTarget) return
    try {
      await renameProject(renameTarget.id, newName)
      const updatedProjects = await getProjectsWithChapters()
      setProjects(updatedProjects || [])
      addNotification({ type: 'success', message: 'Project renamed' })
    } catch (error) {
      console.error('Failed to rename project:', error)
      addNotification({ type: 'error', message: 'Failed to rename project' })
    }
  }
  
  // Handle duplicate project
  const handleDuplicateProject = async (project, container) => {
    try {
      const duplicateName = `${project.name} (Copy)`
      const projectId = await createProject(duplicateName, project.genre || '')
      
      if (projectId) {
        const updatedProjects = await getProjectsWithChapters()
        setProjects(updatedProjects || [])
        
        // If duplicating from a folder, add to same folder
        if (container && container.id) {
          const newProject = updatedProjects.find(p => p.id === projectId)
          if (newProject) {
            // Check if it's a folder or series
            const isFolder = folders.some(f => f.id === container.id)
            if (isFolder) {
              setFolders(prev => {
                const updated = prev.map(f => 
                  f.id === container.id 
                    ? { ...f, projects: [...(f.projects || []), newProject], updated_at: new Date().toISOString() }
                    : f
                )
                localStorage.setItem('exelsias_folders', JSON.stringify(updated))
                return updated
              })
            } else {
              setSeries(prev => {
                const updated = prev.map(s => 
                  s.id === container.id 
                    ? { ...s, projects: [...(s.projects || []), newProject], updated_at: new Date().toISOString() }
                    : s
                )
                localStorage.setItem('exelsias_series', JSON.stringify(updated))
                return updated
              })
            }
          }
        }
        
        addNotification({ type: 'success', message: `Project duplicated as "${duplicateName}"` })
      }
    } catch (error) {
      console.error('Failed to duplicate project:', error)
      addNotification({ type: 'error', message: 'Failed to duplicate project' })
    }
  }
  
  // Handle export project (entire project as .zip)
  const handleExportProject = async (project, format = 'zip') => {
    try {
      addNotification({ type: 'info', message: 'Preparing export...' })
      
      // Get chapters for the project
      const chapters = project.chapters || []
      
      if (chapters.length === 0) {
        addNotification({ type: 'warning', message: 'No chapters to export' })
        return
      }
      
      // Fetch full chapter content for each chapter
      const chaptersWithContent = await Promise.all(
        chapters.map(async (ch) => {
          const content = await getChapterContent(ch.id)
          return { ...ch, content: content || '' }
        })
      )
      
      if (format === 'zip') {
        // Create ZIP file with all chapters as .docx files
        const zip = new JSZip()
        
        for (const chapter of chaptersWithContent) {
          // Convert HTML to DOCX paragraphs with formatting preserved
          const contentParagraphs = htmlToDocxParagraphs(chapter.content)
          
          // Create DOCX document for each chapter
          const doc = new Document({
            sections: [{
              children: [
                new Paragraph({
                  text: chapter.title || `Chapter ${chapter.order || ''}`,
                  heading: HeadingLevel.HEADING_1,
                }),
                new Paragraph({ text: '' }), // Empty line after title
                ...contentParagraphs,
              ],
            }],
          })
          
          const docxBuffer = await Packer.toBlob(doc)
          const safeTitle = (chapter.title || `chapter_${chapter.order || chapter.id}`)
            .replace(/[^a-z0-9]/gi, '_')
            .substring(0, 50)
          zip.file(`${safeTitle}.docx`, docxBuffer)
        }
        
        // Also add a combined full manuscript file
        const fullDoc = new Document({
          sections: [{
            children: chaptersWithContent.flatMap((chapter, idx) => {
              const contentParagraphs = htmlToDocxParagraphs(chapter.content)
              return [
                new Paragraph({
                  text: chapter.title || `Chapter ${chapter.order || idx + 1}`,
                  heading: HeadingLevel.HEADING_1,
                  pageBreakBefore: idx > 0,
                }),
                new Paragraph({ text: '' }),
                ...contentParagraphs,
              ]
            }),
          }],
        })
        
        const fullDocxBuffer = await Packer.toBlob(fullDoc)
        zip.file('_Full_Manuscript.docx', fullDocxBuffer)
        
        // Generate and download the zip
        const zipBlob = await zip.generateAsync({ type: 'blob' })
        const safeProjectName = project.name.replace(/[^a-z0-9]/gi, '_').substring(0, 50)
        saveAs(zipBlob, `${safeProjectName}_export.zip`)
        
        addNotification({ 
          type: 'success', 
          message: `Exported ${chaptersWithContent.length} chapters to ${safeProjectName}_export.zip` 
        })
      }
    } catch (error) {
      console.error('Export failed:', error)
      addNotification({ type: 'error', message: 'Failed to export project' })
    }
  }
  
  // Handle export single chapter as .docx
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
  
  // Handle delete folder (moves folder + all projects inside to recycle bin)
  const handleDeleteFolder = async (folder) => {
    const projectCount = folder.projects?.length || 0
    const message = projectCount > 0 
      ? `Move folder "${folder.name}" and its ${projectCount} project(s) to recycle bin?`
      : `Move folder "${folder.name}" to recycle bin?`
    
    if (!confirm(message)) {
      return
    }
    
    try {
      // Get full data for all projects in the folder
      const projectsWithData = []
      for (const proj of (folder.projects || [])) {
        const fullData = await getFullProjectData(proj.id)
        if (fullData) {
          projectsWithData.push(fullData)
        }
      }
      
      // Create folder data with full project data for recycle bin
      const folderData = {
        id: folder.id,
        name: folder.name,
        created_at: folder.created_at,
        updated_at: folder.updated_at,
        projects: projectsWithData
      }
      
      // Move to recycle bin
      await moveToRecycleBin('folder', folder.id, folderData)
      
      // Hard delete all projects in the folder (they're backed up in recycle bin)
      for (const proj of (folder.projects || [])) {
        await deleteProject(proj.id)
        
        // Clear current project if it's being deleted
        if (currentProjectId === proj.id) {
          clearCurrentProject()
        }
      }
      
      // Remove folder from state
      const updated = folders.filter(f => f.id !== folder.id)
      setFolders(updated)
      localStorage.setItem('exelsias_folders', JSON.stringify(updated))
      
      // Reload projects
      const freshProjects = await getProjectsWithChapters()
      setProjects(freshProjects || [])
      
      // Clear current folder view if we just deleted it
      if (currentFolder?.id === folder.id) {
        setCurrentFolder(null)
      }
      
      addNotification({ type: 'success', message: `Folder "${folder.name}" moved to recycle bin` })
    } catch (error) {
      console.error('Failed to delete folder:', error)
      addNotification({ type: 'error', message: 'Failed to delete folder' })
    }
  }
  
  // Handle rename folder
  const handleRenameFolder = (folder) => {
    setRenameTarget(folder)
    setRenameType('folder')
    setShowRenameModal(true)
  }
  
  // Execute folder rename (called from RenameModal)
  const executeRenameFolder = (newName) => {
    if (!renameTarget) return
    setFolders(prev => {
      const updated = prev.map(f => 
        f.id === renameTarget.id ? { ...f, name: newName, updated_at: Date.now() } : f
      )
      localStorage.setItem('exelsias_folders', JSON.stringify(updated))
      return updated
    })
    addNotification({ type: 'success', message: 'Folder renamed' })
  }
  
  // Handle delete series (moves series + all projects inside to recycle bin)
  const handleDeleteSeries = async (s) => {
    const projectCount = s.projects?.length || 0
    const message = projectCount > 0 
      ? `Move series "${s.name}" and its ${projectCount} project(s) to recycle bin?`
      : `Move series "${s.name}" to recycle bin?`
    
    if (!confirm(message)) {
      return
    }
    
    try {
      // Get full data for all projects in the series
      const projectsWithData = []
      for (const proj of (s.projects || [])) {
        const fullData = await getFullProjectData(proj.id)
        if (fullData) {
          projectsWithData.push(fullData)
        }
      }
      
      // Create series data with full project data for recycle bin
      const seriesData = {
        id: s.id,
        name: s.name,
        created_at: s.created_at,
        updated_at: s.updated_at,
        projects: projectsWithData
      }
      
      // Move to recycle bin
      await moveToRecycleBin('series', s.id, seriesData)
      
      // Hard delete all projects in the series (they're backed up in recycle bin)
      for (const proj of (s.projects || [])) {
        await deleteProject(proj.id)
        
        // Clear current project if it's being deleted
        if (currentProjectId === proj.id) {
          clearCurrentProject()
        }
      }
      
      // Remove series from state
      const updated = series.filter(ser => ser.id !== s.id)
      setSeries(updated)
      localStorage.setItem('exelsias_series', JSON.stringify(updated))
      
      // Reload projects
      const freshProjects = await getProjectsWithChapters()
      setProjects(freshProjects || [])
      
      // Clear current series view if we just deleted it
      if (currentSeries?.id === s.id) {
        setCurrentSeries(null)
      }
      
      addNotification({ type: 'success', message: `Series "${s.name}" moved to recycle bin` })
    } catch (error) {
      console.error('Failed to delete series:', error)
      addNotification({ type: 'error', message: 'Failed to delete series' })
    }
  }
  
  // ==================== RECYCLE BIN HANDLERS ====================
  
  // Open recycle bin and load items
  const handleOpenRecycleBin = async () => {
    setShowRecycleBin(true)
    setRecycleBinLoading(true)
    try {
      const items = await getRecycleBinItems()
      setRecycleBinItems(items || [])
    } catch (error) {
      console.error('Failed to load recycle bin:', error)
      addNotification({ type: 'error', message: 'Failed to load recycle bin' })
    } finally {
      setRecycleBinLoading(false)
    }
  }
  
  // Restore an item from recycle bin
  const handleRestoreFromRecycleBin = async (item) => {
    try {
      const result = await restoreFromRecycleBin(item.id)
      if (!result) {
        addNotification({ type: 'error', message: 'Failed to restore item' })
        return
      }
      
      // If it's a folder, add it back to folders
      if (item.item_type === 'folder' && result.folder_data) {
        setFolders(prev => {
          const updated = [...prev, result.folder_data]
          localStorage.setItem('exelsias_folders', JSON.stringify(updated))
          return updated
        })
      }
      
      // If it's a series, add it back to series
      if (item.item_type === 'series' && result.series_data) {
        setSeries(prev => {
          const updated = [...prev, result.series_data]
          localStorage.setItem('exelsias_series', JSON.stringify(updated))
          return updated
        })
      }
      
      // Reload projects to get any restored projects
      const freshProjects = await getProjectsWithChapters()
      setProjects(freshProjects || [])
      
      // Remove from recycle bin list
      setRecycleBinItems(prev => prev.filter(i => i.id !== item.id))
      
      const itemName = item.item_data?.name || 'Item'
      addNotification({ type: 'success', message: `"${itemName}" restored successfully` })
    } catch (error) {
      console.error('Failed to restore from recycle bin:', error)
      addNotification({ type: 'error', message: 'Failed to restore item' })
    }
  }
  
  // Permanently delete an item from recycle bin
  const handlePermanentDelete = async (item) => {
    try {
      await permanentDeleteFromRecycleBin(item.id)
      
      // Remove from recycle bin list
      setRecycleBinItems(prev => prev.filter(i => i.id !== item.id))
      
      const itemName = item.item_data?.name || 'Item'
      addNotification({ type: 'success', message: `"${itemName}" permanently deleted` })
    } catch (error) {
      console.error('Failed to permanently delete:', error)
      addNotification({ type: 'error', message: 'Failed to permanently delete' })
    }
  }
  
  // Empty the entire recycle bin
  const handleEmptyRecycleBin = async () => {
    try {
      await emptyRecycleBin()
      setRecycleBinItems([])
      addNotification({ type: 'success', message: 'Recycle bin emptied' })
    } catch (error) {
      console.error('Failed to empty recycle bin:', error)
      addNotification({ type: 'error', message: 'Failed to empty recycle bin' })
    }
  }
  
  // Handle rename series
  const handleRenameSeries = (s) => {
    setRenameTarget(s)
    setRenameType('series')
    setShowRenameModal(true)
  }
  
  // Execute series rename (called from RenameModal)
  const executeRenameSeries = (newName) => {
    if (!renameTarget) return
    setSeries(prev => {
      const updated = prev.map(ser => 
        ser.id === renameTarget.id ? { ...ser, name: newName, updated_at: Date.now() } : ser
      )
      localStorage.setItem('exelsias_series', JSON.stringify(updated))
      return updated
    })
    addNotification({ type: 'success', message: 'Series renamed' })
  }
  
  // Handle reorder projects in series (drag and drop timeline)
  const handleReorderSeriesProjects = (newProjectsOrder) => {
    if (!currentSeries) return
    
    setSeries(prev => {
      const updated = prev.map(s => 
        s.id === currentSeries.id 
          ? { ...s, projects: newProjectsOrder, updated_at: new Date().toISOString() }
          : s
      )
      localStorage.setItem('exelsias_series', JSON.stringify(updated))
      return updated
    })
    
    // Update current series view
    setCurrentSeries(prev => ({
      ...prev,
      projects: newProjectsOrder,
      updated_at: new Date().toISOString()
    }))
    
    addNotification({ type: 'success', message: 'Series timeline updated' })
  }
  
  // Handle move project from series to home (standalone)
  const handleMoveProjectToHome = (project) => {
    if (!currentSeries) return
    
    if (!confirm(`Remove "${project.name}" from this series? It will become a standalone project and lose access to shared Story Bible data.`)) {
      return
    }
    
    // Remove from series
    setSeries(prev => {
      const updated = prev.map(s => 
        s.id === currentSeries.id 
          ? { ...s, projects: s.projects?.filter(p => p.id !== project.id) || [], updated_at: new Date().toISOString() }
          : s
      )
      localStorage.setItem('exelsias_series', JSON.stringify(updated))
      return updated
    })
    
    // Update current series view
    setCurrentSeries(prev => ({
      ...prev,
      projects: prev.projects?.filter(p => p.id !== project.id) || [],
      updated_at: new Date().toISOString()
    }))
    
    addNotification({ type: 'success', message: `"${project.name}" moved to Home` })
  }
  
  // Open folder
  const handleOpenFolder = (folder) => {
    // Sync folder projects with current project data
    const syncedProjects = folder.projects?.map(fp => 
      projects.find(p => p.id === fp.id) || fp
    ).filter(Boolean) || []
    
    setCurrentFolder({ ...folder, projects: syncedProjects })
  }
  
  // Open series
  const handleOpenSeries = (s) => {
    // Sync series projects with current project data
    const syncedProjects = s.projects?.map(sp => 
      projects.find(p => p.id === sp.id) || sp
    ).filter(Boolean) || []
    
    setCurrentSeries({ ...s, projects: syncedProjects })
  }
  
  // If viewing a folder
  if (currentFolder) {
    return (
      <div className="h-full flex flex-col">
        {/* Header */}
        <header className="px-8 py-4 glass relative" style={{ zIndex: 100000 }}>
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <NewButtonDropdown
              onCreateProject={() => {
                setCreateType('project')
                setShowCreateModal(true)
              }}
              onCreateFolder={() => {
                setCreateType('folder')
                setShowCreateModal(true)
              }}
              onCreateSeries={() => {
                setCreateType('series')
                setShowCreateModal(true)
              }}
            />
            
            <div className="flex items-center gap-2">
              <span className="text-2xl font-serif tracking-tight gold-gradient-text">
                exelsias
              </span>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                className="p-2 rounded-lg text-text-muted hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
                onClick={handleOpenRecycleBin}
                title="Recycle Bin"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
              <StorageModeIndicator mode={bridgeStorageMode || storageMode} />
              <WindowControls />
            </div>
          </div>
        </header>
        
        <FolderView
          folder={currentFolder}
          onBack={() => setCurrentFolder(null)}
          onSelectProject={handleSelectProject}
          onCreateProject={() => {
            setCreateType('project')
            setShowCreateModal(true)
          }}
          onDeleteProject={handleDeleteProject}
          onRenameProject={handleRenameProject}
          onDuplicateProject={(p) => handleDuplicateProject(p, currentFolder)}
          onExportProject={handleExportProject}
        />
        
        <CreateModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreate}
          type={createType}
        />
      </div>
    )
  }
  
  // If viewing a series
  if (currentSeries) {
    return (
      <div className="h-full flex flex-col">
        {/* Header */}
        <header className="px-8 py-4 glass relative" style={{ zIndex: 100000 }}>
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <NewButtonDropdown
              onCreateProject={() => {
                setCreateType('project')
                setShowCreateModal(true)
              }}
              onCreateFolder={() => {
                setCreateType('folder')
                setShowCreateModal(true)
              }}
              onCreateSeries={() => {
                setCreateType('series')
                setShowCreateModal(true)
              }}
            />
            
            <div className="flex items-center gap-2">
              <span className="text-2xl font-serif tracking-tight gold-gradient-text">
                exelsias
              </span>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                className="p-2 rounded-lg text-text-muted hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
                onClick={handleOpenRecycleBin}
                title="Recycle Bin"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
              <StorageModeIndicator mode={bridgeStorageMode || storageMode} />
              <WindowControls />
            </div>
          </div>
        </header>
        
        <SeriesView
          series={currentSeries}
          onBack={() => setCurrentSeries(null)}
          onSelectProject={handleSelectProject}
          onCreateProject={() => {
            setCreateType('project')
            setShowCreateModal(true)
          }}
          onDeleteProject={handleDeleteProject}
          onRenameProject={handleRenameProject}
          onDuplicateProject={(p) => handleDuplicateProject(p, currentSeries)}
          onExportProject={handleExportProject}
          onReorderProjects={handleReorderSeriesProjects}
          onMoveProjectToHome={handleMoveProjectToHome}
        />
        
        <CreateModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreate}
          type={createType}
        />
      </div>
    )
  }
  
  // Main Dashboard View
  return (
    <div className="h-full flex flex-col">
      {/* Header - Elegant dark gold */}
      <header className="px-8 py-4 glass relative" style={{ zIndex: 100000 }}>
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          {/* Left side - New & Import */}
          <div className="flex items-center gap-4">
            <NewButtonDropdown
              onCreateProject={() => {
                setCreateType('project')
                setShowCreateModal(true)
              }}
              onCreateFolder={() => {
                setCreateType('folder')
                setShowCreateModal(true)
              }}
              onCreateSeries={() => {
                setCreateType('series')
                setShowCreateModal(true)
              }}
            />
            
            <button
              className={clsx(
                'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-200',
                'bg-transparent text-text-secondary hover:text-gold-rich hover:bg-gold-rich/10 border border-transparent hover:border-gold-rich/30'
              )}
              onClick={() => setShowImportModal(true)}
            >
              {HeaderIcons.IMPORT}
              <span>Import</span>
            </button>
          </div>
          
          {/* Center - Logo */}
          <div className="flex items-center gap-2">
            <span className="text-2xl font-serif tracking-tight gold-gradient-text">
              exelsias
            </span>
          </div>
          
          {/* Right side - Status, Recycle Bin & Window Controls */}
          <div className="flex items-center gap-4">
            <button
              className="p-2 rounded-lg text-text-muted hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
              onClick={handleOpenRecycleBin}
              title="Recycle Bin"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
            <StorageModeIndicator mode={bridgeStorageMode || storageMode} />
            <WindowControls />
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-5xl mx-auto">
          {/* Loading State */}
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="spinner mx-auto mb-4" />
                <p className="text-gray-400">Loading projects...</p>
              </div>
            </div>
          ) : (
            /* Project Grid */
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {/* Standalone Projects */}
              {standaloneProjects.map(project => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  onSelect={handleSelectProject}
                  onDelete={handleDeleteProject}
                  onRename={handleRenameProject}
                  onDuplicate={(p) => handleDuplicateProject(p, null)}
                  onExport={handleExportProject}
                />
              ))}
              
              {/* Folders */}
              {folders.map(folder => (
                <FolderCard
                  key={folder.id}
                  folder={folder}
                  onClick={handleOpenFolder}
                  onDelete={handleDeleteFolder}
                  onRename={handleRenameFolder}
                  onDuplicateProject={handleDuplicateProject}
                  onDeleteProject={handleDeleteProject}
                  onExportProject={handleExportProject}
                />
              ))}
              
              {/* Series */}
              {series.map(s => (
                <SeriesCard
                  key={s.id}
                  series={s}
                  onClick={handleOpenSeries}
                  onDelete={handleDeleteSeries}
                  onRename={handleRenameSeries}
                  onDuplicateProject={handleDuplicateProject}
                  onDeleteProject={handleDeleteProject}
                  onExportProject={handleExportProject}
                />
              ))}
              
              {/* Feature Card */}
              {(standaloneProjects.length > 0 || folders.length > 0 || series.length > 0) && (
                <FeatureCard />
              )}
            </div>
          )}
          
          {/* Empty State */}
          {!isLoading && standaloneProjects.length === 0 && folders.length === 0 && series.length === 0 && (
            <div className="text-center py-16">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-dark-700 shadow-gold border border-gold-rich/30 mb-6">
                <span className="text-4xl">📚</span>
              </div>
              <h3 className="text-xl font-serif font-semibold text-gold-rich mb-2">
                No projects yet
              </h3>
              <p className="text-text-muted mb-6 max-w-md mx-auto">
                Create your first project to start writing your story with AI assistance.
              </p>
              <div className="flex items-center justify-center gap-4">
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    setCreateType('project')
                    setShowCreateModal(true)
                  }}
                >
                  + Create Project
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowImportModal(true)}
                >
                  ↓ Import Novel
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
      
      {/* Create Modal */}
      <CreateModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreate}
        type={createType}
      />
      
      {/* Rename Modal */}
      <RenameModal
        isOpen={showRenameModal}
        onClose={() => {
          setShowRenameModal(false)
          setRenameTarget(null)
        }}
        onRename={(newName) => {
          if (renameType === 'project') executeRenameProject(newName)
          else if (renameType === 'folder') executeRenameFolder(newName)
          else if (renameType === 'series') executeRenameSeries(newName)
        }}
        currentName={renameTarget?.name || ''}
        type={renameType}
      />
      
      {/* Import Novel Modal */}
      <ImportNovel
        isOpen={showImportModal}
        onClose={(skipRefresh = false) => {
          setShowImportModal(false)
          // Only refresh projects if not navigating to a project (skipRefresh = false means refresh)
          if (!skipRefresh) {
            getProjectsWithChapters().then(projectList => {
              setProjects(projectList || [])
            })
          }
        }}
        onImportComplete={async (result) => {
          // Immediately refresh the projects list when import completes
          const updatedProjects = await getProjectsWithChapters()
          if (updatedProjects) {
            setProjects(updatedProjects)
          }
        }}
      />
      
      {/* Recycle Bin Modal */}
      <RecycleBinModal
        isOpen={showRecycleBin}
        onClose={() => setShowRecycleBin(false)}
        items={recycleBinItems}
        loading={recycleBinLoading}
        onRestore={handleRestoreFromRecycleBin}
        onPermanentDelete={handlePermanentDelete}
        onEmptyBin={handleEmptyRecycleBin}
      />
    </div>
  )
}

export default Dashboard
