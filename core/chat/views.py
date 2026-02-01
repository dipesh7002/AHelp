from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from django.db.models import Subquery, OuterRef, Max
from chat.models import Room, Message, Conversation
from chat.serializers import (
    RoomSerializer,
    MessageSerializer,
    ConversationSerializer,
    ConversationListSerializer
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
    permission_classes = [IsAuthenticated, CanViewConversation]

    def get_serializer_class(self):
        if self.action == 'list':
            return ConversationListSerializer
        return ConversationSerializer
    
    def get_queryset(self):
        user = self.request.user

        # Get base queryset
        if user.role == CommonUser.Role.ADMIN:
            queryset = Conversation.objects.all()
        else:
            queryset = Conversation.objects.filter(
                participant1=user
            ) | Conversation.objects.filter(
                participant2=user
            )

        # Annotate with last message data for list views
        if self.action == 'list':
            # Get the latest message for each conversation
            latest_message_subquery = Message.objects.filter(
                conversation=OuterRef('pk')
            ).order_by('-created_at').values('text', 'created_at')[:1]

            queryset = queryset.annotate(
                last_message_text=Subquery(latest_message_subquery.values('text')[:1]),
                last_message_created_at=Subquery(latest_message_subquery.values('created_at')[:1])
            )

        return queryset
    
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

    def create(self, request, *args, **kwargs):
        conversation_id = request.data.get('conversation')
        user = request.user

        if not conversation_id:
            return Response(
                {'error': 'conversation is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate user can send message in this conversation
        if user.role != CommonUser.Role.ADMIN and not conversation.has_participant(user):
            return Response(
                {'error': 'You are not part of this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Set sender and receiver
        receiver = conversation.get_other_participant(user)

        # Create the message directly
        message = Message.objects.create(
            conversation=conversation,
            sender=user,
            receiver=receiver,
            text=request.data.get('text', '')
        )

        # Update conversation's updated_at timestamp
        conversation.save(update_fields=['updated_at'])

        serializer = self.get_serializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
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
    
