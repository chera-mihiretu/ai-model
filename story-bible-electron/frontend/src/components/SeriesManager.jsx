/**
 * Series Manager Component
 * ========================
 * Manages series folders with shared story bible across multiple projects.
 */

import { useState, useEffect } from 'react'
import useStore from '../hooks/useStore'
import { usePythonBridge } from '../hooks/usePythonBridge'
import { clsx } from 'clsx'

// Icons
const Icons = {
  SERIES: '📚',
  BOOK: '📖',
  PLUS: '+',
  DELETE: '🗑️',
  EDIT: '✏️',
  FOLDER: '📁',
  CHARACTERS: '👥',
  WORLD: '🌍',
  TIMELINE: '📅',
  DRAG: '⋮⋮',
  LINK: '🔗',
  UNLINK: '❌',
  CHECK: '✅',
  BIBLE: '📜',
}

function SeriesCard({ series, isSelected, onClick, onDelete }) {
  return (
    <div
      className={clsx(
        'p-4 rounded-xl cursor-pointer transition-all duration-200',
        'bg-gradient-to-br from-bg-card/90 to-bg-sidebar/90',
        'border border-glass-border',
        'hover:border-accent-primary hover:shadow-lg hover:shadow-accent-primary/20',
        'hover:-translate-y-1',
        isSelected && 'border-accent-primary ring-2 ring-accent-primary/30'
      )}
      onClick={() => onClick(series)}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-3xl">{Icons.SERIES}</span>
          <div>
            <h3 className="font-semibold text-text-primary">{series.name}</h3>
            <p className="text-xs text-text-muted">
              {series.project_count || 0} book{(series.project_count || 0) !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
        <button
          className="w-7 h-7 flex items-center justify-center rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors text-sm"
          onClick={(e) => {
            e.stopPropagation()
            onDelete(series)
          }}
          title="Delete Series"
        >
          {Icons.DELETE}
        </button>
      </div>
      
      {series.description && (
        <p className="text-sm text-text-secondary line-clamp-2">
          {series.description}
        </p>
      )}
    </div>
  )
}

function ProjectCard({ project, inSeries, onAdd, onRemove, dragHandleProps }) {
  return (
    <div className={clsx(
      'p-3 rounded-lg flex items-center justify-between',
      'bg-bg-hover/50 border border-border/50',
      'transition-all hover:bg-bg-hover'
    )}>
      <div className="flex items-center gap-3">
        {dragHandleProps && (
          <span className="text-text-muted cursor-grab" {...dragHandleProps}>
            {Icons.DRAG}
          </span>
        )}
        <span className="text-xl">{Icons.BOOK}</span>
        <div>
          <h4 className="font-medium text-text-primary text-sm">{project.name}</h4>
          {project.book_order !== undefined && (
            <p className="text-xs text-text-muted">Book #{project.book_order}</p>
          )}
        </div>
      </div>
      
      {inSeries ? (
        <button
          className="btn btn-ghost text-xs py-1 text-red-400 hover:text-red-300"
          onClick={() => onRemove(project)}
        >
          {Icons.UNLINK} Remove
        </button>
      ) : (
        <button
          className="btn btn-ghost text-xs py-1 text-green-400 hover:text-green-300"
          onClick={() => onAdd(project)}
        >
          {Icons.LINK} Add
        </button>
      )}
    </div>
  )
}

function SeriesTimeline({ series, timeline, onUpdate }) {
  const [events, setEvents] = useState(timeline || [])
  const [newEvent, setNewEvent] = useState({ title: '', book: '', description: '' })
  
  const handleAddEvent = () => {
    if (!newEvent.title.trim()) return
    
    const updated = [...events, { ...newEvent, id: Date.now() }]
    setEvents(updated)
    onUpdate(updated)
    setNewEvent({ title: '', book: '', description: '' })
  }
  
  const handleRemoveEvent = (eventId) => {
    const updated = events.filter(e => e.id !== eventId)
    setEvents(updated)
    onUpdate(updated)
  }
  
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2">
        <span>{Icons.TIMELINE}</span>
        <span>Series Timeline</span>
      </h3>
      
      {/* Timeline events */}
      <div className="space-y-2">
        {events.length === 0 ? (
          <p className="text-text-muted text-sm italic">No timeline events yet</p>
        ) : (
          events.map((event, index) => (
            <div
              key={event.id}
              className="flex items-start gap-3 p-3 rounded-lg bg-bg-hover/50 border-l-4 border-accent-primary"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-text-primary">{event.title}</span>
                  {event.book && (
                    <span className="text-xs px-2 py-0.5 rounded bg-accent-primary/20 text-accent-primary">
                      {event.book}
                    </span>
                  )}
                </div>
                {event.description && (
                  <p className="text-sm text-text-muted mt-1">{event.description}</p>
                )}
              </div>
              <button
                className="text-red-400 hover:text-red-300"
                onClick={() => handleRemoveEvent(event.id)}
              >
                {Icons.DELETE}
              </button>
            </div>
          ))
        )}
      </div>
      
      {/* Add event form */}
      <div className="p-3 rounded-lg bg-bg-hover/30 border border-border/50 space-y-2">
        <input
          type="text"
          className="input text-sm"
          placeholder="Event title..."
          value={newEvent.title}
          onChange={(e) => setNewEvent(prev => ({ ...prev, title: e.target.value }))}
        />
        <div className="flex gap-2">
          <input
            type="text"
            className="input text-sm flex-1"
            placeholder="Book (optional)..."
            value={newEvent.book}
            onChange={(e) => setNewEvent(prev => ({ ...prev, book: e.target.value }))}
          />
          <button
            className="btn btn-primary text-sm"
            onClick={handleAddEvent}
            disabled={!newEvent.title.trim()}
          >
            Add Event
          </button>
        </div>
        <textarea
          className="input-textarea text-sm min-h-[60px]"
          placeholder="Description (optional)..."
          value={newEvent.description}
          onChange={(e) => setNewEvent(prev => ({ ...prev, description: e.target.value }))}
        />
      </div>
    </div>
  )
}

