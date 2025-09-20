import fitz  # PyMuPDF
import docx
import re
import streamlit as st
from io import BytesIO

def extract_text_from_pdf(file_bytes):
    """Extract text from PDF file"""
    try:
        # Open PDF from bytes
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        
        pdf_document.close()
        return clean_text(text)
    
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return ""

def extract_text_from_docx(file_bytes):
    """Extract text from DOCX file"""
    try:
        # Open DOCX from bytes
        doc = docx.Document(BytesIO(file_bytes))
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return clean_text(text)
    
    except Exception as e:
        st.error(f"Error extracting text from DOCX: {str(e)}")
        return ""

def clean_text(text):
    """Clean and normalize extracted text"""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Remove common PDF artifacts
    text = re.sub(r'[^\w\s\-.,;:()\[\]@+/&%]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text

def extract_contact_info(text):
    """Extract contact information from text"""
    contact_info = {}
    
    # Email extraction
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    contact_info['email'] = emails[0] if emails else ""
    
    # Phone extraction
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phones = re.findall(phone_pattern, text)
    contact_info['phone'] = phones[0] if phones else ""
    
    # Name extraction (basic - first few words before common resume sections)
    lines = text.split('\n')
    name = ""
    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        if line and len(line.split()) <= 4 and not any(keyword in line.lower() for keyword in ['resume', 'cv', 'curriculum', 'vitae', 'email', 'phone', '@']):
            if not re.search(r'\d', line):  # No numbers in name
                name = line
                break
    
    contact_info['name'] = name
    
    return contact_info

def extract_sections(text):
    """Extract different sections from resume text"""
    sections = {
        'experience': '',
        'education': '',
        'skills': '',
        'projects': '',
        'certifications': ''
    }
    
    # Common section headers
    section_patterns = {
        'experience': r'(experience|work\s+experience|professional\s+experience|employment|career)',
        'education': r'(education|academic|qualification|degree)',
        'skills': r'(skills|technical\s+skills|competencies|expertise)',
        'projects': r'(projects|personal\s+projects|portfolio)',
        'certifications': r'(certifications?|certificates?|credentials)'
    }
    
    text_lower = text.lower()
    
    for section_name, pattern in section_patterns.items():
        # Find section start
        matches = list(re.finditer(pattern, text_lower))
        if matches:
            start_pos = matches[0].start()
            
            # Find next section or end of text
            end_pos = len(text)
            for other_pattern in section_patterns.values():
                if other_pattern != pattern:
                    other_matches = list(re.finditer(other_pattern, text_lower[start_pos + 50:]))
                    if other_matches:
                        potential_end = start_pos + 50 + other_matches[0].start()
                        if potential_end < end_pos:
                            end_pos = potential_end
            
            sections[section_name] = text[start_pos:end_pos].strip()
    
    return sections

def process_uploaded_file(uploaded_file):
    """Process uploaded resume file and extract all information"""
    if uploaded_file is None:
        return None
    
    file_bytes = uploaded_file.read()
    filename = uploaded_file.name
    file_extension = filename.lower().split('.')[-1]
    
    # Extract text based on file type
    if file_extension == 'pdf':
        extracted_text = extract_text_from_pdf(file_bytes)
    elif file_extension in ['docx', 'doc']:
        extracted_text = extract_text_from_docx(file_bytes)
    else:
        st.error("Unsupported file format. Please upload PDF or DOCX files.")
        return None
    
    if not extracted_text:
        st.error("Could not extract text from the file. Please check the file format.")
        return None
    
    # Extract contact information
    contact_info = extract_contact_info(extracted_text)
    
    # Extract sections
    sections = extract_sections(extracted_text)
    
    return {
        'filename': filename,
        'extracted_text': extracted_text,
        'contact_info': contact_info,
        'sections': sections
    }
