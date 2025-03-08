
import sys
import coloredlogs, logging
import signal
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout

def handle_sigint(signal, frame):
    print("SIGINT received, exiting gracefully...")
    sys.exit(0)

def main():
    # Set up logging
    logger = logging.getLogger(__name__)
    coloredlogs.install(level='DEBUG', logger=logger)
    logger.info("Starting PyQt6 application")

    # Set up SIGINT handler
    signal.signal(signal.SIGINT, handle_sigint)

    # Set up PyQt6 application
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle('PyQt6 Hello World')

    # Create central widget and layout
    centralWidget = QWidget(window)
    layout = QVBoxLayout(centralWidget)
    
    # Add label to layout
    helloMsg = QLabel('<h1>Hello, World with PyQt6!</h1>')
    layout.addWidget(helloMsg)

    # Set layout on the central widget
    centralWidget.setLayout(layout)
    centralWidget.show()

    window.show()

    logger.info("PyQt6 application is running")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
