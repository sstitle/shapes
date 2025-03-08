
import sys
import coloredlogs, logging
import signal
from dataclasses import dataclass, field
from typing import List, Tuple
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt, QPoint

@dataclass
class State:
    points: List[Tuple[int, int]] = field(default_factory=list)

    def reduce(self, action, logger):
        if action['type'] == 'ADD_POINT':
            self.points.append(action['payload'])
            logger.info(f"Point added: {action['payload']}")

class OpenGLWidget(QOpenGLWidget):
    def __init__(self, parent=None, state=None, logger=None):
        super(OpenGLWidget, self).__init__(parent)
        self.state = state
        self.logger = logger

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(event.rect(), QColor(255, 255, 255))
        
        painter.setPen(QColor(0, 0, 0))
        for point in self.state.points:
            painter.drawEllipse(QPoint(*point), 5, 5)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.state.reduce({'type': 'ADD_POINT', 'payload': (event.pos().x(), event.pos().y())}, self.logger)
            self.update()

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
    window = QMainWindow()
    window.setWindowTitle('PyQt6 OpenGL Point Renderer')

    # Create state
    state = State()

    # Create central widget and layout
    centralWidget = OpenGLWidget(window, state=state, logger=logger)
    layout = QVBoxLayout()
    layout.addWidget(centralWidget)

    # Set layout on the central widget
    window.setCentralWidget(centralWidget)
    window.show()

    logger.info("PyQt6 application is running")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
