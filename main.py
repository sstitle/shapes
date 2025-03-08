
import sys
import coloredlogs, logging
import signal
from dataclasses import dataclass, field
from typing import List, Tuple
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint

@dataclass
class State:
    lines: List[Tuple[Tuple[int, int], Tuple[int, int]]] = field(default_factory=lambda: [((50, 100), (250, 100)), ((50, 200), (250, 200))])
    selected_point: Tuple[int, int] = None

    def reduce(self, action, logger):
        if action['type'] == 'SELECT_POINT':
            self.selected_point = action['payload']
            logger.info(f"Point selected: {action['payload']}")
        elif action['type'] == 'MOVE_POINT' and self.selected_point is not None:
            line_index, point_index = self.selected_point
            line = self.lines[line_index]
            new_point = action['payload']
            if point_index == 0:
                self.lines[line_index] = (new_point, line[1])
            else:
                self.lines[line_index] = (line[0], new_point)
            logger.info(f"Point moved to: {new_point}")

class OpenGLWidget(QOpenGLWidget):
    def __init__(self, parent=None, state=None, logger=None):
        super(OpenGLWidget, self).__init__(parent)
        self.state = state
        self.logger = logger
        self.dragging = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(event.rect(), QColor(255, 255, 255))
        
        bluePen = QPen(QColor(0, 0, 255))
        bluePen.setWidth(3)
        for line in self.state.lines:
            painter.setPen(bluePen)
            painter.drawLine(QPoint(*line[0]), QPoint(*line[1]))
            
            # Draw anchor points with black outline
            painter.setBrush(QColor(255, 0, 0))  # Set color for anchor points
            painter.setPen(QColor(0, 0, 0))  # Set outline color to black
            painter.drawEllipse(QPoint(*line[0]), 5, 5)
            painter.drawEllipse(QPoint(*line[1]), 5, 5)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            for i, line in enumerate(self.state.lines):
                for j, point in enumerate(line):
                    if (QPoint(*point) - event.pos()).manhattanLength() < 10:
                        self.state.reduce({'type': 'SELECT_POINT', 'payload': (i, j)}, self.logger)
                        self.dragging = True
                        break

    def mouseMoveEvent(self, event):
        if self.dragging and self.state.selected_point is not None:
            self.state.reduce({'type': 'MOVE_POINT', 'payload': (event.pos().x(), event.pos().y())}, self.logger)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.state.selected_point = None

def handle_sigint(signal, frame):
    print("SIGINT received, exiting gracefully...")
    QApplication.quit()

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
    window.setWindowTitle('PyQt6 OpenGL Line Renderer')

    # Get screen size and set window size to 2/3 of screen size
    screen = app.primaryScreen()
    screen_size = screen.size()
    window_width = int(screen_size.width() * 2 / 3)
    window_height = int(screen_size.height() * 2 / 3)
    window.resize(window_width, window_height)

    # Center the window
    window.move((screen_size.width() - window_width) // 2, (screen_size.height() - window_height) // 2)

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
