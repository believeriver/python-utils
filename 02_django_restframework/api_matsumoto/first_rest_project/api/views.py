from django.shortcuts import render
from django.http import HttpResponse, JsonResponse


def index(request):
    return HttpResponse("<h1>Welcome to the First REST Project!</h1>")


def json_example(request):
    data = {
        "message": "Hello, this is a JSON response!",
        "status": "success"
    }
    return JsonResponse(data)

