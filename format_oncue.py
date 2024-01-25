import re

""" Prepare Text for OnCue """

def sort_key(s):
    """ Sort designations"""
    page, lines = s.split(':')
    start_line, end_line = map(int, lines.split('-'))
    return int(page), start_line

def prepare_text_for_oncue(text):
    matches = []
    lines = text.split()
    for i, line in enumerate(lines):
        line = line.strip()  # Strips any white-space at the beginning or end of a line
        match = re.match(r'\d+:\d+-\d+:', line)

        if match:
            matches.append(line.rstrip(":"))

    sorted_matches = sorted(matches, key=sort_key)
    processed_text = "\n".join(sorted_matches)
    return processed_text
