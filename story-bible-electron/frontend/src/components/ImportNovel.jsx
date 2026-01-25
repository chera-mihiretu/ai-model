/**
 * Import Novel Component
 * ======================
 * Wizard for importing manuscripts and auto-generating story bible.
 */

import { useState, useRef } from 'react'
import useStore from '../hooks/useStore'
import { usePythonBridge } from '../hooks/usePythonBridge'
import { clsx } from 'clsx'

// Icons
const Icons = {
  UPLOAD: '📤',
  FILE: '📄',
  CHECK: '✅',
  CHAPTERS: '📑',
  CHARACTERS: '👥',
  WORLD: '🌍',
  SYNOPSIS: '📖',
  SPARKLE: '✨',
  CLOSE: '✕',
  BACK: '←',
  NEXT: '→',
  LOADING: '⏳',
}

// Wizard steps
const STEPS = {
  UPLOAD: 'upload',
  PREVIEW: 'preview',
  EXTRACT: 'extract',
  CONFIRM: 'confirm',
  COMPLETE: 'complete'
}

function ImportNovel({ isOpen, onClose }) {
  const { addNotification, setCurrentProjectId } = useStore()
  const { 
    isElectronApi,
    parseManuscript,
    importManuscriptToProject,
    detectChapters
  } = usePythonBridge()
  
  const [step, setStep] = useState(STEPS.UPLOAD)
  const [fileName, setFileName] = useState('')
  const [fileContent, setFileContent] = useState('')
  const [projectName, setProjectName] = useState('')
  const [extractAll, setExtractAll] = useState(true)
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingMessage, setProcessingMessage] = useState('')
  const [parsedData, setParsedData] = useState(null)
  const [importResult, setImportResult] = useState(null)
  
  const fileInputRef = useRef(null)
  
  // Handle file selection
  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    
    setFileName(file.name)
    setProjectName(file.name.replace(/\.[^.]+$/, '')) // Remove extension
    
    // Read file content
    const reader = new FileReader()
    reader.onload = (event) => {
      setFileContent(event.target.result)
      setStep(STEPS.PREVIEW)
    }
    reader.onerror = () => {
      addNotification({ type: 'error', message: 'Failed to read file' })
    }
    reader.readAsText(file)
  }
  
  // Handle paste content
  const handlePasteContent = () => {
    if (fileContent.trim()) {
      setFileName('Pasted content')
      setProjectName('Imported Novel')
      setStep(STEPS.PREVIEW)
    }
  }
  
  // Preview chapters
  const handlePreviewChapters = async () => {
    if (!fileContent.trim()) return
    
    setIsProcessing(true)
    setProcessingMessage('Detecting chapters...')
    
    try {
      // Use simple chapter detection for preview
      const chapters = await detectChapters(fileContent)
      setParsedData({
        chapters: chapters || [],
        word_count: fileContent.split(/\s+/).length
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
    setProcessingMessage('Analyzing manuscript with AI...')
    
    try {
      const result = await parseManuscript(fileContent, extractAll)
      setParsedData(result)
      setStep(STEPS.CONFIRM)
    } catch (error) {
      console.error('Extraction failed:', error)
      addNotification({ type: 'error', message: 'AI extraction failed. Proceeding with basic import.' })
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
    setIsProcessing(true)
    setProcessingMessage('Creating project and importing content...')
    
    try {
      const result = await importManuscriptToProject(fileContent, projectName, extractAll)
      
      if (result.error) {
        addNotification({ type: 'error', message: result.error })
        return
      }
      
      setImportResult(result)
      setStep(STEPS.COMPLETE)
      
      // Select the new project
      if (result.project_id) {
        setCurrentProjectId(result.project_id)
      }
    } catch (error) {
      console.error('Import failed:', error)
      addNotification({ type: 'error', message: 'Import failed: ' + error.message })
    } finally {
      setIsProcessing(false)
    }
  }
  
  // Reset wizard
  const handleReset = () => {
    setStep(STEPS.UPLOAD)
    setFileName('')
    setFileContent('')
    setProjectName('')
    setExtractAll(true)
    setParsedData(null)
    setImportResult(null)
  }
  
  if (!isOpen) return null
  
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="glass-card w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div>
            <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
              <span>{Icons.UPLOAD}</span>
              <span>Import Novel</span>
            </h2>
            <p className="text-sm text-text-muted mt-1">
              Import a manuscript and auto-generate your story bible
            </p>
          </div>
          <button
            className="w-8 h-8 rounded-lg flex items-center justify-center text-text-muted hover:text-text-primary hover:bg-bg-hover transition-colors"
            onClick={onClose}
          >
            {Icons.CLOSE}
          </button>
        </div>
        
        {/* Step indicator */}
        <div className="px-6 py-4 border-b border-border/50">
          <div className="flex items-center gap-2">
            {Object.values(STEPS).slice(0, -1).map((s, i) => (
              <div key={s} className="flex items-center">
                <div className={clsx(
                  'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors',
                  step === s ? 'bg-accent-primary text-white' :
                  Object.values(STEPS).indexOf(step) > i ? 'bg-green-500 text-white' :
                  'bg-bg-hover text-text-muted'
                )}>
                  {Object.values(STEPS).indexOf(step) > i ? Icons.CHECK : i + 1}
                </div>
                {i < 3 && (
                  <div className={clsx(
                    'w-8 h-0.5 mx-1',
                    Object.values(STEPS).indexOf(step) > i ? 'bg-green-500' : 'bg-border'
                  )} />
                )}
              </div>
            ))}
          </div>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Upload Step */}
          {step === STEPS.UPLOAD && (
            <div className="space-y-6">
              <div
                className="border-2 border-dashed border-border rounded-xl p-12 text-center hover:border-accent-primary transition-colors cursor-pointer"
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  accept=".txt,.md,.docx"
                  className="hidden"
                  onChange={handleFileSelect}
                />
                <div className="text-5xl mb-4">{Icons.FILE}</div>
                <h3 className="text-lg font-semibold text-text-primary mb-2">
                  Drop your manuscript here
                </h3>
                <p className="text-text-muted mb-4">
                  Supports .txt, .md, .docx files
                </p>
                <button className="btn btn-primary">
                  Choose File
                </button>
              </div>
              
              <div className="text-center text-text-muted">or</div>
              
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Paste your manuscript text:
                </label>
                <textarea
                  className="input-textarea h-40 font-mono text-sm"
                  placeholder="Paste your novel content here..."
                  value={fileContent}
                  onChange={(e) => setFileContent(e.target.value)}
                />
                <button
                  className="btn btn-secondary mt-3"
                  onClick={handlePasteContent}
                  disabled={!fileContent.trim()}
                >
                  Use Pasted Content
                </button>
              </div>
            </div>
          )}
          
          {/* Preview Step */}
          {step === STEPS.PREVIEW && (
            <div className="space-y-6">
              <div className="flex items-start gap-4">
                <div className="text-4xl">{Icons.FILE}</div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-text-primary">{fileName}</h3>
                  <p className="text-text-muted">
                    {fileContent.split(/\s+/).length.toLocaleString()} words
                  </p>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Project Name:
                </label>
                <input
                  type="text"
                  className="input"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="Enter project name..."
                />
              </div>
              
              <div className="p-4 rounded-xl bg-bg-hover/50">
                <h4 className="font-medium text-text-primary mb-2">Content Preview:</h4>
                <pre className="text-sm text-text-muted whitespace-pre-wrap max-h-40 overflow-y-auto">
                  {fileContent.slice(0, 1000)}
                  {fileContent.length > 1000 && '...'}
                </pre>
              </div>
            </div>
          )}
          
          {/* Extract Step */}
          {step === STEPS.EXTRACT && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="text-5xl mb-4">{Icons.SPARKLE}</div>
                <h3 className="text-xl font-semibold text-text-primary mb-2">
                  AI-Powered Extraction
                </h3>
                <p className="text-text-muted max-w-md mx-auto">
                  Our AI can analyze your manuscript to automatically extract:
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-bg-hover/50 border border-border">
                  <span className="text-2xl">{Icons.SYNOPSIS}</span>
                  <h4 className="font-medium text-text-primary mt-2">Synopsis</h4>
                  <p className="text-sm text-text-muted">Story overview and plot summary</p>
                </div>
                <div className="p-4 rounded-xl bg-bg-hover/50 border border-border">
                  <span className="text-2xl">{Icons.CHARACTERS}</span>
                  <h4 className="font-medium text-text-primary mt-2">Characters</h4>
                  <p className="text-sm text-text-muted">Character profiles and traits</p>
                </div>
                <div className="p-4 rounded-xl bg-bg-hover/50 border border-border">
                  <span className="text-2xl">{Icons.WORLD}</span>
                  <h4 className="font-medium text-text-primary mt-2">World Building</h4>
                  <p className="text-sm text-text-muted">Settings, locations, and elements</p>
                </div>
                <div className="p-4 rounded-xl bg-bg-hover/50 border border-border">
                  <span className="text-2xl">{Icons.CHAPTERS}</span>
                  <h4 className="font-medium text-text-primary mt-2">Chapters</h4>
                  <p className="text-sm text-text-muted">
                    {parsedData?.chapters?.length || 0} detected
                  </p>
                </div>
              </div>
              
              {!isElectronApi && (
                <div className="p-4 rounded-xl bg-yellow-500/20 border border-yellow-500/30">
                  <p className="text-yellow-400 text-sm">
                    ⚠️ AI extraction requires the Python backend. Running in offline mode - only chapter detection is available.
                  </p>
                </div>
              )}
            </div>
          )}
          
          {/* Confirm Step */}
          {step === STEPS.CONFIRM && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="text-5xl mb-4">{Icons.CHECK}</div>
                <h3 className="text-xl font-semibold text-text-primary mb-2">
                  Ready to Import
                </h3>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-xl bg-bg-hover/50">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{Icons.FILE}</span>
                    <span className="text-text-primary">{projectName}</span>
                  </div>
                  <span className="text-text-muted">
                    {fileContent.split(/\s+/).length.toLocaleString()} words
                  </span>
                </div>
                
                <div className="flex items-center justify-between p-4 rounded-xl bg-bg-hover/50">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{Icons.CHAPTERS}</span>
                    <span className="text-text-primary">Chapters</span>
                  </div>
                  <span className="text-accent-secondary font-medium">
                    {parsedData?.chapters?.length || 0} detected
                  </span>
                </div>
                
                {parsedData?.characters?.length > 0 && (
                  <div className="flex items-center justify-between p-4 rounded-xl bg-bg-hover/50">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{Icons.CHARACTERS}</span>
                      <span className="text-text-primary">Characters</span>
                    </div>
                    <span className="text-accent-secondary font-medium">
                      {parsedData.characters.length} extracted
                    </span>
                  </div>
                )}
                
                {parsedData?.world_elements?.length > 0 && (
                  <div className="flex items-center justify-between p-4 rounded-xl bg-bg-hover/50">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{Icons.WORLD}</span>
                      <span className="text-text-primary">World Elements</span>
                    </div>
                    <span className="text-accent-secondary font-medium">
                      {parsedData.world_elements.length} extracted
                    </span>
                  </div>
                )}
                
                {parsedData?.synopsis && (
                  <div className="p-4 rounded-xl bg-bg-hover/50">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">{Icons.SYNOPSIS}</span>
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
          
          {/* Complete Step */}
          {step === STEPS.COMPLETE && (
            <div className="text-center space-y-6">
              <div className="text-6xl mb-4">🎉</div>
              <h3 className="text-2xl font-bold text-text-primary">
                Import Complete!
              </h3>
              
              {importResult && (
                <div className="space-y-3 text-left max-w-sm mx-auto">
                  <div className="flex justify-between text-text-secondary">
                    <span>Chapters imported:</span>
                    <span className="font-medium text-accent-secondary">
                      {importResult.chapters_imported}
                    </span>
                  </div>
                  <div className="flex justify-between text-text-secondary">
                    <span>Characters extracted:</span>
                    <span className="font-medium text-accent-secondary">
                      {importResult.characters_imported}
                    </span>
                  </div>
                  <div className="flex justify-between text-text-secondary">
                    <span>World elements extracted:</span>
                    <span className="font-medium text-accent-secondary">
                      {importResult.world_elements_imported}
                    </span>
                  </div>
                </div>
              )}
              
              <p className="text-text-muted">
                Your project is ready! Click below to start writing.
              </p>
            </div>
          )}
          
          {/* Processing overlay */}
          {isProcessing && (
            <div className="absolute inset-0 bg-bg-card/80 flex items-center justify-center">
              <div className="text-center">
                <div className="spinner mx-auto mb-4" style={{ width: 48, height: 48 }} />
                <p className="text-text-primary font-medium">{processingMessage}</p>
                <p className="text-text-muted text-sm mt-2">This may take a moment...</p>
              </div>
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-border">
          <div>
            {step !== STEPS.UPLOAD && step !== STEPS.COMPLETE && (
              <button
                className="btn btn-ghost"
                onClick={() => {
                  const steps = Object.values(STEPS)
                  const currentIndex = steps.indexOf(step)
                  if (currentIndex > 0) {
                    setStep(steps[currentIndex - 1])
                  }
                }}
                disabled={isProcessing}
              >
                {Icons.BACK} Back
              </button>
            )}
          </div>
          
          <div className="flex items-center gap-3">
            {step === STEPS.PREVIEW && (
              <button
                className="btn btn-primary"
                onClick={handlePreviewChapters}
                disabled={isProcessing || !projectName.trim()}
              >
                Continue {Icons.NEXT}
              </button>
            )}
            
            {step === STEPS.EXTRACT && (
              <>
                <button
                  className="btn btn-ghost"
                  onClick={handleSkipExtraction}
                  disabled={isProcessing}
                >
                  Skip AI Extraction
                </button>
                <button
                  className="btn btn-primary"
                  onClick={handleExtraction}
                  disabled={isProcessing || !isElectronApi}
                >
                  {Icons.SPARKLE} Run AI Extraction
                </button>
              </>
            )}
            
            {step === STEPS.CONFIRM && (
              <button
                className="btn btn-primary"
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
                  onClick={handleReset}
                >
                  Import Another
                </button>
                <button
                  className="btn btn-primary"
                  onClick={onClose}
                >
                  Start Writing
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

