from pypdf import PdfReader
from collections import defaultdict
from callgpt import call_gpt
import pandas as pd


def main():
    interpreter = PdfDataDictInterpreter('./pdf/SRC2022ReadMe_Group IV.pdf')

    while True:
        user_input = input("Enter a database identifier: ")
        if user_input == 'quit':
            break
        # ctx = interpreter.make_zero_shot_prompt(user_input)
        ctx = interpreter.make_few_shot_prompt(user_input)
        print(ctx)
        response = call_gpt(ctx)
        print(response)


def test_driver():
    interpreter = XmlDataDictInterpreter('./xml/ATBI_plots_20150511_atribs.xml')
    ctx = interpreter.make_zero_shot_prompt('MPD')
    print(ctx)


class DataDictInterpreter:

    def __init__(self):
        pass

    def make_zero_shot_prompt(self, identifier: str, example_limit: int = 10) -> str:
        context = self.get_context_around_identifier(identifier)

        limit_ix = min(example_limit, len(context))
        context_str = "\n".join(context[:limit_ix])

        prompt = f"""
Using the following text extracted from a data dictionary:
{context_str}

In the response, provide only the old identifier and new identifier (e.g. "old_identifier, new_identifier").
Create a meaningful and concise database identifier using SQL compatible complete words to represent abbreviations and acronyms for only the identifier {identifier}:
"""
        return prompt
    
    def make_few_shot_prompt(self, identifier: str, example_limit: int = 10) -> str:
        context = self.get_context_around_identifier(identifier)
        prompt_file = open('./prompts/fewshot.txt', 'r')
        prompt = prompt_file.read()
        prompt_file.close()
        prompt = prompt.replace('__IDENTIFIER__', identifier)
        prompt = prompt.replace('__CONTEXT__', "\n".join(context))
        return prompt

    def get_context_around_identifier(self, identifier: str, beam_width: int = None) -> list:
        pass

    def index_dictionary_file(self, file_obj) -> defaultdict:
        pass



class PdfDataDictInterpreter(DataDictInterpreter):
    """
    This class is used to interpret a PDF data dictionary
    """

    def __init__(self, pdf_file: str):
        super().__init__()
        print("Loading PDF")
        # If errors are encountered when reading the PDF, you may need to repair it first
        # using a program like ghostscript
        # https://ghostscript.readthedocs.io/en/latest/Use.html
        self.pdf = PdfReader(pdf_file)
        print("Loaded PDF with {} pages".format(len(self.pdf.pages)))
        print("Indexing PDF")
        self.index = self.index_dictionary_file(self.pdf)
        print("Indexed PDF")
        self.beam_width = 200


    def get_context_around_identifier(self, identifier: str, beam_width: int = None) -> list:
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
    """

    def __init__(self, xml_file: str):
        super().__init__()
        print("Loading XML")
        self.xml_text = open(xml_file, 'r').read()
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
        index = defaultdict(list)
        for ix, word in enumerate(self.xml_list):
            index[word].append(ix)
        return index

if __name__ == '__main__':
    test_driver()
    # main()