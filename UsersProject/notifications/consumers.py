from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.utils import timezone

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
        else:
            self.user_group_name = f"user_{self.scope['user'].id}"
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )

    async def notification_message(self, event):
        """
        Send notification to WebSocket.
        """
        print(f"Sending notification message: {event}")  # Debug log
        message = event["message"]
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "type": "notification.message",
            "message": {
                "id": str(message["id"]),
                "title": message["title"],
                "message": message["message"],
                "type": message["type"],
                "timestamp": message["createdAt"]
            }
        }))
