
from pypdf import PdfReader
from collections import defaultdict
from callgpt import call_gpt
import pandas as pd
import json
import os

class DataDictInterpreter:
    """
    This class is used to interpret a data dictionary 

    This is a superclass. Subclasses exist for different document types.
    
    Attributes:
        index: A dictionary mapping words to a list of locations in the document
        data_dict_file: The path to the data dictionary file
        filename: The name of the fewshot prompt file for a data dictionary
        call_gpt: A function that takes a prompt and returns a GPT response

    methods:
        interactive_prompt_builder: A method that prompts the user to build a fewshot prompt for a data dictionary
        make_zero_shot_prompt: A method that generates a zero-shot prompt for a data dictionary
        make_few_shot_prompt: A method that generates a few-shot prompt for a data dictionary
        get_context_around_identifier: A method that returns the context around an identifier in a data dictionary
        index_dictionary_file: A method that indexes a data dictionary file
        getNaturalIdentifier: A method that returns the natural identifier for a database identifier

    """

    def __init__(self, database_name: str = None, data_dict_file: str = None):

        self.index = defaultdict(list)

        if data_dict_file != None:
            self.data_dict_file = data_dict_file
            self.filename = self.data_dict_file.split('.')[-2] + "_fewshot.txt"
            if "/" in self.filename:
                self.filename = self.filename.split("/")[-1]

        elif database_name != None:
            db_file_xwalk = json.load(open('./database_dict_info.json', 'r'))
            data_dict_filename = db_file_xwalk[database_name]
            filetype = data_dict_filename.split('.')[-1]
            self.data_dict_file = "./" + filetype + "/" + data_dict_filename
            self.filename = (database_name + "_fewshot.txt")

        from callgpt import call_gpt
        self.call_gpt = call_gpt
        

    def interactive_prompt_builder(self, num_examples: int = 5):
        """ User interaction method to build a fewshot prompt for a data dictionary

        The interaction prompts the user to provide a valid database identifier for the document.
        The user is then prompted to confirm whether the generated identifier is a good example.
        If the user confirms the example is good, the example is added to the fewshot prompt.
        The user is then prompted to provide another valid database identifier for the document.
        This process repeats until the user has provided the desired number of examples.
        The user is then asked if the prompt should be saved to disk and used for the data dictionary.

        Args:
            num_examples: The number of examples to generate for the fewshot prompt

        Returns:
            None
        
        """
        num_good_examples = 0
        good_examples = []
        print(f"This is the interactive fewshot prompt builder. At the prompt, provide a valid database identifier for the document. Confirm whether the generated identifier is a good example.")
        while num_good_examples < num_examples:
            identifier_example = input(f"Enter example identifier {num_good_examples + 1}: ")
            ctx = self.make_zero_shot_prompt(identifier_example)
            response = call_gpt(ctx)
            print(ctx)
            print(response)
            user_assessment = input(f"Is this a good example of an N1 representation of example identifier {identifier_example} (Y/n)?:")
            if user_assessment.strip().lower() == 'y':
                good_examples.append("\n".join([ctx, response]))
                num_good_examples += 1
        prompt = "\n".join(good_examples)
        print("This is the fewshot prompt we generated:")
        print(prompt)
        user_approval = input("Should we save this prompt to disk and use it for this database (Y/n):")
        if user_approval.strip().lower() == 'y':
            
            print(f"Saving prompt file as {self.filename}")
            new_prompt_file = open(f"./prompts/{self.filename}", 'w')
            new_prompt_file.write(prompt)
            new_prompt_file.write("""
Using the following text extracted from a data dictionary:
__CONTEXT__

In the response, provide only the old identifier and new identifier (e.g. "old_identifier, new_identifier").
Create a meaningful and concise database identifier using SQL compatible complete words to represent abbreviations and acronyms for only the identifier __IDENTIFIER__:
""")
        elif user_approval.strip().lower() == 'n':
            user_response = input("Sorry, would you like to try again (Y/n)?")
            if user_response.strip().lower() == 'y':
                self.interactive_prompt_builder()
            else:
                print("Exiting prompt builder.")



    def make_zero_shot_prompt(self, identifier: str, context_limit: int = 10) -> str:
        """ Generates a zero-shot prompt for a data dictionary
        
        This method generates a zero-shot prompt for a data dictionary.
        The prompt is generated using the identifier provided by the user and the context around the identifier in the data dictionary.

        Args:
            identifier: The identifier to generate a zero-shot prompt for
            context_limit: The limit on number of instances of the identifier referenced within the text of the data dictionary to include in the prompt

        Returns:
            A zero-shot prompt for the data dictionary
        """

        context = self.get_context_around_identifier(identifier)

        limit_ix = min(context_limit, len(context))
        context_str = "\n".join(context[:limit_ix])

        prompt = f"""
Using the following text extracted from a data dictionary:
{context_str}

In the response, provide only the old identifier and new identifier (e.g. "old_identifier, new_identifier").
Create a meaningful and concise database identifier using SQL compatible complete words to represent abbreviations and acronyms for only the identifier {identifier}:
"""
        return prompt
    


    def make_few_shot_prompt(self, identifier: str, context_limit: int = 10) -> str:
        """ Generates a few-shot prompt for a data dictionary
        
        args:
            identifier: The identifier to generate a few-shot prompt for
            context_limit: The limit on number of instances of the identifier referenced within the text of the data dictionary to include in the prompt

        Returns:
            A few-shot prompt for the data dictionary
        """

        context = self.get_context_around_identifier(identifier)
        limit_ix = min(context_limit, len(context))
        context_str = "\n".join(context[:limit_ix])

        prompt = ""
        prompt_filename = './prompts/' + self.filename

        # check if prompt file exists
        file_exists = os.path.isfile(prompt_filename)

        if not file_exists:
            user_response = input(f"WARNING: No fewshot prompt file exists for this database. Would you like to generate one now (Y/n)?")
            if user_response.strip().lower() == 'y':
                self.interactive_prompt_builder()

        try:
            print(f"\nAttempting to load dictionary specific prompt file {prompt_filename}")
            prompt_file = open(prompt_filename, 'r')
        except:
            print("\n WARNING: No dictionary-specific prompt exists, using default fewshot prompt ./prompts/fewshot.txt instead.")
            prompt_file = open('./prompts/fewshot.txt', 'r')

        prompt = prompt_file.read()
        prompt_file.close()
        prompt = prompt.replace('__IDENTIFIER__', identifier)
        prompt = prompt.replace('__CONTEXT__', context_str)
        return prompt
    


    def getNaturalIdentifier(self, identifier: str) -> str:
        """ Returns the natural identifier for a database identifier

        Args:
            identifier: The identifier to get the natural identifier for

        Returns:
            The natural identifier for the database identifier
        """

        prompt = self.make_few_shot_prompt(identifier)
        response = self.call_gpt(prompt)
        response = response.split(",")
        if len(response) == 2:
            return response[1].strip()
        else:
            return response[0].strip()

    def get_context_around_identifier(self, identifier: str, beam_width: int = None) -> list:
        pass

    def index_dictionary_file(self, file_obj) -> defaultdict:
        pass



