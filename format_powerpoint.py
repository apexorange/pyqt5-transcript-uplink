import re
import process_lines as pl
from globals import conditions_dict as cd

""" Prepare Text for Powerpoint """

def prepare_text_for_powerpoint(text: str) -> str:
    """
    This function takes in a text string and prepares it for use in a PowerPoint presentation.

    Parameters:
    text (str): The text to be prepared.

    Returns:
    str: The prepared text.

    """
    # Initial setup
    name = "Carly"
    first_num = None
    last_num = None
    capitalize = False
    phrase_being_assembled = ""
    completed_line_groups = []
    show_depo_name = True

    # Call Split text Function
    lines = pl.split_text(text)

    # Process each line
    for i, line in enumerate(lines):

        # Call Replace words Function
        line = pl.replace_words(line.strip(), cd['swap_phrase_dict'])

        # Call Detect Pages Numbers Function
        match = re.match(r'(\d+)\s*', line)
        result = pl.detect_page_numbers(line, match)
        num = result['num']
        line = result['line']
        if num is None:
            hidden_num = 0
        elif num is not None:
            if first_num is None:
                first_num = num
            last_num = num

        # Call Filter lines Function
        line = pl.filter_lines(line, match)
        if line is None:
            continue

        # Call Assemble phrases Function
        phrase_being_assembled, new_completed_line_groups, capitalize = pl.assemble_phrases(
            line, cd['qa_phrases'], cd['objection_phrases'], cd['non_party_phrases'], capitalize,
            phrase_being_assembled
        )
        completed_line_groups.extend(new_completed_line_groups)

    # Finalizing the assembled text
    if phrase_being_assembled:
        completed_line_groups.append(phrase_being_assembled.upper() if capitalize else phrase_being_assembled)

    # # Removing objections if necessary
    # if hide_objections:
    #     completed_line_groups = [line for line in completed_line_groups if not line.isupper()]

    # Format the final output
    return pl.format_output(completed_line_groups, first_num, last_num, show_depo_name, name)
