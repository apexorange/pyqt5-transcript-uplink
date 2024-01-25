import re
import sys
import fitz  # PyMuPDF
from PyQt5.QtCore import pyqtSlot, QTimer
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout,\
                               QCheckBox,QLabel, QSpacerItem, QSizePolicy, QLineEdit, QFileDialog, QMessageBox

build_number = 7710
known_issues_lst = ("- Segments that span multiple pages are not yet supported for designation lists",
                    "- Items imported from PDF appear in the left window in the order they were highlighted, "
                    "not sequentially",
                    "- The auto-generated cite does not yet account for multiple segments",
                    "- When copying from pdf or text file, make sure to include selection of the first line number to"
                    " get an accurate cite")
the_known_issues = "\n".join(known_issues_lst)
copyright_info = "Copyright 2024, Core Legal Concepts, LLC."


def sort_key(s):
    page, lines = s.split(':')
    start_line, end_line = map(int, lines.split('-'))
    return int(page), start_line


light_stylesheet = """
QPushButton {
    border-radius: 6px;
    color: #111111;
    background: #D9DADA;
    padding: 10px;
}
QLabel {
    padding: 10px;
}
QTextEdit {
    background-color: #ffffff;
    border-radius: 8px;
    padding: 10px;
}
}
QPushButton:pressed {
  background: #C2BBDE;
}
"""

dark_stylesheet = """
QPushButton {
  border-radius: 6px;
  color: #ffffff;
  background-color: #6A6A6A;
  padding: 10px;
}
QLabel {
    padding: 10px;
}
QLineEdit {
    border: 2px solid gray;
    background-color: #2B2B2B;
}
}
QPushButton:pressed {
  background: #64407C;
}
QTextEdit {
    background-color: #2b2b2b;
    border-radius: 8px;
    color: #F7F8FA;
    padding: 10px;
}

QWidget {
    background: rgb(80, 80, 80);
    color: #ffffff;
}
"""


class TextProcessorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.spacer = None
        self.build_number = None
        self.clear_button = None
        self.copy_oncue_button = None
        self.copy_powerpoint_button = None
        self.copyright_label = None
        self.flash_duration = None
        self.footer_text = None
        self.hide_names_checkbox = None
        self.hide_objections_checkbox = None
        self.load_pdf_button = None
        self.name_edit = None
        self.name_label = None
        self.text_box_bottom_right = None
        self.text_box_left = None
        self.text_box_right = None
        self.text_box_top_right = None
        self.text_box_top_right_label = None
        self.timer = None
        self.toggle_dark_mode(False)
        self.init_ui()

    def init_ui(self):
        '''PyQT 5 interface specific code'''

        ###########################################
        # SETUP UI
        ###########################################
        self.setWindowIcon(QIcon('corelogo80.png'))  # Set window icon
        self.spacer_top = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.spacer_bottom = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        ''' INITIALIZE CONTAINERS'''

        total_vbox = QVBoxLayout()  # Total container
        top_hbox = QHBoxLayout()  # First horizontal line
        hbox = QHBoxLayout()  # Second - text box - line
        button_hbox = QHBoxLayout()  # Third - buttons line
        label_hbox = QHBoxLayout()  # Fourth - footer line

        ###########################################
        # CREATE ELEMENTS FOR GUI
        ###########################################

        '''TIMER FOR FLASHING EFFECT'''

        self.timer = QTimer()
        self.timer.timeout.connect(self.reset_color)
        self.flash_duration = 200  # Duration in milliseconds

        '''CREATE LOAD PDF BUTTON'''

        # Create a button to load and extract highlights from a PDF
        self.load_pdf_button = QPushButton('Import Highlighted PDF')
        self.load_pdf_button.setStyleSheet("QPushButton {padding: 8px; }")
        self.load_pdf_button.clicked.connect(self.load_highlighted_pdf)

        '''CREATE DARK MODE TOGGLE'''

        self.dark_mode_switch = QCheckBox("Dark Mode", self)
        self.dark_mode_switch.stateChanged.connect(self.toggle_dark_mode)

        '''CREATE NAME TEXT BOX'''

        # Add the Depo_Name label and text box
        self.hide_depo_name_checkbox = QCheckBox('Name:')
        # self.name_label = QLabel("Name:")  # Set label
        self.name_edit = QLineEdit()  # Set editable textbox
        self.name_edit.setStyleSheet("QLineEdit {padding: 8px; }")
        self.name_edit.setText("Witness Dep.")  # Set initial text in editable text box
        # self.hide_names_checkbox.stateChanged.connect(self.on_text_change)
        self.hide_depo_name_checkbox.stateChanged.connect(self.hide_depo_name_checkbox_change)

        '''CREATE CHECKBOXES'''

        # Hide objections textbox
        self.hide_objections_checkbox = QCheckBox("Hide Objections")
        self.hide_objections_checkbox.setChecked(True)
        self.hide_objections_checkbox.stateChanged.connect(self.hide_objections_change)

        # Hide names checkbox
        self.hide_names_checkbox = QCheckBox("Hide Names")
        self.hide_names_checkbox.setChecked(True)
        self.hide_names_checkbox.stateChanged.connect(self.on_text_change)

        '''CREATE MAIN TEXT BOXES'''

        # Text boxes for input and output
        self.text_box_left = QTextEdit()
        self.text_box_left.setPlaceholderText("Paste PDF or TXT Transcript lines")
        self.text_box_top_right_label = QLabel("PowerPoint Format")
        self.text_box_top_right = QTextEdit()
        self.text_box_bottom_right = QTextEdit()

        '''CREATE CLEAR BUTTON'''

        self.clear_button = QPushButton('Clear')
        self.clear_button.setStyleSheet("QPushButton {padding: 8px; }")
        self.clear_button.clicked.connect(self.activate_clear_button)

        '''CREATE COPY TO POWERPOINT BUTTON'''

        self.copy_powerpoint_button = QPushButton('PowerPoint Copy')
        self.copy_powerpoint_button.setStyleSheet("QPushButton {padding: 8px; }")
        self.copy_powerpoint_button.clicked.connect(self.copy_top_right_to_clipboard)

        '''CREATE COPY TO ONCUE BUTTON'''

        self.copy_oncue_button = QPushButton('Designation Copy')
        self.copy_oncue_button.setStyleSheet("QPushButton {padding: 8px; }")
        self.copy_oncue_button.clicked.connect(self.copy_bottom_right_to_clipboard)

        '''CREATE COPYRIGHT AND FOOTER TEXT'''

        self.footer_text = QLabel(f"Known Issues:\n{the_known_issues}\n\n{copyright_info}\nBuild: {build_number}")
        # self.copyright_label = QLabel("Copyright 2024, Core Legal Concepts, LLC.")

        # Set the background color using CSS
        # self.footer_text.setStyleSheet("QLabel {background-color: #DFE2EE; padding: 20px;}")

        ###########################################
        # FORMATTING
        ###########################################

        '''FORMAT TEXT BOXES'''

        font = QFont()
        font.setPointSize(14)
        self.text_box_top_right.setFont(font)
        self.text_box_bottom_right.setFont(font)
        self.text_box_left.setAcceptRichText(False)
        self.text_box_top_right.setAcceptRichText(False)
        self.text_box_bottom_right.setAcceptRichText(False)
        self.text_box_left.setFont(font)

        ###########################################
        # ADD WIDGETS TO CONTAINERS
        ###########################################

        ''' ADD TOP ELEMENTS TO CONTAINERS'''

        top_hbox.addWidget(self.load_pdf_button)
        top_hbox.addSpacerItem(self.spacer_top)
        top_hbox.addWidget(self.dark_mode_switch)
        top_hbox.addWidget(self.hide_depo_name_checkbox)
        top_hbox.addWidget(self.name_edit)
        top_hbox.addWidget(self.hide_objections_checkbox)
        top_hbox.addWidget(self.hide_names_checkbox)

        ''' ADD TEXT BOX ELEMENTS TO CONTAINERS'''

        # Create a new vertical layout to stack the right text boxes
        vbox_right = QVBoxLayout()
        vbox_right.addWidget(self.text_box_top_right, stretch=2)  # Add the right text box
        vbox_right.addWidget(self.text_box_bottom_right,
                             stretch=1)  # Add the far right text box below the right text box

        hbox.addWidget(self.text_box_left)
        hbox.addLayout(vbox_right)  # Add the vbox_right layout to the hbox

        ''' ADD EXPORT BUTTONS TO CONTAINERS'''

        button_hbox.addWidget(self.clear_button)
        button_hbox.addSpacerItem(self.spacer_bottom)
        button_hbox.addWidget(self.copy_powerpoint_button)
        button_hbox.addWidget(self.copy_oncue_button)

        ''' ADD FOOTER TEXT TO CONTAINERS '''

        label_hbox.addWidget(self.footer_text)

        ###########################################
        # ADD LAYOUTS TO LARGER CONTAINER
        ###########################################

        # Finalize the layout setup
        total_vbox.addLayout(top_hbox)
        total_vbox.addLayout(hbox)  # This now contains the left text box and the stacked right text boxes
        total_vbox.addLayout(button_hbox)
        total_vbox.addLayout(label_hbox)

        ###########################################
        # OUTPUT TO OS
        ###########################################

        self.setLayout(total_vbox)
        self.setWindowTitle('Core Transcript Cleaner')
        self.resize(1200, 1000)
        self.text_box_left.textChanged.connect(self.on_text_change)

    def toggle_dark_mode(self, enabled):
        if enabled:
            self.setStyleSheet(dark_stylesheet)
        else:
            self.setStyleSheet(light_stylesheet)  # Set to default or light mode stylesheet

    def load_highlighted_pdf(self):
        # Prompt the user to select a PDF file
        pdf_path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF files (*.pdf);;All files (*)")

        if pdf_path:
            # Call the function to extract highlighted text and populate the left text field
            highlighted_text = self.extract_highlighted_text_with_coordinates(pdf_path)
            self.text_box_left.setPlainText(highlighted_text[0].strip())

    def extract_highlighted_text_with_coordinates(self, pdf_path) -> object:
        """ EXTRACT TEXT FROM PDF """

        highlighted_texts = []
        citations = []
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            annotations = page.annots()

            if annotations is not None:
                annotations_found = True
                for annot in annotations:
                    if annot.type[0] == 8:  # Check if the annotation is a highlight
                        rect = annot.rect
                        highlighted_text = page.get_text("text", clip=rect)

                        # Process the highlighted text and get line range info
                        line_range_info: str
                        process_pdf_highlighted_text: str
                        # line_range_info, process_pdf_highlighted_text = (
                        #     self.process_pdf_highlighted_text(highlighted_text, page_num))
                        result = self.process_pdf_highlighted_text(highlighted_text, page_num)
                        line_range_info = result[0]
                        process_pdf_highlighted_text = result[1]
                        highlighted_texts.append(f"\n--- Page {line_range_info}: \n{process_pdf_highlighted_text} "
                                                 f"---\n")
                        citations.append(line_range_info)

        doc.close()
        # if not annotations_found:
        #     self.show_error_dialog("No annotations found", "No highlighted annotations were found in the PDF.")

        return "".join(highlighted_texts), citations

    @staticmethod
    def process_pdf_highlighted_text(text, page_num):
        """ PREPARE TEXT THAT HAS BEEN EXTRACTED FROM PDF """

        processed_text = []
        first_line_number = None
        last_line_number = None
        lines = text.split('\n')

        for i, line in enumerate(lines):
            # Match a line number at the beginning of a line
            match = re.match(r'^(\d+)\s*$', line)
            if match:
                line_number = int(match.group(1))

                # Track the first and last line numbers
                if first_line_number is None:
                    first_line_number = line_number
                last_line_number = line_number

                # Append line number with the subsequent line of text
                if i + 1 < len(lines):
                    combined_line = f"{line_number} {lines[i + 1]}"
                    processed_text.append(combined_line)
            elif i == 0 or not re.match(r'^\d+\s*$', lines[i - 1]):
                # Include lines that are not immediately after a line number
                processed_text.append(line)

        # Format the line range and page information
        line_range_info = f"{page_num + 1}:{first_line_number}-{last_line_number}" if (first_line_number and
                                                                                       last_line_number) else f"{page_num + 1}"
        return line_range_info, '\n'.join(processed_text)

    @pyqtSlot()
    def hide_objections_change(self):
        """ Fill in """
        self.on_text_change()

    def hide_depo_name_checkbox_change(self):
        self.on_text_change()

    def on_text_change(self):
        """ Trigger text reprocessing when the left text field changes either by paste or import """
        text = self.text_box_left.toPlainText()
        prepare_text_for_powerpoint = self.prepare_text_for_powerpoint(text)
        prepare_text_for_oncue = self.prepare_text_for_oncue(text)
        self.text_box_top_right.setPlainText(prepare_text_for_powerpoint)
        self.text_box_bottom_right.setPlainText(prepare_text_for_oncue)

    def on_name_change(self):
        # Trigger text reprocessing when the name field changes
        self.on_text_change()

    """ PREPARE TEXT """

    ''' Text Processing '''

    def split_text(self, text):
        return text.split('\n')

    def replace_words(self, line, swap_phrase_dict):
        for word, replacement in swap_phrase_dict.items():
            if word in line:
                line = line.replace(word, replacement)
        return line


    """ Line Filtering"""

    # def detect_page_numbers(self, line, match):
    #     if match:
    #         num = int(match.group(1))
    #         return num, line[match.end():].lstrip()
    #     return None, line

    def detect_page_numbers(self, line, match):
        result = {'num': None, 'line': line}
        if match:
            result['num'] = int(match.group(1))
            result['line'] = line[match.end():].lstrip()
        return result

    def filter_lines(self, line, hide_names, match):
        if hide_names and line.startswith("BY") and ":" in line:
            return None
        if hide_names and line.startswith("QUESTIONS BY") and ":" in line:
            return None
        if line.startswith("--- Page"):
            return "\n\n" + line + "\n"
        return line


    """ Phrase Assembly """

    def assemble_phrases(self, line, qa_phrases, objection_phrases, non_party_phrases, capitalize, hide_objections,
                         phrase_being_assembled):
        completed_line_groups = []

        if any(line.startswith(phrase) for phrase in qa_phrases):
            if phrase_being_assembled and not (capitalize and hide_objections):
                completed_line_groups.append(phrase_being_assembled.upper() if capitalize else phrase_being_assembled)
            phrase_being_assembled = "\n" + line[:2] + "\t" + line[2:].lstrip()
            capitalize = False

        elif any(line.startswith(phrase) for phrase in objection_phrases):
            if phrase_being_assembled and not (capitalize and hide_objections):
                completed_line_groups.append(phrase_being_assembled.upper() if capitalize else phrase_being_assembled)
            phrase_being_assembled = "\n" + line
            capitalize = True

        elif any(line.startswith(phrase) for phrase in non_party_phrases):
            if phrase_being_assembled and not (capitalize and hide_objections):
                completed_line_groups.append(phrase_being_assembled.upper() if capitalize else phrase_being_assembled)
            phrase_being_assembled = "\n" + line
            capitalize = True

        else:
            if line and not (capitalize and hide_objections):
                if phrase_being_assembled and not any(line.startswith(phrase) for phrase in qa_phrases):
                    phrase_being_assembled += " "
                phrase_being_assembled += line

        return phrase_being_assembled, completed_line_groups, capitalize

    """ Final Output Formatting """

    def format_output(self, completed_line_groups, first_num, last_num, show_depo_name, name):
        processed_text = ''.join(completed_line_groups).strip()
        if show_depo_name:
            if first_num is not None:
                return processed_text + '\n\n{} Tr. Pg. __, Ln. {}-{}'.format(name, first_num, last_num)
        return processed_text


    """ Prepare Text for Powerpoint """

    def prepare_text_for_powerpoint(self, text):
        # Initial setup
        qa_phrases = ["Q.", "A."]
        objection_phrases = ["MR", "MS", "MRS", "ATTY", "ATTORNEY"]
        non_party_phrases = ["THE VIDEOGRAPHER"]
        swap_phrase_dict = {"THE WITNESS:": "A."}
        show_depo_name = self.hide_depo_name_checkbox.isChecked()
        hide_names = self.hide_names_checkbox.isChecked()
        hide_objections = self.hide_objections_checkbox.isChecked()
        first_num = None
        last_num = None
        capitalize = False
        phrase_being_assembled = ""
        completed_line_groups = []

        # Call Split text Function
        lines = self.split_text(text)

        # Process each line
        for i, line in enumerate(lines):

            # Call Replace words Function
            line = self.replace_words(line.strip(), swap_phrase_dict)

            # Call Detect Pages Numbers Function
            match = re.match(r'(\d+)\s*', line)
            result = self.detect_page_numbers(line, match)
            num = result['num']
            line = result['line']
            if num is None:
                hidden_num = 0
            elif num is not None:
                if first_num is None:
                    first_num = num
                last_num = num

            # Call Filter lines Function
            line = self.filter_lines(line, hide_names, match)
            if line is None:
                continue

            # Call Assemble phrases Function
            phrase_being_assembled, new_completed_line_groups, capitalize = self.assemble_phrases(
                line, qa_phrases, objection_phrases, non_party_phrases, capitalize, hide_objections,
                phrase_being_assembled
            )
            completed_line_groups.extend(new_completed_line_groups)

        # Finalizing the assembled text
        if phrase_being_assembled:
            completed_line_groups.append(phrase_being_assembled.upper() if capitalize else phrase_being_assembled)

        # Removing objections if necessary
        if hide_objections:
            completed_line_groups = [line for line in completed_line_groups if not line.isupper()]

        # Format the final output
        return self.format_output(completed_line_groups, first_num, last_num, show_depo_name, self.name_edit.text())

    def prepare_text_for_oncue(self, text):
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

    @pyqtSlot()
    def activate_clear_button(self):
        self.text_box_left.clear()

    def copy_top_right_to_clipboard(self):
        clipboard = QApplication.clipboard()
        selected_text = self.text_box_top_right.toPlainText()
        # self.flash_color(self.text_box_top_right)
        clipboard.setText(selected_text)

    def copy_bottom_right_to_clipboard(self):
        clipboard = QApplication.clipboard()
        selected_text = self.text_box_bottom_right.toPlainText()
        # self.flash_color(self.text_box_bottom_right)
        clipboard.setText(selected_text)


def main():
    app = QApplication(sys.argv)
    # Apply the complete dark theme to your Qt App.
    # qdarktheme.setup_theme("light")
    ex = TextProcessorApp()
    ex.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
