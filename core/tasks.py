import subprocess
import re
import os
from django.conf import settings
from .mongodb import get_db

def process_pdf(file_path, filename):
    # Create nougat_output directory inside MEDIA_ROOT
    output_dir = os.path.join(settings.MEDIA_ROOT, 'nougat_output')
    os.makedirs(output_dir, exist_ok=True)

    # Run Nougat OCR
    command = ['nougat', file_path, '-o', output_dir, '--markdown']
    subprocess.run(command, check=True)

    # Read the generated .mmd file
    mmd_file = os.path.join(output_dir, os.path.basename(file_path).replace('.pdf', '.mmd'))
    with open(mmd_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into questions using regex (assuming questions start with number like "1.", "2.")
    questions = re.split(r'(?=\d+\.)', content.strip())
    questions = [q.strip() for q in questions if q.strip()]

    # Insert into MongoDB
    db = get_db()
    collection = db['questions']
    for question in questions:
        collection.insert_one({"content": question, "source": filename})
