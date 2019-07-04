from PySide2.QtWidgets import QDialog
from ui_py.ui_alert import Ui_Dialog as Ui_Alert

class Alert(QDialog):
	def __init__(self, msg):
		super(Alert, self).__init__()
		self.ui = Ui_Alert()
		self.ui.setupUi(self)
		
		self.ui.textEdit.setText(msg)
		self.ui.textEdit.setReadOnly(True)