from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QImage
from PIL import ImageGrab
from float_image import FloatImage


class ScreenshotTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setMouseTracking(True)
        self.origin = QPoint()
        self.end = QPoint()
        self.drawing = False
        self.full_pil_image = None
        self.screen_pixmap = None

    def showFullScreen(self):
        try:
            self.full_pil_image = ImageGrab.grab()
        except Exception as e:
            print(f"[showFullScreen] PIL截图失败: {e}")
            self.screen_pixmap = None
        super().showFullScreen()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

    def paintEvent(self, event):
        painter = QPainter(self)
        # 背景图
        painter.drawImage(self.rect(), QImage(self.full_pil_image.tobytes("raw", "RGB"), self.full_pil_image.width, self.full_pil_image.height, QImage.Format.Format_RGB888))

        # 如果有选区，绘制红色选框
        if not self.origin.isNull() and not self.end.isNull():
            rect = QRect(self.origin, self.end).normalized()
            painter.setPen(QPen(Qt.GlobalColor.red, 2))
            painter.drawRect(rect)
        else:
            # 未开始选区时，显示提示文字（可选）
            painter.setPen(QColor(255, 255, 255, 200))
            font = painter.font()
            font.setPointSize(14)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "拖动鼠标选择截图区域，双击截图全图")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.pos()
            self.end = event.pos()
            self.drawing = True

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
            self.end = event.pos()
            rect = QRect(self.origin, self.end).normalized()
            if rect.width() > 5 and rect.height() > 5:
                self.capture(rect)
                self.close()
            else:
                print("[选区] 选区太小，请重新拖拽")
                self.origin = QPoint()
                self.end = QPoint()
                self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            print("[取消] 用户按下 ESC，关闭窗口")
            self.close()
        else:
            super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 双击直接截取全屏
            full_rect = QRect(0, 0, self.width(), self.height())
            self.capture(full_rect)

    def capture(self, rect):
        try:
            if self.full_pil_image:
                # 直接从已有的全屏截图中裁剪
                cropped = self.full_pil_image.crop((rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height()))
                print(f"裁剪后尺寸: {cropped.size}")
                self.float_window = FloatImage(cropped)
                self.float_window.show()
        except Exception as e:
            print(f"[截图异常] {e}")
        finally:
            self.close()
