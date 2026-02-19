/**
 * Python Bridge Hook
 * ==================
 * React hook for communicating with the Python backend via Electron IPC.
 * Falls back to localStorage when running in browser without Electron.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import useStore from './useStore'
import localStorageAdapter, { deleteCharacter as deleteCharacterLocal } from '../utils/localStorageAdapter'

export function usePythonBridge() {
  const {
    setAiStatus,
    setAiGenerating,
    appendAiToken,
    addNotification,
    setStorageMode,
  } = useStore()

  const pollingRef = useRef(null)

  // Check if Electron API is available
  const isElectronApi = typeof window !== 'undefined' && window.api

  // Use Electron API or localStorage fallback
  const api = isElectronApi ? window.api : localStorageAdapter

  // Notify user about storage mode on first load
  const hasNotifiedRef = useRef(false)
  useEffect(() => {
    if (!hasNotifiedRef.current) {
      hasNotifiedRef.current = true
      if (!isElectronApi) {
        console.log('📦 Running in offline mode - using localStorage')
        addNotification({
          type: 'info',
          message: 'Running in offline mode. Data saved locally in browser.'
        })
      } else {
        console.log('🔗 Connected to Python backend')
      }

      // Update store with storage mode
      if (setStorageMode) {
        setStorageMode(isElectronApi ? 'backend' : 'local')
      }
    }
  }, [isElectronApi, addNotification, setStorageMode])

  // ==================== PROJECT METHODS ====================

  const getProjects = useCallback(async () => {
    try {
      const result = isElectronApi
        ? await api.getProjects()
        : api.getProjects()
      return result || []
    } catch (error) {
      console.error('Failed to get projects:', error)
      addNotification({ type: 'error', message: 'Failed to load projects' })
      return []
    }
  }, [isElectronApi, api, addNotification])

  const getProjectsWithChapters = useCallback(async () => {
    try {
      const result = isElectronApi
        ? await api.getProjectsWithChapters()
        : api.getProjectsWithChapters()
      return result || []
    } catch (error) {
      console.error('Failed to get projects:', error)
      return []
    }
  }, [isElectronApi, api])

  const createProject = useCallback(async (name, genre = '') => {
    try {
      const projectId = isElectronApi
        ? await api.createProject(name, genre)
        : api.createProject(name, genre)

      if (projectId) {
        addNotification({ type: 'success', message: `Project "${name}" created` })
      }
      return projectId
    } catch (error) {
      console.error('Failed to create project:', error)
      addNotification({ type: 'error', message: 'Failed to create project' })
      return null
    }
  }, [isElectronApi, api, addNotification])

  const deleteProject = useCallback(async (projectId) => {
    try {
      const result = isElectronApi
        ? await api.deleteProject(projectId)
        : api.deleteProject(projectId)

      if (result) {
        addNotification({ type: 'success', message: 'Project deleted' })
      }
      return result
    } catch (error) {
      console.error('Failed to delete project:', error)
      addNotification({ type: 'error', message: 'Failed to delete project' })
      return false
    }
  }, [isElectronApi, api, addNotification])

  const renameProject = useCallback(async (projectId, newName) => {
    try {
      const result = isElectronApi
        ? await api.renameProject(projectId, newName)
        : api.renameProject(projectId, newName)
      return result
    } catch (error) {
      console.error('Failed to rename project:', error)
      return false
    }
  }, [isElectronApi, api])

  // ==================== CHAPTER METHODS ====================

  const createChapter = useCallback(async (projectId, title, content = '') => {
    try {
      const chapterId = isElectronApi
        ? await api.createChapter(projectId, title, content)
        : api.createChapter(projectId, title, content)
      return chapterId
    } catch (error) {
      console.error('Failed to create chapter:', error)
      addNotification({ type: 'error', message: 'Failed to create chapter' })
      return null
    }
  }, [isElectronApi, api, addNotification])

  const getChapterContent = useCallback(async (chapterId) => {
    try {
      const result = isElectronApi
        ? await api.getChapterContent(chapterId)
        : api.getChapterContent(chapterId)
      return result || ''
    } catch (error) {
      console.error('Failed to get chapter content:', error)
      return ''
    }
  }, [isElectronApi, api])

  const updateChapterContent = useCallback(async (chapterId, content) => {
    try {
      const result = isElectronApi
        ? await api.updateChapterContent(chapterId, content)
        : api.updateChapterContent(chapterId, content)
      return result
    } catch (error) {
      console.error('Failed to update chapter:', error)
      return false
    }
  }, [isElectronApi, api])

  const deleteChapter = useCallback(async (chapterId) => {
    try {
      const result = isElectronApi
        ? await api.deleteChapter(chapterId)
        : api.deleteChapter(chapterId)
      return result
    } catch (error) {
      console.error('Failed to delete chapter:', error)
      return false
    }
  }, [isElectronApi, api])

  const renameChapter = useCallback(async (chapterId, newTitle) => {
    try {
      const result = isElectronApi
        ? await api.renameChapter(chapterId, newTitle)
        : api.renameChapter(chapterId, newTitle)
      return result
    } catch (error) {
      console.error('Failed to rename chapter:', error)
      return false
    }
  }, [isElectronApi, api])

  const moveChapterUp = useCallback(async (chapterId) => {
    try {
      const result = isElectronApi
        ? await api.moveChapterUp(chapterId)
        : api.moveChapterUp(chapterId)
      return result
    } catch (error) {
      console.error('Failed to move chapter:', error)
      return false
    }
  }, [isElectronApi, api])

  const moveChapterDown = useCallback(async (chapterId) => {
    try {
      const result = isElectronApi
        ? await api.moveChapterDown(chapterId)
        : api.moveChapterDown(chapterId)
      return result
    } catch (error) {
      console.error('Failed to move chapter:', error)
      return false
    }
  }, [isElectronApi, api])

  const updateChapterSummaryAi = useCallback(async (chapterContent) => {
    if (!isElectronApi) {
      return 'AI summary requires the Python backend'
    }
    try {
      const result = await api.updateChapterSummaryAi(chapterContent)
      return result || ''
    } catch (error) {
      console.error('Failed to generate chapter summary:', error)
      return ''
    }
  }, [isElectronApi, api])

  // ==================== CHARACTER METHODS ====================

  const getCharacters = useCallback(async (projectId) => {
    try {
      const result = isElectronApi
        ? await api.getCharacters(projectId)
        : api.getCharacters(projectId)
      return result || []
    } catch (error) {
      console.error('Failed to get characters:', error)
      return []
    }
  }, [isElectronApi, api])

  const saveCharacter = useCallback(async (data) => {
    try {
      const result = isElectronApi
        ? await api.saveCharacter(data)
        : api.saveCharacter(data)
      return result
    } catch (error) {
      console.error('Failed to save character:', error)
      addNotification({ type: 'error', message: 'Failed to save character' })
      return false
    }
  }, [isElectronApi, api, addNotification])

  const deleteCharacter = useCallback(async (characterId) => {
    try {
      console.log('deleteCharacter called with id:', characterId, 'isElectronApi:', isElectronApi)

      let result
      if (isElectronApi) {
        result = await api.deleteCharacter(characterId)
      } else {
        // Use directly imported function for localStorage mode
        result = deleteCharacterLocal(characterId)
      }

      console.log('deleteCharacter result:', result)
      return result
    } catch (error) {
      console.error('Failed to delete character:', error)
      addNotification({ type: 'error', message: `Failed to delete character: ${error.message || error}` })
      return false
    }
  }, [isElectronApi, api, addNotification])

  // ==================== STORY BIBLE METHODS ====================

  const getStoryBible = useCallback(async (projectId) => {
    try {
      const result = isElectronApi
        ? await api.getStoryBible(projectId)
        : api.getStoryBible(projectId)
      return result || {}
    } catch (error) {
      console.error('Failed to get story bible:', error)
      return {}
    }
  }, [isElectronApi, api])

  const saveBibleField = useCallback(async (projectId, fieldName, content) => {
    try {
      const result = isElectronApi
        ? await api.saveBibleField(projectId, fieldName, content)
        : api.saveBibleField(projectId, fieldName, content)
      return result
    } catch (error) {
      console.error('Failed to save bible field:', error)
      return false
    }
  }, [isElectronApi, api])

  // ==================== CONTEXT METHODS ====================

  const getDeepMemory = useCallback(async (projectId, query) => {
    if (!isElectronApi) {
      // In offline mode, return empty string
      return ''
    }

    try {
      const result = await api.getDeepMemory(projectId, query)
      return result || ''
    } catch (error) {
      console.error('Failed to get deep memory:', error)
      return ''
    }
  }, [isElectronApi, api])

  const getSummarizedMemory = useCallback(async (projectId) => {
    if (!isElectronApi) {
      return ''
    }

    try {
      const contextSize = useStore.getState().aiContextSize
      const tier = contextSize <= 4096 ? 1000 : 1500
      const result = await api.getSummarizedMemory(projectId, tier)
      return result || ''
    } catch (error) {
      console.error('Failed to get summarized memory:', error)
      // Fall back to deep memory
      return ''
    }
  }, [isElectronApi, api])

  const getContextHealth = useCallback(async (projectId) => {
    if (!isElectronApi) {
      return null
    }
    try {
      return await api.getContextHealth(projectId)
    } catch (error) {
      console.error('Failed to get context health:', error)
      return null
    }
  }, [isElectronApi, api])

  const getContextWindow = useCallback(async (projectId, chapterId, charLimit = 3000) => {
    if (!isElectronApi) {
      return { prev_summary: '', recent_summary: '' }
    }

    try {
      const result = await api.getContextWindow(projectId, chapterId, charLimit)
      return result || { prev_summary: '', recent_summary: '' }
    } catch (error) {
      console.error('Failed to get context window:', error)
      return { prev_summary: '', recent_summary: '' }
    }
  }, [isElectronApi, api])

  // ==================== AI METHODS ====================

  const getAiStatus = useCallback(async () => {
    try {
      const status = isElectronApi
        ? await api.getAiStatus()
        : api.getAiStatus()

      setAiStatus(
        status.is_loaded ? 'ready' : 'error',
        status.status,
        status.context_size || 0
      )
      return status
    } catch (error) {
      console.error('Failed to get AI status:', error)
      setAiStatus('error', 'Failed to connect to AI', 0)
      return { status: 'error', is_loaded: false, context_size: 0 }
    }
  }, [isElectronApi, api, setAiStatus])

  const listModels = useCallback(async () => {
    try {
      const result = isElectronApi
        ? await api.listModels()
        : api.listModels()
      return result?.models || []
    } catch (error) {
      console.error('Failed to list models:', error)
      return []
    }
  }, [isElectronApi, api])

  const selectModel = useCallback(async (modelPath) => {
    if (!isElectronApi) {
      addNotification({ type: 'warning', message: 'Model selection requires the desktop app' })
      return { status: 'unavailable', is_loaded: false }
    }

    try {
      addNotification({ type: 'info', message: 'Loading model... This may take a moment.' })
      const result = await api.selectModel(modelPath)

      if (result?.is_loaded) {
        setAiStatus('ready', result.status, result.context_size || 0)
        addNotification({ type: 'success', message: result.status })
      } else {
        setAiStatus('error', result?.status || 'Failed to load model', 0)
        addNotification({ type: 'error', message: result?.status || 'Failed to load model' })
      }

      return result
    } catch (error) {
      console.error('Failed to select model:', error)
      addNotification({ type: 'error', message: `Model loading failed: ${error.message}` })
      return { status: `Error: ${error.message}`, is_loaded: false }
    }
  }, [isElectronApi, api, setAiStatus, addNotification])

  const browseForModel = useCallback(async () => {
    if (!isElectronApi) {
      addNotification({ type: 'warning', message: 'Model browsing requires the desktop app' })
      return null
    }

    try {
      const result = await api.openFileDialog({
        title: 'Select a GGUF Model File',
        filters: [
          { name: 'GGUF Models', extensions: ['gguf'] },
          { name: 'All Files', extensions: ['*'] },
        ],
        properties: ['openFile'],
      })

      if (result.canceled || !result.filePaths || result.filePaths.length === 0) {
        return null
      }

      const selectedPath = result.filePaths[0]
      return await selectModel(selectedPath)
    } catch (error) {
      console.error('Failed to browse for model:', error)
      addNotification({ type: 'error', message: `Browse failed: ${error.message}` })
      return null
    }
  }, [isElectronApi, api, selectModel, addNotification])

  const startAiStream = useCallback(async (instruction, options = {}) => {
    // In offline mode, show message instead of trying to stream
    if (!isElectronApi) {
      addNotification({
        type: 'warning',
        message: 'AI features require the full Electron app with Python backend'
      })
      return false
    }

    try {
      setAiGenerating(true)

      // Check AI status first
      const status = await api.getAiStatus()
      if (!status.is_loaded) {
        addNotification({ type: 'error', message: 'AI model not loaded. Check if the model file exists.' })
        setAiGenerating(false)
        return false
      }

      await api.aiStreamStart(instruction, options)

      // Start polling for tokens with improved error handling
      let errorCount = 0
      const maxErrors = 5

      pollingRef.current = setInterval(async () => {
        try {
          const result = await api.aiStreamPoll()

          if (result.tokens && result.tokens.length > 0) {
            result.tokens.forEach(token => appendAiToken(token))
            errorCount = 0 // Reset error count on success
          }

          if (result.done) {
            clearInterval(pollingRef.current)
            pollingRef.current = null
            setAiGenerating(false)
            addNotification({ type: 'success', message: 'AI generation complete' })
          }
        } catch (error) {
          console.error('AI polling error:', error)
          errorCount++

          if (errorCount >= maxErrors) {
            clearInterval(pollingRef.current)
            pollingRef.current = null
            setAiGenerating(false)
            addNotification({ type: 'error', message: 'AI streaming connection lost' })
          }
        }
      }, 50) // Poll more frequently for smoother streaming

      return true
    } catch (error) {
      console.error('Failed to start AI stream:', error)
      setAiGenerating(false)
      addNotification({ type: 'error', message: `AI generation failed: ${error.message}` })
      return false
    }
  }, [isElectronApi, api, setAiGenerating, appendAiToken, addNotification])

  const startLoreStream = useCallback(async (query, projectMemory = '', projectName = 'Current Project', structuredContext = null) => {
    if (!isElectronApi) {
      addNotification({
        type: 'warning',
        message: 'AI features require the full Electron app with Python backend'
      })
      return false
    }

    try {
      // Clear any previous polling interval to avoid conflicts
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }

      setAiGenerating(true)

      await api.loreStreamStart(query, projectMemory, projectName, structuredContext)

      // Start polling for tokens (same pattern as startAiStream)
      let errorCount = 0
      const maxErrors = 10
      let isPolling = false // Guard against overlapping poll calls

      return new Promise((resolve) => {
        pollingRef.current = setInterval(async () => {
          // Skip if a previous poll is still in-flight
          if (isPolling) return
          isPolling = true

          try {
            const result = await api.aiStreamPoll()

            if (result.tokens && result.tokens.length > 0) {
              result.tokens.forEach(token => appendAiToken(token))
              errorCount = 0
            }

            if (result.done) {
              clearInterval(pollingRef.current)
              pollingRef.current = null
              setAiGenerating(false)
              resolve(true)
              return
            }
          } catch (error) {
            console.error('Lore stream polling error:', error)
            errorCount++

            if (errorCount >= maxErrors) {
              clearInterval(pollingRef.current)
              pollingRef.current = null
              setAiGenerating(false)
              addNotification({ type: 'error', message: 'AI streaming connection lost' })
              resolve(false)
              return
            }
          } finally {
            isPolling = false
          }
        }, 50) // Poll every 50ms for smooth streaming
      })
    } catch (error) {
      console.error('Failed to start lore stream:', error)
      setAiGenerating(false)
      addNotification({ type: 'error', message: `AI generation failed: ${error.message}` })
      return false
    }
  }, [isElectronApi, api, setAiGenerating, appendAiToken, addNotification])

  const stopAiStream = useCallback(() => {
    // Stop polling
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }

    // Tell backend to stop generation (best-effort)
    if (isElectronApi) {
      api.aiStreamStop().catch((err) => {
        console.warn('Failed to stop AI stream on backend:', err)
      })
    }

    // Reset generating state
    setAiGenerating(false)
  }, [isElectronApi, api, setAiGenerating])

  const generatePluginResponse = useCallback(async (text, pluginType, contextData) => {
    if (!isElectronApi) {
      return 'AI features require the full Electron app with Python backend'
    }

    try {
      return await api.generatePluginResponse(text, pluginType, contextData)
    } catch (error) {
      console.error('Plugin response failed:', error)
      addNotification({ type: 'error', message: 'AI generation failed' })
      return ''
    }
  }, [isElectronApi, api, addNotification])

  const askLoreAssistant = useCallback(async (query, projectMemory, projectName, structuredContext = null) => {
    if (!isElectronApi) {
      return 'AI features require the full Electron app with Python backend'
    }

    try {
      return await api.askLoreAssistant(query, projectMemory, projectName, structuredContext)
    } catch (error) {
      console.error('Lore assistant failed:', error)
      return ''
    }
  }, [isElectronApi, api])

  const generateSingleCharacter = useCallback(async (description, genre) => {
    if (!isElectronApi) {
      return { error: 'AI features require the full Electron app with Python backend' }
    }

    try {
      return await api.generateSingleCharacter(description, genre)
    } catch (error) {
      console.error('Failed to generate single character:', error)
      return { error: error.message || 'Failed to generate character' }
    }
  }, [isElectronApi, api])

  const generateSingleWorldElement = useCallback(async (description, elementType, genre) => {
    if (!isElectronApi) {
      return { error: 'AI features require the full Electron app with Python backend' }
    }

    try {
      return await api.generateSingleWorldElement(description, elementType, genre)
    } catch (error) {
      console.error('Failed to generate single world element:', error)
      return { error: error.message || 'Failed to generate world element' }
    }
  }, [isElectronApi, api])

  // ==================== WORLD ELEMENTS METHODS ====================

  const getWorldElements = useCallback(async (projectId, seriesId = null, elementType = null) => {
    try {
      const result = isElectronApi
        ? await api.getWorldElements(projectId, seriesId, elementType)
        : api.getWorldElements(projectId, seriesId, elementType)
      return result || []
    } catch (error) {
      console.error('Failed to get world elements:', error)
      return []
    }
  }, [isElectronApi, api])

  const createWorldElement = useCallback(async (projectId, data) => {
    try {
      const result = isElectronApi
        ? await api.createWorldElement(projectId, data)
        : api.createWorldElement(projectId, data)
      return result
    } catch (error) {
      console.error('Failed to create world element:', error)
      addNotification({ type: 'error', message: 'Failed to create world element' })
      return null
    }
  }, [isElectronApi, api, addNotification])

  const updateWorldElement = useCallback(async (elementId, data) => {
    try {
      const result = isElectronApi
        ? await api.updateWorldElement(elementId, data)
        : api.updateWorldElement(elementId, data)
      return result
    } catch (error) {
      console.error('Failed to update world element:', error)
      return false
    }
  }, [isElectronApi, api])

  const deleteWorldElement = useCallback(async (elementId) => {
    try {
      const result = isElectronApi
        ? await api.deleteWorldElement(elementId)
        : api.deleteWorldElement(elementId)
      return result
    } catch (error) {
      console.error('Failed to delete world element:', error)
      return false
    }
  }, [isElectronApi, api])

  // ==================== SERIES METHODS ====================

  const getSeriesList = useCallback(async () => {
    try {
      const result = isElectronApi
        ? await api.getSeriesList()
        : api.getSeriesList()
      return result || []
    } catch (error) {
      console.error('Failed to get series list:', error)
      return []
    }
  }, [isElectronApi, api])

  const createSeries = useCallback(async (name, description = '') => {
    try {
      const result = isElectronApi
        ? await api.createSeries(name, description)
        : api.createSeries(name, description)
      return result
    } catch (error) {
      console.error('Failed to create series:', error)
      addNotification({ type: 'error', message: 'Failed to create series' })
      return null
    }
  }, [isElectronApi, api, addNotification])

  const getSeries = useCallback(async (seriesId) => {
    try {
      const result = isElectronApi
        ? await api.getSeries(seriesId)
        : api.getSeries(seriesId)
      return result
    } catch (error) {
      console.error('Failed to get series:', error)
      return null
    }
  }, [isElectronApi, api])

  const updateSeries = useCallback(async (seriesId, data) => {
    try {
      const result = isElectronApi
        ? await api.updateSeries(seriesId, data)
        : api.updateSeries(seriesId, data)
      return result
    } catch (error) {
      console.error('Failed to update series:', error)
      return false
    }
  }, [isElectronApi, api])

  const deleteSeries = useCallback(async (seriesId) => {
    try {
      const result = isElectronApi
        ? await api.deleteSeries(seriesId)
        : api.deleteSeries(seriesId)
      return result
    } catch (error) {
      console.error('Failed to delete series:', error)
      return false
    }
  }, [isElectronApi, api])

  const addProjectToSeries = useCallback(async (seriesId, projectId, bookOrder = null) => {
    try {
      const result = isElectronApi
        ? await api.addProjectToSeries(seriesId, projectId, bookOrder)
        : api.addProjectToSeries(seriesId, projectId, bookOrder)
      return result
    } catch (error) {
      console.error('Failed to add project to series:', error)
      return false
    }
  }, [isElectronApi, api])

  const removeProjectFromSeries = useCallback(async (seriesId, projectId) => {
    try {
      const result = isElectronApi
        ? await api.removeProjectFromSeries(seriesId, projectId)
        : api.removeProjectFromSeries(seriesId, projectId)
      return result
    } catch (error) {
      console.error('Failed to remove project from series:', error)
      return false
    }
  }, [isElectronApi, api])

  const getSeriesTimeline = useCallback(async (seriesId) => {
    try {
      const result = isElectronApi
        ? await api.getSeriesTimeline(seriesId)
        : api.getSeriesTimeline(seriesId)
      return result || []
    } catch (error) {
      console.error('Failed to get series timeline:', error)
      return []
    }
  }, [isElectronApi, api])

  const updateSeriesTimeline = useCallback(async (seriesId, timelineData) => {
    try {
      const result = isElectronApi
        ? await api.updateSeriesTimeline(seriesId, timelineData)
        : api.updateSeriesTimeline(seriesId, timelineData)
      return result
    } catch (error) {
      console.error('Failed to update series timeline:', error)
      return false
    }
  }, [isElectronApi, api])

  const getSeriesCharacters = useCallback(async (seriesId) => {
    try {
      const result = isElectronApi
        ? await api.getSeriesCharacters(seriesId)
        : api.getSeriesCharacters(seriesId)
      return result || []
    } catch (error) {
      console.error('Failed to get series characters:', error)
      return []
    }
  }, [isElectronApi, api])

  const getSeriesWorldElements = useCallback(async (seriesId) => {
    try {
      const result = isElectronApi
        ? await api.getSeriesWorldElements(seriesId)
        : api.getSeriesWorldElements(seriesId)
      return result || []
    } catch (error) {
      console.error('Failed to get series world elements:', error)
      return []
    }
  }, [isElectronApi, api])

  // ==================== SCENE METHODS ====================

  const getScenes = useCallback(async (chapterId) => {
    try {
      const result = isElectronApi
        ? await api.getScenes(chapterId)
        : api.getScenes(chapterId)
      return result || []
    } catch (error) {
      console.error('Failed to get scenes:', error)
      return []
    }
  }, [isElectronApi, api])

  const createScene = useCallback(async (chapterId, data) => {
    try {
      const result = isElectronApi
        ? await api.createScene(chapterId, data)
        : api.createScene(chapterId, data)
      return result
    } catch (error) {
      console.error('Failed to create scene:', error)
      addNotification({ type: 'error', message: 'Failed to create scene' })
      return null
    }
  }, [isElectronApi, api, addNotification])

  const updateScene = useCallback(async (sceneId, data) => {
    try {
      const result = isElectronApi
        ? await api.updateScene(sceneId, data)
        : api.updateScene(sceneId, data)
      return result
    } catch (error) {
      console.error('Failed to update scene:', error)
      return false
    }
  }, [isElectronApi, api])

  const deleteScene = useCallback(async (sceneId) => {
    try {
      const result = isElectronApi
        ? await api.deleteScene(sceneId)
        : api.deleteScene(sceneId)
      return result
    } catch (error) {
      console.error('Failed to delete scene:', error)
      return false
    }
  }, [isElectronApi, api])

  const getSceneContext = useCallback(async (chapterId) => {
    if (!isElectronApi) {
      return null
    }
    try {
      return await api.getSceneContext(chapterId)
    } catch (error) {
      console.error('Failed to get scene context:', error)
      return null
    }
  }, [isElectronApi, api])

  const getProjectSeriesId = useCallback(async (projectId) => {
    if (!isElectronApi) {
      return null
    }
    try {
      return await api.getProjectSeriesId(projectId)
    } catch (error) {
      console.error('Failed to get project series ID:', error)
      return null
    }
  }, [isElectronApi, api])

  const getSeriesContextForProject = useCallback(async (projectId) => {
    if (!isElectronApi) {
      return null
    }
    try {
      return await api.getSeriesContextForProject(projectId)
    } catch (error) {
      console.error('Failed to get series context:', error)
      return null
    }
  }, [isElectronApi, api])

  // ==================== CSV IMPORT/EXPORT METHODS ====================

  const exportCharactersCsv = useCallback(async (projectId) => {
    try {
      const result = isElectronApi
        ? await api.exportCharactersCsv(projectId)
        : api.exportCharactersCsv(projectId)
      return result || ''
    } catch (error) {
      console.error('Failed to export characters:', error)
      return ''
    }
  }, [isElectronApi, api])

  const importCharactersCsv = useCallback(async (projectId, csvData) => {
    try {
      const result = isElectronApi
        ? await api.importCharactersCsv(projectId, csvData)
        : api.importCharactersCsv(projectId, csvData)
      return result || { imported: 0, errors: [] }
    } catch (error) {
      console.error('Failed to import characters:', error)
      return { imported: 0, errors: [error.message] }
    }
  }, [isElectronApi, api])

  const exportWorldElementsCsv = useCallback(async (projectId) => {
    try {
      const result = isElectronApi
        ? await api.exportWorldElementsCsv(projectId)
        : api.exportWorldElementsCsv(projectId)
      return result || ''
    } catch (error) {
      console.error('Failed to export world elements:', error)
      return ''
    }
  }, [isElectronApi, api])

  const importWorldElementsCsv = useCallback(async (projectId, csvData) => {
    try {
      const result = isElectronApi
        ? await api.importWorldElementsCsv(projectId, csvData)
        : api.importWorldElementsCsv(projectId, csvData)
      return result || { imported: 0, errors: [] }
    } catch (error) {
      console.error('Failed to import world elements:', error)
      return { imported: 0, errors: [error.message] }
    }
  }, [isElectronApi, api])

  // ==================== TTS METHODS ====================

  const getTtsVoices = useCallback(async () => {
    try {
      const result = isElectronApi
        ? await api.ttsListVoices()
        : api.ttsListVoices()
      return result || []
    } catch (error) {
      console.error('Failed to get TTS voices:', error)
      return []
    }
  }, [isElectronApi, api])

  const ttsSpeak = useCallback(async (text, voice) => {
    if (!text || !text.trim()) {
      addNotification({ type: 'warning', message: 'No text to read' })
      return false
    }

    try {
      const result = isElectronApi
        ? await api.ttsReadText(text, voice)
        : api.ttsReadText(text, voice)

      if (result?.status === 'playing') {
        return true
      }
      return false
    } catch (error) {
      console.error('TTS failed:', error)
      addNotification({ type: 'error', message: `Text-to-speech failed: ${error.message}` })
      return false
    }
  }, [isElectronApi, api, addNotification])

  const ttsStop = useCallback(async () => {
    try {
      const result = isElectronApi
        ? await api.ttsStop()
        : api.ttsStop()
      return true
    } catch (error) {
      console.error('Failed to stop TTS:', error)
      return false
    }
  }, [isElectronApi, api])

  const ttsIsPlaying = useCallback(async () => {
    try {
      const result = isElectronApi
        ? await api.ttsIsPlaying()
        : api.ttsIsPlaying()
      return result?.is_playing || false
    } catch (error) {
      console.error('Failed to check TTS status:', error)
      return false
    }
  }, [isElectronApi, api])

  const ttsDownload = useCallback(async (text, voice) => {
    if (!text || !text.trim()) {
      addNotification({ type: 'warning', message: 'No text to convert to speech' })
      return false
    }

    if (!isElectronApi) {
      addNotification({ type: 'warning', message: 'Speech download requires the desktop app' })
      return false
    }

    try {
      // Open save dialog
      const result = await api.saveFileDialog({
        title: 'Save Speech Audio',
        defaultPath: 'speech.mp3',
        filters: [
          { name: 'MP3 Audio', extensions: ['mp3'] },
        ],
      })

      if (result.canceled || !result.filePath) {
        return false
      }

      addNotification({ type: 'info', message: 'Generating speech audio...' })

      // Generate MP3 to the chosen path
      const filePath = await api.ttsGenerateMp3(text, voice, result.filePath)

      if (filePath) {
        addNotification({ type: 'success', message: 'Speech audio saved successfully!' })
        return true
      } else {
        addNotification({ type: 'error', message: 'Failed to generate speech audio' })
        return false
      }
    } catch (error) {
      console.error('TTS download failed:', error)
      addNotification({ type: 'error', message: `Speech download failed: ${error.message}` })
      return false
    }
  }, [isElectronApi, api, addNotification])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
    }
  }, [])

  return {
    // Connection info
    isApiAvailable: true, // Always true now (either Electron or localStorage)
    isElectronApi,
    storageMode: isElectronApi ? 'backend' : 'local',

    // Projects
    getProjects,
    getProjectsWithChapters,
    createProject,
    deleteProject,
    renameProject,

    // Chapters
    createChapter,
    getChapterContent,
    updateChapterContent,
    deleteChapter,
    renameChapter,
    moveChapterUp,
    moveChapterDown,
    updateChapterSummaryAi,

    // Characters
    getCharacters,
    saveCharacter,
    deleteCharacter,

    // Story Bible
    getStoryBible,
    saveBibleField,

    // Context
    getDeepMemory,
    getSummarizedMemory,
    getContextWindow,
    getContextHealth,

    // AI
    getAiStatus,
    listModels,
    selectModel,
    browseForModel,
    startAiStream,
    startLoreStream,
    stopAiStream,
    generatePluginResponse,
    askLoreAssistant,
    generateSingleCharacter,
    generateSingleWorldElement,

    // TTS
    getTtsVoices,
    ttsSpeak,
    ttsStop,
    ttsIsPlaying,
    ttsDownload,

    // World Elements
    getWorldElements,
    createWorldElement,
    updateWorldElement,
    deleteWorldElement,

    // Series
    getSeriesList,
    createSeries,
    getSeries,
    updateSeries,
    deleteSeries,
    addProjectToSeries,
    removeProjectFromSeries,
    getSeriesTimeline,
    updateSeriesTimeline,
    getSeriesCharacters,
    getSeriesWorldElements,

    // Scenes
    getScenes,
    createScene,
    updateScene,
    deleteScene,
    getSceneContext,

    // Project helpers
    getProjectSeriesId,
    getSeriesContextForProject,

    // CSV Import/Export
    exportCharactersCsv,
    importCharactersCsv,
    exportWorldElementsCsv,
    importWorldElementsCsv,

    // Import Novel
    parseManuscript: async (content, extractAll = true) => {
      if (!isElectronApi) {
        // Use localStorageAdapter's parse function
        return localStorageAdapter.parseManuscript(content, extractAll)
      }

      try {
        return await api.parseManuscript(content, extractAll)
      } catch (error) {
        console.error('Parse manuscript failed:', error)
        // Fallback to local parsing
        return localStorageAdapter.parseManuscript(content, extractAll)
      }
    },

    detectChapters: async (content) => {
      if (!isElectronApi) {
        // Use localStorageAdapter's chapter detection
        return localStorageAdapter.detectChaptersFromText(content)
      }

      try {
        return await api.detectChapters(content)
      } catch (error) {
        console.error('Detect chapters failed:', error)
        // Fallback to local detection
        return localStorageAdapter.detectChaptersFromText(content)
      }
    },

    importManuscriptToProject: async (content, projectName, extractAll = true) => {
      if (!isElectronApi) {
        // Use localStorageAdapter's import function for offline mode
        const result = localStorageAdapter.importManuscriptToProject(content, projectName, extractAll)
        if (result.success) {
          addNotification({ type: 'success', message: `Imported "${projectName}" successfully!` })
        }
        return result
      }

      try {
        return await api.importManuscriptToProject(content, projectName, extractAll)
      } catch (error) {
        console.error('Import manuscript failed:', error)
        // Fallback to local import
        addNotification({ type: 'warning', message: 'Backend unavailable, using local import' })
        return localStorageAdapter.importManuscriptToProject(content, projectName, extractAll)
      }
    },
  }
}

export default usePythonBridge
