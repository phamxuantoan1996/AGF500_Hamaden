class Lift_Dir:
    Lift_Up = "Up"
    Lift_Down = "Down"
    Lift_Stop = "Stop"

class Slider_Dir:
    In = 'In'
    Out = 'Out'
    Stop = 'stop'
class AGF_Work_Mode:
    Manual = "Manual"
    Auto = "Auto"

class Pallet_State:
    Pallet_Empty = "Empty"
    Pallet_Full = "Full"
    Pallet_None = "None"

class Mission_Status:
    Mission_Status_None = "None"
    Mission_Status_Cancle = "Cancle"
    Mission_Status_Running = "Running"
    Mission_Status_Complete = "Complete"

class AGF_Status:
    AGF_Status_Idle = 1
    AGF_Status_Busy = 2

class AGF_Work_Status:
    def __init__(self,agf_id:int):
        self.__agf_id = agf_id
        self.__agf_error = []
        self.__agf_work_mode = AGF_Work_Mode.Manual
        self.__pallet = False
        self.__task_list = []
        self.__task_current = {}
        self.__slider_speed = 0
        self.__slider_dir = Slider_Dir.Stop
        self.__lift_dir = Lift_Dir.Lift_Stop
        self.__lift_pos = 0
        self.__agf_sound_audio = ""
        self.__notices = "AMR Busy"
        self.__mission_status = Mission_Status.Mission_Status_None
        self.__agf_status = AGF_Status.AGF_Status_Idle
        self.__is_human = False
        self.__mission_recv = None
        self.__task_index = None

    
    def get_agf_work_status(self) -> dict:
        status = {
            "agf_id":self.__agf_id,
            "agf_status":self.__agf_status,
            "agf_error":self.__agf_error,
            "pallet":self.__pallet,
            "task_list":self.__task_list,
            "task_current":self.__task_current,
            "slider_speed":self.__slider_speed,
            "slider_dir":self.__slider_dir,
            "lift_dir":self.__lift_dir,
            "lift_pos":self.__lift_pos,
            "agf_work_mode":self.__agf_work_mode,
            "notices":self.__notices,
            "mission_status":self.__mission_status,
            "mission_recv":self.__mission_recv,
            "task_index":self.__task_index
        }
        return status
    
    @property
    def agf_id(self) -> int:
        return self.__agf_id
    @agf_id.setter
    def agf_id(self,id:int):
        self.__agf_id = id

    @property
    def agf_status(self) -> AGF_Status:
        return self.__agf_status
    @agf_status.setter
    def agf_status(self,status:AGF_Status):
        self.__agf_status = status

    @property
    def agf_error(self) -> list:
        return self.__agf_error
    @agf_error.setter
    def agf_error(self,error:list):
        self.__agf_error = error

    @property
    def pallet(self) -> bool:
        return self.__pallet
    @pallet.setter
    def pallet(self,pallet:bool):
        self.__pallet = pallet
    
    @property
    def task_list(self) -> list:
        return self.__task_list
    @task_list.setter
    def task_list(self,task_list:list):
        self.__task_list = task_list

    @property
    def task_current(self) -> dict:
        return self.__task_current
    @task_current.setter
    def task_current(self,task_current:dict):
        self.__task_current = task_current

    @property
    def agf_work_mode(self) -> str:
        return self.__agf_work_mode
    @agf_work_mode.setter
    def agf_work_mode(self,mode:str):
        self.__agf_work_mode = mode

    @property
    def slider_speed(self):
        return self.__slider_speed
    @slider_speed.setter
    def slider_speed(self,speed:int):
        self.__slider_speed = speed

    @property
    def slider_dir(self):
        return self.slider_dir
    @slider_dir.setter
    def slider_dir(self,dir:int):
        if dir == 1:
            self.__slider_dir = Slider_Dir.In
        if dir == 2:
            self.__slider_dir = Slider_Dir.Out
        if dir == 0:
            self.__slider_dir = Slider_Dir.Stop

    @property
    def lift_dir(self):
        return self.__lift_dir
    @lift_dir.setter
    def lift_dir(self,dir:int):
        if dir == 2:
            self.__lift_dir = Lift_Dir.Lift_Up
        if dir == 1:
            self.__lift_dir = Lift_Dir.Lift_Down
        if dir == 0:
            self.__lift_dir = Lift_Dir.Lift_Stop
    
    @property
    def lift_pos(self):
        return self.__lift_pos
    @lift_pos.setter
    def lift_pos(self,pos:int):
        self.__lift_pos = pos


    @property
    def agf_sound_audio(self):
        return self.__agf_sound_audio
    @agf_sound_audio.setter
    def agf_sound_audio(self,audio:str):
        self.__agf_sound_audio = audio

    @property
    def notices(self):
        return self.__notices
    @notices.setter
    def notices(self,notice:str):
        self.notices = notice

    @property
    def mission_status(self) -> Mission_Status:
        return self.__mission_status
    @mission_status.setter
    def mission_status(self,status:Mission_Status):
        self.__mission_status = status

    @property
    def is_human(self) -> bool:
        return self.__is_human
    @is_human.setter
    def is_human(self,human):
        self.__is_human = human

    @property
    def mission_recv(self) -> dict:
        return self.__mission_recv
    @mission_recv.setter
    def mission_recv(self,mission:dict):
        self.__mission_recv = mission

    @property
    def task_index(self) -> int:
        return self.__task_index
    @task_index.setter
    def task_index(self,index:int):
        self.__task_index = index
