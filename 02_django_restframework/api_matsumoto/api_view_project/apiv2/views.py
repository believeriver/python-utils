from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import ItemModelSerializer
from api.models import Item

"""
ModelViewを使ったAPIViewの実装例
create, updateの実装が必要なくなる
"""

class ItemModelView(APIView):

    serializer_class = ItemModelSerializer

    def get(self, request):
        item = Item.objects.all()
        serializer = self.serializer_class(item, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK)

    def post(self, request):
        item = request.data.get('item')
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            # save data
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED)

        return Response(
            {"message": f"Item '{item}' created successfully."},
            status=status.HTTP_201_CREATED)


class ItemModelDetailView(APIView):

    serializer_class = ItemModelSerializer

    def get(self, request, pk):
        try:
            item = Item.objects.get(pk=pk)
        except Item.DoesNotExist:
            return Response(
                {"error": "Item not found."},
                status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(item)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK)

    def put(self, request, pk):
        try:
            item = Item.objects.get(pk=pk)
        except Item.DoesNotExist:
            return Response(
                {"error": "Item not found."},
                status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(item, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK)

        return Response(
            {"error": "Failed to update item."},
            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            item = Item.objects.get(pk=pk)
        except Item.DoesNotExist:
            return Response(
                {"error": "Item not found."},
                status=status.HTTP_404_NOT_FOUND)

        item.delete()
        return Response(
            {"message": "Item deleted successfully."},
            status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, pk):
        item = Item.objects.get(pk=pk)
        serializer = self.serializer_class(item, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK)

