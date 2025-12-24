import sys
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    
    # Instantiate and show the main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
