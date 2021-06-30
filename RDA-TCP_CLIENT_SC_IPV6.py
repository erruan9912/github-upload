#!/usr/bin/python
# -*- coding: utf-8 -*-
import time                    #加载时间函数
import datetime                #加载获取时间函数
import signal
import socket
import os,sys
import select
#A区域
#脚本编写日期及编写人员--------------------------------------------------------------------
#V1.0--Fester--20201230
#脚本逻辑
# 1.模拟TCP client连接SERVER端
# 2.连接成功后，发送数据，等待SERVER端回复消息
# 3.连续发送三次后，close连接，结束Runtimes
# 4.循环1-2

#B区域
#=========================================================================

#注意事项：
#与SERVER端脚本一同使用
#注意查看打印消息
# 先运行server端脚本，获取IP和端口
#=========================================================================

#用户可以配置变量
#=========================================================================
#TCP_server_ip = "220.180.239.212"    测试端口
# 10.66.103.58

TCP_server_port = 2020

client_ID = "A2"
data = "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
# data1 = "A2012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"                        #发送数据
# data2 = "B2012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"                        #发送数据
# data3 = "C2012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"                        #发送数据
#C区域
#=========================================================================
#脚本统计参数
sock_ok_times = 0    # 建立sock成功次数
sock_fail_times = 0
send_times = 0    # 发送次数
recv_fail_times = 0
recv_succ_times = 0    # 发送成功次数
recv_timeout = 0    # 接收超时次数
Disconnect_times = 0
close_abnormal_times = 0
Success_open = "0%"
Success_recv = "0%"
#=========================================================================
print("输入SERVER端IP")
TCP_server_ip = input("IP: ")
print(TCP_server_ip)

print("输入总运行次数,若为0则表示无限循环，若不为0则为设置的循环次数")
run_time_count = int(input("总次数： "))
#run_time_count = 0   #运行次数，若为0则表示无限循环，若不为0则为设置的循环次数
print("输入每次连接数据收发次数")
onetime_send_count = int(input("收发次数： "))
#onetime_send_count = 3  #每次连接数据收发次数
print("输入等待server回复的超时时间")
timeout_in_seconds = int(input("超时时间： "))
#timeout_in_seconds = 60   #client 等待SERVER回复数据的超时时间
def sigint_handler(signum, frame): #捕获ctrl+c信号
    num = int(input("1,carry on;0,our\n"))
    if num:
        print("yuor choice:", num, "carry on")
    else:
        print("yuor choice:", num, "out")
        Result_log.write("RUN_time: " + str(Script_start_time) + "---" + str(Script_end_time) + "\n")
        Result_log.write("Runtimes: " + str(Runtimes) + "\n")

        Result_log.write("OPEN succ times: " + str(sock_ok_times) + "\n")
        Result_log.write("OPEN fail times: " + str(sock_fail_times) + "\n")
        Result_log.write("OPEN Probability " + Success_open + "\n")
        Result_log.write("SEND TIMES: " + str(send_times) + "\n")
        Result_log.write("RECV SUCC TIMES: " + str(recv_succ_times) + "\n")
        Result_log.write("RECV FAIL TIMES " + str(recv_fail_times) + "\n")
        Result_log.write("RECV OUT TIMES " + str(recv_timeout) + "\n")
        Result_log.write("RECV Probability " + Success_recv + "\n")
        Result_log.write("CLOSE abnormal" + str(close_abnormal_times) + "\n")
        AT_log.close()
        Result_log.close()
        sys.exit()

#=========================================================================
Script_start_time = datetime.datetime.now()
signal.signal(signal.SIGINT, sigint_handler) #调用封装的sigint_handler检测CTRL+C信号
signal.signal(signal.SIGTERM, sigint_handler) #调用封装的sigint_handler检测CTRL+C信号

Runtimes = 0
print("Please confirm whether the SERVER side has been opened")
time.sleep(5)
AT_log = open("TCP_Client_SC_ATlog.txt","w+")
Result_log = open("TCP_Client_SC_Resultlog.txt", "w+")  # 以读写方式打开Resultlog文件
Result_log.write("LocalTime\tRuntimes"
                 "\topen succ timge\topen fail times\tOPEN Probability\tsend times\trecv succ times\trecv fail times\trecv out tines\tRECV Probability\tCLOSE abnormal\n")
Result_log.flush()  # 刷新缓冲区
i = 0

