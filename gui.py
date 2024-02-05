import re
import sys
import fitz #pymupdf
import metadata as meta
import pdf_intake as pd
import processing_functions as pl
import format_powerpoint as fp
import format_oncue as fo
import globals as gb
from PyQt5.QtCore import pyqtSlot, QTimer
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout,\
                               QCheckBox,QLabel, QSpacerItem, QSizePolicy, QLineEdit, QFileDialog, QMessageBox

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
        # self.toggle_dark_mode(False)
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

        '''CREATE LOAD PDF BUTTON'''

        # Create a button to load and extract highlights from a PDF
        self.load_pdf_button = QPushButton('Import Highlighted PDF')
        self.load_pdf_button.setStyleSheet("QPushButton {padding: 8px; }")
        self.load_pdf_button.clicked.connect(self.gui_load_highlighted_pdf)

        # '''CREATE DARK MODE TOGGLE'''
        #
        # self.dark_mode_switch = QCheckBox("Dark Mode", self)
        # self.dark_mode_switch.stateChanged.connect(self.toggle_dark_mode)

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

        self.footer_text = QLabel(f"{meta.copyright_info}\nBuild: {meta.build_number}")

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
        # top_hbox.addWidget(self.dark_mode_switch)
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

    # def toggle_dark_mode(self, enabled):
    #     if enabled:
    #         self.setStyleSheet(dark_stylesheet)
    #     else:
    #         self.setStyleSheet(light_stylesheet)  # Set to default or light mode stylesheet

    def gui_load_highlighted_pdf(self):
        # Prompt the user to select a PDF file
        pdf_path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF files (*.pdf);;All files (*)")
        gb.pdf_path = pdf_path
        self.gui_add_input_text()
        # return pdf_path

    def aggregate_processed_pdf_text(self, pdf_path):
        if pdf_path:
            # Call the function to extract highlighted text and populate the left text field
            result = pd.extract_highlighted_text_with_coordinates(gb.pdf_path)
            highlighted_text = result[0]
            citations = result[1]
            return highlighted_text
        else:
            return self.text_box_left.toPlainText()

    def gui_add_input_text(self):
        self.text_box_left.setPlainText(self.aggregate_processed_pdf_text(gb.pdf_path))


    @pyqtSlot()
    def hide_objections_change(self):
        """ Fill in """
        self.on_text_change()

    def hide_depo_name_checkbox_change(self):
        self.on_text_change()

    def on_text_change(self):
        """ Trigger text reprocessing when the left text field changes either by paste or import """
        the_text = self.aggregate_processed_pdf_text(gb.pdf_path)
        output_powerpoint = fp.prepare_text_for_powerpoint(the_text)
        output_oncue = fo.prepare_text_for_oncue(the_text)
        self.text_box_top_right.setPlainText(output_powerpoint)
        self.text_box_bottom_right.setPlainText(output_oncue)

    def on_name_change(self):
        # Trigger text reprocessing when the name field changes
        self.on_text_change()

    @pyqtSlot()
    def activate_clear_button(self):
        self.text_box_left.clear()
        self.text_box_top_right.clear()
        self.text_box_bottom_right.clear()

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
