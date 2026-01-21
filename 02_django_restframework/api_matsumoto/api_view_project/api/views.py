from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import ItemSerializer
from .models import Item

class ItemView(APIView):

    serializer_class = ItemSerializer

    def get(self, request):
        # data = {
        #     "items": ["item1", "item2", "item3"]
        # }
        item = Item.objects.all()
        serializer = self.serializer_class(item, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK)

    def post(self, request):
        item = request.data.get('item')
        serializer = self.serializer_class(data=request.data)
        # print(serializer)
        # print(serializer.is_valid(raise_exception=True))
        # print(serializer.errors)
        if serializer.is_valid(raise_exception=True):
            # save data
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED)

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