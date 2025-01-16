#!/usr/bin/python3
from socket import socket
from frame import tranmit
from api import status, navigation, config, control, other
import socket
import time
import logging
import datetime
import asyncio
import json


format_HMS = '%H:%M:%S'


class ESA_API:
    def __init__(self,host:str):
        self.host = host
        self.apiRobotStatus     = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.apiRobotNavigation = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.apiRobotOther      = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.apiRobotConfig      = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.apiRobotControl      = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
       
        self.data_Status={}
        self.keys = {
            "keys":["area_ids","confidence","current_station","last_station","vx","vy","blocked","block_reason","battery_level",
                "task_status","target_id","emergency","x","y","unfinished_path","target_dist","angle","reloc_status","current_map", "charging","errors"],
            "return_laser":False,
            "return_beams3D":False
        }

    def connect_status(self) -> bool:
        try:
            self.apiRobotStatus.settimeout(5000)
            self.apiRobotStatus.connect((self.host,19204))
            logging.info("connect STATUS success")
            return True
        except socket.error:
            logging.info("connection STATUS lost... reconnecting")
            time.sleep(5)
            self.connect_status()
            return False
            
    def connect_navigation(self) -> bool:
        try:
            self.apiRobotNavigation.settimeout(5000)
            self.apiRobotNavigation.connect((self.host,19206))
            logging.info("connect NAVIGATION success")
            return True
        except socket.error:
            logging.info("connection NAVIGATION lost... reconnecting")
            time.sleep(5)
            self.connect_navigation()
            return False
    def connect_other(self) -> bool:
        try:
            self.apiRobotOther.settimeout(5000)
            self.apiRobotOther.connect((self.host,19210))
            logging.info("connect OTHER success")
            return True
        except socket.error:
            logging.info("connection OTHER lost... reconnecting")
            time.sleep(5)
            self.connect_other()
            return False
    def connect_config(self) -> bool:
        try:
            self.apiRobotConfig.settimeout(5000)
            self.apiRobotConfig.connect((self.host,19207))
            logging.info("connect CONFIG success")
            return True
        except socket.error:
            logging.info("connection CONFIG lost... reconnecting")
            time.sleep(5)
            self.connect_config()
            return False
    def connect_control(self) -> bool:
        try:
            self.apiRobotControl.settimeout(5000)
            self.apiRobotControl.connect((self.host,19205))
            logging.info("connect CONTROL success")
            return True
        except socket.error:
            logging.info("connection CONTROL lost... reconnecting")
            time.sleep(5)
            self.connect_control()
            return False
    def navigation(self,jsonstring:dict) -> bool:
        result = tranmit.sendAPI(self.apiRobotNavigation, navigation.robot_task_gotarget_req, jsonstring)
        logging.info(result)
        if result['ret_code'] != 0:
            logging.info(result)
            return False
        return True
    
    def cancel_navigation(self) -> bool:
        result = tranmit.sendAPI(self.apiRobotNavigation,navigation.robot_task_cancel_req,{})
        if result['ret_code'] != 0:
            logging.error("Cancel Navigation Fail")
            return False
        logging.info("Cancel Navigation Success")
        return True
    
    def pause_navigation(self) -> bool:
        result = tranmit.sendAPI(self.apiRobotNavigation,navigation.robot_task_pause_req,{})
        if result['ret_code'] != 0:
            logging.error("Pause Navigation Fail")
            return False
        logging.info("Pause Navigation Success")
        return True
    
    def resume_navigation(self) -> bool:
        result =tranmit.sendAPI(self.apiRobotNavigation,navigation.robot_task_resume_req,{})
        if result['ret_code'] != 0:
            logging.error("Resume Navigation Fail")
            return False
        logging.info("Resume Navigation Success")
        return True
    
    def status(self,key):
        #request location robot
        try:
            self.data_Status = tranmit.sendAPI(self.apiRobotStatus, status.robot_status_all1_req, key)
        except Exception as e:
            print(e)
        
    def confim_location(self):
        return tranmit.sendAPI(self.apiRobotControl,control.robot_control_comfirmloc_req,{})
    def confim_cancel_location(self):
        return tranmit.sendAPI(self.apiRobotControl,control.robot_control_comfirmloc_req,{})

    def device_setShelf(self,jsonString:dict):
        result = tranmit.sendAPI(self.apiRobotConfig, config.robot_config_set_shelfshape_req, jsonString)
        if result['ret_code'] != 0:
            logging.error("Set Shelf Fail")
            return False
        logging.info("Set Shelf Success")
        return True
    
    def fork(self, jsonString:dict):
        print("data", jsonString)
        result = tranmit.sendAPI(self.apiRobotOther, other.robot_other_set_fork_height_req, jsonString)
        if result['ret_code'] != 0:
            logging.error("Fork Fail")
            return False
        logging.info("Fork Success")
        return True
    
    def device_unsetShelf(self,jsonString:dict):
        result = tranmit.sendAPI(self.apiRobotConfig, config.robot_config_clear_goodsshape_req, jsonString)
        if result['ret_code'] != 0:
            logging.error("Unset Shelf Fail")
            return False
        logging.info("Unset Shelf Success")
        return True
    
    def control_audio(self,jsonString:dict):
        return tranmit.sendAPI(self.apiRobotOther, other.robot_other_play_audio_req, jsonString)
    
    def play_audio(self,jsonString:dict):
        return tranmit.sendAPI(self.apiRobotOther, other.robot_other_play_audio_req, jsonString)
    
    def stop_audio(self,jsonString:dict):
        return tranmit.sendAPI(self.apiRobotOther, other.robot_other_stop_audio_req, jsonString)
        
    def navigation_move_task_list(self,jsonstring:dict):
        return tranmit.sendAPI(self.apiRobotNavigation, navigation.robot_task_gotargetlist_req, jsonstring)
    
    def device_map(self,map_name:str):
        return tranmit.sendAPI(self.apiRobotControl,control.robot_control_loadmap_req,{"map_name":map_name})

    def check_target(self,data_status:dict, target:str):
        time.sleep(1)
        try:
            if(data_status['task_status'] == 4):
                if(data_status['current_station']) == target:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            # handleLog("Error : " + str(e))
            return False
    def monitor(self, data:dict):
        result = tranmit.sendAPI(self.apiRobotControl,control.robot_control_motion_req, data)

    def re_location(self, data:dict):
        result =  tranmit.sendAPI(self.apiRobotControl,control.robot_control_reloc_req,data)
        return result
    
    def connect_all(self):
        try:
            self.connect_config()
            self.connect_control()
            self.connect_other()
            self.connect_status()
            self.connect_navigation()
            msg = (f"Robot khởi động thành công !!!")
            # handleLog(msg, "F")
            self.connectAPI = True
        except Exception as E:
            self.connectAPI = False
            msg = (f"Robot khởi động thất bại, vui lòng đợi hệ thống kết nối !!!")
            # handleLog(msg, "F")
    
    def init_log(self):
        logging.basicConfig(filename="C:/Users/Admin/Downloads/27_7/1._base/logs/log_"+str(datetime.date.today())+".log",
        filemode='a', #Ghi thêm vào đuôi file
        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
        datefmt='%H:%M:%S', #Định nghĩa thời gian
        level=logging.INFO)
        logging.info("------------------START Server ESATECH v1.2------------------")
        log = logging.getLogger('__name__')
        log.setLevel(logging.INFO)

    def switch_map(self,map_name:str):
        tranmit.sendAPI(self.apiRobotControl,control.robot_control_loadmap_req,{"map_name":map_name})
        self.message = "Đang chuyển bản đồ, vui lòng đợi..."
        # handleLog(self.message, "F")
        while(self.data_Status['current_map'] != map_name) and not self.cancel:
            pass
        while self.data_Status["reloc_status"] != 1 and not self.cancel:
            if self.data_Status["reloc_status"] == 3:
                try:
                    self.confim_local()
                    self.message = f"Chuyển bản đồ, xác nhận vị trí thành công"
                    # handleLog(self.message, "F")
                except:
                    pass
            time.sleep(1)
    def set_shelf_shape(self,shelf_shape:str):
        try:
            return tranmit.sendAPI(self.apiRobotConfig,config.robot_config_set_shelfshape_req,{"object_path":shelf_shape})
        except Exception as e:
            return None
        
    def clear_shelf_shape(self):
        try:
            return tranmit.sendAPI(self.apiRobotConfig,config.robot_config_clear_goodsshape_req,{})
        except Exception as e:
            return None
    def robot_sound_status(self):
        try:
            return tranmit.sendAPI(self.apiRobotStatus,status.robot_status_sound_req,{})
        except Exception as e:
            return None
        












    




        
        

        