run_count = 0
while run_time_count == 0 or run_count < run_time_count:
    run_count += 1
    try:
        Runtimes = Runtimes + 1
        if Runtimes%2000 == 1 and Runtimes > 1:
            i = i+1
            AT_log.close()
            AT_log = open("TCP_SC_三态_Client_ATlog_" + str(i) + ".txt", "w+")
        print("Runtimes:" + str(Runtimes))
        AT_log.write("===================================Runtimes:" + str(Runtimes) + "===================================\n")
        AT_log.flush()  # 刷新缓冲区

        client = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        try:
            # ===========================================================
            client.connect((TCP_server_ip, TCP_server_port))
            AT_log.write("[" + str(datetime.datetime.now()) + " Recv]Runtimes:" + str(Runtimes) + " TCP OPEN\n")
            AT_log.flush()  # 刷新缓冲区
        except Exception as e:
            print("TCP OPEN FAIL", e)
            AT_log.write("[" + str(datetime.datetime.now()) + " Recv]Runtimes:" + str(Runtimes) + " TCP OPEN FAIL\n")
            AT_log.flush()  # 刷新缓冲区
            sock_fail_times += 1
            time.sleep(10)
            client.close()
            continue
        else:
            AT_log.write("[" + str(datetime.datetime.now()) + " Recv]Runtimes:" + str(Runtimes) + " TCP OPEN SUCC\n")
            AT_log.flush()  # 刷新缓冲区
            sock_ok_times += 1
            time.sleep(1)

            send_i = 0
            while send_i < onetime_send_count:
                send_i += 1

                Runtimes_data = str(Runtimes)  # 讲Runtimes作为字符串赋值
                send_i_data = str(send_i)
                data_A = data[13:]
                data_B = "00000000"
                data_C = "000"
                Runtimes_data_len = len(Runtimes_data)
                send_i_len = len(send_i_data)
                New_data = client_ID + data_B[Runtimes_data_len:] + Runtimes_data + data_C[send_i_len:] + send_i_data + data_A

                client.send(New_data.encode("utf-8"))
                print("Sendtimes:" + str(send_i))
                AT_log.write("[" + str(datetime.datetime.now()) + " Send] Client NO" + str(send_i) + "  send  " + New_data + "\r\n")
                AT_log.flush()  # 刷新缓冲区
                #=======2020.02.19-arnold-添加等待server回复超时时间========
                client.setblocking(0)
                ready = select.select([client], [], [], timeout_in_seconds)
                if ready[0]:
                    try:
                        info = client.recv(1024)
                        send_times += 1
                    except Exception as e:
                        print("Disconnect!!!", e)
                        Disconnect_times += 1
                        break

                    # ===========================================================  # 10.66.103.58
                    else:
                        recv_info = info.decode(encoding="UTF-8", errors="strict")
                        if len(recv_info) != 0:
                            AT_log.write("[" + str(datetime.datetime.now()) + " Recv] Client NO" + str(send_i) + "  recv  " + recv_info + "\r\n")
                            AT_log.flush()  # 刷新缓冲区
                            if int(len(recv_info)) == 280:
                                recv_succ_times += 1
                                AT_log.write("[" + str(datetime.datetime.now()) + " Recv] Client wait recv success\r\n")
                                AT_log.flush()  # 刷新缓冲区
                            else:
                                recv_fail_times += 1
                                AT_log.write("[" + str(datetime.datetime.now()) + " Recv] Client wait recv fail\r\n")
                                AT_log.flush()  # 刷新缓冲区
                            time.sleep(1)
                        else:
                            print("Disconnect!!!")
                            Disconnect_times += 1   # 未接受到数据 代表接受超时
                            break
                else:
                    print("数据接收超时")
                    recv_timeout += 1
                    AT_log.write("[" + str(datetime.datetime.now()) + " Recv] Client wait recv timeout\r\n")
                    AT_log.flush()  # 刷新缓冲区10.1

            client.close()
            AT_log.write("[" + str(datetime.datetime.now()) + " Recv]Runtimes:" + str(Runtimes) + " TCP CLOSE\n")
            AT_log.flush()  # 刷新缓冲区
            if send_i < int(onetime_send_count):
                close_abnormal_times += 1
                AT_log.write("[" + str(datetime.datetime.now()) + " Recv]Runtimes:" + str(Runtimes) + " TCP CLOSE_异常\n")
                AT_log.flush()  # 刷新缓冲区
            else:
                pass
            time.sleep(10)

            # ========================计算成功率=========================
            Success_open = str(
                float(('%.3f' % (sock_ok_times / Runtimes))) * 100) + "%"
            Success_recv = str(
                float(('%.3f' % (recv_succ_times / send_times))) * 100) + "%"
            # ============================================================
            Result_log.write(str(datetime.datetime.now()) + "\t" + str(Runtimes) + "\t" + str(sock_ok_times)
                             + "\t" + str(sock_fail_times) + "\t" + Success_open + "\t" + str(send_times) + "\t" + str(
                recv_succ_times) + "\t" + str(recv_fail_times) + "\t" + str(recv_timeout) + "\t" + Success_recv + "\t" + str(close_abnormal_times) + "\n")
            Result_log.flush()  # 刷新缓冲区
            Script_end_time = datetime.datetime.now()
    except Exception as e:
        print("client异常", e)
        continue
    if run_time_count != 0 and run_count == run_time_count:
        Result_log.write("RUN_time: " + str(Script_start_time) + "---" + str(Script_end_time) + "\n")
        Result_log.write("Runtimes: " + str(Runtimes) + "\n")

        Result_log.write("OPEN succ times: " + str(sock_ok_times) + "\n")
        Result_log.write("OPEN fail times: " + str(sock_fail_times) + "\n")
        Result_log.write("OPEN Probability " + Success_open + "\n")
        Result_log.write("SEND TIMES: " + str(send_times) + "\n")
        Result_log.write("RECV SUCC TIMES: " + str(recv_succ_times) + "\n")
        Result_log.write("RECV FAIL TIMES " + str(recv_fail_times) + "\n")
        Result_log.write("RECV OUT TIMES " + str(recv_timeout) + "\n")
        Result_log.write("RECV Probability " + Success_recv + "\n")
        Result_log.write("CLOSE abnormal" + str(close_abnormal_times) + "\n")
        AT_log.close()
        Result_log.close()
        sys.exit()
