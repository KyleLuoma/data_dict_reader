from pypdf import PdfReader
from collections import defaultdict
from callgpt import call_gpt
import pandas as pd
from DataDictInterpreter import *


def main():
    factory = DataDictInterpreterFactory('NYSED_SRC2022')
    interpreter = factory.get_current_interpreter()
    # interpreter = XmlDataDictInterpreter(database_name='PacificIslandLandbirds')

    while True:
        user_input = input("Enter a database identifier: ")
        if user_input == 'quit':
            break
        natural_identifier = interpreter.getNaturalIdentifier(user_input)
        print(natural_identifier)



def test_driver():
    interpreter = XmlDataDictInterpreter('./xml/ATBI_plots_20150511_atribs.xml')
    # ctx = interpreter.make_zero_shot_prompt('MPD')
    # print(ctx)
    interpreter.interactive_prompt_builder()


if __name__ == '__main__':
    # test_driver()
    main()