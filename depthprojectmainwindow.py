from PySide2.QtWidgets import QMainWindow

class DepthProjectMainWindow(QMainWindow):
	def __init__(self, cfg):
		self.cfg = cfg
		super(DepthProjectMainWindow, self).__init__()
		print('hey, man!')