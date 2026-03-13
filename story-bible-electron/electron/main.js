/**
 * Exelsias - Electron Main Process
 * ================================
 * Manages window lifecycle, spawns Python backend, and handles IPC.
 */

const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

// GPU stability flags - prevent black screen crashes
app.commandLine.appendSwitch('disable-gpu-sandbox');
app.commandLine.appendSwitch('disable-software-rasterizer');
app.commandLine.appendSwitch('disable-gpu-compositing');
app.commandLine.appendSwitch('ignore-gpu-blocklist');

// Keep global reference to window and python process
let mainWindow = null;
let pythonProcess = null;
let pythonReady = false;
let pendingRequests = new Map();
let requestId = 0;


// Determine if we're in development or production
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

/**
 * Get the path to the Python backend executable
 */
function getPythonPath() {
  if (app.isPackaged) {
    // Production: use bundled Python executable
    const platform = process.platform;
    const ext = platform === 'win32' ? '.exe' : '';
    const backendPath = path.join(process.resourcesPath, 'backend', `api_bridge${ext}`);
    console.log('Looking for backend at:', backendPath);
    console.log('Backend exists:', fs.existsSync(backendPath));
    return backendPath;
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
 * Get the path to the project root (for Python imports and data)
 */
function getProjectRoot() {
  if (app.isPackaged) {
    return process.resourcesPath;
  }
  // Development: use the parent of story-bible-electron (where src/ is located)
  return path.join(__dirname, '..', '..');
}

/**
 * Get the data directory path
 */
function getDataPath() {
  // #region agent log
  const fs = require('fs');
  const logData = {sessionId:'7033cc',location:'main.js:getDataPath',message:'Path resolution debug',data:{isPackaged:app.isPackaged,userData:app.getPath('userData'),dirname:__dirname,uid:process.getuid?.(),euid:process.geteuid?.(),env_HOME:process.env.HOME,env_USER:process.env.USER},timestamp:Date.now()};
  try { fs.appendFileSync('/home/chera/Public/my_stuffs/work/fiverr/ricardoo/.cursor/debug-7033cc.log', JSON.stringify(logData) + '\n'); } catch(e) {}
  // #endregion
  if (app.isPackaged) {
    // In production, use user's app data directory for writable data
    return path.join(app.getPath('userData'), 'data');
  }
  return path.join(__dirname, '..', '..', 'data');
}

/**
 * Get the models directory path (for TTS - bundled with app)
 */
function getModelsPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'models');
  }
  return path.join(__dirname, '..', '..', 'models');
}

/**
 * Get the LLM models directory path (user-provided, not bundled)
 */
function getLLMModelsPath() {
  if (app.isPackaged) {
    // LLM models go in user's app data directory
    return path.join(app.getPath('userData'), 'models', 'llama');
  }
  return path.join(__dirname, '..', '..', 'models', 'llama');
}

/**
 * Ensure data directories exist
 */
function ensureDataDirectories() {
  const dataPath = getDataPath();
  const llmModelsPath = getLLMModelsPath();
  const dirs = [
    dataPath,
    path.join(dataPath, 'database'),
    path.join(dataPath, 'voices'),
    path.join(dataPath, 'voices', 'paragraphs'),
    // Ensure LLM models directory exists for user to place their models
    llmModelsPath
  ];
  
  for (const dir of dirs) {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
      console.log('Created directory:', dir);
    }
  }
}

/**
 * Start the Python backend process
 */
