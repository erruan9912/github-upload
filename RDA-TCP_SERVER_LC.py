#声明所调用的库函数
import serial                  #R232串口打开函数
import time                    #加载时间函数
import datetime                #加载获取时间函数
#from selenium import webdriver #加载网页操作函数webdriver   本脚本中使用splinter函数未用到selenium，留存备用
from time import sleep        #加载睡眠函数
import re                     #加载正则匹配函数
import random                 #加载随机数函数
import winsound               #加载播放器函数
import signal
import os,sys
import threading            # 加入多线程
from threading import currentThread
from threading import Thread
#A区域
#脚本编写日期及编写人员--------------------------------------------------------------------
#V1.0--Fester--20200106
#脚本逻辑
# 1.模块开机配置完成后，执行找网动作
# 2.找网成功后，模块连接sercer
# 3.进入监听模式下
# 4.监听到数据发送
# 5.循环3-4
# =================================修改=====================================
#3.2修改
# 1. QSCKK=2
# 2. 增加server端接收到recv后等待3s后回复client端
# 3. 2s一次连接其他server端修改为120s
# 4. 去掉重传机制.

# 3.3修改
# 1.fake_vlaue值修改为可配置
# 2.修改server端收到数据后等待Xs后回复server，X为可配置

#B区域
#=========================================================================
#EVB说明：普通NB EVB即可
#注意事项：
#测试前保持开机状态。
#与Client端脚本一同使用
#注意查看打印消息
#=========================================================================

#用户可以配置变量
#=========================================================================
#Uart_port_server = "com102"    #server串口号

print("输入模块主串口端口号，如端口45，格式 com45")
Uart_port_server = input("commxx: ")

Baud_rate = 9600             #定义打开串口使用的波特率
#ue_type = "BC32-NB"            #请填写BC25 或BC32-NB或BC32-GSM,当为BC32模块使将会查询网络优先级，BC25不支持，此项设置错误影响开机找网时间判断

print("请填写BC25 或BC32-NB或BC32-GSM,当为BC32模块使将会查询网络优先级")
ue_type = input("ue_type:")

#pdp_type = "IP"             #请添加IP IPV6或IPV4V6，使用正则匹配方式不同

print("请添加IP IPV6或IPV4V6，使用正则匹配方式不同")
pdp_type = input("pdp_type:")

#GSM_APN = "CMNET"       #根据使用网络实际情况修改对应APN

print("若使用GSM网络请输入正确的GSM APN,若使用NB网络，随便填写一个字符串即可")
GSM_APN = input("GSM_APN:")

print("请输入fake_value值")
fake_value = input("FAKE_VALUE:")

print("请输入SERVER收到CLIENT数据后回复的延时时间")
server_recv_client_delay_time = int(input("server_recv_client_delay_time:"))

# UE_states = 0                 # 0---Connect,1---Idel,2---PSM
Access_mode = 1                 # 0---Buffer,1---Push
Data_type = 0                   # 0---Text,1---Hex
#=========================================================================
TCP_server_port = '2020'
Network_out_time = 720                 #找网超时时间

Data = "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
Data_len = len(Data)

#C区域
#=========================================================================
#脚本统计参数
Ram_leak_count = 0    # 内存泄漏
Alarm_times = 0
AT_timeout_times = 0    # AT超时
Socket_open_succ_times_server = 0    # server建立成功次数
Socket_open_fail_times_server = 0    # server建立失败次数
closed_times = 0    # 服务器异常断开连接
Ab_RDY_times_server = 0    # server异常重启
AT_error_times = 0    # 指令上报error
Network_succ_times_server = 0
Network_fail_times_server = 0
PCI_change_times = 0        #小区PCI变化次数
Send_succ_times_server = 0
Send_fail_times_server = 0
Recv_succ_times = 0
Server_abnormal_times = 0
Socket_open_times = 0
CLOSE_times = 0
CLOSE_succ_times = 0
recv_timeout_times = 0


#辅助参数
AT_timeout_10_server = 0
Sum_network_time_server = 0
Open_flag_server = 0
Recv_flag_server = 0
Sum_send_time_server = 0
Ab_RDY_flag = 0
Network_result_server = 0
Dtr_low = 0
Server_flag = 0
Old_PCI = 0
PCI_change_times_server = 0
cereg_0_times_server = 0
cereg_4_times_server = 0
Dur_ue_client_time = 0
Close_flag = 0
recv_flag = 0
data_fail = 0
#=========================================================================


def sigint_handler(signum, frame): #捕获ctrl+c信号
    num = int(input("请输入数字0或1,0代表退出脚本并统计信息,1代表继续执行脚本\n"))
    if num:
        print("你选择的数字为:", num, "即继续脚本不退出")
    else:
        print("你选择的数字为:", num, "即退出脚本并统计信息")
        Result_log_server.write("脚本运行时间： " + str(Script_start_time) + "---" + str(Script_end_time) + "\n")
        Result_log_server.write("总运行次数： " + str(Runtimes) + "\n")

        Result_log_server.write("找网成功次数： " + str(Network_succ_times_server) + "\n")
        Result_log_server.write("SERVER建立成功次数： " + str(Socket_open_succ_times_server) + "\n")
        Result_log_server.write("SERCER建立失败次数： " + str(Socket_open_fail_times_server) + "\n")

        Result_log_server.write("SERCER被连接次数： " + str(Socket_open_times) + "\n")

        Result_log_server.write("SERVER接收到的次数（Runtimes的3倍次数）： " + str(Recv_succ_times) + "\n")
        Result_log_server.write("SERVER发送成功次数（Runtimes的3倍次数）： " + str(Send_succ_times_server) + "\n")
        Result_log_server.write("SERVER发送失败次数： " + str(Send_fail_times_server) + "\n")

        #Result_log_server.write("server断开连接次数： " + str(closed_times) + "\n")recv_timeout_times
        Result_log_server.write("CLOSE次数： " + str(CLOSE_times) + "\n")
        Result_log_server.write("执行close成功次数： " + str(CLOSE_succ_times) + "\n")
        Result_log_server.write("超时20S未接收到数据得次数： " + str(recv_timeout_times) + "\n")
        Result_log_server.write("接收数据与发送长度不一致次数： " + str(data_fail) + "\n")

        Result_log_server.write("SERVER异常次数： " + str(Server_abnormal_times) + "\n")
        Result_log_server.write("模块端异常重启次数： " + str(Ab_RDY_times_server) + "\n")
        Result_log_server.write("模块端cereg4掉网次数： " + str(cereg_4_times_server) + "\n")
        Result_log_server.write("模块端cereg0掉网次数： " + str(cereg_0_times_server) + "\n")
        AT_log_server.close()
        DOS_log.close()
        Result_log_server.close()
        cmdport_server.close()
        sys.exit()

