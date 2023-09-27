import DataDictInterpreter
import json

class DataDictInterpreterFactory():

    def __init__(self, database_name: str) -> DataDictInterpreter:
        self.data_dict_interpreter = self.get_new_interpreter(database_name)

    def get_current_interpreter(self) ->  DataDictInterpreter:
        return self.data_dict_interpreter
    
    def get_new_interpreter(self, database_name: str) -> DataDictInterpreter:
        db_file_xwalk = json.load(open('./database_dict_info.json', 'r'))
        data_dict_filename = db_file_xwalk[database_name]
        filetype = data_dict_filename.split('.')[-1]

        if filetype == "xml":
            self.data_dict_interpreter =  DataDictInterpreter.XmlDataDictInterpreter(database_name)
            return self.data_dict_interpreter
        
        if filetype == "pdf":
            self.data_dict_interpreter =  DataDictInterpreter.PdfDataDictInterpreter(database_name)
            return self.data_dict_interpreter