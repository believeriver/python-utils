from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class ItemView(APIView):
    def get(self, request):
        data = {
            "items": ["item1", "item2", "item3"]
        }
        return Response(data)

    def post(self, request):
        item = request.data.get('item')
        return Response(
            {"message": f"Item '{item}' created successfully."},
            status=status.HTTP_201_CREATED)

    def put(self, request):
        item = request.data.get('item')
        return Response(
            {"message": f"Item '{item}' updated successfully."},
            status=status.HTTP_200_OK)

    def delete(self, request):
        item = request.data.get('item')
        return Response(
            {"message": f"Item '{item}' deleted successfully."},
            status=status.HTTP_200_OK)