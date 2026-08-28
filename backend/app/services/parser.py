import io
import zipfile
from xml.etree import ElementTree
from pypdf import PdfReader

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Robustly extracts text from PDF or DOCX bytes. 
    Uses direct XML tree traversal for DOCX to safely bypass images, floating shapes, and tables.
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
            # DOCX files are zip archives containing XML components
            with zipfile.ZipFile(io.BytesIO(file_content)) as docx_zip:
                # Read the main document XML content
                xml_content = docx_zip.read('word/document.xml')
                tree = ElementTree.fromstring(xml_content)
                
                # Word XML namespace for text nodes
                WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
                TEXT_TAG = WORD_NAMESPACE + 't'
                
                # Extract text from all text elements across paragraphs, tables, and shapes
                paragraphs = []
                for elem in tree.iter():
                    if elem.tag == TEXT_TAG and elem.text:
                        paragraphs.append(elem.text)
                
                text = " ".join(paragraphs)
        else:
            raise ValueError("Unsupported file format.")
            
    except Exception as e:
        print(f"Error parsing file {filename}: {e}")
        return ""
    
    return text.strip()