def Duration(time_per,time_now):
    try:
        time1 = datetime.datetime.strptime(str(time_per).strip(), '%Y-%m-%d %H:%M:%S.%f')
    except Exception as e:
        print("异常信息time1:", e)
        DOS_log.write("[" + str(datetime.datetime.now()) + " ] 异常信息time1:" + str(e) + "\n")
        DOS_log.flush()  # 刷新缓冲区
        time1 = datetime.datetime.strptime(str(time_per).strip(), '%Y-%m-%d %H:%M:%S')
    try:
        time2 = datetime.datetime.strptime(str(time_now).strip(), '%Y-%m-%d %H:%M:%S.%f')
    except Exception as e:
        print("异常信息time2:", e)
        DOS_log.write("[" + str(datetime.datetime.now()) + " ] 异常信息time2:" + str(e) + "\n")
        DOS_log.flush()  # 刷新缓冲区
        time2 = datetime.datetime.strptime(str(time_now).strip(), '%Y-%m-%d %H:%M:%S')
    Data_str=time2 -time1
    if re.compile("(\d+) day").findall(str(Data_str)):
        days = ','.join(re.compile("(\d+) day").findall(str(Data_str)))
    else:
        days = 0
    if re.compile("\d+:\d+:\d+.\d+").findall(str(Data_str)):
        hours = ','.join(re.compile("(\d+):\d+:\d+.\d+").findall(str(Data_str)))
        minutes = ','.join(re.compile("\d+:(\d+):\d+.\d+").findall(str(Data_str)))
        seconds = ','.join(re.compile("\d+:\d+:(\d+).\d+").findall(str(Data_str)))
        microseconds = ','.join(re.compile("\d+:\d+:\d+.(\d+)").findall(str(Data_str)))
    elif re.compile("\d+:\d+:\d+").findall(str(Data_str)):
        hours = ','.join(re.compile("(\d+):\d+:\d+").findall(str(Data_str)))
        minutes = ','.join(re.compile("\d+:(\d+):\d+").findall(str(Data_str)))
        seconds = ','.join(re.compile("\d+:\d+:(\d+)").findall(str(Data_str)))
        microseconds = 0
    else:
        hours = 0
        minutes = 0
        seconds = 0
        microseconds = 0
    Dur = int(days)*86400 + int(hours)*3600 + int(minutes)*60 + int(seconds) + int(microseconds)/1000000
    return Dur

