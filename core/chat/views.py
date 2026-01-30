from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from chat.models import Room, Message, Conversation
from chat.serializers import (
    RoomSerializer,
    MessageSerializer,
    ConversationSerializer
)
from authentication.permissions import (
    CanChatWithUser,
    CanViewConversation,
    IsSuperUser
)
from authentication.models import CommonUser


class ConversationViewSet(ModelViewSet):
    """
    ViewSet for managing conversations.
    Users can only see conversations they're part of.
    SuperUsers can see all conversations.
    """
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated, CanViewConversation]
    
    def get_queryset(self):
        user = self.request.user
        
        # SuperUser can see all conversations
        if user.role == CommonUser.Role.ADMIN:
            return Conversation.objects.all()
        
        # Regular users can only see their own conversations
        return Conversation.objects.filter(
            participant1=user
        ) | Conversation.objects.filter(
            participant2=user
        )
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=False, methods=['get'])
    def my_conversations(self, request):
        """Get all conversations for the current user"""
        user = request.user
        conversations = self.get_queryset()
        serializer = self.get_serializer(conversations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def get_or_create(self, request):
        """
        Get or create a conversation with another user.
        Validates permissions before creating.
        """
        other_user_id = request.data.get('other_user_id')
        
        if not other_user_id:
            return Response(
                {'error': 'other_user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            other_user = CommonUser.objects.get(id=other_user_id)
        except CommonUser.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        user = request.user
        
        # SuperUser can chat with anyone
        if user.role == CommonUser.Role.ADMIN:
            pass  # Allow
        # Check if users can chat (assignment relationship)
        elif user.role == CommonUser.Role.HELPER:
            try:
                helper = user.assignmenthelper
                if other_user not in helper.assigned_users.all():
                    return Response(
                        {'error': 'You can only chat with assigned users'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except:
                return Response(
                    {'error': 'Helper profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        elif user.role == CommonUser.Role.COMMON:
            try:
                helper = other_user.assignmenthelper
                if user not in helper.assigned_users.all():
                    return Response(
                        {'error': 'You can only chat with your assigned helper'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except:
                return Response(
                    {'error': 'Helper profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Get or create conversation
        conversation, created = Conversation.objects.get_or_create(
            participant1=user if user.id < other_user.id else other_user,
            participant2=other_user if user.id < other_user.id else user
        )
        
        serializer = self.get_serializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class MessageViewSet(ModelViewSet):
    """
    ViewSet for managing messages.
    Users can only see messages in conversations they're part of.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        conversation_id = self.request.query_params.get('conversation_id')
        
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id)
                # Check if user is part of conversation or is SuperUser
                if user.role == CommonUser.Role.ADMIN or conversation.has_participant(user):
                    return Message.objects.filter(conversation=conversation)
            except Conversation.DoesNotExist:
                return Message.objects.none()
        
        # SuperUser can see all messages
        if user.role == CommonUser.Role.ADMIN:
            return Message.objects.all()
        
        # Regular users can only see messages in their conversations
        user_conversations = Conversation.objects.filter(
            participant1=user
        ) | Conversation.objects.filter(
            participant2=user
        )
        return Message.objects.filter(conversation__in=user_conversations)
    
    def perform_create(self, serializer):
        conversation_id = self.request.data.get('conversation')
        user = self.request.user
        
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            raise serializers.ValidationError("Conversation not found")
        
        # Validate user can send message in this conversation
        if user.role != CommonUser.Role.ADMIN and not conversation.has_participant(user):
            raise serializers.ValidationError("You are not part of this conversation")
        
        # Set sender and receiver
        receiver = conversation.get_other_participant(user)
        serializer.save(sender=user, receiver=receiver, conversation=conversation)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a message as read"""
        message = self.get_object()
        if message.receiver == request.user:
            message.is_read = True
            message.save()
            return Response({'message': 'Message marked as read'})
        return Response(
            {'error': 'You can only mark your own received messages as read'},
            status=status.HTTP_403_FORBIDDEN
        )


# Keep RoomViewSet for backward compatibility
class RoomViewSet(ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]
    
