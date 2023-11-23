import threading
import time
from queue import Queue

import myo
def get_current_time():
    current_time = time.time()
    milliseconds = int((current_time - int(current_time)) * 1000)
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_time))
    return f"{formatted_time}.{milliseconds:03d}"

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
        # print(f"{get_current_time()}  MyoCollection: {event.emg}")
        self.emg_data_queue.put(event.emg)


if __name__ == '__main__':
    emg_data_queue = Queue()
#    myo.init(sdk_path=r"myo-sdk-win-0.9.0")     # 这是myo的sdk那个文件夹的路径
    myo.init(sdk_path=r"D:\ziliao\MYOinit\myo-sdk-win-0.9.0\myo-sdk-win-0.9.0")  # 这是myo的sdk那个文件夹的路径
    hub = myo.Hub()
    listener = MyoCollection(emg_data_queue)
    # hub.run(listener, 200)
    myo_thread = threading.Thread(target=hub.run, args=(listener, 0))
    myo_thread.start()
    # print(hub.running)
    # hub.run(listener, 10000)

    while True:

        print(f"{get_current_time()} queue: {emg_data_queue.get()}")
    # print(hub.running)

