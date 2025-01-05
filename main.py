from threading import Thread
from agf_init import agf_init_func,mb_client,Robot,work_status,AGF_Param_Config,task_chain
import time
from agf_work_status import Mission_Status,AGF_Status
from agf_task_chain import AGF_Task_Status
from route import app

def lift_set_mode(mode:str):
    '''
    mode : "manual" or "auto"
    '''
    if mode == "manual":
        mb_client.hold_regs[10] = 0
    elif mode == "auto":
        mb_client.hold_regs[10] = 1
    
def lift_set_mission(mission:str):
    '''
    mission: "pick","put" or "none"
    '''
    if mission == "pick":
        mb_client.hold_regs[0] = 1
    elif mission == "put":
        mb_client.hold_regs[0] = 2
    elif mission == 'none':
        mb_client.hold_regs[0] = 0
        mb_client.hold_regs[11] = 0
        mb_client.hold_regs[12] = 0

def lift_set_led(color:int):
    '''
    set led color
    '''
    mb_client.hold_regs[1] = color
    return True


def task_src_poll_status_func():
    while True:
        try:
            Robot.status(Robot.keys)
            sound = Robot.robot_sound_status()
            if 'sound_name' in sound.keys():
                work_status.agf_sound_audio = sound['sound_name']
            
        except Exception as e:
            print(e)
        time.sleep(0.2)

def task_agf_poll_status_func():
    while True:
        try:
            work_status.slider_dir = mb_client.input_regs[10]
            work_status.slider_speed = mb_client.input_regs[11]
            work_status.lift_dir = mb_client.input_regs[12]
            work_status.lift_pos = mb_client.input_regs[13]
            work_status.task_list = task_chain.task_list
            work_status.task_current = task_chain.task_current
            list_error = []
            # notices = "AGF đang hoạt động."
            if Robot.data_Status["emergency"]:
                list_error.append("emergency")
                # notices = "AGF dừng khẩn cấp."
            if Robot.data_Status["blocked"]:
                list_error.append("blocked")
                # notices = "AGF gặp chướng ngại vật."
            if mb_client.modbus_error:
                list_error.append("modbus")
                # notices = "AGF lỗi truyền thông modbus."
            work_status.agf_error = list_error
            if work_status.task_current != {}:
                if work_status.task_current['task_name'] == 'pick':
                    Robot.play_audio({"name":"picking_pallet","loop":False})
                elif work_status.task_current['task_name'] == 'put':
                    Robot.play_audio({"name":"puting_pallet","loop":False})
            if Robot.data_Status['emergency']:
                lift_set_led(9) #Blink red
                Robot.play_audio({"name":"error","loop":False})
            elif Robot.data_Status['blocked'] or mb_client.modbus_error:
                lift_set_led(8) #Red
            elif (Robot.data_Status['task_status'] == 0 or Robot.data_Status['task_status'] == 1 or Robot.data_Status['task_status'] == 4 or Robot.data_Status['task_status'] == 6) and work_status.task_list == []:
                lift_set_led(10) #Yellow
            elif work_status.agf_sound_audio == 'turnleft.wav' or work_status.agf_sound_audio == 'turnright.wav':
                lift_set_led(11)
            else:
                if work_status.task_current != {}:
                    if (work_status.task_current['task_name'] == 'pick' or work_status.task_current['task_name'] == 'put') and (mb_client.input_regs[7] != 0) and (mb_client.hold_regs[0] != 0):
                        lift_set_led(8)
                        # notices = "Có vật cản trong vùng AGF lấy/trả pallet."
                    else:
                        lift_set_led(2)
                else:
                    lift_set_led(2)
            # work_status.notices = notices
            # print(mb_client.input_regs)
        except Exception as e:
            print(e)
        time.sleep(0.2)

