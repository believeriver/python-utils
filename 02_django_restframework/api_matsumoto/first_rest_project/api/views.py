from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from datetime import datetime, timezone
import pytz
from pytz.exceptions import UnknownTimeZoneError

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

def index(request):
    return HttpResponse("<h1>Welcome to the First REST Project!</h1>")


def json_example(request):
    data = {
        "message": "Hello, this is a JSON response!",
        "status": "success"
    }
    return JsonResponse(data)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def country_datetime(request):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    request_data = request.data.get('timezone')
    print(request.method)
    try:
        tz = pytz.timezone(request_data)
    except UnknownTimeZoneError:
        return Response({
            "error": "Unknown timezone"
        }, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'POST':
        utc_datetime = datetime.now(timezone.utc)
        return Response({
            "country": request_data,
            "current_datetime_in_requested_timezone": utc_datetime.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
        })
    elif request.method == 'PUT':
        print('PUT method called')
    elif request.method == 'DELETE':
        print('DELETE method called')

    request_param = request.query_params.get('timezone')
    print(request_param)
    data = {
        "country": "Japan",
        "current_datetime": current_time
    }
    return Response(data)


