import csv
import random
import sys
import time
from queue import Queue
import myo
import nidaqmx
import threading
from PySide6.QtCore import QObject, Slot, Signal, Property, QPointF
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide6.QtWidgets import QApplication
from nidaqmx import constants
from nidaqmx.constants import TerminalConfiguration
from Control import Control


"""数据队列"""
# myo数据队列 元素为列表 长度为8
EMG_DATA_QUEUE = Queue()
# 电压数据队列 元素为列表 长度为5
NID_DATA_QUEUE = Queue()
# 气压数据队列 元素为列表 长度为5
# PRESSURE_DATA_QUEUE = Queue()

# """控制类"""
# # 串口配置
# pre_com_name, pre_com_baud = 'COM4', 38400
# valve_com_name, valve_com_baud = 'COM7', 9600
# CONTROL = Control(pre_com_name, pre_com_baud, valve_com_name, valve_com_baud)
# # 需要打印的手指 0~4
# CONTROL.need_show = [1]
# # 采样电压灵敏度控制 单位v 值越小 执行气压控制的频率越高
# CONTROL.response_threshold = 0.01



def get_current_time():
    current_time = time.time()
    milliseconds = int((current_time - int(current_time)) * 1000)
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_time))
    return f"{formatted_time}.{milliseconds:03d}"

def get_current_time_2():
    current_time = time.time()
    milliseconds = int((current_time - int(current_time)) * 1000)
    formatted_time = time.strftime("%Y-%m-%d__%H-%M-%S", time.localtime(current_time))
    return f"{formatted_time}.{milliseconds:03d}"


class MyoCollection(myo.DeviceListener):

    def __init__(self):
        super().__init__()

    def on_connected(self, event):
        print(f"{event.device_name} 已连接")
        event.device.stream_emg(True)  # 开启电磁信号采集

    def on_disconnected(self, event):
        print(f"{event.device_name} 已断开")

    def on_emg(self, event):
        # print(f"___ {get_current_time()}: {event.emg}")
        EMG_DATA_QUEUE.put(event.emg)





class NidCollection():

    def __init__(self, NUM_CHANNELS=5, RATE=1000, SP=10):
        self.NUM_CHANNELS = NUM_CHANNELS
        self.RATE = RATE
        self.SP = SP
        self.status = True

    def run(self):

        with nidaqmx.Task() as task:
            for i in range(self.NUM_CHANNELS):
                task.ai_channels.add_ai_voltage_chan("Dev/ai{}".format(i), name_to_assign_to_channel="AI{}".format(i),
                                                     terminal_config=TerminalConfiguration.RSE, max_val=10, min_val=-10)
            task.timing.cfg_samp_clk_timing(self.RATE, sample_mode=constants.AcquisitionType.CONTINUOUS,
                                            samps_per_chan=20)  # 一直采，直到停止任务

            def read_callback(task_handle, every_n_samples_event_type, number_of_samples, callback_data):
                try:
                    data = task.read(number_of_samples_per_channel=number_of_samples)
                    # 在这里获取最新的电压值 入队
                    new_data = tuple(data[i][-1] for i in range(self.NUM_CHANNELS))
                    NID_DATA_QUEUE.put(new_data)
                    # print(f"{get_current_time()}:")


                except Exception as e:
                    print(e)
                    pass
                return 0

            # 注册回调函数，就如函数名称，每采集n个样品到buffer触发事件，调用回到函数
            task.register_every_n_samples_acquired_into_buffer_event(self.SP, read_callback)
            task.start()
            while True:
                if not self.status:
                    break
                time.sleep(0.01)


