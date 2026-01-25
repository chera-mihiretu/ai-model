/**
 * Python Bridge Hook
 * ==================
 * React hook for communicating with the Python backend via Electron IPC.
 * Falls back to localStorage when running in browser without Electron.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import useStore from './useStore'
import localStorageAdapter from '../utils/localStorageAdapter'

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
        status.status
      )
      return status
    } catch (error) {
      console.error('Failed to get AI status:', error)
      setAiStatus('error', 'Failed to connect to AI')
      return { status: 'error', is_loaded: false }
    }
  }, [isElectronApi, api, setAiStatus])
  
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
  
  const askLoreAssistant = useCallback(async (query, projectMemory, projectName) => {
    if (!isElectronApi) {
      return 'AI features require the full Electron app with Python backend'
    }
    
    try {
      return await api.askLoreAssistant(query, projectMemory, projectName)
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
    
    // Story Bible
    getStoryBible,
    saveBibleField,
    
    // Context
    getDeepMemory,
    getContextWindow,
    
    // AI
    getAiStatus,
    startAiStream,
    generatePluginResponse,
    askLoreAssistant,
    generateSingleCharacter,
    generateSingleWorldElement,
    
    // TTS
    getTtsVoices,
    ttsSpeak,
    ttsStop,
    ttsIsPlaying,
    
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
    
    // Scenes
    getScenes,
    createScene,
    updateScene,
    deleteScene,
    
    // CSV Import/Export
    exportCharactersCsv,
    importCharactersCsv,
    exportWorldElementsCsv,
    importWorldElementsCsv,
    
    // Import Novel
    parseManuscript: async (content, extractAll = true) => {
      if (!isElectronApi) {
        // Offline mode - simple chapter detection only
        const lines = content.split('\n')
        const chapters = []
        let currentChapter = null
        let currentContent = []
        
        for (const line of lines) {
          if (/^(Chapter|CHAPTER|Part|PART)\s+\d+/i.test(line.trim())) {
            if (currentChapter) {
              chapters.push({ title: currentChapter, content: currentContent.join('\n').trim() })
            }
            currentChapter = line.trim()
            currentContent = []
          } else if (currentChapter) {
            currentContent.push(line)
          }
        }
        if (currentChapter) {
          chapters.push({ title: currentChapter, content: currentContent.join('\n').trim() })
        }
        if (chapters.length === 0) {
          chapters.push({ title: 'Chapter 1', content: content.trim() })
        }
        
        return {
          chapters,
          synopsis: '',
          characters: [],
          world_elements: [],
          word_count: content.split(/\s+/).length
        }
      }
      
      try {
        return await api.parseManuscript(content, extractAll)
      } catch (error) {
        console.error('Parse manuscript failed:', error)
        return { chapters: [], synopsis: '', characters: [], world_elements: [] }
      }
    },
    
    detectChapters: async (content) => {
      if (!isElectronApi) {
        // Same simple detection as above
        const lines = content.split('\n')
        const chapters = []
        let currentChapter = null
        let currentContent = []
        
        for (const line of lines) {
          if (/^(Chapter|CHAPTER|Part|PART)\s+\d+/i.test(line.trim())) {
            if (currentChapter) {
              chapters.push({ title: currentChapter, content: currentContent.join('\n').trim() })
            }
            currentChapter = line.trim()
            currentContent = []
          } else if (currentChapter) {
            currentContent.push(line)
          }
        }
        if (currentChapter) {
          chapters.push({ title: currentChapter, content: currentContent.join('\n').trim() })
        }
        if (chapters.length === 0) {
          chapters.push({ title: 'Chapter 1', content: content.trim() })
        }
        
        return chapters
      }
      
      try {
        return await api.detectChapters(content)
      } catch (error) {
        console.error('Detect chapters failed:', error)
        return []
      }
    },
    
    importManuscriptToProject: async (content, projectName, extractAll = true) => {
      if (!isElectronApi) {
        addNotification({ type: 'warning', message: 'Full import requires the Python backend' })
        return { error: 'Backend not available' }
      }
      
      try {
        return await api.importManuscriptToProject(content, projectName, extractAll)
      } catch (error) {
        console.error('Import manuscript failed:', error)
        return { error: error.message }
      }
    },
  }
}

export default usePythonBridge
