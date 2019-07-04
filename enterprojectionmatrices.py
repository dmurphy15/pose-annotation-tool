import numpy as np
from PySide2.QtWidgets import QDialog, QStyle
from PySide2.QtGui import QIcon
from ui_enterprojectionmatrices import Ui_Dialog as Ui_EnterProjectionMatrices
from alert import Alert


class EnterProjectionMatrices(QDialog):
	def __init__(self, viewNames, projectionMatrices):
		self.viewNames = viewNames
		self.projectionMatrices = projectionMatrices
		super(EnterProjectionMatrices, self).__init__()
		self.ui = Ui_EnterProjectionMatrices()
		self.ui.setupUi(self)

		self.projMatForm = [
			[self.ui.lineEdit_3, self.ui.lineEdit_4, self.ui.lineEdit_5, self.ui.lineEdit_6],
			[self.ui.lineEdit_7, self.ui.lineEdit_8, self.ui.lineEdit_9, self.ui.lineEdit_10],
			[self.ui.lineEdit_11, self.ui.lineEdit_12, self.ui.lineEdit_13, self.ui.lineEdit_14]
		]

		self.selectedView = 0
		for _ in self.viewNames:
			self.projectionMatrices.append([[0.0 for _ in range(4)] for _ in range(3)])
		self.fillProjMatForm()

		self.ui.label_5.setText('Projection Matrix for View: %s'%self.viewNames[self.selectedView])
		self.ui.pushButton_5.clicked.connect(self.advanceView)
		self.ui.pushButton_5.setText('')
		self.ui.pushButton_5.setIcon(QIcon(self.style().standardIcon(QStyle.SP_ArrowForward)))
		self.ui.pushButton_6.clicked.connect(self.revertView)
		self.ui.pushButton_6.setText('')
		self.ui.pushButton_6.setIcon(QIcon(self.style().standardIcon(QStyle.SP_ArrowBack)))

		self.ui.pushButton_3.clicked.connect(self.ok)
		self.ui.pushButton_4.clicked.connect(self.close)

	def advanceView(self):
		if not self.saveProjMatForm():
			return
		self.selectedView = (self.selectedView + 1) % len(self.viewNames)
		self.ui.label_5.setText('Projection Matrix for View: %s'%self.viewNames[self.selectedView])
		self.fillProjMatForm()
	def revertView(self):
		if not self.saveProjMatForm():
			return
		self.selectedView = (self.selectedView - 1 + len(self.viewNames)) % len(self.viewNames)
		self.ui.label_5.setText('Projection Matrix for View: %s'%self.viewNames[self.selectedView])
		self.fillProjMatForm()
	
	def saveProjMatForm(self):
		try:
			projMat = [[float(self.projMatForm[row][col].text()) for col in range(4)] for row in range(3)]
		except:
			Alert('All entries must be numbers.').exec_()
			return False
		self.projectionMatrices[self.selectedView] = projMat
		return True


	def fillProjMatForm(self):
		p = self.projectionMatrices[self.selectedView]
		for row in range(3):
			for col in range(4):
				self.projMatForm[row][col].setText(str(p[row][col]))

	def ok(self):
		if not self.saveProjMatForm():
			return
		if np.equal(self.projectionMatrices, 0).all(axis=(1,2)).any():
			Alert('At least one projection matrix was all 0.').exec_()
			return
		self.done(1)