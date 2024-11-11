from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtCore import Qt, QPointF, QRectF, QSizeF, QTimer
import math

class OrbitWidget(QWidget):
    def __init__(self, update_callback, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self.semi_major_axis = 100
        self.eccentricity = 0
        self.inclination = 0
        self.drag_point = None
        self.update_callback = update_callback
        self.parent_body_name = "Parent"
        self.planet_name = "Planet"
        self.center_offset = QPointF(0, 0)
        self.is_moving_orbit = False
        self.target_semi_major_axis = self.semi_major_axis
        self.target_eccentricity = self.eccentricity

        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.smooth_update)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self.width() // 2 + self.center_offset.x()
        center_y = self.height() // 2 + self.center_offset.y()
        scale = min(self.width(), self.height()) / (2.2 * self.semi_major_axis)

        a = self.semi_major_axis * scale
        b = a * math.sqrt(1 - self.eccentricity**2)
        c = self.eccentricity * a

        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(-self.inclination)

        # Draw orbit
        painter.drawEllipse(QPointF(-c, 0), a, b)

        # Draw drag points
        painter.setPen(QPen(Qt.GlobalColor.red, 6))
        points = [
            QPointF(a - c, b),  # SE
            QPointF(-a - c, b),  # SW
            QPointF(a - c, -b),  # NE
            QPointF(-a - c, -b),  # NW
        ]
        for point in points:
            painter.drawRect(QRectF(point - QPointF(3, 3), QSizeF(6, 6)))

        # Draw parent body
        painter.setPen(QPen(Qt.GlobalColor.blue, 8))
        painter.drawPoint(QPointF(0, 0))
        painter.drawText(QPointF(5, -5), self.parent_body_name)

        # Draw planet
        planet_x = (a - c) * math.cos(math.radians(self.inclination))
        planet_y = (a - c) * math.sin(math.radians(self.inclination))
        painter.setPen(QPen(Qt.GlobalColor.green, 8))
        painter.drawPoint(QPointF(planet_x, planet_y))
        painter.drawText(QPointF(planet_x + 5, planet_y - 5), self.planet_name)

        painter.restore()

    def mousePressEvent(self, event):
        center_x = self.width() // 2 + self.center_offset.x()
        center_y = self.height() // 2 + self.center_offset.y()
        scale = min(self.width(), self.height()) / (2.2 * self.semi_major_axis)
        a = self.semi_major_axis * scale
        b = a * math.sqrt(1 - self.eccentricity**2)
        c = self.eccentricity * a

        points = [
            ("SE", QPointF(center_x + a - c, center_y + b)),
            ("SW", QPointF(center_x - a - c, center_y + b)),
            ("NE", QPointF(center_x + a - c, center_y - b)),
            ("NW", QPointF(center_x - a - c, center_y - b)),
        ]

        for name, point in points:
            if (event.position() - point).manhattanLength() < 10:
                self.drag_point = name
                return

        # Check if click is inside the orbit (with buffer)
        orbit_center = QPointF(center_x - c, center_y)
        click_pos = event.position() - orbit_center
        normalized_x = click_pos.x() / a
        normalized_y = click_pos.y() / b
        distance_from_center = math.sqrt(normalized_x**2 + normalized_y**2)

        if 0.8 < distance_from_center < 0.95:
            self.is_moving_orbit = True
            self.last_pos = event.position()

    def mouseMoveEvent(self, event):
        if self.drag_point:
            center_x = self.width() // 2 + self.center_offset.x()
            center_y = self.height() // 2 + self.center_offset.y()
            scale = min(self.width(), self.height()) / (2.2 * self.semi_major_axis)

            if scale > 0:
                x = (event.position().x() - center_x) / scale
                y = (event.position().y() - center_y) / scale

                if self.drag_point in ["SE", "NE"]:
                    self.target_semi_major_axis = max(0.01, abs(x) / (1 + self.eccentricity))
                elif self.drag_point in ["SW", "NW"]:
                    self.target_semi_major_axis = max(0.01, abs(x) / (1 - self.eccentricity))

                if self.target_semi_major_axis != 0:
                    self.target_eccentricity = max(0, min(0.99, 1 - (y / self.target_semi_major_axis)**2))

            if not self.update_timer.isActive():
                self.update_timer.start(16)  # 16 ms delay for smoother updates
        elif self.is_moving_orbit:
            delta = event.position() - self.last_pos
            self.center_offset += delta
            self.last_pos = event.position()
            self.update()
            if not self.update_timer.isActive():
                self.update_timer.start(16)

    def mouseReleaseEvent(self, event):
        self.drag_point = None
        self.is_moving_orbit = False

    def smooth_update(self):
        # Smooth transition to target values
        self.semi_major_axis += (self.target_semi_major_axis - self.semi_major_axis) * 0.2
        self.eccentricity += (self.target_eccentricity - self.eccentricity) * 0.2

        self.update()
        if self.update_callback:
            self.update_callback()

        # Continue updating if we haven't reached the target
        if abs(self.semi_major_axis - self.target_semi_major_axis) > 0.01 or abs(self.eccentricity - self.target_eccentricity) > 0.001:
            self.update_timer.start(16)

