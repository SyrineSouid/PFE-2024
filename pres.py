from decimal import Decimal
import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QSizePolicy, QSpacerItem, QGridLayout, QScrollArea, QLineEdit, QComboBox,  
    QFrame)
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QIcon
from PyQt5.QtCore import QRect, QSize, Qt, QTimer
from sensors import Pressure # type: ignore
import boto3

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='eu-west-3')  

# Define the table
table = dynamodb.Table('Tanks')

# Créez les objets Pressure pour chaque tank
tank1 = Pressure(channel=0, values=list(range(10, 40)))
tank2 = Pressure(channel=1) 
tank3 = Pressure(channel=2) 
tank4 = Pressure(channel=3) 

# Utiliser une liste pour contenir les objets Pressure
pressure_objects = [tank1, tank2, tank3, tank4]

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tank Level Monitoring System")
        self.setGeometry(0, 0, 700, 350)  # Set initial size
        # self.setWindowFlags(Qt.FramelessWindowHint)  # Enlever la barre en haut
        self.setWindowIcon(QIcon('IrWise.png'))
        self.initUI()

    def initUI(self):
        self.layout = QHBoxLayout(self)
 
        # Create and add multiple tank widgets
        self.tank_widgets = []
        for i , pressure_obj in enumerate(pressure_objects):  # Adjusted to fit 2x2 grid
            #pressure_obj = Pressure(channel=i)  # Ici, on crée un objet Pressure avec un channel différent pour chaque réservoir
            tank_widget = CylinderWidget(tank_name=f"Tank {i + 1}", pressure_obj=pressure_obj)

            #•self.scroll_area_layout.addWidget(tank_widget, i // 2, i % 2)  # Positioning in the grid
            self.layout.addWidget(tank_widget)  # Positioning in the grid
            self.layout.setSpacing(0)
            self.tank_widgets.append(tank_widget)


class CylinderWidget(QWidget):
    def __init__(self,tank_name, pressure_obj):
        super().__init__()
        self.tank_level = 0.0  # Initial tank level (percentage)
        self.tank_name = tank_name  # Tank name
        self.setWindowTitle(tank_name)
        self.liquid_type = "Essence Sans Plomb"  # Default liquid type
        self.density = 0.74  # Default density
        self.radius = 1.0  # Default radius
        self.pressure = 0.0  # Initial pressure
        self.pressure_obj = pressure_obj
        self.height = 3.0 # Tank Height
        self.index=0 # Initialize index for cycling through values
        self.values = self.pressure_obj.get_value()  # Récupère les valeurs de pression
        print(f"Pressure Values: {self.values}")
        self.pressure=self.pressure_obj.get_value()
        self.initUI()

        # Set up a timer to update the pressure periodically
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updatePressure)
        self.timer.start(10000)  # Update every 10 seconds

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

    def update_pressure(self):
        # Récupère la valeur de pression du capteur
        pressure = self.pressure_obj.get_value()
        print(f"Pressure: {pressure}")
        
        if pressure != "no sensor connected" and pressure is not None:
            return pressure
        else:
            # En cas d'absence de données valides, affichez un message d'erreur
            self.volume_label.setText("No sensor connected")
            self.level_label.setText("Level: - %")
            return None

    def updatePressure(self):
        # Mettre à jour la pression depuis le capteur
        new_pressure = self.pressure_obj.get_value()
        print(f"New Pressure: {new_pressure}")
        # Vérifier si la nouvelle pression est valide
        if new_pressure != "no sensor connected":
            self.pressure = new_pressure
            self.updateCalculations()
            self.updateLabelColors()
            self.tank_display.update()
        else:
            # Si aucun capteur n'est connecté, afficher un message d'erreur
            self.volume_label.setText("No sensor connected")
            self.level_label.setText("Level: - %")

        

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
        scaling_factor = 0.5  # Adjust this factor as needed to calibrate

        # Ensure pressure is a single value (not a list)
        if isinstance(self.pressure, list):
            self.pressure = self.pressure[0] if isinstance(self.pressure[0], (int, float)) else None

        print(f"Debug - Current Pressure: {self.pressure}")
    
        if self.pressure is not None:
            try:
                # Apply the scaling factor to reduce the calculated height
                height = (float(self.pressure) / (self.density * g)) * scaling_factor
                print(f"Debug - Calculated Height with Scaling: {height}")
            
                area = 3.14159 * (self.radius ** 2)  # Calculate the area of the tank base
                tank_volume = area * self.height  # Assuming tank height is 3 meters
                volume = area * height  # Calculate the volume of the liquid

                print(f"Debug - Calculated Volume: {volume}, Tank Volume: {tank_volume}")

                if volume >= 0 and volume <= tank_volume:
                    self.tank_level = volume / tank_volume  # Update tank level as a percentage
                    self.volume = volume  # Update volume
                    self.volume_label.setText(f"Volume: {self.volume:.2f} m³")
                    self.level_label.setText(f"Level: {self.tank_level * 100:.2f} %")
                    self.tank_display.update()  # Trigger repaint

                    # Store updated data in DynamoDB
                    self.store_data_in_dynamodb()

                else:
                    print("Debug - Volume is out of expected range.")
            except ValueError:
                print("Error in calculating height.")
        else:
            # Handle the case where pressure is not a number
            self.volume_label.setText("No sensor connected")
            self.level_label.setText("Level: - %")

    def store_data_in_dynamodb(self):
        # Convert float values to Decimal for DynamoDB
        tank_number = self.pressure_obj.channel + 1  # Adjust to ensure Tank#1 is 0001, Tank#2 is 0002, etc.
        sk_value = f"{tank_number:04d}"
        data = {
            "PK": "Tank#1",
            "SK": sk_value,  # Use channel as unique identifier for SK
            "TankNumber": tank_number,
            "Value": Decimal(str(self.pressure)) if self.pressure is not None else Decimal("0.0"),
            "Status": "Connected" if self.pressure is not None else "No Sensor Connected",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),  # Current timestamp in ISO 8601 format
            "Volume": Decimal(str(round(self.volume, 2))) if self.volume is not None else Decimal("0.0"),
            "TankLevelPercentage": Decimal(str(round(self.tank_level * 100, 2))) if self.tank_level is not None else Decimal("0.0")
        }

        # Insert data into DynamoDB
        try:
            response = table.put_item(Item=data)
            print("Data stored successfully:", response)
        except Exception as e:
            print("Error storing data:", e)        

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
        pressure_value = self.cylinder_widget.pressure_obj.get_values()["pressure"]
        self.cylinder_widget.pressure = pressure_value
        self.cylinder_widget.updateCalculations()
        self.close()

    def updateSettings(self):
        try:
            self.cylinder_widget.liquid_type = self.density_input.currentText()
            self.cylinder_widget.tank_name=self.name_input.text()
            pressure_value = self.cylinder_widget.pressure_obj.get_values()["pressure"]
            self.cylinder_widget.pressure = pressure_value
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