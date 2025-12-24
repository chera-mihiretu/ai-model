from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QStackedWidget, QLabel, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from src.core.config import config

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.WINDOW_TITLE)
        self.resize(*config.WINDOW_SIZE)
        
        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Setup UI
        self._setup_sidebar()
        self._setup_content_area()
        self._apply_styles()

    def _setup_sidebar(self):
        """Creates the sidebar navigation."""
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(250)
        
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)
        self.sidebar_layout.setSpacing(5)
        
        # Title/Logo Area
        self.app_title = QLabel(config.APP_NAME)
        self.app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.app_title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 20px 0;")
        self.sidebar_layout.addWidget(self.app_title)
        
        # Navigation Buttons
        self.btn_dashboard = self._create_nav_button("Dashboard")
        self.btn_chat = self._create_nav_button("AI Chat")
        self.btn_settings = self._create_nav_button("Settings")
        
        self.sidebar_layout.addWidget(self.btn_dashboard)
        self.sidebar_layout.addWidget(self.btn_chat)
        self.sidebar_layout.addStretch() # Push settings to bottom
        self.sidebar_layout.addWidget(self.btn_settings)
        
        self.main_layout.addWidget(self.sidebar)

    def _create_nav_button(self, text: str) -> QPushButton:
        """Helper to create consistent sidebar buttons."""
        btn = QPushButton(text)
        btn.setObjectName("sidebar_btn")
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.clicked.connect(lambda: self._handle_nav_click(text))
        return btn

    def _setup_content_area(self):
        """Creates the main content stack."""
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("content_area")
        
        # Example Pages
        self.page_dashboard = QLabel("Dashboard View")
        self.page_dashboard.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.page_chat = QLabel("AI Chat Interface")
        self.page_chat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.page_settings = QLabel("Settings View")
        self.page_settings.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.content_stack.addWidget(self.page_dashboard)
        self.content_stack.addWidget(self.page_chat)
        self.content_stack.addWidget(self.page_settings)
        
        self.main_layout.addWidget(self.content_stack)

    def _handle_nav_click(self, page_name: str):
        """Switches the content stack based on selection."""
        if page_name == "Dashboard":
            self.content_stack.setCurrentWidget(self.page_dashboard)
        elif page_name == "AI Chat":
            self.content_stack.setCurrentWidget(self.page_chat)
        elif page_name == "Settings":
            self.content_stack.setCurrentWidget(self.page_settings)

    def _apply_styles(self):
        """Loads and applies QSS."""
        style_path = Path(__file__).parent / "styles" / "dark_theme.qss"
        if style_path.exists():
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())
