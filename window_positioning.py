"""
窗口定位模块
提供简单的窗口定位辅助功能
原 taskbar_integration.py - 已移除自动定位功能
"""
import ctypes
from ctypes import windll


class WindowPositioning:
    """窗口定位辅助类"""
    
    def __init__(self):
        pass
    
    def apply_mouse_through(self, widget):
        """应用鼠标穿透效果到 Qt 组件"""
        try:
            hwnd = int(widget.winId())
            
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_LAYERED = 0x00080000
            
            # 获取当前扩展样式
            ex_style = windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
            
            # 添加 TRANSPARENT 和 LAYERED 样式
            new_style = ex_style | WS_EX_TRANSPARENT | WS_EX_LAYERED
            
            # 设置扩展样式
            windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, new_style)
            
            return True
        except Exception as e:
            print(f"应用鼠标穿透失败：{e}")
            return False
