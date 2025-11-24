import sys
from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication

from src.ui.main import MainWindow

load_dotenv()

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        w = MainWindow()
        w.show()
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n👋 Exiting")