"""
TransparentSystemMonitor (TSM) - 主程序入口
Windows 实时硬件监控系统 - 透明悬浮窗设计
"""
import sys
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QEvent

# 导入自定义模块
from data_engine import DataEngine
from window_positioning import WindowPositioning
from main_window import MonitorWindow
from system_tray import SystemTrayManager
from settings_manager import SettingsManager
from dashboard import Dashboard


class Application(QApplication):
    """主应用程序类"""
    
    def __init__(self):
        super().__init__(sys.argv)
        
        # 设置 DPI 感知
        self.setup_dpi()
        
        # 初始化各个模块
        self.init_modules()
        
        # 连接信号槽
        self.connect_signals()
        
        # 应用设置
        self.apply_settings()
        
        # 启动数据采集
        self.data_engine.start()
        
        # 延迟显示窗口（确保任务栏已就绪）
        QTimer.singleShot(1000, self.show_windows)
    
    def setup_dpi(self):
        """设置 DPI 感知"""
        try:
            # Windows 8.1+ DPI 感知
            if hasattr(ctypes.windll.shcore, 'SetProcessDpiAwareness'):
                # PROCESS_PER_MONITOR_DPI_AWARE = 2
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception as e:
            print(f"设置 DPI 感知失败：{e}")
    
    def init_modules(self):
        """初始化所有模块"""
        # 设置管理器
        self.settings_manager = SettingsManager()
        
        # 窗口定位
        self.window_positioning = WindowPositioning()
        
        # 数据采集引擎
        refresh_rate = self.settings_manager.get_setting('refresh_rate')
        self.data_engine = DataEngine(update_interval=refresh_rate)
        
        # 主窗口 - 可拖动透明窗口
        self.monitor_window = MonitorWindow()
        
        # 系统托盘
        self.tray_manager = SystemTrayManager(self.settings_manager)
        
        # Dashboard 窗口（初始为 None，按需创建）
        self.dashboard = None
    
    def connect_signals(self):
        """连接信号槽"""
        # 数据更新 -> 主窗口
        self.data_engine.data_updated.connect(self.monitor_window.update_data)
        
        # 数据更新 -> Dashboard（如果存在）
        self.data_engine.data_updated.connect(self.on_data_updated_for_dashboard)
        
        # 托盘显示 Dashboard -> 打开 Dashboard
        self.tray_manager.show_dashboard.connect(self.show_dashboard)
        
        # 托盘切换穿透模式 -> 切换窗口穿透状态
        self.tray_manager.toggle_mouse_through.connect(self.toggle_window_mouse_through)
        
        # 托盘切换网卡 -> 更新数据引擎的网卡
        self.tray_manager.switch_nic.connect(self.switch_monitor_nic)
    
    def apply_settings(self):
        """应用用户设置"""
        # 文字颜色
        color_mode = self.settings_manager.get_setting('text_color')
        self.monitor_window.set_text_color(color_mode)
    
    def show_windows(self):
        """显示窗口"""
        # 显示主窗口
        self.monitor_window.show()
        
        # 显示托盘图标
        self.tray_manager.show()
    
    def show_dashboard(self):
        """显示 Dashboard"""
        if self.dashboard is None:
            self.dashboard = Dashboard(self.data_engine, self.monitor_window)
        
        self.dashboard.refresh_data()
        self.dashboard.show()
        self.dashboard.raise_()
        self.dashboard.activateWindow()
    
    def toggle_window_mouse_through(self):
        """切换窗口鼠标穿透模式"""
        self.monitor_window.toggle_mouse_through_from_menu()
        # 更新托盘菜单显示
        self.tray_manager.update_mouse_through_status(self.monitor_window.mouse_through_enabled)
    
    def switch_monitor_nic(self, nic_name):
        """切换监控的网卡"""
        if nic_name == "auto":
            print("[✓] 已切换到自动选择网卡模式")
            # 恢复自动选择逻辑
            self.data_engine.selected_nic = None
        else:
            print(f"[✓] 已切换到网卡：{nic_name}")
            self.data_engine.selected_nic = nic_name
    
    def on_data_updated_for_dashboard(self, data):
        """Dashboard 数据更新"""
        if self.dashboard and self.dashboard.isVisible():
            self.dashboard.refresh_data()
    
    def customEvent(self, event):
        """处理自定义事件（设置变更）"""
        # 这里可以处理来自托盘菜单的设置变更事件
        super().customEvent(event)
    
    def cleanup(self):
        """清理资源"""
        self.data_engine.stop()
        
        if self.dashboard:
            self.dashboard.close()
        
        self.monitor_window.close()


def main():
    """主函数"""
    # 检查是否已有实例运行
    # （可以添加单实例检查逻辑）
    
    # 创建应用程序
    app = Application()
    
    # 运行应用程序
    exit_code = app.exec()
    
    # 清理资源
    app.cleanup()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
