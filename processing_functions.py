def split_text(text):
    return text.split('\n')


def replace_words(line, swap_phrase_dict):
    for word, replacement in swap_phrase_dict.items():
        if word in line:
            line = line.replace(word, replacement)
    return line


''' LINE FILTERING '''


def detect_page_numbers(line, match):
    result = {'num': None, 'line': line}
    if match:
        result['num'] = int(match.group(1))
        result['line'] = line[match.end():].lstrip()
    return result


def filter_lines(line, match):
    if line.startswith("BY") and ":" in line:
        return None
    if line.startswith("QUESTIONS BY") and ":" in line:
        return None
    if line.startswith("--- Page"):
        return "\n\n" + line + "\n"
    return line


"""Phrase Assembly"""


def assemble_phrases(line, qa_phrases, objection_phrases, non_party_phrases, capitalize, phrase_being_assembled):
    completed_line_groups = []

    def should_append_completed_phrase(phrase_list):
        return any(line.startswith(phrase) for phrase in phrase_list) and phrase_being_assembled and not capitalize

    def append_completed_phrase():
        completed_line_groups.append(phrase_being_assembled.upper() if capitalize else phrase_being_assembled)

    def update_phrase_being_assembled(new_line, new_capitalize):
        nonlocal phrase_being_assembled, capitalize
        if should_append_completed_phrase(qa_phrases):
            append_completed_phrase()
        phrase_being_assembled = new_line
        capitalize = new_capitalize

    if any(line.startswith(phrase) for phrase in qa_phrases):
        update_phrase_being_assembled("\n" + line[:2] + "\t" + line[2:].lstrip(), False)
    elif any(line.startswith(phrase) for phrase in objection_phrases + non_party_phrases):
        update_phrase_being_assembled("\n" + line, True)
    else:
        if line and not capitalize:
            if phrase_being_assembled and not any(line.startswith(phrase) for phrase in qa_phrases):
                phrase_being_assembled += " "
            phrase_being_assembled += line

    return phrase_being_assembled, completed_line_groups, capitalize


""" Final Output Formatting """


def format_output(completed_line_groups, first_num, last_num):
    processed_text = ''.join(completed_line_groups).strip()
    # if show_depo_name:
    #     if first_num is not None:
    #         return processed_text + '\n\n{} Tr. Pg. __, Ln. {}-{}'.format(name, first_num, last_num)
    # print(processed_text)
    return processed_text
