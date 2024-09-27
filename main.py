from PyQt5.QtWidgets import QApplication
from mainwindow import MainWindow
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    try:
        import pyi_splash
        pyi_splash.close()
    except:
        pass
    sys.exit(app.exec_())