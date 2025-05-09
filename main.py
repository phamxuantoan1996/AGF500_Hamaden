from threading import Thread
from agf_init import agf_init_func,mb_client,Robot,work_status,AGF_Param_Config,task_chain
import time
from agf_work_status import Mission_Status,AGF_Status
from agf_task_chain import AGF_Task_Status
from route import app
import requests

def lift_set_mode(mode:str):
    '''
    mode : "manual" or "auto"
    '''
    if mode == "manual":
        mb_client.hold_regs[10] = 0
        print('----------------------------------------------------------------------------------')
        print('----------------------------manual------------------------------------------------------')
        print('----------------------------------------------------------------------------------')
        print('----------------------------------------------------------------------------------')
    elif mode == "auto":
        mb_client.hold_regs[10] = 1
        print('----------------------------------------------------------------------------------')
        print('----------------------------auto------------------------------------------------------')
        print('----------------------------------------------------------------------------------')
        print('----------------------------------------------------------------------------------')
    
def lift_set_mission(mission:str):
    '''
    mission: "pick","put" or "none"
    '''
    if mission == "pick":
        mb_client.hold_regs[0] = 1
        print('----------------------------------------------------------------------------------')
        print('----------------------------------------------------------------------------------')
        print('------------------------------pick----------------------------------------------------')
        print('----------------------------------------------------------------------------------')
    elif mission == "put":
        mb_client.hold_regs[0] = 2
        print('----------------------------------------------------------------------------------')
        print('----------------------------------------------------------------------------------')
        print('------------------------------put----------------------------------------------------')
        print('----------------------------------------------------------------------------------')
    elif mission == 'none':
        mb_client.hold_regs[0] = 0
        mb_client.hold_regs[11] = 0
        mb_client.hold_regs[12] = 0

def lift_set_led(color:int):
    '''
    set led color
    '''
    mb_client.hold_regs[1] = color
    # print('----------------------------------------------------------------------------------')
    # print('----------------------------------------------------------------------------------')
    # print('------------------------------set color----------------------------------------------------')
    # print('----------------------------------------------------------------------------------')
    return True

def task_src_poll_status_func():
    while True:
        try:
            Robot.status(Robot.keys)
            # sound = Robot.robot_sound_status()
            alarm = Robot.robot_alarm_status()
            work_status.alarm = alarm
            # if 'sound_name' in sound.keys():
            #     work_status.agf_sound_audio = sound['sound_name']
        except Exception as e:
            print(e)
        time.sleep(0.3)

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
            notices = " "
            if Robot.data_Status["emergency"]:
                list_error.append("emergency")
                notices = notices + " AGF dừng khẩn cấp."
            if Robot.data_Status["blocked"]:
                list_error.append("blocked")
                notices = notices + " AGF gặp chướng ngại vật."
            if mb_client.modbus_error:
                list_error.append("modbus")
                notices = notices + "AGF lỗi truyền thông modbus."
            work_status.agf_error = list_error
            #audio
            if Robot.data_Status['emergency']:
                Robot.play_audio({"name":"error","loop":False})
            elif work_status.detect_pallet:
                Robot.play_audio({"name":"detect_pallet","loop":False})
            elif work_status.task_current != {}:
                if work_status.task_current['task_name'] == 'pick' and (mb_client.hold_regs[0] != 0):
                    if (work_status.human or mb_client.input_regs[7] != 0):
                        Robot.play_audio({"name":"human","loop":False})
                    else:
                        Robot.play_audio({"name":"picking_pallet","loop":False})
                elif work_status.task_current['task_name'] == 'put' and (mb_client.hold_regs[0] != 0):
                    if (work_status.human or mb_client.input_regs[7] != 0):
                        Robot.play_audio({"name":"human","loop":False})
                    else:
                        Robot.play_audio({"name":"puting_pallet","loop":False})
            #led
            if Robot.data_Status['emergency']:
                lift_set_led(9) #Blink red
            elif Robot.data_Status['blocked'] or mb_client.modbus_error or work_status.is_human:
                lift_set_led(8) #Red
            elif (Robot.data_Status['task_status'] == 0 or Robot.data_Status['task_status'] == 1 or Robot.data_Status['task_status'] == 4 or Robot.data_Status['task_status'] == 6) and work_status.task_list == []:
                lift_set_led(10) #Yellow
            elif work_status.agf_sound_audio == 'turnleft.wav' or work_status.agf_sound_audio == 'turnright.wav':
                lift_set_led(11)
            else:
                if work_status.task_current != {}:
                    if (work_status.task_current['task_name'] == 'pick' or work_status.task_current['task_name'] == 'put') and (mb_client.hold_regs[0] != 0):
                        if work_status.human:
                            notices = notices + " Có người trong vùng camera."
                            lift_set_led(8)
                        elif mb_client.input_regs[7] != 0:
                            notices = notices + " Có vật cản trong vùng lidar của AGF."
                            lift_set_led(8)
                        else:
                            lift_set_led(2)
                    else:
                        lift_set_led(2)
                else:
                    lift_set_led(2)
            work_status.notices = notices

            if task_chain.task_signal_pause:
                Robot.pause_navigation()
                time.sleep(1)
                task_chain.task_signal_pause = False

            if task_chain.task_signal_resume:
                Robot.resume_navigation()
                time.sleep(1)
                task_chain.task_signal_resume = False
            # print('input : ')
            # print(mb_client.input_regs)
            # print('hold : ')
            # print(mb_client.hold_regs)
            # print(work_status.agf_sound_audio)

        except Exception as e:
            print(e)
        time.sleep(0.3)

