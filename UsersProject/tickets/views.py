from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from django.utils import timezone
from .models import Ticket, TicketTemplate, TicketComment, TicketAttachment, TicketAuditLog, RoutingRule
from .serializers import (
    TicketSerializer, TicketCreateSerializer, TicketUpdateSerializer,
    TicketTemplateSerializer, TicketCommentSerializer, TicketAttachmentSerializer,
    TicketBulkUpdateSerializer, TicketMergeSerializer, TicketAuditLogSerializer,
    RoutingRuleSerializer
)

class TicketPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all().order_by('-created_at')
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TicketPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return TicketCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TicketUpdateSerializer
        return TicketSerializer

    def perform_create(self, serializer):
        # Set created_by to the current user and ensure timestamps are set
        ticket = serializer.save(
            created_by=self.request.user,
            status='open',  # Always set initial status to open
        )
        TicketAuditLog.objects.create(
            ticket=ticket,
            user=self.request.user,
            action='CREATE',
            details={'data': serializer.data}
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Use the main TicketSerializer to return the full ticket data
        ticket = serializer.instance
        response_serializer = TicketSerializer(ticket)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        old_instance = self.get_object()
        old_data = {
            'status': old_instance.status,
            'priority': old_instance.priority,
            'assigned_to': old_instance.assigned_to.id if old_instance.assigned_to else None,
            'tags': old_instance.tags
        }
        
        ticket = serializer.save()
        
        # Log status change
        if 'status' in serializer.validated_data and old_data['status'] != ticket.status:
            TicketAuditLog.objects.create(
                ticket=ticket,
                user=self.request.user,
                action='status_change',
                details={
                    'old_value': old_data['status'],
                    'new_value': ticket.status,
                    'note': serializer.validated_data.get('status_note')
                }
            )
        
        # Log priority change
        if 'priority' in serializer.validated_data and old_data['priority'] != ticket.priority:
            TicketAuditLog.objects.create(
                ticket=ticket,
                user=self.request.user,
                action='priority_change',
                details={
                    'old_value': old_data['priority'],
                    'new_value': ticket.priority
                }
            )
        
        # Log assignment change
        new_assignee_id = ticket.assigned_to.id if ticket.assigned_to else None
        if 'assigned_to' in serializer.validated_data and old_data['assigned_to'] != new_assignee_id:
            TicketAuditLog.objects.create(
                ticket=ticket,
                user=self.request.user,
                action='assignment',
                details={
                    'old_value': old_data['assigned_to'],
                    'new_value': new_assignee_id
                }
            )
        
        # Log tag changes
        if 'tags' in serializer.validated_data and old_data['tags'] != ticket.tags:
            added_tags = list(set(ticket.tags) - set(old_data['tags']))
            removed_tags = list(set(old_data['tags']) - set(ticket.tags))
            
            if added_tags:
                TicketAuditLog.objects.create(
                    ticket=ticket,
                    user=self.request.user,
                    action='tag_change',
                    details={
                        'type': 'added',
                        'tags': added_tags
                    }
                )
            
            if removed_tags:
                TicketAuditLog.objects.create(
                    ticket=ticket,
                    user=self.request.user,
                    action='tag_change',
                    details={
                        'type': 'removed',
                        'tags': removed_tags
                    }
                )

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        serializer = TicketBulkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ticket_ids = serializer.validated_data['ticket_ids']
        action = serializer.validated_data['action']
        value = serializer.validated_data['value']

        tickets = Ticket.objects.filter(id__in=ticket_ids)
        if not tickets.exists():
            return Response({'error': 'No tickets found'}, status=status.HTTP_404_NOT_FOUND)

        update_data = {}
        if action == 'status':
            update_data['status'] = value
        elif action == 'priority':
            update_data['priority'] = value
        elif action == 'assign':
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=value)
                update_data['assigned_to'] = user
            except User.DoesNotExist:
                return Response(
                    {'error': f'User with id {value} not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            tickets.update(**update_data)
            for ticket in tickets:
                TicketAuditLog.objects.create(
                    ticket=ticket,
                    user=request.user,
                    action=f'BULK_{action.upper()}',
                    details={'value': value}
                )

        return Response({'message': f'Updated {tickets.count()} tickets'})

    @action(detail=False, methods=['post'])
    def merge(self, request):
        serializer = TicketMergeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ticket_ids = serializer.validated_data['ticket_ids']
        title = serializer.validated_data['title']

        tickets = Ticket.objects.filter(id__in=ticket_ids)
        if tickets.count() != len(ticket_ids):
            return Response({'error': 'One or more tickets not found'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            # Create merged ticket
            merged_description = "\n\n---\n\n".join([
                f"From Ticket #{ticket.id}:\n{ticket.description}"
                for ticket in tickets
            ])

            merged_ticket = Ticket.objects.create(
                title=title,
                description=merged_description,
                priority=tickets.first().priority,
                status='open',
                created_by=request.user,
                custom_fields={},  # Combine custom fields if needed
                tags=list(set().union(*[set(ticket.tags) for ticket in tickets]))
            )

            # Move comments and attachments
            TicketComment.objects.filter(ticket__in=tickets).update(ticket=merged_ticket)
            TicketAttachment.objects.filter(ticket__in=tickets).update(ticket=merged_ticket)

            # Close original tickets and link them
            tickets.update(
                status='closed',
                custom_fields={'merged_into': str(merged_ticket.id)}
            )
            merged_ticket.linked_tickets.add(*tickets)

            # Create audit log entries
            TicketAuditLog.objects.create(
                ticket=merged_ticket,
                user=request.user,
                action='MERGE_CREATE',
                details={'merged_from': [str(id) for id in ticket_ids]}
            )
            for ticket in tickets:
                TicketAuditLog.objects.create(
                    ticket=ticket,
                    user=request.user,
                    action='MERGED_INTO',
                    details={'merged_into': str(merged_ticket.id)}
                )

        return Response(TicketSerializer(merged_ticket).data)

class TicketTemplateViewSet(viewsets.ModelViewSet):
    queryset = TicketTemplate.objects.all()
    serializer_class = TicketTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

class TicketCommentViewSet(viewsets.ModelViewSet):
    queryset = TicketComment.objects.all()
    serializer_class = TicketCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user)
        TicketAuditLog.objects.create(
            ticket=comment.ticket,
            user=self.request.user,
            action='COMMENT_ADD',
            details={'comment_id': str(comment.id)}
        )

class TicketAttachmentViewSet(viewsets.ModelViewSet):
    queryset = TicketAttachment.objects.all()
    serializer_class = TicketAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        attachment = serializer.save(uploaded_by=self.request.user)
        TicketAuditLog.objects.create(
            ticket=attachment.ticket,
            user=self.request.user,
            action='ATTACHMENT_ADD',
            details={'attachment_id': str(attachment.id)}
        )

class RoutingRuleViewSet(viewsets.ModelViewSet):
    queryset = RoutingRule.objects.all()
    serializer_class = RoutingRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        print('Update request data:', request.data)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        print('Existing instance:', instance.__dict__)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        print('Validated data:', serializer.validated_data)
        
        self.perform_update(serializer)
        print('Updated instance:', serializer.instance.__dict__)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        print('Create request data:', request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print('Validated data:', serializer.validated_data)
        
        self.perform_create(serializer)
        print('Created instance:', serializer.instance.__dict__)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
