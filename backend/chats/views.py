from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import ChatThread, ChatMessage
from .serializers import ChatThreadSerializer, ChatMessageSerializer


class ThreadsListCreate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        arch = request.query_params.get('archived')
        show_archived = str(arch).lower() in {'1', 'true', 'yes'}
        qs = ChatThread.objects.filter(owner=request.user, archived=show_archived).order_by('-updated_at')
        return Response(ChatThreadSerializer(qs, many=True).data)

    def post(self, request):
        title = (request.data.get('title') or '').strip()[:200]
        th = ChatThread.objects.create(owner=request.user, title=title)
        return Response(ChatThreadSerializer(th).data, status=status.HTTP_201_CREATED)


class ThreadDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        th = get_object_or_404(ChatThread, pk=pk, owner=request.user)
        title = request.data.get('title')
        if title is not None:
            title = (title or '').strip()[:200]
            if title:
                th.title = title
        if 'archived' in request.data:
            th.archived = bool(request.data.get('archived'))
        th.save(update_fields=['title', 'archived', 'updated_at'])
        return Response(ChatThreadSerializer(th).data)

    def delete(self, request, pk):
        th = get_object_or_404(ChatThread, pk=pk, owner=request.user)
        th.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MessagesListCreate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, thread_id):
        th = get_object_or_404(ChatThread, pk=thread_id, owner=request.user)
        msgs = th.messages.all().order_by('created_at')
        return Response(ChatMessageSerializer(msgs, many=True).data)

    def post(self, request, thread_id):
        th = get_object_or_404(ChatThread, pk=thread_id, owner=request.user)
        role = (request.data.get('role') or '').strip().lower()
        content = (request.data.get('content') or '').strip()
        citations = request.data.get('citations')
        if citations is None:
            citations = []
        # Ensure citations is a list-like
        if not isinstance(citations, (list, tuple)):
            citations = []
        if role not in {'user', 'assistant', 'system'}:
            return Response({"detail": "invalid role"}, status=status.HTTP_400_BAD_REQUEST)
        if not content:
            return Response({"detail": "content required"}, status=status.HTTP_400_BAD_REQUEST)
        msg = ChatMessage.objects.create(thread=th, role=role, content=content, citations=list(citations))
        # If thread has no title and this is the first user message, derive a title
        if not th.title and role == 'user':
            head = ' '.join(content.split())
            th.title = (head[:64])
        # Unarchive on new activity to mimic ChatGPT behavior
        th.archived = False
        th.updated_at = timezone.now()
        th.save(update_fields=['title', 'archived', 'updated_at'])
        return Response(ChatMessageSerializer(msg).data, status=status.HTTP_201_CREATED)