class DataVisualization(QObject):
    nidStatusChanged = Signal(bool)
    myoStatusChanged = Signal(bool)
    emgDataChanged = Signal(list)
    nidDataChanged = Signal(list)
    nidRangeChanged = Signal(list)

    def __init__(self):
        super().__init__()
        self._emg_data = [[] for _ in range(8)]
        self._nid_data = [[] for _ in range(5)]
        self._emg_data_csv = [[] for _ in range(8)]
        self._nid_data_csv = [[] for _ in range(5)]
        self._max_show_length = 50

        self._nid_range = [0, 3.0]

        # nid采集对象
        self.nid_collection = NidCollection()
        # myo采集对象
        self.myo_collection = MyoCollection()
        myo.init(sdk_path=r'myo-sdk-win-0.9.0')
        self.myo_hub = myo.Hub()

        # 启动数据采集线程
        self._thread_sleep_time = 0.01
        self.get_nid_data_thread = threading.Thread(target=self.get_nid_data)
        self.get_nid_data_thread.start()
        self.get_emg_data_thread = threading.Thread(target=self.get_emg_data)
        self.get_emg_data_thread.start()

        self.nid_state = False
        self.myo_state = False
        self.start_flag = False

    @Slot()
    def nid_start(self):
        if self.nid_state:
            return
        nid_thread = threading.Thread(target=self.nid_collection.run)
        nid_thread.start()
        self.nid_collection.status = True
        self.nidStatusChanged.emit(self.nid_collection.status)
        self.nid_state = True
        print("nid start")

    @Slot()
    def nid_stop(self):
        if not self.nid_state:
            return
        self.nid_collection.status = False
        self.nidStatusChanged.emit(self.nid_collection.status)
        self.nid_state = False

    @Slot()
    def myo_start(self):
        if self.myo_state:
            return
        myo_thread = threading.Thread(target=self.myo_hub.run, args=(self.myo_collection, 0))
        myo_thread.start()
        self.myoStatusChanged.emit(self.myo_hub.running)
        self.myo_state = True
        print("myo start")
        # print(f"{self.myo_hub.running=}")

    @Slot()
    def myo_stop(self):
        if not self.myo_state:
            return
        self.myo_hub.stop()
        self.myoStatusChanged.emit(self.myo_hub.running)
        self.myo_state = False
        self.start_flag = False

    # @Slot()
    # def control_switch(self):
    #     CONTROL.switch()

    @Property(list, notify=nidRangeChanged)
    def nid_range(self):
        return self._nid_range

    @Property(bool, notify=nidStatusChanged)
    def nid_status(self):
        return self.nid_collection.status

    @Property(bool, notify=myoStatusChanged)
    def myo_status(self):
        return self.myo_hub.running

    @Property(list, notify=nidDataChanged)
    def nid_data(self):
        return self._nid_data

    @Property(list, notify=emgDataChanged)
    def emg_data(self):
        return self._emg_data

    def get_emg_data(self):
        start_time = time.time()
        while EMG_DATA_QUEUE.get(): # 每次进入循环时额外消耗一条数据 5ms->10ms
            EMG_DATA_QUEUE.task_done()  # 通知队列
            new_data = EMG_DATA_QUEUE.get() # 取当前队列最早数据
            EMG_DATA_QUEUE.task_done()
            # print(f"myo: {get_current_time()}")
            self.start_flag = True

            for i in range(8):
                self._emg_data_csv[i].append(new_data[i])
                if len(self._emg_data_csv[i]) > self._max_show_length:
                    self._emg_data[i] = self._emg_data_csv[i][-self._max_show_length:]
                else:
                    self._emg_data[i] = self._emg_data_csv[i]
            self.emgDataChanged.emit(self._emg_data)



    def get_nid_data(self):
        # 10ms
        while True:
            new_data = NID_DATA_QUEUE.get()
            if not self.start_flag:
                continue
            # print(f"nid: {get_current_time()}")
            # 计算电压值范围
            self._nid_range[0] = self._nid_range[0] if self._nid_range[0] > min(new_data) else min(new_data) - 0.1
            self._nid_range[1] = self._nid_range[1] if self._nid_range[1] > max(new_data) else max(new_data) + 0.1

            self.nidRangeChanged.emit(self._nid_range)
            for i in range(5):
                self._nid_data_csv[i].append(new_data[i])
                # 取最新的数据
                if len(self._nid_data_csv[i]) > self._max_show_length:
                    self._nid_data[i] = self._nid_data_csv[i][-self._max_show_length:]
                else:
                    self._nid_data[i] = self._nid_data_csv[i]
            self.nidDataChanged.emit(self._nid_data)
            # print(f"{get_current_time()} {new_data}")

    @Slot()
    def write_to_csv(self):
        # file_name, data, field_names
        print('write_to_csv')
        print(f"emg: {len(self._emg_data_csv[0])}")
        print(f"nid: {len(self._nid_data_csv[0])}")
        file_name = f"{get_current_time_2()}.csv"
        field_names = ['nid_1', 'nid_2', 'nid_3', 'nid_4', 'nid_5',
                       'emg_1', 'emg_2', 'emg_3', 'emg_4', 'emg_5', 'emg_6', 'emg_7', 'emg_8']
        # 确保emg和nid数据长度一致，以长度短的为准
        data = []
        if self._emg_data_csv[0] > self._nid_data_csv[0]:
            for i in range(len(self._nid_data_csv[0])):
                nid_data = [self._nid_data_csv[j][i] for j in range(5)]
                emg_data = [self._emg_data_csv[j][i] for j in range(8)]
                data.append(nid_data + emg_data)
        else:
            for i in range(len(self._emg_data_csv[0])):
                nid_data = [self._nid_data_csv[j][i] for j in range(5)]
                emg_data = [self._emg_data_csv[j][i] for j in range(8)]
                data.append(nid_data + emg_data)

        with open(file_name, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(field_names)
            transposed_data = zip(*data)
            csv_writer.writerows(transposed_data)

    @Slot()
    def clear(self):
        # 如果采集线程未停止 则先关闭线程
        if self.myo_state:
            self.myo_stop()
        if self.nid_state:
            self.nid_stop()
        print('清除')
        # 清空展示数据
        self._emg_data = [[] for _ in range(8)]
        self._nid_data = [[] for _ in range(5)]
        # 发出属性变化信号 通知页面更新
        self.emgDataChanged.emit(self._emg_data)
        self.nidDataChanged.emit(self._nid_data)
        # 清空csv数据
        self._emg_data_csv = [[] for _ in range(8)]
        self._nid_data_csv = [[] for _ in range(5)]

    def test_emg_data(self):
        # 向队列添加1~10之间的随机浮点数
        for i in range(8):
            self._emg_data[i].append(random.uniform(0.5, 9.5))
            if len(self._emg_data[i]) > self._max_show_length:
                self._emg_data[i] = self._emg_data[i][-self._max_show_length:]
            # 打印每个通道的数据
            # print(f"{i}= {self._emg_data[i]}")
            self.emgDataChanged.emit(self._emg_data)

    def test_nid_data(self):
        # 向队列添加1~10之间的随机数
        for i in range(5):
            self._nid_data[i].append(random.uniform(0.5, 4.5))
            if len(self._nid_data[i]) > self._max_show_length:
                self._nid_data[i] = self._nid_data[i][-self._max_show_length:]
            # 打印每个通道的数据
            # print(f"{i}= {self._nid_data[i]}")
            self.nidDataChanged.emit(self._nid_data)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()
    qmlRegisterType(DataVisualization, 'DataVisualization', 1, 0, 'DataVisualization')
    engine.load('main.qml')
    # engine.load('test.qml')
    if not engine.rootObjects():
        sys.exit(-1)
    sys.exit(app.exec())



