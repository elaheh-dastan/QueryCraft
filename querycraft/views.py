import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .services import SQLAgent


def query_form(request):
    """Main query form page"""
    return render(request, "querycraft/query_form.html")


def api_client(request):
    """Simple API client page"""
    return render(request, "querycraft/api_client.html")


@csrf_exempt
@require_http_methods(["POST"])
def process_query(request):
    """Process question through LangGraph workflow and return result"""
    try:
        data = json.loads(request.body)
        question = data.get("question", "").strip()

        if not question:
            return JsonResponse({"success": False, "error": "Please enter a question"})

        # Use LangGraph workflow to process question
        agent = SQLAgent()
        result = agent.process_question(question)

        # Pydantic models have built-in JSON serialization
        return JsonResponse(result.model_dump())

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Error processing request"})
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Error: {e!s}"})
