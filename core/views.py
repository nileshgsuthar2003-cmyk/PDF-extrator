import threading
import json
import os
from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .tasks import process_pdf
from .mongodb import get_db

def index(request):
    return render(request, 'core/index.html')

@csrf_exempt
def upload_pdf(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        file = request.FILES['pdf_file']

        # Validate file type
        if not file.name.lower().endswith('.pdf'):
            return JsonResponse({"error": "Only PDF files are allowed"}, status=400)

        # Validate file size (max 50MB)
        if file.size > 50 * 1024 * 1024:
            return JsonResponse({"error": "File size must be less than 50MB"}, status=400)

        file_path = default_storage.save(file.name, file)
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)

        # Start background thread for processing
        thread = threading.Thread(target=process_pdf, args=(full_path, file.name))
        thread.start()

        return JsonResponse({
            "status": "processing",
            "message": f"PDF '{file.name}' uploaded successfully. Processing in background with Nougat OCR."
        })
    return JsonResponse({"error": "Invalid request"}, status=400)

def get_random_question(request):
    db = get_db()
    collection = db['questions']
    pipeline = [{"$sample": {"size": 1}}]
    result = list(collection.aggregate(pipeline))
    if result:
        return JsonResponse({"question": result[0]['content']})
    return JsonResponse({"question": "No questions available"})
