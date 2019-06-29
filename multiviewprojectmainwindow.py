from PySide2.QtWidgets import QMainWindow
from ui_multiviewproject import Ui_MainWindow as Ui_MultiviewProjectMainWindow

class MultiviewProjectMainWindow(QMainWindow):
	def __init__(self, cfg):
		self.cfg = cfg
		super(MultiviewProjectMainWindow, self).__init__()
		self.ui = Ui_MultiviewProjectMainWindow()
		self.ui.setupUi(self)