def Execute_command_server(Command,response,timeout): #AT指令写入R232串口
    global AT_timeout_times
    global AT_timeout_10_server
    global AT_start_time
    global closed_times
    global Open_flag_server
    AT_error_times = 0                      #初始定义AT命令出错次数为0
    AT_timeout_times = 0                    #初始定义AT命令超时次数为0
    while 1:
        ATCommad = Command.encode("UTF-8")  # Python3 默认为ASCI（bytes） 类型需转码为UTF-8才能写入串口
        String_AT_W = str(ATCommad, encoding="utf-8", errors="strict")  # 将输入的AT命令编码为utf-8用于写入ATLOG文件
        cmdport_server.write(ATCommad)  # 将AT命令写入串口
        AT_log_server.write("[" + str(datetime.datetime.now()) + " Send]" + String_AT_W)
        AT_log_server.flush()
        AT_start_time = datetime.datetime.now()
        String_AT_R_buffer = ""
        while 1:
            global AT_error_flag         #引用全局变量
            global AT_timeout_flag       #引用全局变量
            global Cereg_sucess_server           #引用全局变量
            global cereg_4_times_server           #引用全局变量
            global cereg_0_times_server
            global UE_IMEI               #引用全局变量
            global SIM_IMSI              #引用全局变量
            global CSCON_state           #引用全局变量
            global PSM_state             #引用全局变量
            global Run_count              #引用全局变量
            global Ab_RDY_times_server
            global Ab_RDY_flag
            global Read_data_len
            global Remaining_len
            global Cgpaddr_new
            global Runtimes
            global SC_earfcn
            global SC_PCI
            global SC_rsrp
            global SC_rsrq
            global SC_rssi
            global SC_snr
            global SC_ecl
            global Dtr_low
            global CSW_ram
            global COS_ram
            global AT_state
            global Qping_result
            global Qping_delay_time
            global Close_flag
            global Open_flag
            global Read_data
            global TCP_server_ip
            global Network_result_server
            AT_error_flag = 0             #每次执行命令时先将AT_error_flag标志置0，包括内部重复执行处理同样标志位置0
            AT_timeout_flag = 0           #每次执行命令时先将AT_timeout_flag标志置0，包括内部重复执行处理同样标志位置0
            Str_R = cmdport_server.read(size=1024) #每次读取1024字节
            AT_end_time = datetime.datetime.now()
            ATtime = Duration(AT_start_time, AT_end_time)  # AT命令返回时间
           #============================超时处理===============================
            if ATtime > timeout and AT_timeout_times < 10:  # 执行AT命令超时处理方法
                AT_timeout_times += 1
                AT_log_server.write("[" + str(datetime.datetime.now()) + "]ATCommand执行超时: " + String_AT_W)
                AT_log_server.flush()
                if Command == "AT\r\n":  #当指令为AT时不做超时处理，直接退出，并将PSM状态置0
                    PSM_state = 0
                    return
                AT_timeout_flag = 1
                sleep(1)  # 等待1s
                AT_start_time = datetime.datetime.now()
                break
            elif ATtime > timeout and AT_timeout_times >= 10:
                AT_timeout_10_server += 1
                return  ##尝试发送10次后，若依然超时则退出循环不再尝试
            #==================================================================
            #if str(Str_R,encoding="utf-8", errors="strict") == "":
             #   continue
            if len(String_AT_R_buffer):  #buffer有内容时进行拼接后重置，避免重复拼接
                String_AT_R = String_AT_R_buffer + Str_R.decode(encoding="UTF-8", errors="strict")  # 将读取的串口数组转为UTF-8格式
                String_AT_R_buffer = ""
            else:
                String_AT_R = Str_R.decode(encoding="UTF-8", errors="strict")
            String_AT_R_array = String_AT_R.split('\r\n')       #以\r\n分割
            #当字符串以\r\n结尾时数组最后一个元素会是一个空串，如果不是以\r\n结尾则是读取到的部分URC，因此不需区分，均把数组最后一个元素拼接到下一个字符串即可
            String_AT_R_array_i = 0
            Run_count = len(String_AT_R_array)-1
            while String_AT_R_array_i < Run_count:
                AT_log_server.write("[" + str(datetime.datetime.now()) + " Recv]" + str(String_AT_R_array[String_AT_R_array_i])+'\n')  # 将读取的数据写入atlog文件中
                AT_log_server.flush()  # 刷新缓冲区
                String_AT_R_array_i = String_AT_R_array_i+1
            String_AT_R_buffer = String_AT_R_buffer+str(String_AT_R_array[Run_count])  #将最后一个数组元素取出用于和下个字符串拼接
            #================================正则匹配区========================================#
            String_AT_R_array_i = 0
            while String_AT_R_array_i < Run_count:
                c_list = str(String_AT_R_array[String_AT_R_array_i])
                String_AT_R_array_i = String_AT_R_array_i + 1
                #print("c_list_EX:"+c_list)
                if re.search("\+CGSN: (\d+)",c_list):
                    UE_IMEI = ','.join(re.compile('\+CGSN: (\d+)').findall(c_list))             #获取模块的IMEI
                elif ','.join(re.compile('\+CEREG: \d+').findall(c_list)) == "+CEREG: 4": #2020.02.20 arnold
                    cereg_4_times_server = cereg_4_times_server+1             #CEREG?查询返回1或者5判断为找网成功
                    Network_result_server = 0   #将网络标志置0，可以进入重新找网
                elif ','.join(re.compile('\+CEREG: \d+').findall(c_list)) == "+CEREG: 0": #2020.02.20 arnold
                    cereg_0_times_server = cereg_0_times_server+1             #CEREG?查询返回0为掉网
                    Network_result_server = 0  #将网络标志置0，可以进入重新找网
                elif ','.join(re.compile('\+CSCON: \d+').findall(c_list)) == "+CSCON: 1":   #2020.02.19 arnold 配置cscon检测
                    CSCON_state = 1
                    AT_log_server.write("[" + str(datetime.datetime.now()) + " ]UE当前处于Connect态!\n")
                    AT_log_server.flush()  # 刷新缓冲区
                elif ','.join(re.compile('\+CSCON: \d+').findall(c_list)) == "+CSCON: 0":
                    CSCON_state = 0
                    AT_log_server.write("[" + str(datetime.datetime.now()) + " ]UE当前处于IDEL态!使用QPING 包唤醒rrc...\n")
                    AT_log_server.flush()  # 刷新缓冲区
                    Execute_command_server("AT+QPING=1,\"180.101.147.115\",4,1\r\n", 'QPING: 2', 3)    #2020.02.19 arnold 配置cscon检测,qping唤醒rrc
                elif re.search("(\d+)",c_list)and Command=="AT+CIMI\r\n":
                    SIM_IMSI = ','.join(re.compile('(\d+)').findall(c_list))           #获取当前卡槽中SIM卡的IMSI号
                #elif ','.join(re.compile('\+CEREG: \d+,\d+').findall(c_list))=="+CEREG: 1,1" or ','.join(re.compile('\+CEREG: \d+,\d+').findall(c_list))=="+CEREG: 1,5":
                    #Cereg_sucess=1             #CEREG?查询返回1或者5判断为找网成功
                elif ','.join(re.compile('\+CEREG: \d+,\d+').findall(c_list))=="+CEREG: 1,0" or','.join(re.compile('\+CEREG: \d+,\d+').findall(c_list))=="+CEREG: 1,2" or ','.join(re.compile('\+CEREG: \d+,\d+').findall(c_list))=="+CEREG: 1,3" or ','.join(re.compile('\+CEREG: \d+,\d+').findall(c_list))=="+CEREG: 1,4":
                    Cereg_sucess_server = 0             #CEREG?查询返回2/3/4判断尚未找网成功
                elif re.search('\+CGPADDR: \d+,\S+,\S+', c_list):  #2020.02.27 arnold
                    Cereg_sucess_server = 1
                    Cgpaddr_new = ','.join(re.compile('\+CGPADDR: \d+,"(\S+)","\S+"').findall(c_list))
                    TCP_server_ip = Cgpaddr_new
                elif re.search('\+CGPADDR: \d+,\S+', c_list):  #2020.02.27 arnold
                    Cereg_sucess_server = 1
                    Cgpaddr_new = ','.join(re.compile('\+CGPADDR: \d+,"(\S+)"').findall(c_list))
                    TCP_server_ip = Cgpaddr_new
                elif re.search('\+QENG: 0,\d+,,\d+,\S+,\S+,\S+,\S+,\S+,\S+,\S+,\d+,\S+', c_list):
                    SC_earfcn = ','.join(re.compile('\+QENG: 0,(\d+),,\d+,\S+,\S+,\S+,\S+,\S+,\S+,\S+,\d+,\S+').findall(c_list))
                    SC_PCI = ','.join(re.compile('\+QENG: 0,\d+,,(\d+),\S+,\S+,\S+,\S+,\S+,\S+,\S+,\d+,\S+').findall(c_list))
                    SC_rsrp = ','.join(re.compile('\+QENG: 0,\d+,,\d+,\S+,(\S+),\S+,\S+,\S+,\S+,\S+,\d+,\S+').findall(c_list))
                    SC_rsrq = ','.join(re.compile('\+QENG: 0,\d+,,\d+,\S+,\S+,(\S+),\S+,\S+,\S+,\S+,\d+,\S+').findall(c_list))
                    SC_rssi = ','.join(re.compile('\+QENG: 0,\d+,,\d+,\S+,\S+,\S+,(\S+),\S+,\S+,\S+,\d+,\S+').findall(c_list))
                    SC_snr = ','.join(re.compile('\+QENG: 0,\d+,,\d+,\S+,\S+,\S+,\S+,(\S+),\S+,\S+,\d+,\S+').findall(c_list))
                    SC_ecl = ','.join(re.compile('\+QENG: 0,\d+,,\d+,\S+,\S+,\S+,\S+,\S+,\S+,\S+,(\d+),\S+').findall(c_list))

                elif re.search("GCHS:CSW:\d+,COS:\d+", c_list):  # 获取当前剩余内存
                    CSW_ram = ','.join(re.compile("GCHS:CSW:(\d+),COS:\d+").findall(c_list))
                    COS_ram = ','.join(re.compile("GCHS:CSW:\d+,COS:(\d+)").findall(c_list))

                elif re.search("\+QIRD: (\d+),(\d+),(\S+)", c_list):
                    Read_data_len = ','.join(re.compile('\+QIRD: (\d+),\d+,\S+').findall(c_list))
                    Remaining_len = ','.join(re.compile('\+QIRD: \d+,(\d+),\S+').findall(c_list))
                elif re.search("\+QIRD: (\d+),(\S+)", c_list):
                    Read_data_len = ','.join(re.compile('\+QIRD: (\d+),\S+').findall(c_list))
                    Read_data = ','.join(re.compile('\+QIRD: \d+,(\S+)').findall(c_list))

                elif re.search("\+QNBIOTEVENT: EXIT PSM", c_list):
                    PSM_state = 0  # 退出PSM成功
                elif ','.join(re.compile('\+QPING: \d+,\d+,\d+,\d+,\d+,\d+,\d+').findall(c_list)):
                    AT_log_server.write("[" + str(datetime.datetime.now()) + " Recv]" + 'Ping结束！！！\n')  # 将读取的数据写入atlog文件中
                    AT_log_server.flush()  # 刷新缓冲区
                elif ','.join(re.compile('\+QPING: \d+,\S+,\d+,\d+,\d+').findall(c_list)):
                    Qping_result = int(','.join(re.compile('\+QPING: (\d+),\S+,\d+,\d+,\d+').findall(c_list)))  # 获取Ping结果，0表示ping成功，1表示ping失败
                    Qping_delay_time = float(','.join(re.compile('\+QPING: \d+,\S+,\d+,(\d+),\d+').findall(c_list)))  # 获取Ping包时延值，单位ms

                # elif re.search("\+QIURC: \"closed\",(\d+)", c_list):  # +QIURC: "closed",0
                #     socket_id = ','.join(re.compile('\+QIURC: \"closed\",(\d+)').findall(c_list))
                #     Execute_command_server("AT+QICLOSE=" + socket_id + "\r\n", 'OK', 3)
                #     Close_flag = 1
                #     Open_flag = 0
                #     AT_log_server.write("[" + str(datetime.datetime.now()) + " ]" + 'client 断开连接！！！\n')  # 将读取的数据写入atlog文件中
                #     AT_log_server.flush()  # 刷新缓冲区
                #     closed_times = closed_times + 1

                elif re.search("RDY",c_list)and Command != "AT+QRST=1\r\n"and Runtimes > 0:
                    Execute_command_server("AT^FORCENOWDT=1\r\n", 'OK', 5)  # 打开遇到dump死机不重启，断电无法保存
                    Ab_RDY_flag = 1
                    Ab_RDY_times_server += 1
                #===============================================================================#
                if re.search(response,c_list):  # 匹配到指定的response后结束循环
                    #AT_log_server.flush()
                    if Command == "AT\r\n":
                        PSM_state = 1
                    return
                elif re.search('ERROR', c_list)and AT_error_times < 10:  # 执行命令返回ERROR处理方法
                    AT_error_flag = 1
                    AT_log_server.write("[" + str(datetime.datetime.now()) + "]ATCommand执行ERROR: " + String_AT_W)
                    AT_log_server.flush()
                    sleep(1)                        #等待1s
                    cmdport_server.write(ATCommad)         #重复发送AT命令
                    AT_log_server.write("[" + str(datetime.datetime.now()) + " Send]" + String_AT_W)
                    AT_log_server.flush()
                    AT_start_time = datetime.datetime.now()
                    AT_error_times += 1 #重复执行次数累计
                    break   #跳出第一层循环
                elif re.search('ERROR', c_list)and AT_error_times >= 10:  # 执行命令返回ERROR处理方法
                    DOS_log.write("[" + str(datetime.datetime.now()) + "]ATCommand执行ERROR: " + String_AT_W)
                    DOS_log.flush()
                    return                                                   #尝试发送10次后，若依然ERROR则退出循环不再尝试
            time.sleep(0.1)  # 间隔0.1s读一次串口

