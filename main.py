import sys
import coloredlogs, logging
import signal
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QTextDocument
from PyQt6.QtCore import Qt, QPoint, QRect

@dataclass
class State:
    lines: List[Tuple[Tuple[int, int], Tuple[int, int]]] = field(default_factory=lambda: [((-100, 0), (100, 0)), ((0, -100), (0, 100))])
    selected_point: Tuple[int, int] = None

    def reduce(self, action, logger):
        if action['type'] == 'SELECT_POINT':
            self.selected_point = action['payload']
        elif action['type'] == 'MOVE_POINT' and self.selected_point is not None:
            line_index, point_index = self.selected_point
            line = self.lines[line_index]
            new_point = action['payload']
            if point_index == 0:
                self.lines[line_index] = (new_point, line[1])
            else:
                self.lines[line_index] = (line[0], new_point)

def do_lines_intersect(line1: Tuple[Tuple[int, int], Tuple[int, int]], line2: Tuple[Tuple[int, int], Tuple[int, int]]) -> Optional[Tuple[int, int]]:
    """Check if two line segments intersect and return the intersection point if they do."""
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    A, B = line1
    C, D = line2
    if ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D):
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
        painter.fillRect(event.rect(), QColor(192, 192, 192))  # Set background to gray

        # Draw x and y axes
        center_x = self.width() // 2
        center_y = self.height() // 2
        axis_pen = QPen(QColor(0, 0, 0))
        axis_pen.setWidth(2)
        painter.setPen(axis_pen)
        painter.drawLine(QPoint(center_x, 0), QPoint(center_x, self.height()))  # y-axis
        painter.drawLine(QPoint(0, center_y), QPoint(self.width(), center_y))  # x-axis

        intersection_point = None
        if len(self.state.lines) >= 2:
            intersection_point = do_lines_intersect(self.state.lines[0], self.state.lines[1])

        pen_color = QColor(255, 0, 0) if intersection_point else QColor(0, 0, 255)
        for line in self.state.lines:
            pen = QPen(pen_color)
            pen.setWidth(5)
            painter.setPen(pen)
            # Adjust points to be centered on the screen
            p1 = QPoint(center_x + line[0][0], center_y - line[0][1])
            p2 = QPoint(center_x + line[1][0], center_y - line[1][1])
            painter.drawLine(p1, p2)
            
            painter.setBrush(QColor(255, 0, 0))
            painter.setPen(QColor(0, 0, 0))
            painter.drawEllipse(p1, 5, 5)
            painter.drawEllipse(p2, 5, 5)

        if intersection_point:
            painter.setBrush(QColor(255, 255, 0))
            intersection_qpoint = QPoint(center_x + intersection_point[0], center_y - intersection_point[1])
            painter.drawEllipse(intersection_qpoint, 5, 5)

        self.drawDataPanel(painter, intersection_point)

    def drawDataPanel(self, painter, intersection_point):
        text_lines = []
        for i, line in enumerate(self.state.lines):
            p1, p2 = line
            A, B, C = self.lineEquation(p1, p2)
            m = -A / B if B != 0 else float('inf')
            b = -C / B if B != 0 else float('inf')
            text_lines.append(f"<b>Line {i+1}:</b> (<span style='color:blue'>{p1[0]}</span>, <span style='color:blue'>{p1[1]}</span>) to (<span style='color:blue'>{p2[0]}</span>, <span style='color:blue'>{p2[1]}</span>)")
            text_lines.append(f"<b>Equation (Standard Form):</b> <span style='color:red'>{A}</span>x + <span style='color:red'>{B}</span>y + <span style='color:red'>{C}</span> = 0")
            text_lines.append(f"<b>Equation (Slope-Intercept Form):</b> y = <span style='color:green'>{round(m, 3)}</span>x + <span style='color:green'>{round(b, 3)}</span>")
            text_lines.append(f"<b>Equation (Two-Point Form):</b> y - <span style='color:blue'>{p1[1]}</span> = <span style='color:green'>{round(m, 3)}</span>(x - <span style='color:blue'>{p1[0]}</span>)")

        if intersection_point:
            x, y = intersection_point
            text_lines.append(f"<b>Intersection:</b> (<span style='color:green'>{round(x, 3)}</span>, <span style='color:green'>{round(y, 3)}</span>)")

        document = QTextDocument()
        document.setHtml("<span style='color:black'>" + "<br>".join(text_lines) + "</span>")
        painter.save()
        # Position the text in the lower left corner
        painter.translate(10, self.height() - document.size().height() - 10)
        document.drawContents(painter)
        painter.restore()

    def lineEquation(self, p1, p2):
        A = p1[1] - p2[1]
        B = p2[0] - p1[0]
        C = p1[0] * p2[1] - p2[0] * p1[1]
        return A, B, C

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            for i, line in enumerate(self.state.lines):
                for j, point in enumerate(line):
                    adjusted_point = QPoint(self.width() // 2 + point[0], self.height() // 2 - point[1])
                    if (adjusted_point - event.pos()).manhattanLength() < 10:
                        self.state.reduce({'type': 'SELECT_POINT', 'payload': (i, j)}, self.logger)
                        self.dragging = True
                        break

    def mouseMoveEvent(self, event):
        if self.dragging and self.state.selected_point is not None:
            new_x = event.pos().x() - self.width() // 2
            new_y = self.height() // 2 - event.pos().y()
            self.state.reduce({'type': 'MOVE_POINT', 'payload': (new_x, new_y)}, self.logger)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.state.selected_point = None

def handle_sigint(signal, frame):
    print("SIGINT received, exiting gracefully...")
    QApplication.quit()

def main():
    logger = logging.getLogger(__name__)
    coloredlogs.install(level='DEBUG', logger=logger)
    logger.info("Starting Line Intersection Visualizer")

    signal.signal(signal.SIGINT, handle_sigint)

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle('Line Intersection Visualizer')

    screen = app.primaryScreen()
    screen_size = screen.size()
    window_width = int(screen_size.width() * 2 / 3)
    window_height = int(screen_size.height() * 2 / 3)
    window.resize(window_width, window_height)

    window.move((screen_size.width() - window_width) // 2, (screen_size.height() - window_height) // 2)

    state = State()

    centralWidget = OpenGLWidget(window, state=state, logger=logger)
    layout = QVBoxLayout()
    layout.addWidget(centralWidget)

    window.setCentralWidget(centralWidget)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
