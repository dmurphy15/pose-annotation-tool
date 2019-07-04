from PySide2.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame, QGraphicsItem
from PySide2.QtCore import Signal, QPoint, QPointF, Qt, QRectF, QEvent, QSize
from PySide2.QtGui import QBrush, QColor, QPixmap, QPainter

# based on https://stackoverflow.com/questions/35508711/how-to-enable-pan-and-zoom-in-a-qgraphicsview
class MainImageView(QGraphicsView):
	photoClicked = Signal(QPointF)
	photoRightClicked = Signal()

	def __init__(self, parent):
		super(MainImageView, self).__init__(parent)
		self._zoom = 0
		self._empty = True
		self._scene = QGraphicsScene(self)
		self._photo = QGraphicsPixmapItem()
		self._scene.addItem(self._photo)
		self.setScene(self._scene)
		self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
		self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
		self.setFrameShape(QFrame.NoFrame)
		self.setDragMode(QGraphicsView.ScrollHandDrag)
		self.viewport().setCursor(Qt.CrossCursor)

		self._annotations = {}

		self._mousePressed = False

	def hasPhoto(self):
		return not self._empty

	def resizeEvent(self, e):
		self.fitInView()

	def fitInView(self):
		rect = QRectF(self._photo.pixmap().rect())
		if not rect.isNull():
			self.setSceneRect(rect)
			if self.hasPhoto():
				unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
				self.scale(1 / unity.width(), 1 / unity.height())
				viewrect = self.viewport().rect()
				scenerect = self.transform().mapRect(rect)
				factor = min(viewrect.width() / scenerect.width(),
							 viewrect.height() / scenerect.height())
				self.scale(factor, factor)
			self._zoom = 0 

	def setPhoto(self, pixmap=None):
		self._zoom = 0
		if pixmap and not pixmap.isNull():
			self._empty = False
			self._photo.setPixmap(pixmap)
		else:
			self._empty = True
			self._photo.setPixmap(QPixmap())
		self.fitInView()

	def addAnnotation(self, position, color, radius, key):
		if key in self._annotations:
			self._scene.removeItem(self._annotations[key])
		d = DotItem(position, color, radius)
		self._annotations[key] = d
		self._scene.addItem(d)

	def removeAnnotation(self, key):
		self._scene.removeItem(self._annotations.pop(key))

	def hideAnnotation(self, key):
		if key in self._annotations:
			self._scene.removeItem(self._annotations[key])

	def showAnnotation(self, key):
		if key in self._annotations:
			self._scene.addItem(self._annotations[key])


	def wheelEvent(self, event):
		if self.hasPhoto():
			if event.angleDelta().y() > 0:
				factor = 1.25
				self._zoom += 1
			else:
				factor = 0.8
				self._zoom -= 1
			if self._zoom > 0:
				self.scale(factor, factor)
			elif self._zoom == 0:
				self.fitInView()
			else:
				self._zoom = 0

	def mousePressEvent(self, event):
		super(MainImageView, self).mousePressEvent(event)
		if event.button == Qt.RightButton:
			self.photoRightClicked.emit()
			return
		if self._photo.isUnderMouse():
			self._mousePressed = True

	def mouseMoveEvent(self, event):
		super(MainImageView, self).mouseMoveEvent(event)
		if self._mousePressed:
			self._mousePressed = False
		

	def mouseReleaseEvent(self, event):
		super(MainImageView, self).mouseReleaseEvent(event)
		self.viewport().setCursor(Qt.CrossCursor)
		if self._mousePressed:
			self._mousePressed = False
			self.photoClicked.emit(self.mapToScene(event.pos()))

	def getAnnotations(self):
		return { key: val.copy() for key, val in self._annotations.items() }

	def setAnnotations(self, annotations):
		self.clearAnnotations()
		self._annotations = annotations
		for a in self._annotations.values():
			self._scene.addItem(a)

	def clearAnnotations(self):
		for a in self._annotations.values():
			self._scene.removeItem(a)
		self._annotations = {}

	def getPixmap(self):
		return self._photo.pixmap()

