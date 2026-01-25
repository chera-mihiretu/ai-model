/**
 * Assistant Panel Component
 * =========================
 * Right sidebar with AI chat and streaming responses.
 * Supports markdown rendering and content insertion to editor.
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
  OPENINGS: '✨',
  DRAFT: '⚡',
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
    html = html.replace(/^### (.*$)/gm, '<h3 class="text-lg font-bold text-text-primary mt-4 mb-2">$1</h3>')
    html = html.replace(/^## (.*$)/gm, '<h2 class="text-xl font-bold text-text-primary mt-4 mb-2">$1</h2>')
    html = html.replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold text-text-primary mt-4 mb-3">$1</h1>')
    
    // Bold
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-bold text-text-primary">$1</strong>')
    html = html.replace(/__([^_]+)__/g, '<strong class="font-bold text-text-primary">$1</strong>')
    
    // Italic
    html = html.replace(/\*([^*]+)\*/g, '<em class="italic">$1</em>')
    html = html.replace(/_([^_]+)_/g, '<em class="italic">$1</em>')
    
    // Code blocks
    html = html.replace(/```([^`]+)```/gs, '<pre class="bg-bg-card p-3 rounded-lg my-2 overflow-x-auto font-mono text-sm">$1</pre>')
    
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code class="bg-bg-card px-1 rounded font-mono text-sm">$1</code>')
    
    // Blockquotes
    html = html.replace(/^> (.*$)/gm, '<blockquote class="border-l-4 border-accent-primary pl-4 my-2 italic text-text-secondary">$1</blockquote>')
    
    // Horizontal rule
    html = html.replace(/^---$/gm, '<hr class="border-border my-4" />')
    
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
      className="prose prose-invert max-w-none text-sm text-text-primary"
      dangerouslySetInnerHTML={{ __html: parseMarkdown(content) }}
    />
  )
}

function ChatMessage({ role, content, onCopy, onSpeak, onInsert, messageType }) {
  const isAi = role === 'assistant'
  
  // Get the icon based on message type
  const getTypeIcon = () => {
    if (messageType === 'openings') return Icons.OPENINGS
    if (messageType === 'draft') return Icons.DRAFT
    return Icons.AI
  }
  
  return (
    <div className={clsx(
      'flex gap-3 animate-fade-in',
      isAi ? 'flex-row' : 'flex-row-reverse'
    )}>
      {/* Avatar */}
      <div className={clsx(
        'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
        isAi ? 'bg-accent-primary/20' : 'bg-bg-card'
      )}>
        {isAi ? getTypeIcon() : Icons.USER}
      </div>
      
      {/* Message */}
      <div className={clsx(
        'flex-1 p-3 rounded-lg',
        isAi ? 'bg-bg-card' : 'bg-accent-primary/20'
      )}>
        {/* Render markdown for AI messages, plain text for user */}
        {isAi ? (
          <MarkdownContent content={content} />
        ) : (
          <p className="text-text-primary text-sm whitespace-pre-wrap">
            {content}
          </p>
        )}
        
        {/* Actions */}
        {isAi && content && (
          <div className="flex items-center gap-2 mt-3 pt-2 border-t border-border/30">
            {/* Insert Button - prominent */}
            <button
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-accent-primary text-white hover:bg-accent-hover flex items-center gap-1 transition-colors"
              onClick={() => onInsert(content)}
              title="Insert at cursor position in editor"
            >
              {Icons.INSERT} Insert to Editor
            </button>
            
            <button
              className="text-xs text-text-muted hover:text-text-primary flex items-center gap-1"
              onClick={() => onCopy(content)}
            >
              {Icons.COPY} Copy
            </button>
            <button
              className="text-xs text-text-muted hover:text-text-primary flex items-center gap-1"
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
    const userMessage = request.type === 'openings' 
      ? '✨ Generate 3 Opening Options' 
      : '⚡ Generate Story Draft'
    
    setMessages(prev => [...prev, { 
      role: 'user', 
      content: userMessage,
      type: request.type 
    }])
    
    setIsLoading(true)
    
    try {
      // Get project context
      let projectMemory = ''
      try {
        projectMemory = currentProjectId 
          ? await getDeepMemory(currentProjectId, request.instruction)
          : ''
      } catch (e) {
        console.warn('Could not get deep memory:', e)
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
          type: request.type 
        }])
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
          <h2 className="font-semibold text-text-primary">Lore Assistant</h2>
        </div>
        
        <div className="flex items-center gap-2">
          {/* AI Status */}
          <div className={clsx(
            'w-2 h-2 rounded-full',
            aiStatus === 'ready' ? 'bg-green-400' : 
            aiStatus === 'loading' ? 'bg-yellow-400' : 'bg-red-400'
          )} />
          
          <button
            className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:bg-bg-hover hover:text-text-primary"
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
              <p className="text-text-muted text-sm">
                Ask me anything about your story!
              </p>
              <p className="text-text-muted text-xs mt-2">
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
              />
            ))}
            
            {/* Streaming indicator */}
            {isLoading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full flex items-center justify-center bg-accent-primary/20">
                  {Icons.AI}
                </div>
                <div className="flex-1 p-3 rounded-lg bg-bg-card">
                  <div className="flex items-center gap-2 text-text-muted text-sm">
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
              ? 'bg-accent-primary text-white hover:bg-accent-hover'
              : 'bg-bg-card text-text-muted cursor-not-allowed'
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
            className="px-2 py-1 text-xs rounded bg-bg-card/60 text-text-muted hover:bg-bg-hover hover:text-text-primary transition-colors"
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

