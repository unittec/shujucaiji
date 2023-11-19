import binascii
import time
import serial
import threading
from queue import Queue
from CRC16 import crc16Add


def get_current_time():
    current_time = time.time()
    milliseconds = int((current_time - int(current_time)) * 1000)
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_time))
    return f"{formatted_time}.{milliseconds:03d}"


class ValveControls:
    """
    设备控制类
    """
    __open_rtu = ("FE050000FF009835", "FE050001FF00C9F5", "FE050002FF0039F5", "FE050003FF006835", "FE050004FF00D9F4",
                  "FE050005FF008834", "FE050006FF007834", "FE050007FF0029F4", "FE050008FF0019F7", "FE050009FF004837")
    # 共十个电磁阀，两个组成一路，每两个对应一路的两个电磁阀的开
    __close_rtu = ("FE0500000000D9C5", "FE05000100008805", "FE05000200007805", "FE050003000029C5", "FE05000400009804",
                   "FE0500050000C9C4", "FE050006000039C4", "FE05000700006804", "FE05000800005807", "FE050009000009C7")

    __open_all_rtu = "FE0F0000001002FFFFA664"
    __close_all_rtu = "FE0F00000010020000A7D4"

    def __init__(self, com_name, com_baud):
        self.com_name = com_name  # 串口名称
        self.com_baud = com_baud  # 串口波特率
        self.com_interval = 0.01  # 串口读取间隔时间

        self.com = serial.Serial(port=self.com_name, baudrate=self.com_baud, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                                 bytesize=serial.EIGHTBITS, timeout=self.com_interval)
        print(f'串口:{self.com_name} 打开成功' if self.com.isOpen() else f'串口:{self.com_name} 打开失败')

    def send_data(self, data: str):
        if self.com.isOpen():
            send_hex_data = binascii.a2b_hex(data)
            self.com.write(send_hex_data)
            self.com.flushOutput()  # 清空发送缓冲区，达到直接发送目的

    def open_valves(self, rtu_index_list: list):
        for rtu_index in rtu_index_list:
            self.send_data(self.__open_rtu[rtu_index])

    def close_valves(self, rtu_index_list: list):
        for rtu_index in rtu_index_list:
            self.send_data(self.__close_rtu[rtu_index])

    def open_all_valves(self):
        self.send_data(self.__open_all_rtu)

    def close_all_valves(self):
        self.send_data(self.__close_all_rtu)

    def refresh_valves_status(self, status_list: list[bool]):
        """
        刷新所有电磁阀状态
        :param status_list: bool列表 对应16个通道的状态 0:关闭 1:打开 下标对应顺序 -1 ~ -16
        """
        assert len(status_list) == 16, "传入的bool列表长度不为16!"
        bool_list = status_list[8:] + status_list[:8]
        binary_str = ''.join(str(int(status)) for status in bool_list)
        hex_str = hex(int(binary_str, 2))
        hex_upper_str = hex_str[2:].upper()
        self.send_data(self.__open_all_rtu.replace("FFFF", hex_upper_str))


