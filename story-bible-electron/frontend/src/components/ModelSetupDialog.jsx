import { useState } from 'react'
import { LuBrain, LuFolderOpen, LuX } from 'react-icons/lu'
import { usePythonBridge } from '../hooks/usePythonBridge'

function ModelSetupDialog({ 
  isOpen, 
  onClose, 
  onModelLoaded, 
  mode = 'inline',
  context = ''
}) {
  const [isSettingUpModel, setIsSettingUpModel] = useState(false)
  const { browseAndCopyModel } = usePythonBridge()

  if (!isOpen) return null

  const handleBrowseForModel = async () => {
    setIsSettingUpModel(true)
    try {
      const result = await browseAndCopyModel()
      
      if (result && result.is_loaded) {
        if (onModelLoaded) {
          onModelLoaded()
        }
        if (onClose) {
          onClose()
        }
      }
    } catch (error) {
      console.error('Failed to setup model:', error)
    } finally {
      setIsSettingUpModel(false)
    }
  }

  const handleSkip = () => {
    if (onClose) {
      onClose()
    }
  }

  const isFirstLaunch = mode === 'first-launch'
  const containerClass = isFirstLaunch
    ? 'h-screen w-screen flex items-center justify-center relative overflow-hidden'
    : 'fixed inset-0 flex items-center justify-center z-[9999] bg-black/50 backdrop-blur-sm'

  return (
    <div className={containerClass}>
      {!isFirstLaunch && (
        <div className="absolute inset-0" onClick={handleSkip} />
      )}
      
      <div className={`relative z-10 ${isFirstLaunch ? 'max-w-2xl' : 'max-w-xl'} mx-auto p-8`}>
        <div className="glass-panel rounded-2xl p-8 shadow-2xl relative">
          {!isFirstLaunch && (
            <button
              onClick={handleSkip}
              className="absolute top-4 right-4 p-2 text-text-muted hover:text-text-primary transition-colors"
              disabled={isSettingUpModel}
            >
              <LuX className="w-5 h-5" />
            </button>
          )}
          
          <div className="flex items-center gap-3 mb-6">
            <LuBrain className="w-12 h-12 text-gold-rich" />
            <div>
              <h1 className="text-3xl font-bold text-text-primary">
                {isFirstLaunch ? 'Welcome to Exelsias' : 'AI Model Required'}
              </h1>
              <p className="text-text-muted">
                {isFirstLaunch ? 'AI-Powered Story Bible' : context || 'Load a model to continue'}
              </p>
            </div>
          </div>
          
          <div className="space-y-4 mb-8">
            <p className="text-text-secondary text-lg">
              {isFirstLaunch 
                ? 'No AI model detected. To use AI features, you need to select a GGUF model file.'
                : 'This feature requires an AI model. Please select a GGUF model file to continue.'}
            </p>
            
            <div className="bg-dark-700/50 rounded-lg p-4 border border-gold-rich/20">
              <h3 className="text-sm font-semibold text-gold-rich mb-2">What you need:</h3>
              <ul className="text-sm text-text-muted space-y-1 list-disc list-inside">
                <li>A GGUF format language model (e.g., LLaMA, Mistral, etc.)</li>
                <li>The model will be copied to the application directory</li>
                <li>Recommended: 4GB+ models for better quality</li>
              </ul>
            </div>
          </div>
          
          <div className="flex gap-4">
            <button
              onClick={handleBrowseForModel}
              disabled={isSettingUpModel}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gold-rich hover:bg-gold-rich/90 text-dark-900 font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSettingUpModel ? (
                <>
                  <div className="spinner-small" />
                  <span>Setting up model...</span>
                </>
              ) : (
                <>
                  <LuFolderOpen className="w-5 h-5" />
                  <span>Browse for Model</span>
                </>
              )}
            </button>
            
            <button
              onClick={handleSkip}
              disabled={isSettingUpModel}
              className="px-6 py-3 bg-dark-700 hover:bg-dark-600 text-text-secondary font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isFirstLaunch ? 'Skip for Now' : 'Cancel'}
            </button>
          </div>
          
          {isFirstLaunch && (
            <p className="text-xs text-text-muted mt-4 text-center">
              You can always add a model later from the toolbar
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

export default ModelSetupDialog
