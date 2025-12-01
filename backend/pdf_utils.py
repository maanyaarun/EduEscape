"""
This file extracts text from PDF files and detects topic headings.
It's like a helper that reads the PDF for us.
"""

import PyPDF2
import re


def extract_text_from_pdf(pdf_path):
    """
    Reads a PDF file and extracts all the text from it.
    
    Args:
        pdf_path: The location of the PDF file on your computer
        
    Returns:
        A string containing all the text from the PDF
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            # Go through each page and extract text
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""
    
    return text


def detect_topics(text):
    """
    Finds topic headings in the text (like chapter titles or section headers).
    This uses simple rules to find lines that look like headings.
    
    Args:
        text: The full text from the PDF
        
    Returns:
        A list of dictionaries, each containing a topic title and its content
    """
    # Split text into lines
    lines = text.split('\n')
    topics = []
    current_topic = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Check if this line looks like a heading
        # (short, starts with capital, might have numbers, ends without punctuation)
        is_heading = (
            len(line) < 100 and  # Headings are usually short
            line[0].isupper() and  # Starts with capital letter
            not line.endswith('.') and  # Doesn't end with period
            not line.endswith(',')  # Doesn't end with comma
        )
        
        # Also check for numbered headings like "1. Introduction" or "Chapter 1"
        if re.match(r'^[\d\.]+\s+[A-Z]', line) or re.match(r'^Chapter\s+\d+', line, re.IGNORECASE):
            is_heading = True
        
        if is_heading and len(line.split()) <= 10:  # Headings have max 10 words
            # Save previous topic if exists
            if current_topic:
                topics.append({
                    'title': current_topic,
                    'content': '\n'.join(current_content)
                })
            
            # Start new topic
            current_topic = line
            current_content = []
        else:
            # Add line to current topic content
            if current_topic:
                current_content.append(line)
    
    # Don't forget the last topic!
    if current_topic:
        topics.append({
            'title': current_topic,
            'content': '\n'.join(current_content)
        })
    
    # If no topics were detected, create one big topic
    if not topics:
        topics.append({
            'title': 'Main Content',
            'content': text
        })
    
    return topics