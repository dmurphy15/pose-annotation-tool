from PySide2.QtWidgets import QMainWindow

class SingleviewProjectMainWindow(QMainWindow):
	def __init__(self, cfg):
		self.cfg = cfg
		super(SingleviewProjectMainWindow, self).__init__()
		print('hey nice job, man!')