from celery import shared_task

from .models import GenerationRequest
from .services import execute_generation

@shared_task
def process_generation_request(request_id: str):
    gen_request = GenerationRequest.objects.get(pk=request_id)
    execute_generation(gen_request)
    return str(gen_request.id)