def task_chain_run_func():
    while True:
        if len(task_chain.task_list) > 0:
            work_status.mission_status = Mission_Status.Mission_Status_Running
            task_chain.task_status = AGF_Task_Status.AGF_Status_Running
            while True:
                for task in task_chain.task_list:
                    task_chain.task_current = task
                    if task['task_name'] == 'pick':#1
                        #########Di chuyen den diem detect pallet###########
                        print('AGF di chuyen den diem detect pallet')
                        Robot.navigation({'id':task['detect_point']})
                        time.sleep(5)
                        while True:
                            if Robot.check_target(Robot.data_Status,target=task['detect_point']):
                                break
                            if task_chain.task_signal_cancel:
                                Robot.cancel_navigation()
                                break
                            time.sleep(1)
                        if task_chain.task_signal_cancel:
                            break
                        #########Di chuyen den diem lay hang pallet#########
                        print('AGF di chuyen den diem lay pallet')
                        Robot.navigation({'id':task['pick_point']})
                        time.sleep(5)
                        while True:
                            if Robot.check_target(Robot.data_Status,target=task['pick_point']):
                                break
                            if task_chain.task_signal_cancel:
                                Robot.cancel_navigation()
                                break
                            time.sleep(1)
                        if task_chain.task_signal_cancel:
                            break
                        #########Lay pallet#######
                        print('AMR lay pallet')
                        lift_set_mission(mission="pick")
                        time.sleep(2)
                        lift_set_mode("auto")
                        time.sleep(2)
                        while True:
                            if len(mb_client.input_regs) == 50:
                                if mb_client.input_regs[0] == 1:
                                    break
                                if task_chain.task_signal_cancel:
                                    break
                            time.sleep(1)
                        lift_set_mission(mission="none")
                        time.sleep(1)
                        lift_set_mode("manual")
                        time.sleep(1)
                        if not task_chain.task_signal_cancel:
                            if mb_client.input_regs[5] == 1:
                                work_status.pallet = True
                            print('AMR lay xong pallet')
                        time.sleep(1)
                        #-------------------------------------------------------------
                    ######################
                    elif task['task_name'] == 'put':#2
                        # #AGF di chuyen den diem tra pallet
                        print('AGF di chuyen den diem tra pallet')
                        Robot.navigation({'id':task['put_point']})
                        time.sleep(5)
                        while True:
                            if Robot.check_target(Robot.data_Status,target=task['put_point']):
                                break
                            if task_chain.task_signal_cancel:
                                break
                            time.sleep(1)
                        if task_chain.task_signal_cancel:
                            break
                        #AGF tra pallet
                        print('AMR tra pallet')
                        lift_set_mission(mission="put")
                        time.sleep(2)
                        lift_set_mode("auto")
                        time.sleep(2)
                        while True:
                            if len(mb_client.input_regs) == 50:
                                if mb_client.input_regs[0] == 1:
                                    break
                                if task_chain.task_signal_cancel:
                                    break
                            time.sleep(1)
                        lift_set_mode("manual")
                        lift_set_mission(mission="none")
                        if not task_chain.task_signal_cancel:
                            work_status.pallet = False
                            print('AMR tra xong pallet')
                        time.sleep(1)
                    #------------------------------------------------------------
                    elif task['task_name'] == 'navigation':
                        print('AMR di chuyen den diem ' + task['target_point'])
                        Robot.navigation({'id':task['target_point']})
                        time.sleep(5)
                        while True:
                            if Robot.check_target(Robot.data_Status,target=task['target_point']):
                                break
                            if task_chain.task_signal_cancel:
                                break
                            time.sleep(1)
                        if task_chain.task_signal_cancel:
                            break
                        print('AMR da den diem ' + task['target_point'])
                        time.sleep(1)
                    #--------------------------------------------------------------
                    elif task['task_name'] == 'wait':
                        print('AMR cho : ' + str(task['wait_time']) + 's')
                        counter = 0
                        while True:
                            if counter > 10:
                                break
                            counter = counter + 1
                            time.sleep(1)
                        #--------------------------------------------------------
                if task_chain.task_signal_cancel:
                    break
                if not task_chain.loop:
                    break
            
            if task_chain.task_signal_cancel:#sau khi huy nhiem vu
                work_status.agf_work_mode = "Manual"
                work_status.mission_status = Mission_Status.Mission_Status_Cancle
                task_chain.task_signal_cancel = False
            else:#khi AGF xong nhiem vu
                work_status.mission_status = Mission_Status.Mission_Status_Complete
            task_chain.task_list = []
            task_chain.task_current = {}
            task_chain.task_status = AGF_Task_Status.AGF_Status_None
            work_status.agf_status = AGF_Status.AGF_Status_Idle
        print('-----------------------------------------------')
        time.sleep(3)


if __name__ == '__main__':
    agf_init_func()
    work_status.agf_status = AGF_Status.AGF_Status_Idle
    lift_set_led(2)

    task_poll_modbus = Thread(target=mb_client.poll_server,args=())
    task_poll_modbus.start()

    task_src_poll_status = Thread(target=task_src_poll_status_func,args=())
    task_src_poll_status.start()

    task_agf_poll_status = Thread(target=task_agf_poll_status_func,args=())
    task_agf_poll_status.start()

    task_chain_run = Thread(target=task_chain_run_func,args=())
    task_chain_run.start()

    task_server = Thread(target=app.run,args=(host:=AGF_Param_Config['host_api'],port:=AGF_Param_Config['port_api']))
    task_server.start()
