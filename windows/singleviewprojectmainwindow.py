import os
from glob import iglob
import numpy as np 
import pandas as pd
from PySide2.QtWidgets import QMainWindow, QRadioButton, QCheckBox, QWidget, QVBoxLayout, QLabel, QGraphicsView
from PySide2.QtGui import QPixmap, QColor
from PySide2.QtCore import Qt, QPointF
from ui_py.ui_singleviewproject import Ui_MainWindow as Ui_SingleviewProjectMainWindow
from util.alert import Alert
from util.confirm import Confirm
from .imageviews import MainImageView, ImageView

class SingleviewProjectMainWindow(QMainWindow):
	def __init__(self, cfg):
		super(SingleviewProjectMainWindow, self).__init__()
		self.cfg = cfg
		# we will only use images that exist for all views
		imageNames = iglob(os.path.join(cfg.imageFolder, '*'+cfg.imageExtension))
		imageNames = set(map(lambda s: os.path.basename(s), imageNames))

		# read the data; if there is none, then create a new frame for the data
		try:
			data_pixel = pd.read_csv(os.path.join(cfg.projectFolder, 'pixel-annotation-data.csv'), index_col=0, header=[0,1])
		except FileNotFoundError:
			data_pixel = pd.DataFrame(
				columns=pd.MultiIndex.from_product([cfg.joints, ['u', 'v']], names=['joint', 'coordinate']),
				index=pd.Index([], name='image')
			)

		# in case the user has deleted images
		removed = set.difference(set(data_pixel.index.values), imageNames)
		if len(removed) > 0:
			msg = 'The following %d images are not present in all views, and this project\'s annotation data for them will be deleted:\n%s'
			msg = msg%(len(removed), '\n'.join(sorted(removed)))
			if not Confirm(msg).exec_():
				self.close()
				return

		# in case the user has added images
		added = set.difference(imageNames, set(data_pixel.index.values))
		if len(added) > 0:
			msg = 'The following %d images have been added to this project:\n%s'
			msg = msg%(len(added), '\n'.join(sorted(added)))
			if not Confirm(msg).exec_():
				self.close()
				return

		# create the dataframes, including anything that has been added/removed
		self.data_pixel = pd.concat([
			data_pixel.drop(labels=removed), 
			pd.DataFrame(
				columns=pd.MultiIndex.from_product([cfg.joints, ['u', 'v']], names=['joint', 'coordinate']),
				index=pd.Index(added, name='image')
			)
		])
		self.data_pixel.sort_index(inplace=True)

		# the project needs to have at least one image
		self.images = self.data_pixel.index.values
		if len(self.images) == 0:
			Alert('Project must have at least one image that exists in all view folders.').exec_()
			self.close()
			return

		# set up UI
		self.ui = Ui_SingleviewProjectMainWindow()
		self.ui.setupUi(self)

		# initialize counters
		self.imageIdx = 0
		self.jointIdx = 0

		# initialize which joints are displaying (all of them, to start)
		self.displaying = set(range(len(self.cfg.joints)))

		# initialize radius for annotations
		self.radius = 5

		# initialize joint colors (I guess these aren't necessarily visually distinct, maybe there's a better way)
		inc = 256**3 // len(self.cfg.joints)
		color = 256**3-1
		self.colors = [QColor(*tuple((color-inc*i).to_bytes(3, 'big'))) for i in range(len(self.cfg.joints))]

		# set headers above main view
		self.ui.label_4.setText('Image: %s'%self.images[self.imageIdx])

		# set up the spinbox for changing the frame below the main view
		self.ui.spinBox.setMinimum(-1)
		self.ui.spinBox.setMaximum(len(self.images))
		self.ui.spinBox.valueChanged.connect(self.setFrame)

		# set up the double spinbox for changing the annotation radius
		self.ui.doubleSpinBox.valueChanged.connect(self.setRadius)
		self.ui.doubleSpinBox.setValue(self.radius)

		# set up skip to next frame missing any/all displayed annotations
		self.ui.pushButton.clicked.connect(self.skipMissingAny)
		self.ui.pushButton_2.clicked.connect(self.skipMissingAll)

		# add buttons for labeling and displaying annotations
		self.labelingButtons = []
		self.displayingButtons = []
		for row, jointName in enumerate(cfg.joints):
			r = QRadioButton(jointName+'*', self.ui.scrollAreaWidgetContents_3)
			r.clicked.connect(self.setJoint(row))
			# r.setStyleSheet('color: red'
			self.ui.gridLayout.addWidget(r, row, 0, 1, 1)
			self.labelingButtons.append(r)
			c = QCheckBox(jointName, self.ui.scrollAreaWidgetContents_2)
			c.clicked.connect(self.setDisplaying(row))
			c.setChecked(True)
			self.ui.gridLayout_2.addWidget(c, row, 0, 1, 1)
			self.displayingButtons.append(c)
		self.labelingButtons[self.jointIdx].setChecked(True)
		self.ui.gridLayout.setRowStretch(len(cfg.joints), 1)
		self.ui.gridLayout_2.setRowStretch(len(cfg.joints), 1)

		# initialize the main view
		self.mainView = MainImageView(self.ui.centralwidget)
		self.ui.verticalLayout_2.addWidget(self.mainView)
		self.mainView.photoClicked.connect(self.mainImageClicked)
		self.mainView.photoRightClicked.connect(self.removeAnnotation)

		self.loadPhotos()
		self.loadAnnotations()

		# helps register keypress events
		self.setFocusPolicy(Qt.ClickFocus)

	def loadPhotos(self):
		self.mainView.setPhoto(QPixmap(os.path.join(self.cfg.imageFolder, self.images[self.imageIdx])))

	def loadAnnotations(self):
		self.mainView.clearAnnotations()
		r = self.mainView.getPixmap().rect()
		data2d = self.data_pixel.loc[self.images[self.imageIdx], :]
		for j, joint in enumerate(self.cfg.joints):
			d = data2d[joint]
			if d.isna().any():
				self.labelingButtons[j].setText(joint+'*')
				continue
			self.mainView.addAnnotation(QPointF(d['u'] * r.width(), d['v'] * r.height()), self.colors[j], self.radius, joint)
			self.labelingButtons[j].setText(joint)
			if not j in self.displaying:
				self.mainView.hideAnnotation(joint)

	def setFrame(self, index):
		if index >= len(self.images):
			self.ui.spinBox.setValue(0)
			return
		elif index < 0: 
			self.ui.spinBox.setValue(len(self.images)-1)
		self.imageIdx = index
		self.ui.label_4.setText('Image: %s'%self.images[self.imageIdx])
		self.loadPhotos()
		self.loadAnnotations()

	def setRadius(self, r):
		self.radius = r

	def setJoint(self, index):
		def f():
			if self.labelingButtons[index].isChecked():
				self.jointIdx = index
		return f
	def setDisplaying(self, index):
		def f():
			if self.displayingButtons[index].isChecked():
				self.showAnnotations(self.cfg.joints[index])
				self.displaying.add(index)
				self.labelingButtons[index].setEnabled(True)
			else:
				# ensure that at least one box will stay checked
				if len(self.displaying) == 1:
					self.displayingButtons[index].setChecked(True)
				else:
					self.hideAnnotations(self.cfg.joints[index])
					self.displaying.remove(index)
					self.labelingButtons[index].setEnabled(False)
					if self.jointIdx == index:
						self.labelingButtons[self.jointIdx].setChecked(False)
						self.jointIdx = next(iter(self.displaying))
						self.labelingButtons[self.jointIdx].setChecked(True)
		return f

	def mainImageClicked(self, pos):
		self.labelingButtons[self.jointIdx].setText(self.cfg.joints[self.jointIdx])
		r = self.mainView.getPixmap().rect()
		pos_normalized = (pos.x() / r.width(), pos.y() / r.height())
		self.data_pixel.loc[self.images[self.imageIdx], self.cfg.joints[self.jointIdx]] = pos_normalized
		self.mainView.addAnnotation(pos, self.colors[self.jointIdx], self.radius, self.cfg.joints[self.jointIdx])

	def removeAnnotation(self):
		self.labelingButtons[self.jointIdx].setText(self.cfg.joints[self.jointIdx]+'*')
		self.data_pixel.loc[self.images[self.imageIdx], self.cfg.joints[self.jointIdx]] = [np.nan, np.nan]
		self.mainView.removeAnnotation(self.cfg.joints[self.jointIdx])

	def hideAnnotations(self, key):
		self.mainView.hideAnnotation(key)

	def showAnnotations(self, key):
		self.mainView.showAnnotation(key)

	def skipMissingAny(self):
		cols = [self.cfg.joints[idx] for idx in self.displaying]
		data = self.data_pixel.loc[:, cols]
		missing = data.isna().any(axis=1)
		idx = missing[missing].index.get_loc(self.images[self.imageIdx])
		image = missing[missing].index[idx+1]
		idx = missing.index.get_loc(image)
		self.ui.spinBox.setValue(idx)

	def skipMissingAll(self):
		cols = [self.cfg.joints[idx] for idx in self.displaying]
		data = self.data_pixel.loc[:, cols]
		missing = data.isna().all(axis=1)
		idx = missing[missing].index.get_loc(self.images[self.imageIdx])
		image = missing[missing].index[idx+1]
		idx = missing.index.get_loc(image)
		self.ui.spinBox.setValue(idx)

	def keyPressEvent(self, event):
		if event.key() == Qt.Key_F:
			self.ui.spinBox.setValue((self.imageIdx + 1) % len(self.images))
		elif event.key() == Qt.Key_B:
			self.ui.spinBox.setValue((self.imageIdx + len(self.images) - 1) % len(self.images))
		elif event.key() == Qt.Key_J:
			idx = (self.jointIdx + 1) % len(self.cfg.joints)
			while True:
				if idx in self.displaying:
					break
				idx = (idx + 1) % len(self.cfg.joints) 
			self.jointIdx = idx
			self.labelingButtons[self.jointIdx].setChecked(True)

	def closeEvent(self, event):
		self.data_pixel.to_csv(os.path.join(self.cfg.projectFolder, 'pixel-annotation-data.csv'))
		super(SingleviewProjectMainWindow, self).closeEvent(event)