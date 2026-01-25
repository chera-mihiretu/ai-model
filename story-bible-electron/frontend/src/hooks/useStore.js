/**
 * Global State Store using Zustand
 * =================================
 * Manages all application state and provides actions for state updates.
 */

import { create } from 'zustand'

export const useStore = create((set, get) => ({
  // ==================== PROJECT STATE ====================
  projects: [],
  currentProjectId: null,
  currentChapterId: null,
  
  setProjects: (projects) => set({ projects }),
  
  setCurrentProject: (projectId) => set({ currentProjectId: projectId }),
  
  setCurrentChapter: (chapterId) => set({ currentChapterId: chapterId }),
  
  // ==================== EDITOR STATE ====================
  editorContent: '',
  isEditorDirty: false,
  wordCount: 0,
  
  setEditorContent: (content) => set({ 
    editorContent: content,
    isEditorDirty: true,
    wordCount: content.trim() ? content.trim().split(/\s+/).length : 0
  }),
  
  markEditorClean: () => set({ isEditorDirty: false }),
  
  // ==================== STORY BIBLE STATE ====================
  storyBibleData: {},
  currentBibleTab: null,
  isBibleExpanded: false,
  
  setStoryBibleData: (data) => set({ storyBibleData: data }),
  
  setCurrentBibleTab: (tab) => set({ currentBibleTab: tab }),
  
  toggleBibleExpanded: () => set((state) => ({ isBibleExpanded: !state.isBibleExpanded })),
  
  updateBibleField: (field, content) => set((state) => ({
    storyBibleData: {
      ...state.storyBibleData,
      [field]: content
    }
  })),
  
  // ==================== CHARACTER STATE ====================
  characters: [],
  selectedCharacterId: null,
  
  setCharacters: (characters) => set({ characters }),
  
  setSelectedCharacter: (characterId) => set({ selectedCharacterId: characterId }),
  
  updateCharacter: (characterId, data) => set((state) => ({
    characters: state.characters.map(c => 
      c.id === characterId ? { ...c, ...data } : c
    )
  })),
  
  addCharacter: (character) => set((state) => ({
    characters: [...state.characters, character]
  })),
  
  removeCharacter: (characterId) => set((state) => ({
    characters: state.characters.filter(c => c.id !== characterId)
  })),
  
  // ==================== AI STATE ====================
  aiStatus: 'loading',
  aiStatusMessage: 'Initializing...',
  isAiGenerating: false,
  aiStreamedText: '',
  
  // Pending AI request from Editor to AssistantPanel
  pendingAiRequest: null, // { type: 'openings' | 'draft' | 'chat', instruction: string, formData: object }
  
  // Editor insertion callback
  editorInsertCallback: null,
  
  setAiStatus: (status, message) => set({ 
    aiStatus: status, 
    aiStatusMessage: message 
  }),
  
  setAiGenerating: (isGenerating) => set({ 
    isAiGenerating: isGenerating,
    aiStreamedText: isGenerating ? '' : get().aiStreamedText
  }),
  
  appendAiToken: (token) => set((state) => ({
    aiStreamedText: state.aiStreamedText + token
  })),
  
  clearAiStream: () => set({ aiStreamedText: '' }),
  
  // Set pending AI request
  setPendingAiRequest: (request) => set({ pendingAiRequest: request }),
  
  // Clear pending AI request
  clearPendingAiRequest: () => set({ pendingAiRequest: null }),
  
  // Set editor insert callback
  setEditorInsertCallback: (callback) => set({ editorInsertCallback: callback }),
  
  // ==================== TTS STATE ====================
  ttsVoices: [],
  selectedVoice: 'Jenny (US Female)',
  isTtsPlaying: false,
  
  setTtsVoices: (voices) => set({ ttsVoices: voices }),
  
  setSelectedVoice: (voice) => set({ selectedVoice: voice }),
  
  setTtsPlaying: (isPlaying) => set({ isTtsPlaying: isPlaying }),
  
  // ==================== UI STATE ====================
  currentView: 'dashboard', // 'dashboard' | 'editor' | 'characters' | 'storyBible'
  sidebarCollapsed: false,
  assistantCollapsed: false,
  showSettings: false,
  storageMode: 'local', // 'local' | 'backend'
  
  setCurrentView: (view) => set({ currentView: view }),
  
  setStorageMode: (mode) => set({ storageMode: mode }),
  
  // When project is cleared, go back to dashboard
  clearCurrentProject: () => set({ 
    currentProjectId: null, 
    currentChapterId: null,
    currentView: 'dashboard',
    characters: [],
    storyBibleData: {},
    editorContent: '',
    isEditorDirty: false,
    wordCount: 0,
  }),
  
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  
  toggleAssistant: () => set((state) => ({ assistantCollapsed: !state.assistantCollapsed })),
  
  setShowSettings: (show) => set({ showSettings: show }),
  
  // ==================== NOTIFICATION STATE ====================
  notifications: [],
  
  addNotification: (notification) => set((state) => ({
    notifications: [...state.notifications, { 
      id: Date.now(), 
      ...notification 
    }]
  })),
  
  removeNotification: (id) => set((state) => ({
    notifications: state.notifications.filter(n => n.id !== id)
  })),
}))

export default useStore

