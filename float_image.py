from PyQt6.QtWidgets import (QLabel, QMenu, QFileDialog, QApplication,
                             QWidget, QHBoxLayout, QPushButton, QColorDialog, QInputDialog)
from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QPixmap, QImage, QAction, QPainter, QPen, QColor

class ToolBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowFlags(Qt.WindowType.ToolTip)
        self.setStyleSheet("background: rgba(240,240,240,200); border: 1px solid gray; border-radius: 5px;")
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        self.btn_pen = QPushButton("✏️画笔")
        self.btn_rect = QPushButton("⬜矩形")
        self.btn_ellipse = QPushButton("⚪椭圆")
        self.btn_color = QPushButton("🎨颜色")
        self.btn_width = QPushButton("📏线宽")
        self.btn_undo = QPushButton("↩️撤销")
        self.btn_clear = QPushButton("🗑️清空")
        self.btn_exit = QPushButton("❌退出标注")

        for btn in [self.btn_pen, self.btn_rect, self.btn_ellipse, self.btn_color, 
                    self.btn_width, self.btn_undo, self.btn_clear, self.btn_exit]:  
            btn.setFixedHeight(30)
            layout.addWidget(btn)

        self.setLayout(layout)
        self.btn_pen.clicked.connect(lambda: parent.set_annotation_mode('pen'))
        self.btn_rect.clicked.connect(lambda: parent.set_annotation_mode('rectangle'))
        self.btn_ellipse.clicked.connect(lambda: parent.set_annotation_mode('ellipse'))
        self.btn_color.clicked.connect(parent.choose_color)
        self.btn_width.clicked.connect(parent.choose_width)
        self.btn_undo.clicked.connect(parent.undo)
        self.btn_clear.clicked.connect(parent.clear_annotations)
        self.btn_exit.clicked.connect(parent.exit_annotation_mode)
    
    def update_tool_style(self, mode):
        self.btn_pen.setStyleSheet("background: lightblue;" if mode == 'pen' else "")
        self.btn_rect.setStyleSheet("background: lightblue;" if mode == 'rectangle' else "")
        self.btn_ellipse.setStyleSheet("background: lightblue;" if mode == 'ellipse' else "")