class VerticalOrbitWidget(QWidget):
    def __init__(self, update_callback, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self.semi_major_axis = 100
        self.eccentricity = 0
        self.inclination = 0
        self.drag_point = None
        self.update_callback = update_callback
        self.parent_body_name = "Parent"
        self.planet_name = "Planet"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw coordinate system
        painter.drawLine(0, self.height() // 2, self.width(), self.height() // 2)
        painter.drawLine(self.width() // 2, 0, self.width() // 2, self.height())

        # Draw orbit
        center_x = self.width() // 2
        center_y = self.height() // 2
        scale = min(self.width(), self.height()) / (2.2 * self.semi_major_axis)

        a = self.semi_major_axis * scale
        b = a * math.sqrt(1 - self.eccentricity**2)

        painter.save()
        painter.translate(center_x, center_y)

        # Draw ellipse
        painter.drawEllipse(QPointF(0, 0), a, b * math.cos(math.radians(self.inclination)))

        # Draw inclination line
        inclination_radians = math.radians(self.inclination)
        inclination_slope = math.tan(inclination_radians)
        painter.setPen(QPen(Qt.GlobalColor.red, 2))
        painter.drawLine(QPointF(-a, 0), QPointF(a, inclination_slope * a))
        
        # Draw drag point for inclination
        painter.setPen(QPen(Qt.GlobalColor.red, 8))
        incl_point = QPointF(a, inclination_slope * a)
        painter.drawRect(QRectF(incl_point - QPointF(4, 4), QSizeF(8, 8)))

        # Draw parent body
        painter.setPen(QPen(Qt.GlobalColor.blue, 8))
        painter.drawPoint(QPointF(0, 0))
        painter.drawText(QPointF(5, -5), self.parent_body_name)

        # Draw planet
        planet_x = a
        planet_y = inclination_slope * a
        painter.setPen(QPen(Qt.GlobalColor.green, 8))
        painter.drawPoint(QPointF(planet_x, planet_y))
        painter.drawText(QPointF(planet_x + 5, planet_y - 5), self.planet_name)

        painter.restore()

    def mousePressEvent(self, event):
        center_x = self.width() // 2
        center_y = self.height() // 2
        scale = min(self.width(), self.height()) / (2.2 * self.semi_major_axis)
        a = self.semi_major_axis * scale
        b = a * math.sqrt(1 - self.eccentricity**2)

        inclination_radians = math.radians(self.inclination)
        inclination_slope = math.tan(inclination_radians)
        incl_point = QPointF(center_x + a, center_y + inclination_slope * a)
        
        if (event.position() - incl_point).manhattanLength() < 10:
            self.drag_point = "incl"
        else:
            self.drag_point = None

    def mouseMoveEvent(self, event):
        if self.drag_point == "incl":
            center_y = self.height() // 2
            scale = min(self.width(), self.height()) / (2.2 * self.semi_major_axis)
            a = self.semi_major_axis * scale
            b = a * math.sqrt(1 - self.eccentricity**2)

            y = (center_y - event.position().y()) / b
            self.inclination = math.degrees(math.asin(max(-1, min(1, y))))

            self.update()
            self.update_callback()

    def mouseReleaseEvent(self, event):
        self.drag_point = None