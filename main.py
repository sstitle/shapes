
import sys
import coloredlogs, logging
import signal
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
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
            # logger.info(f"Point selected: {action['payload']}")
        elif action['type'] == 'MOVE_POINT' and self.selected_point is not None:
            line_index, point_index = self.selected_point
            line = self.lines[line_index]
            new_point = action['payload']
            if point_index == 0:
                self.lines[line_index] = (new_point, line[1])
            else:
                self.lines[line_index] = (line[0], new_point)
            # logger.info(f"Point moved to: {new_point}")

def do_lines_intersect(line1: Tuple[Tuple[int, int], Tuple[int, int]], line2: Tuple[Tuple[int, int], Tuple[int, int]]) -> Optional[Tuple[int, int]]:
    """Check if two line segments intersect and return the intersection point if they do."""
    def ccw(A, B, C):
        # Check if the points A, B, C are listed in a counterclockwise order
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    A, B = line1
    C, D = line2
    # Lines intersect if the points A, B are on different sides of line CD and points C, D are on different sides of line AB
    if ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D):
        # Calculate intersection point
        def line(p1, p2):
            A = (p1[1] - p2[1])
            B = (p2[0] - p1[0])
            C = (p1[0] * p2[1] - p2[0] * p1[1])
            return A, B, -C

        L1 = line(A, B)
        L2 = line(C, D)

        D = L1[0] * L2[1] - L1[1] * L2[0]
        Dx = L1[2] * L2[1] - L1[1] * L2[2]
        Dy = L1[0] * L2[2] - L1[2] * L2[0]
        if D != 0:
            x = Dx / D
            y = Dy / D
            return int(x), int(y)
    return None

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
        
        intersection_point = None
        if len(self.state.lines) >= 2:
            intersection_point = do_lines_intersect(self.state.lines[0], self.state.lines[1])

        pen_color = QColor(255, 0, 0) if intersection_point else QColor(0, 0, 255)
        for line in self.state.lines:
            pen = QPen(pen_color)
            pen.setWidth(5)  # Set thicker pen width
            painter.setPen(pen)
            painter.drawLine(QPoint(*line[0]), QPoint(*line[1]))
            
            # Draw anchor points with black outline
            painter.setBrush(QColor(255, 0, 0))  # Set color for anchor points
            painter.setPen(QColor(0, 0, 0))  # Set outline color to black
            painter.drawEllipse(QPoint(*line[0]), 5, 5)
            painter.drawEllipse(QPoint(*line[1]), 5, 5)

        if intersection_point:
            painter.setBrush(QColor(255, 255, 0))  # Yellow for intersection point
            painter.drawEllipse(QPoint(*intersection_point), 5, 5)

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
