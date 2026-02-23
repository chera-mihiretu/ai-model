import { LuTriangleAlert, LuX, LuDownload } from 'react-icons/lu'
import useStore from '../hooks/useStore'

function ModelWarningBanner() {
  const { showModelBanner, setShowModelBanner, setShowModelDialog } = useStore()

  if (!showModelBanner) return null

  const handleLoadModel = () => {
    setShowModelDialog(true, 'Load Model')
  }

  const handleDismiss = () => {
    setShowModelBanner(false)
  }

  return (
    <div className="relative z-40 bg-gradient-to-r from-amber-900/90 to-orange-900/90 border-b border-amber-700/50 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-1">
            <LuTriangleAlert className="w-5 h-5 text-amber-300 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium text-amber-100">
                AI Model Not Loaded
              </p>
              <p className="text-xs text-amber-200/80">
                AI features are unavailable. Load a model to use AI-powered writing assistance.
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={handleLoadModel}
              className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white text-sm font-semibold rounded-lg transition-colors"
            >
              <LuDownload className="w-4 h-4" />
              <span>Load Model</span>
            </button>
            
            <button
              onClick={handleDismiss}
              className="p-2 text-amber-200 hover:text-amber-100 transition-colors"
              title="Dismiss (will reappear on restart)"
            >
              <LuX className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ModelWarningBanner
