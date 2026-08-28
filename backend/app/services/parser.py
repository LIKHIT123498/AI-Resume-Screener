import io
from pypdf import PdfReader
from docx import Document

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Robustly extracts text from PDF or DOCX bytes, safely ignoring embedded images.
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
            
            # Extract text paragraph by paragraph, ignoring embedded drawing layers/photos
            for paragraph in doc.paragraphs:
                para_text = "".join([run.text for run in paragraph.runs if run.text])
                if not para_text.strip():
                    para_text = paragraph.text
                if para_text.strip():
                    text += para_text + "\n"
                    
            # Extract text from tables safely
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        cell_text = "".join([p.text for p in cell.paragraphs])
                        if cell_text.strip():
                            text += cell_text + "\n"
        else:
            raise ValueError("Unsupported file format.")
            
    except Exception as e:
        print(f"Error parsing file {filename}: {e}")
        return ""
    
    return text.strip()