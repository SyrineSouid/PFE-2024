import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QSizePolicy, QSpacerItem, QGridLayout, QScrollArea, QLineEdit, QComboBox,  
    QFrame)
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QIcon
from PyQt5.QtCore import QRect, QSize, Qt, QTimer
from sensor_simulation import pressure

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tank Level Monitoring System")
        self.setGeometry(250, 250, 300, 230)  # Set initial size
        self.setWindowFlags(Qt.FramelessWindowHint)  # Enlever la barre en haut
        self.setWindowIcon(QIcon('IrWise.png'))
        self.initUI()

    def initUI(self):
        self.layout = QHBoxLayout(self)
        #self.layout = QGridLayout(self)

        """# Create a scroll area to hold tank widgets
        self.scroll_area = QWidget()
        self.scroll_area_layout = QGridLayout(self.scroll_area)
        self.scroll_area.setLayout(self.scroll_area_layout)"""

        # Create and add multiple tank widgets
        self.tank_widgets = []
        for i in range(4):  # Adjusted to fit 2x2 grid
            tank_widget = CylinderWidget(tank_name=f"Tank {i + 1}", channel=i)
            #•self.scroll_area_layout.addWidget(tank_widget, i // 2, i % 2)  # Positioning in the grid
            self.layout.addWidget(tank_widget)  # Positioning in the grid
            self.layout.setSpacing(0)
            self.tank_widgets.append(tank_widget)

        """# Create a scroll area and add the scroll area to the main layout
        self.scroll = QScrollArea()
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.scroll_area)
        self.layout.addWidget(self.scroll)
        self.setLayout(self.layout)"""


class CylinderWidget(QWidget):
    def __init__(self,tank_name,channel):
        super().__init__()
        self.tank_level = 0.0  # Initial tank level (percentage)
        self.tank_name = tank_name  # Tank name
        self.setWindowTitle(tank_name)
        self.liquid_type = "Essence Sans Plomb"  # Default liquid type
        self.density = 0.74  # Default density
        self.radius = 1.0  # Default radius
        self.pressure = 0.0  # Initial pressure
        self.height = 3.0 # Tank Height
        self.channel = channel  # Sensor channel for this tank
        self.initUI()

        # Set up a timer to update the pressure periodically
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updatePressure)
        self.timer.start(3000)  # Update every 3 seconds

    def initUI(self):
        self.layout = QVBoxLayout(self)

        self.tank_display = TankDisplayWidget(self)
        self.layout.addWidget(self.tank_display)
        
        self.info_layout = QVBoxLayout()
        self.layout.setSpacing(0)  # Reduced spacing between elements within the tank widget
        self.layout.setContentsMargins(0,0,0,0)  # Reduced margins within the tank widget

        self.volume_label = QLabel("Volume: 0.0 m³")
        self.info_layout.addWidget(self.volume_label,alignment=Qt.AlignCenter)
        self.level_label = QLabel("Level: 0.0 %")
        self.info_layout.addWidget(self.level_label,alignment=Qt.AlignCenter)
        
        self.layout.addLayout(self.info_layout)
        self.setLayout(self.layout)

        self.button_layout = QHBoxLayout()

        self.parameter_btn = QPushButton("Configure")
        self.parameter_btn.setStyleSheet("background-color: #C2DDE4; color: #040C24;")
        self.parameter_btn.setStyleSheet("font-size: 12px;padding: 2px; color: #111212")
        self.parameter_btn.setIcon(QIcon('parameter.png'))
        self.parameter_btn.setIconSize(QSize(20, 20))
        self.parameter_btn.setFixedSize(90, 30)
        self.parameter_btn.clicked.connect(self.showSettings)
        self.button_layout.addWidget(self.parameter_btn, alignment=Qt.AlignCenter)

        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

    def updatePressure(self):
        # Fetch pressure from the sensor based on the sensor number
        self.pressure = pressure(self.channel)
        self.updateCalculations()
        self.updateLabelColors()
        
    
    def updateLabelColors(self):
        if 0 <= self.tank_level < 0.26:
            color = "#BA1301"
        elif 0.25 <= self.tank_level < 0.51:
            color = "#E4670B"
        elif 0.5 <= self.tank_level < 0.76:
            color = "#EBA104"
        elif 0.75 <= self.tank_level <= 1.0:
            color = "#94C816"
        
        self.volume_label.setStyleSheet(f"font-size: 12px;color: {color}")
        self.level_label.setStyleSheet(f"font-size: 12px;color: {color}")

    def showSettings(self):
        self.settings_widget = SettingsWidget(self)
        self.settings_widget.show()

    def setTankLevel(self, level):
        self.tank_level = level
        self.tank_display.update()  # Trigger repaint

    def updateCalculations(self):
        # Perform calculations based on current pressure, density, and radius
        g = 9.81  # Acceleration due to gravity in m/s^2
        height = self.pressure / (self.density * g)  # Calculate the height of the liquid column
        area = 3.14159 * (self.radius ** 2)  # Calculate the area of the tank base
        tank_volume = area * self.height  # Assuming tank height is 3 meters
        volume = area * height  # Calculate the volume of the liquid
        if volume >= 0 and volume <= tank_volume:
            self.tank_level = volume / tank_volume  # Update tank level as a percentage
            self.volume = volume  # Update volume
            self.tank_display.update()  # Trigger repaint
            self.volume_label.setText(f"Volume: {self.volume:.2f} m³")
            self.level_label.setText(f"Level: {self.tank_level * 100:.2f} %")
            self.tank_display.update()  # Trigger repaint
        else:
            pass
        

class TankDisplayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cylinder_widget = parent
        self.setMinimumSize(130, 230)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Set background color to blue
        painter.setBrush(QColor(4, 12, 36))
        painter.drawRect(2, 0, self.width()+130, self.height())

        # Set color of the tank
        tank_color = QColor(165, 165, 165)  # Light gray color
        painter.setBrush(tank_color)
        pen = QPen(tank_color, 2)
        painter.setPen(pen)

        # Draw tank shape
        tank_width = 60
        tank_height = 100
        tank_x = ((self.width() - tank_width) // 2)-25
        tank_y = (self.height() - tank_height) // 2

        # Fill top ellipse
        painter.drawEllipse(QRect(int(tank_x), int(tank_y), int(tank_width), int(tank_width // 2)))

        # Fill bottom ellipse
        painter.drawEllipse(QRect(int(tank_x), int(tank_y + tank_height - tank_width // 2), int(tank_width), int(tank_width // 2)))

        # Draw curved sides
        painter.drawRect(int(tank_x), int(tank_y + tank_width // 4), int(tank_width), int(tank_height - tank_width // 2))

        # Define colors for different level ranges
        colors = {
            (0, 25): QColor("#94C816"),   # Green
            (25, 50): QColor("#EBA104"),  # Yellow
            (50, 75): QColor("#E4670B"),  # Orange
            (75, 100): QColor("#BA1301")  # Red
        }

        # Draw tank level indicator line with different colors based on tank level percentage
        level_x = tank_x + tank_width + 20
        level_height = tank_height

        for (start, end), color in colors.items():
            line_color = color
            start_y = tank_y + tank_height * start / 100
            end_y = tank_y + tank_height * end / 100
            painter.setPen(QPen(line_color, 8))
            painter.drawLine(int(level_x), int(start_y), int(level_x), int(end_y))  # Vertical line

        # Draw tank level indicator
        level_indicator_height = 5  # Height of the indicator rectangle
        level_indicator_width = 20  # Width of the indicator rectangle
        level_indicator_y = int(tank_y + tank_height * (1 - self.cylinder_widget.tank_level))
        level_indicator_x = int(tank_x + tank_width + 10)  # Adjust the position of the indicator
        if 0 <= self.cylinder_widget.tank_level < 0.26:
            painter.setPen(QColor("#BA1301"))
            painter.setBrush(QColor("#BA1301"))
        elif 0.25 <= self.cylinder_widget.tank_level < 0.51:
            painter.setPen(QColor("#E4670B"))
            painter.setBrush(QColor("#E4670B"))
        elif 0.5 <= self.cylinder_widget.tank_level < 0.76:
            painter.setPen(QColor("#EBA104"))
            painter.setBrush(QColor("#EBA104"))
        elif 0.75 <= self.cylinder_widget.tank_level <= 1.0:
            painter.setPen(QColor("#94C816"))
            painter.setBrush(QColor("#94C816"))

        painter.drawRect(level_indicator_x, level_indicator_y - level_indicator_height // 2, level_indicator_width, level_indicator_height)  # Draw the indicator rectangle

        # Draw tank level labels
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.setPen(QPen(QColor(194, 221, 228), 8))
        painter.drawText(level_x + 3, tank_y + tank_height + 25, "0%")  # 0% label
        painter.drawText(level_x + 3, tank_y - 13, "100%")  # 100% label

        # Draw tank name
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.drawText(tank_x + 23, tank_y + tank_height + 40, self.cylinder_widget.tank_name)

        # Draw liquid type
        font = QFont("Arial", 9)
        painter.setFont(font)
        if self.cylinder_widget.liquid_type == "Essence Sans Plomb":
            painter.drawText(tank_x-4, tank_y + tank_height + 60, self.cylinder_widget.liquid_type)
        elif self.cylinder_widget.liquid_type == "GPL":
            painter.drawText(tank_x + 30, tank_y + tank_height + 60, self.cylinder_widget.liquid_type)
        elif self.cylinder_widget.liquid_type == "Gasoil 50":
            painter.drawText(tank_x+20, tank_y + tank_height + 60, self.cylinder_widget.liquid_type)
        else:
            painter.drawText(tank_x, tank_y + tank_height + 60, self.cylinder_widget.liquid_type)

        # Draw tank level
        font = QFont("Arial", 9)
        painter.setFont(font)
        if 0 <= self.cylinder_widget.tank_level < 0.26:
            painter.setPen(QColor("#BA1301"))
            painter.setBrush(QColor("#BA1301"))
            if self.cylinder_widget.tank_level == 0:
                painter.drawText(tank_x-3, tank_y + tank_height -140, f"Tank Level={int(self.cylinder_widget.tank_level * 100)}%")
                painter.drawText(tank_x-3, tank_y + tank_height -120, f"EMPTY TANK")

            else:
                painter.drawText(tank_x -3, tank_y + tank_height -140, f"Tank Level={int(self.cylinder_widget.tank_level * 100)}%")
                painter.drawText(tank_x -3, tank_y + tank_height -120, f"CRITICAL")

        elif 0.25 <= self.cylinder_widget.tank_level < 0.51:
            painter.setPen(QColor("#E4670B"))
            painter.setBrush(QColor("#E4670B"))
            painter.drawText(tank_x -3, tank_y + tank_height -140, f"Tank Level={int(self.cylinder_widget.tank_level * 100)}%")
            painter.drawText(tank_x -3, tank_y + tank_height -120, f"MODERATE")

        elif 0.5 <= self.cylinder_widget.tank_level < 0.76:
            painter.setPen(QColor("#EBA104"))
            painter.setBrush(QColor("#EBA104"))
            painter.drawText(tank_x -3, tank_y + tank_height - 140, f"Tank Level={int(self.cylinder_widget.tank_level * 100)}%")
            painter.drawText(tank_x -3, tank_y + tank_height -120, f"GOOD")

        elif 0.75 <= self.cylinder_widget.tank_level <= 1.0:
            painter.setPen(QColor("#94C816"))
            painter.setBrush(QColor("#94C816"))
            if self.cylinder_widget.tank_level == 1:
                painter.drawText(tank_x-3, tank_y + tank_height-140, f"Tank Level={int(self.cylinder_widget.tank_level * 100)}%")
                painter.drawText(tank_x -3, tank_y + tank_height -120, f"FULL TANK")

            else:
                painter.drawText(tank_x-3, tank_y + tank_height-140, f"Tank Level={int(self.cylinder_widget.tank_level * 100)}%")
                painter.drawText(tank_x -3, tank_y + tank_height -120, f"HIGH")

        
        painter.drawText(level_x + 15, level_indicator_y - level_indicator_height // 2, f"{int(self.cylinder_widget.tank_level * 100)}%")

        # Draw tank level indicator shape
        tank_fill_height = tank_height * self.cylinder_widget.tank_level  # Calculate the height of the filled area
        tank_fill_y = tank_y + tank_height - tank_fill_height  # Calculate the y-coordinate of the filled area


        if self.cylinder_widget.tank_level <= 0.29 and self.cylinder_widget.tank_level > 0.19:  # If the tank level is between 20% and 30%
            # Calculate the height and width of the bottom ellipse
            bottom_ellipse_height = tank_height * self.cylinder_widget.tank_level * 1.2  # Adjusting the factor (1.2) to fit visually
            # Draw the bottom ellipse for the filled area
            painter.drawEllipse(QRect(int(tank_x), int(tank_y + tank_height - bottom_ellipse_height), int(tank_width), int(bottom_ellipse_height)))

        elif self.cylinder_widget.tank_level <= 0.19 and self.cylinder_widget.tank_level> 0:  # If the tank level is 19% or less
            if self.cylinder_widget.tank_level>0.09 and self.cylinder_widget.tank_level<=0.19:
                bottom_ellipse_height = tank_height * self.cylinder_widget.tank_level * 1.2  # Adjusting the factor (1.2) to fit visually
                bottom_ellipse_width = tank_width * 3 / 4  # Adjusting the factor to fit visually
            elif self.cylinder_widget.tank_level>0.02 and self.cylinder_widget.tank_level<=0.09:
                bottom_ellipse_height = tank_height * self.cylinder_widget.tank_level * 1.2   # Adjusting the factor (1.2) to fit visually
                bottom_ellipse_width = tank_width * 0.4  # Adjusting the factor to fit visually
            elif self.cylinder_widget.tank_level>0 and self.cylinder_widget.tank_level<=0.02:
                bottom_ellipse_height = tank_height * self.cylinder_widget.tank_level * 1.2   # Adjusting the factor (1.2) to fit visually
                bottom_ellipse_width = tank_width * 0.3  # Adjusting the factor to fit visually
            # Draw the bottom ellipse for the filled area
            painter.drawEllipse(QRect(int(tank_x + (tank_width - bottom_ellipse_width) / 2), int(tank_y + tank_height - bottom_ellipse_height), int(bottom_ellipse_width), int(bottom_ellipse_height)))
        
        elif self.cylinder_widget.tank_level == 0:
            pass   
            
        else:
            # Draw the top ellipse of the filled area
            painter.drawEllipse(QRect(int(tank_x), int(tank_fill_y), int(tank_width), int(tank_width // 2)))

            # Limit the filled area to the lower edge of the bottom ellipse
            bottom_ellipse_bottom_y = tank_y + tank_height  # Y-coordinate of the bottom edge of the bottom ellipse
            if tank_fill_y + tank_fill_height > bottom_ellipse_bottom_y:
                tank_fill_height = bottom_ellipse_bottom_y - tank_fill_y

            # Draw the bottom ellipse of the filled area
            painter.drawEllipse(QRect(int(tank_x), int(tank_fill_y + tank_fill_height - tank_width // 2), int(tank_width), int(tank_width // 2)))

            # Draw the curved sides of the filled area
            painter.drawRect(int(tank_x), int(tank_fill_y + tank_width // 4), int(tank_width), int(tank_fill_height - tank_width // 2))


class SettingsWidget(QWidget):

    def __init__(self, parent_widget):
        super().__init__()
        self.cylinder_widget = parent_widget  # Store the parent widget (CylinderWidget)
        self.setWindowTitle("Settings")
        #self.setStyleSheet("background-color: #a5a5a5")
        self.setWindowIcon(QIcon('IrWise.png')) 
        self.setGeometry(275, 275, 260, 120)
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.name_input.setText(str(self.cylinder_widget.tank_name))
        self.layout.addSpacing(10)
        self.layout.addWidget(self.createLabel("Tank Name"))
        self.name_input.setStyleSheet("color: #000000; font-size: 10pt; font-family: Arial, sans-serif;")
        self.layout.addWidget(self.name_input)

        self.density_input = QComboBox()
        self.density_input.addItem("Essence Sans Plomb", 0.74)
        self.density_input.addItem("Gasoil (Diesel)", 0.85)
        self.density_input.addItem("Gasoil 50", 0.85)
        self.density_input.addItem("GPL", 0.51)
        self.setDensityValue(self.cylinder_widget.density)  # Set initial selection
        self.layout.addSpacing(10)
        self.layout.addWidget(self.createLabel("Select Liquid Type"))
        self.density_input.setStyleSheet("color: #000000; font-size: 10pt; font-family: Arial, sans-serif;")
        self.layout.addWidget(self.density_input)

        self.radius_input = QLineEdit()
        self.radius_input.setText(str(self.cylinder_widget.radius))
        self.layout.addSpacing(10)
        self.layout.addWidget(self.createLabel("Tank Radius (m)"))
        self.radius_input.setStyleSheet("color: #000000; font-size: 10pt; font-family: Arial, sans-serif;")
        self.layout.addWidget(self.radius_input)

        self.height_input = QLineEdit()
        self.height_input.setText(str(self.cylinder_widget.height))
        self.layout.addSpacing(10)
        self.layout.addWidget(self.createLabel("Tank Height (m)"))
        self.height_input.setStyleSheet("color: #000000; font-size: 10pt; font-family: Arial, sans-serif;")
        self.layout.addWidget(self.height_input)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.saveSettings)
        self.layout.addWidget(self.save_button)

        self.setLayout(self.layout)

    def createLabel(self, text):
        label = QLabel(text)
        label.setStyleSheet("color: #000000; font-size: 11pt; font-family: Arial, sans-serif;")
        return label
        
    def setDensityValue(self, density):
        # Set the current index of the QComboBox based on density value
        index = self.density_input.findData(density)
        if index != -1:
            self.density_input.setCurrentIndex(index)
        self.setLayout(self.layout)

    def saveSettings(self):
        self.cylinder_widget.liquid_type = self.density_input.currentText()
        self.cylinder_widget.tank_name= self.name_input.text()
        self.cylinder_widget.density = float(self.density_input.currentData())
        self.cylinder_widget.radius = float(self.radius_input.text())
        self.cylinder_widget.height = float(self.height_input.text())
        self.cylinder_widget.pressure = pressure(self.cylinder_widget.channel)
        self.cylinder_widget.updateCalculations()
        self.close()

    def updateSettings(self):
        try:
            self.cylinder_widget.liquid_type = self.density_input.currentText()
            self.cylinder_widget.tank_name=self.name_input.text()
            self.cylinder_widget.pressure = pressure(self.cylinder_widget.channel)
            self.cylinder_widget.density = float(self.density_input.text())
            self.cylinder_widget.radius = float(self.radius_input.text())
            self.cylinder_widget.updateCalculations()
        except ValueError:
            pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 