/**
 * Import Novel Component
 * ======================
 * Sudowrite-style wizard for importing manuscripts and auto-generating story bible.
 * Supports: .txt, .doc, .docx, .rtf, .odt files
 * Features:
 * - Drag and drop file upload
 * - Automatic chapter detection
 * - Character extraction
 * - Story Bible population
 * - Progress indicators
 */

import { useState, useRef, useCallback, useEffect } from 'react'
import useStore from '../hooks/useStore'
import { usePythonBridge } from '../hooks/usePythonBridge'
import { clsx } from 'clsx'
import mammoth from 'mammoth'

// Constants
const MAX_WORDS = 120000
const SUPPORTED_EXTENSIONS = ['.txt', '.doc', '.docx', '.rtf', '.odt', '.md']

// Icons
const Icons = {
  UPLOAD: (
    <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
    </svg>
  ),
  FILE: (
    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  ),
  CHECK: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  ),
  CHAPTERS: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
    </svg>
  ),
  CHARACTERS: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  ),
  WORLD: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  SYNOPSIS: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
    </svg>
  ),
  SPARKLE: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
    </svg>
  ),
  CLOSE: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  ARROW_LEFT: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
    </svg>
  ),
  ARROW_RIGHT: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  ),
  WARNING: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  SUCCESS: (
    <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
}

// Wizard steps
const STEPS = {
  UPLOAD: 'upload',
  PREVIEW: 'preview',
  EXTRACT: 'extract',
  CONFIRM: 'confirm',
  PROCESSING: 'processing',
  COMPLETE: 'complete'
}

const STEP_LABELS = {
  [STEPS.UPLOAD]: 'Upload',
  [STEPS.PREVIEW]: 'Preview',
  [STEPS.EXTRACT]: 'Analyze',
  [STEPS.CONFIRM]: 'Confirm',
}

