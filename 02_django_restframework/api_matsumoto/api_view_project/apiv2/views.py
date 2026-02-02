from django.contrib.auth import get_user_model, login
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework import permissions

from .serializers import (
    ItemModelSerializer, UserModelSerializer, ProductModelSerializer, LoginSerializer)
from .permissions import CustomPermission
from api.models import Item, Product

"""
ModelViewを使ったAPIViewの実装例
create, updateの実装が必要なくなる
"""

class BaseListView(APIView):
    def get(self, request):
        objects = self.model.objects.all()
        serializer = self.serializer_class(objects, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK)

    def post(self, request):
        # item = request.data.get('item')
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            # save data
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED)

        return Response(
            {"message": "created successfully."},
            status=status.HTTP_201_CREATED)



class ItemModelView(BaseListView):
    """
    AllowAny: 認証不要
    IsAuthenticated: 認証済みユーザーのみ
    IsAdminUser: 管理者ユーザーのみ
    IsAuthenticatedOrReadOnly: 認証済みユーザーは読み書き可能、未認証ユーザーは読み取り専用
    などがある
    user: admin
    mail: admin@mail.com
    pass: admin
    """
    # permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    permission_classes = [CustomPermission]
    serializer_class = ItemModelSerializer
    model = Item


class ProductModelView(BaseListView):
    serializer_class = ProductModelSerializer
    model = Product


class UserModelView(BaseListView):
    serializer_class = UserModelSerializer
    model = get_user_model()


class BaseDetailView(APIView):
    def get(self, request, pk):
        try:
            objects = self.model.objects.get(pk=pk)
        except Item.DoesNotExist:
            return Response(
                {"error": "Item not found."},
                status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(objects)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK)

    def put(self, request, pk):
        try:
            objects = self.model.objects.get(pk=pk)
        except Item.DoesNotExist:
            return Response(
                {"error": "Item not found."},
                status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(objects, data=request.data)
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
            objects = self.model.objects.get(pk=pk)
        except Item.DoesNotExist:
            return Response(
                {"error": "Item not found."},
                status=status.HTTP_404_NOT_FOUND)

        objects.delete()
        return Response(
            {"message": "Item deleted successfully."},
            status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, pk):
        objects = self.model.objects.get(pk=pk)
        serializer = self.serializer_class(objects, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK)
        return Response(
            {"error": "Failed to update item."},
            status=status.HTTP_400_BAD_REQUEST)


class ItemModelDetailView(BaseDetailView):

    serializer_class = ItemModelSerializer
    permission_classes = [CustomPermission]
    model = Item


class ProductModelDetailView(BaseDetailView):
    serializer_class = ProductModelSerializer
    model = Product


class UserModelDetailView(BaseDetailView):
    serializer_class = UserModelSerializer
    model = get_user_model()


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=self.request.data, context={'request': self.request})
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user']
            login(request, user)
            return Response(
                {
                    "message": "Login successful.",
                    "user_id": user.id,
                    "username": user.username,
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {"error": "Invalid credentials."},
            status=status.HTTP_400_BAD_REQUEST
        )



