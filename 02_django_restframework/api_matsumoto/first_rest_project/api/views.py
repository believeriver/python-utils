from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from datetime import datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response

def index(request):
    return HttpResponse("<h1>Welcome to the First REST Project!</h1>")


def json_example(request):
    data = {
        "message": "Hello, this is a JSON response!",
        "status": "success"
    }
    return JsonResponse(data)


@api_view(['GET'])
def country_datetime(request):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "country": "Japan",
        "current_datetime": current_time
    }
    return Response(data)


