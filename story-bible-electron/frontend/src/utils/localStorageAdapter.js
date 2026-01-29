/**
 * Local Storage Adapter
 * =====================
 * Provides a localStorage-based fallback storage when Python backend is unavailable.
 * Mirrors the Python API so the app can work in standalone browser mode.
 */

const STORAGE_KEYS = {
  PROJECTS: 'storybible_projects',
  CHAPTERS: 'storybible_chapters',
  CHARACTERS: 'storybible_characters',
  STORY_BIBLE: 'storybible_bible',
  APP_STATE: 'storybible_app_state',
  WORLD_ELEMENTS: 'storybible_world_elements',
  SERIES: 'storybible_series',
  SCENES: 'storybible_scenes',
}

// ==================== HELPERS ====================

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 9)
}

function getStorage(key) {
  try {
    const data = localStorage.getItem(key)
    return data ? JSON.parse(data) : null
  } catch (error) {
    console.error(`Failed to read ${key} from localStorage:`, error)
    return null
  }
}

function setStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
    return true
  } catch (error) {
    console.error(`Failed to write ${key} to localStorage:`, error)
    return false
  }
}

// ==================== PROJECT METHODS ====================

export function getProjects() {
  const projects = getStorage(STORAGE_KEYS.PROJECTS) || []
  return projects.map(({ id, name, genre, created_at }) => ({ id, name, genre, created_at }))
}

export function getProjectsWithChapters() {
  const projects = getStorage(STORAGE_KEYS.PROJECTS) || []
  const chapters = getStorage(STORAGE_KEYS.CHAPTERS) || []
  
  return projects.map(project => ({
    ...project,
    chapters: chapters
      .filter(ch => ch.project_id === project.id)
      .sort((a, b) => (a.order || 0) - (b.order || 0))
  }))
}