def UART_read_server(timeout):
    global Open_flag_server
    global Send_flag
    global Recv_flag_server
    global Send_end_time_server
    global Recv_end_time_server
    global Recv_date_len_server
    global Ab_RDY_times
    global Ab_RDY_flag
    global Dtr_low
    global Open_server
    global Read_start_time_server
    global Dur_read_time_server
    global Send_flag_server
    global Socket_open_succ_times_server
    global Socket_open_fail_times_server
    global Ab_RDY_times_server
    global Open_i_server
    global Close_flag
    global Incoming_flag
    global PSM_state
    global Deep_sleep_state
    global CFGDUALMODE_state
    global closed_times
    global Open_flag
    global Read_data_len
    global Read_data
    global CSCON_state  # 引用全局变量
    global cereg_4_times_server  # 引用全局变量
    global cereg_0_times_server
    global Network_result_server
    global Send_succ_times_server
    global Send_fail_times_server
    global Socket_open_times
    global Recv_succ_times
    global CLOSE_times
    global CLOSE_succ_times
    global Dur_ue_client_time
    global recv_timeout_times
    global recv_flag
    global data_fail
    global pdp_type
    global server_recv_client_delay_time
    Dur_read_time_server=0
    Recv_date_len_server=0
    Open_i_server = 0

    Read_start_time_server = datetime.datetime.now()
    
    # recv_start_time = datetime.datetime.now()
    ue_client_start_time = datetime.datetime.now()

    while 1:
        Read_end_time_server = datetime.datetime.now()
        # recv_end_time = datetime.datetime.now()
        Dur_read_time_server = Duration(Read_start_time_server, Read_end_time_server)
        # Dur_recv_time = Duration(recv_start_time, recv_end_time)
        # if Runtimes > 0:
        Dur_ue_client_time = Duration(ue_client_start_time, Read_end_time_server)
        # if Dur_recv_time > 20:
        #     if recv_flag == 1:
        #         recv_timeout_times += 1
        #         print("第" + str(recv_timeout_times) + "超时20S未收到数据")
        #         if Data_type == 0:  # text模式
        #             cmdport_server.write(("AT+QISEND=" + c_id + "," + str(Data_len) + ",\"" + Data + "\"\r\n").encode("UTF-8"))
        #             AT_log_server.write("[" + str(datetime.datetime.now()) + " Send2]" + "AT+QISEND=" + c_id + "," + str(Data_len) + ",\"" + Data + "\"\r\n")
        #             AT_log_server.flush()
        #         elif Data_type == 1:  # HEX模式
        #             cmdport_server.write(("AT+QISENDEX=" + c_id + "\"," + str(Data_len) + ",\"" + Data + "\"\r\n").encode("UTF-8"))
        #             AT_log_server.write("[" + str(datetime.datetime.now()) + " Send2]" + "AT+QISENDEX=" + c_id + "," + str(Data_len) + ",\"" + Data + "\"\r\n")
        #             AT_log_server.flush()
        #         recv_start_time = datetime.datetime.now()
        if Dur_ue_client_time > 120:
            if pdp_type == "IPV6":
                cmdport_server.write(("AT+QIOPEN=1,5,\"TCP\",\"2001:468:3000:5:2001:468:3000:5\",9024,1,1\r\n").encode("UTF-8"))
                AT_log_server.write("[" + str(datetime.datetime.now()) + " Send2]" + "AT+QIOPEN=1,5,\"TCP\",\"2001:468:3000:5:2001:468:3000:5\",9024,1,1\r\n")
            else:
                cmdport_server.write(("AT+QIOPEN=1,5,\"TCP\",\"220.180.239.212\",9024,0,0\r\n").encode("UTF-8"))
                AT_log_server.write("[" + str(datetime.datetime.now()) + " Send2]" + "AT+QIOPEN=1,5,\"TCP\",\"220.180.239.212\",9024,1,1\r\n")
            cmdport_server.write(("AT+QICLOSE=5\r\n").encode("UTF-8"))
            AT_log_server.write("[" + str(datetime.datetime.now()) + " Send-C]" + "AT+QICLOSE=5\r\n")
            AT_log_server.flush()
            ue_client_start_time = datetime.datetime.now()

        if Dur_read_time_server > timeout:   #超时未读取到URC则退出函数
            AT_log_server.write("[" + str(datetime.datetime.now()) + " Recv]Runtimes:" + str(Runtimes) + "超时" +str(timeout)+ "s未读取到正确URC\n")  # 将读取的数据写入atlog文件中
            AT_log_server.flush()  # 刷新缓冲区
            return
        else:
            # ========== 尝试回显后没有 / R / N立即打印 ==== 5.7修改
            Str_R = cmdport_server.readline()  # 每次读取1行
            String_AT_R = Str_R.decode(encoding="UTF-8", errors="strict")
            if String_AT_R:
                if Str_R == b'\r\n':
                    AT_log_server.write("\n[" + str(datetime.datetime.now()) + " Recv]" + str(String_AT_R))  # 将读取的数据写入atlog文件中
                else:
                    AT_log_server.write("[" + str(datetime.datetime.now()) + " Recv]" + str(String_AT_R))  # 将读取的数据写入atlog文件中
                AT_log_server.flush()  # 刷新缓冲区
            # ==============
            c_list = str(String_AT_R)  # 5.7修改==========================
            #==========================正则匹配区========================
            if ','.join(re.compile('\+QIOPEN: \d+,\d+').findall(c_list)):
                Open_server = ','.join(re.compile('\+QIOPEN: \d+,(\d+)').findall(c_list))
                if int(Open_server) == 0:
                    Open_flag_server = 1  # OPEN成功标志
                    Socket_open_succ_times_server += 1
                    AT_log_server.write("[" + str(datetime.datetime.now()) + " Recv]TCP Socket OPEN Success\n")
                    AT_log_server.flush()  # 刷新缓冲区
                    return 1
                else:
                    Open_flag_server = 0  # OPEN失败标志
                    return 0
            elif ','.join(re.compile('\+CEREG: \d+').findall(c_list)) == "+CEREG: 4":  # 2020.02.20 arnold
                cereg_4_times_server = cereg_4_times_server + 1  # CEREG?查询返回1或者5判断为找网成功
                Network_result_server = 0  # 将网络标志置0，可以进入重新找网
                return
            elif ','.join(re.compile('\+CEREG: \d+').findall(c_list)) == "+CEREG: 0":  # 2020.02.20 arnold
                cereg_0_times_server = cereg_0_times_server + 1  # CEREG?查询返回0为掉网
                Network_result_server = 0  # 将网络标志置0，可以进入重新找网
                return
            elif ','.join(re.compile('\+CSCON: \d+').findall(c_list)) == "+CSCON: 1":  # 2020.02.19 arnold 配置cscon检测
                CSCON_state = 1
                AT_log_server.write("[" + str(datetime.datetime.now()) + " ]UE当前处于Connect态!\n")
                AT_log_server.flush()  # 刷新缓冲区
            elif ','.join(re.compile('\+CSCON: \d+').findall(c_list)) == "+CSCON: 0":
                CSCON_state = 0
                AT_log_server.write("[" + str(datetime.datetime.now()) + " ]UE当前处于IDEL态!使用QPING 包唤醒rrc...\n")
                AT_log_server.flush()  # 刷新缓冲区
                if pdp_type == "IPV6":
                    cmdport_server.write(("AT+QPING=1,\"2001:468:3000:5:2001:468:3000:5\",4,1\r\n").encode("UTF-8"))
                else:
                    cmdport_server.write(("AT+QPING=1,\"180.101.147.115\",4,1\r\n").encode("UTF-8"))
                AT_log_server.write("[" + str(datetime.datetime.now()) + " Send2]" + "AT+QPING=1,\"180.101.147.115\",4,1\r\n")
                AT_log_server.flush()

            elif re.search("SEND OK", c_list):
                Send_succ_times_server += 1
            elif re.search("SEND FAIL", c_list):
                Send_fail_times_server += 1
            elif re.search("CLOSE OK", c_list):
                CLOSE_succ_times += 1
                AT_log_server.write("[" + str(datetime.datetime.now()) + " ]" + 'Client 断开成功 ！！！\n')  # 将读取的数据写入atlog文件中
                AT_log_server.flush()  # 刷新缓冲区
            elif re.search("\+QIURC: \"closed\",(\d+)", c_list):
                socket_id = ','.join(re.compile('\+QIURC: \"closed\",(\d+)').findall(c_list))
                cmdport_server.write(("AT+QICLOSE=" + socket_id + "\r\n").encode("UTF-8"))
                AT_log_server.write("[" + str(datetime.datetime.now()) + " Send2]" + "AT+QICLOSE=" + socket_id + "\r\n")
                AT_log_server.flush()
                CLOSE_times += 1
                Close_flag = 0
                recv_flag = 0

            elif c_list.find("incoming") != -1:
                print("SERVER被连接成功")
                Socket_open_times += 1
                Close_flag = 1
                Incoming_flag = 1
                time.sleep(0.3)

            elif re.search("\+QIURC: \"recv\",(\d+),(\d+),(\S+)", c_list):
                print("收到数据,延时" + str(server_recv_client_delay_time) + "回复client端数据")
                time.sleep(server_recv_client_delay_time)
                recv_flag = 1
                recv_start_time = datetime.datetime.now()
                Recv_succ_times += 1
                c_id = ','.join(re.compile('\+QIURC: \"recv\",(\d+),\d+,\S+').findall(c_list))
                Recv_date_len_server = ','.join(re.compile('\+QIURC: \"recv\",\d+,(\d+),\S+').findall(c_list))
                # Read_data = ','.join(re.compile('\+QIURC: \"recv\",\d+,\d+,(\S+)').findall(c_list))
                if int(Recv_date_len_server) == 100:
                    if Data_type == 0:  # text模式
                        cmdport_server.write(("AT+QISEND=" + c_id + "," + str(Data_len) + ",\"" + Data + "\"\r\n").encode("UTF-8"))
                        AT_log_server.write("[" + str(datetime.datetime.now()) + " Send2]" + "AT+QISEND=" + c_id + "," + str(Data_len) + ",\"" + Data + "\"\r\n")
                        AT_log_server.flush()
                    elif Data_type == 1:  # HEX模式
                        cmdport_server.write(("AT+QISENDEX=" + c_id + "\"," + str(Data_len) + ",\"" + Data + "\"\r\n").encode("UTF-8"))
                        AT_log_server.write("[" + str(datetime.datetime.now()) + " Send2]" + "AT+QISENDEX=" + c_id + "," + str(Data_len) + ",\"" + Data + "\"\r\n")
                        AT_log_server.flush()
                else:
                    data_fail += 1
                    print("接收数据长度与client端发送不一致")


            elif re.search("\+QNBIOTEVENT: ENTER PSM", c_list):
                PSM_state = 1  # 进入PSM成功
            elif re.search("\+QATSLEEP", c_list):
                Deep_sleep_state = 1  # 进入深睡眠成功
                return
            elif re.search("\+QATWAKEUP", c_list):
                Deep_sleep_state = 0  # 退出深睡眠成功
                return
            elif re.search("\+QNBIOTEVENT: EXIT PSM", c_list):
                PSM_state = 0  # 退出PSM成功
                return
            elif re.search('\+CPIN: READY', c_list):
                return
            elif re.search('\+CPIN: NOT READY', c_list):
                AT_log_server.write("[" + str(datetime.datetime.now()) + " Recv2]" + '模块已掉卡，请检查SIM卡是否正常插入！！！\n')  # 将读取的数据写入atlog文件中
                AT_log_server.flush()  # 刷新缓冲区
                DOS_log.write("[" + str(datetime.datetime.now()) + " Recv2]" + '模块已掉卡，请检查SIM卡是否正常插入！！！\n')  # 将读取的数据写入doslog文件中
                DOS_log.flush()  # 刷新缓冲区
                print('模块已掉卡，请检查SIM卡是否正常插入！！！\n')
                return
            elif re.search('ERROR', c_list):
                AT_log_server.write("[" + str(datetime.datetime.now()) + " Recv2]" + '读取到ERROR！！！\n')  # 将读取的数据写入atlog文件中
                AT_log_server.flush()  # 刷新缓冲区
                DOS_log.write("[" + str(datetime.datetime.now()) + " Recv2]" + '读取到ERROR！！！\n')  # 将读取的数据写入doslog文件中
                DOS_log.flush()  # 刷新缓
                # return
            elif re.search("RDY", c_list):
                Execute_command_server("AT^FORCENOWDT=1\r\n", 'OK', 5)  # 打开遇到dump死机不重启，断电无法保存
                if Runtimes == 0:
                    AT_log_server.write("[" + str(datetime.datetime.now()) + " Recv2]" + 'OPen 端口从Deep sleep唤醒！！！\n')  # 将读取的数据写入atlog文件中
                    AT_log_server.flush()  # 刷新缓冲区
                    return
                elif Runtimes > 0:
                    if Dtr_low == 1:
                        AT_log_server.write("[" + str(datetime.datetime.now()) + " Recv2]" + 'UE从Deep sleep唤醒！！！\n')  # 将读取的数据写入atlog文件中
                        AT_log_server.flush()  # 刷新缓冲区
                        Dtr_low = 0
                        return
                    else:
                        Ab_RDY_flag = 1
                        Ab_RDY_times_server = Ab_RDY_times_server + 1
                        return
            else:
                continue  # 添加执行语句，避免因读取到一个非必须的urc，导致函数退出
            time.sleep(0.1)  # 间隔0.1s读一次串口

