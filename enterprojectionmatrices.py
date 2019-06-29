import numpy as np
from PySide2.QtWidgets import QDialog
from ui_enterprojectionmatrices import Ui_Dialog as Ui_EnterProjectionMatrices
from alert import Alert


class EnterProjectionMatrices(QDialog):
	def __init__(self, parentWindow):
		self.parentWindow = parentWindow
		super(EnterProjectionMatrices, self).__init__()
		self.ui = Ui_EnterProjectionMatrices()
		self.ui.setupUi(self)

		self.projMatForm = [
			[self.ui.lineEdit_3, self.ui.lineEdit_4, self.ui.lineEdit_5, self.ui.lineEdit_6],
			[self.ui.lineEdit_7, self.ui.lineEdit_8, self.ui.lineEdit_9, self.ui.lineEdit_10],
			[self.ui.lineEdit_11, self.ui.lineEdit_12, self.ui.lineEdit_13, self.ui.lineEdit_14]
		]

		self.selectedView = 0
		self.viewNames = parentWindow.viewNames
		self.projectionMatrices = [np.zeros([3, 4]) for _ in self.viewNames]
		self.fillProjMatForm()

		self.ui.label_5.setText('Projection Matrix for View: %s'%self.viewNames[self.selectedView])
		self.ui.pushButton_5.clicked.connect(self.advanceView)
		self.ui.pushButton_6.clicked.connect(self.revertView)

		for row in range(3):
			for col in range(4):
				self.projMatForm[row][col].textChanged.connect(self.setProjMatElement(row, col))

		self.ui.pushButton_3.clicked.connect(self.ok)
		self.ui.pushButton_4.clicked.connect(self.close)

	def advanceView(self):
		self.selectedView = (self.selectedView + 1) % len(self.viewNames)
		self.ui.label_5.setText('Projection Matrix for View: %s'%self.viewNames[self.selectedView])
		self.fillProjMatForm()
	def revertView(self):
		self.selectedView = (self.selectedView - 1 + len(self.viewNames)) % len(self.viewNames)
		self.ui.label_5.setText('Projection Matrix for View: %s'%self.viewNames[self.selectedView])
		self.fillProjMatForm()
	def setProjMatElement(self, row, col):
		def f(val):
			try:
				v = float(val)
				self.projectionMatrices[self.selectedView][row, col] = v
			except ValueError:
				self.projMatForm[row][col].setText(str(self.projectionMatrices[self.selectedView][row, col]))
		return f
			
	def fillProjMatForm(self):
		p = self.projectionMatrices[self.selectedView]
		for row in range(3):
			for col in range(4):
				self.projMatForm[row][col].setText(str(p[row, col]))

	def ok(self):
		if np.equal(self.projectionMatrices, 0).all(axis=(1,2)).any():
			Alert('At least one projection matrix was all 0.').exec_()
			return
		self.parentWindow.projectionMatrices = [p.tolist() for p in self.projectionMatrices]
		self.done(1)