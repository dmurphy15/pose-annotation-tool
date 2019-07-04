import os
import yaml
from PySide2.QtWidgets import QDialog, QFileDialog
from ui_py.ui_newprojectdialog import Ui_Dialog as Ui_NewProjectDialog
from util.alert import Alert
from .enterprojectionmatrices import EnterProjectionMatrices
from collections import OrderedDict


class NewProjectDialog(QDialog):
	projectModes = [
		'RGB Single View',
		'RGB Multi View',
		'RGB Depth'
	]
	imageExtensions = [
		'.png',
		'.jpg'
	]
	
	def __init__(self, projectPathToOpen):
		self.projectPathToOpen = projectPathToOpen
		super(NewProjectDialog, self).__init__()
		self.ui = Ui_NewProjectDialog()
		self.ui.setupUi(self)
		
		# selecting project path
		self.ui.lineEdit.setText(os.path.join(os.getcwd(), 'Untitled'))
		self.ui.pushButton.clicked.connect(self.selectProjectPath)
		# selecting image directory path
		self.ui.lineEdit_2.setText(os.getcwd())
		self.ui.lineEdit_2.textChanged.connect(self.setViewNames)
		self.ui.pushButton_2.clicked.connect(self.selectImagePath)
		# selecting project mode
		self.ui.comboBox_2.currentTextChanged.connect(self.setProjectMode)
		# displaying view names
		self.ui.label_5.setHidden(True)
		self.ui.scrollArea.setHidden(True)
		self.ui.label_6.setText('\n'.join(self.getViewNames(os.getcwd())))
	
		# ok
		self.ui.pushButton_3.clicked.connect(self.ok)
		# cancel
		self.ui.pushButton_4.clicked.connect(self.close)
		
	def selectProjectPath(self):
		dialog = QFileDialog(self)
		dialog.setFileMode(QFileDialog.AnyFile)
		dialog.setOption(dialog.ShowDirsOnly, True)
		dialog.selectFile(self.ui.lineEdit_2.text())
		dialog.setWindowTitle('Name A New Directory For Project')
		if dialog.exec_():
			self.ui.lineEdit.setText(dialog.selectedFiles()[0])
	
	def selectImagePath(self):
		dialog = QFileDialog(self)
		dialog.setFileMode(QFileDialog.DirectoryOnly)
		dialog.selectFile(self.ui.lineEdit_2.text())
		dialog.setWindowTitle('Select Directory Where Images Are Stored')
		if dialog.exec_():
			self.ui.lineEdit_2.setText(dialog.selectedFiles()[0])
			
	def setViewNames(self, text):
		self.ui.label_6.setText('\n'.join(self.getViewNames(text)))
	def setProjectMode(self, mode): 
		hide = mode!='RGB Multi View' 
		self.ui.label_5.setHidden(hide)
		self.ui.scrollArea.setHidden(hide)
	def getViewNames(self, imagePath):
		try: 
			return sorted(next(os.walk(imagePath))[1])
		except: 
			return []
		
	def ok(self):
		imagePath = self.ui.lineEdit_2.text()
		if not os.path.exists(imagePath):
			Alert('Please select an image folder path that exists.').exec_()
			return
		projectPath = self.ui.lineEdit.text()
		if os.path.exists(projectPath):
			Alert('Please choose a project folder path that does not already exist.').exec_()
			return
		jointNames = OrderedDict.fromkeys(map(lambda s: s.strip(), self.ui.textEdit.toPlainText().split('\n')))
		jointNames.pop('', None)
		jointNames = list(jointNames.keys())
		if len(jointNames)==0:
			Alert('Please enter at least one joint to label.').exec_()
			return
		projectMode = self.ui.comboBox_2.currentText()
		if projectMode == 'RGB Multi View':
			viewNames = sorted(self.getViewNames(imagePath))
			if len(viewNames) < 2:
				Alert('Multiview mode must have at least 2 views. (Each view will correspond to a folder inside the ' + \
					'image folder path)').exec_()
				return
			# this will prompt the user and put the projection matrices into the list
			projectionMatrices = []
			d = EnterProjectionMatrices(viewNames, projectionMatrices)
			if not d.exec_():
				return
		imageExtension = self.ui.comboBox.currentText()
		try:
			os.mkdir(projectPath)
			f = open(os.path.join(projectPath, 'cfg.yaml'), 'w')
			cfg = {
				'projectFolder': projectPath,
				'imageFolder': imagePath,
				'imageExtension': imageExtension,
				'mode': projectMode,
				'joints': jointNames
			}
			if projectMode == 'RGB Multi View':
				cfg['views'] = viewNames
				cfg['projectionMatrices'] = projectionMatrices 
			yaml.dump(cfg, f)

			self.projectPathToOpen.append(projectPath)
			self.done(1)
		except Exception as e:
			Alert(str(e)).exec_()