def Preparation_server():  #初始化函数
    Execute_command_server("AT+VERCTRL=,1\r\n", 'OK', 3)
    # Execute_command_server("AT+QCGDEFCONT=\"IP\"\r\n", 'OK', 3)
    if ue_type == "BC32-NB":
        Execute_command_server("AT+QCSEARFCN=0\r\n", 'OK', 3)  # 清除NB先验频点  2020.02.27 arnold
        Execute_command_server("AT+QNWCFG=0,0\r\n", 'OK', 3)   #配置NB优先   2020.02.27 arnold
    elif ue_type == "BC32-GSM":
        Execute_command_server("AT+QCSEARFCN=1\r\n", 'OK', 3)  # 清除GSM先验频点  2020.02.27 arnold
        Execute_command_server("AT+QNWCFG=0,1\r\n", 'OK', 3)  # 配置GSM优先   2020.02.27 arnold
    time.sleep(2)
    if pdp_type == "IP":   #2020.02.27 arnold
        if ue_type == "BC32-GSM":
            Execute_command_server("AT+CGDCONT=1,\"IP\",\"" + GSM_APN + "\"\r\n", 'OK', 20)
        else:
            Execute_command_server("AT+QCGDEFCONT=\"IP\",\"" + GSM_APN + "\"\r\n", 'OK', 5)
    elif pdp_type == "IPV6":
        if ue_type == "BC32-GSM":
            Execute_command_server("AT+CGDCONT=1,\"IPV6\",\"" + GSM_APN + "\"\r\n", 'OK', 20)
        else:
            Execute_command_server("AT+QCGDEFCONT=\"IPV6\",\"" + GSM_APN + "\"\r\n", 'OK', 5)
    elif pdp_type == "IPV4V6":
        if ue_type == "BC32-GSM":
            Execute_command_server("AT+CGDCONT=1,\"IPV4V6\",\"" + GSM_APN + "\"\r\n", 'OK', 20)
        else:
            Execute_command_server("AT+QCGDEFCONT=\"IPV4V6\",\"" + GSM_APN + "\"\r\n", 'OK', 5)

    Execute_command_server("AT+QRST=1\r\n", 'RDY', 5)  # 实网下qrst重启要注销
    UART_read_server(5)
    Execute_command_server("AT^FORCENOWDT=1\r\n", 'OK', 5)  # 打开遇到dump死机不重启，断电无法保存
    Execute_command_server("AT^TRACECTRL=1\r\n", 'OK', 5)  # 打开强制吐log机制，会存入NV，断电不会丢失
    Execute_command_server("ATI\r\n", 'OK', 3)  # 查看版本信息
    Execute_command_server("AT+CSUB\r\n", 'OK', 3)
    Execute_command_server("AT+CGMR\r\n", 'OK', 3)
    Execute_command_server("AT+CGSN=1\r\n", 'OK', 3)
    Execute_command_server("AT+CIMI\r\n", 'OK', 5)
    Execute_command_server("AT+CEREG=1\r\n", 'OK', 3)  #设置CEREG自动上报
    Execute_command_server("AT+CSCON=1\r\n", 'OK', 3)
    # if UE_states == 0 or UE_states == 1:  #Connect  IDEL 态测试，关闭PSM，关闭模块睡眠
    #     Execute_command_server("AT+CPSMS=0\r\n", 'OK', 3)
    #     Execute_command_server("AT+QSCLK=2\r\n", 'OK', 3)   #无法保存，需在出现异常重启后再次设置
    # else:   #PSM 态测试，打开PSM，打开深睡眠
    #     Execute_command_server("AT+CPSMS=1,,,\"00100001\",\"00100010\"\r\n", 'OK', 3)
    #     Execute_command_server("AT+QSCLK=1\r\n", 'OK', 3)  # 无法保存，出现重启会默认恢复 1
    Execute_command_server("AT+CPSMS=0\r\n", 'OK', 3)
    Execute_command_server("AT+QSCLK=2\r\n", 'OK', 3)   #无法保存，需在出现异常重启后再次设置AT+CEDRXS=1,5,"0101"
    Execute_command_server("AT+CEDRXS=0\r\n", 'OK', 3)
    Execute_command_server("AT+QICFG=\"viewmode\",1\r\n", 'OK', 3)  # 配置接收数据不换行
    Execute_command_server("AT+QICFG=\"showlength\",1\r\n", 'OK', 3)  # 配置接收数据显示长度
    if Access_mode == 1:
        Execute_command_server("AT+QISWTMD=0,1\r\n", 'OK', 3)  # 配置为push模式
        Execute_command_server("AT+QISWTMD=1,1\r\n", 'OK', 3)  # 配置为push模式
        Execute_command_server("AT+QISWTMD=2,1\r\n", 'OK', 3)  # 配置为push模式
    elif Access_mode == 0:
        Execute_command_server("AT+QISWTMD=1,0\r\n", 'OK', 3)  # 配置为buffer模式
        Execute_command_server("AT+QISWTMD=2,0\r\n", 'OK', 3)  # 配置为buffer模式
    if Data_type == 0:
        Execute_command_server("AT+QICFG=\"dataformat\",0,0\r\n", 'OK', 3)  # 配置发送接收为text格式
    elif Data_type == 1:
        Execute_command_server("AT+QICFG=\"dataformat\",1,1\r\n", 'OK', 3)  # 配置发送接收为HEX格式
    Execute_command_server("AT&W\r\n", 'OK', 3)

