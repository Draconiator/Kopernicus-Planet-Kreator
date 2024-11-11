from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, QTabWidget, QScrollArea, 
                             QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox, QColorDialog,
                             QTextEdit, QGridLayout, QCheckBox, QMessageBox)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt
from orbit_widgets import OrbitWidget, VerticalOrbitWidget
from utility_functions import convert_to_dds
from genconfig import generate_config
from texture_previewer import TexturePreviewContainer
from PIL import Image

import os

class PlanetCreator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KSP Planet Creator")
        self.setGeometry(100, 100, 800, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)

        title = QLabel("KSP Planet Creator")
        title.setFont(title_font)
        main_layout.addWidget(title)

        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Basic Properties Tab
        basic_tab = QWidget()
        basic_layout = QFormLayout()
        basic_tab.setLayout(basic_layout)
        self.tab_widget.addTab(basic_tab, "Basic Properties")

        self.planet_name = QLineEdit()
        basic_layout.addRow("Planet Name:", self.planet_name)

        self.radius = QSpinBox()
        self.radius.setRange(1, 1000000)
        self.radius.setSuffix(" km")
        basic_layout.addRow("Radius:", self.radius)

        self.gravity = QDoubleSpinBox()
        self.gravity.setRange(0, 10)
        self.gravity.setSingleStep(0.01)
        basic_layout.addRow("Surface Gravity (g):", self.gravity)

        # Time Warp Tab
        time_warp_tab = QWidget()
        time_warp_layout = QVBoxLayout()
        time_warp_tab.setLayout(time_warp_layout)
        self.tab_widget.addTab(time_warp_tab, "Time Warp")

        time_warp_input_layout = QGridLayout()
        time_warp_layout.addLayout(time_warp_input_layout)

        self.altitude_input = QSpinBox()
        self.altitude_input.setRange(0, 1000000)
        self.altitude_input.setSuffix(" m")
        time_warp_input_layout.addWidget(QLabel("Altitude:"), 0, 0)
        time_warp_input_layout.addWidget(self.altitude_input, 0, 1)

        self.multiplier_input = QSpinBox()
        self.multiplier_input.setRange(1, 100000)
        self.multiplier_input.setSuffix("x")
        time_warp_input_layout.addWidget(QLabel("Multiplier:"), 1, 0)
        time_warp_input_layout.addWidget(self.multiplier_input, 1, 1)

        self.add_time_warp_button = QPushButton("Add Time Warp Level")
        self.add_time_warp_button.clicked.connect(self.add_time_warp_level)
        time_warp_input_layout.addWidget(self.add_time_warp_button, 2, 0, 1, 2)

        self.time_warp_display = QTextEdit()
        self.time_warp_display.setReadOnly(True)
        time_warp_layout.addWidget(self.time_warp_display)

        # Add rescaling options
        self.enable_rescale = QCheckBox("Enable Rescaling")
        basic_layout.addRow("Enable Rescaling:", self.enable_rescale)

        self.rescale_factor = QDoubleSpinBox()
        self.rescale_factor.setRange(0.1, 10)
        self.rescale_factor.setValue(1)
        self.rescale_factor.setSingleStep(0.1)
        basic_layout.addRow("Rescale Factor:", self.rescale_factor)

        self.time_warp_levels = []

        # Atmosphere Tab
        atmo_tab = QWidget()
        atmo_layout = QFormLayout()
        atmo_tab.setLayout(atmo_layout)
        self.tab_widget.addTab(atmo_tab, "Atmosphere")

        self.atmosphere_height = QSpinBox()
        self.atmosphere_height.setRange(0, 1000000)
        self.atmosphere_height.setSuffix(" m")
        atmo_layout.addRow("Atmosphere Height:", self.atmosphere_height)

        self.atmosphere_temp = QSpinBox()
        self.atmosphere_temp.setRange(-273, 1000)
        self.atmosphere_temp.setSuffix(" °C")
        atmo_layout.addRow("Surface Temperature:", self.atmosphere_temp)

        self.atmo_ambient_color = QPushButton("Set Ambient Color")
        self.atmo_ambient_color.clicked.connect(lambda: self.select_color(self.atmo_ambient_color))
        atmo_layout.addRow("Atmosphere Ambient Color:", self.atmo_ambient_color)

        self.atmo_light_color = QPushButton("Set Light Color")
        self.atmo_light_color.clicked.connect(lambda: self.select_color(self.atmo_light_color))
        atmo_layout.addRow("Atmosphere Light Color:", self.atmo_light_color)

        self.atmo_pressure_curve = QTextEdit()
        self.atmo_pressure_curve.setPlaceholderText("Enter pressure curve keys (e.g., 0 1.01325 0 -0.000136962)")
        atmo_layout.addRow("Pressure Curve:", self.atmo_pressure_curve)

        self.atmo_temp_curve = QTextEdit()
        self.atmo_temp_curve.setPlaceholderText("Enter temperature curve keys (e.g., 0 73.15 0 -0.007975)")
        atmo_layout.addRow("Temperature Curve:", self.atmo_temp_curve)

        self.static_pressure = QDoubleSpinBox()
        self.static_pressure.setRange(0, 10000)
        self.static_pressure.setSingleStep(0.1)
        self.static_pressure.setValue(101.325)  # Default Earth-like pressure
        self.static_pressure.setSuffix(" kPa")
        atmo_layout.addRow("Static Pressure at Sea Level:", self.static_pressure)

        self.has_atmosphere = QComboBox()
        self.has_atmosphere.addItems(["Yes", "No"])
        self.has_atmosphere.currentTextChanged.connect(self.toggle_atmosphere)
        atmo_layout.addRow("Has Atmosphere:", self.has_atmosphere)

        # List of widgets to disable when there's no atmosphere
        self.atmo_widgets = [self.atmosphere_height, self.atmosphere_temp, self.static_pressure,
                             self.atmo_ambient_color, self.atmo_light_color, self.atmo_pressure_curve,
                             self.atmo_temp_curve]

        # Orbit Tab
        orbit_tab = QWidget()
        orbit_layout = QVBoxLayout()
        orbit_tab.setLayout(orbit_layout)
        self.tab_widget.addTab(orbit_tab, "Orbit")

        # Create a nested tab widget for orbit views
        orbit_view_tabs = QTabWidget()
        orbit_layout.addWidget(orbit_view_tabs)

        # Top-down view tab
        top_down_tab = QWidget()
        top_down_layout = QVBoxLayout()
        top_down_tab.setLayout(top_down_layout)
        orbit_view_tabs.addTab(top_down_tab, "Top-down View")

        self.orbit_widget = OrbitWidget(self.update_orbit_fields)
        top_down_layout.addWidget(self.orbit_widget)

        # Side view tab
        side_view_tab = QWidget()
        side_view_layout = QVBoxLayout()
        side_view_tab.setLayout(side_view_layout)
        orbit_view_tabs.addTab(side_view_tab, "Side View")

        self.vertical_orbit_widget = VerticalOrbitWidget(self.update_orbit_fields)
        side_view_layout.addWidget(self.vertical_orbit_widget)

        # Orbit parameters (keep this part as it was)
        orbit_params_layout = QFormLayout()
        orbit_layout.addLayout(orbit_params_layout)

        orbit_params_layout = QFormLayout()
        orbit_layout.addLayout(orbit_params_layout)

        self.parent_body = QLineEdit()
        orbit_params_layout.addRow("Parent Body:", self.parent_body)

        self.semi_major_axis = QDoubleSpinBox()
        self.semi_major_axis.setRange(1, 100000000)
        self.semi_major_axis.setSuffix(" km")
        self.semi_major_axis.valueChanged.connect(self.update_orbit_widget)
        orbit_params_layout.addRow("Semi-major Axis:", self.semi_major_axis)

        self.eccentricity = QDoubleSpinBox()
        self.eccentricity.setRange(0, 0.99)
        self.eccentricity.setSingleStep(0.01)
        self.eccentricity.valueChanged.connect(self.update_orbit_widget)
        orbit_params_layout.addRow("Eccentricity:", self.eccentricity)

        self.inclination = QDoubleSpinBox()
        self.inclination.setRange(0, 360)
        self.inclination.setSuffix("°")
        self.inclination.valueChanged.connect(self.update_orbit_widget)
        orbit_params_layout.addRow("Inclination:", self.inclination)
        self.planet_name.textChanged.connect(self.update_orbit_widget)
        self.parent_body.textChanged.connect(self.update_orbit_widget)

        # Biomes Tab
        biomes_tab = QWidget()
        biomes_layout = QVBoxLayout()
        biomes_tab.setLayout(biomes_layout)
        self.tab_widget.addTab(biomes_tab, "Biomes")

        self.biomes = []
        self.add_biome_button = QPushButton("Add Biome")
        self.add_biome_button.clicked.connect(self.add_biome)
        biomes_layout.addWidget(self.add_biome_button)

        # Textures Tab
        textures_tab = QWidget()
        textures_layout = QVBoxLayout()
        textures_tab.setLayout(textures_layout)
        self.tab_widget.addTab(textures_tab, "Textures")

        # Create a form layout for the file selections
        file_selection_layout = QFormLayout()
        textures_layout.addLayout(file_selection_layout)

        # Color Map
        self.color_map = QLineEdit()
        self.color_map_button = QPushButton("Browse")
        self.color_map_button.clicked.connect(lambda: self.browse_file(self.color_map))
        color_map_layout = QHBoxLayout()
        color_map_layout.addWidget(self.color_map)
        color_map_layout.addWidget(self.color_map_button)
        file_selection_layout.addRow("Color Map:", color_map_layout)

        # Height Map
        self.height_map = QLineEdit()
        self.height_map_button = QPushButton("Browse")
        self.height_map_button.clicked.connect(lambda: self.browse_file(self.height_map))
        height_map_layout = QHBoxLayout()
        height_map_layout.addWidget(self.height_map)
        height_map_layout.addWidget(self.height_map_button)
        file_selection_layout.addRow("Height Map:", height_map_layout)

        # Normal Map
        self.normal_map = QLineEdit()
        self.normal_map_button = QPushButton("Browse")
        self.normal_map_button.clicked.connect(lambda: self.browse_file(self.normal_map))
        normal_map_layout = QHBoxLayout()
        normal_map_layout.addWidget(self.normal_map)
        normal_map_layout.addWidget(self.normal_map_button)
        file_selection_layout.addRow("Normal Map:", normal_map_layout)

        generate_button = QPushButton("Create Mod Folder")
        generate_button.clicked.connect(self.save_complete_mod)
        main_layout.addWidget(generate_button)

        self.texture_previews = TexturePreviewContainer()
        textures_layout.addWidget(self.texture_previews)

    def toggle_atmosphere(self, value):
        has_atmo = (value == "Yes")
        for widget in self.atmo_widgets:
            widget.setEnabled(has_atmo)

    def add_biome(self):
        biome_widget = QWidget()
        biome_layout = QHBoxLayout()
        biome_widget.setLayout(biome_layout)

        biome_name = QLineEdit()
        biome_layout.addWidget(biome_name)

        biome_color = QPushButton("Select Color")
        biome_color.clicked.connect(lambda: self.select_color(biome_color))
        biome_layout.addWidget(biome_color)

        self.biomes.append((biome_name, biome_color))
        self.tab_widget.widget(4).layout().insertWidget(self.tab_widget.widget(4).layout().count() - 1, biome_widget)

    def select_color(self, button):
        color = QColorDialog.getColor()
        if color.isValid():
            button.setStyleSheet(f"background-color: {color.name()}")

    def browse_file(self, line_edit):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Image File", "", 
                                                 "Image Files (*.png *.jpg *.dds)")
        if file_name:
            line_edit.setText(file_name)
            # Update texture previews
            if line_edit == self.color_map:
                self.texture_previews.update_textures(color_path=file_name)
            elif line_edit == self.height_map:
                self.texture_previews.update_textures(height_path=file_name)
            elif line_edit == self.normal_map:
                self.texture_previews.update_textures(normal_path=file_name)

    def add_time_warp_level(self):
        altitude = self.altitude_input.value()
        multiplier = self.multiplier_input.value()
        self.time_warp_levels.append((altitude, multiplier))
        self.time_warp_levels.sort(key=lambda x: x[0])
        self.update_time_warp_display()

    def update_time_warp_display(self):
        display_text = "Time Warp Levels:\n"
        for altitude, multiplier in self.time_warp_levels:
            display_text += f"Altitude: {altitude} m, Multiplier: {multiplier}x\n"
        self.time_warp_display.setText(display_text)

    def update_orbit_widget(self):
        self.orbit_widget.semi_major_axis = self.semi_major_axis.value()
        self.orbit_widget.eccentricity = self.eccentricity.value()
        self.orbit_widget.inclination = self.inclination.value()
        self.orbit_widget.parent_body_name = self.parent_body.text()
        self.orbit_widget.planet_name = self.planet_name.text()
    
        self.vertical_orbit_widget.semi_major_axis = self.semi_major_axis.value()
        self.vertical_orbit_widget.eccentricity = self.eccentricity.value()
        self.vertical_orbit_widget.inclination = self.inclination.value()
        self.vertical_orbit_widget.parent_body_name = self.parent_body.text()
        self.vertical_orbit_widget.planet_name = self.planet_name.text()
    
        self.orbit_widget.update()
        self.vertical_orbit_widget.update()

    def update_orbit_fields(self):
        self.semi_major_axis.setValue(self.orbit_widget.semi_major_axis)
        self.eccentricity.setValue(self.orbit_widget.eccentricity)
        self.inclination.setValue(self.orbit_widget.inclination)
    
        # Update the spin boxes with the center offset
        scale_factor = min(self.orbit_widget.width(), self.orbit_widget.height()) / (2.2 * self.orbit_widget.semi_major_axis)
    
        if scale_factor > 0:
            center_x_km = self.orbit_widget.center_offset.x() / scale_factor
            center_y_km = self.orbit_widget.center_offset.y() / scale_factor
        else:
            center_x_km = 0
            center_y_km = 0
    
        # You may want to add new spin boxes for these offsets in your UI
        if hasattr(self, 'center_x_offset'):
            self.center_x_offset.setValue(center_x_km)
        if hasattr(self, 'center_y_offset'):
            self.center_y_offset.setValue(center_y_km)

    def generate_config(self):
        return generate_config(self)

    def save_config(self):
        config = generate_config(self)
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Kopernicus Config", "", "Config Files (*.cfg)")
        if file_name:
            with open(file_name, 'w') as f:
                f.write(config)
        
            # Copy and convert texture files to the same directory as the config file
            config_dir = os.path.dirname(file_name)
            for texture_field in [self.color_map, self.height_map, self.normal_map]:
                texture_path = texture_field.text()
                if texture_path:
                    texture_filename = os.path.basename(texture_path)
                    base_name, _ = os.path.splitext(texture_filename)
                    destination = os.path.join(config_dir, base_name + '.dds')
                    try:
                        convert_to_dds(texture_path, destination)
                        # Update the config file with the new DDS filename
                        with open(file_name, 'r') as f:
                            config_content = f.read()
                        config_content = config_content.replace(texture_filename, base_name + '.dds')
                        with open(file_name, 'w') as f:
                            f.write(config_content)
                    except Exception as e:
                        print(f"Error converting {texture_path} to DDS: {e}")

    def create_mod_folder_structure(self, config_name, save_path):
        mod_name = f"{config_name}Pack"
        mod_folder = os.path.join(save_path, mod_name)
    
        folders = {
            'config': os.path.join(mod_folder, 'GameData', mod_name, 'Config'),
            'textures': os.path.join(mod_folder, 'GameData', mod_name, 'Textures'),
            'cache': os.path.join(mod_folder, 'GameData', mod_name, 'Cache')
        }
    
        for folder in folders.values():
            os.makedirs(folder, exist_ok=True)
        
        return mod_folder, folders

    def save_complete_mod(self):
        if not self.planet_name.text():
            QMessageBox.warning(self, "Missing Information", "Please enter a planet name before creating the mod folder.")
            return

        # Get folder location from user
        save_path = QFileDialog.getExistingDirectory(self, "Select Location to Save Mod Folder")
        if not save_path:
            return

        # Create mod folder structure
        mod_folder, folders = self.create_mod_folder_structure(self.planet_name.text(), save_path)
    
        # Save config file
        config = self.generate_config()
        config_file = os.path.join(folders['config'], f"{self.planet_name.text()}.cfg")
        with open(config_file, 'w') as f:
            f.write(config)
    
        # Process and save textures
        texture_fields = {
            'color': (self.color_map, 'colormap'),
            'height': (self.height_map, 'heightmap'),
            'normal': (self.normal_map, 'normalmap')
        }
    
        for tex_type, (field, suffix) in texture_fields.items():
            texture_path = field.text()
            if texture_path:
                # Generate standardized texture name
                base_name = f"{self.planet_name.text()}_{suffix}"
                dds_path = os.path.join(folders['textures'], f"{base_name}.dds")
            
                try:
                    self.convert_to_dds(texture_path, dds_path)
                    # Update config file with correct texture path
                    with open(config_file, 'r') as f:
                        config_content = f.read()
                    old_name = os.path.splitext(os.path.basename(texture_path))[0]
                    config_content = config_content.replace(old_name, base_name)
                    with open(config_file, 'w') as f:
                        f.write(config_content)
                except Exception as e:
                    print(f"Error processing {tex_type} texture: {e}")
    
        # Create README file
        readme_content = f"""# {self.planet_name.text()}Pack
    Created with KSP Planet Creator

    ## Installation
    1. Copy the GameData folder to your Kerbal Space Program installation
    2. Ensure Kopernicus is installed

    ## Planet Details
    - Name: {self.planet_name.text()}
    - Parent Body: {self.parent_body.text()}
    - Radius: {self.radius.value()} km
    - Surface Gravity: {self.gravity.value()}g
    """
    
        with open(os.path.join(mod_folder, 'README.md'), 'w') as f:
            f.write(readme_content)
    
        QMessageBox.information(
            self, "Success",
            f"Mod folder created successfully at:\n{mod_folder}\n\nYou can now copy the GameData folder to your KSP installation."
        )

        return mod_folder