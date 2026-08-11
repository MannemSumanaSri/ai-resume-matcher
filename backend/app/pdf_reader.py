from io import BytesIO
from pypdf import PdfReader


def extract_text_from_pdf(file):
    """
    Extract text from an uploaded PDF.
    Accepts either raw bytes or a file-like object.
    """

    if isinstance(file, bytes):
        file = BytesIO(file)

    reader = PdfReader(file)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text