def Network_check_server(timeout): #网络检查
    global Network_result_server     #返回网络状态结果
    global Network_fail_times_server  #统计找网失败次数
    global Network_succ_times_server  #统计找网成功次数
    global Network_time_server       #统计找网时间
    global Sum_network_time_server   #统计找网总时间
    global Runtimes
    global SC_earfcn
    global SC_PCI
    global SC_rsrp
    global SC_rsrq
    global SC_rssi
    global SC_snr
    global SC_ecl
    global Old_PCI
    global Network_start_time_server
    global PCI_change_times_server
    global Restart_to_network_time_server
    global Cereg_sucess_server  # 引用全局变量  =====5.7修改
    global Restart_end_time_server
    Cereg_sucess_server = 0  # 检查网络状态之前给一个初始值=====5.7修改
    Timeout_i = 0
    Network_start_time_server=datetime.datetime.now()
    if ue_type == "BC32-GSM":
        Execute_command_server("AT+CGACT=1,1\r\n", 'OK', 92)  #激活GSM PDP  2020.02.27 arnold
    while Timeout_i < timeout:
        Execute_command_server("AT+CEREG?\r\n", 'OK', 5)
        Execute_command_server("AT+CGPADDR\r\n", 'OK', 5)
        Execute_command_server("AT+CSQ\r\n", 'OK', 5)
        Execute_command_server("AT+CREG?\r\n", 'OK', 5)
        Execute_command_server("AT+CGREG?\r\n", 'OK', 5)
        Execute_command_server("AT+CPIN?\r\n", 'OK', 5)
        Execute_command_server("AT+COPS?\r\n", 'OK', 5)
        # if ue_type == "BC32":
            # Execute_command_server("AT+CFGDUALMODE?\r\n", 'OK', 5)
            # Execute_command_server("AT+CFGRATPRIO?\r\n", 'OK', 5)  # 跑BC25的时候请注释这两个模式查询指令
        Execute_command_server("AT+TUESTATS=\"ALL\"\r\n", 'OK', 20)
        if Cereg_sucess_server == 1:   #
            Network_succ_times_server = Network_succ_times_server+1
            Network_OK_time_server = datetime.datetime.now()
            Network_time_server = Duration(Network_start_time_server, Network_OK_time_server)  # 计算找网成功时间
            Sum_network_time_server = Sum_network_time_server + Network_time_server
            Network_result_server = 1  # 网络状态结果
            AT_log_server.write("[" + str(datetime.datetime.now()) +" ]Success  to find the network!\n")
            AT_log_server.flush()  # 刷新缓冲区
            Execute_command_server("AT+QENG=0\r\n", 'OK', 5)
            if Runtimes == 1:
                Old_PCI = SC_PCI
            elif Runtimes > 1:
                if Old_PCI == SC_PCI:
                    AT_log_server.write("[" + str(datetime.datetime.now()) + " ]小区PCI未发生变化!\n")
                    AT_log_server.flush()  # 刷新缓冲区
                else:
                    PCI_change_times_server = PCI_change_times_server+1
                    Old_PCI = SC_PCI
                    AT_log_server.write("[" + str(datetime.datetime.now()) + " ]小区PCI发生变化!\n")
                    AT_log_server.flush()  # 刷新缓冲区
            Net_log.write(str(datetime.datetime.now()) + "\t" + str(Runtimes) + "\t" + str(SC_earfcn) + "\t" + str(SC_PCI) + "\t" + str(SC_rsrp) + "\t" + str(SC_rsrq) + "\t" + str(SC_rssi) + "\t" + str(SC_snr) + "\t" + str(SC_ecl) + "\t" + str(PCI_change_times) + "\n")
            Net_log.flush()  # 刷新缓冲区
            break #成功找到网络后跳出循环
        elif Cereg_sucess_server == 0:
            sleep(1)              #未找到网络则等待1s后再进入下个循环查询
            Network_Fail_time = datetime.datetime.now()
            Timeout_i = Duration(Network_start_time_server, Network_Fail_time)  # 尝试次数自增
    if int(Timeout_i) >= timeout:
        AT_log_server.write("[" + str(datetime.datetime.now()) + " ]Fail  to find the network!（timeout:"+str(timeout)+"s)\n")
        AT_log_server.flush()  # 刷新缓冲区
        DOS_log.write("[" + str(datetime.datetime.now()) + " ]Fail  to find the network!（timeout:" + str(timeout) + "s)\n")
        DOS_log.flush()  # 刷新缓冲区
        Network_fail_times_server = Network_fail_times_server+1
        Network_time_server = "Find Network Failed"
        Restart_to_network_time_server = "Find Network Failed"
        Network_result_server = 0  # 网络状态结果
    return  Network_result_server


