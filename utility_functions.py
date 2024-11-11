import os
import shutil
from PIL import Image

def convert_to_dds(input_path, output_path):
    # Check if the file is already in DDS format
    if input_path.lower().endswith('.dds'):
        # If it is, just copy the file
        shutil.copy(input_path, output_path)
    else:
        # If it's not, convert it to PNG first (as Pillow doesn't support direct DDS conversion)
        with Image.open(input_path) as img:
            png_path = os.path.splitext(output_path)[0] + '.png'
            img.save(png_path)
        
        # Now use the texconv tool to convert PNG to DDS
        os.system(f'texconv -f DXT5 -o "{os.path.dirname(output_path)}" "{png_path}"')

def save_config(self):
    config = self.generate_config()
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
                    self.convert_to_dds(texture_path, destination)
                    # Update the config file with the new DDS filename
                    with open(file_name, 'r') as f:
                        config_content = f.read()
                    config_content = config_content.replace(texture_filename, base_name + '.dds')
                    with open(file_name, 'w') as f:
                        f.write(config_content)
                except Exception as e:
                    print(f"Error converting {texture_path} to DDS: {e}")
