from queue import Queue

import myo


class MyoCollection(myo.DeviceListener):

    def __init__(self, emg_data_queue: Queue):
        super().__init__()
        self.emg_data_queue = emg_data_queue

    def on_connected(self, event):
        print(f"{event.device_name} 已连接")
        event.device.stream_emg(True)   # 开启电磁信号采集

    def on_disconnected(self, event):
        print(f"{event.device_name} 已断开")

    def on_emg(self, event):
        print(event.emg)
        self.emg_data_queue.put(event.emg)



