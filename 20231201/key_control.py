import binascii
import time
import crcmod
import serial
import threading
from binascii import *


test = True

def get_current_time():
    if test:
        return ''
    current_time = time.time()
    milliseconds = int((current_time - int(current_time)) * 1000)
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_time))
    return f"{formatted_time}.{milliseconds:03d}"

def crc16Add(read):
    """
    生成CRC16-MODBUS校验码
    :param read: 读取的数据
    :return: 返回带有CRC16校验码的数据
    """
    crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
    data = read.replace(" ", "")  # 消除空格
    readcrcout = hex(crc16(unhexlify(data))).upper()
    str_list = list(readcrcout)
    if len(str_list) == 5:
        str_list.insert(2, '0')  # 位数不足补0，因为一般最少是5个
    crc_data = "".join(str_list)  # 用""把数组的每一位结合起来  组成新的字符串
    read = read.strip() + ' ' + crc_data[4:] + ' ' + crc_data[2:4]  # 把源代码和crc校验码连接起来
    return read




class KeyMonitor:
    """
    按键监控类
    """

    def __init__(self, com_name, com_baud, key_handle_func):
        """
        初始化
        :param com_name:
        :param com_baud:
        """
        self.com_name = com_name                # 串口名称
        self.com_baud = com_baud                # 串口波特率
        self.key_handle_func = key_handle_func  # 按键处理函数
        self.curr_key = 0                       # 当前按键值
        self.com_interval = 0.009               # 串口读取间隔时间
        self.close_flag = False                 # 关闭标志位 默认为False

        # 打开串口
        self.com = serial.Serial(port=self.com_name, baudrate=self.com_baud, timeout=self.com_interval, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                                 bytesize=serial.EIGHTBITS)
        if self.com.isOpen():
            print(f'串口:{self.com_name} 打开成功')
        else:
            print(f'串口:{self.com_name} 打开失败')

        # 启动按键监控线程
        self.key_monitor_thread = threading.Thread(target=self.key_monitor, name='key_monitor_thread')
        self.key_monitor_thread.start()

    def key_monitor(self):
        """
        监控按键
        :return:
        """
        print(f"{get_current_time()} 按键监控线程启动")
        while self.close_flag is False:
            # 控制串口读取间隔时间 降低CPU占用率
            time.sleep(0.01)
            # 从串口读取数据 fixme:win32.GetOverlappedResult
            data = self.com.readline().decode('utf-8')
            # print(f"{get_current_time()} 串口数据:{data}")
            if data < '0':
                continue
            new_key = int(data)
            # 串口有数据时进行处理
            if 1 <= new_key <= 7:
                self.curr_key = new_key
                # print(f'调用按键处理{self.curr_key=}')
                self.key_handle_func(self.curr_key)  # 调用按键处理函数


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
        """
        初始化
        :param com_name:
        :param com_baud:
        """
        self.com_name = com_name  # 串口名称
        self.com_baud = com_baud  # 串口波特率
        self.com_interval = 0.01  # 串口读取间隔时间

        # 打开串口
        self.com = serial.Serial(port=self.com_name, baudrate=self.com_baud, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                                 bytesize=serial.EIGHTBITS, timeout=self.com_interval)
        if self.com.isOpen():
            print(f'串口:{self.com_name} 打开成功')
        else:
            print(f'串口:{self.com_name} 打开失败')

    def send_data(self, data: str):
        """
        发送数据
        :param data: 数据
        :return:
        """
        if self.com.isOpen():
            send_hex_data = binascii.a2b_hex(data)
            self.com.write(send_hex_data)
            # print(f'{get_current_time()}:{self.com_name} 发送数据: {data}')
            self.com.flushOutput()  # 清空发送缓冲区，达到直接发送目的

    def open_valves(self, rtu_index_list: list):
        """
        打开指定的电磁阀
        :param rtu_index_list: rtu下标列表
        :return:
        """
        for rtu_index in rtu_index_list:
            self.send_data(self.__open_rtu[rtu_index])

    def close_valves(self, rtu_index_list: list):
        """
        关闭指定的电磁阀
        :param rtu_index_list: rtu下标列表
        :return:
        """
        for rtu_index in rtu_index_list:
            self.send_data(self.__close_rtu[rtu_index])

    def open_all_valves(self):
        """打开所有电磁阀"""
        self.send_data(self.__open_all_rtu)

    def close_all_valves(self):
        """关闭所有电磁阀"""
        self.send_data(self.__close_all_rtu)


class PressureControls:
    """
    气压控制类
    """
    __set_rtu = 'FE06000'

    def __init__(self, com_name, com_baud):
        """
        初始化
        :param com_name:
        :param com_baud:
        """
        self.com_name = com_name
        self.com_baud = com_baud
        self.com_interval = 0.01  # 串口读取间隔时间

        # 打开串口
        self.com = serial.Serial(port=self.com_name, baudrate=self.com_baud, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                                 bytesize=serial.EIGHTBITS)
        if self.com.isOpen():
            print(f'串口:{self.com_name} 打开成功')
        else:
            print(f'串口:{self.com_name} 打开失败')

    def set_pressure(self, address: int, pressure: int):
        """
        设置气压
        :param pressure:
        :return:
        """
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
        print(f'{get_current_time()}:{self.com_name} 发送数据: {set_rtu_whole}')
        self.com.flushOutput()  # 清空发送缓冲区，达到直接发送目的


if __name__ == '__main__':

    # 串口信息
    pre_com_name, pre_com_baud = 'COM4', 38400
    valve_com_name, valve_com_baud = 'COM10', 9600
    keys_com_name, keys_com_baud = 'COM12', 38400

    # 气压值序列
    pressure_sequence = [200, 300, 300, 100, 150]

    # 初始化气压控制类
    pressure_controls = PressureControls(pre_com_name, pre_com_baud)

    # 初始化电磁阀控制类
    valve_controls = ValveControls(valve_com_name, valve_com_baud)

    def key_handle_func1(key_number: int):
        """处理按键1~5 设置气压并打开对应的电磁阀"""
        if 1 <= key_number <= 5:
            start_index = (key_number - 1) * 2
            end_index = start_index + 1
            pressure_value = pressure_sequence[key_number - 1]
            # 设置气压
            pressure_controls.set_pressure(key_number-1, pressure_value)
            # 打开电磁阀
            valve_controls.open_valves([start_index, end_index])
            print(f"打开阀门{start_index=} {end_index=} 设置气压:{pressure_sequence[key_number - 1]}")
        else:
            print(f"按键编号错误:{key_number=}")

    def key_handle_func2():
        """处理按键6 打开所有电磁阀"""
        # 设置气压
        for i, v in enumerate(pressure_sequence):
            pressure_controls.set_pressure(i, v)
        # 开启所有电磁阀
        valve_controls.open_all_valves()

    def key_handle_func3():
        """处理按键3 关闭所有电磁阀"""
        # 设置气压
        for i, v in enumerate(pressure_sequence):
            pressure_controls.set_pressure(i, 0)
        # 关闭所有电磁阀
        valve_controls.close_all_valves()

    def key_handle_func(num: int):
        """按键处理方法"""
        if num == 6:
            print(f"处理按键6")
            key_handle_func2()
        elif num == 7:
            print(f"处理按键7")
            key_handle_func3()
        elif 1 <= num <= 5:
            print(f"处理按键{num}")
            key_handle_func1(num)
        else:
            print(f"按键编号错误:{num=}")

    # 初始化按键监控类
    key_monitor = KeyMonitor(keys_com_name, keys_com_baud, key_handle_func)
    # input('按任意键退出:')
    # key_monitor.close_flag = True

