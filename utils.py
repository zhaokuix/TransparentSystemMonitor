"""
工具函数模块
提供通用的辅助函数
"""
import ctypes
from ctypes import wintypes


def get_dpi_for_window(hwnd):
    """获取窗口的 DPI 值"""
    try:
        user32 = ctypes.windll.user32
        # Windows 8.1+ API
        GetDpiForWindow = user32.GetDpiForWindow
        if GetDpiForWindow:
            return GetDpiForWindow(hwnd)
    except Exception:
        pass
    
    # 回退到系统 DPI
    hdc = ctypes.windll.gdi32.GetDC(0)
    dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
    ctypes.windll.gdi32.ReleaseDC(0, hdc)
    return dpi


def format_bytes(bytes_value):
    """格式化字节数为人类可读格式"""
    for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
        if abs(bytes_value) < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB/s"


def calculate_color_from_percentage(percentage):
    """
    根据百分比计算颜色
    正常：< 90% -> 白色 (RGBA: 255, 255, 255, 0.9)
    警告：90%-95% -> 橙色 (#FFA500)
    危险：> 95% -> 红色 (#FF0000)
    """
    if percentage >= 95:
        return "#FF0000"  # 红色
    elif percentage >= 90:
        return "#FFA500"  # 橙色
    else:
        return "rgba(255, 255, 255, 0.9)"  # 白色


class RECT(ctypes.Structure):
    """Windows RECT 结构体"""
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]


class POINT(ctypes.Structure):
    """Windows POINT 结构体"""
    _fields_ = [
        ('x', ctypes.c_long),
        ('y', ctypes.c_long)
    ]
