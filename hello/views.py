from django.http import HttpResponse


def hello_world(request):
    """Simple view that returns Hello World"""
    return HttpResponse("Hello World!")

