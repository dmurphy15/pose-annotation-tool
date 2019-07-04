import sys
from PySide2.QtWidgets import QApplication
from windows.mainwindow import MainWindow 

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())