class PdfDataDictInterpreter(DataDictInterpreter):
    """ This class is used to interpret a PDF data dictionary

        Attributes:
            pdf: A PdfReader object representing the PDF data dictionary
            index: A dictionary mapping words to a list of locations in the document
            data_dict_file: The path to the data dictionary file
            filename: The name of the fewshot prompt file for a data dictionary
            call_gpt: A function that takes a prompt and returns a GPT response

        methods:
            get_context_around_identifier: A method that returns the context around an identifier in a data dictionary
            index_dictionary_file: A method that indexes a data dictionary file
    """

    def __init__(self, database_name: str = None, data_dict_file: str = None):
        super().__init__(database_name, data_dict_file)
        print("Loading PDF")
        # If errors are encountered when reading the PDF, you may need to repair it first
        # using a program like ghostscript
        # https://ghostscript.readthedocs.io/en/latest/Use.html
        self.pdf = PdfReader(self.data_dict_file)
        print("Loaded PDF with {} pages".format(len(self.pdf.pages)))
        print("Indexing PDF")
        self.index = self.index_dictionary_file(self.pdf)
        print("Indexed PDF")
        self.beam_width = 200



    def get_context_around_identifier(self, identifier: str, beam_width: int = None) -> list:
        """ Returns the context around an identifier in a data dictionary
        
        Args:
            identifier: The identifier to get the context around
            beam_width: The number of characters to include on either side of the identifier

        Returns:
            A list of strings containing the context around the identifier
        """

        if beam_width == None:
            beam_width = self.beam_width

        identifier = identifier.lower()
        locations = self.index[identifier]

        context_list = []

        for loc in locations:
            start_ix = max(0, loc[1] - beam_width)
            stop_ix = min(len(self.pdf.pages[loc[0]].extract_text()), loc[1] + beam_width)
            context_list.append(self.pdf.pages[loc[0]].extract_text()[start_ix : stop_ix])
        return context_list



    def index_dictionary_file(self, file_obj: PdfReader) -> defaultdict:
        """ Indexes a PDF data dictionary file

        Args:
            file_obj: A PdfReader object representing the PDF data dictionary

        Returns:
            A defaultdict mapping words to a list of locations in the document
        """

        # Create an index of words to pages and word positions
        index = defaultdict(list)
        for pg_ix, page in enumerate(file_obj.pages):
            page_text = page.extract_text().lower()
            for word in page_text.split():
                last_found_entry = index[word][-1] if len(index[word]) > 0 else None
                if last_found_entry != None and last_found_entry[0] == pg_ix:
                    # If the word was found on the same page, append the new position
                    index[word][-1] = (pg_ix, page_text.find(word, last_found_entry[1] + 1))
                else:
                    # Otherwise, add a new entry
                    index[word].append((pg_ix, page_text.find(word)))
        return index



