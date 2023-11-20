import sys
import time
from queue import Queue
import myo
import nidaqmx
import threading
from PySide6.QtCore import QObject, Slot, Signal, Property
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
PRESSURE_DATA_QUEUE = Queue()

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


class MyoCollection(myo.DeviceListener):

    def __init__(self, sync_queue: Queue):
        super().__init__()
        self.sync_queue = sync_queue

    def on_connected(self, event):
        print(f"{event.device_name} 已连接")
        event.device.stream_emg(True)  # 开启电磁信号采集

    def on_disconnected(self, event):
        print(f"{event.device_name} 已断开")

    def on_emg(self, event):
        print(f"{get_current_time()}: {event.emg}")
        # EMG_DATA_QUEUE.put(event.emg)
        self.sync_queue.put(event.emg)





class NidCollection:

    def __init__(self,  sync_queue: Queue, controls_queue: Queue, NUM_CHANNELS=5, RATE=200 / 5, SP=10):
        self.NUM_CHANNELS = NUM_CHANNELS
        self.RATE = RATE
        self.SP = SP
        self.status = True
        self.sync_queue = sync_queue
        self.controls_queue = controls_queue

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
                    self.sync_queue.put(new_data)
                    self.controls_queue.put(new_data)

                except Exception as e:
                    print(e)
                    pass
                return 0

            # 注册回调函数，就如函数名称，每采集n个样品到buffer触发事件，调用回到函数
            task.register_every_n_samples_acquired_into_buffer_event(self.SP, read_callback)
            while True:
                if not self.status:
                    break


class DataVisualization(QObject):
    nidStatusChanged = Signal(bool)
    myoStatusChanged = Signal(bool)


    def __init__(self):
        super().__init__()
        self._emg_data = [0] * 8
        self._nid_data = [0] * 5
        self._pressure_data = [0] * 5

        self.nid_sync_queue = Queue()
        self.controls_queue = Queue()
        self.myo_sync_queue = Queue()

        # 气压控制对象
        self.pre_com_name = 'COM4'
        self.pre_com_baud = 38400
        self.valve_com_name = 'COM7'
        self.valve_com_baud = 9600
        self.pressure_control = Control(self.pre_com_name, self.pre_com_baud, self.valve_com_name, self.valve_com_baud)
        self.pressure_control.need_show = [1]   # 需要打印的手指 0~4
        self.pressure_control.response_threshold = 0.01  # 采样电压灵敏度控制 单位v 值越小 执行气压控制的频率越高

        # nid采集对象
        self.nid_collection = NidCollection(self.nid_sync_queue, self.controls_queue)

        # myo采集对象
        self.myo_collection = MyoCollection(self.myo_sync_queue)
        myo.init(sdk_path=r'myo-sdk-win-0.9.0')
        self.myo_hub = myo.Hub()



    @Slot()
    def nid_start(self):
        nid_thread = threading.Thread(target=self.nid_collection.run)
        nid_thread.start()
        self.nid_collection.status = True
        self.nidStatusChanged.emit(self.nid_collection.status)

    @Slot()
    def nid_stop(self):
        self.nid_collection.status = False
        self.nidStatusChanged.emit(self.nid_collection.status)

    @Slot()
    def myo_start(self):
        print("myo start")
        myo_thread = threading.Thread(target=self.myo_hub.run, args=(self.myo_collection, 200))
        myo_thread.start()
        self.myoStatusChanged.emit(self.myo_hub.running)
        print(f"{self.myo_hub.running=}")

    @Slot()
    def myo_stop(self):
        self.myo_hub.stop()
        self.myoStatusChanged.emit(self.myo_hub.running)

    @Slot(result=bool)
    def pressure_control_switch(self):
        return self.pressure_control.switch()

    @Property(bool, notify=nidStatusChanged)
    def nid_status(self):
        return self.nid_collection.status

    @Property(bool, notify=myoStatusChanged)
    def myo_status(self):
        return self.myo_hub.running



    #  Angular

if __name__ == '__main__':
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()
    # 注册 DataVisualization 类型
    qmlRegisterType(DataVisualization, 'DataVisualization', 1, 0, 'DataVisualization')
    engine.load('visualization.qml')

    if not engine.rootObjects():
        sys.exit(-1)
    print(engine.rootObjects())
    sys.exit(app.exec())



