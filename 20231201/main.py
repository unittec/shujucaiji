import sys
from datetime import datetime

import pandas as pd
# 导入图形组件库
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from Control import Control
#导入做好的界面库
from untitled import Ui_MainWindow
import pyqtgraph as pg
import nidaqmx
from nidaqmx import constants
from nidaqmx.constants import TerminalConfiguration

def get_current_time():
    current_time = datetime.now()
    return f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}.{current_time.microsecond // 1000:03d}"

# 控制台颜色转义序列
class OutColors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    RESET = '\033[0m'


# 串口配置
pre_com_name, pre_com_baud = 'COM4', 38400
valve_com_name, valve_com_baud = 'COM7', 9600
keys_com_name, keys_com_baud = 'COM8', 9600
# 初始化控制类
control = Control(pre_com_name, pre_com_baud, valve_com_name, valve_com_baud, keys_com_name, keys_com_baud)
# 需要打印的手指 0~4
control.need_show = [1]
# 采样电压灵敏度控制 单位v 值越小 执行气压控制的频率越高
control.response_threshold = 0.01

# 采样速率



class mythread(QThread):
    d = pyqtSignal(list)
    def __init__(self):
        super(mythread, self).__init__()
        self.status = 0
    def run(self) -> None:

        global control  # 声明全局变量


        NUM_CHANNELS = 5
        RATE = 200 / NUM_CHANNELS
        SP = 10
        try:
            with nidaqmx.Task() as task:
                for i in range(NUM_CHANNELS):
                    task.ai_channels.add_ai_voltage_chan("Dev/ai{}".format(i), name_to_assign_to_channel="AI{}".format(i),
                                                         terminal_config = TerminalConfiguration.RSE, max_val=10, min_val=-10)
                task.timing.cfg_samp_clk_timing(RATE, sample_mode=constants.AcquisitionType.CONTINUOUS,
                                                samps_per_chan=20)  # 一直采，直到停止任务
                # task.timing.cfg_samp_clk_timing(RATE,sample_mode=constants.AcquisitionType.FINITE,samps_per_chan=300000) #采集指定数量的样本

                channel1_data = []
                channel2_data = []
                channel3_data = []
                channel4_data = []
                channel5_data = []

                def read_callback(task_handle, every_n_samples_event_type,
                                  number_of_samples, callback_data):

                    ####################直接使用 read 函数 #############
                    try:
                        data = task.read(number_of_samples_per_channel=number_of_samples)
                        # non_local_var['All samples'].extend(data)
                        channel1_data.extend(data[0])
                        channel2_data.extend(data[1])
                        channel3_data.extend(data[2])
                        channel4_data.extend(data[3])
                        channel5_data.extend(data[4])
                        # 在这里获取最新的电压值 入队
                        control.nid_queue.put(tuple(data[i][-1] for i in range(NUM_CHANNELS)))

                    except Exception as e:
                        print(e)
                        pass
                    return 0

                task.register_every_n_samples_acquired_into_buffer_event(
                    SP, read_callback)  # 注册回调函数，就如函数名称，每采集n个样品到buffer触发事件，调用回到函数

                task.start()
                print(f"{OutColors.GREEN}{get_current_time()}| NID卡连接成功{OutColors.RESET}")

                oldNums = 0
                while True:
                    if self.status == 1:
                        break
                    _senData = [
                        channel1_data,
                        channel2_data,
                        channel3_data,
                        channel4_data,
                        channel5_data
                    ]
                    if len(channel1_data) == oldNums:
                        pass
                    else:
                        oldNums = len(channel1_data)
                        self.d.emit(_senData)
        except FileNotFoundError as e:
            print(f"{OutColors.RED}{get_current_time()}| NID卡连接失败: {e}{OutColors.RESET}")





class MainWindow(QMainWindow,Ui_MainWindow):
    def __init__(self):
        #继承(QMainWindow,Ui_MainWindow)父类的属性
        super(MainWindow,self).__init__()
        #初始化界面组件
        self.setupUi(self)
        #初始化界面
        self.init_window_setting()
        #初始化按钮
        self.init_button_setting()
        # 控制模式
        self.control_mode = 0  # 0:被动模式 1:主动模式 -1:无控制

        print(f"{OutColors.GREEN}{get_current_time()}| 界面初始化完成{OutColors.RESET}")


    def refrsh(self,data):
        data1, data2, data3, data4, data5 = data

        #颜色
        colors = ['r', 'g', 'b', 'c', 'm']
        if len(data1) <= self.length:
            self.curve1.setData(data1, pen=pg.mkPen(width=self.lineWidth, color=colors[0]))
            self.curve2.setData(data2, pen=pg.mkPen(width=self.lineWidth, color=colors[1]))
            self.curve3.setData(data3, pen=pg.mkPen(width=self.lineWidth, color=colors[2]))
            self.curve4.setData(data4, pen=pg.mkPen(width=self.lineWidth, color=colors[3]))
            self.curve5.setData(data5, pen=pg.mkPen(width=self.lineWidth, color=colors[4]))
        else:
            self.curve1.setData(range(len(data1)-self.length,len(data1)),data1[len(data1)-self.length:len(data1)], pen=pg.mkPen(width=self.lineWidth, color=colors[0]))
            self.curve2.setData(range(len(data2)-self.length,len(data2)),data2[len(data2)-self.length:len(data2)], pen=pg.mkPen(width=self.lineWidth, color=colors[1]))
            self.curve3.setData(range(len(data3)-self.length,len(data3)),data3[len(data3)-self.length:len(data3)], pen=pg.mkPen(width=self.lineWidth, color=colors[2]))
            self.curve4.setData(range(len(data4)-self.length,len(data4)),data4[len(data4)-self.length:len(data4)], pen=pg.mkPen(width=self.lineWidth, color=colors[3]))
            self.curve5.setData(range(len(data5)-self.length,len(data5)),data5[len(data5)-self.length:len(data5)], pen=pg.mkPen(width=self.lineWidth, color=colors[4]))
        self.datas = [
            data1,
            data2,
            data3,
            data4,
            data5
        ]
        # self.plot_widget.setXRange(len(data1) - self.length, len(data1))
    def init_window_setting(self):
        self.datas = []
        #显示长度
        self.length = 50
        #线条粗细
        self.lineWidth = 3
        # 嵌入图
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setTitle("手指传感数据")
        self.plot_widget.getAxis("bottom").setLabel("时间")
        self.plot_widget.getAxis("left").setLabel("电压")
        self.plot_widget.setAntialiasing(True)
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setBackground('w')

        self.curve1 = self.plot_widget.plot([], name="拇指")
        self.curve2 = self.plot_widget.plot([], name="食指")
        self.curve3 = self.plot_widget.plot([], name="中指")
        self.curve4 = self.plot_widget.plot([], name="无名指")
        self.curve5 = self.plot_widget.plot([], name="小指")


        self.plot_widget.setMouseEnabled(x=False, y=False)  # 禁用轴操作

        layout = QHBoxLayout()
        layout.addWidget(self.plot_widget)
        self.widget.setLayout(layout)
        #清除关闭
        self.pushButton_2.setEnabled(False)
        self.pushButton_4.setEnabled(False)



        self.startLine()
    def init_button_setting(self):
        #开始
        self.pushButton.clicked.connect(self.startLine)
        #清除
        self.pushButton_2.clicked.connect(self.clearData)
        #保存
        self.pushButton_4.clicked.connect(self.saveData)
        # 控制
        # self.pushButton_5.setText('控制开关')
        # self.pushButton_5.clicked.connect(self.control_switch)
        # 主动模式按钮 替代原本的控制开关
        self.pushButton_5.setVisible(False)  # 隐藏控制开关
        # 连接主动模式按钮方法
        self.pushButton_active.clicked.connect(self.open_active_mode)
        # 连接被动模式按钮方法
        self.pushButton_passive.clicked.connect(self.open_passive_mode)

        # 初始化打开主动模式
        self.open_active_mode()

    def clearData(self):
        try:
            self._thread.status = 1
            self.pushButton.setText('开始')
        except:
            pass
        self.datas = []
        colors = ['r', 'g', 'b', 'c', 'm']
        self.curve1.setData([], pen=pg.mkPen(width=self.lineWidth, color=colors[0]))
        self.curve2.setData([], pen=pg.mkPen(width=self.lineWidth, color=colors[1]))
        self.curve3.setData([], pen=pg.mkPen(width=self.lineWidth, color=colors[2]))
        self.curve4.setData([], pen=pg.mkPen(width=self.lineWidth, color=colors[3]))
        self.curve5.setData([], pen=pg.mkPen(width=self.lineWidth, color=colors[4]))
    def saveData(self):
        if self.datas:
            fileName_choose, filetype = QFileDialog.getSaveFileName(self,
                                                                    "Save File",
                                                                    "./",  # 起始路径
                                                                    "Excel file (*.csv)")
            if fileName_choose:
                _data = {
                    "曲线1":self.datas[0],
                    "曲线2":self.datas[1],
                    "曲线3":self.datas[2],
                    "曲线4":self.datas[3],
                    "曲线5":self.datas[4]
                }
                pd.DataFrame(_data).to_csv(fileName_choose)
                QMessageBox.information(self, "提示", "保存成功", QMessageBox.Yes)
        else:
            QMessageBox.warning(self,"警告","没数据",QMessageBox.Yes)
    def startLine(self):
        if self.pushButton.text() == "开始":
            self._thread = mythread()
            self._thread.d.connect(self.refrsh)
            print(f"{OutColors.GREEN}{get_current_time()}| 开始NID采集{OutColors.RESET}")
            self._thread.start()
            self.pushButton.setText("停止")
        else:
            self._thread.status = 1
            print(f"{OutColors.GREEN}{get_current_time()}| 停止NID采集{OutColors.RESET}")
            self.pushButton.setText("开始")
            self.pushButton_2.setEnabled(True)
            self.pushButton_4.setEnabled(True)

    # def control_switch(self):
    #     if control.switch():
    #         # self.pushButton_5.setStyleSheet("QPushButton {color: green}")
    #         self.pushButton_active.setStyleSheet("QPushButton {color: green}")
    #     else:
    #         # self.pushButton_5.setStyleSheet("QPushButton {color: black}")
    #         self.pushButton_active.setStyleSheet("QPushButton {color: black}")

    def open_active_mode(self):
        # 打开主动模式
        is_active_mode = control.open_active_mode()
        # 设置按钮字体颜色
        self.pushButton_active.setStyleSheet("QPushButton {color: green}" if is_active_mode else "QPushButton {color: black}")
        self.pushButton_passive.setStyleSheet("QPushButton {color: black}" if is_active_mode else "QPushButton {color: green}")

    def open_passive_mode(self):
        # 打开被动模式
        is_passive_mode = control.open_passive_mode()
        # 设置按钮字体颜色
        self.pushButton_passive.setStyleSheet("QPushButton {color: green}" if is_passive_mode else "QPushButton {color: black}")
        self.pushButton_active.setStyleSheet("QPushButton {color: black}" if is_passive_mode else "QPushButton {color: green}")


if __name__ == "__main__":


    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    #创建QApplication 固定写法
    app = QApplication(sys.argv)
    # 实例化界面
    window = MainWindow()
    #显示界面
    window.show()
    #阻塞，固定写法
    sys.exit(app.exec_())