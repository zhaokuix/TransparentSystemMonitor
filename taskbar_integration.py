"""
任务栏嵌入模块
负责将监控窗口嵌入到 Windows 11 任务栏
实现鼠标穿透、DPI 监听、Explorer 重启检测等功能
"""
import ctypes
from ctypes import wintypes, windll
from PySide6.QtCore import QObject, Signal, QTimer
import utils


# Windows API 常量
GWL_EXSTYLE = -20
WS_EX_TOPMOST = -1
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010

# Shell 托盘窗口类名
TRAYNOTIFY_CLASS = "TrayNotifyWnd"
SHELL_TRAY_CLASS = "Shell_TrayWnd"


class TaskbarIntegration(QObject):
    """任务栏集成管理器"""
    
    # 信号：位置需要更新
    position_updated = Signal(int, int, int, int)  # x, y, width, height
    
    def __init__(self):
        super().__init__()
        self.taskbar_hwnd = None
        self.tray_hwnd = None
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_position)
        self.position_timer.start(500)  # 每 500ms 检查一次位置
        
        # 注册窗口消息过滤，监听 Explorer 重启
        self._last_known_rect = None
    
    def get_taskbar_rect(self):
        """获取任务栏矩形区域"""
        try:
            # 查找任务栏窗口
            self.taskbar_hwnd = windll.user32.FindWindowW(SHELL_TRAY_CLASS, None)
            
            if not self.taskbar_hwnd:
                return None
            
            # 获取任务栏矩形
            rect = utils.RECT()
            windll.user32.GetWindowRect(self.taskbar_hwnd, ctypes.byref(rect))
            
            return (rect.left, rect.top, rect.right, rect.bottom)
            
        except Exception as e:
            print(f"获取任务栏矩形失败：{e}")
            return None
    
    def get_tray_rect(self):
        """获取系统托盘区域矩形"""
        try:
            if not self.taskbar_hwnd:
                self.taskbar_hwnd = windll.user32.FindWindowW(SHELL_TRAY_CLASS, None)
            
            if not self.taskbar_hwnd:
                return None
            
            # 枚举任务栏的子窗口，找到 TrayNotifyWnd
            def enum_child_windows_callback(hwnd, lparam):
                class_name_buf = ctypes.create_unicode_buffer(260)
                windll.user32.GetClassNameW(hwnd, class_name_buf, 260)
                
                if class_name_buf.value == TRAYNOTIFY_CLASS:
                    self.tray_hwnd = hwnd
                    return False  # 停止枚举
                
                return True  # 继续枚举
            
            # 定义回调函数类型
            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            callback = WNDENUMPROC(enum_child_windows_callback)
            
            # 枚举子窗口
            windll.user32.EnumChildWindows(self.taskbar_hwnd, callback, 0)
            
            if self.tray_hwnd:
                rect = utils.RECT()
                windll.user32.GetWindowRect(self.tray_hwnd, ctypes.byref(rect))
                
                return (rect.left, rect.top, rect.right, rect.bottom)
            
            return None
            
        except Exception as e:
            print(f"获取托盘矩形失败：{e}")
            return None
    
    def calculate_monitor_position(self, tray_rect, taskbar_rect):
        """
        计算监控条的位置
        对齐至系统托盘的左侧边界
        """
        if not tray_rect or not taskbar_rect:
            return None
        
        tray_left, tray_top, tray_right, tray_bottom = tray_rect
        task_left, task_top, task_right, task_bottom = taskbar_rect
        
        # 监控条宽度（根据内容动态调整，这里给个默认值）
        monitor_width = 200
        # 监控条高度与任务栏高度一致
        monitor_height = task_bottom - task_top
        
        # 位置：托盘左侧
        x = tray_left - monitor_width
        y = task_top
        
        return (x, y, monitor_width, monitor_height)
    
    def set_window_transparent(self, hwnd):
        """设置窗口透明和鼠标穿透"""
        try:
            # 获取当前扩展样式
            ex_style = windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
            
            # 添加 TOPMOST, TRANSPARENT, LAYERED 样式
            new_style = ex_style | WS_EX_TOPMOST | WS_EX_TRANSPARENT | WS_EX_LAYERED
            
            # 设置扩展样式
            windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, new_style)
            
            return True
            
        except Exception as e:
            print(f"设置窗口透明失败：{e}")
            return False
    
    def update_position(self):
        """更新窗口位置"""
        try:
            taskbar_rect = self.get_taskbar_rect()
            tray_rect = self.get_tray_rect()
            
            if taskbar_rect and tray_rect:
                # 检查任务栏是否发生变化
                current_rect_key = (taskbar_rect, tray_rect)
                if current_rect_key != self._last_known_rect:
                    self._last_known_rect = current_rect_key
                    
                    # 计算新位置
                    pos = self.calculate_monitor_position(tray_rect, taskbar_rect)
                    
                    if pos:
                        x, y, width, height = pos
                        print(f"[DEBUG] 更新窗口位置：x={x}, y={y}, size={width}x{height}")
                        print(f"[DEBUG] 托盘位置：{tray_rect}")
                        print(f"[DEBUG] 任务栏位置：{taskbar_rect}")
                        self.position_updated.emit(x, y, width, height)
                    else:
                        print("[DEBUG] 无法计算位置")
                else:
                    print("[DEBUG] 位置未变化，跳过更新")
                        
        except Exception as e:
            print(f"[DEBUG] 更新位置失败：{e}")
    
    def apply_mouse_through(self, widget):
        """应用鼠标穿透效果到 Qt 组件"""
        try:
            hwnd = int(widget.winId())
            self.set_window_transparent(hwnd)
            return True
        except Exception as e:
            print(f"应用鼠标穿透失败：{e}")
            return False
    
    def setup_dpi_awareness(self):
        """设置 DPI 感知"""
        try:
            # Windows 8.1+ DPI 感知
            if hasattr(windll.shcore, 'SetProcessDpiAwareness'):
                # PROCESS_PER_MONITOR_DPI_AWARE = 2
                windll.shcore.SetProcessDpiAwareness(2)
                return True
            # Windows Vista+ DPI 感知
            elif hasattr(windll.user32, 'SetProcessDPIAware'):
                windll.user32.SetProcessDPIAware()
                return True
        except Exception as e:
            print(f"设置 DPI 感知失败：{e}")
        
        return False
    
    def register_explorer_restart_listener(self, callback):
        """
        注册 Explorer 重启监听器
        当任务栏重启时重新执行定位算法
        """
        # Windows 消息：TaskbarCreated
        WM_TASKBARCREATED = windll.user32.RegisterWindowMessageW("TaskbarCreated")
        
        # 保存回调以便后续使用
        self.explorer_restart_callback = callback
        
        # 注意：Qt 中需要使用 native event filter 来捕获这个 Windows 消息
        # 这将在主窗口中实现
        return WM_TASKBARCREATED