class PressureControls:
    __set_rtu = 'FE06000'
    __set_all_rtu = 'FE100000000A14'

    def __init__(self, com_name, com_baud):
        self.com_name = com_name
        self.com_baud = com_baud
        self.com_interval = 0.01  # 串口读取间隔时间

        self.com = serial.Serial(port=self.com_name, baudrate=self.com_baud, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                                 bytesize=serial.EIGHTBITS)
        print(f'串口:{self.com_name} 打开成功' if self.com.isOpen() else f'串口:{self.com_name} 打开失败')

    def set_pressure(self, address: int, pressure: int):
        """设置指定通道的气压"""
        voltage = int((pressure * 100) / 9)
        voltage_high = int(voltage / 256)
        voltage_low = int(voltage % 256)
        str_voltage_high = '{:02X}'.format(voltage_high)  # 0意味着补零，2是要求输出两位数，x代表十六进制数，大写X生成大写十六进制数
        str_voltage_low = '{:02X}'.format(voltage_low)
        crc16_input = f"{self.__set_rtu}{address}{str_voltage_high}{str_voltage_low}"
        set_rtu_whole = crc16Add(crc16_input)
        set_rtu_whole = set_rtu_whole.replace(" ", "")
        set_hex_data = binascii.a2b_hex(set_rtu_whole)  # 十六进制
        self.com.write(set_hex_data)
        # print(f'{get_current_time()}:{self.com_name} 发送数据: {set_rtu_whole}')
        self.com.flushOutput()  # 清空发送缓冲区，达到直接发送目的
        time.sleep(0.01)

    def set_all_pressure(self, pressure_t: ()):
        """设置1-5通道的气压"""
        pressure_hex_list = "".join([self.pressure2hex(pressure) for pressure in pressure_t])
        pressure_hex_list = f"{self.__set_all_rtu}{pressure_hex_list}{'00' * 10}"
        set_rtu_whole = crc16Add(pressure_hex_list).replace(" ", "")
        set_hex_data = binascii.a2b_hex(set_rtu_whole)
        self.com.write(set_hex_data)
        # self.com.flushOutput()  # 清空发送缓冲区，达到直接发送目的
        # print(f"set_all_pressure:{set_rtu_whole}")

    def pressure2hex(self, pressure: int):
        voltage = int((pressure * 100) / 9)
        voltage_high = int(voltage / 256)
        voltage_low = int(voltage % 256)
        return f"{'{:02X}'.format(voltage_high) }{'{:02X}'.format(voltage_low)}"

