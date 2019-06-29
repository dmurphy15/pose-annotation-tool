import os
import yaml
from PySide2.QtWidgets import QDialog, QFileDialog
from ui_newprojectdialog import Ui_Dialog as Ui_NewProjectDialog
from alert import Alert
from enterprojectionmatrices import EnterProjectionMatrices


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
	
	def __init__(self, mainWindow):
		self.mainWindow = mainWindow
		super(NewProjectDialog, self).__init__()
		self.ui = Ui_NewProjectDialog()
		self.ui.setupUi(self)
		
		self.projectPath = os.path.join(os.getcwd(), 'Untitled')
		self.imagePath = os.getcwd()
		self.viewNames = self.getViewNames()
		self.imageExtension = self.imageExtensions[0]
		self.projectMode = self.projectModes[0]
		
		# selecting project path
		self.ui.lineEdit.setText(self.projectPath)
		self.ui.lineEdit.textChanged.connect(self.setProjectPath)
		self.ui.pushButton.clicked.connect(self.selectProjectPath)
		# selecting image directory path
		self.ui.lineEdit_2.setText(self.imagePath)
		self.ui.lineEdit_2.textChanged.connect(self.setImagePath)
		self.ui.pushButton_2.clicked.connect(self.selectImagePath)
		# selecting image extension
		self.ui.comboBox.currentTextChanged.connect(self.setImageExtension)
		# selecting project mode
		self.ui.comboBox_2.currentTextChanged.connect(self.setProjectMode)
		# displaying view names
		self.ui.label_5.setHidden(True)
		self.ui.scrollArea.setHidden(True)
		self.ui.label_6.setText('\n'.join(self.viewNames))
	
		# ok
		self.ui.pushButton_3.clicked.connect(self.ok)
		# cancel
		self.ui.pushButton_4.clicked.connect(self.close)
		
	def selectProjectPath(self):
		dialog = QFileDialog(self)
		dialog.setFileMode(QFileDialog.AnyFile)
		dialog.setOption(dialog.ShowDirsOnly, True)
		dialog.selectFile(self.projectPath)
		dialog.setWindowTitle('Name A New Directory For Project')
		if dialog.exec_():
			self.ui.lineEdit.setText(dialog.selectedFiles()[0])
	
	def selectImagePath(self):
		dialog = QFileDialog(self)
		dialog.setFileMode(QFileDialog.DirectoryOnly)
		dialog.selectFile(self.imagePath)
		dialog.setWindowTitle('Select Directory Where Images Are Stored')
		if dialog.exec_():
			self.ui.lineEdit_2.setText(dialog.selectedFiles()[0])
			
	def setProjectPath(self, text):
		self.projectPath = text
	def setImagePath(self, text):
		self.imagePath = text
		self.viewNames = self.getViewNames()
		self.ui.label_6.setText('\n'.join(self.viewNames))
	def setImageExtension(self, ext):
		self.imageExtension = ext
	def setProjectMode(self, mode):
		self.projectMode = mode
		self.ui.label_5.setHidden(mode!='RGB Multi View')
		self.ui.scrollArea.setHidden(mode!='RGB Multi View')
	def getViewNames(self):
		try:
			return next(os.walk(self.imagePath))[1]
		except:
			return []
		
	def ok(self):
		if not os.path.exists(self.imagePath):
			Alert('Please select an image folder path that exists.').exec_()
			return
		if os.path.exists(self.projectPath):
			Alert('Please choose a project folder path that does not already exist.').exec_()
			return
		if self.projectMode == 'RGB Multi View':
			if len(self.viewNames) < 2:
				Alert('Multiview mode must have at least 2 views. (Each view will correspond to a folder inside the ' + \
					'image folder path)').exec_()
				return
			# this will prompt the user and set projectionMatrices
			d = EnterProjectionMatrices(self)
			if not d.exec_():
				return
		try:
			os.mkdir(self.projectPath)
			f = open(os.path.join(self.projectPath, 'cfg.yaml'), 'w')
			cfg = {
				'imageFolder': self.imagePath,
				'imageExtension': self.imageExtension,
				'mode': self.projectMode
			}
			if self.projectMode == 'RGB Multi View':
				cfg['projectionMatrices'] = { self.viewNames[i]: self.projectionMatrices[i] for i in range(len(self.viewNames)) }
			yaml.dump(cfg, f)
			self.done(1)
			self.mainWindow.doOpenProject(self.projectPath)
		except Exception as e:
			Alert(str(e)).exec_()