class XmlDataDictInterpreter(DataDictInterpreter):
    """
    This class is used to interpret an XML data dictionary

    Attributes:
        xml_text: A string containing the text of the XML data dictionary
        xml_list: A list of words in the XML data dictionary
        index: A dictionary mapping words to a list of locations in the document
        data_dict_file: The path to the data dictionary file
        filename: The name of the fewshot prompt file for a data dictionary
        call_gpt: A function that takes a prompt and returns a GPT response

    methods:
        get_context_around_identifier: A method that returns the context around an identifier in a data dictionary
        index_dictionary_file: A method that indexes a data dictionary file
    """

    def __init__(self, database_name: str = None, data_dict_file: str = None):
        super().__init__(database_name, data_dict_file)
        print("Loading XML")
        self.xml_text = open(self.data_dict_file, 'r').read()
        xml_text = self.xml_text.replace('<', ' <').replace('>', '> ')
        xml_text = xml_text.replace('\n', ' ').replace('\t', ' ')
        xml_text = xml_text.lower()
        while '  ' in xml_text:
            xml_text = xml_text.replace('  ', ' ')
        self.xml_list = xml_text.split(' ')
        print("Loaded XML")
        print("Indexing XML")
        self.index = self.index_dictionary_file(self.xml_text)
        print("Indexed XML")
        self.beam_width = 15



    def get_context_around_identifier(self, identifier: str, beam_width: int = None) -> list:
        """ Returns the context around an identifier in a data dictionary

        Args:
            identifier: The identifier to get the context around
            beam_width: The number of words to include on either side of the identifier

        Returns:
            A list of strings containing the context around the identifier
        """

        if beam_width == None:
            beam_width = self.beam_width

        identifier = identifier.lower()
        locations = self.index[identifier]

        context_list = []

        for loc in locations:
            start_ix = max(0, loc - 1)
            stop_ix = min(len(self.xml_list), loc + beam_width)
            context_list.append(" ".join(self.xml_list[start_ix : stop_ix]))

        print(context_list)

        return context_list



    def index_dictionary_file(self, file_obj) -> defaultdict:
        """ Indexes an XML data dictionary file

        Args:
            file_obj: A string containing the text of the XML data dictionary

        Returns:
            A defaultdict mapping words to a list of locations in the document
        """

        index = defaultdict(list)
        for ix, word in enumerate(self.xml_list):
            index[word].append(ix)
        return index
    

class DataDictInterpreterFactory():

    def __init__(self, database_name: str) -> DataDictInterpreter:
        self.data_dict_interpreter = self.get_new_interpreter(database_name)

    def get_current_interpreter(self) ->  DataDictInterpreter:
        return self.data_dict_interpreter
    
    def get_new_interpreter(self, database_name: str) -> DataDictInterpreter:
        print(os.path.realpath(__file__))
        db_file_xwalk = json.load(open('./database_dict_info.json', 'r'))
        data_dict_filename = db_file_xwalk[database_name]
        filetype = data_dict_filename.split('.')[-1]

        if filetype == "xml":
            self.data_dict_interpreter =  XmlDataDictInterpreter(database_name)
            return self.data_dict_interpreter
        
        if filetype == "pdf":
            self.data_dict_interpreter =  PdfDataDictInterpreter(database_name)
            return self.data_dict_interpreter