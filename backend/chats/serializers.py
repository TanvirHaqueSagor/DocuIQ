from rest_framework import serializers
from .models import ChatThread, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'citations', 'inline_refs', 'created_at']


class ChatThreadSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatThread
        fields = ['id', 'title', 'archived', 'created_at', 'updated_at', 'last_message']

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        if not msg:
            return None
        return ChatMessageSerializer(msg).data
