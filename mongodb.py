import pymongo

class AGF_System_DB_Collection:
    AGF_Mission_Pending = 'AGF_Mission_Pending'
    AGF_Mission_Executing = 'AGF_Mission_Executing'
    AGF_Mission_Completed = 'AGF_Mission_Completed'
    AGFs_Info = 'AGFs_Info'

class AGF_Hamaden_Collection:
    AGF_Info = "AGF_Info"
    AGF_Log = "AMR_Log"


class MongoDB:
    def __init__(self,database_name:str,collections_name:list) -> None:
        self.clientMongo = pymongo.MongoClient('mongodb://localhost:27017/')
        self.collectionsDB = {}
        self.database_name = database_name
        self.collections_name = collections_name

    def MongoDB_check(self) -> bool:
        try:
            self.clientMongo.admin.command("ping")
            
            databases_name = self.clientMongo.list_database_names()

            if self.database_name in databases_name:
                self.mongoDB = self.clientMongo[self.database_name]

                collections = self.mongoDB.list_collection_names()
                for name in self.collections_name:
                    if name in collections:
                        self.collectionsDB[name] = self.mongoDB[name]
                    else:
                        return False
                return True
        except Exception as e:
            print(e)
        return False
    
    def MongoDB_insert(self,collection_name:str,data:dict) -> bool:
        try:
            self.collectionsDB[collection_name].insert_one(data)
            return True
        except Exception as e:
            print(e)
            return False

    def MongoDB_detele(self,collection_name:str,data:dict) -> int:
        try:
            res = self.collectionsDB[collection_name].delete_one(data)
            return res.deleted_count
        except Exception as e:
            print(e)
            return -1
        

    def MongoDB_find(self,collection_name:str,query:dict) -> list:
        try:
            return list(self.collectionsDB[collection_name].find(query))
        except Exception as e:
            print(e)
            return []


# db = MongoDB(database_name='AGF_System_DB',collections_name=[AGF_System_DB_Collection.AGF_Mission_Completed,AGF_System_DB_Collection.AGF_Mission_Executing,AGF_System_DB_Collection.AGF_Mission_Pending,AGF_System_DB_Collection.AGFs_Info])
# print(db.MongoDB_check())

# print(db.MongoDB_find(AGF_System_DB_Collection.AGF_Mission_Pending,{}))
