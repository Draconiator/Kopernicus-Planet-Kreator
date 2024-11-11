import os
import math
from PyQt6.QtGui import QColor

def get_color_from_button(button):
    style = button.styleSheet()
    if "background-color" in style:
        color_str = style.split("background-color: ")[1].split(";")[0]
        return QColor(color_str)
    return QColor(0, 0, 0)  # Default to black if no color is set

def generate_config(self):
    config = f"""@Kopernicus:FOR[YourMod]
    {{
        Body
        {{
            name = {self.planet_name.text()}
            cacheFile = YourMod/{self.planet_name.text()}.bin
            Template
            {{
                name = Laythe
            }}
            Properties
            {{
                radius = {self.radius.value() * 1000}
                geeASL = {self.gravity.value()}
                timewarpAltitudeLimits = {' '.join(str(alt) for alt, _ in self.time_warp_levels)}
            }}
            Orbit
            {{
                referenceBody = {self.parent_body.text()}
                semiMajorAxis = {self.semi_major_axis.value() * 1000}
                eccentricity = {self.eccentricity.value()}
                inclination = {self.inclination.value()}
                longitudeOfAscendingNode = {math.degrees(math.atan2(self.orbit_widget.center_offset.y(), self.orbit_widget.center_offset.x()))}
                argumentOfPeriapsis = {math.degrees(math.atan2(self.orbit_widget.center_offset.y(), self.orbit_widget.center_offset.x()))}
            }}
    """
    if self.has_atmosphere.currentText() == "Yes":
        ambient_color = get_color_from_button(self.atmo_ambient_color)
        light_color = get_color_from_button(self.atmo_light_color)

        config += f"""        Atmosphere
        {{
            enabled = true
            oxygen = false
            maxAltitude = {self.atmosphere_height.value()}
            staticPressureASL = {self.static_pressure.value()}
            temperatureSeaLevel = {self.atmosphere_temp.value()}
            ambientColor = {ambient_color.redF():.6f},{ambient_color.greenF():.6f},{ambient_color.blueF():.6f},1
            lightColor = {light_color.redF():.6f},{light_color.greenF():.6f},{light_color.blueF():.6f},0.2
    
            pressureCurve
            {{
{self.atmo_pressure_curve.toPlainText()}
            }}
    
            temperatureCurve
            {{
{self.atmo_temp_curve.toPlainText()}
            }}
        }}
"""
    else:
        config += """        Atmosphere
        {
            enabled = false
        }
"""

    config += """        Biomes
        {
"""
    for biome_name, biome_color in self.biomes:
        color = get_color_from_button(biome_color)
        config += f"""            Biome
            {{
                name = {biome_name.text()}
                value = 1.0
                color = #{color.red():02x}{color.green():02x}{color.blue():02x}
            }}
"""
    config += """        }
        ScaledVersion
        {
            type = Atmospheric
            fadeStart = 50000
            fadeEnd = 60000
            Material
            {
                texture = """ + os.path.splitext(os.path.basename(self.color_map.text()))[0] + """.dds
                normals = """ + os.path.splitext(os.path.basename(self.normal_map.text()))[0] + """.dds
            }
        }
        PQS
        {
            Mods
            {
                VertexHeightMap
                {
                    map = """ + os.path.splitext(os.path.basename(self.height_map.text()))[0] + """.dds
                    offset = 0
                    deformity = 6500
                    scaleDeformityByRadius = false
                    order = 20
                    enabled = true
                }
                VertexColorMap
                {
                    map = """ + os.path.splitext(os.path.basename(self.color_map.text()))[0] + """.dds
                    order = 21
                    enabled = true
                }
            }
        }
    }
}
"""
    if self.enable_rescale.isChecked():
        rescale_factor = self.rescale_factor.value()
        config += f"""
    @Kopernicus:AFTER[YourMod]
    {{
        @Body[{self.planet_name.text()}]
        {{
            @Properties
            {{
                @radius *= {rescale_factor}
            }}
            @Orbit
            {{
                @semiMajorAxis *= {rescale_factor}
            }}
        }}
    }}
"""
    return config
