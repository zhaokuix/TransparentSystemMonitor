"""
配置管理模块
负责管理程序设置，包括注册表操作、颜色设置、刷新率等
"""
import sys
import winreg
from PySide6.QtCore import QObject


class SettingsManager(QObject):
    """设置管理器"""
    
    # 注册表路径 (Current User)
    REG_PATH = r"Software\TaskbarSystemMonitor"
    
    # 默认设置
    DEFAULTS = {
        'auto_start': False,
        'text_color': 'auto',  # auto | white | black
        'refresh_rate': 1.0,  # 秒：0.5 | 1.0 | 3.0
    }
    
    def __init__(self):
        super().__init__()
        self.settings = self.DEFAULTS.copy()
        self.load_settings()
    
    def _open_registry(self, create=False):
        """打开注册表键"""
        try:
            if create:
                return winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.REG_PATH)
            else:
                return winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REG_PATH, 0, winreg.KEY_READ | winreg.KEY_WRITE)
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"注册表操作失败：{e}")
            return None
    
    def load_settings(self):
        """从注册表加载设置"""
        key = self._open_registry()
        if not key:
            return
        
        try:
            # 读取各项设置
            value, _ = winreg.QueryValueEx(key, 'AutoStart')
            self.settings['auto_start'] = bool(value)
            
            value, _ = winreg.QueryValueEx(key, 'TextColor')
            self.settings['text_color'] = str(value)
            
            value, _ = winreg.QueryValueEx(key, 'RefreshRate')
            self.settings['refresh_rate'] = float(value)
            
        except FileNotFoundError:
            pass  # 使用默认值
        except Exception as e:
            print(f"加载设置失败：{e}")
        finally:
            winreg.CloseKey(key)
    
    def save_setting(self, name, value):
        """保存单个设置项"""
        key = self._open_registry(create=True)
        if not key:
            return False
        
        try:
            if isinstance(value, bool):
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, int(value))
            elif isinstance(value, (int, float)):
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, int(value * 100))  # 存储为整数
            elif isinstance(value, str):
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
            
            self.settings[name] = value
            return True
            
        except Exception as e:
            print(f"保存设置失败：{e}")
            return False
        finally:
            winreg.CloseKey(key)
    
    def set_auto_start(self, enabled):
        """
        设置开机自启
        写入 CurrentUser 注册表 Run 键
        """
        # 保存到程序设置
        self.save_setting('AutoStart', enabled)
        
        # 注册表 Run 键路径
        run_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        try:
            run_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key_path, 0, winreg.KEY_WRITE)
            
            if enabled:
                # 添加启动项
                exe_path = sys.executable
                if hasattr(sys, 'frozen'):
                    # PyInstaller 打包后的路径
                    import os
                    exe_path = os.path.abspath(sys.executable)
                
                winreg.SetValueEx(run_key, 'TaskbarSystemMonitor', 0, winreg.REG_SZ, f'"{exe_path}"')
            else:
                # 删除启动项
                try:
                    winreg.DeleteValue(run_key, 'TaskbarSystemMonitor')
                except FileNotFoundError:
                    pass  # 值不存在，忽略
            
            winreg.CloseKey(run_key)
            return True
            
        except Exception as e:
            print(f"设置开机自启失败：{e}")
            return False
    
    def set_text_color(self, color_mode):
        """
        设置文字颜色模式
        color_mode: "auto" | "white" | "black"
        """
        if color_mode in ['auto', 'white', 'black']:
            return self.save_setting('TextColor', color_mode)
        return False
    
    def set_refresh_rate(self, rate):
        """
        设置刷新率
        rate: 0.5 | 1.0 | 3.0 (秒)
        """
        if rate in [0.5, 1.0, 3.0]:
            return self.save_setting('RefreshRate', rate)
        return False
    
    def get_setting(self, name):
        """获取设置项"""
        return self.settings.get(name, self.DEFAULTS.get(name))
    
    def get_all_settings(self):
        """获取所有设置"""
        return self.settings.copy()
