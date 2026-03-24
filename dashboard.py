"""
Dashboard 弹窗模块
显示过去 1 分钟的硬件状态折线图
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
import time


class Dashboard(QDialog):
    """硬件监控 Dashboard 弹窗"""
    
    def __init__(self, data_engine, parent=None):
        super().__init__(parent)
        self.data_engine = data_engine
        
        # 窗口设置
        self.setup_window()
        
        # UI 组件
        self.setup_ui()
        
        # 更新图表数据
        self.update_chart()
    
    def setup_window(self):
        """设置窗口属性"""
        self.setWindowTitle("硬件监控 - Dashboard")
        self.setFixedSize(800, 600)
        
        # 模态对话框
        self.setWindowModality(Qt.ApplicationModal)
        
        # 置顶
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
    
    def setup_ui(self):
        """设置 UI 布局"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("过去 1 分钟硬件状态")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont("Segoe UI Variable", 14, QFont.Bold)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # 创建 Matplotlib 图表
        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        
        layout.addWidget(self.canvas)
    
    def update_chart(self):
        """更新图表数据"""
        # 获取历史数据
        history = list(self.data_engine.history)[-60:]  # 最近 60 秒
        
        if not history:
            return
        
        # 准备数据
        timestamps = [data['timestamp'] for data in history]
        cpu_values = [data['cpu'] for data in history]
        ram_values = [data['ram'] for data in history]
        
        # 转换时间戳为可读格式
        times = [time.strftime('%H:%M:%S', time.localtime(ts)) for ts in timestamps]
        
        # 清空图表
        self.figure.clear()
        
        # 创建子图
        ax = self.figure.add_subplot(111)
        
        # 绘制 CPU 曲线
        ax.plot(times, cpu_values, 'r-', label='CPU %', linewidth=2, marker='o', markersize=3)
        
        # 绘制 RAM 曲线
        ax.plot(times, ram_values, 'b-', label='RAM %', linewidth=2, marker='s', markersize=3)
        
        # 设置样式
        ax.set_xlabel('时间', fontsize=10)
        ax.set_ylabel('利用率 (%)', fontsize=10)
        ax.set_title('CPU & RAM 使用率趋势', fontsize=12, fontweight='bold')
        
        # 旋转 x 轴标签
        ax.tick_params(axis='x', rotation=45)
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        
        # 添加图例
        ax.legend(loc='upper left')
        
        # 设置 y 轴范围
        ax.set_ylim(0, 100)
        
        # 添加阈值线
        ax.axhline(y=90, color='orange', linestyle='--', alpha=0.7, label='警告 (90%)')
        ax.axhline(y=95, color='red', linestyle='--', alpha=0.7, label='危险 (95%)')
        
        # 自动调整布局
        self.figure.tight_layout()
        
        # 刷新画布
        self.canvas.draw()
    
    def refresh_data(self):
        """刷新数据"""
        self.update_chart()
