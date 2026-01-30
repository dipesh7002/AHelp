from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from helper.models import (
    AssignmentHelper,
    Subject,
    Education
)
from helper.serializers import (
    AssignmentHelperSerializer,
    SubjectSerializer,
    EducationSerializer
)
from authentication.permissions import IsSuperUser, IsAssignmentHelper
from authentication.models import CommonUser


class AssignmentHelperViewSet(ModelViewSet):
    queryset = AssignmentHelper.objects.all()
    serializer_class = AssignmentHelperSerializer
    
    def get_permissions(self):
        """
        Allow anyone to view (for writers page),
        but require authentication for other operations.
        SuperUser can do everything.
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action in ['destroy']:
            return [IsAuthenticated(), IsSuperUser()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """
        Filter queryset based on user role.
        CommonUsers see all helpers.
        Helpers see themselves.
        SuperUsers see all.
        """
        user = self.request.user
        
        if not user.is_authenticated:
            # Public view - show all verified helpers
            return AssignmentHelper.objects.filter(
                user__email_verified=True,
                user__role=CommonUser.Role.HELPER
            )
        
        if user.role == CommonUser.Role.ADMIN:
            return AssignmentHelper.objects.all()
        
        if user.role == CommonUser.Role.HELPER:
            # Helpers see themselves
            try:
                return AssignmentHelper.objects.filter(user=user)
            except:
                return AssignmentHelper.objects.none()
        
        # CommonUsers see all verified helpers
        return AssignmentHelper.objects.filter(
            user__email_verified=True,
            user__role=CommonUser.Role.HELPER
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSuperUser])
    def assign_user(self, request, pk=None):
        """
        Assign a CommonUser to this AssignmentHelper.
        Only SuperUser can do this.
        """
        helper = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = CommonUser.objects.get(id=user_id, role=CommonUser.Role.COMMON)
        except CommonUser.DoesNotExist:
            return Response(
                {'error': 'CommonUser not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        helper.assigned_users.add(user)
        return Response({
            'message': f'User {user.email} assigned to helper {helper.user.email}'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSuperUser])
    def unassign_user(self, request, pk=None):
        """Unassign a user from this helper"""
        helper = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = CommonUser.objects.get(id=user_id)
        except CommonUser.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        helper.assigned_users.remove(user)
        return Response({
            'message': f'User {user.email} unassigned from helper {helper.user.email}'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def assigned_users(self, request, pk=None):
        """Get all users assigned to this helper"""
        helper = self.get_object()
        user = request.user
        
        # Only helper themselves or SuperUser can see assigned users
        if user.role != CommonUser.Role.ADMIN and helper.user != user:
            return Response(
                {'error': 'You do not have permission to view this'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        assigned = helper.assigned_users.all()
        from authentication.serializers import CommonUserSerializer
        serializer = CommonUserSerializer(assigned, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAssignmentHelper])
    def update_availability(self, request, pk=None):
        """Update helper availability"""
        helper = self.get_object()
        user = request.user
        
        # Only helper themselves can update availability
        if helper.user != user:
            return Response(
                {'error': 'You can only update your own availability'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        is_available = request.data.get('is_available', True)
        helper.is_available = is_available
        helper.save()
        
        return Response({
            'message': f'Availability updated to {is_available}',
            'is_available': helper.is_available
        })


class SubjectViewSet(ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [AllowAny]


class EducationViewSet(ModelViewSet):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
    permission_classes = [AllowAny]