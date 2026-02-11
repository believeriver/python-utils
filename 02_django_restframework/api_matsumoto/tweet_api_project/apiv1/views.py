from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login

from .serializers import UserRegisterSerializer, UserLoginSerializer, TweetSerializer

import os
import sys

dir_path = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
print({'Project path': dir_path})
sys.path.insert(0, dir_path)

from  tweet_api_project.models import Tweet


class UserRegisterView(APIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            return Response(
                {
                    "message": "User registered successfully.",
                    "user": UserRegisterSerializer(user).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user']
            login(request, user)
            return Response(
                {
                    "message": "User logged in successfully.",
                    "user": UserRegisterSerializer(user).data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TweetListView(APIView):
    serializer_class = TweetSerializer
    # permission_classes = [AllowAny]

    def get(self, request):
        tweets = Tweet.objects.all().order_by('-created_at')
        serializer = self.serializer_class(tweets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'user': request.user})
        if serializer.is_valid(raise_exception=True):
            tweet = serializer.save()
            return Response(
                {
                    "message": "Tweet created successfully.",
                    "tweet": self.serializer_class(tweet).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
