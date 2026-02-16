# Third-party modules
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrReadOnly(BasePermission):
    """
    Custom permission class:
    - Anyone can read (GET, HEAD, OPTIONS)
    - Only authenticated users can create
    - Only the author can edit or delete their own content
    """

    def has_permission(self, request, view):
        """
        Allow read access to anyone.
        Require authentication for write operations.
        """
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Allow read access to anyone.
        Only allow authors to edit/delete their own content.
        """
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user
