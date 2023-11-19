import nidaqmx
from nidaqmx import constants
NUM_CHANNELS = 5
RATE = 100 / NUM_CHANNELS

with nidaqmx.Task() as task:
    for i in range(NUM_CHANNELS):
        task.ai_channels.add_ai_voltage_chan("Dev/ai{}".format(i), name_to_assign_to_channel="AI{}".format(i),
                                             max_val=10, min_val=-10)
    task.timing.cfg_samp_clk_timing(RATE, sample_mode=constants.AcquisitionType.CONTINUOUS,
                                    samps_per_chan=200)  # 一直采，直到停止任务
    # task.timing.cfg_samp_clk_timing(RATE,sample_mode=constants.AcquisitionType.FINITE,samps_per_chan=300000) #采集指定数量的样本

    channel1_data = []
    channel2_data = []
    channel3_data = []
    channel4_data = []
    channel5_data = []


    def read_callback(task_handle, every_n_samples_event_type,
                      number_of_samples, callback_data):

        ####################直接使用 read 函数 #############
        data = task.read(number_of_samples_per_channel=number_of_samples)
        # non_local_var['All samples'].extend(data)
        channel1_data.extend(data[0])
        channel2_data.extend(data[1])
        channel3_data.extend(data[2])
        channel4_data.extend(data[3])
        channel5_data.extend(data[4])

        return 0


    task.register_every_n_samples_acquired_into_buffer_event(
        100, read_callback)  # 注册回调函数，就如函数名称，每采集n个样品到buffer触发事件，调用回到函数

    task.start()

    while True:
        print(len(channel1_data))
