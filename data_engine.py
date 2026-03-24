"""
数据采集模块
负责采集 CPU、内存、网络流量等硬件状态数据
"""
import psutil
import time
from collections import deque
from PySide6.QtCore import QThread, Signal, QObject


class DataEngine(QObject):
    """数据采集引擎"""
    
    # 信号：数据更新
    data_updated = Signal(dict)
    
    def __init__(self, update_interval=1.0):
        super().__init__()
        self.update_interval = update_interval
        self.running = False
        
        # 网络流量计算相关
        self.prev_net_io = None
        self.prev_time = None
        
        # 历史数据（用于 Dashboard）
        self.history_max_length = 60  # 保存 60 秒的数据
        self.history = deque(maxlen=self.history_max_length)
        
        # 用户选择的网卡（None 表示自动选择）
        self.selected_nic = None
        
        # 初始化网络计数器
        self._init_net_counter()
    
    def _init_net_counter(self):
        """初始化网络计数器"""
        try:
            self.prev_net_io = psutil.net_io_counters(pernic=True)
            self.prev_time = time.time()
        except Exception as e:
            print(f"初始化网络计数器失败：{e}")
            self.prev_net_io = None
            self.prev_time = None
    
    def start(self):
        """启动采集线程"""
        self.running = True
        self.thread = QThread()
        self.moveToThread(self.thread)
        
        # 连接信号槽
        self.thread.started.connect(self._run)
        self.thread.finished.connect(self.stop)
        
        self.thread.start()
    
    def stop(self):
        """停止采集线程"""
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.quit()
            self.thread.wait()
    
    def set_update_interval(self, interval):
        """设置更新间隔"""
        self.update_interval = interval
    
    def _get_active_nic(self, net_io):
        """
        获取当前活跃的网络适配器
        优先选择物理网卡（WiFi/以太网），跳过虚拟网卡
        如果用户指定了网卡，则使用用户指定的
        """
        # 如果用户指定了网卡，优先使用用户的
        if self.selected_nic and self.selected_nic in net_io:
            print(f"[DEBUG] 使用用户指定的网卡：{self.selected_nic}")
            return self.selected_nic
        
        # 第一次遍历：找到有流量的物理网卡
        for nic_name, nic_stats in net_io.items():
            # 跳过虚拟网卡和回环接口
            if self._is_virtual_nic(nic_name):
                continue
            
            # 如果有发送或接收的字节数，认为该网卡活跃
            if nic_stats.bytes_sent > 0 or nic_stats.bytes_recv > 0:
                print(f"[DEBUG] 检测到物理网卡：{nic_name}")
                print(f"[DEBUG]   发送：{nic_stats.bytes_sent:,} 字节")
                print(f"[DEBUG]   接收：{nic_stats.bytes_recv:,} 字节")
                return nic_name
        
        # 第二次遍历：如果没有活跃的物理网卡，找第一个非虚拟网卡
        for nic_name in net_io.keys():
            if not self._is_virtual_nic(nic_name):
                print(f"[DEBUG] 使用备用物理网卡：{nic_name}")
                return nic_name
        
        print("[DEBUG] 未找到可用物理网卡，使用任意网卡")
        # 最后的备选：使用第一个网卡
        for nic_name in net_io.keys():
            return nic_name
        
        return None
    
    def _is_virtual_nic(self, nic_name):
        """判断是否是虚拟网卡"""
        virtual_keywords = [
            'vmware', 'virtual', 'vmnet', 'vethernet',  # VMware
            'loopback', 'pseudo',                        # 回环
            'isatap', 'teredo', 'tunnel',                # 隧道
            'hyper-v', 'docker', 'wsl'                   # 其他虚拟化
        ]
        
        nic_name_lower = nic_name.lower()
        for keyword in virtual_keywords:
            if keyword in nic_name_lower:
                return True
        
        return False
    
    def _calculate_network_speed(self):
        """计算网络上传/下载速度"""
        try:
            current_net_io = psutil.net_io_counters(pernic=True)
            current_time = time.time()
            
            if self.prev_net_io is None or self.prev_time is None:
                self.prev_net_io = current_net_io
                self.prev_time = current_time
                return 0.0, 0.0
            
            # 找到活跃的网卡
            active_nic = self._get_active_nic(current_net_io)
            
            if active_nic and active_nic in current_net_io and active_nic in self.prev_net_io:
                # 计算差值
                time_diff = current_time - self.prev_time
                if time_diff <= 0:
                    return 0.0, 0.0
                
                upload_diff = (current_net_io[active_nic].bytes_sent - 
                              self.prev_net_io[active_nic].bytes_sent)
                download_diff = (current_net_io[active_nic].bytes_recv - 
                                self.prev_net_io[active_nic].bytes_recv)
                
                upload_speed = max(0, upload_diff) / time_diff
                download_speed = max(0, download_diff) / time_diff
                
                # 更新历史数据
                self.prev_net_io = current_net_io
                self.prev_time = current_time
                
                return upload_speed, download_speed
            else:
                # 网卡切换，重新初始化
                self.prev_net_io = current_net_io
                self.prev_time = current_time
                return 0.0, 0.0
                
        except Exception as e:
            print(f"计算网络速度失败：{e}")
            return 0.0, 0.0
    
    def _collect_data(self):
        """采集一次数据"""
        try:
            # CPU 利用率 - 所有逻辑核心的平均负载
            cpu_percent = round(psutil.cpu_percent(interval=None))
            
            # RAM 利用率
            memory = psutil.virtual_memory()
            ram_percent = round((memory.used / memory.total) * 100)
            
            # 网络速度
            upload_speed, download_speed = self._calculate_network_speed()
            
            data = {
                'cpu': cpu_percent,
                'ram': ram_percent,
                'upload': upload_speed,
                'download': download_speed,
                'timestamp': time.time()
            }
            
            # 保存到历史记录
            self.history.append(data.copy())
            
            return data
            
        except Exception as e:
            print(f"采集数据失败：{e}")
            return None
    
    def _run(self):
        """运行采集循环"""
        while self.running:
            data = self._collect_data()
            if data:
                self.data_updated.emit(data)
            
            # 休眠指定时间
            time.sleep(self.update_interval)


# 测试代码
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    engine = DataEngine(update_interval=1.0)
    
    def on_data(data):
        print(f"CPU: {data['cpu']}%")
        print(f"RAM: {data['ram']}%")
        print(f"Upload: {data['upload']:.2f} B/s")
        print(f"Download: {data['download']:.2f} B/s")
        print("---")
    
    engine.data_updated.connect(on_data)
    engine.start()
    
    sys.exit(app.exec())