def Socket_create_server(Server_ip,Server_port):  #建立socket
    global Open_flag_server
    global Open_flag
    #global Cgpaddr_new
    global Socket_open_fail_times_server
    # Execute_command_server("AT+QICFG=\"URCMODE\",1\r\n", 'OK', 3)
    print("进入建立连接")
    if Open_flag_server == 0:
        if pdp_type == "IPV6":
            cmdport_server.write(("AT+QIOPEN=1,0,\"TCP LISTENER\",\"" + Server_ip + "\",1," + Server_port + ",1,1\r\n").encode("UTF-8"))  # 创建是用默认，在此处添加切换模块接收模式和数据格式
            AT_log_server.write("[" + str(datetime.datetime.now()) + " Send2]" + "AT+QIOPEN=1,0,\"TCP LISTENER\",\"" + Server_ip + "\",1," + Server_port + ",1,1\r\n")  #2020.02.27 arnold
            AT_log_server.flush()
        else:
            cmdport_server.write(("AT+QIOPEN=1,0,\"TCP LISTENER\",\"" + Server_ip + "\",1," + Server_port + "\r\n").encode("UTF-8"))  # 创建是用默认，在此处添加切换模块接收模式和数据格式
            AT_log_server.write("[" + str(datetime.datetime.now()) + " Send2]" + "AT+QIOPEN=1,0,\"TCP LISTENER\",\"" + Server_ip + "\",1," + Server_port + "\r\n")  # 2020.02.27 arnold
            AT_log_server.flush()
        UART_read_server(5)  # 读取OPEN状态URC
        if Open_flag_server == 1:
            Open_flag = 1
            print("server端建立成功！")
    else:
        Socket_open_fail_times_server += 1
        return

def UE_client_C(event): # 2020.02.28 arnold
    while True:
        try:
            event.wait()  #event事件为True时执行
            time.sleep(2)
            Execute_command_server("AT+QIOPEN=2,1,\"TCP\",\"220.18.39.22\",8062,0,0\r\n", 'QIOPEN', 36.1)
            cmdport_server.write(("AT+QICLOSE=2\r\n").encode("UTF-8"))
            AT_log_server.write("[" + str(datetime.datetime.now()) + " Send-C]" + "AT+QICLOSE=2\r\n")
            AT_log_server.flush()
            cmdport_server.write(("AT+QICLOSE=3\r\n").encode("UTF-8"))
            AT_log_server.write("[" + str(datetime.datetime.now()) + " Send-C]" + "AT+QICLOSE=3\r\n")
            AT_log_server.flush()
            cmdport_server.write(("AT+QICLOSE=4\r\n").encode("UTF-8"))
            AT_log_server.write("[" + str(datetime.datetime.now()) + " Send-C]" + "AT+QICLOSE=4\r\n")
            AT_log_server.flush()
            cmdport_server.write(("AT+QICLOSE=5\r\n").encode("UTF-8"))
            AT_log_server.write("[" + str(datetime.datetime.now()) + " Send-C]" + "AT+QICLOSE=5\r\n")
            AT_log_server.flush()
        except Exception as e:
            print("异常信息-辅线程:", e)
            DOS_log.write("[" + str(datetime.datetime.now()) + " ]Runtimes: " + str(Runtimes) + " 异常信息辅线程:" + str(e) + "\n")
            DOS_log.flush()  # 刷新缓冲区
            event.clear()
            event.set()
            time.sleep(2)  # 主线程必须有等待时间，等待辅线程唤醒
            continue