export function createProject(name, genre = '') {
  const projects = getStorage(STORAGE_KEYS.PROJECTS) || []
  
  const newProject = {
    id: generateId(),
    name,
    genre,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
  
  projects.unshift(newProject) // Add to beginning
  setStorage(STORAGE_KEYS.PROJECTS, projects)
  
  // Initialize empty story bible for this project
  const bibles = getStorage(STORAGE_KEYS.STORY_BIBLE) || {}
  bibles[newProject.id] = {
    braindump: '',
    genre: genre,
    style: '',
    synopsis: '',
    worldbuilding: '',
    outline: '',
  }
  setStorage(STORAGE_KEYS.STORY_BIBLE, bibles)
  
  return newProject.id
}

export function deleteProject(projectId) {
  // Delete project
  let projects = getStorage(STORAGE_KEYS.PROJECTS) || []
  projects = projects.filter(p => p.id !== projectId)
  setStorage(STORAGE_KEYS.PROJECTS, projects)
  
  // Delete associated chapters
  let chapters = getStorage(STORAGE_KEYS.CHAPTERS) || []
  chapters = chapters.filter(ch => ch.project_id !== projectId)
  setStorage(STORAGE_KEYS.CHAPTERS, chapters)
  
  // Delete associated characters
  let characters = getStorage(STORAGE_KEYS.CHARACTERS) || []
  characters = characters.filter(c => c.project_id !== projectId)
  setStorage(STORAGE_KEYS.CHARACTERS, characters)
  
  // Delete story bible
  const bibles = getStorage(STORAGE_KEYS.STORY_BIBLE) || {}
  delete bibles[projectId]
  setStorage(STORAGE_KEYS.STORY_BIBLE, bibles)
  
  return true
}

export function renameProject(projectId, newName) {
  const projects = getStorage(STORAGE_KEYS.PROJECTS) || []
  const project = projects.find(p => p.id === projectId)
  
  if (project) {
    project.name = newName
    project.updated_at = new Date().toISOString()
    setStorage(STORAGE_KEYS.PROJECTS, projects)
    return true
  }
  return false
}

export function getProjectSettings(projectId) {
  const projects = getStorage(STORAGE_KEYS.PROJECTS) || []
  return projects.find(p => p.id === projectId) || null
}

// ==================== CHAPTER METHODS ====================

export function createChapter(projectId, title, content = '') {
  const chapters = getStorage(STORAGE_KEYS.CHAPTERS) || []
  
  // Get max order for this project
  const projectChapters = chapters.filter(ch => ch.project_id === projectId)
  const maxOrder = projectChapters.length > 0 
    ? Math.max(...projectChapters.map(ch => ch.order || 0)) 
    : -1
  
  const newChapter = {
    id: generateId(),
    project_id: projectId,
    title,
    content,
    order: maxOrder + 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
  
  chapters.push(newChapter)
  setStorage(STORAGE_KEYS.CHAPTERS, chapters)
  
  return newChapter.id
}

export function getChapters(projectId) {
  const chapters = getStorage(STORAGE_KEYS.CHAPTERS) || []
  return chapters
    .filter(ch => ch.project_id === projectId)
    .sort((a, b) => (a.order || 0) - (b.order || 0))
    .map(({ id, title, order }) => ({ id, title, order }))
}

export function getChapterContent(chapterId) {
  const chapters = getStorage(STORAGE_KEYS.CHAPTERS) || []
  const chapter = chapters.find(ch => ch.id === chapterId)
  return chapter ? chapter.content : ''
}

export function updateChapterContent(chapterId, content) {
  const chapters = getStorage(STORAGE_KEYS.CHAPTERS) || []
  const chapter = chapters.find(ch => ch.id === chapterId)
  
  if (chapter) {
    chapter.content = content
    chapter.updated_at = new Date().toISOString()
    setStorage(STORAGE_KEYS.CHAPTERS, chapters)
    return true
  }
  return false
}

export function renameChapter(chapterId, newTitle) {
  const chapters = getStorage(STORAGE_KEYS.CHAPTERS) || []
  const chapter = chapters.find(ch => ch.id === chapterId)
  
  if (chapter) {
    chapter.title = newTitle
    chapter.updated_at = new Date().toISOString()
    setStorage(STORAGE_KEYS.CHAPTERS, chapters)
    return true
  }
  return false
}

export function deleteChapter(chapterId) {
  let chapters = getStorage(STORAGE_KEYS.CHAPTERS) || []
  chapters = chapters.filter(ch => ch.id !== chapterId)
  setStorage(STORAGE_KEYS.CHAPTERS, chapters)
  return true
}

export function moveChapterUp(chapterId) {
  const chapters = getStorage(STORAGE_KEYS.CHAPTERS) || []
  const chapter = chapters.find(ch => ch.id === chapterId)
  
  if (!chapter) return false
  
  const projectChapters = chapters
    .filter(ch => ch.project_id === chapter.project_id)
    .sort((a, b) => (a.order || 0) - (b.order || 0))
  
  const index = projectChapters.findIndex(ch => ch.id === chapterId)
  if (index <= 0) return false
  
  // Swap orders
  const prevChapter = projectChapters[index - 1]
  const tempOrder = chapter.order
  chapter.order = prevChapter.order
  prevChapter.order = tempOrder
  
  setStorage(STORAGE_KEYS.CHAPTERS, chapters)
  return true
}

export function moveChapterDown(chapterId) {
  const chapters = getStorage(STORAGE_KEYS.CHAPTERS) || []
  const chapter = chapters.find(ch => ch.id === chapterId)
  
  if (!chapter) return false
  
  const projectChapters = chapters
    .filter(ch => ch.project_id === chapter.project_id)
    .sort((a, b) => (a.order || 0) - (b.order || 0))
  
  const index = projectChapters.findIndex(ch => ch.id === chapterId)
  if (index >= projectChapters.length - 1) return false
  
  // Swap orders
  const nextChapter = projectChapters[index + 1]
  const tempOrder = chapter.order
  chapter.order = nextChapter.order
  nextChapter.order = tempOrder
  
  setStorage(STORAGE_KEYS.CHAPTERS, chapters)
  return true
}

// ==================== CHARACTER METHODS ====================

export function getCharacters(projectId) {
  const characters = getStorage(STORAGE_KEYS.CHARACTERS) || []
  return characters.filter(c => c.project_id === projectId)
}

export function getAllCharacters(projectId) {
  return getCharacters(projectId)
}

export function getCharacterDetails(name, projectId) {
  const characters = getStorage(STORAGE_KEYS.CHARACTERS) || []
  return characters.find(c => c.name === name && c.project_id === projectId) || null
}

export function saveCharacter(data) {
  const characters = getStorage(STORAGE_KEYS.CHARACTERS) || []
  
  // Check if character exists
  const existingIndex = characters.findIndex(
    c => c.id === data.id || (c.name === data.name && c.project_id === data.project_id)
  )
  
  if (existingIndex >= 0) {
    // Update existing
    characters[existingIndex] = {
      ...characters[existingIndex],
      ...data,
      updated_at: new Date().toISOString(),
    }
  } else {
    // Create new
    characters.push({
      id: generateId(),
      ...data,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
  }
  
  setStorage(STORAGE_KEYS.CHARACTERS, characters)
  return true
}

export function deleteCharacter(characterId) {
  let characters = getStorage(STORAGE_KEYS.CHARACTERS) || []
  characters = characters.filter(c => c.id !== characterId)
  setStorage(STORAGE_KEYS.CHARACTERS, characters)
  return true
}

// ==================== STORY BIBLE METHODS ====================

export function getStoryBible(projectId) {
  const bibles = getStorage(STORAGE_KEYS.STORY_BIBLE) || {}
  return bibles[projectId] || {
    braindump: '',
    genre: '',
    style: '',
    synopsis: '',
    worldbuilding: '',
    outline: '',
  }
}

export function saveBibleField(projectId, fieldName, content) {
  const bibles = getStorage(STORAGE_KEYS.STORY_BIBLE) || {}
  
  if (!bibles[projectId]) {
    bibles[projectId] = {
      braindump: '',
      genre: '',
      style: '',
      synopsis: '',
      worldbuilding: '',
      outline: '',
    }
  }
  
  bibles[projectId][fieldName] = content
  setStorage(STORAGE_KEYS.STORY_BIBLE, bibles)
  return true
}

export function getBibleField(projectId, fieldName) {
  const bible = getStoryBible(projectId)
  return bible[fieldName] || ''
}

// ==================== APP STATE METHODS ====================

export function saveAppState(key, value) {
  const state = getStorage(STORAGE_KEYS.APP_STATE) || {}
  state[key] = value
  setStorage(STORAGE_KEYS.APP_STATE, state)
  return true
}

export function getAppState(key) {
  const state = getStorage(STORAGE_KEYS.APP_STATE) || {}
  return state[key] || null
}

// ==================== CONTEXT METHODS ====================

export function getDeepMemory(projectId, query) {
  // In offline mode, return a simple context from story bible
  const bible = getStoryBible(projectId)
  const characters = getCharacters(projectId)
  
  let context = ''
  if (bible.synopsis) {
    context += `Synopsis: ${bible.synopsis}\n`
  }
  if (characters.length > 0) {
    context += `Characters: ${characters.map(c => c.name).join(', ')}\n`
  }
  
  return context
}

export function getContextWindow(projectId, chapterId, charLimit = 3000) {
  return {
    prev_summary: '',
    recent_summary: '',
  }
}

// ==================== AI METHODS (Stubs for offline mode) ====================

export function getAiStatus() {
  return {
    status: 'AI unavailable in offline mode',
    is_loaded: false,
  }
}

export function aiStreamStart() {
  return { status: 'unavailable' }
}

export function aiStreamPoll() {
  return { tokens: ['AI is not available in offline mode. Please run the full Electron app with Python backend.'], done: true }
}

export function generatePluginResponse() {
  return 'AI features require the Python backend. Please run the full Electron app.'
}

export function askLoreAssistant() {
  return 'AI features require the Python backend. Please run the full Electron app.'
}

// ==================== WORLD ELEMENTS METHODS ====================

export function getWorldElements(projectId, seriesId = null, elementType = null) {
  const elements = getStorage(STORAGE_KEYS.WORLD_ELEMENTS) || []
  let filtered = elements
  
  if (projectId) {
    filtered = filtered.filter(e => e.project_id === projectId)
  }
  if (seriesId) {
    filtered = filtered.filter(e => e.series_id === seriesId)
  }
  if (elementType) {
    filtered = filtered.filter(e => e.element_type === elementType)
  }
  
  return filtered.sort((a, b) => (a.element_type || '').localeCompare(b.element_type || ''))
}

export function createWorldElement(projectId, data) {
  const elements = getStorage(STORAGE_KEYS.WORLD_ELEMENTS) || []
  
  const newElement = {
    id: generateId(),
    project_id: projectId,
    series_id: data.series_id || null,
    name: data.name || 'Unnamed Element',
    element_type: data.element_type || 'other',
    description: data.description || '',
    sensory_details: data.sensory_details || '',
    significance: data.significance || '',
    custom_traits: data.custom_traits || '',
    source_project_id: projectId,
    is_visible: 1,
    created_at: new Date().toISOString(),
  }
  
  elements.push(newElement)
  setStorage(STORAGE_KEYS.WORLD_ELEMENTS, elements)
  
  return newElement.id
}

export function getWorldElement(elementId) {
  const elements = getStorage(STORAGE_KEYS.WORLD_ELEMENTS) || []
  return elements.find(e => e.id === elementId) || null
}

export function updateWorldElement(elementId, data) {
  const elements = getStorage(STORAGE_KEYS.WORLD_ELEMENTS) || []
  const element = elements.find(e => e.id === elementId)
  
  if (element) {
    Object.assign(element, data)
    element.updated_at = new Date().toISOString()
    setStorage(STORAGE_KEYS.WORLD_ELEMENTS, elements)
    return true
  }
  return false
}

export function deleteWorldElement(elementId) {
  let elements = getStorage(STORAGE_KEYS.WORLD_ELEMENTS) || []
  elements = elements.filter(e => e.id !== elementId)
  setStorage(STORAGE_KEYS.WORLD_ELEMENTS, elements)
  return true
}

// ==================== SERIES METHODS ====================

export function getSeriesList() {
  const series = getStorage(STORAGE_KEYS.SERIES) || []
  return series.map(s => ({
    ...s,
    project_count: (s.project_ids || []).length
  }))
}

export function createSeries(name, description = '') {
  const series = getStorage(STORAGE_KEYS.SERIES) || []
  
  const newSeries = {
    id: generateId(),
    name,
    description,
    timeline_data: '[]',
    project_ids: [],
    created_at: new Date().toISOString(),
  }
  
  series.push(newSeries)
  setStorage(STORAGE_KEYS.SERIES, series)
  
  return newSeries.id
}

export function getSeries(seriesId) {
  const seriesList = getStorage(STORAGE_KEYS.SERIES) || []
  const series = seriesList.find(s => s.id === seriesId)
  
  if (!series) return null
  
  // Get projects in this series
  const projects = getStorage(STORAGE_KEYS.PROJECTS) || []
  const seriesProjects = projects.filter(p => (series.project_ids || []).includes(p.id))
  
  return {
    ...series,
    projects: seriesProjects
  }
}

export function updateSeries(seriesId, data) {
  const seriesList = getStorage(STORAGE_KEYS.SERIES) || []
  const series = seriesList.find(s => s.id === seriesId)
  
  if (series) {
    if (data.name !== undefined) series.name = data.name
    if (data.description !== undefined) series.description = data.description
    if (data.timeline_data !== undefined) series.timeline_data = data.timeline_data
    setStorage(STORAGE_KEYS.SERIES, seriesList)
    return true
  }
  return false
}

export function deleteSeries(seriesId) {
  let seriesList = getStorage(STORAGE_KEYS.SERIES) || []
  seriesList = seriesList.filter(s => s.id !== seriesId)
  setStorage(STORAGE_KEYS.SERIES, seriesList)
  return true
}

export function addProjectToSeries(seriesId, projectId, bookOrder = null) {
  const seriesList = getStorage(STORAGE_KEYS.SERIES) || []
  const series = seriesList.find(s => s.id === seriesId)
  
  if (series) {
    if (!series.project_ids) series.project_ids = []
    if (!series.project_ids.includes(projectId)) {
      series.project_ids.push(projectId)
    }
    setStorage(STORAGE_KEYS.SERIES, seriesList)
    return true
  }
  return false
}

export function removeProjectFromSeries(seriesId, projectId) {
  const seriesList = getStorage(STORAGE_KEYS.SERIES) || []
  const series = seriesList.find(s => s.id === seriesId)
  
  if (series && series.project_ids) {
    series.project_ids = series.project_ids.filter(id => id !== projectId)
    setStorage(STORAGE_KEYS.SERIES, seriesList)
    return true
  }
  return false
}

export function getSeriesTimeline(seriesId) {
  const series = getSeries(seriesId)
  if (series && series.timeline_data) {
    try {
      return JSON.parse(series.timeline_data)
    } catch {
      return []
    }
  }
  return []
}

export function updateSeriesTimeline(seriesId, timelineData) {
  return updateSeries(seriesId, { timeline_data: JSON.stringify(timelineData) })
}

export function getSeriesCharacters(seriesId) {
  const series = getSeries(seriesId)
  if (!series || !series.projects) return []
  
  const allCharacters = []
  const projects = getStorage(STORAGE_KEYS.PROJECTS) || []
  
  for (const project of series.projects) {
    const projectName = projects.find(p => p.id === project.id)?.name || 'Unknown'
    const chars = getCharacters(project.id)
    chars.forEach(char => {
      allCharacters.push({
        ...char,
        source_project_id: project.id,
        source_project_name: projectName
      })
    })
  }
  
  return allCharacters
}

export function getSeriesWorldElements(seriesId) {
  const series = getSeries(seriesId)
  if (!series || !series.projects) return []
  
  const allElements = []
  const projects = getStorage(STORAGE_KEYS.PROJECTS) || []
  
  for (const project of series.projects) {
    const projectName = projects.find(p => p.id === project.id)?.name || 'Unknown'
    const elements = getWorldElements(project.id, null, null)
    elements.forEach(elem => {
      allElements.push({
        ...elem,
        source_project_id: project.id,
        source_project_name: projectName
      })
    })
  }
  
  return allElements
}

// ==================== SCENE METHODS ====================

export function getScenes(chapterId) {
  const scenes = getStorage(STORAGE_KEYS.SCENES) || []
  return scenes
    .filter(s => s.chapter_id === chapterId)
    .sort((a, b) => (a.scene_order || 0) - (b.scene_order || 0))
}

export function createScene(chapterId, data) {
  const scenes = getStorage(STORAGE_KEYS.SCENES) || []
  
  // Get max order for this chapter
  const chapterScenes = scenes.filter(s => s.chapter_id === chapterId)
  const maxOrder = chapterScenes.length > 0 
    ? Math.max(...chapterScenes.map(s => s.scene_order || 0))
    : 0
  
  const newScene = {
    id: generateId(),
    chapter_id: chapterId,
    scene_order: maxOrder + 1,
    title: data.title || '',
    summary: data.summary || '',
    content: data.content || '',
    pov_character: data.pov_character || '',
    location: data.location || '',
    created_at: new Date().toISOString(),
  }
  
  scenes.push(newScene)
  setStorage(STORAGE_KEYS.SCENES, scenes)
  
  return newScene.id
}

export function updateScene(sceneId, data) {
  const scenes = getStorage(STORAGE_KEYS.SCENES) || []
  const scene = scenes.find(s => s.id === sceneId)
  
  if (scene) {
    Object.assign(scene, data)
    scene.updated_at = new Date().toISOString()
    setStorage(STORAGE_KEYS.SCENES, scenes)
    return true
  }
  return false
}

export function deleteScene(sceneId) {
  let scenes = getStorage(STORAGE_KEYS.SCENES) || []
  scenes = scenes.filter(s => s.id !== sceneId)
  setStorage(STORAGE_KEYS.SCENES, scenes)
  return true
}

export function reorderScenes(chapterId, sceneIds) {
  const scenes = getStorage(STORAGE_KEYS.SCENES) || []
  
  sceneIds.forEach((sceneId, index) => {
    const scene = scenes.find(s => s.id === sceneId && s.chapter_id === chapterId)
    if (scene) {
      scene.scene_order = index + 1
    }
  })
  
  setStorage(STORAGE_KEYS.SCENES, scenes)
  return true
}

// ==================== CSV IMPORT/EXPORT METHODS ====================

export function exportCharactersCsv(projectId) {
  const characters = getCharacters(projectId)
  if (!characters.length) return ''
  
  const headers = ['name', 'role', 'pronouns', 'personality_traits', 'physical_description', 
                   'backstory', 'motivations', 'internal_conflicts', 'strengths', 'weaknesses',
                   'speech_pattern', 'character_arc']
  
  const rows = characters.map(char => 
    headers.map(h => `"${(char[h] || '').replace(/"/g, '""')}"`).join(',')
  )
  
  return [headers.join(','), ...rows].join('\n')
}

export function importCharactersCsv(projectId, csvData) {
  const lines = csvData.trim().split('\n')
  if (lines.length < 2) return { imported: 0, errors: ['No data rows found'] }
  
  const headers = lines[0].split(',').map(h => h.trim().toLowerCase().replace(/"/g, ''))
  const imported = []
  const errors = []
  
  for (let i = 1; i < lines.length; i++) {
    try {
      // Simple CSV parsing (doesn't handle all edge cases)
      const values = lines[i].split(',').map(v => v.trim().replace(/^"|"$/g, '').replace(/""/g, '"'))
      const charData = { project_id: projectId }
      
      headers.forEach((header, index) => {
        charData[header] = values[index] || ''
      })
      
      if (!charData.name) {
        errors.push(`Row ${i + 1}: Missing name`)
        continue
      }
      
      saveCharacter(charData)
      imported.push(charData.name)
    } catch (err) {
      errors.push(`Row ${i + 1}: ${err.message}`)
    }
  }
  
  return { imported: imported.length, errors }
}

export function exportWorldElementsCsv(projectId) {
  const elements = getWorldElements(projectId)
  if (!elements.length) return ''
  
  const headers = ['name', 'element_type', 'description', 'sensory_details', 'significance', 'custom_traits']
  
  const rows = elements.map(elem => 
    headers.map(h => `"${(elem[h] || '').replace(/"/g, '""')}"`).join(',')
  )
  
  return [headers.join(','), ...rows].join('\n')
}

export function importWorldElementsCsv(projectId, csvData) {
  const lines = csvData.trim().split('\n')
  if (lines.length < 2) return { imported: 0, errors: ['No data rows found'] }
  
  const headers = lines[0].split(',').map(h => h.trim().toLowerCase().replace(/"/g, ''))
  const imported = []
  const errors = []
  
  for (let i = 1; i < lines.length; i++) {
    try {
      const values = lines[i].split(',').map(v => v.trim().replace(/^"|"$/g, '').replace(/""/g, '"'))
      const elemData = {}
      
      headers.forEach((header, index) => {
        elemData[header] = values[index] || ''
      })
      
      if (!elemData.name) {
        errors.push(`Row ${i + 1}: Missing name`)
        continue
      }
      
      createWorldElement(projectId, elemData)
      imported.push(elemData.name)
    } catch (err) {
      errors.push(`Row ${i + 1}: ${err.message}`)
    }
  }
  
  return { imported: imported.length, errors }
}

// ==================== TTS METHODS (Stubs for offline mode) ====================

export function ttsListVoices() {
  return ['Browser Speech (Default)']
}

export function ttsReadText(text) {
  // Use browser's built-in speech synthesis as fallback
  if ('speechSynthesis' in window) {
    const utterance = new SpeechSynthesisUtterance(text)
    window.speechSynthesis.speak(utterance)
    return { status: 'playing' }
  }
  return { status: 'unavailable' }
}

export function ttsStop() {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel()
  }
  return { status: 'stopped' }
}

export function ttsIsPlaying() {
  if ('speechSynthesis' in window) {
    return { is_playing: window.speechSynthesis.speaking }
  }
  return { is_playing: false }
}

// ==================== EXPORT ALL AS API OBJECT ====================

const localStorageAdapter = {
  // Projects
  getProjects,
  getProjectsWithChapters,
  createProject,
  deleteProject,
  renameProject,
  getProjectSettings,
  
  // Chapters
  createChapter,
  getChapters,
  getChapterContent,
  updateChapterContent,
  renameChapter,
  deleteChapter,
  moveChapterUp,
  moveChapterDown,
  
  // Characters
  getCharacters,
  getAllCharacters,
  getCharacterDetails,
  saveCharacter,
  deleteCharacter,
  
  // Story Bible
  getStoryBible,
  saveBibleField,
  getBibleField,
  
  // App State
  saveAppState,
  getAppState,
  
  // Context
  getDeepMemory,
  getContextWindow,
  
  // AI (stubs)
  getAiStatus,
  aiStreamStart,
  aiStreamPoll,
  generatePluginResponse,
  askLoreAssistant,
  
  // TTS (browser fallback)
  ttsListVoices,
  ttsReadText,
  ttsStop,
  ttsIsPlaying,
  
  // World Elements
  getWorldElements,
  createWorldElement,
  getWorldElement,
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
  reorderScenes,
  
  // CSV Import/Export
  exportCharactersCsv,
  importCharactersCsv,
  exportWorldElementsCsv,
  importWorldElementsCsv,
}

export default localStorageAdapter

