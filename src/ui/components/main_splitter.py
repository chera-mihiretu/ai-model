from PyQt6.QtWidgets import QSplitter, QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QSettings, QTimer
# import logging

class MainWorkspaceSplitter(QSplitter):
    """
    Custom 3-panel splitter (Left, Middle, Right) with persistence and premium feel.
    replaces the static QHBoxLayout in the main editor view.
    """
    
    def __init__(self, left_panel: QWidget, middle_panel: QWidget, right_panel: QWidget, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        
        # Add widgets in correct order
        self.addWidget(left_panel)
        self.addWidget(middle_panel)
        self.addWidget(right_panel)
        
        # References for resizing logic
        self.left_panel = left_panel
        self.middle_panel = middle_panel
        self.right_panel = right_panel
        
        # Configure Splitter Properties
        self.setHandleWidth(8)
        self.setChildrenCollapsible(False)  # We handle collapse manually via double-click
        
        # Visual Styling for Handles (done via stylesheet in main app, but defaults here just in case)
        # The handle styling is usually handled by the global stylesheet QSplitter::handle
        
        # Setup specific policies for panels to ensure smooth resizing
        self._setup_panel_policies()
        
        # Load saved sizes
        QTimer.singleShot(0, self._load_sizes) # Defer to ensure geometry is ready-ish
        
        # Debounce saves
        self.splitterMoved.connect(self._on_splitter_moved)
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(500)
        self._save_timer.timeout.connect(self.save_sizes)

    def _setup_panel_policies(self):
        """Configure size policies for proper behavior."""
        # Left: Fixed/Preferred, can shrink but has min width
        self.left_panel.setMinimumWidth(200)
        policy_left = self.left_panel.sizePolicy()
        policy_left.setHorizontalStretch(0) # Priority 0
        self.left_panel.setSizePolicy(policy_left)
        
        # Middle: Expanding, takes available space
        self.middle_panel.setMinimumWidth(400)
        policy_mid = self.middle_panel.sizePolicy()
        policy_mid.setHorizontalPolicy(QSizePolicy.Policy.Expanding)
        policy_mid.setHorizontalStretch(1) # Higher priority to take space
        self.middle_panel.setSizePolicy(policy_mid)
        
        # Right: Preferred, can shrink/grow
        self.right_panel.setMinimumWidth(250)
        policy_right = self.right_panel.sizePolicy()
        policy_right.setHorizontalStretch(0)
        self.right_panel.setSizePolicy(policy_right)
        
        # Set stretch factors on the splitter itself
        # Index 0 (Left): 0
        # Index 1 (Middle): 1 (Stretches most)
        # Index 2 (Right): 0
        self.setStretchFactor(0, 0)
        self.setStretchFactor(1, 1)
        self.setStretchFactor(2, 0)

    def createHandle(self):
        """Return custom handle if needed, or rely on default."""
        return super().createHandle()

    def _on_splitter_moved(self, pos, index):
        """Handle splitter move event."""
        # Trigger delayed save
        self._save_timer.start()

    def _load_sizes(self):
        """Load split sizes from settings."""
        settings = QSettings()
        # "layout/splitter_sizes" is a list of ints
        saved_sizes = settings.value("layout/splitter_sizes")
        
        if saved_sizes:
            try:
                # Convert to int list
                sizes = [int(x) for x in saved_sizes]
                if len(sizes) == 3 and sum(sizes) > 0:
                    self.setSizes(sizes)
                    return
            except Exception as e:
                # logging.warning(f"Failed to load splitter sizes: {e}")
                pass
        
        # Default sizes if no save found
        # We need total width to calculate proportional default if window isn't fully shown yet
        # But setSizes accepts absolute values and normalizes them.
        self.setSizes([300, 800, 350])

    def save_sizes(self):
        """Save current split sizes."""
        sizes = self.sizes()
        if sum(sizes) > 0:
            settings = QSettings()
            # PyQt6 QSettings handles list of ints fine mostly, but casting to explicit list helps
            settings.setValue("layout/splitter_sizes", [int(s) for s in sizes])
            # logging.info(f"Layout saved: {sizes}")

    def mouseDoubleClickEvent(self, event):
        """
        Handle double click on handle to collapse/restore.
        Since we set setChildrenCollapsible(False), we must do this manually.
        """
        # Determine if click was on a handle
        handle_width = self.handleWidth()
        
        # Logic to find which handle was clicked
        # This is tricky in pure Python without accessing `handle(i)`.
        # Easier approach: Iterate handles and check geometry.
        
        clicked_handle_index = -1
        for i in range(self.count() - 1):
            handle = self.handle(i+1) # handle(1) is between widget 0 and 1
            if handle and handle.underMouse():
                clicked_handle_index = i + 1
                break
        
        if clicked_handle_index != -1:
            self._toggle_collapse(clicked_handle_index)
        else:
            super().mouseDoubleClickEvent(event)

    def _toggle_collapse(self, handle_index):
        """
        Toggle collapse state of the adjacent panel.
        Handle 1: Between Left (0) and Middle (1). Double click toggles Left.
        Handle 2: Between Middle (1) and Right (2). Double click toggles Right.
        """
        sizes = self.sizes()
        
        # Define collapse thresholds
        COLLAPSED_THRESHOLD = 50 
        
        if handle_index == 1:
            # Toggle Left Panel (Index 0)
            if sizes[0] < COLLAPSED_THRESHOLD:
                # Restore
                sizes[0] = 300 # Default restore width
            else:
                # Collapse
                sizes[0] = 0
                
        elif handle_index == 2:
            # Toggle Right Panel (Index 2)
            if sizes[2] < COLLAPSED_THRESHOLD:
                # Restore
                sizes[2] = 350
            else:
                # Collapse
                sizes[2] = 0
        
        self.setSizes(sizes)
        self.save_sizes()
