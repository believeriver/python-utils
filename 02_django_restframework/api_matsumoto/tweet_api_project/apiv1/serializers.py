from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers

import os
import sys

dir_path = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
print({'Project path': dir_path})
sys.path.insert(0, dir_path)

from  tweet_api_project.models import Tweet# Replace with your Tweet model


class UserRegisterSerializer(serializers.ModelSerializer):
    # password = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = get_user_model().objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password)
            if not user:
                raise serializers.ValidationError("Invalid username or password.")
        else:
            raise serializers.ValidationError("Both username and password are required.")

        data['user'] = user
        return data


class TweetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tweet
        fields = ('id', 'content', 'created_at')
        read_only_fields = ('id', 'created_at',)

    def create(self, validated_data):
        tweet = Tweet.objects.create(
            content=validated_data['content'],
            user=self.context.get('user'),
        )
        return tweet
