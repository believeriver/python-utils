from rest_framework.permissions import BasePermission

from . import views

class CustomPermission(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    # def has_object_permission(self, request, view, obj):
    #     # Read permissions are allowed to any request,
    #     # so we'll always allow GET, HEAD or OPTIONS requests.
    #     if request.method in ('GET', 'HEAD', 'OPTIONS'):
    #         return True
    #
    #     # Write permissions are only allowed to the owner of the snippet.
    #     return obj.owner == request.user

    def has_permission(self, request, view):
        print(request.method)
        print(view)
        print(request.user)
        print(request.META['REMOTE_ADDR'])
        print(request.user.is_authenticated)
        if isinstance(view, views.ItemModelDetailView):
            return True
        if request.method == "GET":
            return True
        return False