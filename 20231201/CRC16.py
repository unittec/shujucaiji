from binascii import *
import crcmod


# 生成CRC16-MODBUS校验码
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


# if __name__ == '__main__':
#     crc16Add("FE 06 00 00 03 20")
