from mongodb import AGF_Hamaden_Collection,MongoDB

from datetime import datetime
from bson import ObjectId

class LogDataBase:
    def __init__(self,database:MongoDB) -> None:
        self.database = database

    def writeLog(self,msg:str) -> bool:
        mongoDocument = {}
        current = datetime.now()
        mongoDocument["date"] = current.strftime("%Y-%m-%d")
        mongoDocument["time"] = current.strftime("%H:%M:%S")
        mongoDocument["msg"] = msg
        mongoDocument["_id"] = str(ObjectId())
        return self.database.MongoDB_insert(AGF_Hamaden_Collection.AGF_Log,mongoDocument)
    
    def readLog(self,date:str) -> list:
        mongoQuery = {'date':date}
        return self.database.MongoDB_find(AGF_Hamaden_Collection.AGF_Log,mongoQuery)
