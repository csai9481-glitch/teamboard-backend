from rest_framework.permissions import BasePermission
from .models import Company


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.company.role == Company.Role.ADMIN