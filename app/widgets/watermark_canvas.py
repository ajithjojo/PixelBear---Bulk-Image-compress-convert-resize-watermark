import io

from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPixmap, QPen, QColor, QBrush, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem,
)
from PIL import Image

MAX_SOURCE_SIZE = 1024


def _pil_to_qpixmap(pil_image):
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    pix = QPixmap()
    pix.loadFromData(buf.getvalue())
    return pix


class WatermarkItem(QGraphicsPixmapItem):
    HANDLE_SIZE = 10
    MIN_SIZE = 20

    def __init__(self, source_path, source_pixmap, display_w, display_h, canvas):
        display_pix = source_pixmap.scaled(
            display_w, display_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        super().__init__(display_pix)
        self.source_path = source_path
        self._source_pixmap = source_pixmap
        self._canvas = canvas
        self._aspect = source_pixmap.width() / max(1, source_pixmap.height())
        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self._resizing = False
        self._resize_corner = -1
        self._drag_start_scene = None
        self._drag_start_rect = None
        self._drag_start_pos = None

    def boundingRect(self):
        r = QRectF(0, 0, self.pixmap().width(), self.pixmap().height())
        if self.isSelected():
            s = self.HANDLE_SIZE / 2
            return r.adjusted(-s, -s, s, s)
        return r

    def shape(self):
        path = QPainterPath()
        path.addRect(QRectF(0, 0, self.pixmap().width(), self.pixmap().height()))
        if self.isSelected():
            for rect in self._handle_rects():
                path.addRect(rect)
        return path

    def paint(self, painter, option, widget=None):
        painter.drawPixmap(0, 0, self.pixmap())
        if self.isSelected():
            r = QRectF(0, 0, self.pixmap().width(), self.pixmap().height())
            painter.setPen(QPen(QColor("#818cf8"), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(r)
            painter.setBrush(QBrush(QColor("#818cf8")))
            painter.setPen(QPen(QColor("#ffffff"), 1))
            for rect in self._handle_rects():
                painter.drawRect(rect)

    def _handle_rects(self):
        pw, ph = self.pixmap().width(), self.pixmap().height()
        s = self.HANDLE_SIZE
        hs = s / 2
        return [
            QRectF(-hs, -hs, s, s),
            QRectF(pw - hs, -hs, s, s),
            QRectF(-hs, ph - hs, s, s),
            QRectF(pw - hs, ph - hs, s, s),
        ]

    def _corner_at(self, pos):
        for i, rect in enumerate(self._handle_rects()):
            if rect.contains(pos):
                return i
        return -1

    def hoverMoveEvent(self, event):
        if self.isSelected():
            c = self._corner_at(event.pos())
            if c in (0, 3):
                self.setCursor(Qt.SizeFDiagCursor)
            elif c in (1, 2):
                self.setCursor(Qt.SizeBDiagCursor)
            else:
                self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.OpenHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.isSelected():
            c = self._corner_at(event.pos())
            if c >= 0:
                self._resizing = True
                self._resize_corner = c
                self._drag_start_scene = event.scenePos()
                self._drag_start_rect = QRectF(
                    0, 0, self.pixmap().width(), self.pixmap().height()
                )
                self._drag_start_pos = self.pos()
                event.accept()
                return
        self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing:
            self._do_resize(event.scenePos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._resizing:
            self._resizing = False
            self._canvas.itemsChanged.emit()
            event.accept()
            return
        self.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)
        self._canvas.itemsChanged.emit()

    def _do_resize(self, scene_pos):
        delta = scene_pos - self._drag_start_scene
        r = self._drag_start_rect
        pos = self._drag_start_pos
        corner = self._resize_corner

        if corner == 3:
            new_w = max(self.MIN_SIZE, r.width() + delta.x())
            new_x, new_y = pos.x(), pos.y()
        elif corner == 0:
            new_w = max(self.MIN_SIZE, r.width() - delta.x())
            new_h = new_w / self._aspect
            new_x = pos.x() + r.width() - new_w
            new_y = pos.y() + r.height() - new_h
        elif corner == 1:
            new_w = max(self.MIN_SIZE, r.width() + delta.x())
            new_h = new_w / self._aspect
            new_x = pos.x()
            new_y = pos.y() + r.height() - new_h
        elif corner == 2:
            new_w = max(self.MIN_SIZE, r.width() - delta.x())
            new_h = new_w / self._aspect
            new_x = pos.x() + r.width() - new_w
            new_y = pos.y()
        else:
            return

        new_h = new_w / self._aspect
        scaled = self._source_pixmap.scaled(
            int(new_w), int(new_h), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.prepareGeometryChange()
        self.setPixmap(scaled)
        self.setPos(new_x, new_y)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self._canvas.itemsChanged.emit()
        return super().itemChange(change, value)

    def get_placement(self, scene_w, scene_h):
        pos = self.pos()
        pix = self.pixmap()
        return {
            "path": self.source_path,
            "x_frac": pos.x() / max(1, scene_w),
            "y_frac": pos.y() / max(1, scene_h),
            "w_frac": pix.width() / max(1, scene_w),
        }


class WatermarkCanvas(QGraphicsView):
    itemsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setAlignment(Qt.AlignCenter)
        self.setObjectName("watermarkCanvas")
        self.setStyleSheet(
            "QGraphicsView#watermarkCanvas {"
            "  background: #060a16;"
            "  border: 1px solid #1e2740;"
            "  border-radius: 10px;"
            "}"
        )
        self._bg_item = None
        self._scene_w = 0
        self._scene_h = 0
        self._watermark_items: list[WatermarkItem] = []

    def set_base_image(self, pil_rgba):
        view_w = max(320, self.viewport().width() - 4)
        view_h = max(240, self.viewport().height() - 4)
        ratio = min(view_w / pil_rgba.width, view_h / pil_rgba.height)
        new_w = max(1, int(pil_rgba.width * ratio))
        new_h = max(1, int(pil_rgba.height * ratio))
        resized = pil_rgba.resize((new_w, new_h), Image.LANCZOS)
        pix = _pil_to_qpixmap(resized)

        self._scene_w = new_w
        self._scene_h = new_h
        self._scene.setSceneRect(0, 0, new_w, new_h)

        if self._bg_item:
            self._scene.removeItem(self._bg_item)
        self._bg_item = self._scene.addPixmap(pix)
        self._bg_item.setZValue(-1000)
        self.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)

    def clear_base(self):
        if self._bg_item:
            self._scene.removeItem(self._bg_item)
            self._bg_item = None
        self._scene_w = 0
        self._scene_h = 0

    def add_watermark(self, path):
        if self._scene_w < 1:
            return None
        try:
            with Image.open(path) as wm:
                wm_rgba = wm.convert("RGBA")
                if wm_rgba.width > MAX_SOURCE_SIZE:
                    r = MAX_SOURCE_SIZE / wm_rgba.width
                    wm_rgba = wm_rgba.resize(
                        (MAX_SOURCE_SIZE, max(1, int(wm_rgba.height * r))), Image.LANCZOS
                    )
                source_pix = _pil_to_qpixmap(wm_rgba)
        except Exception:
            return None

        target_w = max(30, int(self._scene_w * 0.25))
        target_h = max(30, int(target_w / max(1, source_pix.width()) * source_pix.height()))

        item = WatermarkItem(path, source_pix, target_w, target_h, self)
        offset = len(self._watermark_items) * 15
        x = (self._scene_w - target_w) / 2 + offset
        y = (self._scene_h - target_h) / 2 + offset
        item.setPos(x, y)
        item.setZValue(len(self._watermark_items))
        self._scene.addItem(item)
        self._watermark_items.append(item)
        self.itemsChanged.emit()
        return item

    def remove_selected(self):
        removed = [i for i in self._watermark_items if i.isSelected()]
        for item in removed:
            self._scene.removeItem(item)
            self._watermark_items.remove(item)
        if removed:
            self.itemsChanged.emit()
        return len(removed)

    def clear_watermarks(self):
        for item in self._watermark_items:
            self._scene.removeItem(item)
        self._watermark_items.clear()
        self.itemsChanged.emit()

    def get_placements(self):
        return [
            item.get_placement(self._scene_w, self._scene_h)
            for item in self._watermark_items
        ]

    def watermark_count(self):
        return len(self._watermark_items)

    def set_items_opacity(self, pct):
        for item in self._watermark_items:
            item.setOpacity(pct / 100.0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._bg_item:
            self.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.remove_selected()
        else:
            super().keyPressEvent(event)