// Progress bar component
function ProgressBar({ progress, label }) {
  return (
    <div className="w-full">
      <div className="flex justify-between text-sm text-text-muted mb-2">
        <span>{label}</span>
        <span>{Math.round(progress)}%</span>
      </div>
      <div className="w-full h-2 bg-dark-700 rounded-full overflow-hidden">
        <div 
          className="h-full bg-gradient-to-r from-gold-rich to-gold-amber transition-all duration-300 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  )
}

// Step indicator component
function StepIndicator({ currentStep }) {
  const steps = Object.values(STEPS).filter(s => s !== STEPS.PROCESSING && s !== STEPS.COMPLETE)
  const currentIndex = steps.indexOf(currentStep)
  
  return (
    <div className="flex items-center justify-center gap-2">
      {steps.map((step, i) => {
        const isCompleted = currentIndex > i
        const isCurrent = currentStep === step || 
          (currentStep === STEPS.PROCESSING && step === STEPS.CONFIRM) ||
          (currentStep === STEPS.COMPLETE && step === STEPS.CONFIRM)
        
        return (
          <div key={step} className="flex items-center">
            <div className={clsx(
              'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all duration-300',
              isCompleted ? 'bg-green-500 text-white' :
              isCurrent ? 'bg-gold-rich text-dark-900' :
              'bg-dark-700 text-text-muted'
            )}>
              {isCompleted ? Icons.CHECK : i + 1}
            </div>
            {i < steps.length - 1 && (
              <div className={clsx(
                'w-8 h-0.5 mx-1 transition-all duration-300',
                isCompleted ? 'bg-green-500' : 'bg-dark-700'
              )} />
            )}
          </div>
        )
      })}
    </div>
  )
}

// File type badge
function FileTypeBadge({ extension }) {
  const colors = {
    '.txt': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    '.docx': 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
    '.doc': 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
    '.rtf': 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    '.odt': 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    '.md': 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  }
  
  return (
    <span className={clsx(
      'px-2 py-0.5 rounded text-xs font-medium border uppercase',
      colors[extension] || 'bg-gray-500/20 text-gray-400 border-gray-500/30'
    )}>
      {extension.replace('.', '')}
    </span>
  )
}

function ImportNovel({ isOpen, onClose, onImportComplete }) {
  const { addNotification, setCurrentProject, setCurrentView, setProjects, setCurrentChapter } = useStore()
  const { 
    isElectronApi,
    parseManuscript,
    importManuscriptToProject,
    detectChapters,
    getProjectsWithChapters
  } = usePythonBridge()
  
  const [step, setStep] = useState(STEPS.UPLOAD)
  const [fileName, setFileName] = useState('')
  const [fileExtension, setFileExtension] = useState('')
  const [fileContent, setFileContent] = useState('')
  const [projectName, setProjectName] = useState('')
  const [extractAll, setExtractAll] = useState(true)
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingProgress, setProcessingProgress] = useState(0)
  const [processingMessage, setProcessingMessage] = useState('')
  const [parsedData, setParsedData] = useState(null)
  const [importResult, setImportResult] = useState(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const [fileError, setFileError] = useState('')
  const [isNavigating, setIsNavigating] = useState(false)
  
  const fileInputRef = useRef(null)
  const dropZoneRef = useRef(null)
  
  // Calculate word count
  const wordCount = fileContent ? fileContent.split(/\s+/).filter(w => w.length > 0).length : 0
  const isOverLimit = wordCount > MAX_WORDS
  
  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setStep(STEPS.UPLOAD)
      setFileName('')
      setFileExtension('')
      setFileContent('')
      setProjectName('')
      setExtractAll(true)
      setParsedData(null)
      setImportResult(null)
      setFileError('')
      setProcessingProgress(0)
    }
  }, [isOpen])
  
  // Parse file content based on type
  const parseFileContent = useCallback(async (file) => {
    const extension = '.' + file.name.split('.').pop().toLowerCase()
    setFileExtension(extension)
    setFileName(file.name)
    setProjectName(file.name.replace(/\.[^.]+$/, ''))
    setFileError('')
    
    if (!SUPPORTED_EXTENSIONS.includes(extension)) {
      setFileError(`Unsupported file type. Supported: ${SUPPORTED_EXTENSIONS.join(', ')}`)
      return
    }
    
    try {
      let content = ''
      
      if (extension === '.docx') {
        // Use mammoth for .docx files
        const arrayBuffer = await file.arrayBuffer()
        const result = await mammoth.extractRawText({ arrayBuffer })
        content = result.value
      } else if (extension === '.txt' || extension === '.md') {
        // Plain text
        content = await file.text()
      } else {
        // For .doc, .rtf, .odt - read as text (may not work perfectly)
        // In a real app, you'd want server-side conversion
        content = await file.text()
        if (content.includes('\0') || content.length < 100) {
          // Binary file detected - show warning
          setFileError(`${extension} files may not import correctly in offline mode. For best results, convert to .txt or .docx first.`)
        }
      }
      
      setFileContent(content)
      setStep(STEPS.PREVIEW)
    } catch (error) {
      console.error('File parsing error:', error)
      setFileError(`Failed to read file: ${error.message}`)
    }
  }, [])
  
  // Handle file selection
  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0]
    if (file) {
      await parseFileContent(file)
    }
  }
  
  // Drag and drop handlers
  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }, [])
  
  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }, [])
  
  const handleDrop = useCallback(async (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
    
    const file = e.dataTransfer.files?.[0]
    if (file) {
      await parseFileContent(file)
    }
  }, [parseFileContent])
  
  // Handle paste content
  const handlePasteContent = () => {
    if (fileContent.trim()) {
      setFileName('Pasted content')
      setFileExtension('.txt')
      setProjectName('Imported Novel')
      setStep(STEPS.PREVIEW)
    }
  }
  
  // Preview chapters
  const handlePreviewChapters = async () => {
    if (!fileContent.trim()) return
    
    setIsProcessing(true)
    setProcessingMessage('Detecting chapters...')
    setProcessingProgress(20)
    
    try {
      const chapters = await detectChapters(fileContent)
      setProcessingProgress(100)
      
      setParsedData({
        chapters: chapters || [],
        word_count: wordCount
      })
      setStep(STEPS.EXTRACT)
    } catch (error) {
      console.error('Chapter detection failed:', error)
      addNotification({ type: 'error', message: 'Failed to detect chapters' })
    } finally {
      setIsProcessing(false)
    }
  }
  
  // Run AI extraction
  const handleExtraction = async () => {
    setIsProcessing(true)
    setProcessingMessage('Preparing AI analysis...')
    setProcessingProgress(5)
    
    // Determine manuscript size category
    const isVeryLargeManuscript = wordCount > 100000
    const isLargeManuscript = wordCount > 50000
    const isMediumManuscript = wordCount > 20000
    
    // Estimated time based on size
    const estimatedMinutes = isVeryLargeManuscript ? 8 : isLargeManuscript ? 5 : isMediumManuscript ? 2 : 1
    
    try {
      // Progress simulation that adapts to manuscript size
      let progressValue = 5
      let elapsedSeconds = 0
      
      // Messages that cycle through to show the system is working
      const analysisMessages = [
        'Analyzing manuscript structure...',
        'Scanning for character names...',
        'Identifying relationships...',
        'Extracting story elements...',
        'Building character profiles...',
        'Analyzing narrative themes...',
        'Identifying key locations...',
        'Generating synopsis...',
        'Compiling story bible...',
        'Still working on your manuscript...',
        'Processing large text sections...',
        'Almost there, finalizing analysis...',
      ]
      
      let messageIndex = 0
      const progressInterval = setInterval(() => {
        elapsedSeconds += 1
        
        // Slower progress for larger manuscripts
        const progressIncrement = isVeryLargeManuscript ? 0.15 : isLargeManuscript ? 0.3 : isMediumManuscript ? 0.8 : 1.5
        progressValue = Math.min(progressValue + progressIncrement, 92)
        setProcessingProgress(progressValue)
        
        // Cycle through messages every few seconds
        if (elapsedSeconds % (isLargeManuscript ? 8 : 5) === 0) {
          messageIndex = (messageIndex + 1) % analysisMessages.length
          setProcessingMessage(analysisMessages[messageIndex])
        }
        
        // Add time elapsed indicator for long operations
        if (elapsedSeconds > 30 && elapsedSeconds % 15 === 0) {
          const minutesElapsed = Math.floor(elapsedSeconds / 60)
          const secondsRemaining = elapsedSeconds % 60
          if (minutesElapsed > 0) {
            setProcessingMessage(`${analysisMessages[messageIndex]} (${minutesElapsed}m ${secondsRemaining}s)`)
          }
        }
      }, 1000)
      
      // Timeout matches the backend timeout (10 minutes)
      const timeoutDuration = 600000
      
      // Create a promise that will timeout if AI takes too long
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Analysis taking longer than expected. Using basic extraction.')), timeoutDuration)
      })
      
      // Race between the actual extraction and timeout
      const result = await Promise.race([
        parseManuscript(fileContent, true),
        timeoutPromise
      ])
      
      clearInterval(progressInterval)
      setProcessingProgress(100)
      setProcessingMessage('Analysis complete!')
      
      setParsedData(result)
      setStep(STEPS.CONFIRM)
    } catch (error) {
      console.error('Extraction failed or timed out:', error)
      
      // Even on failure, try basic parsing
      try {
        const basicResult = await parseManuscript(fileContent, false)
        setParsedData(basicResult)
        addNotification({ type: 'warning', message: 'AI analysis timed out. Using basic extraction.' })
      } catch (basicError) {
        addNotification({ type: 'error', message: 'Analysis failed. Proceeding with basic import.' })
      }
      
      setStep(STEPS.CONFIRM)
    } finally {
      setIsProcessing(false)
    }
  }
  
  // Skip AI extraction
  const handleSkipExtraction = () => {
    setExtractAll(false)
    setStep(STEPS.CONFIRM)
  }
  
  // Perform import
  const handleImport = async () => {
    setStep(STEPS.PROCESSING)
    setIsProcessing(true)
    setProcessingMessage('Creating project...')
    setProcessingProgress(10)
    
    try {
      // Start with initial progress
      setProcessingProgress(20)
      setProcessingMessage('Analyzing manuscript...')
      
      // For large manuscripts, use longer timeouts
      const isLargeManuscript = wordCount > 50000
      
      // Progress simulation that continues while waiting for AI
      let progressValue = 20
      const progressInterval = setInterval(() => {
        progressValue = Math.min(progressValue + (isLargeManuscript ? 2 : 5), 85)
        setProcessingProgress(progressValue)
        
        // Update message based on progress
        if (progressValue > 30 && progressValue <= 50) {
          setProcessingMessage('Detecting chapters...')
        } else if (progressValue > 50 && progressValue <= 70) {
          setProcessingMessage('Extracting characters...')
        } else if (progressValue > 70) {
          setProcessingMessage('Building story bible...')
        }
      }, isLargeManuscript ? 2000 : 800)
      
      // Perform the actual import
      const result = await importManuscriptToProject(fileContent, projectName, extractAll)
      
      // Clear progress interval
      clearInterval(progressInterval)
      
      if (result.error) {
        addNotification({ type: 'error', message: result.error })
        setStep(STEPS.CONFIRM)
        return
      }
      
      setProcessingProgress(90)
      setProcessingMessage('Saving to database...')
      
      // CRITICAL: Refresh the projects list to include the new project with all its data
      const updatedProjects = await getProjectsWithChapters()
      if (updatedProjects) {
        setProjects(updatedProjects)
      }
      
      setProcessingProgress(100)
      setProcessingMessage('Import complete!')
      
      // Small delay to show 100% completion
      await new Promise(resolve => setTimeout(resolve, 300))
      
      setImportResult(result)
      setStep(STEPS.COMPLETE)
      
      // Notify parent that import is complete (for any additional refresh logic)
      if (onImportComplete) {
        onImportComplete(result)
      }
      
      addNotification({ 
        type: 'success', 
        message: `Successfully imported "${projectName}" with ${result.chapters_imported} chapters!` 
      })
      
    } catch (error) {
      console.error('Import failed:', error)
      addNotification({ type: 'error', message: 'Import failed: ' + error.message })
      setStep(STEPS.CONFIRM)
    } finally {
      setIsProcessing(false)
    }
  }
  
  // Handle close and go to project
  const handleGoToProject = async () => {
    if (!importResult?.project_id) {
      console.error('No project_id in importResult')
      onClose(false)
      return
    }
    
    setIsNavigating(true)
    const projectId = importResult.project_id
    
    try {
      // Refresh projects first
      const updatedProjects = await getProjectsWithChapters()
      
      if (updatedProjects) {
        setProjects(updatedProjects)
        
        // Find the imported project and select its first chapter
        const importedProject = updatedProjects.find(p => p.id === projectId)
        
        if (importedProject?.chapters?.length > 0) {
          // Sort chapters by order and select the first one
          const sortedChapters = [...importedProject.chapters].sort((a, b) => (a.order || 0) - (b.order || 0))
          setCurrentChapter(sortedChapters[0].id)
        }
      }
      
      // IMPORTANT: Set project FIRST, then view
      // This ensures the App component sees the project ID before switching away from dashboard
      setCurrentProject(projectId)
      setCurrentView('editor')
      
      // Close modal with skipRefresh=true since we already refreshed
      onClose(true)
      
    } catch (e) {
      console.error('Failed to navigate to project:', e)
      // Still try to navigate
      setCurrentProject(projectId)
      setCurrentView('editor')
      onClose(true)
    }
  }
  
  if (!isOpen) return null
  
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="glass-card w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gold-rich/20">
          <div>
            <h2 className="text-xl font-serif font-semibold text-gold-soft flex items-center gap-3">
              {Icons.UPLOAD}
              <span>Import Novel</span>
            </h2>
            <p className="text-sm text-text-muted mt-1">
              Import a manuscript and auto-generate your Story Bible
            </p>
          </div>
          <button
            className="w-8 h-8 rounded-lg flex items-center justify-center text-text-muted hover:text-gold-rich hover:bg-gold-rich/10 transition-colors"
            onClick={() => onClose(false)}
          >
            {Icons.CLOSE}
          </button>
        </div>
        
        {/* Step indicator */}
        {step !== STEPS.PROCESSING && step !== STEPS.COMPLETE && (
          <div className="px-6 py-4 border-b border-gold-rich/10">
            <StepIndicator currentStep={step} />
          </div>
        )}
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 relative">
          {/* Upload Step */}
          {step === STEPS.UPLOAD && (
            <div className="space-y-6">
              <div
                ref={dropZoneRef}
                className={clsx(
                  'border-2 border-dashed rounded-xl p-12 text-center transition-all duration-200 cursor-pointer',
                  isDragOver 
                    ? 'border-gold-rich bg-gold-rich/10 scale-[1.02]' 
                    : 'border-gold-rich/30 hover:border-gold-rich/50 hover:bg-dark-700/50'
                )}
                onClick={() => fileInputRef.current?.click()}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  accept={SUPPORTED_EXTENSIONS.join(',')}
                  className="hidden"
                  onChange={handleFileSelect}
                />
                <div className={clsx(
                  'text-gold-rich/50 mb-4 transition-colors',
                  isDragOver && 'text-gold-rich'
                )}>
                  {Icons.UPLOAD}
                </div>
                <h3 className="text-lg font-medium text-text-primary mb-2">
                  {isDragOver ? 'Drop your file here' : 'Drop your manuscript here'}
                </h3>
                <p className="text-text-muted mb-4">
                  or click to browse
                </p>
                <div className="flex flex-wrap items-center justify-center gap-2 mb-4">
                  {SUPPORTED_EXTENSIONS.map(ext => (
                    <FileTypeBadge key={ext} extension={ext} />
                  ))}
                </div>
                <p className="text-xs text-text-muted">
                  Optimized for manuscripts up to {MAX_WORDS.toLocaleString()} words
                </p>
              </div>
              
              {fileError && (
                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-start gap-3">
                  <span className="text-red-400">{Icons.WARNING}</span>
                  <p className="text-red-400 text-sm">{fileError}</p>
                </div>
              )}
              
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gold-rich/20" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-dark-800 text-text-muted">or paste text</span>
                </div>
              </div>
              
              <div>
                <textarea
                  className="w-full h-32 bg-dark-700/50 border border-gold-rich/20 rounded-xl p-4 text-text-primary placeholder:text-text-muted focus:outline-none focus:border-gold-rich/50 resize-none font-mono text-sm"
                  placeholder="Paste your novel content here..."
                  value={fileContent}
                  onChange={(e) => setFileContent(e.target.value)}
                />
                <div className="flex items-center justify-between mt-2">
                  <span className="text-xs text-text-muted">
                    {wordCount > 0 && `${wordCount.toLocaleString()} words`}
                  </span>
                  <button
                    className="btn btn-secondary text-sm"
                    onClick={handlePasteContent}
                    disabled={!fileContent.trim()}
                  >
                    Use Pasted Content
                  </button>
                </div>
              </div>
            </div>
          )}
          
          {/* Preview Step */}
          {step === STEPS.PREVIEW && (
            <div className="space-y-6">
              <div className="flex items-start gap-4 p-4 rounded-xl bg-dark-700/50 border border-gold-rich/20">
                <div className="text-gold-rich/70">{Icons.FILE}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-lg font-medium text-text-primary truncate">{fileName}</h3>
                    {fileExtension && <FileTypeBadge extension={fileExtension} />}
                  </div>
                  <p className={clsx(
                    'text-sm',
                    isOverLimit ? 'text-amber-400' : 'text-text-muted'
                  )}>
                    {wordCount.toLocaleString()} words
                    {isOverLimit && ` (exceeds ${MAX_WORDS.toLocaleString()} word limit)`}
                  </p>
                </div>
              </div>
              
              {isOverLimit && (
                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
                  <span className="text-amber-400">{Icons.WARNING}</span>
                  <div>
                    <p className="text-amber-400 text-sm font-medium">Large manuscript detected</p>
                    <p className="text-amber-400/80 text-sm mt-1">
                      Your manuscript exceeds {MAX_WORDS.toLocaleString()} words. Import may take longer and character detection might be less accurate.
                    </p>
                  </div>
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium text-gold-pale mb-2">
                  Project Name
                </label>
                <input
                  type="text"
                  className="input"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="Enter project name..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gold-pale mb-2">
                  Content Preview
                </label>
                <div className="p-4 rounded-xl bg-dark-700/30 border border-gold-rich/10 max-h-48 overflow-y-auto">
                  <pre className="text-sm text-text-muted whitespace-pre-wrap font-mono">
                    {fileContent.slice(0, 2000)}
                    {fileContent.length > 2000 && (
                      <span className="text-gold-rich/50">
                        {'\n\n'}... {(fileContent.length - 2000).toLocaleString()} more characters ...
                      </span>
                    )}
                  </pre>
                </div>
              </div>
            </div>
          )}
          
          {/* Extract Step */}
          {step === STEPS.EXTRACT && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gold-rich/20 text-gold-rich mb-4">
                  {Icons.SPARKLE}
                </div>
                <h3 className="text-xl font-serif font-semibold text-text-primary mb-2">
                  AI-Powered Analysis
                </h3>
                <p className="text-text-muted max-w-md mx-auto">
                  Analyze your manuscript to automatically extract story elements:
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-dark-700/50 border border-gold-rich/10 hover:border-gold-rich/30 transition-colors">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-gold-rich">{Icons.SYNOPSIS}</span>
                    <h4 className="font-medium text-text-primary">Synopsis</h4>
                  </div>
                  <p className="text-sm text-text-muted">Story overview and plot summary</p>
                </div>
                
                <div className="p-4 rounded-xl bg-dark-700/50 border border-gold-rich/10 hover:border-gold-rich/30 transition-colors">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-gold-rich">{Icons.CHARACTERS}</span>
                    <h4 className="font-medium text-text-primary">Characters</h4>
                  </div>
                  <p className="text-sm text-text-muted">5-7 primary character profiles</p>
                </div>
                
                <div className="p-4 rounded-xl bg-dark-700/50 border border-gold-rich/10 hover:border-gold-rich/30 transition-colors">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-gold-rich">{Icons.WORLD}</span>
                    <h4 className="font-medium text-text-primary">World Building</h4>
                  </div>
                  <p className="text-sm text-text-muted">Settings, locations, and elements</p>
                </div>
                
                <div className="p-4 rounded-xl bg-dark-700/50 border border-gold-rich/10 hover:border-gold-rich/30 transition-colors">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-gold-rich">{Icons.CHAPTERS}</span>
                    <h4 className="font-medium text-text-primary">Chapters</h4>
                  </div>
                  <p className="text-sm text-text-muted">
                    {parsedData?.chapters?.length || 0} detected
                  </p>
                </div>
              </div>
              
              {!isElectronApi && (
                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
                  <span className="text-amber-400">{Icons.WARNING}</span>
                  <div>
                    <p className="text-amber-400 text-sm font-medium">Offline Mode</p>
                    <p className="text-amber-400/80 text-sm mt-1">
                      Running without Python backend. Basic character detection and chapter splitting will be used instead of AI analysis.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Confirm Step */}
          {step === STEPS.CONFIRM && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-500/20 text-green-400 mb-4">
                  {Icons.CHECK}
                </div>
                <h3 className="text-xl font-serif font-semibold text-text-primary mb-2">
                  Ready to Import
                </h3>
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between p-4 rounded-xl bg-dark-700/50 border border-gold-rich/10">
                  <div className="flex items-center gap-3">
                    <span className="text-gold-rich/70">{Icons.FILE}</span>
                    <span className="text-text-primary font-medium">{projectName}</span>
                  </div>
                  <span className="text-text-muted">
                    {wordCount.toLocaleString()} words
                  </span>
                </div>
                
                <div className="flex items-center justify-between p-4 rounded-xl bg-dark-700/50 border border-gold-rich/10">
                  <div className="flex items-center gap-3">
                    <span className="text-gold-rich/70">{Icons.CHAPTERS}</span>
                    <span className="text-text-primary">Chapters</span>
                  </div>
                  <span className="text-gold-rich font-medium">
                    {parsedData?.chapters?.length || 0} detected
                  </span>
                </div>
                
                {parsedData?.characters?.length > 0 && (
                  <div className="flex items-center justify-between p-4 rounded-xl bg-dark-700/50 border border-gold-rich/10">
                    <div className="flex items-center gap-3">
                      <span className="text-gold-rich/70">{Icons.CHARACTERS}</span>
                      <span className="text-text-primary">Characters</span>
                    </div>
                    <span className="text-gold-rich font-medium">
                      {parsedData.characters.length} detected
                    </span>
                  </div>
                )}
                
                {parsedData?.synopsis && (
                  <div className="p-4 rounded-xl bg-dark-700/50 border border-gold-rich/10">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-gold-rich/70">{Icons.SYNOPSIS}</span>
                      <span className="text-text-primary font-medium">Synopsis</span>
                    </div>
                    <p className="text-sm text-text-muted line-clamp-3">
                      {parsedData.synopsis}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* Processing Step */}
          {step === STEPS.PROCESSING && (
            <div className="flex flex-col items-center justify-center py-12 space-y-8">
              <div className="relative">
                <div className="w-24 h-24 rounded-full border-4 border-gold-rich/20" />
                <div 
                  className="absolute inset-0 w-24 h-24 rounded-full border-4 border-gold-rich border-t-transparent animate-spin"
                />
                {/* Pulsing inner circle */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-16 h-16 rounded-full bg-gold-rich/10 animate-pulse" />
                </div>
              </div>
              
              <div className="text-center max-w-md">
                <h3 className="text-lg font-medium text-text-primary mb-2">
                  {processingMessage}
                </h3>
                <p className="text-sm text-text-muted mb-1">
                  {wordCount > 50000 
                    ? `Processing ${wordCount.toLocaleString()} words - this may take several minutes`
                    : wordCount > 20000
                    ? `Processing ${wordCount.toLocaleString()} words - please wait`
                    : 'This may take a few moments...'}
                </p>
                {wordCount > 50000 && (
                  <p className="text-xs text-gold-rich/70 mt-2">
                    Large manuscripts require more processing time for accurate character and story extraction
                  </p>
                )}
              </div>
              
              <div className="w-full max-w-md">
                <ProgressBar progress={processingProgress} label="Progress" />
              </div>
              
              {/* Info cards during processing */}
              {processingProgress > 20 && processingProgress < 90 && (
                <div className="grid grid-cols-3 gap-3 w-full max-w-md text-center">
                  <div className={clsx(
                    'p-3 rounded-lg border transition-all duration-500',
                    processingProgress > 30 ? 'bg-gold-rich/10 border-gold-rich/30' : 'bg-dark-700/30 border-dark-600'
                  )}>
                    <div className="text-lg mb-1">{Icons.CHAPTERS}</div>
                    <div className="text-xs text-text-muted">Chapters</div>
                  </div>
                  <div className={clsx(
                    'p-3 rounded-lg border transition-all duration-500',
                    processingProgress > 50 ? 'bg-gold-rich/10 border-gold-rich/30' : 'bg-dark-700/30 border-dark-600'
                  )}>
                    <div className="text-lg mb-1">{Icons.CHARACTERS}</div>
                    <div className="text-xs text-text-muted">Characters</div>
                  </div>
                  <div className={clsx(
                    'p-3 rounded-lg border transition-all duration-500',
                    processingProgress > 70 ? 'bg-gold-rich/10 border-gold-rich/30' : 'bg-dark-700/30 border-dark-600'
                  )}>
                    <div className="text-lg mb-1">{Icons.SYNOPSIS}</div>
                    <div className="text-xs text-text-muted">Synopsis</div>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Complete Step */}
          {step === STEPS.COMPLETE && (
            <div className="text-center space-y-6 py-8">
              <div className="text-green-400 flex justify-center">
                {Icons.SUCCESS}
              </div>
              <h3 className="text-2xl font-serif font-bold text-text-primary">
                Import Complete!
              </h3>
              
              {importResult && (
                <div className="space-y-3 text-left max-w-sm mx-auto bg-dark-700/30 rounded-xl p-4 border border-gold-rich/10">
                  <div className="flex justify-between text-text-secondary">
                    <span>Chapters imported:</span>
                    <span className="font-medium text-gold-rich">
                      {importResult.chapters_imported}
                    </span>
                  </div>
                  <div className="flex justify-between text-text-secondary">
                    <span>Characters extracted:</span>
                    <span className="font-medium text-gold-rich">
                      {importResult.characters_imported}
                    </span>
                  </div>
                  {importResult.world_elements_imported > 0 && (
                    <div className="flex justify-between text-text-secondary">
                      <span>World elements:</span>
                      <span className="font-medium text-gold-rich">
                        {importResult.world_elements_imported}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between text-text-secondary pt-2 border-t border-gold-rich/10">
                    <span>Total words:</span>
                    <span className="font-medium text-text-primary">
                      {importResult.word_count?.toLocaleString()}
                    </span>
                  </div>
                </div>
              )}
              
              <p className="text-text-muted">
                Your project is ready! Click below to start writing.
              </p>
            </div>
          )}
          
          {/* Processing overlay for intermediate states */}
          {isProcessing && step !== STEPS.PROCESSING && (
            <div className="absolute inset-0 bg-dark-800/80 backdrop-blur-sm flex items-center justify-center">
              <div className="text-center">
                <div className="w-12 h-12 mx-auto mb-4">
                  <div className="w-full h-full rounded-full border-3 border-gold-rich/20 border-t-gold-rich animate-spin" />
                </div>
                <p className="text-text-primary font-medium">{processingMessage}</p>
              </div>
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gold-rich/20">
          <div>
            {step !== STEPS.UPLOAD && step !== STEPS.COMPLETE && step !== STEPS.PROCESSING && (
              <button
                className="btn btn-ghost flex items-center gap-2"
                onClick={() => {
                  const steps = [STEPS.UPLOAD, STEPS.PREVIEW, STEPS.EXTRACT, STEPS.CONFIRM]
                  const currentIndex = steps.indexOf(step)
                  if (currentIndex > 0) {
                    setStep(steps[currentIndex - 1])
                  }
                }}
                disabled={isProcessing}
              >
                {Icons.ARROW_LEFT} Back
              </button>
            )}
          </div>
          
          <div className="flex items-center gap-3">
            {step === STEPS.PREVIEW && (
              <button
                className="btn btn-primary flex items-center gap-2"
                onClick={handlePreviewChapters}
                disabled={isProcessing || !projectName.trim()}
              >
                Continue {Icons.ARROW_RIGHT}
              </button>
            )}
            
            {step === STEPS.EXTRACT && (
              <>
                <button
                  className="btn btn-ghost"
                  onClick={handleSkipExtraction}
                  disabled={isProcessing}
                >
                  Skip Analysis
                </button>
                <button
                  className="btn btn-primary flex items-center gap-2"
                  onClick={handleExtraction}
                  disabled={isProcessing}
                >
                  <span className="text-gold-amber">{Icons.SPARKLE}</span>
                  Run Analysis
                </button>
              </>
            )}
            
            {step === STEPS.CONFIRM && (
              <button
                className="btn btn-primary flex items-center gap-2"
                onClick={handleImport}
                disabled={isProcessing}
              >
                {Icons.CHECK} Import Novel
              </button>
            )}
            
            {step === STEPS.COMPLETE && (
              <>
                <button
                  className="btn btn-ghost"
                  onClick={() => {
                    setStep(STEPS.UPLOAD)
                    setFileName('')
                    setFileContent('')
                    setProjectName('')
                    setParsedData(null)
                    setImportResult(null)
                  }}
                  disabled={isNavigating}
                >
                  Import Another
                </button>
                <button
                  className="btn btn-primary flex items-center gap-2"
                  onClick={handleGoToProject}
                  disabled={isNavigating}
                >
                  {isNavigating ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Opening...</span>
                    </>
                  ) : (
                    <span>Start Writing</span>
                  )}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ImportNovel
