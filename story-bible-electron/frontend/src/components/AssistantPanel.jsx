/**
 * Assistant Panel Component
 * =========================
 * Right sidebar with AI chat and streaming responses.
 * Supports markdown rendering and content insertion to editor.
 * Dark & Gold luxury theme styling.
 */

import { useState, useRef, useEffect } from 'react'
import useStore from '../hooks/useStore'
import { usePythonBridge } from '../hooks/usePythonBridge'
import { clsx } from 'clsx'
import { LuDownload } from 'react-icons/lu'

// Icons
const Icons = {
  SEND: '➤',
  BRAIN: '🧠',
  USER: '👤',
  AI: '🤖',
  COPY: '📋',
  REFRESH: '🔄',
  SPEAKER: '🔊',
  STOP: '⏹️',
  INSERT: '📝',
  REPLACE: '🔄',
  OPENINGS: '✨',
  DRAFT: '⚡',
  WRITE: '✍️',
  REWRITE: '🔄',
  DESCRIBE: '✨',
}

// Sense icons for describe results
const SenseIcons = {
  SIGHT: '👁️',
  SOUND: '🔊',
  SMELL: '👃',
  TASTE: '👅',
  TOUCH: '🖐️',
  METAPHOR: '≋',
}

// Simple markdown renderer
function MarkdownContent({ content }) {
  // Parse markdown into HTML
  const parseMarkdown = (text) => {
    if (!text) return ''
    
    let html = text
    
    // Escape HTML
    html = html.replace(/</g, '&lt;').replace(/>/g, '&gt;')
    
    // Headers
    html = html.replace(/^### (.*$)/gm, '<h3 class="text-lg font-bold text-gold-soft mt-4 mb-2">$1</h3>')
    html = html.replace(/^## (.*$)/gm, '<h2 class="text-xl font-bold text-gold-soft mt-4 mb-2">$1</h2>')
    html = html.replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold text-gold-soft mt-4 mb-3">$1</h1>')
    
    // Bold
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-bold text-gray-100">$1</strong>')
    html = html.replace(/__([^_]+)__/g, '<strong class="font-bold text-gray-100">$1</strong>')
    
    // Italic
    html = html.replace(/\*([^*]+)\*/g, '<em class="italic">$1</em>')
    html = html.replace(/_([^_]+)_/g, '<em class="italic">$1</em>')
    
    // Code blocks
    html = html.replace(/```([^`]+)```/gs, '<pre class="bg-dark-700 p-3 rounded-lg my-2 overflow-x-auto font-mono text-sm text-gray-300">$1</pre>')
    
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code class="bg-dark-700 px-1 rounded font-mono text-sm text-gray-300">$1</code>')
    
    // Blockquotes
    html = html.replace(/^> (.*$)/gm, '<blockquote class="border-l-4 border-gold-rich pl-4 my-2 italic text-gray-400">$1</blockquote>')
    
    // Horizontal rule
    html = html.replace(/^---$/gm, '<hr class="border-gold-rich/20 my-4" />')
    
    // Unordered lists
    html = html.replace(/^\* (.*$)/gm, '<li class="ml-4 list-disc">$1</li>')
    html = html.replace(/^- (.*$)/gm, '<li class="ml-4 list-disc">$1</li>')
    
    // Numbered lists
    html = html.replace(/^\d+\. (.*$)/gm, '<li class="ml-4 list-decimal">$1</li>')
    
    // Wrap consecutive <li> tags in <ul> or <ol>
    html = html.replace(/(<li class="ml-4 list-disc">.*<\/li>\n?)+/g, '<ul class="my-2">$&</ul>')
    html = html.replace(/(<li class="ml-4 list-decimal">.*<\/li>\n?)+/g, '<ol class="my-2">$&</ol>')
    
    // Line breaks (preserve paragraphs)
    html = html.replace(/\n\n/g, '</p><p class="mb-3">')
    html = html.replace(/\n/g, '<br />')
    
    // Wrap in paragraph
    html = '<p class="mb-3">' + html + '</p>'
    
    return html
  }
  
  return (
    <div 
      className="prose max-w-none text-sm text-gray-300"
      dangerouslySetInnerHTML={{ __html: parseMarkdown(content) }}
    />
  )
}

function ChatMessage({ role, content, onCopy, onSpeak, onDownload, onInsert, onReplace, messageType, canReplace, selectionStart, selectionEnd, senses, isStreaming }) {
  const isAi = role === 'assistant'
  
  // Get the icon based on message type
  const getTypeIcon = () => {
    if (messageType === 'openings') return Icons.OPENINGS
    if (messageType === 'draft') return Icons.DRAFT
    if (messageType === 'write') return Icons.WRITE
    if (messageType === 'rewrite') return Icons.REWRITE
    if (messageType === 'describe') return Icons.DESCRIBE
    return Icons.AI
  }
  
  // Wrapper to pass messageType to onInsert
  const handleInsertClick = () => {
    onInsert(content, messageType)
  }
  
  // Wrapper to pass messageType to onReplace
  const handleReplaceClick = () => {
    onReplace(content, selectionStart, selectionEnd, messageType)
  }
  
  // Parse describe content into separate sense sections
  const parseDescribeSections = (text) => {
    if (messageType !== 'describe' || !text) return null
    
    const sections = []
    const senseRegex = /##\s*(SIGHT|SOUND|SMELL|TASTE|TOUCH|METAPHOR)\s*\n([\s\S]*?)(?=##\s*(?:SIGHT|SOUND|SMELL|TASTE|TOUCH|METAPHOR)|$)/gi
    
    let match
    while ((match = senseRegex.exec(text)) !== null) {
      sections.push({
        sense: match[1].toUpperCase(),
        content: match[2].trim()
      })
    }
    
    // If no sections found, return null to use default rendering
    if (sections.length === 0) return null
    return sections
  }
  
  const describeSections = parseDescribeSections(content)
  
  // For user messages or non-describe AI messages, use standard rendering
  if (!isAi || messageType !== 'describe' || !describeSections) {
    return (
      <div className={clsx(
        'flex gap-3 animate-fade-in',
        isAi ? 'flex-row' : 'flex-row-reverse'
      )}>
        {/* Avatar */}
        <div className={clsx(
          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
          isAi ? 'bg-gold-rich/20' : 'bg-dark-600'
        )}>
          {isAi ? getTypeIcon() : Icons.USER}
        </div>
        
        {/* Message */}
        <div className={clsx(
          'flex-1 p-3 rounded-lg',
          isAi ? 'bg-dark-700 border border-gold-rich/10' : 'bg-gold-rich/10 border border-gold-rich/20'
        )}>
          {/* Render markdown for AI messages, plain text for user */}
          {isAi ? (
            <>
              <MarkdownContent content={content} />
              {isStreaming && (
                <span className="inline-block w-2 h-4 bg-gold-rich/60 animate-pulse ml-0.5 align-text-bottom" />
              )}
            </>
          ) : (
            <p className="text-gray-200 text-sm whitespace-pre-wrap">
              {content}
            </p>
          )}
          
          {/* Actions - hidden while streaming */}
          {isAi && content && !isStreaming && (
            <div className="flex items-center gap-2 mt-3 pt-2 border-t border-gold-rich/10 flex-wrap">
              {/* Replace Selection Button - for rewrite messages */}
              {messageType === 'rewrite' && canReplace && (
                <button
                  className="px-3 py-1.5 text-xs font-medium rounded-lg bg-green-500 text-white hover:bg-green-600 flex items-center gap-1 transition-colors"
                  onClick={handleReplaceClick}
                  title="Replace selected text with this rewrite"
                >
                  {Icons.REPLACE} Replace Selection
                </button>
              )}
              
              {/* Insert Button */}
              <button
                className={clsx(
                  "px-3 py-1.5 text-xs font-medium rounded-lg flex items-center gap-1 transition-colors",
                  messageType === 'rewrite' && canReplace
                    ? "bg-dark-600 text-gray-300 hover:bg-dark-500"
                    : "bg-gold-rich text-dark-950 hover:bg-gold-amber"
                )}
                onClick={handleInsertClick}
                title="Insert at cursor position in editor"
              >
                {Icons.INSERT} Insert to Editor
              </button>
              
              <button
                className="text-xs text-gray-500 hover:text-gold-rich flex items-center gap-1"
                onClick={() => onCopy(content)}
              >
                {Icons.COPY} Copy
              </button>
              <button
                className="text-xs text-gray-500 hover:text-gold-rich flex items-center gap-1"
                onClick={() => onSpeak(content)}
              >
                {Icons.SPEAKER} Read
              </button>
              <button
                className="text-gray-500 hover:text-gold-rich flex items-center"
                onClick={() => onDownload(content)}
                title="Download as MP3"
              >
                <LuDownload className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>
    )
  }
  
  // Special rendering for describe messages - show each sense as a separate card
  return (
    <div className="space-y-3 animate-fade-in">
      {describeSections.map((section, idx) => (
        <div key={idx} className="bg-dark-700 border border-gold-rich/10 rounded-lg overflow-hidden">
          {/* Sense Header */}
          <div className="flex items-center gap-2 px-4 py-2 bg-dark-750 border-b border-gold-rich/10">
            <span className="text-lg">{SenseIcons[section.sense] || '✨'}</span>
            <span className="text-sm font-semibold text-gold-pale tracking-wide">
              {section.sense}
            </span>
            <button
              className="ml-auto text-gray-500 hover:text-gold-rich"
              title="More options"
            >
              •••
            </button>
          </div>
          
          {/* Sense Content */}
          <div className="p-4">
            <MarkdownContent content={section.content} />
          </div>
          
          {/* Actions */}
          <div className="flex items-center gap-3 px-4 py-2 border-t border-gold-rich/10">
            <button
              className="text-sm text-gray-400 hover:text-gold-rich flex items-center gap-1 transition-colors"
              onClick={() => onInsert(section.content, 'describe')}
              title="Insert this description"
            >
              ⊕ Insert
            </button>
            <button
              className="text-sm text-gray-400 hover:text-gold-rich flex items-center gap-1 transition-colors"
              onClick={() => onCopy(section.content)}
              title="Copy this description"
            >
              {Icons.COPY} Copy
            </button>
            <div className="flex items-center gap-2 ml-auto text-gray-500">
              <button className="hover:text-green-400" title="Helpful">👍</button>
              <button className="hover:text-red-400" title="Not helpful">👎</button>
              <button className="hover:text-yellow-400" title="Favorite">☆</button>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function AssistantPanel() {
  const {
    aiStatus,
    isAiGenerating,
    aiStreamedText,
    currentProjectId,
    currentChapterId,
    isTtsPlaying,
    selectedVoice,
    clearAiStream,
    addNotification,
    pendingAiRequest,
    clearPendingAiRequest,
    editorInsertCallback,
    editorReplaceSelectionCallback,
  } = useStore()
  
  const {
    startLoreStream,
    askLoreAssistant,
    getSummarizedMemory,
    getDeepMemory,
    getStoryBible,
    getCharacters,
    getContextWindow,
    getScenes,
    getSeriesContextForProject,
    ttsSpeak,
    ttsStop,
    ttsDownload,
    generatePluginResponse,
  } = usePythonBridge()
  
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  
  // Scroll to bottom on new messages or when streaming text updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, aiStreamedText])
  
  // Handle pending AI requests from Editor
  useEffect(() => {
    if (pendingAiRequest && !isLoading) {
      handlePendingRequest(pendingAiRequest)
      clearPendingAiRequest()
    }
  }, [pendingAiRequest])
  
  // Finalize streaming: read final text from Zustand store and update the placeholder message
  const finalizeStream = (meta) => {
    // Read the final accumulated text directly from the store (most reliable)
    const finalText = useStore.getState().aiStreamedText || ''
    
    // Update the last (placeholder) assistant message with the final content
    setMessages(prev => {
      const updated = [...prev]
      const lastIdx = updated.length - 1
      if (lastIdx >= 0 && updated[lastIdx].role === 'assistant' && updated[lastIdx].isStreaming) {
        updated[lastIdx] = {
          ...updated[lastIdx],
          content: finalText || 'I couldn\'t generate a response. Please check if the AI model is loaded properly.',
          isStreaming: false,
        }
      }
      return updated
    })
    
    // Auto-insert for 'write' type
    if (finalText && meta?.insertAtCursor && meta?.type === 'write' && editorInsertCallback) {
      const plainText = finalText
        .replace(/\*\*([^*]+)\*\*/g, '$1')
        .replace(/__([^_]+)__/g, '$1')
        .replace(/\*([^*]+)\*/g, '$1')
        .replace(/_([^_]+)_/g, '$1')
        .replace(/^#{1,6}\s*/gm, '')
        .replace(/^>\s*/gm, '')
        .replace(/^[\*\-]\s*/gm, '')
        .replace(/^\d+\.\s*/gm, '')
        .replace(/`([^`]+)`/g, '$1')
        .replace(/```[^`]*```/gs, '')
        .trim()
      
      try {
        editorInsertCallback('\n\n' + plainText)
        addNotification({ type: 'success', message: 'AI text inserted at cursor position' })
      } catch (err) {
        console.error('Error auto-inserting text:', err)
      }
    }
    
    setIsLoading(false)
    clearAiStream()
  }
  
  // Helper: start a streamed AI request with blocking fallback
  const startStreamedRequest = async (instruction, projectMemory, meta, structuredContext = null) => {
    // Add placeholder assistant message that will show streaming text
    setMessages(prev => [...prev, { 
      role: 'assistant', 
      content: '',
      type: meta.type,
      isStreaming: true,
      insertAtCursor: meta.insertAtCursor,
      replaceSelection: meta.replaceSelection,
      originalText: meta.originalText,
      style: meta.style,
      selectionStart: meta.selectionStart,
      selectionEnd: meta.selectionEnd,
      senses: meta.senses,
    }])
    
    // Pass the instruction as the query and the summarized memory as project_memory
    // The backend will put project_memory into the STORY DATA section of the system prompt
    // and the instruction/query into the user section
    // If structured_context is provided, backend will use token-budgeted assembly
    
    // Try streaming first for real-time token display
    let streamedText = ''
    try {
      const success = await startLoreStream(instruction, projectMemory, 'Current Project', structuredContext)
      streamedText = useStore.getState().aiStreamedText || ''
    } catch (err) {
      console.warn('Streaming failed, will fall back to blocking call:', err)
    }
    
    // If streaming produced output, finalize with it
    if (streamedText.trim()) {
      finalizeStream(meta)
      return
    }
    
    // Fallback: use the blocking askLoreAssistant call (proven reliable)
    console.log('Streaming produced no output, falling back to blocking call...')
    clearAiStream()
    
    try {
      const response = await askLoreAssistant(instruction, projectMemory, 'Current Project', structuredContext)
      
      if (response && response.trim()) {
        // Update the placeholder message with the blocking response
        setMessages(prev => {
          const updated = [...prev]
          const lastIdx = updated.length - 1
          if (lastIdx >= 0 && updated[lastIdx].role === 'assistant') {
            updated[lastIdx] = {
              ...updated[lastIdx],
              content: response,
              isStreaming: false,
            }
          }
          return updated
        })
        
        // Auto-insert for 'write' type
        if (meta?.insertAtCursor && meta?.type === 'write' && editorInsertCallback) {
          const plainText = response
            .replace(/\*\*([^*]+)\*\*/g, '$1')
            .replace(/__([^_]+)__/g, '$1')
            .replace(/\*([^*]+)\*/g, '$1')
            .replace(/_([^_]+)_/g, '$1')
            .replace(/^#{1,6}\s*/gm, '')
            .replace(/^>\s*/gm, '')
            .replace(/^[\*\-]\s*/gm, '')
            .replace(/^\d+\.\s*/gm, '')
            .replace(/`([^`]+)`/g, '$1')
            .replace(/```[^`]*```/gs, '')
            .trim()
          try {
            editorInsertCallback('\n\n' + plainText)
            addNotification({ type: 'success', message: 'AI text inserted at cursor position' })
          } catch (err) {
            console.error('Error auto-inserting text:', err)
          }
        }
      } else {
        // Both streaming and blocking failed
        setMessages(prev => {
          const updated = [...prev]
          const lastIdx = updated.length - 1
          if (lastIdx >= 0 && updated[lastIdx].role === 'assistant') {
            updated[lastIdx] = {
              ...updated[lastIdx],
              content: 'I couldn\'t generate a response. Please check if the AI model is loaded properly.',
              isStreaming: false,
            }
          }
          return updated
        })
      }
    } catch (error) {
      console.error('Blocking fallback also failed:', error)
      setMessages(prev => {
        const updated = [...prev]
        const lastIdx = updated.length - 1
        if (lastIdx >= 0 && updated[lastIdx].role === 'assistant') {
          updated[lastIdx] = {
            ...updated[lastIdx],
            content: `Error: ${error.message || 'Unknown error occurred'}. Please try again.`,
            isStreaming: false,
          }
        }
        return updated
      })
    }
    
    setIsLoading(false)
    clearAiStream()
  }
  
  // Process pending request from Editor
  const handlePendingRequest = async (request) => {
    if (!request) return
    
    // Chat Ideas just focuses the input
    if (request.type === 'chat') {
      inputRef.current?.focus()
      addNotification({ type: 'info', message: 'Ask the AI about your story ideas!' })
      return
    }
    
    // Check AI status
    if (aiStatus !== 'ready') {
      addNotification({ type: 'warning', message: 'AI is not ready. Please wait for the model to load.' })
      return
    }
    
    // Add user message showing what was requested
    let userMessage = '⚡ Generate Story Draft'
    if (request.type === 'openings') {
      userMessage = '✨ Generate 3 Opening Options'
    } else if (request.type === 'write') {
      userMessage = `✍️ Continue Writing (${request.mode || 'Continue Writing'})`
    } else if (request.type === 'rewrite') {
      userMessage = `🔄 Rewrite in "${request.style}" style`
    } else if (request.type === 'describe') {
      const sensesList = request.senses?.join(', ') || 'selected senses'
      userMessage = `✨ Describe: "${request.originalText?.substring(0, 50)}${request.originalText?.length > 50 ? '...' : ''}"\n\nSenses: ${sensesList}`
    }
    
    setMessages(prev => [...prev, { 
      role: 'user', 
      content: userMessage,
      type: request.type 
    }])
    
    setIsLoading(true)
    
    try {
      // Build structured context for server-side token budgeting
      // This gives the AI full awareness of the project (Sudowrite-style)
      let projectMemory = ''
      let structuredContext = null
      
      if (currentProjectId) {
        try {
          // For write requests, context was already gathered by Toolbar
          // But we still build structured context for proper server-side budgeting
          if (request.type === 'write' && request.context) {
            structuredContext = {
              chapter_continuity: request.context.chapterContinuity || '',
              synopsis: request.context.storyContext || '',
              worldbuilding: request.context.worldbuildingContext || '',
              outline: request.context.outlineContext || '',
              characters: request.context.characterContext || '',
              scene_context: request.context.sceneContext || '',
              series_context: request.context.seriesContext || '',
              preceding_text: request.context.precedingText || '',
              text_after: request.context.textAfterCursor || '',
            }
          } else {
            // For rewrite/describe/chat: build structured context from project data
            try {
              const [bible, characters, contextWindow, sceneData, seriesCtx] = await Promise.all([
                getStoryBible(currentProjectId),
                getCharacters(currentProjectId),
                currentChapterId 
                  ? getContextWindow(currentProjectId, currentChapterId, 2000)
                  : Promise.resolve(null),
                currentChapterId
                  ? getScenes(currentChapterId)
                  : Promise.resolve([]),
                getSeriesContextForProject(currentProjectId),
              ])
              
              let characterStr = ''
              if (characters && characters.length > 0) {
                const visibleChars = characters.filter(c => c.is_visible !== 0)
                characterStr = visibleChars.slice(0, 8).map(c => {
                  let entry = `${c.name}${c.role ? ` (${c.role})` : ''}`
                  if (c.personality_traits) entry += `: ${c.personality_traits}`
                  if (c.speech_pattern) entry += ` | Speech: ${c.speech_pattern}`
                  return entry
                }).join('\n')
              }
              
              // Build scene context string from scene data
              let sceneStr = ''
              if (sceneData && sceneData.length > 0) {
                sceneStr = sceneData.map(sc => {
                  const parts = []
                  if (sc.title) parts.push(`Scene: ${sc.title}`)
                  if (sc.pov_character) parts.push(`POV: ${sc.pov_character}`)
                  if (sc.location) parts.push(`Location: ${sc.location}`)
                  if (sc.summary) parts.push(`Summary: ${sc.summary}`)
                  return parts.join(' | ')
                }).filter(Boolean).join('\n')
              }
              
              structuredContext = {
                synopsis: bible?.synopsis_summary || bible?.synopsis?.substring(0, 800) || '',
                worldbuilding: bible?.worldbuilding_summary || bible?.worldbuilding?.substring(0, 600) || '',
                outline: bible?.outline_summary || bible?.outline?.substring(0, 600) || '',
                characters: characterStr,
                chapter_continuity: contextWindow?.prev_summary || '',
                scene_context: sceneStr,
                series_context: seriesCtx || '',
              }
              
              // For rewrite/describe, include surrounding editor context if available
              if ((request.type === 'rewrite' || request.type === 'describe') && request.context) {
                structuredContext.preceding_text = request.context?.precedingText || ''
                structuredContext.text_after = request.context?.textAfterCursor || ''
              }
            } catch (e) {
              console.warn('Could not build structured context, falling back to summarized memory:', e)
              // Fallback to flat memory
              try {
                projectMemory = await getSummarizedMemory(currentProjectId)
              } catch (e2) {
                try {
                  projectMemory = await getDeepMemory(currentProjectId, request.instruction)
                } catch (e3) {
                  console.warn('All memory methods failed:', e3)
                }
              }
            }
          }
        } catch (e) {
          console.warn('Context building failed:', e)
        }
      }
      
      // Start streamed response with structured context
      await startStreamedRequest(request.instruction, projectMemory, {
        type: request.type,
        insertAtCursor: request.insertAtCursor,
        replaceSelection: request.replaceSelection,
        originalText: request.originalText,
        style: request.style,
        selectionStart: request.selectionStart,
        selectionEnd: request.selectionEnd,
        senses: request.senses,
      }, structuredContext)
    } catch (error) {
      console.error('AI request error:', error)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `Error: ${error.message || 'Unknown error occurred'}. Please try again.`,
        type: request.type 
      }])
      setIsLoading(false)
    }
  }
  
  // Handle send message
  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return
    
    // Check AI status first
    if (aiStatus !== 'ready') {
      addNotification({ type: 'warning', message: 'AI is not ready. Please wait for the model to load.' })
      return
    }
    
    const userMessage = inputValue.trim()
    setInputValue('')
    
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: userMessage, type: 'chat' }])
    
    setIsLoading(true)
    try {
      // Build structured context for chat - gives AI full project awareness
      let projectMemory = ''
      let structuredContext = null
      
      if (currentProjectId) {
        try {
          const [bible, characters, seriesCtx] = await Promise.all([
            getStoryBible(currentProjectId),
            getCharacters(currentProjectId),
            getSeriesContextForProject(currentProjectId),
          ])
          
          let characterStr = ''
          if (characters && characters.length > 0) {
            const visibleChars = characters.filter(c => c.is_visible !== 0)
            characterStr = visibleChars.slice(0, 10).map(c => {
              let entry = `${c.name}${c.role ? ` (${c.role})` : ''}`
              if (c.personality_traits) entry += `: ${c.personality_traits}`
              if (c.speech_pattern) entry += ` | Speech: ${c.speech_pattern}`
              if (c.backstory) entry += ` | Backstory: ${c.backstory}`
              return entry
            }).join('\n')
          }
          
          structuredContext = {
            synopsis: bible?.synopsis_summary || bible?.synopsis?.substring(0, 800) || '',
            worldbuilding: bible?.worldbuilding_summary || bible?.worldbuilding?.substring(0, 600) || '',
            outline: bible?.outline_summary || bible?.outline?.substring(0, 600) || '',
            characters: characterStr,
            series_context: seriesCtx || '',
          }
        } catch (e) {
          console.warn('Could not build structured context for chat, falling back:', e)
          try {
            projectMemory = await getSummarizedMemory(currentProjectId)
          } catch (e2) {
            try {
              projectMemory = await getDeepMemory(currentProjectId, userMessage)
            } catch (e3) {
              console.warn('Could not get any memory:', e3)
            }
          }
        }
      }
      
      // Start streamed response with structured context
      await startStreamedRequest(userMessage, projectMemory, { type: 'chat' }, structuredContext)
    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `Error: ${error.message || 'Unknown error occurred'}. Please try again.`,
        type: 'chat'
      }])
      setIsLoading(false)
    }
  }
  
  // Handle keyboard submit
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }
  
  // Handle copy
  const handleCopy = (text) => {
    navigator.clipboard.writeText(text)
    addNotification({ type: 'success', message: 'Copied to clipboard' })
  }
  
  // Handle speak
  const handleSpeak = (text) => {
    if (isTtsPlaying) {
      ttsStop()
    } else {
      ttsSpeak(text, selectedVoice)
    }
  }
  
  // Handle download speech
  const handleDownloadSpeech = (text) => {
    ttsDownload(text, selectedVoice)
  }
  
  // Handle insert to editor - insert text as-is (prompts handle formatting)
  const handleInsert = (text, messageType) => {
    console.log('handleInsert called, callback exists:', !!editorInsertCallback)
    
    if (editorInsertCallback && typeof editorInsertCallback === 'function') {
      // Insert text as-is - the AI prompts are designed to output clean text
      const insertText = (text || '').trim()
      
      console.log('Calling editorInsertCallback with text length:', insertText.length)
      try {
        editorInsertCallback(insertText)
        addNotification({ type: 'success', message: 'Content inserted into editor' })
      } catch (err) {
        console.error('Error calling editorInsertCallback:', err)
        addNotification({ type: 'error', message: 'Failed to insert content: ' + err.message })
      }
    } else {
      console.log('No callback available')
      addNotification({ type: 'warning', message: 'No editor available. Open a chapter first.' })
    }
  }
  
  // Handle replace selection (for rewrite) - insert text as-is
  const handleReplace = (text, selectionStart, selectionEnd, messageType) => {
    console.log('handleReplace called, callback exists:', !!editorReplaceSelectionCallback)
    console.log('Selection positions:', selectionStart, selectionEnd)
    
    if (editorReplaceSelectionCallback && typeof editorReplaceSelectionCallback === 'function') {
      // Insert text as-is - the AI prompts are designed to output clean text
      const replaceText = (text || '').trim()
      
      try {
        // Pass the stored selection positions to replace at the correct location
        const success = editorReplaceSelectionCallback(replaceText, selectionStart, selectionEnd)
        if (success) {
          addNotification({ type: 'success', message: 'Selection replaced with rewritten text' })
        } else {
          addNotification({ type: 'warning', message: 'Could not replace selection. Try selecting text again.' })
        }
      } catch (err) {
        console.error('Error replacing selection:', err)
        addNotification({ type: 'error', message: 'Failed to replace selection: ' + err.message })
      }
    } else {
      addNotification({ type: 'warning', message: 'No editor available. Open a chapter first.' })
    }
  }
  
  // Clear chat
  const handleClear = () => {
    setMessages([])
    clearAiStream()
  }
  
  return (
    <div className="h-full flex flex-col p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xl">{Icons.BRAIN}</span>
          <h2 className="font-semibold text-gold-soft">Lore Assistant</h2>
        </div>
        
        <div className="flex items-center gap-2">
          {/* AI Status */}
          <div className={clsx(
            'w-2 h-2 rounded-full',
            aiStatus === 'ready' ? 'bg-green-400' : 
            aiStatus === 'loading' ? 'bg-gold-rich' : 'bg-red-400'
          )} />
          
          <button
            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-500 hover:bg-gold-rich/10 hover:text-gold-rich"
            onClick={handleClear}
            title="Clear Chat"
          >
            {Icons.REFRESH}
          </button>
        </div>
      </div>
      
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="text-4xl mb-4">{Icons.BRAIN}</div>
              <p className="text-gray-400 text-sm">
                Ask me anything about your story!
              </p>
              <p className="text-gray-500 text-xs mt-2">
                I know all about your characters, plot, and world.
              </p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => {
              const isLastMessage = idx === messages.length - 1
              const isStreamingMsg = msg.isStreaming && isLastMessage
              // For streaming messages, show the live aiStreamedText
              const displayContent = isStreamingMsg ? aiStreamedText : msg.content
              
              return (
                <ChatMessage
                  key={idx}
                  role={msg.role}
                  content={displayContent}
                  messageType={msg.type}
                  onCopy={handleCopy}
                  onSpeak={handleSpeak}
                  onDownload={handleDownloadSpeech}
                  onInsert={handleInsert}
                  onReplace={handleReplace}
                  canReplace={msg.replaceSelection}
                  selectionStart={msg.selectionStart}
                  selectionEnd={msg.selectionEnd}
                  senses={msg.senses}
                  isStreaming={isStreamingMsg}
                />
              )
            })}
            
            {/* Show a waiting indicator only if loading but no streaming text yet */}
            {isLoading && !aiStreamedText && messages.length > 0 && messages[messages.length - 1].role === 'user' && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full flex items-center justify-center bg-gold-rich/20">
                  {Icons.AI}
                </div>
                <div className="flex-1 p-3 rounded-lg bg-dark-700 border border-gold-rich/10">
                  <div className="flex items-center gap-2 text-gray-400 text-sm">
                    <div className="spinner !w-4 !h-4" />
                    <span>AI is thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
      
      {/* Input Area */}
      <div className="relative">
        <textarea
          ref={inputRef}
          className="input-textarea pr-12 resize-none"
          placeholder="Ask about your story..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={2}
          disabled={isLoading || aiStatus !== 'ready'}
        />
        <button
          className={clsx(
            'absolute right-3 bottom-3 w-8 h-8 rounded-lg flex items-center justify-center',
            'transition-colors',
            inputValue.trim() && !isLoading
              ? 'bg-gold-rich text-dark-950 hover:bg-gold-amber'
              : 'bg-dark-600 text-gray-500 cursor-not-allowed'
          )}
          onClick={handleSend}
          disabled={!inputValue.trim() || isLoading}
        >
          {Icons.SEND}
        </button>
      </div>
      
      {/* Quick Prompts */}
      <div className="mt-3 flex flex-wrap gap-2">
        {['Who is...', 'What happens in...', 'Describe the...'].map(prompt => (
          <button
            key={prompt}
            className="px-2 py-1 text-xs rounded bg-dark-700 text-gray-400 hover:bg-gold-rich/10 hover:text-gold-rich border border-gold-rich/10 transition-colors"
            onClick={() => setInputValue(prompt)}
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  )
}

export default AssistantPanel
