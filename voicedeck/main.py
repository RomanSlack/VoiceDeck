"""Main entry point for VoiceDeck application."""

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from . import __app_name__, __version__
from .config import AppConfig
from .gui import MainWindow
from .stt.openai_client import create_transcriber, TranscriberError


def main():
    """Application entry point."""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)

    # Load configuration
    config = AppConfig.load()

    # Create transcriber
    try:
        transcriber = create_transcriber(config.stt)
    except TranscriberError as e:
        QMessageBox.critical(
            None,
            "Configuration Error",
            f"Failed to initialize speech-to-text backend:\n\n{e}",
        )
        return 1

    # Create and show main window
    window = MainWindow(config, transcriber)
    window.show()

    # Run application event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
