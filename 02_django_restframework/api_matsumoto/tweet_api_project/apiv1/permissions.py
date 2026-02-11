from rest_framework import permissions
from rest_framework.permissions import BasePermission


class TweetUpdateDeletePermission(BasePermission):
    """
    Custom permission to only allow owners of a tweet to edit or delete it.
    """

    def has_object_permission(self, request, view, obj):
        # Allow read permissions for any request
        if request.method == 'POST':
            return False
        elif request.method in ('PUT', 'DELETE'):
            # Write permissions are only allowed to the owner of the tweet
            return obj.user == request.user
        return True
