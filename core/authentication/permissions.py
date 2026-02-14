from rest_framework import permissions
from authentication.models import CommonUser


class IsCommonUser(permissions.BasePermission):
    """Permission check for CommonUser role"""
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == CommonUser.Role.COMMON
        )


class IsAssignmentHelper(permissions.BasePermission):
    """Permission check for AssignmentHelper role"""
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == CommonUser.Role.HELPER and
            request.user.email_verified
        )


class IsSuperUser(permissions.BasePermission):
    """Permission check for SuperUser role"""
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == CommonUser.Role.ADMIN
        )


class IsHelperOrSuperUser(permissions.BasePermission):
    """Permission check for AssignmentHelper or SuperUser"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == CommonUser.Role.ADMIN:
            return True
        return (
            request.user.role == CommonUser.Role.HELPER and
            request.user.email_verified
        )


class IsSelfOrAdmin(permissions.BasePermission):
    """Permission to allow users to access/modify their own user record or admins."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == CommonUser.Role.ADMIN or obj == request.user


class IsHelperSelfOrAdmin(permissions.BasePermission):
    """Permission to allow helpers to access/modify their own helper profile or admins."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == CommonUser.Role.ADMIN or getattr(obj, "user", None) == request.user


class CanChatWithUser(permissions.BasePermission):
    """
    Permission to check if user can chat with another user.
    Rules:
    - SuperUser can chat with anyone
    - AssignmentHelper can chat with assigned users
    - CommonUser can chat with assigned helpers
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if not user or not user.is_authenticated:
            return False
        
        # SuperUser can chat with anyone
        if user.role == CommonUser.Role.ADMIN:
            return True
        
        # Get the other participant
        if hasattr(obj, 'get_other_participant'):
            other_user = obj.get_other_participant(user)
        elif hasattr(obj, 'participant1') and hasattr(obj, 'participant2'):
            if obj.participant1 == user:
                other_user = obj.participant2
            else:
                other_user = obj.participant1
        else:
            return False
        
        # AssignmentHelper can chat with assigned users
        if user.role == CommonUser.Role.HELPER and user.email_verified:
            try:
                helper = user.assignmenthelper
                return other_user in helper.assigned_users.all()
            except:
                return False
        
        # CommonUser can chat with assigned helpers
        if user.role == CommonUser.Role.COMMON:
            try:
                # Check if other_user is a helper and user is assigned to them
                helper = other_user.assignmenthelper
                return user in helper.assigned_users.all()
            except:
                return False
        
        return False


class CanViewConversation(permissions.BasePermission):
    """Permission to view a conversation"""
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if not user or not user.is_authenticated:
            return False
        
        # SuperUser can view any conversation
        if user.role == CommonUser.Role.ADMIN:
            return True
        
        # User must be a participant
        if hasattr(obj, 'has_participant'):
            return obj.has_participant(user)
        
        return False
