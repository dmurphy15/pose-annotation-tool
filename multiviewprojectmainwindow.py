import os
from glob import iglob
import numpy as np 
import pandas as pd
from PySide2.QtWidgets import QMainWindow, QRadioButton, QCheckBox, QWidget, QVBoxLayout, QLabel, QGraphicsView
from PySide2.QtGui import QPixmap, QColor
from PySide2.QtCore import Qt, QPointF
from ui_multiviewproject import Ui_MainWindow as Ui_MultiviewProjectMainWindow
from alert import Alert
from confirm import Confirm
from imageviews import MainImageView, MiniImageView

class MultiviewProjectMainWindow(QMainWindow):
	def __init__(self, cfg):
		super(MultiviewProjectMainWindow, self).__init__()
		self.cfg = cfg
		# we will only use images that exist for all views
		imageNames = [iglob(os.path.join(cfg.imageFolder, view, '*'+cfg.imageExtension)) for view in cfg.views]
		imageNames = [set(map(lambda s: os.path.basename(s), l)) for l in imageNames]
		imageNames = set.intersection(*imageNames)

		# read the data; if there is none, then create a new frame for the data
		try:
			data_pixel = pd.read_csv(os.path.join(cfg.projectFolder, 'pixel-annotation-data.csv'))
			data_3d = pd.read_csv(os.path.join(cfg.projectFolder, '3d-annotation-data.csv'))
		except FileNotFoundError:
			data_pixel = pd.DataFrame(
				columns=pd.MultiIndex.from_product([cfg.joints, ['u', 'v']], names=['joint', 'coordinate']),
				index=pd.MultiIndex(levels=[[],[]], codes=[[],[]], names=['view', 'image'])
			)
			data_3d = pd.DataFrame(
				columns=pd.MultiIndex.from_product([cfg.joints, ['x','y','z']], names=['joint', 'coordinate']),
				index=pd.Index([], name='image')
			)

		# in case the user has deleted images
		removed = set.difference(set(data_3d.index.values), imageNames)
		if len(removed) > 0:
			msg = 'The following %d images are not present in all views, and this project\'s annotation data for them will be deleted:\n%s'
			msg = msg%(len(removed), '\n'.join(sorted(removed)))
			if not Confirm(msg).exec_():
				self.close()
				return
		remove_idx = pd.MultiIndex.from_product([cfg.views, removed])

		# in case the user has added images
		added = set.difference(imageNames, set(data_3d.index.values))
		if len(added) > 0:
			msg = 'The following %d images have been added to this project:\n%s'
			msg = msg%(len(added), '\n'.join(sorted(added)))
			if not Confirm(msg).exec_():
				self.close()
				return
		add_idx = pd.MultiIndex.from_product([cfg.views, added])

		# create the dataframes, including anything that has been added/removed
		self.data_pixel = pd.concat([
			data_pixel.drop(labels=remove_idx), 
			pd.DataFrame(
				columns=pd.MultiIndex.from_product([cfg.joints, ['u', 'v']], names=['joint', 'coordinate']),
				index=add_idx
			)
		])
		self.data_pixel.sort_index(inplace=True)
		self.data_3d = pd.concat([
			data_3d.drop(labels=removed), 
			pd.DataFrame(
				columns=pd.MultiIndex.from_product([cfg.joints, ['x', 'y', 'z']], names=['joint', 'coordinate']),
				index=pd.Index(added, name='image')
			)
		])
		self.data_3d.sort_index(inplace=True)

		# the project needs to have at least one image
		self.images = self.data_3d.index.values
		if len(self.images) == 0:
			Alert('Project must have at least one image that exists in all view folders.').exec_()
			self.close()
			return

		# set up UI
		self.ui = Ui_MultiviewProjectMainWindow()
		self.ui.setupUi(self)

		# initialize counters
		self.viewIdx = 0
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
		self.ui.label.setText('View: %s'%str(self.cfg.views[self.viewIdx]))
		self.ui.label_4.setText('Image: %s'%self.images[self.imageIdx])

		# set up the combobox/spinbox for changing the view/frame below the main view
		for view in cfg.views:
			self.ui.comboBox.addItem(str(view))
		self.ui.spinBox.setMinimum(-1)
		self.ui.spinBox.setMaximum(len(self.images))
		self.ui.spinBox.valueChanged.connect(self.setFrame)
		self.ui.comboBox.currentIndexChanged.connect(self.setView)

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

		# add a miniature display for every view
		self.miniViews = []
		for row, view in enumerate(cfg.views):
			w = QWidget(self.ui.scrollAreaWidgetContents)
			self.ui.gridLayout_3.addWidget(w, row, 0, 1, 1)
			vLayout = QVBoxLayout(w)
			l = QLabel(w)
			l.setText('View: %s'%str(view))
			vLayout.addWidget(l)
			v = MiniImageView(w)
			vLayout.addWidget(v)
			self.miniViews.append({
				'container': w,
				'layout': vLayout,
				'label': l,
				'view': v
			})

		self.loadPhotos()
		self.loadAnnotations()

		self.setFocusPolicy(Qt.ClickFocus)

	def loadPhotos(self):
		self.mainView.setPhoto(QPixmap(os.path.join(self.cfg.imageFolder, self.cfg.views[self.viewIdx], self.images[self.imageIdx])))
		for i, view in enumerate(self.miniViews):
			view['view'].setPhoto(QPixmap(os.path.join(self.cfg.imageFolder, self.cfg.views[i], self.images[self.imageIdx])))

	def loadAnnotations(self):
		self.mainView.clearAnnotations()
		r = self.mainView.getPixmap().rect()
		data2d = self.data_pixel.loc[(self.cfg.views[self.viewIdx], self.images[self.imageIdx]), :]
		for j, joint in enumerate(self.cfg.joints):
			d = data2d[joint]
			if d.isna().any():
				self.labelingButtons[j].setText(joint+'*')
				continue
			self.mainView.addAnnotation(QPointF(d['u'] * r.width(), d['v'] * r.height()), self.colors[j], self.radius, joint)
			self.labelingButtons[j].setText(joint)
			if not j in self.displaying:
				self.mainView.hideAnnotation(joint)
		for i, view in enumerate(self.cfg.views):
			self.miniViews[i]['view'].clearAnnotations()
			r = self.miniViews[i]['view'].getPixmap().rect()
			data2d = self.data_pixel.loc[(view, self.images[self.imageIdx]), :]
			for j, joint in enumerate(self.cfg.joints):
				d = data2d[joint]
				if d.isna().any():
					continue
				self.miniViews[i]['view'].addAnnotation(QPointF(d['u']*r.width(), d['v']*r.height()), self.colors[j], self.radius, joint)
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

	def setView(self, index):
		self.viewIdx = index
		self.ui.label.setText('View: %s'%str(self.cfg.views[self.viewIdx]))
		self.mainView.setPhoto(self.miniViews[index]['view'].getPixmap())
		self.mainView.setAnnotations(self.miniViews[index]['view'].getAnnotations())

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
		self.data_pixel.loc[(self.cfg.views[self.viewIdx], self.images[self.imageIdx]), self.cfg.joints[self.jointIdx]] = pos_normalized
		preds3d = self.project_3d()
		if preds3d is not None:
			self.data_3d.loc[self.images[self.imageIdx], self.cfg.joints[self.jointIdx]] = preds3d
			preds2d = self.compute2d(preds3d)
			for i, view in enumerate(self.cfg.views):
				self.data_pixel.loc[(view, self.images[self.imageIdx]), self.cfg.joints[self.jointIdx]] = preds2d[i]
			self.addAnnotations(preds2d)
		else:
			self.mainView.addAnnotation(pos, self.colors[self.jointIdx], self.radius, self.cfg.joints[self.jointIdx])
			self.miniViews[self.viewIdx]['view'].addAnnotation(pos, self.colors[self.jointIdx], self.radius, self.cfg.joints[self.jointIdx])

	def removeAnnotation(self):
		self.labelingButtons[self.jointIdx].setText(self.cfg.joints[self.jointIdx]+'*')
		self.data_pixel.loc[(self.cfg.views[self.viewIdx], self.images[self.imageIdx]), self.cfg.joints[self.jointIdx]] = [np.nan, np.nan]
		self.mainView.removeAnnotation(self.cfg.joints[self.jointIdx])
		self.miniViews[self.viewIdx]['view'].removeAnnotation(self.cfg.joints[self.jointIdx])

	# preds3d is just (x,y,z)
	def compute2d(self, preds3d):
		preds3d_aug = np.concatenate([preds3d, [1]], axis=0)
		A = np.vstack(self.cfg.projectionMatrices)
		preds2d = np.matmul(A, preds3d_aug)
		preds2d = preds2d.reshape([-1, 3])
		preds2d = preds2d[:, :2] / preds2d[:, 2, None]
		return preds2d # num_views x 2

	def addAnnotations(self, preds2d):
		# rescale them to match image dimensions
		r = self.mainView.getPixmap().rect()
		p = QPointF(preds2d[self.viewIdx, 0] * r.width(), preds2d[self.viewIdx, 1] * r.height())
		self.mainView.addAnnotation(p, self.colors[self.jointIdx], self.radius, self.cfg.joints[self.jointIdx])
		for i, view in enumerate(self.miniViews):
			r = view['view'].getPixmap().rect()
			p = QPointF(preds2d[i, 0] * r.width(), preds2d[i, 1] * r.height())
			view['view'].addAnnotation(p, self.colors[self.jointIdx], self.radius, self.cfg.joints[self.jointIdx])

	def hideAnnotations(self, key):
		self.mainView.hideAnnotation(key)
		for view in self.miniViews:
			view['view'].hideAnnotation(key)

	def showAnnotations(self, key):
		self.mainView.showAnnotation(key)
		for view in self.miniViews:
			view['view'].showAnnotation(key)

	# get least squares 3d projection, then correct it to be exactly consistent with our current view
	def project_3d(self):
		# kind of want to solve linear system to get 3D coordinates minimizing l2 error
		# helpful explanation of equation found on pg 5 here: https://hal.inria.fr/inria-00524401/PDF/Sturm-cvpr05.pdf

		preds2d = self.data_pixel.loc[[(view, self.images[self.imageIdx]) for view in self.cfg.views], self.cfg.joints[self.jointIdx]]
		labeledViews = np.arange(len(self.cfg.views))[preds2d.loc[:, 'u'].notna().values]

		if len(labeledViews) <= 1:
			return None

		num_views = len(labeledViews)
		preds2d = preds2d.values[labeledViews, :]
		preds2d = np.concatenate([preds2d, np.ones([num_views, 1])], axis=1)
		mats = np.array(self.cfg.projectionMatrices)[labeledViews]

		A1 = np.vstack(mats)
		A2 = np.zeros([3*num_views, num_views])
		A = np.concatenate([A1, A2], axis=1).astype(np.float)

		updates_rows = np.arange(3*num_views)
		updates_cols = np.repeat(np.arange(num_views)+4, 3)
		A[updates_rows, updates_cols] = -1*preds2d.reshape([3*num_views])

		u, s, vh = np.linalg.svd(A)
		preds3d = vh[-1] # bottom row of V^T is eigenvector of smallest singular value

		# now make our 3d predictions consistent with the current view, possibly at the expense of the others
		# we can do this by subtracting the basis row vectors of our current projection matrix
		for idx, v in enumerate(labeledViews):
			if v == self.viewIdx:
				break
		space = A[3*idx:3*(idx+1), :].T
		Q, _ = np.linalg.qr(space)
		components = np.matmul(Q.T, preds3d)[:,None] * Q.T
		preds3d = preds3d - np.sum(components, axis=0)


		preds3d = preds3d[:3] / preds3d[3] 

		return preds3d

	def skipMissingAny(self):
		cols = [self.cfg.joints[idx] for idx in self.displaying]
		data = self.data_pixel.loc[self.cfg.views[self.viewIdx], cols]
		missing = data.isna().any(axis=1)
		idx = missing[missing].index.get_loc(self.images[self.imageIdx])
		image = missing[missing].index[idx+1]
		idx = missing.index.get_loc(image)
		self.ui.spinBox.setValue(idx)

	def skipMissingAll(self):
		cols = [self.cfg.joints[idx] for idx in self.displaying]
		data = self.data_pixel.loc[self.cfg.views[self.viewIdx], cols]
		missing = data.isna().all(axis=1)
		idx = missing[missing].index.get_loc(self.images[self.imageIdx])
		image = missing[missing].index[idx+1]
		idx = missing.index.get_loc(image)
		self.ui.spinBox.setValue(idx)

	def keyPressEvent(self, event):
		if event.key() == Qt.Key_V:
			self.ui.comboBox.setCurrentIndex((self.viewIdx + 1) % len(self.cfg.views))
		elif event.key() == Qt.Key_F:
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
		pd.to_csv(os.path.join(self.cfg.projectFolder, 'pixel-annotation-data.csv', self.data_pixel))
		pd.to_csv(os.path.join(self.cfg.projectFolder, '3d-annotation-data.csv', self.data_3d))
		super(MultiviewProjectMainWindow, self).closeEvent(event)