class MiniImageView(QGraphicsView):

	def __init__(self, parent):
		super(MiniImageView, self).__init__(parent)
		self._empty = True
		self._scene = QGraphicsScene(self)
		self._photo = QGraphicsPixmapItem()
		self._scene.addItem(self._photo)
		self.setScene(self._scene)
		self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
		self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
		self.setFrameShape(QFrame.NoFrame)

		self._annotations = {}

	def hasPhoto(self):
		return not self._empty

	def resizeEvent(self, e):
		self.fitInView()

	def fitInView(self):
		rect = QRectF(self._photo.pixmap().rect())
		if not rect.isNull():
			self.setSceneRect(rect)
			if self.hasPhoto():
				unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
				self.scale(1 / unity.width(), 1 / unity.height())
				viewrect = self.viewport().rect()
				scenerect = self.transform().mapRect(rect)
				factor = min(viewrect.width() / scenerect.width(),
							 viewrect.height() / scenerect.height())
				self.scale(factor, factor)

	def setPhoto(self, pixmap=None):
		# self._zoom = 0
		if pixmap and not pixmap.isNull():
			self._empty = False 
			# self.setDragMode(QGraphicsView.ScrollHandDrag)
			self._photo.setPixmap(pixmap)
		else:
			self._empty = True
			# self.setDragMode(QGraphicsView.NoDrag)
			self._photo.setPixmap(QPixmap())
		self.fitInView()

	def addAnnotation(self, position, color, radius, key):
		if key in self._annotations:
			self._scene.removeItem(self._annotations[key])
		d = DotItem(position, color, radius)
		self._annotations[key] = d
		self._scene.addItem(d)

	def removeAnnotation(self, key):
		self._scene.removeItem(self._annotations.pop(key))

	def hideAnnotation(self, key):
		if key in self._annotations:
			self._scene.removeItem(self._annotations[key])

	def showAnnotation(self, key):
		if key in self._annotations:
			self._scene.addItem(self._annotations[key])

	def getAnnotations(self):
		return { key: val.copy() for key, val in self._annotations.items() }

	def setAnnotations(self, annotations):
		self.clearAnnotations()
		self._annotations = annotations
		for a in self._annotations.values():
			self._scene.addItem(a)

	def clearAnnotations(self):
		for a in self._annotations.values():
			self._scene.removeItem(a)
		self._annotations = {}

	def getPixmap(self):
		return self._photo.pixmap()

class DotItem(QGraphicsItem):
	def __init__(self, point, color, radius):
		super(DotItem, self).__init__()
		self.point = point
		self.color = color
		self.radius = radius

		self.rect = QRectF(point - QPointF(radius, radius), 2*QSize(radius, radius))

	def boundingRect(self):
		return self.rect

	def paint(self, painter, option, widget=None):
		painter.setPen(self.color)
		painter.setBrush(self.color)	
		painter.drawEllipse(self.point, self.radius, self.radius)

	def copy(self):
		return DotItem(self.point, self.color, self.radius)

# class Window(QtWidgets.QWidget):
#     def __init__(self):
#         super(Window, self).__init__()
#         self.viewer = PhotoViewer(self)
#         # 'Load image' button
#         self.btnLoad = QtWidgets.QToolButton(self)
#         self.btnLoad.setText('Load image')
#         self.btnLoad.clicked.connect(self.loadImage)
#         # Button to change from drag/pan to getting pixel info
#         self.btnPixInfo = QtWidgets.QToolButton(self)
#         self.btnPixInfo.setText('Enter pixel info mode')
#         self.btnPixInfo.clicked.connect(self.pixInfo)
#         self.editPixInfo = QtWidgets.QLineEdit(self)
#         self.editPixInfo.setReadOnly(True)
#         self.viewer.photoClicked.connect(self.photoClicked)
#         # Arrange layout
#         VBlayout = QtWidgets.QVBoxLayout(self)
#         VBlayout.addWidget(self.viewer)
#         HBlayout = QtWidgets.QHBoxLayout()
#         HBlayout.setAlignment(QtCore.Qt.AlignLeft)
#         HBlayout.addWidget(self.btnLoad)
#         HBlayout.addWidget(self.btnPixInfo)
#         HBlayout.addWidget(self.editPixInfo)
#         VBlayout.addLayout(HBlayout)

#     def loadImage(self):
#         self.viewer.setPhoto(QPixmap('image.jpg'))

#     def pixInfo(self):
#         self.viewer.toggleDragMode()

#     def photoClicked(self, pos):
#         if self.viewer.dragMode()  == QtWidgets.QGraphicsView.NoDrag:
#             self.editPixInfo.setText('%d, %d' % (pos.x(), pos.y()))