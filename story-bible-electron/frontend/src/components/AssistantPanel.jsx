/**
 * Assistant Panel Component
 * =========================
 * Right sidebar with AI chat and streaming responses.
 * Supports markdown rendering and content insertion to editor.
 * Paper-light theme styling.
 */

import { useState, useRef, useEffect } from 'react'
import useStore from '../hooks/useStore'
import { usePythonBridge } from '../hooks/usePythonBridge'
import { clsx } from 'clsx'

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
    html = html.replace(/^### (.*$)/gm, '<h3 class="text-lg font-bold text-gray-800 mt-4 mb-2">$1</h3>')
    html = html.replace(/^## (.*$)/gm, '<h2 class="text-xl font-bold text-gray-800 mt-4 mb-2">$1</h2>')
    html = html.replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold text-gray-800 mt-4 mb-3">$1</h1>')
    
    // Bold
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-bold text-gray-800">$1</strong>')
    html = html.replace(/__([^_]+)__/g, '<strong class="font-bold text-gray-800">$1</strong>')
    
    // Italic
    html = html.replace(/\*([^*]+)\*/g, '<em class="italic">$1</em>')
    html = html.replace(/_([^_]+)_/g, '<em class="italic">$1</em>')
    
    // Code blocks
    html = html.replace(/```([^`]+)```/gs, '<pre class="bg-gray-100 p-3 rounded-lg my-2 overflow-x-auto font-mono text-sm">$1</pre>')
    
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 rounded font-mono text-sm">$1</code>')
    
    // Blockquotes
    html = html.replace(/^> (.*$)/gm, '<blockquote class="border-l-4 border-primary-500 pl-4 my-2 italic text-gray-600">$1</blockquote>')
    
    // Horizontal rule
    html = html.replace(/^---$/gm, '<hr class="border-gray-200 my-4" />')
    
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
      className="prose max-w-none text-sm text-gray-700"
      dangerouslySetInnerHTML={{ __html: parseMarkdown(content) }}
    />
  )
}

function ChatMessage({ role, content, onCopy, onSpeak, onInsert, onReplace, messageType, canReplace, selectionStart, selectionEnd, senses }) {
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
          isAi ? 'bg-primary-100' : 'bg-gray-100'
        )}>
          {isAi ? getTypeIcon() : Icons.USER}
        </div>
        
        {/* Message */}
        <div className={clsx(
          'flex-1 p-3 rounded-lg',
          isAi ? 'bg-white border border-gray-100' : 'bg-primary-50'
        )}>
          {/* Render markdown for AI messages, plain text for user */}
          {isAi ? (
            <MarkdownContent content={content} />
          ) : (
            <p className="text-gray-700 text-sm whitespace-pre-wrap">
              {content}
            </p>
          )}
          
          {/* Actions */}
          {isAi && content && (
            <div className="flex items-center gap-2 mt-3 pt-2 border-t border-gray-100 flex-wrap">
              {/* Replace Selection Button - for rewrite messages */}
              {messageType === 'rewrite' && canReplace && (
                <button
                  className="px-3 py-1.5 text-xs font-medium rounded-lg bg-green-500 text-white hover:bg-green-600 flex items-center gap-1 transition-colors"
                  onClick={() => onReplace(content, selectionStart, selectionEnd)}
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
                    ? "bg-gray-100 text-gray-600 hover:bg-gray-200"
                    : "bg-primary-500 text-white hover:bg-primary-600"
                )}
                onClick={() => onInsert(content)}
                title="Insert at cursor position in editor"
              >
                {Icons.INSERT} Insert to Editor
              </button>
              
              <button
                className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1"
                onClick={() => onCopy(content)}
              >
                {Icons.COPY} Copy
              </button>
              <button
                className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1"
                onClick={() => onSpeak(content)}
              >
                {Icons.SPEAKER} Read
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
        <div key={idx} className="bg-white border border-gray-100 rounded-lg overflow-hidden">
          {/* Sense Header */}
          <div className="flex items-center gap-2 px-4 py-2 bg-gray-50 border-b border-gray-100">
            <span className="text-lg">{SenseIcons[section.sense] || '✨'}</span>
            <span className="text-sm font-semibold text-gray-700 tracking-wide">
              {section.sense}
            </span>
            <button
              className="ml-auto text-gray-400 hover:text-gray-600"
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
          <div className="flex items-center gap-3 px-4 py-2 border-t border-gray-100">
            <button
              className="text-sm text-gray-500 hover:text-primary-600 flex items-center gap-1 transition-colors"
              onClick={() => onInsert(section.content)}
              title="Insert this description"
            >
              ⊕ Insert
            </button>
            <button
              className="text-sm text-gray-500 hover:text-primary-600 flex items-center gap-1 transition-colors"
              onClick={() => onCopy(section.content)}
              title="Copy this description"
            >
              {Icons.COPY} Copy
            </button>
            <div className="flex items-center gap-2 ml-auto text-gray-400">
              <button className="hover:text-gray-600" title="Helpful">👍</button>
              <button className="hover:text-gray-600" title="Not helpful">👎</button>
              <button className="hover:text-yellow-500" title="Favorite">☆</button>
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
    askLoreAssistant,
    getDeepMemory,
    ttsSpeak,
    ttsStop,
    generatePluginResponse,
  } = usePythonBridge()
  
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  
  // Scroll to bottom on new messages
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
      // Get project context (skip for 'write' type as it already has context)
      let projectMemory = ''
      if (request.type !== 'write') {
        try {
          projectMemory = currentProjectId 
            ? await getDeepMemory(currentProjectId, request.instruction)
            : ''
        } catch (e) {
          console.warn('Could not get deep memory:', e)
        }
      }
      
      // Combine instruction with context
      const fullInstruction = projectMemory 
        ? `Context about the story:\n${projectMemory}\n\n${request.instruction}`
        : request.instruction
      
      // Ask lore assistant
      const response = await askLoreAssistant(fullInstruction, '', 'Current Project')
      
      // Add AI response
      if (response && response.trim()) {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: response,
          type: request.type,
          insertAtCursor: request.insertAtCursor,
          replaceSelection: request.replaceSelection,
          originalText: request.originalText,
          style: request.style,
          selectionStart: request.selectionStart,
          selectionEnd: request.selectionEnd,
          senses: request.senses,
        }])
        
        // Auto-insert for 'write' type if insertAtCursor is true
        if (request.type === 'write' && request.insertAtCursor && editorInsertCallback) {
          // Strip markdown formatting for plain text insertion
          const plainText = response
            .replace(/\*\*([^*]+)\*\*/g, '$1')  // Remove bold
            .replace(/__([^_]+)__/g, '$1')
            .replace(/\*([^*]+)\*/g, '$1')  // Remove italic
            .replace(/_([^_]+)_/g, '$1')
            .replace(/^#{1,6}\s*/gm, '')  // Remove headers
            .replace(/^>\s*/gm, '')  // Remove blockquotes
            .replace(/^[\*\-]\s*/gm, '')  // Remove list markers
            .replace(/^\d+\.\s*/gm, '')  // Remove numbered list markers
            .replace(/`([^`]+)`/g, '$1')  // Remove inline code
            .replace(/```[^`]*```/gs, '')  // Remove code blocks
            .trim()
          
          // Add a space before if needed
          const textToInsert = '\n\n' + plainText
          
          try {
            editorInsertCallback(textToInsert)
            addNotification({ type: 'success', message: 'AI text inserted at cursor position' })
          } catch (err) {
            console.error('Error auto-inserting text:', err)
            addNotification({ type: 'info', message: 'Text generated! Click "Insert to Editor" to add it.' })
          }
        }
      } else {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: 'I couldn\'t generate a response. Please check if the AI model is loaded properly.',
          type: request.type 
        }])
      }
    } catch (error) {
      console.error('AI request error:', error)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `Error: ${error.message || 'Unknown error occurred'}. Please try again.`,
        type: request.type 
      }])
    } finally {
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
      // Get project context
      let projectMemory = ''
      try {
        projectMemory = currentProjectId 
          ? await getDeepMemory(currentProjectId, userMessage)
          : ''
      } catch (e) {
        console.warn('Could not get deep memory:', e)
      }
      
      // Ask lore assistant
      const response = await askLoreAssistant(userMessage, projectMemory, 'Current Project')
      
      // Add AI response
      if (response && response.trim()) {
        setMessages(prev => [...prev, { role: 'assistant', content: response, type: 'chat' }])
      } else {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: 'I couldn\'t generate a response. Please check if the AI model is loaded properly.',
          type: 'chat'
        }])
      }
    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `Error: ${error.message || 'Unknown error occurred'}. Please try again.`,
        type: 'chat'
      }])
    } finally {
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
  
  // Handle insert to editor
  const handleInsert = (text) => {
    console.log('handleInsert called, callback exists:', !!editorInsertCallback)
    console.log('editorInsertCallback type:', typeof editorInsertCallback)
    
    if (editorInsertCallback && typeof editorInsertCallback === 'function') {
      // Strip markdown formatting for plain text insertion
      const plainText = text
        .replace(/\*\*([^*]+)\*\*/g, '$1')  // Remove bold
        .replace(/__([^_]+)__/g, '$1')
        .replace(/\*([^*]+)\*/g, '$1')  // Remove italic
        .replace(/_([^_]+)_/g, '$1')
        .replace(/^#{1,6}\s*/gm, '')  // Remove headers
        .replace(/^>\s*/gm, '')  // Remove blockquotes
        .replace(/^[\*\-]\s*/gm, '')  // Remove list markers
        .replace(/^\d+\.\s*/gm, '')  // Remove numbered list markers
        .replace(/`([^`]+)`/g, '$1')  // Remove inline code
        .replace(/```[^`]*```/gs, '')  // Remove code blocks
        .trim()
      
      console.log('Calling editorInsertCallback with text length:', plainText.length)
      try {
        editorInsertCallback(plainText)
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
  
  // Handle replace selection (for rewrite)
  const handleReplace = (text, selectionStart, selectionEnd) => {
    console.log('handleReplace called, callback exists:', !!editorReplaceSelectionCallback)
    console.log('Selection positions:', selectionStart, selectionEnd)
    
    if (editorReplaceSelectionCallback && typeof editorReplaceSelectionCallback === 'function') {
      // Strip markdown formatting for plain text replacement
      const plainText = text
        .replace(/\*\*([^*]+)\*\*/g, '$1')  // Remove bold
        .replace(/__([^_]+)__/g, '$1')
        .replace(/\*([^*]+)\*/g, '$1')  // Remove italic
        .replace(/_([^_]+)_/g, '$1')
        .replace(/^#{1,6}\s*/gm, '')  // Remove headers
        .replace(/^>\s*/gm, '')  // Remove blockquotes
        .replace(/^[\*\-]\s*/gm, '')  // Remove list markers
        .replace(/^\d+\.\s*/gm, '')  // Remove numbered list markers
        .replace(/`([^`]+)`/g, '$1')  // Remove inline code
        .replace(/```[^`]*```/gs, '')  // Remove code blocks
        .trim()
      
      try {
        // Pass the stored selection positions to replace at the correct location
        const success = editorReplaceSelectionCallback(plainText, selectionStart, selectionEnd)
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
          <h2 className="font-semibold text-gray-800">Lore Assistant</h2>
        </div>
        
        <div className="flex items-center gap-2">
          {/* AI Status */}
          <div className={clsx(
            'w-2 h-2 rounded-full',
            aiStatus === 'ready' ? 'bg-green-400' : 
            aiStatus === 'loading' ? 'bg-amber-400' : 'bg-red-400'
          )} />
          
          <button
            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600"
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
              <p className="text-gray-500 text-sm">
                Ask me anything about your story!
              </p>
              <p className="text-gray-400 text-xs mt-2">
                I know all about your characters, plot, and world.
              </p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => (
              <ChatMessage
                key={idx}
                role={msg.role}
                content={msg.content}
                messageType={msg.type}
                onCopy={handleCopy}
                onSpeak={handleSpeak}
                onInsert={handleInsert}
                onReplace={handleReplace}
                canReplace={msg.replaceSelection}
                selectionStart={msg.selectionStart}
                selectionEnd={msg.selectionEnd}
                senses={msg.senses}
              />
            ))}
            
            {/* Streaming indicator */}
            {isLoading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full flex items-center justify-center bg-primary-100">
                  {Icons.AI}
                </div>
                <div className="flex-1 p-3 rounded-lg bg-white border border-gray-100">
                  <div className="flex items-center gap-2 text-gray-500 text-sm">
                    <div className="spinner !w-4 !h-4" />
                    <span>AI is writing...</span>
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
              ? 'bg-primary-500 text-white hover:bg-primary-600'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
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
            className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700 transition-colors"
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
