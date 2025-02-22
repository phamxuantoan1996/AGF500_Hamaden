class AGF_Task_Status:
    AGF_Status_None = 0
    AGF_Status_Running = 1
    AGF_Status_Pause = 2
    AGF_Status_Cancel = 3
class AGF_Task_Chain:
    def __init__(self):
        self.__task_list = []
        self.__task_current = {}
        self.__loop = False
        self.__task_status = AGF_Task_Status.AGF_Status_None
        self.__task_signal_cancel = False
        self.__task_signal_detect_pallet_resume = False
        self.__task_signal_pause = False
        self.__task_signal_resume = False

    @property
    def task_list(self) -> list:
        return self.__task_list
    @task_list.setter
    def task_list(self,task_list:list):
        self.__task_list = task_list

    @property
    def task_current(self):
        return self.__task_current
    @task_current.setter
    def task_current(self,task_current):
        self.__task_current = task_current

    @property
    def task_status(self):
        return self.__task_status
    @task_status.setter
    def task_status(self,status:AGF_Task_Status):
        self.__task_status = status

    @property
    def loop(self):
        return self.__loop
    @loop.setter
    def loop(self,loop:bool):
        self.__loop = loop

    @property
    def task_signal_cancel(self) -> bool:
        return self.__task_signal_cancel
    @task_signal_cancel.setter
    def task_signal_cancel(self,signal:bool):
        self.__task_signal_cancel = signal

    @property
    def task_signal_detect_pallet_resume(self) -> bool:
        return self.__task_signal_detect_pallet_resume
    @task_signal_detect_pallet_resume.setter
    def task_signal_detect_pallet_resume(self,val : bool):
        self.__task_signal_detect_pallet_resume = val

    @property
    def task_signal_pause(self) -> bool:
        return self.__task_signal_pause
    @task_signal_pause.setter
    def task_signal_pause(self,val:bool):
        self.__task_signal_pause = val

    @property
    def task_signal_resume(self) -> bool:
        return self.__task_signal_resume
    @task_signal_resume.setter
    def task_signal_resume(self,val:bool):
        self.__task_signal_resume = val
