import sys, os
import keyboarded as keyboard
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter
from screenshot_tool import ScreenshotTool


def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和 PyInstaller 打包后的环境"""
    try:
        # PyInstaller 创建的临时文件夹
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# 信号发射器，用于跨线程安全地调用主线程
class SignalEmitter(QObject):
    trigger_screenshot = pyqtSignal()
    trigger_quit = pyqtSignal()


def do_quit():
    QApplication.quit()


def quit_app():
    emitter.trigger_quit.emit()


# 创建系统托盘图标
def create_tray_icon(app):
    # 使用默认图标（如果没有自定义图标，Qt 会提供一个默认样式）
    tray_icon = QSystemTrayIcon()
    icon_path = resource_path("assets/sst.png")
    if os.path.exists(icon_path):
        tray_icon.setIcon(QIcon(icon_path))
    else:
        # 如果找不到文件，回退到绘制内置图标（备用方案）
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(0, 120, 215))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 28, 28)
        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(14)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "S")
        painter.end()
        tray_icon.setIcon(QIcon(pixmap))
    tray_icon.setToolTip("sst 截图工具")

    # 创建右键菜单
    menu = QMenu()

    action1 = menu.addAction("📷 截图 (Ctrl+1)")
    action1.triggered.connect(do_screenshot)

    menu.addSeparator()

    action2 = menu.addAction("❌ 退出 (Ctrl+2)")
    action2.triggered.connect(do_quit)

    tray_icon.setContextMenu(menu)
    tray_icon.show()

    # 左键点击托盘图标也可触发截图（可选）
    tray_icon.activated.connect(lambda reason: do_screenshot() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)

    return tray_icon


def start_screenshot():
    # 通过信号发射到主线程
    emitter.trigger_screenshot.emit()


def do_screenshot():
    global tool
    tool = ScreenshotTool()
    tool.showFullScreen()


def send_qt_notification(tray_icon):  # 使用指南弹窗通知
    tray_icon.showMessage("⭐使用指南⭐", "Ctrl+1 开始截图...\nCtrl+2 退出程序...", QSystemTrayIcon.MessageIcon.Information, 2000)  # 标题  # 消息内容  # 图标类型  # 显示时间（毫秒）


def main():
    global app
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # 创建信号发射器，并将信号连接到截图槽函数
    global emitter  # 必须保持引用，防止被垃圾回收
    emitter = SignalEmitter()
    emitter.trigger_screenshot.connect(do_screenshot, Qt.ConnectionType.QueuedConnection)
    emitter.trigger_quit.connect(do_quit, Qt.ConnectionType.QueuedConnection)

    # 创建系统托盘
    tray = create_tray_icon(app)

    QTimer.singleShot(1000, lambda: send_qt_notification(tray))

    # 注册热键，suppress=True 阻止按键传递到其他应用（避免误触 Ctrl+S）
    keyboard.add_hotkey("ctrl+1", start_screenshot, suppress=True)
    keyboard.add_hotkey("ctrl+2", quit_app, suppress=True)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
