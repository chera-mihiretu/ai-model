/**
 * Story Bible Pro - Preload Script
 * =================================
 * Exposes safe APIs to the renderer process via contextBridge.
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('api', {
  // ==================== PYTHON BACKEND API ====================

  // Generic Python call
  call: (method, params) => ipcRenderer.invoke('python-call', method, params),

  // ==================== PROJECT METHODS ====================

  getProjects: () => ipcRenderer.invoke('python-call', 'get_projects'),
  getProjectsWithChapters: () => ipcRenderer.invoke('python-call', 'get_projects_with_chapters'),
  createProject: (name, genre) => ipcRenderer.invoke('python-call', 'create_project', { name, genre }),
  deleteProject: (projectId) => ipcRenderer.invoke('python-call', 'delete_project', { project_id: projectId }),
  renameProject: (projectId, newName) => ipcRenderer.invoke('python-call', 'rename_project', { project_id: projectId, new_name: newName }),
  getProjectSettings: (projectId) => ipcRenderer.invoke('python-call', 'get_project_settings', { project_id: projectId }),

  // ==================== RECYCLE BIN METHODS ====================

  moveProjectToRecycleBin: (projectId) => ipcRenderer.invoke('python-call', 'move_project_to_recycle_bin', { project_id: projectId }),
  moveToRecycleBin: (itemType, itemId, itemData) => ipcRenderer.invoke('python-call', 'move_to_recycle_bin', { item_type: itemType, item_id: itemId, item_data: itemData }),
  getRecycleBinItems: () => ipcRenderer.invoke('python-call', 'get_recycle_bin_items'),
  restoreFromRecycleBin: (recycleId) => ipcRenderer.invoke('python-call', 'restore_from_recycle_bin', { recycle_id: recycleId }),
  permanentDeleteFromRecycleBin: (recycleId) => ipcRenderer.invoke('python-call', 'permanent_delete_from_recycle_bin', { recycle_id: recycleId }),
  emptyRecycleBin: () => ipcRenderer.invoke('python-call', 'empty_recycle_bin'),
  getFullProjectData: (projectId) => ipcRenderer.invoke('python-call', 'get_full_project_data', { project_id: projectId }),

  // ==================== CHAPTER METHODS ====================

  createChapter: (projectId, title, content) => ipcRenderer.invoke('python-call', 'create_chapter', { project_id: projectId, title, content }),
  getChapters: (projectId) => ipcRenderer.invoke('python-call', 'get_chapters', { project_id: projectId }),
  getChapterContent: (chapterId) => ipcRenderer.invoke('python-call', 'get_chapter_content', { chapter_id: chapterId }),
  updateChapterContent: (chapterId, content) => ipcRenderer.invoke('python-call', 'update_chapter_content', { chapter_id: chapterId, content }),
  renameChapter: (chapterId, newTitle) => ipcRenderer.invoke('python-call', 'rename_chapter', { chapter_id: chapterId, new_title: newTitle }),
  deleteChapter: (chapterId) => ipcRenderer.invoke('python-call', 'delete_chapter', { chapter_id: chapterId }),
  moveChapterUp: (chapterId) => ipcRenderer.invoke('python-call', 'move_chapter_up', { chapter_id: chapterId }),
  moveChapterDown: (chapterId) => ipcRenderer.invoke('python-call', 'move_chapter_down', { chapter_id: chapterId }),

  // ==================== CHARACTER METHODS ====================

  getCharacters: (projectId) => ipcRenderer.invoke('python-call', 'get_characters', { project_id: projectId }),
  getAllCharacters: (projectId) => ipcRenderer.invoke('python-call', 'get_all_characters', { project_id: projectId }),
  getCharacterDetails: (name, projectId) => ipcRenderer.invoke('python-call', 'get_character_details', { name, project_id: projectId }),
  saveCharacter: (data) => ipcRenderer.invoke('python-call', 'save_character', { data }),
  deleteCharacter: (characterId) => ipcRenderer.invoke('python-call', 'delete_character', { character_id: characterId }),

  // ==================== STORY BIBLE METHODS ====================

  getStoryBible: (projectId) => ipcRenderer.invoke('python-call', 'get_story_bible', { project_id: projectId }),
  saveBibleField: (projectId, fieldName, content) => ipcRenderer.invoke('python-call', 'save_bible_field', { project_id: projectId, field_name: fieldName, content }),
  getBibleField: (projectId, fieldName) => ipcRenderer.invoke('python-call', 'get_bible_field', { project_id: projectId, field_name: fieldName }),

  // ==================== APP STATE METHODS ====================

  saveAppState: (key, value) => ipcRenderer.invoke('python-call', 'save_app_state', { key, value }),
  getAppState: (key) => ipcRenderer.invoke('python-call', 'get_app_state', { key }),

  // ==================== CONTEXT METHODS ====================

  getContextWindow: (projectId, chapterId, charLimit) => ipcRenderer.invoke('python-call', 'get_context_window', { project_id: projectId, chapter_id: chapterId, char_limit: charLimit }),
  getDeepMemory: (projectId, query) => ipcRenderer.invoke('python-call', 'get_deep_memory', { project_id: projectId, query }),
  getSummarizedMemory: (projectId, tokenTier) => ipcRenderer.invoke('python-call', 'get_summarized_memory', { project_id: projectId, token_tier: tokenTier }),
  getContextHealth: (projectId) => ipcRenderer.invoke('python-call', 'get_context_health', { project_id: projectId }),

  // ==================== AI METHODS ====================

  getAiStatus: () => ipcRenderer.invoke('python-call', 'get_ai_status'),
  getAiConfig: () => ipcRenderer.invoke('python-call', 'get_ai_config'),
  listModels: () => ipcRenderer.invoke('python-call', 'list_models'),
  selectModel: (modelPath) => ipcRenderer.invoke('python-call', 'select_model', { model_path: modelPath }),
  copyModelToDirectory: (sourcePath) => ipcRenderer.invoke('python-call', 'copy_model_to_directory', { source_path: sourcePath }),

  aiStreamStart: (instruction, options) => ipcRenderer.invoke('python-call', 'ai_stream_start', {
    instruction,
    bible_data: options?.bibleData,
    current_text: options?.currentText,
    character_context: options?.characterContext,
    rag_context: options?.ragContext,
    style: options?.style,
    long_form: options?.longForm
  }),

  aiStreamPoll: () => ipcRenderer.invoke('python-call', 'ai_stream_poll'),
  aiStreamStop: () => ipcRenderer.invoke('python-call', 'ai_stream_stop'),

  generateSummary: (text, mode) => ipcRenderer.invoke('python-call', 'generate_summary', { text, mode }),

  expandScene: (contextText) => ipcRenderer.invoke('python-call', 'expand_scene', { context_text: contextText }),

  generatePluginResponse: (text, pluginType, contextData) => ipcRenderer.invoke('python-call', 'generate_plugin_response', { text, plugin_type: pluginType, context_data: contextData }),

  askLoreAssistant: (query, projectMemory, projectName, structuredContext) => ipcRenderer.invoke('python-call', 'ask_lore_assistant', { query, project_memory: projectMemory, project_name: projectName, structured_context: structuredContext }),
  loreStreamStart: (query, projectMemory, projectName, structuredContext) => ipcRenderer.invoke('python-call', 'lore_stream_start', { query, project_memory: projectMemory, project_name: projectName, structured_context: structuredContext }),

  getGenreContext: (genre) => ipcRenderer.invoke('python-call', 'get_genre_context', { genre }),

  generateBeatsFromProse: (proseText) => ipcRenderer.invoke('python-call', 'generate_beats_from_prose', { prose_text: proseText }),

  suggestNextBeats: (prevBeats, lorePackage) => ipcRenderer.invoke('python-call', 'suggest_next_beats', { prev_beats: prevBeats, lore_package: lorePackage }),

  // ==================== WORLD ELEMENTS METHODS ====================

  createWorldElement: (projectId, data) => ipcRenderer.invoke('python-call', 'create_world_element', {
    project_id: projectId,
    name: data.name,
    element_type: data.element_type,
    description: data.description,
    sensory_details: data.sensory_details,
    significance: data.significance,
    custom_traits: data.custom_traits,
    series_id: data.series_id
  }),
  getWorldElements: (projectId, seriesId, elementType) => ipcRenderer.invoke('python-call', 'get_world_elements', {
    project_id: projectId,
    series_id: seriesId,
    element_type: elementType
  }),
  getWorldElement: (elementId) => ipcRenderer.invoke('python-call', 'get_world_element', { element_id: elementId }),
  updateWorldElement: (elementId, data) => ipcRenderer.invoke('python-call', 'update_world_element', { element_id: elementId, data }),
  deleteWorldElement: (elementId) => ipcRenderer.invoke('python-call', 'delete_world_element', { element_id: elementId }),

  // ==================== SERIES METHODS ====================

  createSeries: (name, description) => ipcRenderer.invoke('python-call', 'create_series', { name, description }),
  getSeriesList: () => ipcRenderer.invoke('python-call', 'get_series_list'),
  getSeries: (seriesId) => ipcRenderer.invoke('python-call', 'get_series', { series_id: seriesId }),
  updateSeries: (seriesId, data) => ipcRenderer.invoke('python-call', 'update_series', {
    series_id: seriesId,
    name: data.name,
    description: data.description,
    timeline_data: data.timeline_data
  }),
  deleteSeries: (seriesId) => ipcRenderer.invoke('python-call', 'delete_series', { series_id: seriesId }),
  addProjectToSeries: (seriesId, projectId, bookOrder) => ipcRenderer.invoke('python-call', 'add_project_to_series', {
    series_id: seriesId,
    project_id: projectId,
    book_order: bookOrder
  }),
  removeProjectFromSeries: (seriesId, projectId) => ipcRenderer.invoke('python-call', 'remove_project_from_series', {
    series_id: seriesId,
    project_id: projectId
  }),
  getSeriesBible: (seriesId) => ipcRenderer.invoke('python-call', 'get_series_bible', { series_id: seriesId }),
  getSeriesCharacters: (seriesId) => ipcRenderer.invoke('python-call', 'get_series_characters', { series_id: seriesId }),
  getSeriesWorldElements: (seriesId) => ipcRenderer.invoke('python-call', 'get_series_world_elements', { series_id: seriesId }),
  getSeriesTimeline: (seriesId) => ipcRenderer.invoke('python-call', 'get_series_timeline', { series_id: seriesId }),
  updateSeriesTimeline: (seriesId, timelineData) => ipcRenderer.invoke('python-call', 'update_series_timeline', {
    series_id: seriesId,
    timeline_data: timelineData
  }),

  // ==================== SCENE METHODS ====================

  createScene: (chapterId, data) => ipcRenderer.invoke('python-call', 'create_scene', {
    chapter_id: chapterId,
    title: data.title,
    summary: data.summary,
    pov_character: data.pov_character,
    location: data.location
  }),
  getScenes: (chapterId) => ipcRenderer.invoke('python-call', 'get_scenes', { chapter_id: chapterId }),
  updateScene: (sceneId, data) => ipcRenderer.invoke('python-call', 'update_scene', { scene_id: sceneId, data }),
  deleteScene: (sceneId) => ipcRenderer.invoke('python-call', 'delete_scene', { scene_id: sceneId }),
  reorderScenes: (chapterId, sceneIds) => ipcRenderer.invoke('python-call', 'reorder_scenes', {
    chapter_id: chapterId,
    scene_ids: sceneIds
  }),
  getSceneContext: (chapterId) => ipcRenderer.invoke('python-call', 'get_scene_context', { chapter_id: chapterId }),
  getProjectSeriesId: (projectId) => ipcRenderer.invoke('python-call', 'get_project_series_id', { project_id: projectId }),
  getSeriesContextForProject: (projectId) => ipcRenderer.invoke('python-call', 'get_series_context_for_project', { project_id: projectId }),

  // ==================== CHARACTER VERSION METHODS ====================

  createCharacterVersion: (characterId, projectId, versionNotes, traitOverrides) => ipcRenderer.invoke('python-call', 'create_character_version', {
    character_id: characterId,
    project_id: projectId,
    version_notes: versionNotes,
    trait_overrides: traitOverrides
  }),
  getCharacterVersions: (characterId) => ipcRenderer.invoke('python-call', 'get_character_versions', { character_id: characterId }),
  setCanonicalVersion: (versionId, characterId) => ipcRenderer.invoke('python-call', 'set_canonical_version', {
    version_id: versionId,
    character_id: characterId
  }),
  deleteCharacterVersion: (versionId) => ipcRenderer.invoke('python-call', 'delete_character_version', { version_id: versionId }),

  // ==================== CHAPTER OUTLINE LINKING METHODS ====================

  linkChapterToOutline: (chapterId, outlineSection, outlineOrder) => ipcRenderer.invoke('python-call', 'link_chapter_to_outline', {
    chapter_id: chapterId,
    outline_section: outlineSection,
    outline_order: outlineOrder
  }),
  getChapterOutlineLinks: (projectId) => ipcRenderer.invoke('python-call', 'get_chapter_outline_links', { project_id: projectId }),
  unlinkChapterFromOutline: (chapterId) => ipcRenderer.invoke('python-call', 'unlink_chapter_from_outline', { chapter_id: chapterId }),
  getChapterSummary: (chapterId) => ipcRenderer.invoke('python-call', 'get_chapter_summary', { chapter_id: chapterId }),
  saveChapterSummary: (chapterId, summary, recentSummary) => ipcRenderer.invoke('python-call', 'save_chapter_summary', {
    chapter_id: chapterId,
    summary,
    recent_summary: recentSummary
  }),

  // ==================== CSV IMPORT/EXPORT METHODS ====================

  exportCharactersCsv: (projectId) => ipcRenderer.invoke('python-call', 'export_characters_csv', { project_id: projectId }),
  importCharactersCsv: (projectId, csvData) => ipcRenderer.invoke('python-call', 'import_characters_csv', {
    project_id: projectId,
    csv_data: csvData
  }),
  exportWorldElementsCsv: (projectId) => ipcRenderer.invoke('python-call', 'export_world_elements_csv', { project_id: projectId }),
  importWorldElementsCsv: (projectId, csvData) => ipcRenderer.invoke('python-call', 'import_world_elements_csv', {
    project_id: projectId,
    csv_data: csvData
  }),

  // ==================== IMPORT NOVEL METHODS ====================

  parseManuscript: (content, extractAll) => ipcRenderer.invoke('python-call', 'parse_manuscript', {
    content,
    extract_all: extractAll
  }),
  detectChapters: (content) => ipcRenderer.invoke('python-call', 'detect_chapters', { content }),
  extractSynopsis: (content) => ipcRenderer.invoke('python-call', 'extract_synopsis', { content }),
  extractCharacters: (content) => ipcRenderer.invoke('python-call', 'extract_characters', { content }),
  extractWorldElements: (content) => ipcRenderer.invoke('python-call', 'extract_world_elements', { content }),
  detectGenreStyle: (content) => ipcRenderer.invoke('python-call', 'detect_genre_style', { content }),
  importManuscriptToProject: (content, projectName, extractAll) => ipcRenderer.invoke('python-call', 'import_manuscript_to_project', {
    content,
    project_name: projectName,
    extract_all: extractAll
  }),

  // ==================== AI GENERATION FROM SYNOPSIS METHODS ====================

  generateCharactersFromSynopsis: (synopsis, genre) => ipcRenderer.invoke('python-call', 'generate_characters_from_synopsis', {
    synopsis,
    genre
  }),
  generateSingleCharacter: (description, genre) => ipcRenderer.invoke('python-call', 'generate_single_character', {
    description,
    genre
  }),
  generateSingleWorldElement: (description, elementType, genre) => ipcRenderer.invoke('python-call', 'generate_single_world_element', {
    description,
    element_type: elementType,
    genre
  }),
  generateWorldFromSynopsis: (synopsis, genre) => ipcRenderer.invoke('python-call', 'generate_world_from_synopsis', {
    synopsis,
    genre
  }),
  generateSynopsis: (storyElements, genre, targetWords) => ipcRenderer.invoke('python-call', 'generate_synopsis', {
    story_elements: storyElements,
    genre,
    target_words: targetWords
  }),
  generateOutlineFromSynopsis: (synopsis, chapterCount, genre) => ipcRenderer.invoke('python-call', 'generate_outline_from_synopsis', {
    synopsis,
    chapter_count: chapterCount,
    genre
  }),
  updateChapterSummaryAi: (chapterContent) => ipcRenderer.invoke('python-call', 'update_chapter_summary_ai', {
    chapter_content: chapterContent
  }),
  expandSceneFromSummary: (sceneSummary, context, genre) => ipcRenderer.invoke('python-call', 'expand_scene_from_summary', {
    scene_summary: sceneSummary,
    context,
    genre
  }),

  // ==================== TTS METHODS ====================

  ttsListVoices: () => ipcRenderer.invoke('python-call', 'tts_list_voices'),
  ttsReadText: (text, voice, characterName) => ipcRenderer.invoke('python-call', 'tts_read_text', { text, voice, character_name: characterName }),
  ttsStop: () => ipcRenderer.invoke('python-call', 'tts_stop'),
  ttsGenerateMp3: (text, voice, outputPath) => ipcRenderer.invoke('python-call', 'tts_generate_mp3', { text, voice, output_path: outputPath }),
  ttsGetDownloadProgress: () => ipcRenderer.invoke('python-call', 'tts_get_download_progress'),
  ttsIsPlaying: () => ipcRenderer.invoke('python-call', 'tts_is_playing'),

  // ==================== EVENT LISTENERS ====================

  onAiToken: (callback) => {
    const listener = (event, token) => callback(token);
    ipcRenderer.on('ai-token', listener);
    return () => ipcRenderer.removeListener('ai-token', listener);
  },

  // ==================== DIALOG METHODS ====================

  openFileDialog: (options) => ipcRenderer.invoke('dialog-open-file', options),
  saveFileDialog: (options) => ipcRenderer.invoke('dialog-save-file', options),

  // ==================== APP INFO ====================

  getAppInfo: () => ipcRenderer.invoke('get-app-info'),

  // ==================== WINDOW CONTROLS ====================

  windowMinimize: () => ipcRenderer.send('window-minimize'),
  windowMaximize: () => ipcRenderer.send('window-maximize'),
  windowClose: () => ipcRenderer.send('window-close')
});

console.log('Preload script loaded');

