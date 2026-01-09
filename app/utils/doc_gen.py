import os
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime

# Ensure a directory exists for temporary files
os.makedirs("temp_downloads", exist_ok=True)

def create_docx(text, filename="digitized_note"):
    path = f"temp_downloads/{filename}_{datetime.now().strftime('%H%M%S')}.docx"
    doc = Document()
    doc.add_heading('Digitized Study Notes', 0)
    doc.add_paragraph(text)
    doc.save(path)
    return path

def create_pdf(text, filename="digitized_note"):
    path = f"temp_downloads/{filename}_{datetime.now().strftime('%H%M%S')}.pdf"
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    
    text_obj = c.beginText(40, height - 40)
    text_obj.setFont("Helvetica", 12)
    
    # Wrap text manually
    lines = text.split('\n')
    for line in lines:
        text_obj.textLine(line)
        
    c.drawText(text_obj)
    c.showPage()
    c.save()
    return path