function SeriesView({ series, onBack, onProjectSelect }) {
  const { addNotification } = useStore()
  const {
    getProjects,
    getSeries,
    addProjectToSeries,
    removeProjectFromSeries,
    getSeriesTimeline,
    updateSeriesTimeline,
    getSeriesCharacters,
    getSeriesWorldElements,
  } = usePythonBridge()
  
  const [seriesData, setSeriesData] = useState(series)
  const [allProjects, setAllProjects] = useState([])
  const [timeline, setTimeline] = useState([])
  const [characters, setCharacters] = useState([])
  const [worldElements, setWorldElements] = useState([])
  const [activeTab, setActiveTab] = useState('projects') // 'projects' | 'timeline' | 'characters' | 'world'
  
  // Load data
  useEffect(() => {
    async function loadData() {
      const [projects, seriesDetails, timelineData, chars, elements] = await Promise.all([
        getProjects(),
        getSeries(series.id),
        getSeriesTimeline(series.id),
        getSeriesCharacters(series.id),
        getSeriesWorldElements(series.id),
      ])
      
      setAllProjects(projects)
      setSeriesData(seriesDetails || series)
      setTimeline(timelineData || [])
      setCharacters(chars || [])
      setWorldElements(elements || [])
    }
    loadData()
  }, [series.id])
  
  // Get projects in series and not in series
  const seriesProjectIds = (seriesData?.projects || []).map(p => p.id)
  const seriesProjects = seriesData?.projects || []
  const availableProjects = allProjects.filter(p => !seriesProjectIds.includes(p.id))
  
  const handleAddProject = async (project) => {
    const success = await addProjectToSeries(series.id, project.id)
    if (success) {
      const updated = await getSeries(series.id)
      setSeriesData(updated)
      addNotification({ type: 'success', message: `Added "${project.name}" to series` })
    }
  }
  
  const handleRemoveProject = async (project) => {
    const success = await removeProjectFromSeries(series.id, project.id)
    if (success) {
      const updated = await getSeries(series.id)
      setSeriesData(updated)
      addNotification({ type: 'success', message: `Removed "${project.name}" from series` })
    }
  }
  
  const handleTimelineUpdate = async (timelineData) => {
    await updateSeriesTimeline(series.id, timelineData)
    setTimeline(timelineData)
  }
  
  const tabs = [
    { id: 'projects', label: 'Books', icon: Icons.BOOK, count: seriesProjects.length },
    { id: 'timeline', label: 'Timeline', icon: Icons.TIMELINE },
    { id: 'characters', label: 'Characters', icon: Icons.CHARACTERS, count: characters.length },
    { id: 'world', label: 'World', icon: Icons.WORLD, count: worldElements.length },
  ]
  
  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button
          className="btn btn-ghost"
          onClick={onBack}
        >
          ← Back
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            <span>{Icons.SERIES}</span>
            <span>{seriesData?.name || series.name}</span>
          </h1>
          {seriesData?.description && (
            <p className="text-text-muted mt-1">{seriesData.description}</p>
          )}
        </div>
      </div>
      
      {/* Tabs */}
      <div className="flex items-center gap-2 mb-4">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all',
              activeTab === tab.id
                ? 'bg-accent-primary text-white'
                : 'bg-bg-card/60 text-text-muted hover:bg-bg-hover hover:text-text-primary'
            )}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="mr-2">{tab.icon}</span>
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span className="ml-2 text-xs opacity-70">({tab.count})</span>
            )}
          </button>
        ))}
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Projects Tab */}
        {activeTab === 'projects' && (
          <div className="grid grid-cols-2 gap-4">
            {/* Series Projects */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wide">
                In Series ({seriesProjects.length})
              </h3>
              {seriesProjects.length === 0 ? (
                <p className="text-text-muted text-sm italic">No books in this series yet</p>
              ) : (
                seriesProjects.map(project => (
                  <ProjectCard
                    key={project.id}
                    project={project}
                    inSeries={true}
                    onRemove={handleRemoveProject}
                  />
                ))
              )}
            </div>
            
            {/* Available Projects */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wide">
                Available Projects ({availableProjects.length})
              </h3>
              {availableProjects.length === 0 ? (
                <p className="text-text-muted text-sm italic">All projects are in this series</p>
              ) : (
                availableProjects.map(project => (
                  <ProjectCard
                    key={project.id}
                    project={project}
                    inSeries={false}
                    onAdd={handleAddProject}
                  />
                ))
              )}
            </div>
          </div>
        )}
        
        {/* Timeline Tab */}
        {activeTab === 'timeline' && (
          <SeriesTimeline
            series={seriesData}
            timeline={timeline}
            onUpdate={handleTimelineUpdate}
          />
        )}
        
        {/* Characters Tab */}
        {activeTab === 'characters' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2">
              <span>{Icons.CHARACTERS}</span>
              <span>Series Characters ({characters.length})</span>
            </h3>
            
            {characters.length === 0 ? (
              <p className="text-text-muted">No characters in series projects yet</p>
            ) : (
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                {characters.map((char, index) => (
                  <div
                    key={`${char.name}-${index}`}
                    className="p-3 rounded-lg bg-bg-hover/50 border border-border/50"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-text-primary">{char.name}</h4>
                      <span className="text-xs px-2 py-0.5 rounded bg-accent-secondary/20 text-accent-secondary">
                        {char.role || 'Unknown'}
                      </span>
                    </div>
                    {char.source_project_name && (
                      <p className="text-xs text-text-muted">
                        Source: {char.source_project_name}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* World Tab */}
        {activeTab === 'world' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2">
              <span>{Icons.WORLD}</span>
              <span>World Elements ({worldElements.length})</span>
            </h3>
            
            {worldElements.length === 0 ? (
              <p className="text-text-muted">No world elements in series projects yet</p>
            ) : (
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                {worldElements.map((elem, index) => (
                  <div
                    key={`${elem.name}-${index}`}
                    className="p-3 rounded-lg bg-bg-hover/50 border border-border/50"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-text-primary">{elem.name}</h4>
                      <span className="text-xs px-2 py-0.5 rounded bg-accent-primary/20 text-accent-primary">
                        {elem.element_type || 'other'}
                      </span>
                    </div>
                    {elem.source_project_name && (
                      <p className="text-xs text-text-muted">
                        Source: {elem.source_project_name}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function SeriesManager() {
  const { addNotification } = useStore()
  const {
    getSeriesList,
    createSeries,
    deleteSeries,
  } = usePythonBridge()
  
  const [seriesList, setSeriesList] = useState([])
  const [selectedSeries, setSelectedSeries] = useState(null)
  const [isCreating, setIsCreating] = useState(false)
  const [newSeriesName, setNewSeriesName] = useState('')
  const [newSeriesDescription, setNewSeriesDescription] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  
  // Load series list
  useEffect(() => {
    async function loadSeries() {
      setIsLoading(true)
      const list = await getSeriesList()
      setSeriesList(list || [])
      setIsLoading(false)
    }
    loadSeries()
  }, [])
  
  const handleCreateSeries = async () => {
    if (!newSeriesName.trim()) return
    
    const id = await createSeries(newSeriesName, newSeriesDescription)
    if (id) {
      const list = await getSeriesList()
      setSeriesList(list || [])
      setNewSeriesName('')
      setNewSeriesDescription('')
      setIsCreating(false)
      addNotification({ type: 'success', message: `Created series "${newSeriesName}"` })
    }
  }
  
  const handleDeleteSeries = async (series) => {
    if (!confirm(`Delete series "${series.name}"? Projects will not be deleted.`)) return
    
    const success = await deleteSeries(series.id)
    if (success) {
      const list = await getSeriesList()
      setSeriesList(list || [])
      addNotification({ type: 'success', message: `Deleted series "${series.name}"` })
    }
  }
  
  // If viewing a series, show SeriesView
  if (selectedSeries) {
    return (
      <div className="h-full p-6">
        <SeriesView
          series={selectedSeries}
          onBack={() => setSelectedSeries(null)}
        />
      </div>
    )
  }
  
  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary flex items-center gap-2">
            <span>{Icons.SERIES}</span>
            <span>Series</span>
          </h1>
          <p className="text-text-muted mt-1">
            Manage multi-book series with shared story bibles
          </p>
        </div>
        
        <button
          className="btn btn-primary"
          onClick={() => setIsCreating(true)}
        >
          <span>{Icons.PLUS}</span>
          <span>New Series</span>
        </button>
      </div>
      
      {/* Create Series Modal */}
      {isCreating && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="glass-card p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-text-primary mb-4">Create New Series</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  Series Name *
                </label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., The Lord of the Rings"
                  value={newSeriesName}
                  onChange={(e) => setNewSeriesName(e.target.value)}
                  autoFocus
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  Description
                </label>
                <textarea
                  className="input-textarea min-h-[80px]"
                  placeholder="Describe your series..."
                  value={newSeriesDescription}
                  onChange={(e) => setNewSeriesDescription(e.target.value)}
                />
              </div>
            </div>
            
            <div className="flex justify-end gap-3 mt-6">
              <button
                className="btn btn-ghost"
                onClick={() => {
                  setIsCreating(false)
                  setNewSeriesName('')
                  setNewSeriesDescription('')
                }}
              >
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleCreateSeries}
                disabled={!newSeriesName.trim()}
              >
                Create Series
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Series Grid */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="spinner mx-auto mb-4" />
              <p className="text-text-muted">Loading series...</p>
            </div>
          </div>
        ) : seriesList.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md">
              <div className="text-6xl mb-6">{Icons.SERIES}</div>
              <h2 className="text-xl font-semibold text-text-primary mb-2">
                No Series Yet
              </h2>
              <p className="text-text-muted mb-6">
                Create a series folder to manage multiple books with a shared story bible, 
                characters, and world building elements.
              </p>
              <button
                className="btn btn-primary"
                onClick={() => setIsCreating(true)}
              >
                <span>{Icons.PLUS}</span>
                <span>Create Your First Series</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {seriesList.map(series => (
              <SeriesCard
                key={series.id}
                series={series}
                isSelected={selectedSeries?.id === series.id}
                onClick={setSelectedSeries}
                onDelete={handleDeleteSeries}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default SeriesManager

