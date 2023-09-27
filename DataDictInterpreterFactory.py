import DataDictInterpreter
import json

class DataDictInterpreterFactory():

    def __init__(self, database_name: str) -> DataDictInterpreter:
        db_file_xwalk = json.load(open('./database_dict_info.json', 'r'))
        data_dict_filename = db_file_xwalk[database_name]
        filetype = data_dict_filename.split('.')[-1]

        if filetype == "xml":
            return DataDictInterpreter.XmlDataDictInterpreter(database_name)
        
        if filetype == "pdf":
            return DataDictInterpreter.PdfDataDictInterpreter(database_name)