class Control:
    """
    计算公式：
    α1 = 454.54 * v1 - 1304.54
    α2 = 857.14 * v2 - 2537.14
    α3 = 857.14 * v3 - 2417.14
    α4 = 857.14 * v4 - 2511.43
    α5 = 937.50 * v5 - 2221.87
    P1 = 1.33 * α1
    P2 = 1.67 * α2
    P3 = 1.67 * α3
    P4 = 0.83 * α4
    P5 = 0.67 * α5
    """

    def __init__(self, p_com_name, p_com_baud, v_com_name, v_com_baud):
        # 气压控制
        self.pressureControls = PressureControls(p_com_name, p_com_baud)
        # 电磁阀控制
        self.valveControls = ValveControls(v_com_name, v_com_baud)
        # # 五指电压->气压 顺序: 大拇指->小指
        self.getP_list = [
            lambda v, v_min=2.87, v_max=3.20, p_max=200: ((v - v_min) / (v_max - v_min)) * p_max if v_min <= v <= v_max else 0,
            lambda v, v_min=2.96, v_max=3.17, p_max=300: ((v - v_min) / (v_max - v_min)) * p_max if v_min <= v <= v_max else 0,
            lambda v, v_min=2.82, v_max=3.03, p_max=300: ((v - v_min) / (v_max - v_min)) * p_max if v_min <= v <= v_max else 0,
            lambda v, v_min=2.93, v_max=3.14, p_max=150: ((v - v_min) / (v_max - v_min)) * p_max if v_min <= v <= v_max else 0,
            lambda v, v_min=2.37, v_max=2.53, p_max=100: ((v - v_min) / (v_max - v_min)) * p_max if v_min <= v <= v_max else 0
        ]
        # 电磁阀状态列表
        self.valve_status_list = [True] * 16                # 从-1开始 每两个对应一路的两个电磁阀的开或者关
        # 记录上一次发送的电磁阀状态
        self.last_valve_status_list = [True] * 16           # 从-1开始 每两个对应一路的两个电磁阀的开或者关
        # NID卡实时电压值队列
        self.nid_queue = Queue()                            # 每一帧数据为一个列表元组 顺序: 大拇指->小指
        # 记录上一次入队的电压值
        self.last_put_queue_t = (0,) * 5                    # 初始化为0 顺序: 大拇指->小指
        # 上一次发送气压值
        self.last_pressure_t = (0,) * 5                     # 初始化为0 顺序: 大拇指->小指
        # 控制响应阈值  # 对采集的电压值的敏感度 最新一帧电压值相较于上一帧的变化范围
        self.response_threshold = 0.01
        # 降采样触发阈值  # 当队列里面堆积的待处理数据超过10 执行一次降采样，去除10个 处理最新的那1个
        self.down_sample_counter = 10
        # 手指伸直判断 角度映射到气压的阈值  # 当输出气压超过指的的气压值，输出气压被指定为0
        self.p_threshold = [200, 300, 300, 150, 100]    # 对应五指 大拇指~小指

        # 控制开关
        self.k = False
        # 开关改变信号
        self.change = False
        # 需要打印信息的手指
        self.need_show = []

        # 创建线程
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        """线程运行函数"""
        print(f'{get_current_time()}: 控制线程启动')
        # 进入循环
        while True:
            # 记录进入时间
            start_time = time.time_ns()
            # 如果开关状态改变
            if self.change:
                if not self.k:  # 关闭状态
                    for i in range(5):
                        self.pressureControls.set_all_pressure((0,) * 5)
                    self.valveControls.close_all_valves()
                    print("控制关闭")
                else:           # 打开状态
                    print("控制打开")
                    self.valveControls.open_all_valves()
                # 改变信号复位
                self.change = False
            # 如果开关为关闭状态
            if not self.k:
                time.sleep(0.1)  # 线程休眠0.1s
                continue

            # 从队列中获取数据 如果队列为空则阻塞线程
            nid_queue_t = self.nid_queue.get()
            # 判断是否需要响应 如果本次入队电压值与上次入队电压值相差小于阈值
            if all(abs(nid_queue_t[i] - self.last_put_queue_t[i]) < self.response_threshold for i in range(5)):
                self.nid_queue.task_done()
                continue
            # 判断是否需要降采样
            if self.nid_queue.qsize() > self.down_sample_counter:
                for _ in range(self.down_sample_counter):
                    self.nid_queue.get()
                    self.nid_queue.task_done()
                nid_queue_t = self.nid_queue.get()
            # 记录本次入队的电压值
            self.last_put_queue_t = nid_queue_t
            # 计算气压值
            p_t = tuple(self.getP_list[i](nid_queue_t[i]) for i in range(5))
            # 判断是否伸直 伸直时气压为0
            valve_status_list = [True] * 16
            for i in range(5):
                if p_t[i] > self.p_threshold[i]:
                    valve_status_list[i * 2] = False
                    valve_status_list[i * 2 + 1] = False
                    p_t[i] = 0
            # 更新电磁阀状态 如果有任意一个电磁阀状态更新 则发送控制命令 同时输出多路电磁阀控制命令
            if valve_status_list != self.last_valve_status_list:
                self.valveControls.refresh_valves_status(valve_status_list)
                self.last_valve_status_list = valve_status_list
            # 更新气压值 如果有任意一个气压值更新 则发送控制命令 同时输出多路气压控制命令
            if p_t != self.last_pressure_t:
                self.pressureControls.set_all_pressure(p_t)
                self.last_pressure_t = p_t
                # print(f'发送:{p_t}')
            # 通知队列任务完成
            self.nid_queue.task_done()
            # 判断是否需要打印信息
            print(f"{p_t}")
            if self.need_show:
                for i in range(5):
                    if i not in self.need_show:
                        continue
                    run_time = (time.time_ns() - start_time) / 1000000  # 在这里计算本次循环耗时
                    print(f'{get_current_time()}: {i}指气压: {p_t[i]:.2f}kPa  采集电压: {nid_queue_t[i]:.2f}V  '
                          f'队列堆积:{self.nid_queue.qsize()}  运行时间: {run_time:.6f}ms')



    def switch(self):
        self.k = not self.k
        self.change = True
        return self.k


if __name__ == '__main__':
    ...