def task_post_status_agf_andon_server_func():
    url_post_status = "http://10.122.79.118:9000/robot_status/AGF_1"
    while True:
        try:
            status = Robot.data_Status
            status['work_status'] = work_status.get_agf_work_status()
            requests.post(url=url_post_status,json=status)
        except Exception as e:
            print(e)
        time.sleep(1)

def task_check_human_func():
    url_detect_human = "http://127.0.0.1:8001/detect_human"
    detect_human = {
        "enable":True,
        "thres":2.65
    }
      
    while True:
        try:
            response = requests.post(url=url_detect_human,json=detect_human)
            if response.status_code == 201:
                break
        except Exception as e:
            print(e)
        time.sleep(1)


    url_check_human = "http://127.0.0.1:8001/check_human"
    while True:
        try:
            response = requests.get(url=url_check_human)
            if response.status_code == 200:
                content = response.json()
                if content['human']:
                    print('co nguoi')
                    mb_client.hold_regs[13] = 1
                    work_status.human = True
                else:
                    print('khong co nguoi')
                    work_status.human = False
                    mb_client.hold_regs[13] = 0
        except Exception as e:
            print(e)
        if (work_status.task_current['task_name'] != 'pick' and work_status.task_current['task_name'] != 'put') or (mb_client.hold_regs[0] == 0):
            print('Dung detect nguoi')
            break
        time.sleep(0.1)
    work_status.human = False
    mb_client.hold_regs[13] = 0
    url_detect_human = "http://127.0.0.1:8001/detect_human"
    detect_human = {
        "enable":False,
        "thres":2.65
    }
    while True:
        try:
            response = requests.post(url=url_detect_human,json=detect_human)
            if response.status_code == 201:
                break
        except Exception as e:
            print(e)
        time.sleep(1)

