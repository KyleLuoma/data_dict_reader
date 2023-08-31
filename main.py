from pypdf import PdfReader
from collections import defaultdict
from callgpt import call_gpt
import pandas as pd



def main():
    interpreter = PdfDataDictInterpreter('./pdf/repaired.pdf')

    while True:
        user_input = input("Enter a database identifier: ")
        if user_input == 'quit':
            break
        ctx = interpreter.make_zero_shot_prompt(user_input)
        print(ctx)
        response = call_gpt(ctx)
        print(response)



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
Create a descriptive database identifier using complete words to represent abbreviations and acronyms for only the identifier {identifier}:
"""
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
        self.beam_width = 100


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
            char_count = 0
            for word in page.extract_text().lower().split():
                index[word].append((pg_ix, char_count))
                char_count += (len(word) + 1)
        return index


if __name__ == '__main__':
    main()