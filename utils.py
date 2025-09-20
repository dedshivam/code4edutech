import re
import string
import unicodedata
from datetime import datetime
import streamlit as st

def clean_filename(filename):
    """Clean filename for safe storage"""
    # Remove extension for processing
    name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
    
    # Remove special characters and normalize
    name = re.sub(r'[^\w\s-]', '', name.strip())
    name = re.sub(r'[-\s]+', '_', name)
    
    # Add timestamp to make unique
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    return f"{name}_{timestamp}.{ext}" if ext else f"{name}_{timestamp}"

def normalize_text(text):
    """Normalize text for better processing"""
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep important punctuation
    text = re.sub(r'[^\w\s.,;:()\-]', ' ', text)
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_keywords(text, min_length=3):
    """Extract keywords from text"""
    if not text:
        return []
    
    # Normalize text
    text = normalize_text(text)
    
    # Split into words
    words = text.split()
    
    # Filter keywords
    keywords = []
    for word in words:
        if (len(word) >= min_length and 
            word not in string.punctuation and
            not word.isdigit()):
            keywords.append(word)
    
    return list(set(keywords))

def calculate_text_similarity(text1, text2):
    """Calculate simple text similarity using Jaccard similarity"""
    if not text1 or not text2:
        return 0.0
    
    # Get keywords from both texts
    keywords1 = set(extract_keywords(text1))
    keywords2 = set(extract_keywords(text2))
    
    if not keywords1 or not keywords2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(keywords1.intersection(keywords2))
    union = len(keywords1.union(keywords2))
    
    return intersection / union if union > 0 else 0.0

def format_date(date_string):
    """Format date string for display"""
    try:
        if isinstance(date_string, str):
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        else:
            dt = date_string
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return str(date_string)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_input(text, max_length=None):
    """Sanitize user input"""
    if not text:
        return ""
    
    # Remove potentially harmful characters
    text = re.sub(r'[<>"\']', '', text)
    
    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()

def create_download_link(data, filename, mime_type="text/plain"):
    """Create a download link for data"""
    return st.download_button(
        label=f"Download {filename}",
        data=data,
        file_name=filename,
        mime=mime_type
    )

def format_score(score, precision=1):
    """Format score for display"""
    try:
        return f"{float(score):.{precision}f}"
    except:
        return "N/A"

def get_verdict_color(verdict):
    """Get color for verdict display"""
    colors = {
        'High': '#28a745',    # Green
        'Medium': '#ffc107',  # Yellow
        'Low': '#dc3545',     # Red
    }
    return colors.get(verdict, '#6c757d')  # Default gray

def truncate_text(text, max_length=100):
    """Truncate text with ellipsis"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def parse_json_safely(json_string):
    """Safely parse JSON string"""
    try:
        import json
        return json.loads(json_string) if json_string else {}
    except:
        return {}

def format_list_for_display(items, separator=", "):
    """Format list for display"""
    if not items:
        return "None"
    
    if isinstance(items, str):
        items = parse_json_safely(items)
    
    if isinstance(items, list):
        return separator.join(str(item) for item in items)
    
    return str(items)

def highlight_keywords(text, keywords, highlight_color="#ffff00"):
    """Highlight keywords in text for display"""
    if not text or not keywords:
        return text
    
    highlighted_text = text
    for keyword in keywords:
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        highlighted_text = pattern.sub(
            f'<mark style="background-color: {highlight_color};">{keyword}</mark>',
            highlighted_text
        )
    
    return highlighted_text

def calculate_completion_percentage(completed_items, total_items):
    """Calculate completion percentage"""
    if total_items == 0:
        return 0
    return (completed_items / total_items) * 100

def get_file_size_mb(file_bytes):
    """Get file size in MB"""
    return len(file_bytes) / (1024 * 1024)

def validate_file_size(file_bytes, max_size_mb=10):
    """Validate file size"""
    size_mb = get_file_size_mb(file_bytes)
    return size_mb <= max_size_mb, size_mb

def create_progress_indicator(current, total, label="Progress"):
    """Create a progress indicator"""
    if total == 0:
        return st.write(f"{label}: No items to process")
    
    percentage = (current / total) * 100
    return st.progress(percentage / 100)
