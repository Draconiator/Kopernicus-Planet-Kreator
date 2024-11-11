from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                            QSizePolicy, QScrollArea)
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor
from PyQt6.QtCore import Qt, QSize, QTimer
import numpy as np
from PIL import Image
import io

class TexturePreviewWidget(QWidget):
    def __init__(self, preview_type="color", parent=None):
        """
        Initialize a texture preview widget.
        
        Args:
            preview_type (str): Type of texture being previewed 
                              ("color", "height", or "normal")
            parent: Parent widget
        """
        super().__init__(parent)
        self.preview_type = preview_type
        self.current_path = None
        self.setup_ui()
        
        # Setup refresh timer for smooth updates
        self.refresh_timer = QTimer()
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.timeout.connect(self.update_preview)
        
    def setup_ui(self):
        """Setup the widget's UI components"""
        self.layout = QVBoxLayout(self)
        
        # Create title label
        title_map = {
            "color": "Color Map Preview",
            "height": "Height Map Preview",
            "normal": "Normal Map Preview"
        }
        self.title = QLabel(title_map.get(self.preview_type, "Texture Preview"))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title)
        
        # Create scroll area for the preview
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.preview_label.setMinimumSize(200, 200)
        
        self.scroll_area.setWidget(self.preview_label)
        self.layout.addWidget(self.scroll_area)
        
    def set_texture(self, file_path):
        """
        Set the texture to be previewed.
        
        Args:
            file_path (str): Path to the texture file
        """
        if file_path == self.current_path:
            return
            
        self.current_path = file_path
        if not self.refresh_timer.isActive():
            self.refresh_timer.start(100)  # 100ms delay for smooth updates
            
    def update_preview(self):
        """Update the preview with the current texture"""
        if not self.current_path:
            self.preview_label.setText("No texture loaded")
            return
            
        try:
            # Open image with PIL first
            with Image.open(self.current_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    
                # Process based on preview type
                if self.preview_type == "height":
                    # Convert height map to visible grayscale
                    img = img.convert('L')
                    img = img.convert('RGB')
                elif self.preview_type == "normal":
                    # Ensure normal map colors are visible
                    img = self._process_normal_map(img)
                    
                # Convert to QImage
                img_data = img.tobytes("raw", "RGB")
                q_img = QImage(img_data, img.size[0], img.size[1], 
                             img.size[0] * 3, QImage.Format.Format_RGB888)
                
                # Create and scale pixmap
                pixmap = QPixmap.fromImage(q_img)
                scaled_pixmap = self._scale_pixmap(pixmap)
                
                # Update preview
                self.preview_label.setPixmap(scaled_pixmap)
                
        except Exception as e:
            self.preview_label.setText(f"Error loading texture:\n{str(e)}")
            
    def _process_normal_map(self, img):
        """
        Process normal map to enhance visibility.
        
        Args:
            img (PIL.Image): Input normal map image
            
        Returns:
            PIL.Image: Processed normal map
        """
        # Convert to numpy array
        img_array = np.array(img)
        
        # Normalize and enhance contrast
        img_array = ((img_array / 255.0) * 0.5 + 0.5) * 255
        img_array = img_array.astype(np.uint8)
        
        return Image.fromarray(img_array)
        
    def _scale_pixmap(self, pixmap):
        """
        Scale the pixmap to fit the preview area while maintaining aspect ratio.
        
        Args:
            pixmap (QPixmap): Input pixmap
            
        Returns:
            QPixmap: Scaled pixmap
        """
        # Get available size
        available_size = self.scroll_area.size()
        pixmap_size = pixmap.size()
        
        # Calculate scaling factors
        w_scale = available_size.width() / pixmap_size.width()
        h_scale = available_size.height() / pixmap_size.height()
        scale = min(w_scale, h_scale, 1.0)  # Don't upscale beyond original size
        
        # Calculate new size
        new_size = QSize(
            int(pixmap_size.width() * scale),
            int(pixmap_size.height() * scale)
        )
        
        return pixmap.scaled(
            new_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
    def sizeHint(self):
        """Provide a reasonable default size"""
        return QSize(300, 300)

class TexturePreviewContainer(QWidget):
    """Container widget to manage multiple texture previews"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the container's UI layout"""
        self.layout = QVBoxLayout(self)
        
        # Create preview widgets for each texture type
        self.color_preview = TexturePreviewWidget("color")
        self.height_preview = TexturePreviewWidget("height")
        self.normal_preview = TexturePreviewWidget("normal")
        
        # Add previews to layout
        self.layout.addWidget(self.color_preview)
        self.layout.addWidget(self.height_preview)
        self.layout.addWidget(self.normal_preview)
        
    def update_textures(self, color_path=None, height_path=None, normal_path=None):
        """
        Update all texture previews.
        
        Args:
            color_path (str, optional): Path to color map
            height_path (str, optional): Path to height map
            normal_path (str, optional): Path to normal map
        """
        if color_path:
            self.color_preview.set_texture(color_path)
        if height_path:
            self.height_preview.set_texture(height_path)
        if normal_path:
            self.normal_preview.set_texture(normal_path)