function startPythonBackend() {
  return new Promise((resolve, reject) => {
    const pythonPath = getPythonPath();
    const scriptPath = getPythonScript();
    const projectRoot = getProjectRoot();
    const dataPath = getDataPath();
    const modelsPath = getModelsPath();
    const llmModelsPath = getLLMModelsPath();
    
    // Ensure data directories exist
    ensureDataDirectories();
    
    console.log('Starting Python backend...');
    console.log('Python path:', pythonPath);
    console.log('Script path:', scriptPath);
    console.log('Project root:', projectRoot);
    console.log('Data path:', dataPath);
    console.log('TTS Models path:', modelsPath);
    console.log('LLM Models path:', llmModelsPath);
    console.log('Is packaged:', app.isPackaged);
    
    // Check if backend exists
    if (app.isPackaged && !fs.existsSync(pythonPath)) {
      const errorMsg = `Backend executable not found at: ${pythonPath}\n\nPlease make sure the application was installed correctly.`;
      console.error(errorMsg);
      reject(new Error(errorMsg));
      return;
    }
    
    // Set environment variables for Python
    const env = {
      ...process.env,
      PYTHONPATH: projectRoot,
      PYTHONUNBUFFERED: '1',
      // Pass paths to the backend
      EXELSIAS_DATA_PATH: dataPath,
      EXELSIAS_MODELS_PATH: modelsPath,
      EXELSIAS_LLM_MODELS_PATH: llmModelsPath,
      EXELSIAS_PROJECT_ROOT: projectRoot
    };
    
    // Spawn Python process
    const args = scriptPath ? [scriptPath] : [];
    pythonProcess = spawn(pythonPath, args, {
      cwd: app.isPackaged ? path.dirname(pythonPath) : projectRoot,
      env: env,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    // Buffer for accumulating JSON responses (handles multi-line JSON)
    let jsonBuffer = '';
    
    // Handle stdout (JSON-RPC responses)
    pythonProcess.stdout.on('data', (data) => {
      jsonBuffer += data.toString();
      
      // Try to extract complete JSON objects from the buffer
      // JSON-RPC responses are separated by newlines, but the JSON itself may contain newlines
      let startIdx = 0;
      
      while (startIdx < jsonBuffer.length) {
        // Find the start of a JSON object
        const objStart = jsonBuffer.indexOf('{', startIdx);
        if (objStart === -1) {
          // No more JSON objects, clear processed part
          jsonBuffer = '';
          break;
        }
        
        // Try to find a complete JSON object by tracking braces
        let braceCount = 0;
        let inString = false;
        let escapeNext = false;
        let objEnd = -1;
        
        for (let i = objStart; i < jsonBuffer.length; i++) {
          const char = jsonBuffer[i];
          
          if (escapeNext) {
            escapeNext = false;
            continue;
          }
          
          if (char === '\\' && inString) {
            escapeNext = true;
            continue;
          }
          
          if (char === '"' && !escapeNext) {
            inString = !inString;
            continue;
          }
          
          if (!inString) {
            if (char === '{') braceCount++;
            else if (char === '}') {
              braceCount--;
              if (braceCount === 0) {
                objEnd = i;
                break;
              }
            }
          }
        }
        
        if (objEnd === -1) {
          // Incomplete JSON, keep buffer for next data chunk
          jsonBuffer = jsonBuffer.substring(objStart);
          break;
        }
        
        // Extract the complete JSON string
        const jsonStr = jsonBuffer.substring(objStart, objEnd + 1);
        startIdx = objEnd + 1;
        
        try {
          const response = JSON.parse(jsonStr);
          
          // Check for init/ready response
          if (response.id === 'init' && response.result === 'ready') {
            console.log('Python backend ready!');
            pythonReady = true;
            resolve();
            // Continue processing in case there are more responses
            jsonBuffer = jsonBuffer.substring(startIdx);
            startIdx = 0;
            continue;
          }
          
          // Handle normal responses
          if (response.id && pendingRequests.has(response.id)) {
            const { resolve, reject, timeoutHandle } = pendingRequests.get(response.id);
            if (timeoutHandle) clearTimeout(timeoutHandle);
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
          console.error('Failed to parse Python response:', jsonStr.substring(0, 200) + '...');
        }
        
        // Update buffer to remove processed JSON
        jsonBuffer = jsonBuffer.substring(startIdx);
        startIdx = 0;
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
    }, 60000); // 60 seconds for slow machines
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
    
    // Send request to Python
    pythonProcess.stdin.write(JSON.stringify(request) + '\n');
    
    // Timeout for response - longer for AI operations and manuscript parsing
    const isLongOperation = 
      method.includes('generate') || 
      method.includes('ai') || 
      method.includes('stream') || 
      method.includes('lore') || 
      method.includes('assistant') ||
      method.includes('parse') ||      // parse_manuscript
      method.includes('import') ||     // import_manuscript
      method.includes('extract') ||    // character/element extraction
      method.includes('analyze') ||    // text analysis
      method.includes('model') ||      // list_models, select_model (may wait for AI lock)
      method.includes('context') ||    // context_health, scene_context, etc.
      method.includes('series') ||     // series operations
      method.includes('expand');       // expand_scene, expand_scene_from_summary
    
    const timeoutMs = isLongOperation
      ? 600000  // 10 minutes for AI generation and large manuscript processing
      : 60000;  // 60 seconds for regular operations
    
    
    const timeoutHandle = setTimeout(() => {
      if (pendingRequests.has(id)) {
        pendingRequests.delete(id);
        reject(new Error(`Request timeout: ${method}`));
      }
    }, timeoutMs);
    
    // Store timeout handle so we can clear it when response arrives
    pendingRequests.set(id, { resolve, reject, timeoutHandle });
  });
}

/**
 * Get the path to the app icon
 */
function getAppIconPath() {
  if (app.isPackaged) {
    // Production: use bundled icon
    const platform = process.platform;
    const iconName = platform === 'win32' ? 'logo.ico' : 'logo.png';
    return path.join(process.resourcesPath, 'frontend', 'assets', iconName);
  } else {
    // Development: use source icon
    const platform = process.platform;
    const iconName = platform === 'win32' ? 'logo.ico' : 'logo.png';
    return path.join(__dirname, '..', 'frontend', 'public', 'assets', iconName);
  }
}

/**
 * Create the main application window
 */
function createWindow() {
  const iconPath = getAppIconPath();
  console.log('App icon path:', iconPath);
  console.log('Icon exists:', fs.existsSync(iconPath));
  
  mainWindow = new BrowserWindow({
    width: 1600,
    height: 1000,
    minWidth: 1200,
    minHeight: 800,
    backgroundColor: '#0A0A0C',
    titleBarStyle: 'hiddenInset',
    frame: process.platform === 'darwin' ? true : false,
    icon: iconPath,
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
    // DevTools removed from auto-open to save ~200-500MB of RAM.
    // Open manually with Ctrl+Shift+I when needed.
  } else {
    // Production: load from bundled files in resources
    const frontendPath = path.join(process.resourcesPath, 'frontend', 'index.html');
    console.log('Loading frontend from:', frontendPath);
    console.log('Frontend exists:', fs.existsSync(frontendPath));
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
      isDev: isDev,
      dataPath: getDataPath(),
      modelsPath: getModelsPath()
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
    dialog.showErrorBox('Startup Error', `${error.message}\n\nPlease check the logs for more details.`);
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