class FloatImage(QLabel):
    def __init__(self, pil_image):
        super().__init__()
        self.pil_image = pil_image
        self.original_pixmap = self.pil2pixmap(pil_image)
        self.setPixmap(self.original_pixmap)
        self.resize(pil_image.width, pil_image.height)

        # 窗口设置
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: white; border: 1px solid gray;")
        self.setMouseTracking(True)

        # 拖动相关
        self.drag_pos = QPoint()
        self.dragging = False

        # 标注模式相关
        self.annotation_mode = False          # 是否处于标注模式
        self.current_tool = 'pen'             # pen, rectangle, ellipse
        self.pen_color = QColor(Qt.GlobalColor.red)
        self.pen_width = 2
        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.shapes = []                      # 存储标注元素
        self.current_shape = None             # 正在绘制的临时形状

        # 工具栏
        self.toolbar = ToolBar(self)
        self.toolbar.hide()

    # ---------- 辅助函数 ----------
    def pil2pixmap(self, pil_img):
        # 确保图像模式为 RGBA 或 RGB
        if pil_img.mode == "RGB":
            qimage = QImage(pil_img.tobytes("raw", "RGB"), pil_img.width, pil_img.height, pil_img.width * 3, QImage.Format.Format_RGB888)
        elif pil_img.mode == "RGBA":
            qimage = QImage(pil_img.tobytes("raw", "RGBA"), pil_img.width, pil_img.height, pil_img.width * 4, QImage.Format.Format_RGBA8888)
        else:
            pil_img = pil_img.convert("RGBA")
            qimage = QImage(pil_img.tobytes("raw", "RGBA"), pil_img.width, pil_img.height, pil_img.width * 4, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qimage)

    def update_display(self):
        """将标注绘制到原始图片上并更新显示"""
        pixmap = self.original_pixmap.copy()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制已保存的形状
        for shape in self.shapes:
            pen = QPen(shape['color'], shape['width'])
            painter.setPen(pen)
            if shape['type'] == 'pen':
                points = shape['points']
                for i in range(len(points) - 1):
                    painter.drawLine(points[i], points[i + 1])
            elif shape['type'] == 'rectangle':
                painter.drawRect(shape['rect'])
            elif shape['type'] == 'ellipse':
                painter.drawEllipse(shape['rect'])

        # 绘制当前正在进行的形状
        if self.drawing and self.current_shape:
            pen = QPen(self.pen_color, self.pen_width)
            painter.setPen(pen)
            if self.current_tool == 'pen':
                points = self.current_shape['points']
                for i in range(len(points) - 1):
                    painter.drawLine(points[i], points[i + 1])
            elif self.current_tool in ('rectangle', 'ellipse'):
                rect = QRect(self.start_point, self.end_point).normalized()
                if self.current_tool == 'rectangle':
                    painter.drawRect(rect)
                else:
                    painter.drawEllipse(rect)

        painter.end()
        self.setPixmap(pixmap)

    # ---------- 标注模式切换 ----------
    def enter_annotation_mode(self):
        self.annotation_mode = True
        self.setStyleSheet("background: white; border: 2px dashed blue;")
        self.toolbar.show()
        self.toolbar.update_tool_style(self.current_tool)
        # 将工具栏放置在窗口下方
        self.toolbar.move(self.x(), self.y() + self.height() + 5)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def exit_annotation_mode(self):
        self.annotation_mode = False
        self.setStyleSheet("background: white; border: 1px solid gray;")
        self.toolbar.hide()
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.drawing = False
        self.current_shape = None

    def set_annotation_mode(self, tool):
        self.current_tool = tool
        self.toolbar.update_tool_style(tool)

    def choose_color(self):
        color = QColorDialog.getColor(self.pen_color, self, "选择颜色")
        if color.isValid():
            self.pen_color = color

    def choose_width(self):
        width, ok = QInputDialog.getInt(self, "线宽", "请输入线宽 (1-20):", self.pen_width, 1, 20)
        if ok:
            self.pen_width = width
    
    def undo(self):
        """撤销上一次标注"""
        if self.shapes:
            self.shapes.pop()
            self.update_display()

    def clear_annotations(self):
        """清空所有标注"""
        self.shapes.clear()
        self.update_display()

    # ---------- 鼠标事件 ----------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.annotation_mode:
                # 标注模式：开始绘制
                self.drawing = True
                pos = event.pos()
                self.start_point = pos
                self.end_point = pos
                if self.current_tool == 'pen':
                    self.current_shape = {
                        'type': 'pen',
                        'color': self.pen_color,
                        'width': self.pen_width,
                        'points': [pos]
                    }
            else:
                # 普通模式：开始拖动
                self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                self.dragging = True
        elif event.button() == Qt.MouseButton.RightButton:
            if self.annotation_mode:
                # 标注模式下右键退出标注
                self.exit_annotation_mode()
            else:
                self.show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self.annotation_mode and self.drawing:
            pos = event.pos()
            if self.current_tool == 'pen':
                if self.current_shape:
                    self.current_shape['points'].append(pos)
            else:
                self.end_point = pos
            self.update_display()
        elif not self.annotation_mode and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.annotation_mode and self.drawing:
                pos = event.pos()
                if self.current_tool == 'pen':
                    if self.current_shape and len(self.current_shape['points']) > 1:
                        self.shapes.append(self.current_shape)
                    self.current_shape = None
                else:
                    self.end_point = pos
                    rect = QRect(self.start_point, self.end_point).normalized()
                    if rect.width() > 2 and rect.height() > 2:
                        shape = {
                            'type': self.current_tool,
                            'color': self.pen_color,
                            'width': self.pen_width,
                            'rect': rect
                        }
                        self.shapes.append(shape)
                self.drawing = False
                self.update_display()
            else:
                self.dragging = False

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.annotation_mode:
            self.close()

    # ---------- 右键菜单 ----------
    def show_context_menu(self, pos):
        menu = QMenu()
        annotate_action = QAction("✏️ 标注模式", self)
        annotate_action.triggered.connect(self.enter_annotation_mode)
        save_action = QAction("💾 保存", self)
        save_action.triggered.connect(self.save_image)
        copy_action = QAction("📋 复制到剪贴板", self)
        copy_action.triggered.connect(self.copy_to_clipboard)
        close_action = QAction("❌ 关闭", self)
        close_action.triggered.connect(self.close)

        menu.addAction(annotate_action)
        menu.addSeparator()
        menu.addAction(save_action)
        menu.addAction(copy_action)
        menu.addSeparator()
        menu.addAction(close_action)
        menu.exec(pos)

    def save_image(self):
        # 保存当前显示的图片（包含标注）
        path, _ = QFileDialog.getSaveFileName(self, "保存截图", "", "PNG (*.png);;JPEG (*.jpg *.jpeg)")
        if path:
            current_pixmap = self.pixmap()
            if current_pixmap:
                current_pixmap.save(path)

    def copy_to_clipboard(self):
        current_pixmap = self.pixmap()
        if current_pixmap:
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(current_pixmap)

    # ---------- 窗口移动时工具栏跟随 ----------
    def moveEvent(self, event):
        if self.toolbar.isVisible():
            self.toolbar.move(self.x(), self.y() + self.height() + 5)
        super().moveEvent(event)