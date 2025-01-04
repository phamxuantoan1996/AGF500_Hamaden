from abc import ABC,abstractmethod
import minimalmodbus
import serial
import time
from logfile import LogFile

class Modbus_Function_Code:
    #input
    ReadInputRegs = 4
    ReadHoldRegs = 3
    
    #holding
    WriteHoldRegs = 16
    WriteHoldReg = 6

class Modbus_Client(ABC):
    def __init__(self,slave_id:int,number_of_input:int,number_of_hold:int,input_regs_addr:int,hold_regs_addr:int,time_poll:int,timeout_modbus:int) -> None:
        super().__init__()
        self._timeout_modbus = timeout_modbus
        self._timeout_response = 10
        self._number_of_input = number_of_input
        self._number_of_hold = number_of_hold
        self._modbus_error = True
        self._input_regs = [0] * self._number_of_input
        self._hold_regs = [0] * self._number_of_hold
        self._input_regs_start = input_regs_addr
        self._hold_regs_start = hold_regs_addr
        self._time_poll = time_poll
        self._slave_id = slave_id
        self._log = LogFile("./LogfileAGF")
        self._log.init_logfile()

    @abstractmethod
    def connect_to_server(self) -> bool:
        pass

    @abstractmethod
    def read_input_regs(self):
        pass

    @abstractmethod
    def write_hold_regs(self):
        pass

    @abstractmethod
    def poll_server(self):
        pass
    @property
    def number_of_input(self):
        return self._number_of_input
    @property
    def number_of_hold(self):
        return self._number_of_hold
    @property 
    def slave_id(self):
        return self._slave_id
    @property
    def input_regs(self):
        return self._input_regs
    
    @property
    def hold_regs(self):
        return self._hold_regs
    @hold_regs.setter
    def hold_regs(self,val:list):
        self._hold_regs = val

    @property
    def modbus_error(self):
        return self._modbus_error
    
class Modbus_Serial_Client(Modbus_Client):
    def __init__(self, slave_id:int, number_of_input: int, number_of_hold: int,input_regs_addr:int,hold_regs_addr:int,time_poll:int,port:str,baudrate:int,timeout_modbus:int) -> None:
        super().__init__(slave_id=slave_id,number_of_input=number_of_input,number_of_hold=number_of_hold,timeout_modbus=timeout_modbus,input_regs_addr=input_regs_addr,hold_regs_addr=hold_regs_addr,time_poll=time_poll)
        self._port = port
        self._baudrate = baudrate
        
        
    def connect_to_server(self) -> bool:
        super().connect_to_server()
        try:
            # os.chmod(self.port,stat.S_IRWXO)
            self.client = minimalmodbus.Instrument(port=self._port,slaveaddress=self._slave_id,mode=minimalmodbus.MODE_RTU)
            self.client.serial.baudrate = self._baudrate
            self.client.serial.bytesize = 8
            self.client.serial.parity = serial.PARITY_NONE
            self.client.serial.timeout = self._timeout_modbus
            self.client.serial.stopbits = 1
            return True
        except Exception as e:
            self._log.writeLog(type_log="error",msg=str(e))
            print(e)
            return False
    
    def read_input_regs(self,address:int,count:int) -> list:
        super().read_input_regs()
        try:
            value = self.client.read_registers(registeraddress=address,numberOfRegisters=count,functioncode=Modbus_Function_Code.ReadInputRegs)
            return value
        except Exception as e:
            self._log.writeLog(type_log="error",msg=str(e))
            print(str(e))
            return []
    
    def write_hold_regs(self,address:int,value:list) -> None:
        super().write_hold_regs()
        try:
            self.client.write_registers(registeraddress=address,values=value)
            return True
        except Exception as e:
            self._log.writeLog(type_log="error",msg=str(e))
            print(str(e))
            return False
    
    def poll_server(self):
        super().poll_server()
        while True:
            self._input_regs = self.read_input_regs(address=self._input_regs_start,count=self.number_of_input)
            
            if self.write_hold_regs(address=self._hold_regs_start,value=self._hold_regs) and (len(self._input_regs) > 0):
                self._modbus_error = False
            else:
                self._modbus_error = True
            time.sleep(self._time_poll)

            
        






