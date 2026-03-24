"""
系统托盘管理模块
负责托盘图标、右键菜单、Dashboard 显示等交互功能
"""
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PySide6.QtCore import Signal, Qt, QObject


class SystemTrayManager(QObject):
    """系统托盘管理器"""
    
    # 信号：显示 Dashboard
    show_dashboard = Signal()
    # 信号：切换鼠标穿透模式
    toggle_mouse_through = Signal()
    # 信号：切换网卡
    switch_nic = Signal(str)  # 网卡名称
    
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.tray_icon = None
        self.context_menu = None
        self.dashboard_callback = None
        self.mouse_through_action = None  # 穿透模式菜单项
        self.nic_menu = None  # 网卡选择子菜单
        
        # 创建托盘图标
        self.setup_tray_icon()
        
        # 创建右键菜单
        self.setup_context_menu()
    
    def create_icon_pixmap(self):
        """创建程序图标（像素画）"""
        # 创建一个简单的监控图标
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制一个绿色的监控条形状
        painter.setBrush(QColor(76, 175, 80))  # 绿色
        painter.setPen(Qt.NoPen)
        
        # 底部矩形
        painter.drawRect(4, 20, 24, 8)
        
        # 三个柱状图
        painter.drawRect(6, 14, 5, 6)
        painter.drawRect(13, 10, 5, 10)
        painter.drawRect(20, 16, 5, 4)
        
        painter.end()
        
        return pixmap
    
    def setup_tray_icon(self):
        """设置托盘图标"""
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(QIcon(self.create_icon_pixmap()))
        self.tray_icon.setToolTip("TaskbarSystemMonitor - 硬件监控")
        
        # 连接点击信号
        self.tray_icon.activated.connect(self.on_tray_activated)
    
    def setup_context_menu(self):
        """创建右键菜单"""
        self.context_menu = QMenu()
        
        # Dashboard 菜单项
        dashboard_action = QAction("📊 Dashboard", self.context_menu)
        dashboard_action.triggered.connect(lambda: self.show_dashboard.emit())
        self.context_menu.addAction(dashboard_action)
        
        self.context_menu.addSeparator()
        
        # 鼠标穿透模式开关
        self.mouse_through_action = QAction("🖱️ 鼠标穿透模式：开启", self.context_menu)
        self.mouse_through_action.setCheckable(True)
        self.mouse_through_action.setChecked(True)
        self.mouse_through_action.triggered.connect(lambda: self.toggle_mouse_through.emit())
        self.context_menu.addAction(self.mouse_through_action)
        
        self.context_menu.addSeparator()
        
        # 网卡选择子菜单
        self.nic_menu = self.context_menu.addMenu("🌐 监控网卡")
        self._setup_nic_menu()
        
        self.context_menu.addSeparator()
        
        # 颜色设置子菜单
        color_menu = self.context_menu.addMenu("🎨 文字颜色")
        
        self.auto_color_action = QAction("自动", self.context_menu)
        self.auto_color_action.setCheckable(True)
        self.auto_color_action.triggered.connect(lambda: self.set_color_mode("auto"))
        color_menu.addAction(self.auto_color_action)
        
        self.white_color_action = QAction("白色", self.context_menu)
        self.white_color_action.setCheckable(True)
        self.white_color_action.triggered.connect(lambda: self.set_color_mode("white"))
        color_menu.addAction(self.white_color_action)
        
        self.black_color_action = QAction("黑色", self.context_menu)
        self.black_color_action.setCheckable(True)
        self.black_color_action.triggered.connect(lambda: self.set_color_mode("black"))
        color_menu.addAction(self.black_color_action)
        
        # 刷新率子菜单
        refresh_menu = self.context_menu.addMenu("⚡ 刷新频率")
        
        self.refresh_05_action = QAction("0.5 秒", self.context_menu)
        self.refresh_05_action.setCheckable(True)
        self.refresh_05_action.triggered.connect(lambda: self.set_refresh_rate(0.5))
        refresh_menu.addAction(self.refresh_05_action)
        
        self.refresh_10_action = QAction("1 秒", self.context_menu)
        self.refresh_10_action.setCheckable(True)
        self.refresh_10_action.triggered.connect(lambda: self.set_refresh_rate(1.0))
        refresh_menu.addAction(self.refresh_10_action)
        
        self.refresh_30_action = QAction("3 秒", self.context_menu)
        self.refresh_30_action.setCheckable(True)
        self.refresh_30_action.triggered.connect(lambda: self.set_refresh_rate(3.0))
        refresh_menu.addAction(self.refresh_30_action)
        
        self.context_menu.addSeparator()
        
        # 开机自启
        self.autostart_action = QAction("🚀 开机自启", self.context_menu)
        self.autostart_action.setCheckable(True)
        self.autostart_action.toggled.connect(self.toggle_autostart)
        self.context_menu.addAction(self.autostart_action)
        
        self.context_menu.addSeparator()
        
        # 退出
        exit_action = QAction("❌ 退出", self.context_menu)
        exit_action.triggered.connect(self.exit_application)
        self.context_menu.addAction(exit_action)
        
        # 加载当前设置
        self.load_current_settings()
        
        # 设置菜单
        self.tray_icon.setContextMenu(self.context_menu)
    
    def _setup_nic_menu(self):
        """设置网卡选择菜单"""
        try:
            import psutil
            net_io = psutil.net_io_counters(pernic=True)
            
            # 自动选择（默认）
            auto_action = QAction("🔄 自动选择（推荐）", self.nic_menu)
            auto_action.setCheckable(True)
            auto_action.setChecked(True)
            auto_action.triggered.connect(lambda: self.switch_nic.emit("auto"))
            self.nic_menu.addAction(auto_action)
            
            self.nic_menu.addSeparator()
            
            # 列出所有物理网卡
            for nic_name in net_io.keys():
                # 跳过虚拟网卡显示
                if self._is_virtual_nic(nic_name):
                    continue
                
                action = QAction(f"{nic_name}", self.nic_menu)
                action.setCheckable(True)
                action.triggered.connect(lambda checked, name=nic_name: self.switch_nic.emit(name))
                self.nic_menu.addAction(action)
        except Exception as e:
            print(f"设置网卡菜单失败：{e}")
    
    def _is_virtual_nic(self, nic_name):
        """判断是否是虚拟网卡"""
        virtual_keywords = [
            'vmware', 'virtual', 'vmnet', 'vethernet',
            'loopback', 'pseudo',
            'isatap', 'teredo', 'tunnel',
            'hyper-v', 'docker', 'wsl'
        ]
        
        nic_name_lower = nic_name.lower()
        for keyword in virtual_keywords:
            if keyword in nic_name_lower:
                return True
        return False
    
    def load_current_settings(self):
        """加载当前设置并更新 UI"""
        settings = self.settings_manager.get_all_settings()
        
        # 颜色模式
        color_mode = settings.get('text_color', 'auto')
        if color_mode == 'auto':
            self.auto_color_action.setChecked(True)
        elif color_mode == 'white':
            self.white_color_action.setChecked(True)
        elif color_mode == 'black':
            self.black_color_action.setChecked(True)
        
        # 刷新率
        refresh_rate = settings.get('refresh_rate', 1.0)
        if refresh_rate == 0.5:
            self.refresh_05_action.setChecked(True)
        elif refresh_rate == 1.0:
            self.refresh_10_action.setChecked(True)
        elif refresh_rate == 3.0:
            self.refresh_30_action.setChecked(True)
        
        # 开机自启
        autostart = settings.get('auto_start', False)
        self.autostart_action.setChecked(autostart)
    
    def set_color_mode(self, mode):
        """设置颜色模式"""
        self.settings_manager.set_text_color(mode)
        
        # 更新菜单选中状态
        self.auto_color_action.setChecked(mode == 'auto')
        self.white_color_action.setChecked(mode == 'white')
        self.black_color_action.setChecked(mode == 'black')
        
        # 通知主窗口更新
        from PySide6.QtCore import QCoreApplication
        event = QCoreApplication.registerEventType(1001)
        QCoreApplication.postEvent(QCoreApplication.instance(), 
                                   QCoreApplication.Type(event))
    
    def set_refresh_rate(self, rate):
        """设置刷新率"""
        self.settings_manager.set_refresh_rate(rate)
        
        # 更新菜单选中状态
        self.refresh_05_action.setChecked(rate == 0.5)
        self.refresh_10_action.setChecked(rate == 1.0)
        self.refresh_30_action.setChecked(rate == 3.0)
        
        # 通知数据引擎更新
        from PySide6.QtCore import QCoreApplication
        event = QCoreApplication.registerEventType(1002)
        QCoreApplication.postEvent(QCoreApplication.instance(),
                                   QCoreApplication.Type(event))
    
    def update_mouse_through_status(self, enabled):
        """更新鼠标穿透状态显示"""
        if self.mouse_through_action:
            if enabled:
                self.mouse_through_action.setText("🖱️ 鼠标穿透模式：开启")
                self.mouse_through_action.setChecked(True)
            else:
                self.mouse_through_action.setText("🖱️ 鼠标穿透模式：关闭")
                self.mouse_through_action.setChecked(False)
    
    def toggle_autostart(self, enabled):
        """切换开机自启状态"""
        self.settings_manager.set_auto_start(enabled)
    
    def on_tray_activated(self, reason):
        """处理托盘图标激活事件"""
        if reason == QSystemTrayIcon.Trigger:  # 左键单击
            self.show_dashboard.emit()
    
    def exit_application(self):
        """退出应用程序"""
        from PySide6.QtWidgets import QApplication
        QApplication.quit()
    
    def show(self):
        """显示托盘图标"""
        self.tray_icon.show()
    
    def hide(self):
        """隐藏托盘图标"""
        self.tray_icon.hide()
