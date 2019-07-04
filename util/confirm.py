from PySide2.QtWidgets import QDialog
from ui_py.ui_confirm import Ui_Dialog as Ui_Confirm

class Confirm(QDialog):
	def __init__(self, msg):
		super(Confirm, self).__init__()
		self.ui = Ui_Confirm()
		self.ui.setupUi(self)
		
		self.ui.textEdit.setText(msg)
		self.ui.textEdit.setReadOnly(True)

		self.ui.pushButton.clicked.connect(lambda: self.done(1))
		self.ui.pushButton_2.clicked.connect(self.close)
