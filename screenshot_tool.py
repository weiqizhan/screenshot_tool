from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, QPoint,QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QImage
from PIL import ImageGrab
from float_image import FloatImage

class ScreenshotTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setMouseTracking(True)
        self.origin = QPoint()
        self.end = QPoint()
        self.drawing = False
        self.screen_pixmap = None

    def showFullScreen(self):
        try:
            pil_img = ImageGrab.grab()
            self.screen_pixmap = self.pil2pixmap(pil_img)
        except Exception as e:
            print(f"[showFullScreen] PIL截图失败: {e}")
            self.screen_pixmap = None
        super().showFullScreen()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

    def pil2pixmap(self, pil_img):
        if pil_img.mode == "RGB":
            qimage = QImage(pil_img.tobytes("raw", "RGB"), pil_img.width, pil_img.height, QImage.Format.Format_RGB888)
        elif pil_img.mode == "RGBA":
            qimage = QImage(pil_img.tobytes("raw", "RGBA"), pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)
        else:
            pil_img = pil_img.convert("RGBA")
            qimage = QImage(pil_img.tobytes("raw", "RGBA"), pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qimage)

    def paintEvent(self, event):
        painter = QPainter(self)

        # 背景图
        if self.screen_pixmap and not self.screen_pixmap.isNull():
            painter.drawPixmap(0, 0, self.screen_pixmap)
        else:
            painter.fillRect(self.rect(), QColor(200, 50, 50))

        # 半透明遮罩
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        # 提示或选区
        if self.origin.isNull() or self.end.isNull():
            # 显示操作提示
            hint_rect = QRect(self.width()//2 - 180, self.height()//2 - 40, 360, 80)
            painter.setPen(QPen(QColor(255, 255, 255, 200), 2))
            painter.setBrush(QColor(255, 255, 255, 40))
            painter.drawRoundedRect(hint_rect, 10, 10)
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            font = painter.font()
            font.setPointSize(14)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(hint_rect, Qt.AlignmentFlag.AlignCenter, "✂️ 拖动鼠标选择截图区域\n按 ESC 取消")
        else:
            rect = QRect(self.origin, self.end).normalized()
            # 挖空选区
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, QColor(0, 0, 0, 0))
            # 红色边框
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(QPen(Qt.GlobalColor.red, 2))
            painter.drawRect(rect)

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

    def capture(self, rect):
        # 1. 隐藏窗口，避免截图中包含红色边框和遮罩
        self.hide()
        # 2. 让 Qt 处理完隐藏事件，确保屏幕刷新
        QApplication.processEvents()
        
        # 3. 短暂延时（50ms），进一步保证窗口完全消失（可选）
        def do_capture():
            bbox = (rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height())
            img = ImageGrab.grab(bbox)
            self.float_window = FloatImage(img)
            self.float_window.show()
            self.close()
        
        QTimer.singleShot(50, do_capture)