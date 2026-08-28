import io
from pypdf import PdfReader
from docx import Document

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Extracts text from uploaded PDF or DOCX bytes safely.
    """
    text = ""
    try:
        if filename.lower().endswith(".pdf"):
            reader = PdfReader(io.BytesIO(file_content))
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
                    
        elif filename.lower().endswith(".docx"):
            doc = Document(io.BytesIO(file_content))
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text += paragraph.text + "\n"
            # Also extract text from tables if any exist in the docx
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text:
                            text += cell.text + "\n"
        else:
            raise ValueError("Unsupported file format.")
    except Exception as e:
        print(f"Error parsing file {filename}: {e}")
        return ""
    
    return text.strip()