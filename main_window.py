"""
主界面模块
实现可拖动的透明 mini 监控窗口
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication, QHBoxLayout
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QFont, QCursor
import utils


class MonitorWindow(QWidget):
    """可拖动的透明监控窗口"""
    
    def __init__(self, taskbar_integration=None):  # 参数改为可选
        super().__init__()
        self.taskbar_integration = taskbar_integration
        
        # 拖动相关
        self.dragging = False
        self.drag_start_pos = QPoint()
        
        # 鼠标穿透状态
        self.mouse_through_enabled = True  # 默认开启穿透
        
        # 窗口基本设置
        self.setup_window()
        
        # UI 组件
        self.setup_ui()
        
        # 样式设置
        self.setup_style()
        
        # 当前数据
        self.current_data = None
        
        # 颜色模式（自动/白色/黑色）
        self.color_mode = "auto"
    
    def setup_window(self):
        """设置窗口属性"""
        # 无边框窗口
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.Tool |  # 不在任务栏显示
            Qt.WindowStaysOnTopHint  # 始终置顶
        )
        
        # 透明背景
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 不获取焦点
        self.setFocusPolicy(Qt.NoFocus)
        
        # 初始大小 - 调整为两列布局，宽度增加
        self.setFixedSize(200, 50)  # 宽度从 180 增加到 200
        
        # 初始位置 - 屏幕中央，用户可以拖动
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center().x() - 100, screen.center().y() - 25)
        
        # 应用鼠标穿透
        if self.taskbar_integration:
            self.taskbar_integration.apply_mouse_through(self)
        
        print("[DEBUG] 可拖动监控窗口已创建")
        print(f"[DEBUG] 初始位置：{self.pos()}")
        print("[提示] 双击窗口可以切换鼠标穿透模式")
        print("[提示] 关闭穿透模式后可以拖动窗口到任务栏")
    
    def setup_ui(self):
        """设置 UI 布局 - 两列并排"""
        # 主布局：水平排列
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(3, 2, 3, 2)
        main_layout.setSpacing(8)  # 两列之间的间距
        
        # 左列：CPU 和 RAM
        left_column = QVBoxLayout()
        left_column.setSpacing(1)
        
        self.cpu_label = QLabel("CPU: --%")
        self.cpu_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.ram_label = QLabel("RAM: --%")
        self.ram_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        left_column.addWidget(self.cpu_label)
        left_column.addWidget(self.ram_label)
        
        # 右列：上传和下载
        right_column = QVBoxLayout()
        right_column.setSpacing(1)
        
        self.upload_label = QLabel("↑ -- B/s")
        self.upload_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.download_label = QLabel("↓ -- B/s")
        self.download_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        right_column.addWidget(self.upload_label)
        right_column.addWidget(self.download_label)
        
        # 添加到主布局
        main_layout.addLayout(left_column, 1)  # 左列
        main_layout.addLayout(right_column, 1)  # 右列
    
    def setup_style(self):
        """设置字体和样式"""
        # 使用等宽字体防止数值变动时文字抖动
        font_family = "Consolas"
        font_size = 8  # 稍微减小字号以适应两列布局
        
        # 根据 DPI 调整字号
        dpi = utils.get_dpi_for_window(int(self.winId()))
        if dpi > 96:
            font_size = int(font_size * (dpi / 96.0))
        
        font = QFont(font_family, font_size)
        font.setStyleHint(QFont.Monospace)
        
        # 应用到所有标签
        for label in [self.cpu_label, self.ram_label, 
                     self.upload_label, self.download_label]:
            label.setFont(font)
            label.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 0.9);
                    background-color: transparent;
                    padding: 0px;
                }
            """)
        
        # 更新穿透状态提示
        self.update_through_indicator()
    
    def update_data(self, data):
        """更新显示数据"""
        self.current_data = data
        
        # 更新 CPU
        cpu_percent = data.get('cpu', 0)
        self.cpu_label.setText(f"CPU: {cpu_percent}%")
        self.cpu_label.setStyleSheet(f"color: {utils.calculate_color_from_percentage(cpu_percent)};")
        
        # 更新 RAM
        ram_percent = data.get('ram', 0)
        self.ram_label.setText(f"RAM: {ram_percent}%")
        self.ram_label.setStyleSheet(f"color: {utils.calculate_color_from_percentage(ram_percent)};")
        
        # 更新网络速度
        upload_speed = data.get('upload', 0)
        download_speed = data.get('download', 0)
        
        self.upload_label.setText(f"↑ {utils.format_bytes(upload_speed)}")
        self.download_label.setText(f"↓ {utils.format_bytes(download_speed)}")
        
        # 网络速度不需要颜色变化
        self.upload_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        self.download_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        
        # 调整窗口大小以适应内容
        self.adjust_size()
        
        print(f"[DEBUG] 数据已更新：CPU={cpu_percent}%, RAM={ram_percent}%")
    
    def set_text_color(self, mode):
        """
        设置文字颜色模式
        mode: "auto" | "white" | "black"
        """
        self.color_mode = mode
        
        if mode == "white":
            color = "rgba(255, 255, 255, 0.9)"
        elif mode == "black":
            color = "rgba(0, 0, 0, 0.9)"
        else:  # auto
            color = "rgba(255, 255, 255, 0.9)"
        
        # 如果不是自动模式，禁用动态颜色变化
        if mode != "auto":
            self.cpu_label.setStyleSheet(f"color: {color};")
            self.ram_label.setStyleSheet(f"color: {color};")
        else:
            # 重新应用自动颜色
            if self.current_data:
                self.update_data(self.current_data)
    
    def adjust_size(self):
        """根据内容调整窗口大小"""
        # 计算左列最大宽度（CPU 和 RAM）
        left_labels = [self.cpu_label, self.ram_label]
        max_left_width = 0
        for label in left_labels:
            fm = label.fontMetrics()
            width = fm.horizontalAdvance(label.text())
            max_left_width = max(max_left_width, width)
        
        # 计算右列最大宽度（上传和下载）
        right_labels = [self.upload_label, self.download_label]
        max_right_width = 0
        for label in right_labels:
            fm = label.fontMetrics()
            width = fm.horizontalAdvance(label.text())
            max_right_width = max(max_right_width, width)
        
        # 总宽度 = 左列 + 右列 + 间距 + 边距
        total_width = max_left_width + max_right_width + 8 + 6  # 8px 间距，6px 边距
        self.setFixedWidth(total_width)
    
    # ========== 拖动功能实现 ==========
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 开始拖动"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖动窗口"""
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_start_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 结束拖动"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            print(f"[提示] 窗口已移动到新位置：{self.pos()}")
    
    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件 - 切换穿透模式"""
        # 切换穿透状态
        self.mouse_through_enabled = not self.mouse_through_enabled
        
        if self.mouse_through_enabled:
            # 开启穿透
            if self.taskbar_integration:
                self.taskbar_integration.apply_mouse_through(self)
            print("[✓] 已开启鼠标穿透模式 - 窗口无法被点击")
        else:
            # 关闭穿透
            self.disable_mouse_through()
            print("[✓] 已关闭鼠标穿透模式 - 现在可以拖动窗口了")
            print("[提示] 再次双击窗口将重新开启穿透模式")
    
    def disable_mouse_through(self):
        """禁用鼠标穿透"""
        try:
            import ctypes
            from ctypes import windll
            
            hwnd = int(self.winId())
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_LAYERED = 0x00080000
            
            # 获取当前扩展样式
            ex_style = windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
            
            # 移除 TRANSPARENT 样式，保留 LAYERED（用于透明）
            new_style = (ex_style & ~WS_EX_TRANSPARENT) | WS_EX_LAYERED
            
            # 设置扩展样式
            windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, new_style)
        except Exception as e:
            print(f"[警告] 禁用穿透失败：{e}")
    
    def toggle_mouse_through_from_menu(self):
        """从托盘菜单切换穿透模式"""
        self.mouse_through_enabled = not self.mouse_through_enabled
        
        if self.mouse_through_enabled:
            # 开启穿透
            if self.taskbar_integration:
                self.taskbar_integration.apply_mouse_through(self)
            print("[✓] 已开启鼠标穿透模式 - 窗口无法被点击")
        else:
            # 关闭穿透
            self.disable_mouse_through()
            print("[✓] 已关闭鼠标穿透模式 - 现在可以拖动窗口了")
        
        # 更新视觉提示
        self.update_through_indicator()
    
    def update_through_indicator(self):
        """更新鼠标穿透状态指示器"""
        if not self.mouse_through_enabled:
            # 关闭穿透时，给窗口加一个边框提示
            self.setStyleSheet("""
                MonitorWindow {
                    border: 1px solid rgba(0, 255, 0, 100);  # 绿色半透明边框
                }
            """)
            print("[视觉提示] 窗口显示绿色边框 - 可以拖动")
        else:
            # 开启穿透时，移除边框
            self.setStyleSheet("")
