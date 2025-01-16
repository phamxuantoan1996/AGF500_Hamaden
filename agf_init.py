from modbus_client import Modbus_Serial_Client
from agf_task_chain import AGF_Task_Chain
from agf_work_status import AGF_Work_Status
from control import ESA_API
from logfile import LogFile
# from logdatabase import LogDataBase

import json
import time


with open("agf_config_param.json", "r") as agf_config_param:
    config_param = json.load(agf_config_param)
AGF_Param_Config = {
    'ip_src':config_param['ip_src'],
    'host_api':config_param['host_api'],
    'port_api':config_param['port_api'],
    'modbus_port':config_param['modbus_port'],
    'modbus_baudrate':config_param['modbus_baudrate'],
    'modbus_slave_id':config_param['modbus_slave_id'],
    'pos_idle':config_param['pos_idle'],
    'agf_id':config_param['agf_id']
}


task_chain = AGF_Task_Chain()
work_status = AGF_Work_Status(agf_id=AGF_Param_Config['agf_id'])
Robot = ESA_API(host=AGF_Param_Config['ip_src'])
mb_client = Modbus_Serial_Client(slave_id=AGF_Param_Config['modbus_slave_id'],number_of_input=50,number_of_hold=50,input_regs_addr=1000,hold_regs_addr=2000,time_poll=0.05,port=AGF_Param_Config['modbus_port'],baudrate=AGF_Param_Config['modbus_baudrate'],timeout_modbus=5)


def agf_init_func() -> bool:
    logfile = LogFile("./LogfileAGF")
    #Modbus
    check_init = True
    logfile.init_logfile()
    if mb_client.connect_to_server():
        logfile.writeLog(type_log="info",msg="Modbus Init ok")
    else:
        logfile.writeLog(type_log="error",msg="Modbus Init error")
        check_init = False
    #MongoDB
    # if database.MongoDB_check():
    #     logfile.writeLog(type_log="info",msg="Database Init ok")
    # else:
    #     logfile.writeLog(type_log="error",msg="Database Init error")
    #     check_init = False
    #SRC
    logfile.writeLog(type_log='info',msg='connecting to src')
    if Robot.connect_status():
        logfile.writeLog(type_log="info",msg="src status connected")
    else:
        check_init = False
        logfile.writeLog(type_log="error",msg="src status connect error")
    if Robot.connect_navigation():
        logfile.writeLog(type_log="info",msg="src naviagtion connected")
    else:
        check_init = False
        logfile.writeLog(type_log="error",msg="src navigation connect error")
    if Robot.connect_other():
        logfile.writeLog(type_log="info",msg="src other connected")
    else:
        check_init = False
        logfile.writeLog(type_log="error",msg="src other connect error")
    if Robot.connect_control():
        logfile.writeLog(type_log="info",msg="src control connected")
    else:
        check_init = False
        logfile.writeLog(type_log="error",msg="src control connect error")
    if Robot.connect_config():
        logfile.writeLog(type_log="info",msg="src config connected")
    else:
        check_init = False
        logfile.writeLog(type_log="error",msg="src config connect error")
    time.sleep(2)
    logfile.writeLog(type_log='info',msg='src relocating')
    while True:
        try:
            Robot.status(Robot.keys)
            print(Robot.data_Status['reloc_status'])
            if Robot.data_Status['reloc_status'] == 0:#failed
                print('a')
                time.sleep(1)
            elif Robot.data_Status['reloc_status'] == 1:#successed
                print('b')
                break
            elif Robot.data_Status['reloc_status'] == 2:#relocating
                print('c')
                time.sleep(1)
            elif Robot.data_Status['reloc_status'] == 3:#complete
                print('d')
                Robot.confim_location()
                time.sleep(2)
        except Exception as e:
            logfile.writeLog(type_log='error',msg='relocation error')

    return check_init