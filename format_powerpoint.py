import re
import processing_functions as pf
from globals import conditions_dict as cd

""" Prepare Text for Powerpoint """


def split_and_preprocess_text(text):
    """
    Splits the text into lines and preprocesses each line.
    """
    lines = pf.split_text(text)
    preprocessed_lines = [line.strip() for line in lines]
    return preprocessed_lines


def process_lines(lines):
    """
    Processes each line for page numbers, word replacements, line filtering, and phrase assembly.
    """
    first_num, last_num, capitalize = None, None, False
    phrase_being_assembled = ""
    completed_line_groups = []

    for line in lines:
        # Replace words
        line = pf.replace_words(line, cd['swap_phrase_dict'])

        # Detect page numbers
        match = re.match(r'(\d+)\s*', line)
        result = pf.detect_page_numbers(line, match)
        num = result['num']
        line = result['line']
        if num is not None:
            if first_num is None:
                first_num = num
            last_num = num

        # Filter lines
        line = pf.filter_lines(line, match)
        if line is None:
            continue

        # Assemble phrases
        phrase_being_assembled, new_completed_line_groups, capitalize = pf.assemble_phrases(
            line, cd['qa_phrases'], cd['objection_phrases'], cd['non_party_phrases'], capitalize,
            phrase_being_assembled
        )
        completed_line_groups.extend(new_completed_line_groups)

    if phrase_being_assembled:
        completed_line_groups.append(phrase_being_assembled.upper() if capitalize else phrase_being_assembled)

    return completed_line_groups, first_num, last_num


def finalize_and_format(completed_line_groups, first_num, last_num, witness_name_text="Jimmy" ):
    """
    Finalizes and formats the output.
    """
    # You might have additional processing here based on your requirements
    formatted_output = pf.format_output(completed_line_groups, first_num, last_num)
    formatted_output += '\n\n{} Tr. Pg. __, Ln. {}-{}'.format(witness_name_text, first_num, last_num)
    return formatted_output


def prepare_text_for_powerpoint(text):
    """
    Prepares text for PowerPoint presentation.
    """
    preprocessed_lines = split_and_preprocess_text(text)
    completed_line_groups, first_num, last_num = process_lines(preprocessed_lines)
    return finalize_and_format(completed_line_groups, first_num, last_num)
