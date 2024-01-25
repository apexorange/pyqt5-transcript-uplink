import re
import sys
import globals as gb
import fitz  # PyMuPDF


def extract_highlighted_text_with_coordinates(pdf_path: str) -> tuple:
    """
    Extracts highlighted text from a PDF file and returns it along with the page numbers where it was found.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        tuple: A tuple containing the highlighted text and a list of the page numbers where it was found.

    Raises:
        ValueError: If the PDF file cannot be opened or read.
    """
    # Open the PDF file
    try:
        doc = fitz.open(gb.pdf_path)
    except OSError as err:
        raise ValueError(f"Failed to open PDF file: {err}")

    # Extract the highlighted text and page numbers
    highlighted_texts = []
    citations = []
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
                    highlighted_text: str
                    result = process_pdf_highlighted_text(highlighted_text, page_num)
                    line_range_info = result[0]
                    pdf_highlighted_text = result[1]
                    highlighted_texts.append(f"\n--- Page {line_range_info}: \n{pdf_highlighted_text} "
                                             f"---\n")
                    citations.append(line_range_info)

    # Close the PDF file
    doc.close()

    return "".join(highlighted_texts), citations


def process_pdf_highlighted_text(text: str, page_num: int) -> tuple:
    """
    Processes the highlighted text extracted from a PDF file and returns it with the page number where it was found.

    Args:
        text (str): The highlighted text.
        page_num (int): The page number where the highlighted text was found.

    Returns:
        tuple: A tuple containing the processed highlighted text and the page number where it was found.
    """
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

