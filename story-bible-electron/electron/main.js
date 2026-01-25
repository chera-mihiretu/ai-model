/**
 * Story Bible Pro - Electron Main Process
 * ========================================
 * Manages window lifecycle, spawns Python backend, and handles IPC.
 */

const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

// Keep global reference to window and python process
let mainWindow = null;
let pythonProcess = null;
let pythonReady = false;
let pendingRequests = new Map();
let requestId = 0;

// Determine if we're in development or production
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

/**
 * Get the path to the Python backend
 */
function getPythonPath() {
  if (app.isPackaged) {
    // Production: use bundled Python executable
    const platform = process.platform;
    const ext = platform === 'win32' ? '.exe' : '';
    return path.join(process.resourcesPath, 'backend', `api_bridge${ext}`);
  } else {
    // Development: use system Python
    return process.platform === 'win32' ? 'python' : 'python3';
  }
}

/**
 * Get the path to the Python script (dev only)
 */
function getPythonScript() {
  if (app.isPackaged) {
    return null; // Script is bundled into executable
  }
  return path.join(__dirname, '..', 'backend', 'api_bridge.py');
}

/**
 * Get the path to the project root (for Python imports)
 */
function getProjectRoot() {
  if (app.isPackaged) {
    return process.resourcesPath;
  }
  // Development: use the parent of story-bible-electron (where src/ is located)
  return path.join(__dirname, '..', '..');
}

/**
 * Start the Python backend process
 */
function startPythonBackend() {
  return new Promise((resolve, reject) => {
    const pythonPath = getPythonPath();
    const scriptPath = getPythonScript();
    const projectRoot = getProjectRoot();
    
    console.log('Starting Python backend...');
    console.log('Python path:', pythonPath);
    console.log('Script path:', scriptPath);
    console.log('Project root:', projectRoot);
    
    // Set environment variables for Python
    const env = {
      ...process.env,
      PYTHONPATH: projectRoot,
      PYTHONUNBUFFERED: '1'
    };
    
    // Spawn Python process
    const args = scriptPath ? [scriptPath] : [];
    pythonProcess = spawn(pythonPath, args, {
      cwd: projectRoot,
      env: env,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    // Handle stdout (JSON-RPC responses)
    pythonProcess.stdout.on('data', (data) => {
      const lines = data.toString().split('\n');
      for (const line of lines) {
        if (!line.trim()) continue;
        
        try {
          const response = JSON.parse(line);
          
          // Check for init/ready response
          if (response.id === 'init' && response.result === 'ready') {
            console.log('Python backend ready!');
            pythonReady = true;
            resolve();
            return;
          }
          
          // Handle normal responses
          if (response.id && pendingRequests.has(response.id)) {
            const { resolve, reject } = pendingRequests.get(response.id);
            pendingRequests.delete(response.id);
            
            if (response.error) {
              reject(new Error(response.error.message));
            } else {
              resolve(response.result);
            }
          }
          
          // Handle streaming AI tokens
          if (response.type === 'ai_token' && mainWindow) {
            mainWindow.webContents.send('ai-token', response.token);
          }
        } catch (e) {
          console.error('Failed to parse Python response:', line);
        }
      }
    });
    
    // Handle stderr (logs)
    pythonProcess.stderr.on('data', (data) => {
      console.log('Python:', data.toString());
    });
    
    // Handle process exit
    pythonProcess.on('close', (code) => {
      console.log(`Python process exited with code ${code}`);
      pythonProcess = null;
      pythonReady = false;
      
      // Reject all pending requests
      for (const [id, { reject }] of pendingRequests) {
        reject(new Error('Python process exited'));
      }
      pendingRequests.clear();
    });
    
    pythonProcess.on('error', (err) => {
      console.error('Failed to start Python process:', err);
      reject(err);
    });
    
    // Timeout for startup
    setTimeout(() => {
      if (!pythonReady) {
        reject(new Error('Python backend startup timeout'));
      }
    }, 30000);
  });
}

/**
 * Send a request to the Python backend
 */
function sendToPython(method, params = {}) {
  return new Promise((resolve, reject) => {
    if (!pythonProcess || !pythonReady) {
      reject(new Error('Python backend not ready'));
      return;
    }
    
    const id = ++requestId;
    const request = {
      jsonrpc: '2.0',
      method: method,
      params: params,
      id: id
    };
    
    pendingRequests.set(id, { resolve, reject });
    
    // Send request to Python
    pythonProcess.stdin.write(JSON.stringify(request) + '\n');
    
    // Timeout for response - longer for AI operations
    const timeoutMs = method.includes('generate') || method.includes('ai') || method.includes('stream') 
      || method.includes('lore') || method.includes('assistant')
      ? 300000  // 5 minutes for AI generation
      : 60000;  // 60 seconds for regular operations
    
    setTimeout(() => {
      if (pendingRequests.has(id)) {
        pendingRequests.delete(id);
        reject(new Error(`Request timeout: ${method}`));
      }
    }, timeoutMs);
  });
}

/**
 * Create the main application window
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1600,
    height: 1000,
    minWidth: 1200,
    minHeight: 800,
    backgroundColor: '#0A0A0C',
    titleBarStyle: 'hiddenInset',
    frame: process.platform === 'darwin' ? true : false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });
  
  // Load the frontend
  if (isDev) {
    // Development: load from Vite dev server
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    // Production: load from bundled files in resources
    const frontendPath = path.join(process.resourcesPath, 'frontend', 'index.html');
    console.log('Loading frontend from:', frontendPath);
    mainWindow.loadFile(frontendPath);
  }
  
  // Handle window close
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * Setup IPC handlers for renderer communication
 */
function setupIPC() {
  // Generic Python API call
  ipcMain.handle('python-call', async (event, method, params) => {
    try {
      return await sendToPython(method, params);
    } catch (error) {
      console.error(`Python call failed: ${method}`, error);
      throw error;
    }
  });
  
  // File dialogs
  ipcMain.handle('dialog-open-file', async (event, options) => {
    const result = await dialog.showOpenDialog(mainWindow, options);
    return result;
  });
  
  ipcMain.handle('dialog-save-file', async (event, options) => {
    const result = await dialog.showSaveDialog(mainWindow, options);
    return result;
  });
  
  // App info
  ipcMain.handle('get-app-info', () => {
    return {
      version: app.getVersion(),
      platform: process.platform,
      isDev: isDev
    };
  });
  
  // Window controls
  ipcMain.on('window-minimize', () => mainWindow?.minimize());
  ipcMain.on('window-maximize', () => {
    if (mainWindow?.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow?.maximize();
    }
  });
  ipcMain.on('window-close', () => mainWindow?.close());
}

/**
 * App lifecycle handlers
 */
app.whenReady().then(async () => {
  try {
    // Start Python backend first
    await startPythonBackend();
    
    // Setup IPC handlers
    setupIPC();
    
    // Create window
    createWindow();
    
    // macOS: re-create window when dock icon clicked
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
      }
    });
  } catch (error) {
    console.error('Failed to start application:', error);
    dialog.showErrorBox('Startup Error', error.message);
    app.quit();
  }
});

// Quit when all windows closed (except on macOS)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Cleanup on quit
app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
});