def task_chain_run_func():
    while True:
        if len(task_chain.task_list) > 0:
            if work_status.agf_work_mode == "Auto":
                while True:
                    try:
                        url_post_progress = "http://10.122.79.118:9000/progress_mission"
                        confirm = {"mission_id":work_status.mission_recv['mission_id'],"mission_status":2}
                        requests.post(url=url_post_progress,json=confirm)
                        break
                    except Exception as e:
                        print(e)
                    time.sleep(0.5)
                time.sleep(110)
            work_status.mission_status = Mission_Status.Mission_Status_Running
            task_chain.task_status = AGF_Task_Status.AGF_Status_Running
            while True:
                task_index = 0
                for task in task_chain.task_list:
                    work_status.task_index = task_index
                    task_chain.task_current = task
                    if task['task_name'] == 'pick':#1
                        #########Di chuyen den diem detect pallet###########
                        print('AGF di chuyen den diem detect pallet')
                        while Robot.data_Status["emergency"]:
                            time.sleep(2)
                        Robot.navigation({'id':task['detect_point']})
                        time.sleep(4)
                        while True:
                            if Robot.check_target(Robot.data_Status,target=task['detect_point']):
                                break
                            if task_chain.task_signal_cancel:
                                Robot.cancel_navigation()
                                break
                            try:
                                if 'warnings' in work_status.alarm.keys() and (not Robot.data_Status["emergency"]):
                                    warnings = work_status.alarm['warnings']
                                    for warn in warnings:
                                        if "54025" in warn.keys():
                                            Robot.robot_estop_on()
                                            time.sleep(1)
                                            Robot.robot_estop_off()
                                            time.sleep(1)
                            except Exception as e:
                                print(e)
                            time.sleep(1)
                        if task_chain.task_signal_cancel:
                            break
                        #########Di chuyen den diem lay hang pallet#########
                        print('AGF di chuyen den diem lay pallet')
                        while Robot.data_Status["emergency"]:
                            time.sleep(2)
                        Robot.navigation({'id':task['pick_point']})
                        time.sleep(4)
                        while True:
                            if Robot.check_target(Robot.data_Status,target=task['pick_point']):
                                break
                            if task_chain.task_signal_cancel:
                                Robot.cancel_navigation()
                                break
                            
                            try:
                                if 'warnings' in work_status.alarm.keys() and (not Robot.data_Status["emergency"]):
                                    warnings = work_status.alarm['warnings']
                                    for warn in warnings:
                                        if "54025" in warn.keys():
                                            Robot.robot_estop_on()
                                            time.sleep(1)
                                            Robot.robot_estop_off()
                                            time.sleep(1)
                            except Exception as e:
                                print(e)
                            time.sleep(1)
                        if task_chain.task_signal_cancel:
                            break
                        #########Lay pallet#######
                        task_check_human = Thread(target=task_check_human_func,args=())
                        task_check_human.start()
                        print('AMR lay pallet')
                        lift_set_mission(mission="pick")
                        time.sleep(1)
                        lift_set_mode("auto")
                        time.sleep(1)
                        #bat dau detect nguoi
                        #########################
                        while True:
                            if len(mb_client.input_regs) == 50:
                                if mb_client.input_regs[0] == 0:
                                    break
                                if task_chain.task_signal_cancel:
                                    break
                            time.sleep(1)
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
                        else:
                            break
                        time.sleep(1)
                        #-------------------------------------------------------------
                    ######################
                    elif task['task_name'] == 'put':#2
                        # #AGF di chuyen den diem tra pallet
                        print('AGF di chuyen den diem tra pallet')
                        while Robot.data_Status["emergency"]:
                            time.sleep(2)
                        Robot.navigation({'id':task['put_point']})
                        time.sleep(4)
                        while True:
                            if Robot.check_target(Robot.data_Status,target=task['put_point']):
                                break
                            if task_chain.task_signal_cancel:
                                break
                            
                            try:
                                if 'warnings' in work_status.alarm.keys() and (not Robot.data_Status["emergency"]):
                                    warnings = work_status.alarm['warnings']
                                    for warn in warnings:
                                        if "54025" in warn.keys():
                                            Robot.robot_estop_on()
                                            time.sleep(1)
                                            Robot.robot_estop_off()
                                            time.sleep(1)
                            except Exception as e:
                                print(e)
                            time.sleep(1)
                        if task_chain.task_signal_cancel:
                            break
                        #AGF tra pallet
                        task_check_human = Thread(target=task_check_human_func,args=())
                        task_check_human.start()
                        print('AMR tra pallet')
                        lift_set_mission(mission="put")
                        time.sleep(1)
                        lift_set_mode("auto")
                        time.sleep(1)
                        while True:
                            if len(mb_client.input_regs) == 50:
                                if mb_client.input_regs[0] == 0:
                                    break
                                if task_chain.task_signal_cancel:
                                    break
                            time.sleep(1)
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
                        else:
                            break
                        time.sleep(1)
                    #------------------------------------------------------------
                    elif task['task_name'] == 'navigation':
                        print('AMR di chuyen den diem ' + task['target_point'])
                        while Robot.data_Status["emergency"]:
                            time.sleep(2)
                        Robot.navigation({'id':task['target_point']})
                        time.sleep(4)
                        while True:
                            if Robot.check_target(Robot.data_Status,target=task['target_point']):
                                break
                            if task_chain.task_signal_cancel:
                                break
                            
                            try:
                                if 'warnings' in work_status.alarm.keys() and (not Robot.data_Status["emergency"]):
                                    warnings = work_status.alarm['warnings']
                                    for warn in warnings:
                                        if "54025" in warn.keys():
                                            Robot.robot_estop_on()
                                            time.sleep(1)
                                            Robot.robot_estop_off()
                                            time.sleep(1)
                            except Exception as e:
                                print(e)
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
                    task_index = task_index + 1
                #################################
                if task_chain.task_signal_cancel:
                    if work_status.agf_work_mode == 'Auto':
                        while True:
                            try:
                                url_post_progress = "http://10.122.79.118:9000/progress_mission"
                                progress = {"mission_id":work_status.mission_recv['mission_id'],"mission_status":20}
                                requests.post(url=url_post_progress,json=progress)
                                break
                            except Exception as e:
                                print(e)
                            time.sleep(0.5)
                    work_status.agf_work_mode = "Manual"
                    work_status.mission_status = Mission_Status.Mission_Status_Cancle
                else:
                    if work_status.agf_work_mode == 'Auto':
                        while True:
                            try:
                                url_post_progress = "http://10.122.79.118:9000/progress_mission"
                                progress = {"mission_id":work_status.mission_recv['mission_id'],"mission_status":10}
                                requests.post(url=url_post_progress,json=progress)
                                break
                            except Exception as e:
                                print(e)
                            time.sleep(0.5)
                    work_status.mission_status = Mission_Status.Mission_Status_Complete
                if not task_chain.loop:
                    break
            if task_chain.task_signal_cancel:#sau khi huy nhiem vu
                task_chain.task_signal_cancel = False
                Robot.cancel_navigation()
            task_chain.task_list = []
            task_chain.task_current = {}
            task_chain.task_status = AGF_Task_Status.AGF_Status_None
            work_status.agf_status = AGF_Status.AGF_Status_Idle
            work_status.mission_recv = None
            work_status.task_index = None
        print('-----------------------------------------------')
        time.sleep(1.5)

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

    task_post_status_agf_andon_server = Thread(target=task_post_status_agf_andon_server_func,args=())
    task_post_status_agf_andon_server.start()

    task_server = Thread(target=app.run,args=(host:=AGF_Param_Config['host_api'],port:=AGF_Param_Config['port_api']))
    task_server.start()

