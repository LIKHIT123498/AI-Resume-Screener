import io
from pypdf import PdfReader
import logging
from docx import Document
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Extracts text from uploaded PDF or DOCX bytes based on file extension.
    """
    text = ""
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_content))
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    elif filename.lower().endswith(".docx"):
        doc = Document(io.BytesIO(file_content))
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    else:
        raise ValueError("Unsupported file format. Only PDF and DOCX are allowed.")
    
    return text