def Ram_check_server():  # 检查内存是否泄漏，内存超过20%报警并统计报警次数，内存超过50%报内存泄漏错误、脚本进入等待状态
    global CSW_Total_Free_First_8
    global CSW_Total_Free_First_5
    global COS_Total_Free_First_8
    global COS_Total_Free_First_5
    global Ram_leak_count  # 记录内存泄漏次数
    global CSW_ram
    global COS_ram
    Execute_command_server("AT+GCHS\r\n", 'OK', 3)
    if (Runtimes == 1):
        CSW_Total_Free_First_5 = int(CSW_ram) * 0.5
        CSW_Total_Free_First_8 = int(CSW_ram) * 0.8
        COS_Total_Free_First_5 = int(COS_ram) * 0.5
        COS_Total_Free_First_8 = int(COS_ram) * 0.8
    else:  # 内存在 20%-50%时候报警
        if (CSW_Total_Free_First_5 < int(CSW_ram) < CSW_Total_Free_First_8 or COS_Total_Free_First_5 < int(COS_ram) < COS_Total_Free_First_8):
            Alarm()  # 调用报警函数
            Ram_leak_count += 1
        elif (int(CSW_ram) < CSW_Total_Free_First_5 or int(COS_ram) < COS_Total_Free_First_5):
            print('出现内存泄漏！！！请保留现场！！！\n')
            flag = True
            while (flag):
                time.sleep(1)  # 让脚本进入等待
        else:
            pass
    return

def Alarm():  # 报警,每次报警循环三次，每次循环蜂鸣声持续十秒，每次间隔三秒开始下一循环
    Alarm_times = 0
    while Alarm_times < 3:  # 每次报警持续时间
        alarm_last = 10
        start_time = time.time()  # 报警开始时间
        end_time = time.time()  # 报警结束时间
        while end_time - start_time <= alarm_last:
            winsound.Beep(6000, 1000)
            end_time = time.time()
        time.sleep(3)  # 每次报警时间间隔3秒
        Alarm_times += 1
    return

#=========================================================================

Script_start_time = datetime.datetime.now()
signal.signal(signal.SIGINT, sigint_handler) #调用封装的sigint_handler检测CTRL+C信号
signal.signal(signal.SIGTERM, sigint_handler) #调用封装的sigint_handler检测CTRL+C信号
# #=========设置一个辅线程和event时间===================
# event = threading.Event()   #设置一个全局的EVENT事件，Event默认内置了一个标志，初始值为False
# t = threading.Thread(target=UE_client_C, args=(event,))   #设置一个辅线程
# t.start()  #辅线程开始运行
# #======================================================
print("初始化...")
Runtimes=0
Local_time = datetime.datetime.now()
AT_log_server = open("TCP SERVER_LC_三态_Server_ATlog.txt","w+")         #以读写方式打开ATlog文件
Net_log = open("TCP SERVER_LC_三态_Server_Netlog.txt", "w+")  # 以读写方式打开Netlog文件
DOS_log = open("TCP SERVER_LC_三态_Server_DOSlog.txt", "w+")  # 以读写方式打开DOSlog文件
Result_log_server = open("TCP SERVER_LC_三态_Server_Resultlog.txt", "w+")  # 以读写方式打开Resultlog文件
Net_log.write("LocalTime\tRuntimes\tSC_earfcn\tSC_PCI\tSC_rsrp\tSC_rsrq\tSC_rssi\tSC_snr\tSC_ecl\t小区PCI变化次数\n")
Net_log.flush()  # 刷新缓冲区
Result_log_server.write("LocalTime\tRuntimes\t找网成功次数\tSERVER建立成功次数\tSERCER建立失败次数"
                        "\tSERCER被连接次数\tSERVER接收到的次数\tSERVER发送成功次数\tSERVER发送失败次数"
                        "\tCLOSE次数\t执行close成功次数"
                        "\tSERVER异常次数\t模块端异常重启次数\tCEREG4掉网次数\tCEREG0掉网次数\t超时20s未接收到数据\t接收数据与client发送长度不一致次数\n")
Result_log_server.flush()  # 刷新缓冲区

cmdport_server = serial.Serial(Uart_port_server,Baud_rate,timeout=0.1)    #打开串口
UART_read_server(5)
Preparation_server()
DOS_log.write("IMEI:"+str(UE_IMEI)+"\n")
DOS_log.flush()  # 刷新缓冲区
DOS_log.write("IMSI:"+str(SIM_IMSI)+"\n")
DOS_log.flush()  # 刷新缓冲区

i = 0
while True:
    try:

        Runtimes=Runtimes+1
        #Ram_check_server()
        if Runtimes % 2000 == 1 and Runtimes > 1:
            i = i+1
            AT_log_server.close()
            AT_log_server = open("TCP_SC_三态_Client_ATlog_" + str(i) + ".txt", "w+")

        # print("Runtimes:" + str(Runtimes))
        # AT_log_server.write("===================================Runtimes:" + str(Runtimes) + "===================================\n")
        # AT_log_server.flush()  # 刷新缓冲区
        if Runtimes == 1 or Ab_RDY_flag == 1 or Network_result_server == 0:
            Ab_RDY_flag = 0
            # #===================遇到异常则关闭辅线程==============
            # event.clear()
            # event_state = event.isSet()
            # AT_log_server.write("因网络异常辅线程停止，待异常恢复后重新执行,当前EVENT值为： " + str(event_state) + "\r\n")
            # AT_log_server.flush()
            # #===========================================
            Network_result_server = Network_check_server(Network_out_time)  # 检查网络状态
            Execute_command_server("AT+FAKEBSR=" + fake_value + ",1000\r\n", 'OK', 3)
            print("SERVER端口IP为：" + TCP_server_ip)
            print("SERVER端口号为：" + TCP_server_port)
            if Network_result_server == 1:
                if Open_flag_server == 0:
                    Socket_create_server(TCP_server_ip, TCP_server_port)
                    # #============启动辅线程==============
                    # event.set()
                    # time.sleep(2)  # 主线程必须有等待时间，等待辅线程唤醒
                    # event_state = event.isSet()
                    # AT_log_server.write("辅线程启动,EVENT值为： " + str(event_state) + "\r\n")
                    # AT_log_server.flush()
                    # #====================================
                if Open_flag_server == 1:
                    print("进入监听模式")
                    AT_log_server.write("[" + str(datetime.datetime.now()) + "]" + '进入监听！！！\n')  # 将读取的数据写入atlog文件中
                    AT_log_server.flush()  # 刷新缓冲区
                    UART_read_server(100000)

                else:
                    print("建立失败")
        else:
            UART_read_server(100000)

        Result_log_server.write(str(datetime.datetime.now()) + "\t" + str(Runtimes) + "\t" + str(Network_succ_times_server)
                                + "\t" + str(Socket_open_succ_times_server) + "\t" + str(Socket_open_fail_times_server)
                                + "\t" + str(Socket_open_times)+ "\t" + str(Recv_succ_times) + "\t" + str(Send_succ_times_server) + "\t" + str(Send_fail_times_server)
                                + "\t" + str(CLOSE_times) + "\t" + str(CLOSE_succ_times) + "\t" + str(Server_abnormal_times) + "\t" + str(Ab_RDY_times_server)
                                + "\t" + str(cereg_4_times_server) + "\t" + str(cereg_0_times_server) + "\t" + str(recv_timeout_times) + "\t" + str(data_fail) + "\n")
        Result_log_server.flush()  # 刷新缓冲区
        Script_end_time = datetime.datetime.now()
    except Exception as e:
        print("server异常", e)
        continue



