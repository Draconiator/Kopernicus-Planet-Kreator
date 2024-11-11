import sys
from PyQt6.QtWidgets import QApplication
from planet_creator import PlanetCreator
import os

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlanetCreator()
    window.show()
    sys.exit(app.exec())